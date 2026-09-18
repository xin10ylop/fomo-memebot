#!/usr/bin/env python3
"""    sudo /opt/sniper-venv/bin/python3 deploy/grid_probe.py [seconds]

are the sequencer's blocks on a fixed grid? arrival (wall) vs block number over N seconds: least-squares period and phase,
residuals, and the flip offsets (first block of each second: its predicted creation minus the second)."""
import asyncio, json, sys, time, statistics as st
import websockets
URL = "wss://feed.mainnet.chain.robinhood.com"; SECS = float(sys.argv[1]) if len(sys.argv) > 1 else 90
async def main():
    rows = []; t_end = time.time() + SECS
    async with websockets.connect(URL, open_timeout=10, max_size=None, ping_interval=10, ping_timeout=5, compression="deflate") as ws:
        while time.time() < t_end:
            raw = await asyncio.wait_for(ws.recv(), timeout=5.0); wall = time.time(); d = json.loads(raw)
            for m in d.get("messages", []):
                hdr = m["message"]["message"].get("header", {})
                ts = int(hdr.get("timestamp", 0) or 0) if int(hdr.get("kind", 0) or 0) == 3 else 0
                if not ts or wall - ts > 2.0: continue
                rows.append((int(m.get("sequenceNumber") or 0), wall, ts))
    rows = [r for r in rows if r[0]]; rows.sort()
    n0 = rows[0][0]; xs = [r[0] - n0 for r in rows]; ys = [r[1] - rows[0][1] for r in rows]
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    P = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs); A = my - P * mx
    res = [1000 * (y - (A + P * x)) for x, y in zip(xs, ys)]
    gaps = [rows[i][0] - rows[i-1][0] for i in range(1, n)]
    print(f"{n} blocks in {SECS:.0f} s; block numbers consecutive: {all(g == 1 for g in gaps)} (max gap {max(gaps)}); period {1000*P:.3f} ms")
    print(f"arrival residuals vs the grid, ms: std {st.pstdev(res):.1f}  p5 {sorted(res)[int(0.05*n)]:.1f}  median {st.median(res):.1f}  p95 {sorted(res)[int(0.95*n)]:.1f}")
    # residual autocorrelation: is the jitter per-block noise (delivery) or a wandering phase?
    d1 = [res[i] - res[i-1] for i in range(1, n)]
    print(f"consecutive-residual difference std {st.pstdev(d1):.1f} ms (about sqrt(2) x per-block noise if the phase is stable)")
    # local fit over the last 100 blocks: how well does it predict the next 10?
    errs = []
    for k in range(150, n - 10, 10):
        X = xs[k-100:k]; Y = ys[k-100:k]; mX = sum(X)/100; mY = sum(Y)/100
        p = sum((x-mX)*(y-mY) for x, y in zip(X, Y)) / sum((x-mX)**2 for x in X); a = mY - p*mX
        errs += [1000 * (ys[k+j] - (a + p * xs[k+j])) for j in range(1, 11)]
    if errs: print(f"prediction error 1-10 blocks ahead from a 100-block fit, ms: median {st.median(errs):.1f}  p5 {sorted(errs)[int(0.05*len(errs))]:.1f}  p95 {sorted(errs)[int(0.95*len(errs))]:.1f}")
    # flips: the first block of each second; its grid-predicted arrival minus the second (wall) = feed lag + slot offset
    flips = [(rows[i][0] - n0, rows[i][1], rows[i][2]) for i in range(1, n) if rows[i][2] > rows[i-1][2]]
    offs = [1000 * ((rows[0][1] + A + P * x) - ts) for x, w, ts in flips]
    print(f"{len(flips)} flips: grid arrival of the flip block minus its second, ms: min {min(offs):.0f} p10 {sorted(offs)[int(0.1*len(offs))]:.0f} median {st.median(offs):.0f} max {max(offs):.0f}  (spread should be about one period: the slot drifts across the second)")
    print("flip offsets in order (first 40):", [round(o) for o in offs[:40]])
asyncio.run(main())
