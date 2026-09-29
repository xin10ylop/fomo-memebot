#!/usr/bin/env python3
"""Two connections to the sequencer feed at once: does the second one deliver first often enough to be worth keeping?
The feed's broadcaster iterates its clients in random order per message (nitro wsbroadcastserver), so two sockets from one
box see each message in a different order; the engine could index whichever arrives first. This probe opens two sockets,
stamps every L2 message (by sequence number) on each, and reports how often B beats A and by how much the earlier-of-two
beats a single socket.

    sudo /opt/sniper-venv/bin/python3 deploy/feed_dual_probe.py [seconds]
"""
import asyncio, json, sys, time, statistics as st
try:
    import websockets
except ImportError:
    raise SystemExit("run with the engine's interpreter: /opt/sniper-venv/bin/python3")
URL = "wss://feed.mainnet.chain.robinhood.com"; SECS = float(sys.argv[1]) if len(sys.argv) > 1 else 120
seen = {"A": {}, "B": {}}; errors = []


async def reader(name, t_end):
    try:
        async with websockets.connect(URL, open_timeout=10, max_size=None, ping_interval=10, ping_timeout=5, compression="deflate") as ws:
            while time.time() < t_end:
                raw = await asyncio.wait_for(ws.recv(), timeout=5.0); now = time.perf_counter(); d = json.loads(raw)
                for m in d.get("messages", []):
                    hdr = m["message"]["message"].get("header", {})
                    if int(hdr.get("kind", 0) or 0) != 3:
                        continue
                    seq = int(m.get("sequenceNumber") or 0)
                    if seq and seq not in seen[name]:
                        seen[name][seq] = now
    except Exception as e:
        errors.append(f"{name}: {type(e).__name__} {str(e)[:120]}")


async def main():
    t_end = time.time() + SECS
    await asyncio.gather(reader("A", t_end), reader("B", t_end))
    both = sorted(set(seen["A"]) & set(seen["B"]))
    if not both:
        print("no message seen on both sockets", errors); return
    d = [(seen["A"][s] - seen["B"][s]) * 1000 for s in both]          # positive: B was earlier
    gain_vs_a = [max(0.0, x) for x in d]; gain_vs_b = [max(0.0, -x) for x in d]
    print(f"{len(both)} messages on both sockets in {SECS:.0f} s (A only {len(set(seen['A']) - set(seen['B']))}, B only {len(set(seen['B']) - set(seen['A']))})")
    print(f"B earlier than A on {sum(1 for x in d if x > 0) / len(d):.0%} of messages; |A-B| median {st.median(abs(x) for x in d):.1f} ms, p90 {sorted(abs(x) for x in d)[int(0.9 * len(d))]:.1f} ms, max {max(abs(x) for x in d):.1f} ms")
    print(f"earlier-of-two beats A alone by median {st.median(gain_vs_a):.1f} ms, mean {st.mean(gain_vs_a):.1f} ms, p90 {sorted(gain_vs_a)[int(0.9 * len(gain_vs_a))]:.1f} ms")
    print(f"earlier-of-two beats B alone by median {st.median(gain_vs_b):.1f} ms, mean {st.mean(gain_vs_b):.1f} ms, p90 {sorted(gain_vs_b)[int(0.9 * len(gain_vs_b))]:.1f} ms")
    if errors:
        print("errors:", errors)

asyncio.run(main())
