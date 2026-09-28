"""Q4: the launches the usual rule refuses (engine fleets at k-1 with the registration block < 2). Is there a signal known before
the tick that predicts a crowd in block k (fleets at k >= 2), or a paying subset, with fit/read halves? Firing on a refused launch
is priced as every fire: second place at h11, $13, the minOut guard at 0.20 (a revert costs the gas), gas $0.33 a burst.
Halves: Sep 21 09:40-23 (fit) / Sep 24-28 21:00 (read), each way. Thresholds are chosen on one half and read on the other."""
import json, gzip, glob, os, time, statistics as st, collections
H = os.path.dirname(os.path.abspath(__file__)); D = "/home/user/fomo-memebot/data/derived/live_vs_table"
US = {"0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}
SPLIT = 1790208000; SLIP = 0.20
K1 = {x["cv"]: x for x in json.load(open(f"{H}/rows_k1reg.json"))}; KK = {x["cv"]: x for x in json.load(open(f"{H}/rows_kreg.json"))}
CR = {}
for cf in glob.glob(f"{D}/crowd_raw_*.json*"):
    if cf.endswith(".json") and os.path.exists(cf + ".gz"): continue
    try: R = json.load(gzip.open(cf, "rt")) if cf.endswith(".gz") else json.load(open(cf))
    except Exception: continue
    for r in R: CR.setdefault(r["cv"].lower(), r)
def cums(r):
    wallets, fleets = set(), set(); cw, cf = [], []
    for rows in r["blocks"][: r["k"] + 1]:
        for t in rows:
            if t["to"] in US or t["to_token"] or t["fr"] in US: continue
            if t["direct"]:
                if not t["named_fr"]: fleets.add(t["fr"]); wallets.add(t["fr"])
            elif not t["named_data"]:
                fleets.add(t["to"]); wallets.add(t["fr"]) if not t["named_fr"] else None
        cw.append(len(wallets)); cf.append(len(fleets))
    return cw, cf
at = lambda c, j: c[j] if 0 <= j < len(c) else 0
allrows = sorted(K1.values(), key=lambda x: x["T0"])
pop = []
for x in allrows:
    if not (x["why"].startswith("GATE attackers") or x.get("fired")): continue          # reached the crowd gate
    y = KK.get(x["cv"]); r = CR.get(x["cv"])
    if not y or not r: continue
    cw, cf = cums(r); k = r["k"]
    # heat: population launches in the previous 60 min and how many of them had a crowd at k (the engine watched them all)
    prev = [p for p in allrows if x["T0"] - 3600 <= p["T0"] < x["T0"] and (p["why"].startswith("GATE attackers") or p.get("fired"))]
    heat = sum(1 for p in prev if (KK.get(p["cv"]) or {}).get("fleets", 0) >= 2)
    g = x.get("guard_ratio"); ret = x["ret"].get("11")
    usd = -0.33 if (ret is None or (g is not None and g < 1 - SLIP)) else ret * 13 - 0.33
    pop.append(dict(cv=x["cv"], T0=x["T0"], fit=x["T0"] < SPLIT, refused=x["why"].startswith("GATE attackers"), f1=x.get("fleets", 0), fk=y.get("fleets", 0),
                    w1=at(cw, k - 1), k=k, bundle=x["bundle"], named=x.get("named") or 0, tier=x.get("tier"), cs=(x.get("tk0") or 0) / 1e9, ib=x.get("init_buy_eth") or 0,
                    hour=time.gmtime(x["T0"]).tm_hour, heat=heat, ret=ret, usd=usd))
ref = [p for p in pop if p["refused"]]
def s(v, lab):
    if not v: return f"{lab}: n=0"
    rr = [p["ret"] for p in v if p["ret"] is not None]
    return f"{lab}: n={len(v):3d} block-k crowd {sum(p['fk'] >= 2 for p in v) / len(v):4.0%}  fire all: mean {st.mean(rr):+6.1%} ${sum(p['usd'] for p in v):+7.2f} (${st.mean(p['usd'] for p in v):+.2f}/fire)"
print("refused at the usual view (engine fleets at k-1 < 2), whole week Sep 21 09:40 - Sep 28 21:00")
for half, lab in ((True, "fit  Sep 21-23"), (False, "read Sep 24-28")):
    v = [p for p in ref if p["fit"] == half]; print("  " + s(v, lab))
    print("    of them with a block-k crowd: " + s([p for p in v if p["fk"] >= 2], "fk>=2") + " | without: " + s([p for p in v if p["fk"] < 2], "fk<2"))
# candidate signals: a threshold rule 'fire the refused launch if feature >= t' (or <= t), chosen on one half, read on the other
feats = {"f1 (fleets at k-1)": "f1", "w1 (wallets at k-1)": "w1", "k (blocks in the second)": "k", "bundle ETH": "bundle", "named wallets": "named",
         "creator supply share": "cs", "creator buy ETH": "ib", "heat (crowded launches, last 60 min)": "heat", "hour UTC": "hour", "tier": "tier"}
def best(v, key):
    vals = sorted(set(p[key] for p in v if p[key] is not None)); out = None
    for t in vals:
        for sgn in (1, -1):
            sub = [p for p in v if p[key] is not None and (p[key] >= t if sgn > 0 else p[key] <= t)]
            if len(sub) < 5: continue
            u = sum(p["usd"] for p in sub)
            if out is None or u > out[0]: out = (u, t, sgn, len(sub))
    return out
print("\nthreshold rules on the refused set: chosen on one half ($ max, >= 5 fires), read on the other")
print(f"{'feature':38s} {'chosen on fit':>28s} {'read on Sep 24-28':>30s} {'chosen on read':>28s} {'read on Sep 21-23':>30s}")
for name, key in feats.items():
    cells = []
    for a, b in ((True, False), (False, True)):
        va = [p for p in ref if p["fit"] == a]; vb = [p for p in ref if p["fit"] == b]
        o = best(va, key)
        if not o: cells += ["-", "-"]; continue
        u, t, sgn, n = o; sub = [p for p in vb if p[key] is not None and (p[key] >= t if sgn > 0 else p[key] <= t)]
        rr = [p["ret"] for p in sub if p["ret"] is not None]
        cells += [f"{'>=' if sgn > 0 else '<='}{t:g}: n={n} ${u:+.1f}", f"n={len(sub)} {st.mean(rr) if rr else float('nan'):+.1%} ${sum(p['usd'] for p in sub):+.1f}"]
    print(f"{name:38s} {cells[0]:>28s} {cells[1]:>30s} {cells[2]:>28s} {cells[3]:>30s}")
# does anything predict the block-k crowd itself? rate of fk>=2 by the two strongest candidates, both halves
print("\nblock-k crowd rate among the refused, by fleets at k-1 and by heat")
for key, bins in (("f1", [(0, 0), (1, 1)]), ("heat", [(0, 0), (1, 2), (3, 99)]), ("w1", [(0, 0), (1, 1), (2, 999)]), ("k", [(0, 3), (4, 6), (7, 99)])):
    for lo, hi in bins:
        cells = []
        for half in (True, False):
            v = [p for p in ref if p["fit"] == half and lo <= p[key] <= hi]
            rr = [p["ret"] for p in v if p["ret"] is not None]
            cells.append(f"n={len(v):3d} crowd@k {sum(p['fk'] >= 2 for p in v) / len(v) if v else 0:4.0%} fire {st.mean(rr) if rr else float('nan'):+6.1%} ${sum(p['usd'] for p in v):+6.1f}")
        print(f"  {key} {lo}-{hi}: fit {cells[0]} | read {cells[1]}")
# today's winners without a pre-tick crowd
print("\ntoday's refused launches that paid >= +20% at second place: their pre-tick features")
for p in ref:
    if p["T0"] >= 1790588400 and p["ret"] is not None and p["ret"] >= 0.2:
        print(f"  {time.strftime('%H:%M', time.gmtime(p['T0']))} {p['cv'][:10]} ret {p['ret']:+.1%} f1 {p['f1']} w1 {p['w1']} fk {p['fk']} k {p['k']} bundle {p['bundle']:.2f} named {p['named']} cs {p['cs']:.3f} heat {p['heat']} tier {p['tier']}")
json.dump(pop, open(f"{H}/q4_pop.json", "w"))
