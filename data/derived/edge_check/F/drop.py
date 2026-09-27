"""drop.py (edge_check/F): what happens between E1+10 and E1+16, where every set's curve falls by about 3 points. For every fire, the
sells in the blocks E1+11..E1+16 and E1+17..E1+22 (our own wallet and relay excluded): how many, how many by wallets that bought in
the creation second or the seat block (the snipers of the first two seconds), how long those wallets held (sell block minus their
first buy block), and the curve's value change over those blocks.
    python3 data/derived/edge_check/F/drop.py > data/derived/edge_check/F/drop.txt"""
import sys, os, collections, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
R = [r for r in load_all() if is_fire(r)]
for per in ("fit", "rec"):
    held = collections.Counter(); c = collections.Counter(); fires_with = 0; wall = collections.Counter(); relb = collections.Counter()
    for r in R:
        if r["set"] != per: continue
        L = tape(r["cv"]); bE1 = seat_block(L); rows = [x for x in L["rows"] if x["who"] not in OURS]
        early = {}
        for x in rows:
            if x["k"] == "B" and x["bn"] <= bE1: early.setdefault(x["who"], x["bn"])
        hit = False
        for x in rows:
            if x["k"] != "S": continue
            d = x["bn"] - bE1
            if 11 <= d <= 16: c["sells 11-16"] += 1; c["sniper sells 11-16"] += x["who"] in early; hit |= x["who"] in early
            if 17 <= d <= 22: c["sells 17-22"] += 1; c["sniper sells 17-22"] += x["who"] in early
            if 5 <= d <= 10: c["sells 5-10"] += 1; c["sniper sells 5-10"] += x["who"] in early
            if x["who"] in early and d <= 40: held[x["bn"] - early[x["who"]]] += 1; relb[d] += 1; wall[x["who"]] += 1
        fires_with += hit
    n = sum(1 for r in R if r["set"] == per)
    print(f"{per}: {n} fires; per fire: " + ", ".join(f"{k} {v/n:.2f}" for k, v in sorted(c.items())) + f"; fires with a first-two-seconds sniper selling in E1+11..16: {fires_with}/{n}")
    print(f"   first-two-seconds snipers' sells by block after E1 (0..40): " + " ".join(f"{d}:{relb[d]}" for d in range(0, 41) if relb[d]))
    print(f"   their holding time (sell block - first buy block), sells within E1+40: " + " ".join(f"{h}:{held[h]}" for h in sorted(held) if held[h] >= 2))
    print(f"   wallets selling most often (within E1+40, across fires): " + ", ".join(f"{w[:10]} {k}" for w, k in wall.most_common(6)))
