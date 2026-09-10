# Speed audit of the first-block sniper (engine v3, commit 754ba5f) — auditor "fable"

Folder: `scratchpad/audit_speed_fable/`. Nothing in the repository was modified by this audit. Line references are to HEAD (754ba5f, engine v3, 642 lines) as the brief specifies; during the audit an uncommitted "engine v4" (879 lines) appeared in the working tree — section 1b states every finding's status against it, with v4 line numbers. Every number below is tagged:
**[M]** measured in this sandbox (scripts in this folder, re-run in this session), **[L]** read from the dry-run logs in
the data root (`sniper_engine_v9/v14/v15_E2.jsonl`), **[I]** inferred for an Ohio box. The sandbox is far from Ohio and
behind a proxy, so absolute network numbers here (35 ms sequencer round trip, 0.5 s feed delay) validate methods only;
CPU-side numbers (decode, wake, sign, scans) transfer to a c6i/c7i core within a factor of ~1.5.

## 1. Summary

1. The largest single gain is not code speed but **when** the send fires: reacting to the feed's first T+2 block puts the
   request on the wire 50 ms (median) to 90-130 ms (p90) after the boundary [M: arrival of the new second's first block
   relative to the estimated boundary, two captures], i.e. block 2-3 of T+2. Predicting the boundary with a robust estimator
   and firing a pre-signed request lands in the **first block of T+2 on roughly 80-90% of launches** [I, model in section 6].
2. The engine's boundary estimator (2nd percentile of flip phases after a largest-gap rotation, `sniper_engine.py:156-165`)
   is hijacked by a single stalled flip: it jumped 260 ms and 162 ms in two dry runs [L] and swings 88-121 ms (sd) at its own
   30-flip minimum on the captures [M]. An interval-vote estimator is stable to 6-24 ms here at 30 flips and 1.5-24 ms at
   60 [M]; from Ohio the residual is delivery jitter, expected at a few ms [I].
3. A `submit()` written on top of the engine's `Rpc` class (thread-local connection, `:65-84`) pays ~25 ms of SSL-context
   construction [M], 1.8 ms DNS [M, 34 ms max] and a TLS handshake [I: 2-4 ms in Ohio] **after the boundary**. Warm
   keep-alive sockets to the sequencer survive 90 s idle [M]; the post-boundary work then is one `sendall` of ~0.1 ms [M].
4. The wait loops poll with `time.sleep(0.002)` while the feed thread holds the GIL: 5.1 ms median / 7.1 ms max late [M].
   A 0.2 ms switch interval plus a 3 ms spin brings that to 0.02 ms median / 0.3 ms max [M].
5. Everything between the wait and the send (two 0.76 ms scans of the 4000-entry `valtx` deque, 0.43 ms signing, thread
   start, logging) can be done 40 ms before the target: 2.1 ms saved with coincurve, ~5 ms without [M].
6. `coincurve` matters more than the setup script suggests: without it the per-frame hot loop is 13 ms median / 258 ms max
   (a creation is understood only after every value-carrying transaction ahead of it in the frame is recovered); with it 1.0
   ms; with direct coincurve recovery and lazy router-buy recovery 0.24 ms median / 1.5 ms max [M].
7. Expected landing for this operator after the changes: first block of T+2 on ~80-90% of launches, second block on most of
   the rest, second-one (+6.18%) landings at ~0 with a 5 ms floor margin [I]. With the engine as it stands (react mode plus a
   naive submit): block 2-3 of T+2, which is about what the backtest's "0.3 s behind the first buyer" assumes.

## 1b. Status against the v4 file that appeared in the working tree during this audit

`git status`: `src/strategy/sniper_engine.py` modified (+406/−169) against HEAD 754ba5f; `deploy/ohio_setup.sh`, the docs and
`latency_probe.py` unchanged; the docstring cites a "section 23" that the report does not yet contain. Sections 2, 8 and the
diff file use HEAD's lines; this table maps each finding to v4.

