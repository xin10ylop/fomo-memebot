#!/usr/bin/env python3
"""Live shadow of the influencer-catalyst scalp (report section 18). No capital, no keys beyond the fomoapi feed key.

Listens to the fomo alerts WebSocket. On every buy alert from a trader whose audience is at least MINF followers
(from the leaderboard files), it starts a 60-minute price watch on DexScreener (one poll every 20 s) and simulates the
rule exactly: entry at the first polled price (about 20-40 s after the alert, the latency of a person reacting to the
app), stop -22%, take-profit +50%, trailing stop 25% below the running high once +30% is reached, exit at 60 minutes
otherwise, costs 3% round trip. Logs each finished trade to data/derived/catalyst_shadow.jsonl.

usage: python3 catalyst_shadow.py [MINF]   (run from the data root with fapi/lb/*.json)
"""
import asyncio, json, time, sys, os, urllib.request, collections, threading

K = "fapi_38babbd7079b48aea53b44b32b0a3faf1cd6d4de865b46cb86e3bfb0b3e10c2a"
MINF = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000
OUT = "/home/user/fomo-memebot/data/derived/catalyst_shadow.jsonl"
H = {"User-Agent": "Mozilla/5.0 fomo-memebot/catalyst-shadow"}
CHAIN = {"robinhood": "robinhood", "solana": "solana", "bsc": "bsc", "base": "base", "ethereum": "ethereum"}
lb = {}
for w in ["24h", "7d", "30d", "all"]:
    try:
        for t in json.load(open(f"fapi/lb/{w}.json"))["traders"]:
            lb[t["handle"].lower()] = t
    except Exception:
        pass
print(f"followers known for {len(lb)} handles; watching buys from >= {MINF:,}", file=sys.stderr, flush=True)
active = {}


def price(chain, addr):
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request("https://api.dexscreener.com/latest/dex/tokens/" + addr, headers=H), timeout=20))
        ps = [p for p in d.get("pairs") or [] if (p.get("baseToken") or {}).get("address", "").lower() == addr.lower() and (chain is None or p.get("chainId") == chain)]
        if not ps:
            return None, None
        p = max(ps, key=lambda p: (p.get("liquidity") or {}).get("usd") or 0)
        return float(p["priceUsd"]), (p.get("liquidity") or {}).get("usd")
    except Exception:
        return None, None


def watch(alert):
    addr = alert.get("tokenAddress"); chain = CHAIN.get(alert.get("chain")); key = (alert.get("trader"), addr)
    t_alert = (alert.get("ts") or alert.get("_recv") or time.time() * 1000) / 1000
    e = None; hi = None; liq = None; path = []
    t_end = time.time() + 3600; why = "time"
    while time.time() < t_end:
        px, lq = price(chain, addr)
        now = time.time()
        if px:
            if e is None:
                e = px; hi = px; liq = lq; t_in = now
            else:
                hi = max(hi, px); r = px / e - 1
                path.append([round(now - t_in), r])
                if r <= -0.22:
                    why = "stop"; break
                if r >= 0.50:
                    why = "tp"; break
                if hi / e - 1 >= 0.30 and px <= hi * 0.75:
                    why = "trail"; break
        time.sleep(20)
    if e is None:
        rec = {"trader": alert.get("trader"), "followers": lb.get((alert.get("trader") or "").lower(), {}).get("followers"), "token": alert.get("token"), "addr": addr, "chain": alert.get("chain"), "t_alert": t_alert, "result": "no price"}
    else:
        px, _ = price(chain, addr); px = px or (path[-1][1] + 1) * e
        r = px / e - 1
        if why == "stop":
            r = -0.22
        elif why == "tp":
            r = 0.50
        rec = {"trader": alert.get("trader"), "followers": lb.get((alert.get("trader") or "").lower(), {}).get("followers"), "token": alert.get("token"), "addr": addr, "chain": alert.get("chain"), "usd": alert.get("usdValue"), "t_alert": t_alert, "t_in": t_in, "entry_delay_s": round(t_in - t_alert), "entry": e, "liq": liq, "exit_reason": why, "ret_gross": r, "ret_net": r - 0.03, "mfe": hi / e - 1, "hold_s": round(time.time() - t_in), "path": path[::3]}
    with open(OUT, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(time.strftime("%H:%M:%S"), "done", rec.get("trader"), rec.get("token"), rec.get("exit_reason"), rec.get("ret_net"), file=sys.stderr, flush=True)
    active.pop(key, None)


async def run():
    import websockets
    backoff = 5
    while True:
        try:
            async with websockets.connect(f"wss://api.fomoapi.io/ws/alerts?key={K}", ping_interval=20, max_size=8_000_000) as ws:
                print(time.strftime("%H:%M:%S"), "connected", file=sys.stderr, flush=True); backoff = 5
                async for msg in ws:
                    try:
                        d = json.loads(msg)
                    except Exception:
                        continue
                    if d.get("type") != "alert" or d.get("alertType") != "buy" or d.get("replay"):
                        continue
                    fol = lb.get((d.get("trader") or "").lower(), {}).get("followers") or 0
                    if fol < MINF or not d.get("tokenAddress"):
                        continue
                    key = (d.get("trader"), d.get("tokenAddress"))
                    if key in active or len(active) >= 12:
                        continue
                    active[key] = time.time()
                    print(time.strftime("%H:%M:%S"), "alert", d.get("trader"), fol, d.get("token"), d.get("chain"), d.get("usdValue"), file=sys.stderr, flush=True)
                    threading.Thread(target=watch, args=(d,), daemon=True).start()
        except Exception as e:
            print(time.strftime("%H:%M:%S"), "ws error", repr(e)[:200], "retry in", backoff, file=sys.stderr, flush=True)
            await asyncio.sleep(backoff); backoff = min(backoff * 2, 120)


asyncio.run(run())
