#!/usr/bin/env python3
"""DexScreener snapshot of every LONG (stock-paired) launch in the eight-week census (report section 15).

Reads rh/launches_all.json (from pull_factory_logs.py), takes every launch with venue "long", and fetches the current
DexScreener state for each token address in batches of 30: the best pair's FDV, liquidity, price, quote symbol,
pair creation time. Tokens without a pair are dead for the purposes of the census. Public API, no key; paced to the
documented 300 requests/minute.

usage: python3 pull_dex_long.py [data-root] -> writes dex/long_tokens.json
"""
import json, sys, os, time, urllib.request

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fomo-memebot/long-census", "Accept": "application/json"}
launches = [x for x in json.load(open(os.path.join(ROOT, "rh", "launches_all.json"))) if x.get("venue") == "long"]
addrs = sorted({"0x" + x["t1"] for x in launches})
out_path = os.path.join(ROOT, "dex", "long_tokens.json")
out = json.load(open(out_path)) if os.path.exists(out_path) else {}
todo = [a for a in addrs if a not in out]
print(f"LONG launches {len(launches)}, unique tokens {len(addrs)}, already fetched {len(out)}, to fetch {len(todo)}", flush=True)


def get(url):
    for i in range(6):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60))
        except Exception as e:
            time.sleep(3 * (i + 1))
    return None


for i in range(0, len(todo), 30):
    batch = todo[i:i + 30]
    d = get("https://api.dexscreener.com/latest/dex/tokens/" + ",".join(batch))
    if d is None:
        print("giving up at", i, flush=True); break
    by = {}
    for p in d.get("pairs") or []:
        ba = (p.get("baseToken") or {}).get("address", "").lower()
        rec = {"fdv": p.get("fdv"), "mcap": p.get("marketCap"), "liq": (p.get("liquidity") or {}).get("usd"), "price": p.get("priceUsd"), "pair": p.get("pairAddress"), "dex": p.get("dexId"), "created": p.get("pairCreatedAt"), "quote": (p.get("quoteToken") or {}).get("symbol"), "symbol": (p.get("baseToken") or {}).get("symbol"), "name": (p.get("baseToken") or {}).get("name"), "vol24": (p.get("volume") or {}).get("h24")}
        if ba not in by or (rec["liq"] or 0) > (by[ba]["liq"] or 0):
            by[ba] = rec
    for a in batch:
        out[a] = by.get(a)  # None = no pair on DexScreener
    if (i // 30) % 40 == 0:
        json.dump(out, open(out_path, "w")); print(f"{len(out)}/{len(addrs)} fetched, {sum(1 for v in out.values() if v)} with a pair", flush=True)
    time.sleep(0.25)
json.dump(out, open(out_path, "w"))
print(f"done: {len(out)} tokens, {sum(1 for v in out.values() if v)} with a pair", flush=True)