| finding | v4 status | v4 lines |
|---|---|---|
| D1 coincurve direct + lazy router-sender recovery | done: `_sender_fast` with a start-up self-test; router senders recovered only when the calldata names a watched curve | 106-140, 415-430, 821-825 |
| D2 estimator | changed, not settled: theta = midpoint of p98(last-old-block offsets) and p2(first-new-block offsets) on the monotonic clock, brackets < 0.5 s, 60-sample minimum, cached 1 s. No modulo, so v3's single-outlier hijack is gone. But the p98 of the lower bound is a tail statistic of delivery jitter. Out of sample [M, `est_compare.py` row `v4_bracket`]: window sd **115 ms at 60 flips / 146 at 30** through the jittery capture (vote 24 / 24) and **21 / 75 ms** through the calm one (vote 1.5 / 6.3); biased **late by +59 / +12 ms** against the vote; first-block share at margin 0 45-58% vs the vote's 86-92%. It matches the vote only at 120+ flips on the calm path. The interval vote (section 5) drops in: it uses the same two arrival times. | 297-313, 865-871 |
| D3 wake | done: one `Condition.notify_all` per indexed message, `sys.setswitchinterval(0.0005)`, sleep then a 4 ms spin in predict mode | 316-345, 835, 872 |
| D4 pre-build / pre-sign | half: reserves are folded incrementally as buys arrive (no deque scans after the wake), the log and the scorer thread come after the send, `wake_to_send_ms` is logged; but the buy is built and (live) signed after the wake and `fire()` runs synchronously: 0.43 ms sign + build + fire still sit between the wake and the wire | 655, 696-700, 266-271 |
| D5 warm sockets | done for the sockets (5 s heartbeat, warm RTT logged). Remaining: `fire()` starts one thread per endpoint (0.15 ms each) and polls `out` every 0.5 ms — about 0.5-1 ms more than two sequential `sendall`s of a pre-serialised request; `http.client.HTTPSConnection()` without a shared context rebuilds an SSL context (21-25 ms) on every reconnect, i.e. exactly when a send finds a dead socket | 164-218 |
| D6 deque scan | moot: one scan at resolve time, off the critical path | 415-430 |
| D7 warm-up, reconnect, flips | not done: 5 s timer warm-up, 2 s reconnect sleep, flip samples kept across connections. New and good: a 2 s stall watchdog on `recv` | 846-874 |
| D8 GC | half: `gc.freeze()` plus thresholds (50000, 20, 20); gen-2 collections still fire automatically | 842 |
| D9 margin tuning / proof | changed: +12 ms early, −12/99 first block, −6 later block, floor 8, ceiling 45, `tx_index` logged. The controller's zero-drift condition 12·P(early) = 6·P(later) + 0.12·P(first), with P(later) ≈ 10-15% from the block-timer lottery even at a perfect margin, puts its equilibrium at **P(early) ≈ 6-8%**, not the 1% the docstring targets; in practice the floor binds, so the floor is the real policy (section 6). No `blocks_after_flip`, no buys-ahead count | 361-378 |
| D10 pinning / instance | `PIN_CPU` via `sched_setaffinity` on the whole process; `deploy/ohio_setup.sh` unchanged (t3.small, chrony without `makestep`/`maxslewrate`) | 64, 830-834 |
| D11 RPC resolution for non-bundled creations | not done: every creation the feed cannot resolve still polls `resolve_rpc` for up to 3 s | 617-634, 531-543 |
| D12 event-driven feed resolution, ping | not done: waits for T+1's first block (0.25 s Condition waits); `ping_interval=10, ping_timeout=10` (20 s detection), `compression=None`, `max_queue=4` | 617-620, 846 |
| new in v4 | `SEAT_WAIT_MS=300`: react mode deliberately sends 300 ms into the seat's second unless an outsider has already bought (`OUT2_MAX`); a strategy rule, not a latency one. With it, react mode lands where the backtest assumes by construction, and the send-path work only matters in predict mode or with `SEAT_WAIT_MS=0`. `blocks_to_seat` and `seat_flip_to_send_ms` are logged: a landing proof from the feed side. `mono()` on the critical path; log writes on a queue | 54, 351-357, 662, 704-708, 78-96 |

## 2. Where the time goes today (E2 seat, predict or react)

| stage | today | after the diffs | source |
|---|---|---|---|
| feed frame arrives -> creation understood (json + segment split + rlp + sender recovery of every buy/value tx ahead of it) | 0.92 ms median, 3.6 ms max (coincurve via eth-account); 13 ms / 258 ms without coincurve | 0.34 ms median, 0.74 ms max | [M] `bench_decode.py`, `bench_lazy.py` |
| creation -> curve resolved from the feed | 196-1,017 ms (waits for the first block of T+1, `:423`) | the BUNDLE_MIN-th named buy, tens to hundreds of ms into T | [L] v15; D12 |
| creation -> curve resolved by RPC (147 of 167 creations in v15 take this path) | up to 3 s of 20 ms polls on the public RPC, 429s | none: skipped before any network call | [L]; D11 |
| wait for the seat (react: feed shows T+2; predict: estimate + margin) | react: boundary + 50 ms median / 90-130 p90 + feed delay; predict: estimator error 88-121 ms sd at 30 flips | vote estimator: 6-24 ms sd at 30 flips here, a few ms in Ohio | [M] `est_compare.py` |
| wake-up of the waiting thread | 5.1 ms median, 7.1 ms max | 0.02 ms median, 0.3 ms max | [M] `bench_wake.py` |
| curve_buys + curve_state + gates + size + build + log | 0.76 + 0.76 + ~0.05 + 0.02 ms | before the target; a re-check of two counters at the target | [M] `bench_send_path.py` |
| sign | 0.43 ms (3.2 ms without coincurve) | before the target | [M] |
| connection to the sequencer (naive submit on `Rpc`) | SSL context 21-25 ms + DNS 1.8 ms + TLS 2 RTT | warm socket: `sendall` 66-234 us | [M] context/DNS/sendall; [I] handshake in Ohio |
| uplink one way | 0.5-1.5 ms | same | [I] half the probe's RTT target |
| garbage collector | full collection 6.3 ms at random moments (35k-object heap) | never while a creation is pending | [M] |

Post-boundary work today (predict mode): ~5 (wake) + 1.5 (scans) + 0.43 (sign) + 0.16 (thread, log) + 25-31 (connection) = **32-38 ms** before the request leaves the box; after the diffs **0.1-0.4 ms**.

## 3. Ranked latency improvements

