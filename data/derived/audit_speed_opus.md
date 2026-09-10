# Speed research deliverable (Opus 5): measurements and proposed diffs

```
audit_speed_opus — measurements, 2026-09-09
Sandbox: far from Ohio, behind an HTTP proxy. Absolute network numbers do NOT transfer; CPU numbers,
cold-minus-warm gaps, poll granularity and the estimator RANKING do.
Feed capture: feed_capture.jsonl, 7 min, 2,559 frames, 4,079 L2 blocks, 43,716 transactions (190/s).

A. DECODE PATH (bench_decode.py, 300 real transactions)
   json.loads of a feed frame                      0.026 ms
   base64 + batch split per L2 payload             0.059 ms
   rlp parse_tx                                    7.4 us / tx  (~16 tx per message)
   Account.recover_transaction, NO coincurve     5,547 us
   Account.recover_transaction, coincurve          411 us
   raw coincurve fast_sender (proposed)            107 us   (50/50 identical to eth-account)
   -> report section 21.2's "about 70 us each" is wrong by ~6x even with coincurve.

B. THE FEED LOOP AS WRITTEN (bench_loop.py, 223 s replay)
   190 tx/s, 29 signature recoveries/s, of which 693 direct buys / 5,765 router / 50 creations
                                 median   p90    p99     max    loop busy
     with coincurve               0.85   1.99   4.51   16.82     1.3%
     without coincurve           11.11  29.74  79.29  208.53    17.1%
   This is also the jitter the engine injects into its OWN boundary estimator: message N's decode delays
   message N+1's arrival stamp.

C. POST-BOUNDARY WORK (bench_loop.py, bench_sign.py)
   curve_buys() over a full 4,000-entry valtx deque       1.10-1.32 ms
   curve_state() (calls curve_buys again)                 1.11-1.27 ms   -> 2.2-2.6 ms, twice per trade
   list(deque(4000)) copy                                 0.013-0.020 ms
   size_buy + build the tx dict                           0.0024 ms
   log(): open + json.dumps + write + close               0.019 ms
   threading.Thread create+start                          0.098 ms
   Account.sign_transaction                               0.351 ms
   to_checksum_address                                    0.020 ms
   json body for eth_sendRawTransaction                   0.003 ms

D. SEAT-WAIT GRANULARITY (bench_wait.py, 150 trials each, overshoot past the target)
                                       median   p90    p99    max
     while ...: time.sleep(0.001)       0.85   1.06  15.76  19.96   (engine, predict branch)
     while ...: time.sleep(0.002)       1.18   1.96   2.06   2.07   (engine, react branch)
     sleep to T-2ms then spin           0.00   0.001  1.34   2.68
     same, under decode load            0.00   0.001  0.015  0.33   (proposed)

E. CONNECTION (bench_net.py; proxy-inflated, read the COLD-WARM gap)
   sequencer : cold 70-272 ms, warm keep-alive median 33.9 ms, p90 41.0  -> cold-warm 87.0 ms
   public RPC: cold 107-206 ms, warm median 51.7 ms, p90 73.8           -> cold-warm 133.3 ms
   The provider/public RPC is 18 ms slower warm-to-warm than the sequencer here: consistent with one extra hop.

F. THE CHAIN'S CLOCK, FROM THE FEED (bench_boundary2.py, clean seconds only)
   block cadence           median 99.0 ms (p10 60.1, p90 133.0)
   blocks per second       median 10
   per-second bracket width (a_first(s) - a_last(s-1))  median 98.3 ms, p90 127.9 ms  = one block, as modelled

G. BOUNDARY ESTIMATORS (train on the first half of the capture, score on the held-out half;
   "consistent" = the estimate falls inside that second's observed bracket)
     estimator                                 consistent  too early  too late   margin for <=5% early
     engine: 2nd pct of flip arrivals             66.1%      32.2%      1.8%          40 ms
     plain minimum of flip arrivals               59.6%      39.8%      0.6%          >60 ms
     median of flip arrivals - cadence/2          73.1%      24.6%      2.3%          40 ms
     all blocks, p05 of (arrival - k*cadence)     75.4%      18.1%      6.4%          25 ms
     BRACKET MID (p98 lower, p02 upper)           75.4%      14.0%     10.5%       15-20 ms
   rolling stability over 100-second windows (sd): bracket-mid 13.5 ms, min 12.4, engine 18.1, med-cad 18.5.
   The ~75% ceiling is this sandbox's proxy jitter, not the estimators.

H. THE PRICE OF A MILLISECOND (from the report's own tables, sections 2 / 2b of the runbook, 10 windows)
   E2 front vs E2 0.3 s behind          +2.92 pp   (= 0.97 pp per 100 ms)
   E2 front vs E2 one block behind      +1.73 pp
   E2 one block behind vs 0.3 s behind  +1.19 pp
   landing a second early (E1 behind) vs E2 front   -4.40 pp
   break-even early rate for one extra block of margin: 39%
   => margin is cheap, earliness is expensive but not catastrophic; the controller should be one-sided.

I. CONFIRMED LANDMINE
   eth_account.Account.sign_transaction rejects the engine's lowercase `to`:
     TypeError: Transaction had invalid fields: {'to': '0xabab…'}
   The first live submit() would raise and lose the trade.

Proposed latency diffs for src/strategy/sniper_engine.py (NOT APPLIED — review copy)
audit_speed_opus, 2026-09-09. Every "saves" number is measured on this sandbox unless marked (inferred).
Measurement scripts in this folder: bench_decode.py, bench_loop.py, bench_wait.py, bench_net.py,
bench_boundary2.py, bench_margin.py, bench_sign.py; raw feed capture in feed_capture.jsonl (7 min, 4,079 blocks).

=====================================================================================
D1  line 629 (and 614) — sender recovery for every value-carrying transaction, on the event loop
=====================================================================================
88.6% of all signature recoveries (5,765 of 6,508 in a 223 s replay) are router transactions whose sender is
only ever read if that transaction turns out to name a curve we care about. Recovering them inline costs
411 us each with coincurve and 5,547 us without, ON THE ASYNCIO LOOP, so it delays the next `ws.recv()` and
therefore the arrival stamp of the next block — the input of the boundary estimator.

measured per-message handling, 223 s replay of the real feed (190 tx/s):
                       median   p90    p99    max   loop busy
  as written, coincurve  0.85   1.99   4.51  16.82    1.3%
  as written, no coincurve 11.11 29.74 79.29 208.53   17.1%
  with D1+D2 (est.)     ~0.15  ~0.30  ~0.60  ~2.0    ~0.2%

--- a/src/strategy/sniper_engine.py
+++ b/src/strategy/sniper_engine.py
@@ -604,6 +604,6 @@ (inside the per-transaction loop of main())
-                                if sel == BUY_SEL:                                                       # direct curve buy
-                                    snd = Account.recover_transaction(t).lower()
-                                    state["buys"][to_hex].append((ts, snd, val, seen)); continue
+                                if sel == BUY_SEL:                                                       # direct curve buy
+                                    # sender is needed to match the creator's named list: recover now, but with
+                                    # the raw coincurve path (D2). 693 of 6,508 recoveries; the rest go lazy.
+                                    state["buys"][to_hex].append((ts, fast_sender(t), val, seen)); continue
@@ -629,3 +629,6 @@
-                                if val > 0 and len(data) >= 36:                                         # a router buy of some curve
-                                    snd = Account.recover_transaction(t).lower(); state["valtx"].append((seen, ts, snd, val, bytes(data)))
+                                if val > 0 and len(data) >= 36:                                         # a router buy of some curve
+                                    # LAZY: keep the envelope, recover the sender only if this transaction is
+                                    # later found to name a curve we are trading (curve_buys below).
+                                    state["valtx"].append([seen, ts, None, val, data, t])   # data is already a bytes slice: no copy
@@ -247,10 +247,14 @@ def curve_buys(curve, since_ts=None):
-    cb = bytes.fromhex(curve[2:]); out = list(state["buys"].get(curve, []))
-    for seen, ts_, snd, val, data in list(state["valtx"]):
-        if cb in data:
-            out.append((ts_, snd, val, seen))
+    cb = bytes.fromhex(curve[2:]); out = list(state["buys"].get(curve, []))
+    for e in state["valtx"]:                       # no list() copy: the deque is only appended to by one thread
+        if cb in e[4]:
+            if e[2] is None:                       # recover the sender only for the handful that name this curve
+                e[2] = fast_sender(e[5])
+            out.append((e[1], e[2], e[3], e[0]))
     if since_ts is not None:
         out = [b for b in out if b[0] >= since_ts]
     return out

`bytes(data)` at line 629 also copies every router calldata (4.4 MB resident across the 4,000-entry deque);
rlp already hands back an immutable bytes slice, so the copy is pure waste and pure GC pressure.

=====================================================================================
D2  new helper — replace eth_account.Account.recover_transaction with raw coincurve
=====================================================================================
measured, 300 real transactions from the feed:
  Account.recover_transaction, no coincurve  5,547 us
  Account.recover_transaction, coincurve       411 us
  fast_sender below (coincurve, no eth-account object churn)   107 us   <-- 3.8x faster than the best of the two
  agreement with Account.recover_transaction on 50 sampled transactions: 50/50 identical.
NOTE the report (21.2) claims "about 70 us each". That is wrong by 6x even with coincurve installed.

+from eth_utils import keccak
+from coincurve import PublicKey
+
+def fast_sender(t):
+    """sender of a legacy / type-1 / type-2 envelope: 107 us, vs 411 us for eth_account (measured)"""
+    if t[0] >= 0xc0:                                   # legacy
+        b = rlp.decode(t); v = int.from_bytes(b[6], "big")
+        if v >= 35:
+            cid = (v - 35) // 2; rec = (v - 35) % 2
+            unsigned = rlp.encode(b[:6] + [cid.to_bytes((cid.bit_length() + 7) // 8 or 1, "big"), b"", b""])
+        else:
+            rec = v - 27; unsigned = rlp.encode(b[:6])
+        h = keccak(unsigned); r, s = b[7], b[8]
+    else:                                              # typed
+        b = rlp.decode(t[1:]); r, s = b[-2], b[-1]
+        rec = int.from_bytes(b[-3], "big") or 0
+        h = keccak(bytes([t[0]]) + rlp.encode(b[:-3]))
+    sig = r.rjust(32, b"\0") + s.rjust(32, b"\0") + bytes([rec])
+    return "0x" + keccak(PublicKey.from_signature_and_message(sig, h, hasher=None).format(compressed=False)[1:])[-20:].hex()
+
+# and at startup, refuse to run blind:
+from eth_keys import KeyAPI
+_backend = KeyAPI().backend.__class__.__name__
+if "CoinCurve" not in _backend:
+    raise SystemExit(f"eth-keys is using {_backend}: signature recovery is 5.5 ms instead of 0.1 ms. pip install coincurve.")

=====================================================================================
D3  lines 168-190 wait_for_second — sleep-poll granularity on the last stretch before the send
=====================================================================================
measured overshoot past the target instant (150 trials each, worker thread, 20 ms horizon):
                                   median    p90     p99     max
  while ...: time.sleep(0.001)      0.85    1.06   15.76   19.96   <-- as written (predict branch)
  while ...: time.sleep(0.002)      1.18    1.96    2.06    2.07   <-- as written (react branch)
  sleep to T-2ms then spin          0.00    0.001   1.34    2.68   (idle)
  sleep to T-2ms then spin, loaded  0.00    0.001   0.015   0.33   <-- proposed
saves ~0.85 ms median and a 2-16 ms tail, per send.

@@ -168,26 +168,32 @@ def wait_for_second(...):
-        if feed_ts + 1 in state["flip_at"] and ph is not None:
-            f1 = state["flip_at"][feed_ts + 1]; edge = f1 - ((f1 - ph) % 1.0)
-            target = edge + (seconds - 1) + MARGIN_MS / 1000.0
-            while time.time() < target and state["feed_ts"] < target_ts and time.time() - seen_at < deadline:
-                time.sleep(0.001)
+        if feed_ts + 1 in state["flip_at"] and ph is not None:
+            f1 = state["flip_at"][feed_ts + 1]; edge = f1 - ((f1 - ph) % 1.0)
+            target = edge + (seconds - 1) + MARGIN_MS / 1000.0
+            # coarse wait, then a spin: sleep() wakes 0.85 ms late at the median and 16 ms late at p99
+            while state["feed_ts"] < target_ts and time.time() - seen_at < deadline:
+                d = target - time.time()
+                if d <= 0.0:
+                    break
+                if d > 0.004:
+                    time.sleep(d - 0.004)          # one sleep, not a poll: no repeated wakeups
+                # else: spin on the clock for the last 4 ms
Also: `time.sleep(0.002)` at line 189 (the react branch) is the *entire* react latency budget — replace with the
same construction watching state["feed_ts"], or better an Event set by the feed loop on each flip (0 poll latency).

=====================================================================================
D4  lines 463 and 499 — the curve state is rebuilt twice, after the boundary, by scanning 4,000 calldatas
=====================================================================================
measured with a full 4,000-entry valtx deque (4.4 MB of calldata):
  curve_buys()   1.10 - 1.32 ms      curve_state() (which calls curve_buys again)  1.11 - 1.27 ms
  => 2.2 - 2.6 ms of substring scanning between the boundary and the send, every trade.
Both calls are after wait_for_second returns (line 461), i.e. squarely on the critical path.

@@ -461,6 +461,6 @@
     send_mode = wait_for_second(feed_ts, SEAT_SECONDS[SEAT], seen_at)
-    buys = curve_buys(curve, feed_ts)
+    buys = _buys_cache                                  # see below: computed once, before the boundary
@@ -497,3 +497,3 @@
-    X, Y = curve_state(curve, tk0, feed_ts); stake_eth = stake_usd / state["eth_usd"]
+    X, Y = _XY_cache                                    # see below
+
Structure: maintain the curve's reserves incrementally. When a curve becomes "watched" (the bundle match
succeeds, inside second T), register it in state["watch"][curve] = {"X":..,"Y":..,"buys":[..]}; the feed loop
then folds each new buy/sell of that curve into X,Y as it decodes it (a dozen float ops, ~1 us) instead of
replaying the history after the boundary.  Post-boundary work becomes: read two floats.
saves 2.2 - 2.6 ms measured.
If the incremental version is too big a change, the minimum fix is to compute buys/X/Y ONCE, just before
wait_for_second, and refresh only from the buys seen during the wait — the same 2.4 ms off the critical path.

=====================================================================================
D5  line 496 — a thread is created for the scorer between the boundary and the send
=====================================================================================
measured: threading.Thread(...).start() = 98 us. It runs `time.sleep(25)` first: nothing about it is urgent.
@@ -496,1 +496,0 @@
-    threading.Thread(target=score_launch, args=(...), daemon=True).start()
@@ -507,0 +508,1 @@  (immediately AFTER `h = submit(buy, "buy")`)
+    threading.Thread(target=score_launch, args=(...), daemon=True).start()
saves 0.10 ms.

=====================================================================================
D6  line 504 — the decision log (open + json.dumps + write + close) runs before submit()
=====================================================================================
measured: 18.9 us for the open/write/close of that record on a warm page cache; unbounded if the log's
filesystem hiccups (EBS gp3 p99 write latency is milliseconds), and it is the only unbounded syscall left
between the boundary and the send.
@@ -504,4 +504,4 @@
-    log({"ev": "trade_decision", ...})
-    h = submit(buy, "buy"); t_buy = time.time()
+    h = submit(buy, "buy"); t_buy = time.time()
+    log({"ev": "trade_decision", ..., "t_send_perf": t_send, "t_target_perf": target})
Better: replace log() globally with a queue.SimpleQueue + one writer thread (put() is ~1 us and never blocks).
The same applies to log({"ev":"creation"}) at line 626, which sits between decoding the creation and starting
the thread that will trade it.
saves 0.02 ms typical, removes an unbounded tail.

=====================================================================================
D7  submit() (line 122) — nothing is pre-signed, and the transaction as built cannot be signed at all
=====================================================================================
(a) CORRECTNESS LANDMINE, verified: eth_account rejects the engine's transaction dict —
      Account.sign_transaction({... "to": "0xabab...ab" ...})
      TypeError: Transaction had invalid fields: {'to': '0xabab…'}
    because `curve` is built as "0x" + to.hex() (lowercase, line 611) and eth-account demands a checksummed
    address or bytes. The first live send would raise inside submit() and lose the trade. to_checksum_address
    costs 20 us — do it once when the curve is resolved, not at send time.
(b) measured signing cost on the critical path: Account.sign_transaction = 351 us; json body for
    eth_sendRawTransaction = 2.9 us; http.client header formatting ~30 us.
(c) Everything the buy needs is known ~1 s before the T+2 boundary: nonce and gasPrice come from the
    background chain_loop, gas is a constant, the curve address is known inside second T, and the size
    depends only on the curve state, which can be frozen at the T+1 flip (SLIP is 25%; a 100 ms-old size is
    far inside that). So the whole raw transaction can be signed and serialised before the boundary.

+class Prepared:
+    """everything for the buy, built and signed when the T+1 flip is seen; at the boundary only sendall() runs"""
+    __slots__ = ("body", "hash", "amount_in", "min_out", "tokens")
+
+def prepare_buy(curve_cs, nonce, gas_price, X, Y, stake_eth, seat):
+    tk, net, gross, fee = size_buy(X, Y, stake_eth, seat)
+    amount_in = int(gross * 1e18); min_out = int(tk * (1 - SLIP) * 1e18)
+    tx = {"to": curve_cs, "value": amount_in, "data": bytes.fromhex(BUY_SEL.hex() + abi_word(amount_in) + abi_word(min_out) + abi_word(WALLET)),
+          "gas": GAS_BUY, "gasPrice": gas_price, "nonce": nonce, "chainId": 4663}
+    raw = ACCT.sign_transaction(tx)                                  # 351 us, ~1 s before the boundary
+    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_sendRawTransaction", "params": ["0x" + raw.raw_transaction.hex()]}).encode()
+    p = Prepared(); p.body = body; p.hash = raw.hash.hex(); p.tokens = tk; return p
Optionally sign a small ladder (reserves x1.0 / x1.15 / x1.30 / x1.50, 4 x 351 us, still ~1 s early) and pick
the matching one at the boundary if the price moved more than expected during the last second.
saves 0.40 ms and removes the TypeError that would kill the first live trade.

=====================================================================================
D8  submit() — no warm connection, no second endpoint
=====================================================================================
measured, this sandbox (proxy-inflated, but the COLD-minus-WARM gap is the transferable number):
  sequencer  : cold connect+request 70-272 ms ; warm keep-alive request median 33.9 ms ; cold-warm = 87.0 ms
  public RPC : cold connect+request 107-206 ms ; warm median 51.7 ms                    ; cold-warm = 133.3 ms
In Ohio the same structure costs DNS (0-20 ms) + TCP (1 RTT) + TLS1.3 (1 RTT) + cert verify (1-3 ms)
= 4-10 ms (inferred). Today `Rpc` keeps connections in threading.local() (line 67) and handle_creation runs
in a NEW thread per launch, so the first RPC call of every launch pays a full handshake.

+class Sender:
+    """two pre-opened, pre-warmed TLS sockets; the boundary path is one sendall() per socket"""
+    def __init__(self, urls):
+        self.eps = []
+        for u in urls:
+            p = urllib.parse.urlparse(u)
+            self.eps.append({"host": p.netloc, "path": p.path or "/", "c": None, "hdr": None})
+        self._connect_all(); threading.Thread(target=self._keepalive, daemon=True).start()
+    def _connect_all(self):
+        for e in self.eps:
+            try:
+                c = http.client.HTTPSConnection(e["host"], timeout=5)
+                c.request("POST", e["path"], body=b'{"jsonrpc":"2.0","id":0,"method":"eth_chainId","params":[]}', headers=UA)
+                c.getresponse().read(); e["c"] = c
+            except Exception:
+                e["c"] = None
+    def _keepalive(self):
+        while True:                       # every 5 s: below any idle timeout, keeps the TLS session hot
+            time.sleep(5)
+            for e in self.eps:
+                try:
+                    e["c"].request("POST", e["path"], body=b'{"jsonrpc":"2.0","id":0,"method":"eth_chainId","params":[]}', headers=UA); e["c"].getresponse().read()
+                except Exception:
+                    self._connect_all()
+    def fire(self, body):
+        """send the SAME signed transaction to both endpoints; identical hash, so a double landing is impossible"""
+        out = []
+        for e in self.eps:
+            threading.Thread(target=self._one, args=(e, body, out), daemon=True).start()
+        return out
+
+SENDER = Sender([os.environ.get("SEQ_URL", "https://sequencer.mainnet.chain.robinhood.com"), RPC_URL])
Order matters: the sequencer is the admission point; a provider RPC forwards to it, so it is strictly one hop
further. Make the sequencer endpoint 0 and the provider endpoint 1. NEVER put the public Cloudflare RPC on the
send path (rate limits and challenge pages).
saves 4-10 ms in Ohio (inferred), 87-133 ms here (measured).

=====================================================================================
D9  lines 156-166 boundary_phase() — a one-sided estimator that throws away half the information
=====================================================================================
Each second gives a TWO-SIDED bracket on the boundary: the last block stamped s-1 was produced before it and
the first block stamped s was produced at or after it, so
      theta  in  ( a_last(s-1) - s ,  a_first(s) - s ].
The engine only uses the upper side (the 2nd percentile of a_first), which is a minimum-statistic: it is
dragged by whichever delivery happened to be fastest, and it is systematically early.
measured on the 7-minute capture (clean seconds only; train on the first half, score on the held-out half,
"consistent" = the estimate lies inside that second's observed bracket):
    estimator                                 consistent   too early   too late
    engine, 2nd pct of flip arrivals             66.1%       32.2%       1.8%
    plain minimum of flip arrivals               59.6%       39.8%       0.6%
    median of flip arrivals - cadence/2          73.1%       24.6%       2.3%
    all blocks, p05 of (arrival - k*cadence)     75.4%       18.1%       6.4%
    BRACKET MID (p98 of lower, p02 of upper)     75.4%       14.0%      10.5%   <-- proposed
  and the margin each needs to reach a <=5% early rate: engine 40 ms, median-cadence 40 ms, allblocks 25 ms,
  bracket-mid 15-20 ms. That is 20-25 ms of head start inside the block at the same risk.
  rolling stability (100-second windows): bracket-mid sd 13.5 ms vs engine 18.1 ms.
  supporting numbers: cadence median 99.0 ms (p10 60, p90 133), 10 blocks per second, bracket width median
  98.3 ms = exactly one block, as the model predicts.

-def boundary_phase():
-    ph = sorted(t % 1.0 for t in state["flips"])
-    if len(ph) < 30: return None
-    gaps = [(ph[(i + 1) % len(ph)] - ph[i]) % 1.0 for i in range(len(ph))]
-    k = max(range(len(ph)), key=lambda i: gaps[i]); base = ph[(k + 1) % len(ph)]
-    rot = sorted((x - base) % 1.0 for x in ph)
-    return (base + rot[int(0.02 * len(rot))]) % 1.0
+_phase_cache = {"at": 0.0, "v": None, "width": None}
+def boundary_phase():
+    """two-sided bracket estimator, cached for 1 s (the old one re-sorted 600 floats on every call)"""
+    if time.time() - _phase_cache["at"] < 1.0:
+        return _phase_cache["v"]
+    up = sorted(state["flip_hi"]); dn = sorted(state["flip_lo"])       # (arrival - ts) for the first block of s
+    if len(up) < 60 or len(dn) < 60:                                    # and for the last block of s-1
+        return None
+    hi = up[int(0.02 * len(up))]; lo = dn[int(0.98 * len(dn))]
+    v = ((lo + hi) / 2.0) % 1.0; _phase_cache.update(at=time.time(), v=v, width=hi - lo)
+    return v
The feed loop keeps both sides: on a flip to ts, append (seen - ts) to flip_hi and (prev_seen - ts) to flip_lo,
and skip the second entirely if it carried fewer than 5 blocks or its delay is more than 3 sigma off the
rolling median (a stall or a reconnect burst). Log `width`: if it is far above one block, the box or the
feed is jittering — fall back to react and say so.

=====================================================================================
D10 lines 199-208 tune_margin — the controller can only go up
=====================================================================================
As written: early +20 ms, later-block -5 ms, FIRST BLOCK -> no change. Once the margin is large enough to stop
landing early it stops landing in later blocks too only by luck; there is no downward pressure from the
first-block case, so the margin sticks wherever it first stopped being early and never comes back down.
Make it a one-sided quantile controller targeting P(early) = 1%:
-        if ts < seat_ts:
-            MARGIN_MS += 20; where = "early"
-        elif prev < ts:
-            where = "first block"
-        else:
-            MARGIN_MS = max(5.0, MARGIN_MS - 5); where = "later block"
+        STEP = 12.0; TARGET_EARLY = 0.01
+        if ts < seat_ts:                                  # landed in T+1: paid +6.18%
+            MARGIN_MS = min(45.0, MARGIN_MS + STEP); where = "early"
+        elif prev < ts:                                   # first block of the seat's second: creep down slowly
+            MARGIN_MS = max(8.0, MARGIN_MS - STEP * TARGET_EARLY / (1 - TARGET_EARLY)); where = "first block"
+        else:                                             # a later block: come down fast
+            MARGIN_MS = max(8.0, MARGIN_MS - STEP / 2); where = "later block"
The fixed point of +12 on 1% of samples and -0.121 on 99% is the 99th percentile of the early tail, which is
the definition of "as close to the boundary as this box can get without landing in T+1". Floor 8 ms (the box's
own send jitter), cap 45 ms (half a block: past that the gain from being first is swamped by falling into
block 2). Note tune_margin also makes TWO blocking RPC calls (lines 200-201) inside the buy path; move it to
the scorer thread.

=====================================================================================
D11 line 588 / main() — connection and process discipline
=====================================================================================
-            async with websockets.connect(FEED_URL, open_timeout=15, max_size=None, ping_interval=20) as ws:
+            async with websockets.connect(FEED_URL, open_timeout=10, max_size=None,
+                                          ping_interval=10, ping_timeout=10, max_queue=1,
+                                          compression=None) as ws:      # max_queue: never hand us a stale frame
  * ping_interval=20 with the default ping_timeout means a dead feed is noticed after up to 40 s. Blocks come
    every ~99 ms: add a watchdog that reconnects if no message has arrived for 2 s.
  * max_queue defaults to 32: under a decode stall the library buffers frames and `seen = time.time()`
    (line 591) then stamps a stale block with the current time — poisoning exactly the estimator that decides
    the send. With max_queue=1 backpressure shows up as a lost connection instead of a silent lie.
  * compression=None: permessage-deflate costs CPU on every frame for a payload that is already base64.
+import gc, sys
+sys.setswitchinterval(0.0005)     # the sender thread must not wait a 5 ms GIL quantum behind the decoder
+gc.collect(); gc.freeze(); gc.disable()   # 4,000 calldata blobs: a gen-2 pass is milliseconds
+try:
+    import uvloop; uvloop.install()
+except ImportError:
+    pass
+os.sched_setaffinity(0, {1})      # keep core 0 for interrupts; run the sender thread with SCHED_FIFO
Record arrival stamps with time.perf_counter() (monotonic) and convert to wall clock once per second: a chrony
step during the seat wait currently moves the send by the size of the step.
```
