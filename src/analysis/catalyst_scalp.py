#!/usr/bin/env python3
"""The influencer-catalyst scalp, replicated exactly on swap-level data (report section 18.1).

Events: the 276 leaderboard buys matched to exact pool swaps in section 11.1 (data/derived/kol_swap_events2.jsonl:
handle, followers, token, block). For each, every Swap of the pool from 30 minutes before to 30 minutes after the
fill is pulled from the chain (cached in rh/catalyst_paths.jsonl), giving the full price path. Rule: entry at the
first swap at least D seconds after the fill (D = 3, 15, 60: bot, fast person, app latency), stop -22% (his "900k ->
700k"), take-profit +50% (his average exit), trailing stop 25% below the running high once +30% is reached, exit at
30 minutes otherwise; a path with no later swap exits at its last price. Costs: 1% pool fee each way plus
constant-product impact of a CLIP-dollar order against the pool's measured depth, each way. Placebo: the same rule
from a random swap 10 to 30 minutes before the fill. Cohorts: audience, pool depth, and an impact rank computed on
the first half of each poster's events and applied to the second (walk-forward "who moves the market").

usage: python3 catalyst_scalp.py [CLIP ...]   (run from the data root)
"""
import json, os, sys, time, random, collections, statistics as st, urllib.request

random.seed(21)
RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 fomo-memebot/catalyst"}
SWAP_V3 = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"; SWAP_V4 = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
PM = "0x8366a39cc670b4001a1121b8f6a443a643e40951"; BPS = 9.9
HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[1:]
WORKER = None
if ARGS and ARGS[0].startswith("--worker="):
    WORKER = tuple(int(x) for x in ARGS[0][9:].split("/")); ARGS = ARGS[1:]   # --worker=i/n : pull only events i mod n, write cache part i
CLIPS = [float(x) for x in ARGS] or [500.0, 2000.0, 5000.0]
pools = json.load(open("gt/pools_v3.json"))