| # | change | saves per send | measured / inferred | method | diff |
|---|---|---|---|---|---|
| 1 | Predict the boundary (robust estimator) and fire at estimate + margin instead of reacting to the feed's T+2 block | 50 ms median, 90-130 ms p90 (moves the landing from block 2-3 to block 1 of T+2) | [M] offset of the first new-second block vs the estimate: p50 +49/+50 ms, p90 +130/+91 ms in two captures; [I] landing | `est_compare.py`, `analyze_capture.py` | D2, D3, D4 |
| 2 | Warm keep-alive TLS sockets, one shared SSL context, DNS once, pre-serialised request to sequencer and provider | 25 ms (context) + 1.8 ms (DNS, 34 max) + TLS handshake (2-4 ms Ohio) = 28-31 ms, only if submit() is built on `Rpc` | [M] context, DNS, sendall, 90 s idle survival; [I] handshake | `bench_send_path.py`, `keepalive_test.py` | D5, `sender.py` |
| 3 | Wake precision: `sys.setswitchinterval(0.0002)`, Event-driven react, sleep-then-spin for the last 3 ms | 5 ms median, 7 ms max -> 0.02 / 0.3 ms | [M] | `bench_wake.py` | D3 |
| 4 | Build, size and sign 40 ms before the target; only `sendall` after it; re-size only if a buy of the curve arrived meanwhile | 2.1 ms (5 ms without coincurve) | [M] | `bench_send_path.py` | D4, D6 |
| 5 | GC: `gc.freeze()` after start, collect only from `prune()` when nothing is pending | 0 median, removes a 6+ ms tail | [M] pause size; [I] frequency | `bench_wake.py` | D8 |
| 6 | Direct coincurve recovery (all three envelope types, 0 mismatches on 615 txs) and lazy recovery of router-buy senders | per frame 1.02 -> 0.24 ms median, 22 -> 1.5 ms max; creation understood 0.92 -> 0.34 ms; vs no coincurve: 13 ms median / 258 ms max | [M] | `bench_decode.py`, `bench_lazy.py`, `recover_fast.py` | D1 |
| 7 | No RPC resolution for creations that cannot pass the rule (88-95% of creations) | removes up to 150 RPC calls + JSON parses per creation on the hot thread; the 429s | [L] counts; [I] 1-10 ms of GIL jitter during bursts | log analysis | D11 |
| 8 | Reconnect at once, warm-up by block timestamp, ping 10 s / timeout 5 s, clear flips on reconnect | blind time per feed drop 7-8 s -> ~1.5 s; dead-feed detection 40 s -> 15 s | [M] drain 0.74-0.99 s, handshake 0.5-0.9 s here; [L] drops every 10-70 min | `analyze_capture.py`, logs | D7, D12 |
| 9 | Resolve from the feed the moment BUNDLE_MIN named wallets have bought one curve | resolve_ms 200-1,000 -> the bundle's own timing; gives #4 its slack | [L] | logs | D12 |
| 10 | c6i/c7i.large instead of t3, engine pinned to one vCPU, `Nice=-10`, chrony on Amazon Time Sync with slewing only | protects #3: a shared core reproduces the 5 ms GIL effect | [I]; the GIL measurement is the model | — | D10 |
| 11 | Log `trade_decision` and start the scorer thread after the send, keep the log file open | 0.16 ms | [M] | `bench_send_path.py` | D4 |

## 4. Measurements

### 4.1 Probe (`latency_probe.py`, 300 s, this sandbox) [M]
Block cadence 92 ms median / 179 p90; 295 flips; boundary edge 0.068; flip spread 0.48 s (proxy jitter); feed delay minus
clock offset 0.66 s median; sequencer RTT 35 ms median / 39 p90; RPC 46 / 52. From Ohio the RTTs should read 1-3 ms and the
spread about one block [I]; the runbook's thresholds (10 ms RTT) are the right go/no-go.

### 4.2 Feed timing, two raw captures (`capture_feed.py`, `analyze_capture.py`) [M]
| | capture 1 (420 s, 4,149 live L2 frames) | capture 2 (210 s, 2,066) |
|---|---|---|
| inter-frame gap ms p10 / p50 / p90 / p99 / max | 53 / 97 / 150 / 245 / 1,055 | 75 / 100 / 127 / 173 / 1,150 |
| gaps > 300 ms | 13 | 3 |
| blocks per second min / median | 6 / 10 | 2 / 10 |
| bracket at a flip (last old-second block -> first new-second block) p50 / p90 | 101 / 148 ms | 100 / 140 ms |
| backlog replayed on connect | 53 s, 528 frames, 11 MB, drained in 0.99 s | 43 s, 454 frames, 13.9 MB, 0.74 s |
| websocket handshake | 916 ms | 491 ms (Server-Timing: cfEdge 23 ms, cfOrigin 241 ms) |
| frame size median / max | 19 KB / 129 KB | 26 KB / 131 KB |
| seconds whose first block arrived > 300 ms late | 1.2% | 1.4% |

The feed is fronted by Cloudflare (`server: cloudflare`, `cf-ray ...-IAD` from here), negotiates no compression
(`extensions: []`), and the `sequenceNumber` of an L2 message **equals the L2 block number** (checked against
`eth_getBlockByNumber` for three consecutive blocks: offset 0). Frames are one message each when live; the backlog arrives as
multi-message frames.

### 4.3 Decode / recover / match (`bench_decode.py`, `bench_lazy.py`, `recover_fast.py`; 1,500 frames, 24,279 txs) [M]
`json.loads` 22 us median / 48 p90 / 494 max per frame; `decode_batch` 68 / 340 / 2,003 us per message (14 txs median, 99
max); `parse_tx` 8.6 / 30.8 us. Sender recovery: eth-account without coincurve **6,609 us** (6,978 p90); eth-account with
coincurve 414 (564); direct coincurve on the signing hash (`recover_fast.py`) 116-127 us (153-166 p90), 0 mismatches vs
eth-account on 300 legacy, 5 type-1, 300 type-2 and 10 unparseable txs (fallback). Hot loop per frame as the engine runs it:
no coincurve 13,032 us median / 258 ms max (16.7% of a core); eth-account+coincurve 1,018-1,077 / 19-22 ms max (1.4%);
recover_fast eager 505 / 6.3 ms; recover_fast with lazy router-buy recovery 244 / 1.5 ms (0.3%). Frame start -> creation
understood (24 creations): 916 us median / 3,622 max -> 338 / 742 with lazy recovery.

