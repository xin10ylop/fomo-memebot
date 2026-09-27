"""decompose.py (edge_check/A): where the recent fires' return went. (1) The bundle's dump: fires where the named wallets
(+ creator) sold >= 50% of what they bought by the seat within 300 blocks of it, fit vs recent (Fisher one-sided).
(2) Counterfactual on the same tapes and the same model: the named wallets' sells removed (as if the bundle held); then also
the outsiders' buys removed (no follow-on demand): how much of the fit-recent gap each accounts for. (3) The 'new fleet' split
done fairly: in time order, a fire is 'new' when one of its k-2 fleets was never counted at k-2 in an earlier fire (fit and
recent in one sequence, Sep 18-19 as the burn-in).   python3 data/derived/edge_check/A/decompose.py"""
import sys, json, gzip, math, statistics as st
sys.path.insert(0, "data/derived/edge_check/A"); sys.path.insert(0, "src/analysis")
from common import *
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()): import price as P
F = json.load(open(A + "fires_features.json")); T = P.T; raw = {r["cv"]: r for r in all_launches(FIT + REC)}
fit = [x for x in F if x["set"] == "fit"]; rec = [x for x in F if x["set"] == "rec"]
def fisher_ge(a, n1, b, n2):   # P(recent count >= b) given the margins (one-sided)
    K = a + b; N = n1 + n2
    return sum(math.comb(K, j) * math.comb(N - K, n2 - j) for j in range(b, min(K, n2) + 1)) / math.comb(N, n2)
d = lambda v: f"n {len(v):2d} mean {st.mean(v):+6.1%} median {st.median(v):+6.1%} win {sum(y > 0 for y in v)/len(v):3.0%}" if v else "n  0"
dump = lambda x: x["named_sold_frac"]["300"] is not None and x["named_sold_frac"]["300"] >= 0.5
a = sum(dump(x) for x in fit); b = sum(dump(x) for x in rec)
print(f"(1) bundle dump (named sold >= 50% of their tokens within 300 blocks of the seat): fit {a}/{len(fit)}, recent {b}/{len(rec)}; Fisher one-sided p {fisher_ge(a, len(fit), b, len(rec)):.4f}")
print(f"    fit   dumped {d([x['ret']['300'] for x in fit if dump(x)])} | not {d([x['ret']['300'] for x in fit if not dump(x)])}")
print(f"    recent dumped {d([x['ret']['300'] for x in rec if dump(x)])} | not {d([x['ret']['300'] for x in rec if not dump(x)])}")
def cf_ret(x, drop_named_sells=False, drop_out_buys=False):
    L = dict(T[x["cv"]]); r = raw[x["cv"]]; named = set(r["named"]) | {r["creator"]}; bE1 = x["bE1"]
    # classes as in chain_change: fleets = relay targets + senders in blocks 0..k+1; early = other buyers by the seat block
    fleet = set()
    for rows in r["blocks"][: r["k"] + 2]:
        for t in rows:
            if not (t["named_fr"] or t["named_data"]): fleet.add(t["to"]); fleet.add(t["fr"])
    early = {e["who"] for e in L["rows"] if e["bn"] <= bE1 and e["k"] == "B"}
    keep = []
    for e in L["rows"]:
        if e["bn"] > bE1:
            if drop_named_sells and e["k"] == "S" and e["who"] in named: continue
            if drop_out_buys and e["k"] == "B" and e["who"] not in named and e["who"] not in fleet and e["who"] not in early: continue
        keep.append(e)
    L["rows"] = keep; return P.my_model(L)[300]
print("\n(2) counterfactuals on the same tapes, second place, 300 blocks, $13")
for name, S in (("fit", fit), ("recent", rec)):
    base = [x["ret"]["300"] for x in S]; nd = [cf_ret(x, True) for x in S]; nb = [cf_ret(x, True, True) for x in S]
    print(f"    {name:6s} actual {d(base)}\n           bundle sells removed {d(nd)}\n           and outsiders' buys removed too {d(nb)}")
    if name == "fit": fb, fnd, fnb = st.mean(base), st.mean(nd), st.mean(nb)
    else: rb, rnd, rnb = st.mean(base), st.mean(nd), st.mean(nb)
print(f"    gap fit - recent (means): actual {fb - rb:+.1%}; with the bundle's sells removed in both {fnd - rnd:+.1%}; with outsiders' buys also removed {fnb - rnb:+.1%}")
# 0xe65b85ad (Sep 24 18:10): the bundle sold 92% and buyers absorbed it; removing those sells while the later buyers keep
# their ETH runs the curve to near-empty (+18,000%): the counterfactual is ill-posed there, so medians and a mean without it
for name, S in (("fit", fit), ("recent", rec)):
    S2 = [x for x in S if x["cv"][:10] != "0xe65b85ad"]
    print(f"    {name:6s} without 0xe65b85ad: actual mean {st.mean(x['ret']['300'] for x in S2):+.1%} median {st.median(x['ret']['300'] for x in S2):+.1%}; bundle sells removed mean {st.mean(cf_ret(x, True) for x in S2):+.1%} median {st.median(cf_ret(x, True) for x in S2):+.1%}")
print("\n(3) 'new fleet' fires in time order (burn-in Sep 18-19: its fires only register addresses)")
seen = set(); seq = sorted(F, key=lambda x: x["T0"]); out = {"fit": {"new": [], "old": []}, "rec": {"new": [], "old": []}}
for x in seq:
    isnew = any(a not in seen for a in x["fl_k2"])
    if x["win"] != "sep1819": out[x["set"]]["new" if isnew else "old"].append(x["ret"]["300"])
    seen |= set(x["fl_k2"])
for s in ("fit", "rec"):
    print(f"    {s:4s} with a first-seen fleet {d(out[s]['new'])} | all fleets seen before {d(out[s]['old'])}")
