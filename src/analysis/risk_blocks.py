"""round 15 (report section 23.2): block-count features for the seat gate, run from the data root after risk_harness.py has built its cache.
block-count features for the seat gate: is the Opus 'first taxed buy before 2.0 s' gate a rival-timing signal, a
creation-phase signal, or a chain-activity signal (few blocks between the creation and the T+2 outsider)?"""
import sys, os, json, pickle, statistics as st, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import risk_harness as RH, sniper_exact as SE
BUY, SELL = SE.BUY, SE.SELL
data = pickle.load(open('risk_harness_cache.pkl', 'rb'))
# block numbers per row, re-read from the event files (rows were built from the same filtered, (b, li)-sorted events)
for (day, win), keep in data.items():
    ev = collections.defaultdict(list)
    for line in open(f"rh/v2curve_{day}_{win}.jsonl"):
        b, li, tx, addr, t0, d = json.loads(line)
        if addr in keep and t0 in (BUY, SELL):
            ev[addr].append((b, li))
    bad = 0
    for cv, (L, f) in keep.items():
        e = sorted(ev[cv])
        if len(e) != len(L["rows"]):
            bad += 1; L["rowb"] = None; continue
        L["rowb"] = [b for b, li in e]
    print(day, win, "rows/blocks mismatches:", bad, "of", len(keep), file=sys.stderr)

def feats2(L, f):
    rows = L["rows"]; tier = L["tier"]; rb = L.get("rowb")
    if not rb:
        return None
    i_rival = next((i for i in range(1, len(rows)) if rows[i][1] == "B" and rows[i][0] <= 3.0 and 0.0012 <= rows[i][5] - tier <= 0.0035), None)
    d_rival = (rb[i_rival] - rb[0]) if i_rival is not None else None
    # blocks from the creation to the first event stamped >= 2.0 s (any kind): a second activity proxy for launches without a rival
    return dict(d_rival=d_rival, ne=RH.G_NE(f), pos=f["pos_create"], lag=f["rival_lag"])

rows = []
for k, keep in data.items():
    half = "FIT" if k in RH.FIT else "TEST"
    for cv, (L, f) in keep.items():
        g = feats2(L, f)
        if g is None:
            continue
        r7 = RH.replay(L, 300 / RH.PX, hold=7.0); r5 = RH.replay(L, 300 / RH.PX, hold=5.0)
        rows.append(dict(half=half, roi7=r7[0] / r7[1] if r7[4] != "reverted" else None, roi5=r5[0] / r5[1] if r5[4] != "reverted" else None, **g))
print("launches with a rival in the seat:", sum(1 for r in rows if r["d_rival"] is not None), "of", len(rows))
dr = [r["d_rival"] for r in rows if r["d_rival"] is not None]
print("blocks from the creation to the first T+2 outsider: deciles", st.quantiles(dr, n=10))
print("\nNE gate vs blocks-to-rival (rival launches): share skipped by NE per block bin")
bins = [(0, 12), (12, 16), (16, 20), (20, 24), (24, 30), (30, 999)]
for half in ("FIT", "TEST"):
    print(half)
    for a, b in bins:
        c = [r for r in rows if r["half"] == half and r["d_rival"] is not None and a <= r["d_rival"] < b and r["roi7"] is not None]
        if not c:
            continue
        print(f"  blocks {a:3d}-{b:3d}: n {len(c):4d}  NE-skipped {100*sum(1 for r in c if r['ne'])/len(c):3.0f}%  ROI hold7 {100*st.mean(r['roi7'] for r in c):+6.1f}%  hold5 {100*st.mean(r['roi5'] for r in c if r['roi5'] is not None):+6.1f}%  tail7 {100*sum(1 for r in c if r['roi7']<-0.4)/len(c):3.0f}%  mean pos {st.mean(r['pos'] for r in c):.2f}")
    c = [r for r in rows if r["half"] == half and r["d_rival"] is None and r["roi7"] is not None]
    print(f"  no rival     : n {len(c):4d}  ROI hold7 {100*st.mean(r['roi7'] for r in c):+6.1f}%  hold5 {100*st.mean(r['roi5'] for r in c if r['roi5'] is not None):+6.1f}%  tail7 {100*sum(1 for r in c if r['roi7']<-0.4)/len(c):3.0f}%")
print("\nwithin the NE-skipped set and the NE-kept set, ROI by creation position (rival launches)")
for half in ("FIT", "TEST"):
    for ne in (True, False):
        for a, b in ((0, 0.5), (0.5, 1.01)):
            c = [r for r in rows if r["half"] == half and r["d_rival"] is not None and r["ne"] == ne and a <= r["pos"] < b and r["roi7"] is not None]
            if c:
                print(f"  {half} NE-skip={ne!s:5s} pos {a:.1f}-{b:.1f}: n {len(c):4d} ROI7 {100*st.mean(r['roi7'] for r in c):+6.1f}% ROI5 {100*st.mean(r['roi5'] for r in c if r['roi5'] is not None):+6.1f}%")
# gates on blocks-to-rival, executable live (the engine counts the blocks between the creation and the first block of T+2)
print("\ngate: skip when a rival exists and blocks(creation -> rival) < K")
for K in (12, 16, 20, 24):
    for hold in (7.0, 5.0):
        cfg = {"hold": hold, "skip_fn": None}
        def mk(K):
            return lambda f: False
        # skip via the feature table: mark launches to skip in a set
        skip = {id(f) for k, keep in data.items() for cv, (L, f) in keep.items() if L.get("rowb") and (lambda g: g["d_rival"] is not None and g["d_rival"] < K)(feats2(L, f))}
        cfg["skip_fn"] = lambda f, skip=skip: id(f) in skip
        res = RH.evaluate(cfg, data); RH.summarize(res, f"skip rival within {K} blocks, hold {hold:.0f}")