### 4.4 Wake-up, GIL and GC (`bench_wake.py`) [M]
| waiter | lateness median / p90 / max |
|---|---|
| idle process, sleep(1 ms) poll | 0.66 / 1.03 / 1.10 ms |
| feed thread decoding, sleep(2 ms) poll — the engine (`:177,182,189`) | 5.08 / 6.98 / 7.08 ms |
| same, sleep(1 ms) | 4.29 / 5.99 / 6.37 |
| switch interval 0.1 ms, sleep(1 ms) | 0.65 / 1.24 / 1.40 |
| switch interval 0.1 ms, sleep(0.2 ms) | 0.22 / 0.50 / 0.55 |
| spin, default 5 ms switch interval | 0.03 / 3.07 / 4.48 |
| spin, 0.1 ms switch interval | 0.02 / 0.26 / 0.32 |
| asyncio `loop.call_at` in the decoding loop | 0.15 / 0.18 / 0.20 |
Full `gc.collect()` over 35k tracked objects: 6.3 ms; gen-0: 0.00 ms. Thread start to running: 146 us.

### 4.5 Post-boundary path (`bench_send_path.py`, valtx deque full at 4,000, 301 curves) [M]
`curve_buys` 757 us (called at `:463` and again inside `curve_state` at `:499`); `curve_state` 763 us; `size_buy` 0.3 us;
buy dict 1.2 us; `log()` open+write+close 16 us (7 us with a kept handle); `Account.sign_transaction` 430 us; JSON body 3.4 us
(213-byte raw tx); constructing an `http.client.HTTPSConnection` with a default context and issuing one request 25.4 ms
(21.1-21.8 ms of it is `ssl.create_default_context()`; 0 with a shared context); `getaddrinfo` 1.8 ms median / 34 ms max
(first run); `sock.sendall` of a pre-built request 66-234 us.

### 4.6 Endpoints [M]
Sequencer `https://sequencer.mainnet.chain.robinhood.com`: istio-envoy front, HTTP/2 capable, not behind Cloudflare;
`eth_blockNumber` and `eth_chainId` -> `-32601 method does not exist`; `eth_sendRawTransaction("0x00")` -> `-32000 typed
transaction too short` (the method is served to an anonymous client); HTTP keep-alive reuse works (`num_connects=0` on the
second and third request), a direct TLS socket answered after 0, 10, 45 and 90 s idle. Public RPC: Cloudflare, HTTP/2, reuse
works, 429s under three engines [L]. Whether the sequencer accepts a real signed transaction from a new address remains
unverified until the first live send (report 22.2).

### 4.7 Dry-run log evidence [L]
v14 (predict, 27 min): boundary phase 0.0715, 0.0748, 0.0787, **0.8189**, 0.0756 with 600 flips: a −260 ms jump, then back.
v9 (predict, 69 min): 0.0693 -> **0.9074** for two consecutive 5-minute readings after a `keepalive ping timeout` reconnect,
then 0.059. Ten predict sends: `feed_ts_at_send - seat_ts = -1` on eight (fired before the feed showed T+2, `sent_ms`
1,168-1,792), `predict-late` on two. v15 (react, 9.5 min): 167 creations, 147 with < 3 named wallets, 20 with a non-ETH
quote; 158 of 167 decisions resolved by RPC, 7 by the feed with `resolve_ms` 196-1,017; one feed drop (`no close frame`).
All runs: 429 from the public RPC in `seed` and `score`.

## 5. The boundary estimator

**Why the low edge fails.** `boundary_phase()` (`:156-165`) sorts flip phases, rotates on the largest circular gap and takes
the 2nd percentile. Flip arrivals are boundary + U + d + jitter with U in [0, one block]; through a stalled delivery a flip
lands 0.3-1.0 s late, which modulo one second is anywhere on the circle. One such flip inside the empty arc splits the
largest gap; the rotation base becomes the outlier and the "low edge" becomes the outlier's phase (v9/v14 jumps above). With
30 flips `int(0.02 * 30) = 0`, so the estimator is the raw minimum. Out of sample (estimate on n flips, judge on the next 60):

| estimator | capture 1, n=30 sd / range | n=60 | n=120 | capture 2, n=30 | n=60 |
|---|---|---|---|---|---|
| p2 low edge (engine) | 88 / 355 ms | 22 / 70 | 9 / 22 | 121 / 335 | 13 / 27 |
| v4 working tree: midpoint of p98(lower) and p2(upper), no modulo | 146 / 591 | 116 / 357 | 22 / 50 | 75 / 192 | 21 / 43 |
| raw minimum | 88 / 355 | 111 / 309 | 9.5 / 22 | (whole capture −307 ms) | — |
| **interval vote** (each bracket (last old-second block, first new-second block] votes for the 1-ms bins it covers; centre of the most-voted run; brackets wider than 350 ms dropped; no rotation) | **24 / 69** | 24 / 65 | 20 / 47 | **6.3 / 17** | **1.5 / 3** |
| median of bracket midpoints | 26 / 76 | 26 / 75 | 21 / 48 | 14 / 40 | 0.5 / 1 |
| median first-block phase − half the median bracket (the "first block + cadence" idea) | 27 / 83 | 25 / 70 | 21 / 51 | 15 / 41 | 3.5 / 7 |
| 10th percentile of first-block phases, wide brackets dropped | 23 / 68 | 21 / 63 | 14 / 34 | 14 / 41 | 7 / 14 |

The v4 midpoint sits 12-59 ms *later* than the vote (its lower bound is the 98th percentile of a right-tailed jitter distribution). The low edge sits 25-37 ms *earlier* than the bracket-based estimators here because it is the extreme of a jittered
distribution; the bracket estimators agree with each other within 3 ms. **Recommendation: the interval vote**, because it
needs no rotation, one outlier cannot move it, it works from 30-60 flips (a fresh connection, D7 clears the deque on
reconnect), and in low jitter its winning run is the intersection of all brackets, i.e. the boundary plus the constant feed
delay. Keep 300 flips (5 minutes: clock and route changes age out), recompute every 3 s in `chain_loop` (never on the critical
path), log the peak vote count and run width; if the peak is below 50% of the flips, mark the estimate low-confidence and
send in react mode. Median-of-midpoints is an acceptable simpler alternative.

