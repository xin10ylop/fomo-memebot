# J: would a Rust/C++ rewrite improve results?

**[M]** repo-measured, **[C]** code, **[S]** measured here (sandbox VM, Python 3.11; ratios transfer, absolute times do not), **[E]** estimate. Bare line numbers are `sniper_engine.py`.

## 1. Critical-path budget (creation seen to first post-tick shot landed)

| step | time | who | basis |
|---|---|---|---|
| creation block to frame on box | 81-93 ms (p5-p10), ~140 ms spread | sequencer | [M] REPORT.md:2656 |
| decode, launch thread started | 0.3-0.5 ms | us | [M] audit_speed_opus.md:10-15 |
| bundle visible | 0, or +101.6 ms a block | launch team | [M] REPORT.md:3389 |
| curve by receipt, cold TLS every launch | 5-30 ms | us, provider | [C] 1717-1728, 257-261; [M] REPORT.md:1526; [E] |
| scans before the watch registers | 2-4 ms | us | [C] 1733-1760, 900-933; [M] audit_speed_opus.md:27 |
| wait to the predicted tick | by design; vote sd 6-25 ms, ramp tails ±70 ms | sequencer clock | [M] REPORT.md:1528, 2669 |
| sign 35 shots, from burst_at − 82.5 ms | 12 ms; 23 [S]; ~50 live | us | [C] 1911; [M] REPORT.md:3358 |
| gate: 2 fleets by t_first + 36 ms | feed lag, then decode (section 2b) | feed, then us | [C]+[S] |
| write one shot | 0.1 ms | us | [M] REPORT.md:3536 |
| box to sequencer | ~0.7 ms (1.4 ms RTT) | network | [M] REPORT.md:2630 |
| first post-tick shot after the tick | 0 to 3-4 ms (the step) | us (gas) | [C] send_step.py:50-64 |
| ordering and intake | FCFS; 20-50 rival txs in 3 ms; reply 104 ms median, 386-1,460 ms on 886-2,056 rival shots; 1 in 20 held ~1 s | sequencer | [M] REPORT.md:2688-2690, 3540-3545 |

## 2. The interpreter's share

**Premises to correct:**
- The switch interval is 0.5 ms: line 2410 resets line 38.
- One thread writes all 35 shots in sequence (send_step.py:50-64). A reader thread starts after each write (385), and 35 receipt pollers start after the burst (1327), each on a cold TLS connection.
- gc is already frozen and disabled (2447, 2160).
- Between shots the sender **busy-spins holding the GIL** (send_step.py:52-55; the paper run too, 1977-1980). That covers the whole burst, and so the whole 36 ms gate.

**(a) Registration.** Mostly not the interpreter: it waits for the bundle's block (~100 ms each) and, for helper bundles, an RPC receipt on a new cold connection (the warm-socket fix covered `SENDER` only). Python adds 2-4 ms [E]. It matters only when registration lands within milliseconds of a frame; then GIL interleaving decides (REPORT.md:3806-3809). The blind window prices as a helpful filter (REPORT.md:3775-3779). Check: `resolve_ms − bundle_wait_ms` by `resolve_src`, `seq_watch − b_create`.

**(b) The k-1 view.** In `crowd_raw` (760 launches), 116 (15%) reach 2 fleets only inside block k-1. The deciding transaction sits at index 9 (median; p90 28), with 2 (p90 14) curve-naming transactions ahead of it.

Each naming shot's sender is recovered **2-3 times** (961/966, then 2208 or 2217-2218). Fleets need none of those recoveries for a relay shot; 6.3 added them for the wallets count (966). Cost to reach the deciding transaction when idle: mean 1.2 ms, p90 3.2 ms, max 11 ms [C+M].

Beside the spinning sender [S], an 18-shot frame:
- takes 4-7 ms alone;
- takes 9-16 ms pinned;
- takes 45-53 ms unpinned (a GIL convoy: each coincurve or keccak call releases the GIL and waits a switch interval to get it back);
- takes 0.2-0.4 ms with no recovery.