def call(payload, tries=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(RPC, data=json.dumps(payload).encode(), headers=H); d = json.load(urllib.request.urlopen(req, timeout=120))
            if "error" in d:
                raise RuntimeError(d["error"])
            return d
        except Exception:
            time.sleep(3 * (i + 1))
    return None


def s256(x):
    return x - (1 << 256) if x >= (1 << 255) else x


def s128(x):
    x &= (1 << 128) - 1; return x - (1 << 128) if x >= (1 << 127) else x


def best_pool(p):
    if not p or not p.get("pools"):
        return None
    b = [q for q in p["pools"] if q.get("base")]; return max(b, key=lambda q: q["liq"]) if b else None


def swaps(pool_addr, frm, to):
    out = []; b = frm; step = 6000; kind = "v3" if len(pool_addr) == 42 else "v4"
    while b <= to:
        e = min(to, b + step)
        flt = {"fromBlock": hex(b), "toBlock": hex(e), "address": pool_addr, "topics": [SWAP_V3]} if kind == "v3" else {"fromBlock": hex(b), "toBlock": hex(e), "address": PM, "topics": [SWAP_V4, pool_addr]}
        r = call({"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs", "params": [flt]})
        if r is None:
            step = max(500, step // 2); continue
        for lg in r.get("result") or []:
            d = lg["data"]
            if len(d) < 2 + 64 * 3:
                continue
            a0 = int(d[2:66], 16); a1 = int(d[66:130], 16); sp = int(d[130:194], 16)
            a0, a1 = (s256(a0), s256(a1)) if kind == "v3" else (s128(a0), s128(a1))
            out.append([int(lg["blockNumber"], 16), int(lg["logIndex"], 16), sp])
        b = e + 1; time.sleep(0.12)
    out.sort(); return out, kind


events = [json.loads(l) for l in open(os.path.join(HERE, "..", "..", "data", "derived", "kol_swap_events2.jsonl"))]
import glob as _glob
cache = {}
for cf_ in _glob.glob("rh/catalyst_paths*.jsonl"):
    for l in open(cf_):
        r = json.loads(l); cache[r["key"]] = r
cache_f = f"rh/catalyst_paths_w{WORKER[0]}.jsonl" if WORKER else "rh/catalyst_paths.jsonl"
todo = [e for i, e in enumerate(events) if e["key"] not in cache and (WORKER is None or i % WORKER[1] == WORKER[0])]
print(f"events {len(events)}, cached {len(cache)}, to pull {len(todo)}", file=sys.stderr, flush=True)
with open(cache_f, "a") as cf:
    for i, e in enumerate(todo):
        bp = best_pool(pools.get(e["token"]))
        if not bp:
            continue
        addr = bp["address"]; tok_is_1 = False
        q = (bp.get("quote") or "").lower()
        # token is currency1 when its address sorts above the quote
        tok_is_1 = e["token"].lower() > q if q else False
        sw, kind = swaps(addr, e["b"] - int(1800 * BPS), e["b"] + int(1800 * BPS))   # 30 min before (placebo entries) to 30 min after
        path = []
        for b, li, sp in sw:
            p = (sp / 2 ** 96) ** 2; px = (1 / p) if tok_is_1 else p
            path.append([b, px])
        rec = {"key": e["key"], "pool": addr, "kind": kind, "liq": bp["liq"], "b0": e["b"], "path": path}
        cache[e["key"]] = rec; cf.write(json.dumps(rec) + "\n"); cf.flush()
        if (i + 1) % 10 == 0:
            print(f"pulled {i + 1}/{len(todo)}", file=sys.stderr, flush=True)
if WORKER:
    print("worker done", file=sys.stderr); sys.exit(0)


def simulate(path, b0, delay_s, clip, liq, entry_at=None):
    """entry at the first swap >= b0 + delay blocks (or a given block); returns (net return, reason, mfe) or None"""
    start = (entry_at if entry_at is not None else b0 + int(delay_s * BPS))
    later = [p for p in path if p[0] >= start]
    if not later:
        return None
    e = later[0][1]; b_in = later[0][0]; imp = clip / max(liq, 1.0); cost = 0.02 + 2 * imp
    hi = e; ret = None; why = "time"; end = b_in + int(1800 * BPS)
    for b, px in later[1:]:
        if b > end:
            break
        hi = max(hi, px); r = px / e - 1
        if r <= -0.22:
            ret, why = -0.22, "stop"; break
        if r >= 0.50:
            ret, why = 0.50, "tp"; break
        if hi / e - 1 >= 0.30 and px <= hi * 0.75:
            ret, why = px / e - 1, "trail"; break
    if ret is None:
        inwin = [p for p in later if p[0] <= end]; ret = inwin[-1][1] / e - 1
    return ret - cost, why, hi / e - 1


rows = []
for e in events:
    c = cache.get(e["key"])
    if not c or len(c["path"]) < 3:
        continue
    b0 = e["b"]; kol_px = None
    pre = [p for p in c["path"] if p[0] <= b0]
    rows.append({**e, "path": c["path"], "depth": c["liq"], "pre": pre})
print(f"events with paths: {len(rows)}; depth median ${st.median(r['depth'] for r in rows):,.0f}", file=sys.stderr)


def stats(vals):
    if not vals:
        return "n=0"
    r = [v[0] for v in vals]; keys = collections.defaultdict(list)
    for v in vals:
        keys[v[3]].append(v[0])
    ks = list(keys); means = []
    for _ in range(600):
        smp = [random.choice(ks) for _ in ks]; means.append(st.mean([x for k in smp for x in keys[k]]))
    means.sort(); why = collections.Counter(v[1] for v in vals)
    return f"n={len(r):3d} mean {100 * st.mean(r):+6.1f}% [{100 * means[15]:+.0f}, {100 * means[584]:+.0f}] median {100 * st.median(r):+6.1f}% win {100 * sum(1 for x in r if x > 0) / len(r):3.0f}% | exits " + " ".join(f"{k}:{100 * v / len(r):.0f}%" for k, v in why.most_common())


def cohort(label, rs, delay, clip, placebo=False):
    vals = []
    for r in rs:
        if placebo:
            cand = [p for p in r["pre"] if p[0] <= r["b"] - int(600 * BPS)]
            if not cand:
                continue
            res = simulate(r["path"], r["b"], 0, clip, r["depth"], entry_at=random.choice(cand)[0])
        else:
            res = simulate(r["path"], r["b"], delay, clip, r["depth"])
        if res:
            vals.append((res[0], res[1], res[2], r["h"]))
    print(f"  {label:44s} {stats(vals)}")


# walk-forward impact rank: a poster is "influential" if, on the first half of their own events, the median 60 s move after the fill was >= +5%
by_h = collections.defaultdict(list)
for r in sorted(rows, key=lambda r: r["b"]):
    by_h[r["h"]].append(r)
influential = set(); second_half = []
for h, rs in by_h.items():
    if len(rs) < 4:
        continue
    k = len(rs) // 2; first = rs[:k]; second = rs[k:]
    med = st.median([x.get("e2_r60") or 0 for x in first])
    if med >= 0.05:
        influential.add(h)
    second_half += [r for r in second if h in influential]
print(f"walk-forward influential posters: {sorted(influential)} ({len(second_half)} later events)", file=sys.stderr)

for clip in CLIPS:
    for delay in (3, 15, 60):
        print(f"\n=== clip ${clip:,.0f}, entry {delay} s after the fill; stop -22%, TP +50%, trail 25% after +30%, 60 min; costs 1% each way + impact")
        cohort("all fills", rows, delay, clip)
        cohort("followers >= 100k", [r for r in rows if r["followers"] >= 100_000], delay, clip)
        cohort("followers >= 300k", [r for r in rows if r["followers"] >= 300_000], delay, clip)
        cohort("pool depth >= $100k", [r for r in rows if r["depth"] >= 100_000], delay, clip)
        cohort("followers >= 100k & depth >= $100k", [r for r in rows if r["followers"] >= 100_000 and r["depth"] >= 100_000], delay, clip)
        cohort("fill >= $5k", [r for r in rows if (r.get("usd") or 0) >= 5000], delay, clip)
        cohort("walk-forward influential, later events", second_half, delay, clip)
        cohort("placebo: same pools, 10-30 min earlier", rows, delay, clip, placebo=True)