**Clock.** The estimate and the target are both local wall-clock phases anchored to the observed T+1 flip, so a constant
clock offset cancels and the feed delay d is *inside* the estimate. What does not cancel: rate error over the deque window
(10 ppm × 300 s = 3 ms; chrony's default 500 ppm slew would be 150 ms, so set `maxslewrate 100` and clear the deque when
`chronyc tracking` shows a step or > 50 ppm) and a step (`makestep 1.0 3` only at boot). Use `time.time()` everywhere the
engine does; never mix `perf_counter`.

## 6. Margin policy

**Model** (Nitro sequencer as I read `createBlock`: it drains its queue, *then* reads `time.Now()` for the block's timestamp,
and makes at most one block per max-block-speed, ~100 ms on this chain [I, verify against the pinned nitro version]). A
transaction arriving at boundary + ε with ε > 0 can never be stamped T+1; it lands in the first T+2 block if no drain
happened between the boundary and its arrival: P(first block) ≈ 1 − ε / 100 ms. A transaction arriving δ *before* the
boundary is stamped T+1 with probability δ / 100 ms (at E2 that is a landed buy paying +6.18%, not a revert) and otherwise
sits ahead of everyone in the first T+2 block. Our arrival is boundary + d + u + MARGIN + e (d feed delay, inside the
estimate; u uplink one-way; e estimator + wake + clock error). The asymmetry decides the policy: a second-one landing costs
about a whole trade's expected profit, a second-block landing costs the first-block bonus the backtest does not count.

| MARGIN | arrival after boundary (d + u ≈ 3-6 ms in Ohio) | P(second one) at σ_e = 3 ms | P(first block of T+2) | the feed's own view here (capture 2 / capture 1): first block delivered after estimate + margin |
|---|---|---|---|---|
| 0 | 3-6 ms | ~2-5% (e < −(d+u)) | 94-97% | 90 / 87% |
| 5 (floor) | 8-11 | < 0.3% (3σ) | 89-92% | 88 / 83 |
| 10 | 13-16 | ~0 (> 4σ) | 84-87% | 87 / 80 |
| 15 (start) | 18-21 | 0 | 79-82% | 84 / 76 |
| 25 (engine default) | 28-31 | 0 | 69-72% | 82 / 69 |
| 40 | 43-46 | 0 | 54-57% | 62 / 58 |

Policy: start at **MARGIN_MS = 15**, floor **5**, ceiling **60**. Tune from receipts (D9): second-one landing +15 ms at once;
otherwise every 20 landings, if none was early and the first-block share is below 80%, −2 ms; if the first-block share is
above 90%, hold. Do not go below 10 ms until 30 landings show no early one. React mode stays the fallback whenever the
estimate is low-confidence, the T+1 flip has not been seen 3.5 s after the creation, or the feed shows T+2 before the target
(`predict-late`, kept). The margin can only be trusted after σ_e is measured on the box: run the engine's `boundary` log
for an hour and take the window-to-window sd (target ≤ 3 ms); if it is 5-10 ms (a shared core, a bad Cloudflare route),
raise the floor to 3σ − (d + u).

## 7. Recommended architecture and configuration

- **Feed**: one direct `wss://feed...` client per box, `compression=None` (nothing is negotiated anyway), `ping_interval=10,
  ping_timeout=5`, reconnect after 0.2 s, warm-up decided per message (block second more than 2 s behind the chrony clock
  = replay), flips cleared on reconnect. The Nitro relay only if a second consumer is needed (the probe while the engine
  runs, or a second seat): it adds a local hop [I: < 1 ms] and its own reconnect; Robinhood's per-client limit is the reason.
  Never run the probe as a second client against a live engine; the engine's `boundary` events are the probe.
- **Decode**: as v3 (all three envelopes, router buys by calldata), direct coincurve recovery; recover router-buy senders
  lazily (only when a decision needs the match) — D1.
- **Resolution**: skip anything that cannot pass the rule before any network call (D11); resolve from the feed the moment the
  bundle is visible (D12); RPC only for the scorer.
- **Pre-build / pre-sign**: at the T+1 flip (a second before the seat) size on the feed-tracked curve, build and sign the buy
  with nonce, gasPrice and value fixed; also sign approve and sell (nonce+1, nonce+2) then; at target − 40 ms re-check two
  counters (buys of the curve, valtx count) and re-sign only if something arrived (0.43 ms). After the target: `sendall` to
  the sequencer, then to the provider (same raw tx, same nonce: the second is a duplicate, harmless), then read both replies.
- **Sockets**: `sender.py` — one shared `ssl` context, DNS once, TCP_NODELAY, keep-alive with a 15 s `eth_chainId`-style
  heartbeat (the sequencer rejects the method but answers, which is all the heartbeat needs; 90 s idle survived here),
  request bytes pre-serialised, reconnect once on failure. `net.ipv4.tcp_slow_start_after_idle=0`.
- **Process model**: one process; the feed loop on asyncio as now; `handle_creation` threads as now but woken by Events
  (D2/D3), `sys.setswitchinterval(0.0002)`, sleep-then-spin for the last 3 ms. The next step, if the box's `bench_wake` p90
  is above 1 ms: move the timer + sockets into a second process pinned to the other vCPU, fed the signed request bytes over
  a unix socket (~0.1 ms [I]); it is immune to the decoder's GIL and GC.
