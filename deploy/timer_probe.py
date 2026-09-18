#!/usr/bin/env python3
"""    sudo /opt/sniper-venv/bin/python3 deploy/timer_probe.py [seconds]

Is block creation a strict timer? For every flip (the first message stamped with a new second) record the second and the block
number, then fit creation = c0 + n * P: for each candidate P the admissible c0 interval is the intersection of [S - nP, S - nP + P);
print the best width, the residual offsets (creation minus the second, should be in [0, P) and walk 16 ms a second), and, with a
least-squares alternative, the scatter of the flips around the line. Also how many blocks per second the feed delivered, and
whether numbers are consecutive."""
import asyncio, json, sys, time, statistics as st
try:
    import websockets
except ImportError:
    raise SystemExit("run with the engine's interpreter: /opt/sniper-venv/bin/python3")
URL = "wss://feed.mainnet.chain.robinhood.com"; SECS = float(sys.argv[1]) if len(sys.argv) > 1 else 180
async def main():
    flips = []; last = 0; nums = []; t_end = time.time() + SECS; kinds = {}
    async with websockets.connect(URL, open_timeout=10, max_size=None, ping_interval=10, ping_timeout=5, compression="deflate") as ws:
        while time.time() < t_end:
            raw = await asyncio.wait_for(ws.recv(), timeout=5.0); wall = time.time(); d = json.loads(raw)
            for m in d.get("messages", []):
                hdr = m["message"]["message"].get("header", {}); kind = int(hdr.get("kind", 0) or 0); kinds[kind] = kinds.get(kind, 0) + 1
                n = int(m.get("sequenceNumber") or 0); nums.append(n)
                ts = int(hdr.get("timestamp", 0) or 0) if kind == 3 else 0
                if not ts or wall - ts > 2.0: continue
                if ts > last:
                    if last: flips.append((ts, n, wall))
                    last = ts
    nums = [x for x in nums if x]; gaps = [nums[i] - nums[i-1] for i in range(1, len(nums))]
    print(f"{len(nums)} messages, kinds {kinds}; number gaps: {dict((g, gaps.count(g)) for g in sorted(set(gaps)))}")
    print(f"{len(flips)} flips; blocks per second between flips: {dict((g, [flips[i][1]-flips[i-1][1] for i in range(1,len(flips))].count(g)) for g in sorted(set(flips[i][1]-flips[i-1][1] for i in range(1,len(flips)))))}")
    best = None
    for i in range(0, 161):
        P = 0.1010 + 0.00001 * i
        xs = sorted(ts - n * P for ts, n, _ in flips); k = max(1, len(xs) // 40)
        lo, hi = xs[-1-k], xs[k] + P; w = hi - lo
        if best is None or w > best[0]: best = (w, P, lo, hi)
    w, P, lo, hi = best; c0 = (lo + hi) / 2
    print(f"intersection fit: best period {1000*P:.3f} ms, admissible c0 width {1000*w:.1f} ms ({'consistent' if w > 0 else 'EMPTY: not a strict timer at any period'})")
    offs = [1000 * (c0 + n * P - ts) for ts, n, _ in flips]
    print(f"creation minus the second at that fit, ms (should lie in [0, {1000*P:.0f}) and walk +16/s): min {min(offs):.1f} max {max(offs):.1f}")
    print("first 40:", [round(o, 1) for o in offs[:40]])
    # least squares on the flips: S ~ a + b n; residual spread = timer jitter plus the sawtooth (uniform 0..P): compare with P/sqrt(12)
    xs = [n for _, n, _ in flips]; ys = [ts for ts, _, _ in flips]; mx = sum(xs) / len(xs); my = sum(ys) / len(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs); a = my - b * mx
    res = [1000 * (y - (a + b * x)) for x, y in zip(xs, ys)]
    print(f"least squares: period {1000*b:.3f} ms; flip residual std {st.pstdev(res):.1f} ms (a perfect timer with a uniform sawtooth gives {1000*b/12**0.5:.1f})")
    # consecutive differences of the offsets: +16 (10 blocks) or -86 (9 blocks) on a strict timer; anything else is jitter
    d = [offs[i] - offs[i-1] for i in range(1, len(offs))]
    print("offset steps (first 40):", [round(x, 1) for x in d[:40]])
asyncio.run(main())
