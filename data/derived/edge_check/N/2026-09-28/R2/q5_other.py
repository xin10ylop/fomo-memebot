"""Q5: today's data added to the week; does any split of the current rule's fires (usual view k-1 with registration, slip 0.20,
second place h11, $13, gas $0.33) now pay in both halves when it did not before? Halves: Sep 21 09:40-23 / Sep 24-28 21:00.
A split is a candidate only if the side it would drop loses money in BOTH halves. Also the hold on today's fills."""
import json, os, statistics as st, time
H = os.path.dirname(os.path.abspath(__file__)); SPLIT = 1790208000; TODAY = 1790588400
pop = {p["cv"]: p for p in json.load(open(f"{H}/q4_pop.json"))}
R = [x for x in json.load(open(f"{H}/rows_k1reg.json")) if x.get("fired")]
for x in R: x.update({k: pop[x["cv"]][k] for k in ("k", "heat", "w1") if x["cv"] in pop})
def cell(v):
    if not v: return f"{'n=0':>30s}"
    f = [x["ret"]["11"] for x in v if x["why"] == "FILL"]
    return f"n={len(v):3d} fills {len(f):3d} {st.mean(f) if f else float('nan'):+6.1%} ${sum(x['usd'] for x in v):+7.2f}"
splits = [("tier 2% (100 bps)", lambda x: (x.get("tier") or 0) < 0.025), ("tier 3% (200 bps)", lambda x: (x.get("tier") or 0) >= 0.025),
          ("bundle < 0.6 ETH", lambda x: x["bundle"] < 0.6), ("bundle >= 0.6 ETH", lambda x: x["bundle"] >= 0.6),
          ("fleets at k-1 == 2", lambda x: x.get("fleets") == 2), ("fleets at k-1 >= 3", lambda x: (x.get("fleets") or 0) >= 3),
          ("k <= 4", lambda x: x.get("k", 99) <= 4), ("k >= 5", lambda x: x.get("k", 0) >= 5),
          ("heat <= 2", lambda x: x.get("heat", 0) <= 2), ("heat >= 3", lambda x: x.get("heat", 0) >= 3),
          ("guard ratio >= 0.93 (the old 7% class)", lambda x: (x.get("guard_ratio") or 1) >= 0.93), ("guard ratio 0.80-0.93 (admitted)", lambda x: 0.80 <= (x.get("guard_ratio") or 1) < 0.93)]
print(f"{'split':40s} {'Sep 21-23':>36s} {'Sep 24-28 09:40':>36s} {'Sep 28 09:40-21:00':>36s}")
for lab, f in splits:
    print(f"{lab:40s} " + " ".join(f"{cell([x for x in R if f(x) and lo <= x['T0'] < hi]):>36s}" for lo, hi in ((0, SPLIT), (SPLIT, TODAY), (TODAY, 2e9))))
print("\nhold on the usual view's fills (same fills), by window")
for lo, hi, lab in ((0, SPLIT, "Sep 21-23"), (SPLIT, TODAY, "Sep 24-28 09:40"), (TODAY, 2e9, "today")):
    v = [x for x in R if x["why"] == "FILL" and lo <= x["T0"] < hi]
    print(f"  {lab:16s} n={len(v):3d} " + "  ".join(f"h{h} {st.mean(x['ret'][h] for x in v if x['ret'].get(h) is not None):+6.1%}" for h in ("9", "11", "13", "15")))