- **GC**: `gc.freeze(); gc.disable()` after start, `gc.collect()` from `prune()` only when no creation is pending (D8).
- **Instance**: c6i.large or c7i.large (2 vCPU, no burst credits, no steal; ~$60/month on demand), engine `CPUAffinity=1`,
  `Nice=-10`. The engine needs 0.3-1.4% of a core [M], so a t3.small could run it; the case against t3 is scheduling jitter
  on a shared core, of which the measured 5 ms GIL effect is the model. t3.small in unlimited mode is acceptable for the dry
  run and, if `bench_wake.py` on it shows p90 < 1 ms, as the budget live box.
- **Clock**: chrony on 169.254.169.123 (`prefer iburst minpoll 4 maxpoll 4`), `makestep 1.0 3`, `maxslewrate 100`; alert on
  offset > 2 ms or a step; the estimator is relative, so what matters is rate stability (section 5).
- **Configuration**: `SEND_MODE=react` for the first 20 live landings (measures d, u and the block position with zero
  early risk), then `SEND_MODE=predict MARGIN_MS=15` with the policy of section 6; `MAX_LATE_S=0.5` as now.
- **What to log to prove the landing** (D9): per send — target local time, fire time, `fire_vs_target_ms`, the estimate and
  its vote count, `flip_at[T+1]`, each endpoint's reply and its RTT, the hash; per receipt — `blockNumber`,
  `transactionIndex`, block timestamp vs `seat_ts`, `blocks_after_flip = blockNumber − sequenceNumber of the first T+2 feed
  message` (offset 0, verified), the number of buys of the curve ahead of ours in that block, and the feed arrival time of
  the block that holds our tx minus the estimate (position in milliseconds without any RPC). Daily: P(early), P(first
  block), P(block 2), P(block ≥ 3), mean and sd of `fire_vs_target_ms`, estimator sd.

## 8. Code review: latency defects with line references and proposed diffs

Full hunks in `sniper_engine_latency.diff` (not applied); companions `recover_fast.py` (validated) and `sender.py`.
Line numbers are HEAD's (v3); section 1b gives the v4 equivalents and which hunks v4 already contains (D1, D3, D6; D4, D5, D8 in part).

| id | lines | defect | proposed change |
|---|---|---|---|
| D1 | 24-26, 614, 619, 629 | `Account.recover_transaction` (414 us with coincurve, 6.6 ms without) for every direct buy, creation and value-carrying tx in the frame, ahead of the creation | `from recover_fast import recover_sender` (116-127 us); recover router-buy senders lazily at decision time |
| D2 | 93, 156-165, 599-601 | largest-gap rotation + 2nd percentile; hijacked by one stalled flip; needs 30 flips; recomputed on the critical path (`:175`) | store flips as (last old-second arrival, first new-second arrival); interval vote, 60-flip minimum, deque 300, cached in `chain_loop` every 3 s; set a per-second `threading.Event` at the flip |
| D3 | 168-192, 640-642 | `time.sleep(0.002)`/`0.001` polls under the GIL: 5 ms late | `sys.setswitchinterval(0.0002)`; Event waits; `sleep_until(target)` = 1 ms sleeps then a 3 ms spin; `wait_for_second` returns 40 ms before the target |
| D4 | 459-508 | after the wait: two deque scans, gates, build, `log()`, thread start, then `submit()` | build/size/sign before the target; at the target re-check two counters, re-sign only if changed; log after the send |
| D5 | 65-87, 127-131 | `Rpc` keeps one connection per thread; a submit on it pays context + DNS + handshake at the boundary | `sender.py`: warm dual-endpoint sockets, shared context, pre-serialised request, `fire()` = two `sendall` then replies; `Rpc` takes the shared context |
| D6 | 247-255 | `curve_buys` copies and scans all 4,000 `valtx` entries (0.76 ms, twice per decision) | scan from the newest entry and stop below `since_ts` (~20 us [I]) |
| D7 | 588-592, 637 | 5 s timer warm-up (discards 4 s of live feed, would accept a slow replay), 2 s reconnect sleep, flips kept across connections | warm-up per message by timestamp; 0.2 s; clear flips and the cached estimate on reconnect |
| D8 | 565-573, 580 | gen-2 collections at arbitrary moments (6.3 ms measured) | `gc.freeze(); gc.disable()`; collect from `prune()` when `pending == 0` |
| D9 | 195-208 | +20/−5 steps, floor 5, no position proof | +15 / −2 per 20 landings, floor 5, log `transactionIndex`, buys ahead in block, `blocks_after_flip` |
| D10 | `deploy/ohio_setup.sh` 2, 8, 10, 59-64 | t3.small, no pinning, chrony steps allowed, coincurve build failure silent | c6i/c7i.large, `CPUAffinity=1`, `Nice=-10`, `makestep 1.0 3`, fail the setup if coincurve is missing |
| D11 | 419-441, 351 | every non-bundled creation (88-95%) polls the RPC every 20 ms for up to 3 s | skip before any network call; 100 ms polls for the rest |
| D12 | 423-424, 588 | feed resolution waits for the first block of T+1; ping 20/20 s | stop waiting when BUNDLE_MIN named wallets have bought one curve; `ping_interval=10, ping_timeout=5, compression=None` |

Key hunks (abridged; the file has the full text):

