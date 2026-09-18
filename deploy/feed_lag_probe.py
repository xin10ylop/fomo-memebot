#!/usr/bin/env python3
"""How far the sequencer feed trails the sequencer's clock, on this box: for every flip (the first message stamped with a new
second) the wall-clock arrival minus that second. The smallest values are the feed's delivery lag (a flip block sealed right
at the tick); the spread is the block cadence. Needs NTP (chrony) on the box: the number is only as good as the clock.

    sudo /opt/sniper-venv/bin/python3 deploy/feed_lag_probe.py [seconds]
"""
import asyncio, json, sys, time, statistics as st, subprocess
try:
    import websockets
except ImportError:
    raise SystemExit("run with the engine's interpreter: /opt/sniper-venv/bin/python3")
URL = "wss://feed.mainnet.chain.robinhood.com"; SECS = float(sys.argv[1]) if len(sys.argv) > 1 else 120
async def main():
    lags = []; last = 0; t_end = time.time() + SECS; n = 0
    async with websockets.connect(URL, open_timeout=10, max_size=None, ping_interval=10, ping_timeout=5, compression="deflate") as ws:
        while time.time() < t_end:
            raw = await asyncio.wait_for(ws.recv(), timeout=5.0); wall = time.time(); d = json.loads(raw)
            for m in d.get("messages", []):
                hdr = m["message"]["message"].get("header", {})
                ts = int(hdr.get("timestamp", 0) or 0) if int(hdr.get("kind", 0) or 0) == 3 else 0
                if not ts or wall - ts > 2.0:
                    continue
                n += 1
                if ts > last:
                    if last:
                        lags.append(1000 * (wall - ts))
                    last = ts
    try:
        chrony = subprocess.run(["chronyc", "tracking"], capture_output=True, text=True, timeout=5).stdout
        off = next((l.strip() for l in chrony.splitlines() if "System time" in l or "Last offset" in l), "chrony: no line")
    except Exception as e:
        off = f"chrony: {e}"
    if not lags:
        print("no flips seen"); return
    lags.sort(); q = lambda p: lags[int(p * (len(lags) - 1))]
    print(f"{len(lags)} flips in {SECS:.0f} s, {n} blocks; flip arrival minus its second, ms: p5 {q(0.05):.0f}  p10 {q(0.10):.0f}  p25 {q(0.25):.0f}  median {q(0.5):.0f}  p90 {q(0.9):.0f}")
    print(f"the feed's delivery lag on this box is about the p5-p10 value (a flip block sealed at the tick); {off}")
asyncio.run(main())