The k-1 arrivals spread over ~200 ms around the close, so a 3-4 ms mean delay costs **~1-3% of fires** [E].

**(c) Send jitter.** Unpinned, shots are punctual (p99 0.3-0.5 ms [S]). `PIN_CPU=1` (2407) puts the feed loop and the sender on one vCPU, since `sched_setaffinity(0)` pins the calling thread and later threads inherit it. Shots then go late whenever the decoder is busy: **p90 2 ms, p99 6 ms** [S]. Near the tick, block k carries 66 naming shots at p90, 261 at p99 (`D/shots_part.jsonl`). The rivals arrive at 7-17 transactions per ms, so 2 ms separates second place from the wave. One live burst read "on time" (REPORT.md:3536). A c6i/c7i.large is one core, two hyperthreads (AWS), not "two dedicated cores" (ohio_setup.sh:3).

**(d) The sell.** The trigger is 9 feed blocks after `blocks_at_fill` (2093), which is read only after the receipts settle. Three serial RPCs follow (1458, 1410, 1383). Python adds 0.35 ms of signing plus the backlog of post-tick frames with 3 recoveries per shot: ~20 ms at p90, ~70 ms at p99 [E]. Returns are flat across blocks 9-13 (REPORT.md:3786), so no P&L effect.

## 3. Verdict

A rewrite would not change the seat in a typical burst. It might add **2-5% of gross P&L** [E]: fires regained at the gate, fewer late decisive shots on busy launches. Python can reach nearly all of it:

1. **Skip relay-shot sender recovery in the gate path.** Count fleets by `to_hex`, recover wallets after the burst, cache one sender per transaction. Frame cost goes from 4-7 ms to 0.2-0.4 ms [S]. Largest gain.
2. **No GIL spin.** Sleep to ~0.3 ms before each shot, or call `time.sleep(0)` inside the spin (removed the convoy [S]). Or run a sender subprocess on its own vCPU, with the gate passed through shared memory.
3. **Two physical cores.** A c7a.large (no SMT, per AWS), with feed and sender in separate processes on separate cores. Never pin two GIL threads to one vCPU.
4. **Sign directly with coincurve.** 35 shots take 4.3 ms instead of 23 ms [S], so the build can move ~70 ms later. The P&L sign of a fresher minOut is unknown.
5. **Warm `rpc_seat` connection:** registration 4-10 ms sooner.
6. **Pre-read balance and nonce during the hold, and fire a pre-signed sell:** 10-30 ms sooner [E], no P&L effect.
7. **Sockets:** nothing to gain. TCP_NODELAY is set (300); headers and body are two writes (http/client.py:1069-1117), microseconds.

## 4. What the claim gets wrong or misses

- **"In C underneath":** signing, RLP and HTTP are Python, and the gate path recovers each shot 2-3 times.
- **"Inside the feed's jitter":** jitter does not absorb a systematic delay, which shifts the k-1 cutoff by delay/spread. Right conclusion, wrong reason.
- **"Sending faster would not help":** true for a uniform shift. The pinned-core lateness is not uniform: it lands on busy launches, which pay best (six or more others +49%, REPORT.md:2588). The step matters more than the language, and Python can already write about 0.2 ms a shot.
- **Brief numbers the repo does not support:** the reply median is 104 ms, not 93; "shot 30-33" was an aim offset (SNIPER_RUNBOOK.md:546), not rival pressure.

**The claim is wrong if, on busy launches:**
- `sent_burst.late_ms` exceeds ~1 ms near the fill shot and those fills sit deeper (`burst_landing.shots[].tx_index` against rival events per curve);
- decisions close mid-frame (`feed_block_at_open − blk0 > seq_at_open − b_create`) with `fleets_at_open < 2` while the chain shows 2 or more;
- `sent_burst.sign_ms` or `late_ms[0]` show signing overruns.

No per-frame decode time is logged; that field would settle (b).