```
--- D1 ---
@@ -26 +26,2 @@
 from eth_account import Account
+from recover_fast import recover_sender        # coincurve on the signing hash; eth-account fallback
@@ -614 +616 @@   (also 619, 629)
-                                    snd = Account.recover_transaction(t).lower()
+                                    snd = recover_sender(t)

--- D2 ---
@@ -156,10 +156,24 @@
 def boundary_phase():
-    ph = sorted(t % 1.0 for t in state["flips"])
-    if len(ph) < 30:
-        return None
-    gaps = [...]; k = max(range(len(ph)), key=lambda i: gaps[i]); base = ph[(k + 1) % len(ph)]
-    rot = sorted((x - base) % 1.0 for x in ph)
-    return (base + rot[int(0.02 * len(rot))]) % 1.0
+    fl = [x for x in state["flips"] if 0 < x[1] - x[0] < 0.35]
+    if len(fl) < 60:
+        return None
+    bins = 1000; v = [0] * bins
+    for tp, tf in fl:
+        a = int((tp % 1.0) * bins); b = int((tf % 1.0) * bins); i = (a + 1) % bins
+        while True:
+            v[i] += 1
+            if i == b:
+                break
+            i = (i + 1) % bins
+    m = max(v); idx = [i for i in range(bins) if v[i] == m]
+    if idx[-1] - idx[0] > bins // 2:
+        idx = sorted(i + bins if i < bins // 2 else i for i in idx)
+    state["boundary_votes"] = (m, len(fl))
+    return (((idx[0] + idx[-1]) / 2 + 0.5) / bins) % 1.0
@@ -599,3 +613,7 @@   (feed loop)
-                                state["flips"].append(seen); state["flip_at"].setdefault(ts, seen)
+                                state["flips"].append((state["last_l2_t"], seen)); state["flip_at"].setdefault(ts, seen)
+                                ev = state["flip_event"].get(ts)
+                                if ev is not None:
+                                    ev.set()
                             state["last_seen_ts"] = max(state["last_seen_ts"], ts); state["feed_ts"] = max(state["feed_ts"], ts)
+                            state["last_l2_t"] = seen

--- D3 ---
+def sleep_until(target, spin_s=0.003):
+    while True:
+        d = target - time.time()
+        if d <= 0:
+            return
+        if d > spin_s:
+            time.sleep(min(0.001, d - spin_s))
 (wait_for_second: Event waits instead of sleep polls; returns (mode, target) at target - 0.040)
@@ -640,3 +680,4 @@
 if __name__ == "__main__":
+    sys.setswitchinterval(0.0002)

--- D4 ---
@@ -496,12 +538,30 @@
-    threading.Thread(target=score_launch, ...).start()
     if gates:
         log({...}); return
-    X, Y = curve_state(curve, tk0, feed_ts); ...; buy = {...}
-    log({"ev": "trade_decision", ...})
-    h = submit(buy, "buy"); t_buy = time.time(); tokens = tk
+    n_buys = len(state["buys"].get(curve, ())); n_val = state["valtx_n"]
+    X, Y, tk, net, gross, fee, amount_in, min_out, buy = build(buys); signed = sender.sign(buy) if sender else None
+    if target is not None:
+        sleep_until(target)
+        if len(state["buys"].get(curve, ())) != n_buys or state["valtx_n"] != n_val:
+            buys = curve_buys(curve, feed_ts); X, Y, tk, net, gross, fee, amount_in, min_out, buy = build(buys); signed = sender.sign(buy) if sender else None
+    t_fire = time.time(); h = submit(buy, "buy", signed); t_buy = time.time(); tokens = tk
+    threading.Thread(target=score_launch, ...).start()
+    log({"ev": "trade_decision", ..., "fire_vs_target_ms": round((t_fire - target) * 1000, 2) if target else None, ...})

--- D5 ---
@@ -127,5 +129,12 @@
-def submit(tx, label):
-    log({"ev": "unsigned_tx", "label": label, "tx": tx})
-    return None
+def submit(tx, label, signed=None):
+    if sender is None:
+        log({"ev": "unsigned_tx", "label": label, "tx": tx}); return None
+    if signed is None:
+        signed = sender.sign(tx)
+    h, detail = sender.fire(signed)            # two sendall() calls, then both replies
+    log({"ev": "sent_tx", "label": label, "hash": h, **detail}); return h
 (Rpc.__init__/call: HTTPSConnection(self.host, timeout=10, context=_CTX) with one module-level context)

--- D6 ---
@@ -250,3 +262,5 @@
-    for seen, ts_, snd, val, data in list(state["valtx"]):
-        if cb in data:
+    for seen, ts_, snd, val, data in reversed(state["valtx"]):
+        if since_ts is not None and ts_ < since_ts:
+            break
+        if cb in data:

--- D7 / D12 ---
@@ -588,5 +628,6 @@
-            async with websockets.connect(FEED_URL, open_timeout=15, max_size=None, ping_interval=20) as ws:
-                log({"ev": "feed_connected"}); state["connected_at"] = time.time()
+            async with websockets.connect(FEED_URL, open_timeout=15, max_size=None, ping_interval=10, ping_timeout=5, compression=None) as ws:
+                log({"ev": "feed_connected"}); state["connected_at"] = time.time(); state["flips"].clear(); state["boundary"] = None
@@ -597,2 +638,4 @@
                         if ts:
+                            warm = seen - ts > 2.0
@@ -637 +680 @@
-            log({"ev": "feed_error", "err": str(e)[:200]}); await asyncio.sleep(2)
+            log({"ev": "feed_error", "err": str(e)[:200]}); await asyncio.sleep(0.2)

--- D8 ---
@@ -565 +609,3 @@
 def prune(now):
+    if state["pending"] == 0:
+        gc.collect()
@@ -580 +626,2 @@
+    gc.freeze(); gc.disable()

--- D9 ---
@@ -200,9 +246,14 @@
-        b = int(receipt["blockNumber"], 16); ts = int(rpc.call("eth_getBlockByNumber", [hex(b), False])["timestamp"], 16)
+        b = int(receipt["blockNumber"], 16); blk = rpc.call("eth_getBlockByNumber", [hex(b), True]); ts = int(blk["timestamp"], 16)
+        idx = int(receipt.get("transactionIndex", "0x0"), 16); curve = receipt["to"].lower()
+        ahead = sum(1 for t in blk["transactions"][:idx] if (t.get("to") or "").lower() == curve or curve[2:] in (t.get("input") or ""))
         if ts < seat_ts:
-            MARGIN_MS += 20; where = "early"
+            MARGIN_MS += 15; where = "early"
         elif prev < ts:
             where = "first block"
         else:
-            MARGIN_MS = max(5.0, MARGIN_MS - 5); where = "later block"
+            where = "later block"                       # -2 ms per 20 landings without an early one, floor 5 (section 6)
+        log({..., "tx_index": idx, "curve_buys_ahead_in_block": ahead, "blocks_after_flip": b - state["flip_block"].get(seat_ts, b), ...})

--- D11 ---
@@ -421,2 +421,4 @@
     curve = token = None; tk0 = None; b_create = None; src = None; named = set(named)
+    if SEAT in ("E1", "E2") and BUNDLE_MIN > 0 and (quote != ZERO or len(named) < BUNDLE_MIN):
+        log({"ev": "skip", "why": ["not a bundled native-ETH launch: no RPC resolution"], ...}); return

--- D12 ---
@@ -423,8 +425,11 @@
-        while state["feed_ts"] <= feed_ts and time.time() - seen_at < 1.5:
-            time.sleep(0.003)
-        cands = collections.Counter(); for cv, lst in list(state["buys"].items()): ...
+        cands = count()
+        while state["feed_ts"] <= feed_ts and time.time() - seen_at < 1.5 and (not cands or cands.most_common(1)[0][1] < BUNDLE_MIN):
+            time.sleep(0.003); cands = count()
```

