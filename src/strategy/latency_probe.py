#!/usr/bin/env python3
"""Latency probe for the sniper's machine (report section 21.5, runbook section 3). Run it where the engine will run.

Measures, without sending anything:
  1. the sequencer feed: block cadence, and the wall-clock phase at which the block timestamp flips to a new second
     (the boundary the seat is keyed to). Flips are only visible at block granularity, so the true boundary is the LOW
     edge of the observed flip phases; the spread above it is block cadence plus jitter;
  2. round trips to the sequencer endpoint and to the RPC (eth_chainId), median and p90;
  3. the feed's delivery delay relative to the block timestamps (arrival wall clock minus timestamp second), which is
     network delay plus clock offset: keep the machine on NTP/chrony.
Prints a summary and writes latency_probe.json next to the log. Duration in seconds as the first argument (default 180).
usage: FEED_URL=... SEQ_URL=... RPC_URL=... python3 latency_probe.py [SECONDS]
"""
import asyncio, json, os, sys, time, statistics as st, http.client, urllib.parse

FEED_URL = os.environ.get("FEED_URL", "wss://feed.mainnet.chain.robinhood.com")
SEQ_URL = os.environ.get("SEQ_URL", "https://sequencer.mainnet.chain.robinhood.com")
RPC_URL = os.environ.get("RPC_URL", "https://rpc.mainnet.chain.robinhood.com")
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 180.0
UA = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fomo-memebot/probe"}


def rtt(url, n=15):
    u = urllib.parse.urlparse(url); out = []
    c = http.client.HTTPSConnection(u.netloc, timeout=10)
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []})
    for i in range(n + 1):
        t0 = time.perf_counter()
        try:
            c.request("POST", u.path or "/", body=body, headers=UA); r = c.getresponse(); r.read()
            if i:                                                       # first call pays the TLS handshake
                out.append((time.perf_counter() - t0) * 1000)
        except Exception as e:
            c = http.client.HTTPSConnection(u.netloc, timeout=10)
        time.sleep(0.2)
    return out


async def feed(duration):
    import websockets
    flips = []; arrivals = []; last_ts = None; offsets = []; n_msgs = 0
    t_end = time.time() + duration; t_warm = time.time() + 5.0            # the feed replays a backlog on connect: ignore the first seconds
    async with websockets.connect(FEED_URL, open_timeout=15, max_size=None, ping_interval=20) as ws:
        while time.time() < t_end:
            d = json.loads(await ws.recv()); now = time.time(); n_msgs += 1
            if now < t_warm:
                continue
            for m in d.get("messages", []):
                h = m["message"]["message"].get("header", {})
                if int(h.get("kind", 0) or 0) != 3:                    # only L2 messages carry the sequencer's clock (kind 11 = batch report, L1 time)
                    continue
                ts = int(h.get("timestamp", 0) or 0)
                if not ts:
                    continue
                arrivals.append(now); offsets.append(now - ts)
                if last_ts is not None and ts > last_ts:
                    flips.append((now, ts))
                last_ts = ts
    return flips, arrivals, offsets, n_msgs


def main():
    print(f"probing feed {FEED_URL} for {DUR:.0f} s ...")
    flips, arrivals, offsets, n_msgs = asyncio.run(feed(DUR))
    gaps = [b - a for a, b in zip(arrivals, arrivals[1:]) if 0 < b - a < 2]
    phases = sorted((t % 1.0) for t, ts in flips)
    # the boundary is the low edge of the flip phases; phases wrap at 1.0, so rotate to the largest gap first
    if len(phases) > 5:
        gaps_c = [(phases[(i + 1) % len(phases)] - phases[i]) % 1.0 for i in range(len(phases))]
        k = max(range(len(phases)), key=lambda i: gaps_c[i]); rot = [(p - phases[(k + 1) % len(phases)]) % 1.0 for p in phases]; rot.sort()
        base = phases[(k + 1) % len(phases)]; edge = (base + rot[int(0.02 * len(rot))]) % 1.0; spread = rot[int(0.98 * len(rot))] - rot[int(0.02 * len(rot))]
    else:
        edge = spread = float("nan")
    seq = rtt(SEQ_URL); rp = rtt(RPC_URL)
    summary = {
        "feed_messages": n_msgs, "block_cadence_ms": {"median": 1000 * st.median(gaps) if gaps else None, "p90": 1000 * sorted(gaps)[int(0.9 * len(gaps))] if gaps else None},
        "second_flips_observed": len(flips), "boundary_phase_local_s": edge, "flip_phase_spread_s": spread,
        "feed_delay_minus_clock_offset_s": {"median": st.median(offsets) if offsets else None, "p10": sorted(offsets)[len(offsets) // 10] if offsets else None},
        "sequencer_rtt_ms": {"median": st.median(seq) if seq else None, "p90": sorted(seq)[int(0.9 * len(seq))] if seq else None},
        "rpc_rtt_ms": {"median": st.median(rp) if rp else None, "p90": sorted(rp)[int(0.9 * len(rp))] if rp else None},
        "when": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}
    json.dump(summary, open("latency_probe.json", "w"), indent=1)
    print(json.dumps(summary, indent=1))
    print("\nhow to read it: the engine's predictive send fires at boundary_phase_local + MARGIN_MS each second of interest;")
    print("flip_phase_spread is mostly block cadence (about 0.1 s) plus jitter; sequencer_rtt is the one-way cost twice;")
    print("feed delay should be a few ms in Ohio (a large or negative value means the clock is off: fix NTP first).")


if __name__ == "__main__":
    main()