Not latency but noticed: `tune_margin` (`:200-201`) makes two RPC calls per landing; fine off the critical path. `close_position`
(`:407-416`) signs at sell time; with D4 the approve and sell are signed at buy time and only sent later, which the runbook
already asks for.

## 9. Achievable landing position from Ohio, honestly

**Measured here**: the CPU side of the path after the diffs is 0.1-0.4 ms from target to wire; the estimator's residual is
jitter-bound (1.5-24 ms sd through this proxy, depending on the hour); the feed's first T+2 block reaches a reactive sender
50 ms (median) to 90-130 ms (p90) after the boundary; the sequencer front keeps connections open and serves
`eth_sendRawTransaction` to anyone.

**Inferred for a c6i.large in us-east-2 with a provider key**: feed delay d 2-10 ms (Cloudflare in the path; measurable on
day one as the p10 of arrival − block second on a chrony-synced box), uplink u 0.5-1.5 ms, σ_e ≤ 3 ms. With `MARGIN_MS`
15 -> 5-10: **first block of T+2 on 80-90% of launches, second block on most of the rest, second-one landings ≈ 0**. Inside
the first block we are behind whoever sent before the boundary and won the drain lottery: on chain the first T+2 buyer is in
the flip block on 27% of launches (report 21.5), so on roughly a quarter of launches someone can still be ahead of us in
that block; on the remainder we are the first T+2 buyer. That is ahead of the backtest's "0.3 s behind the first buyer" on
most launches, and about at it on the rest.

**The engine as it stands** (react mode, a submit built on `Rpc`): boundary + 50 ms (feed) + 5 ms (wake) + 2 ms (scans, sign)
+ 28-31 ms (connection) + u ≈ boundary + 85-110 ms median: block 2 of T+2, sometimes 3. That is roughly the backtest's
assumption, not better.

**What makes it worse**: (1) feed stalls — 1.2-1.4% of seconds here had the first block delivered > 300 ms late; a stall at
the T+1 flip delays the anchor, and beyond ~0.9 s the engine falls back to react (`predict-late`: 2 of 10 sends in v14 through
this proxy); (2) a shared or burstable core — every millisecond of scheduling jitter goes into σ_e and hence the floor margin
(the measured 5 ms GIL effect is the model: a 5 ms σ_e means a 15-20 ms floor and a first-block share near 70%);
(3) the provider — off the critical path after D5 except as the second send endpoint (+5-30 ms [I]), but its nonce/gas
freshness is a gate (`:489`), so a slow provider means no send at all; (4) Cloudflare between the box and the feed — a route
change moves d, which the estimator re-learns in ~60 flips (D7 clears on reconnect for that reason); (5) a second operator in
the seat — a capacity problem (report 22.1), not a latency one.

**Not verifiable from here**: absolute Ohio latencies, the sequencer's acceptance of a real signed transaction, provider
latency, the exact Nitro drain/timestamp order on the pinned version (section 6's model), and the true σ_e; the first 20
react-mode landings with D9's log fields are the measurement.

## 10. Files
`FINAL.md` (this), `sniper_engine_latency.diff` (D1-D12), `recover_fast.py`, `sender.py`, `capture_feed.py`,
`feed_capture.jsonl` / `feed_capture2.jsonl` (raw feed, 420 s / 210 s), `analyze_capture.py` -> `analyze_capture1.txt`,
`analyze_capture2.txt`, `capture_summary.json` (capture 1), `capture_summary2.json`, `est_compare.py` ->
`est_compare_capture1.txt`, `est_compare_capture2.txt`, `bench_decode.py`, `bench_lazy.py` -> `bench_lazy.out`,
`bench_wake.py`, `bench_send_path.py`, `keepalive_test.py` -> `keepalive.out`, `probe_run.out` / `latency_probe.json`
(the repository probe run here), `venv/` (websockets, rlp, eth-account, coincurve).
