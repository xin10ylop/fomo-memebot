"""compare3.py (reviewer B), test 3: what changed on the chain for the launches the rule fires on, fit windows (Sep 18-23)
against Sep 24-27, from features.json (features.py) and the crowd files.
    python3 data/derived/edge_check/B/compare3.py [all]      (all: every launch of the population instead of the fires)"""
import sys, os, json, collections, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
F = json.load(open(c.B + "features.json")); ALL = len(sys.argv) > 1 and sys.argv[1] == "all"
sel = lambda g: [f for f in F if f["grp"] == g and (ALL or f["fire"])]
fit, rec = sel("fit"), sel("recent")
def R(f, h=300): return f["ret"][str(h)]
def med(v): return st.median(v) if v else float("nan")
def mn(v): return st.mean(v) if v else float("nan")
def row(name, fn, fmt="{:.2f}", agg=med):
    a = [fn(f) for f in fit]; b = [fn(f) for f in rec]; a = [x for x in a if x is not None]; b = [x for x in b if x is not None]
    print(f"  {name:52s} fit {fmt.format(agg(a)):>9s}   recent {fmt.format(agg(b)):>9s}")
print(f"=== {'every launch' if ALL else 'the rule fires'}: fit {len(fit)}, recent {len(rec)}")
print(f"  return h300 mean: fit {mn([R(f) for f in fit]):+.1%}  recent {mn([R(f) for f in rec]):+.1%};  median fit {med([R(f) for f in fit]):+.1%} recent {med([R(f) for f in rec]):+.1%}")
print("-- crowd (medians unless said)")
row("k (blocks after b0 in the creation second)", lambda f: f["k"], "{:.1f}")
row("fleets at k-2", lambda f: f["n_f_k2"], "{:.1f}")
row("fleets at k-2 (mean)", lambda f: f["n_f_k2"], "{:.2f}", mn)
row("fleets by the seat block (all, 0..k+1)", lambda f: f["n_f_all"], "{:.1f}")
row("fleets by the seat block (mean)", lambda f: f["n_f_all"], "{:.2f}", mn)
row("wallets at k-2", lambda f: c.at(f["cw"], f["k"] - 2), "{:.1f}")
row("rival shots in the creation second", lambda f: f["shots_cs"], "{:.0f}")
row("rival shots in the seat block", lambda f: f["shots_seat"], "{:.0f}")
row("buys landed in the seat block (not ours)", lambda f: f["seat_n"], "{:.1f}")
row("ETH bought in the seat block", lambda f: f["seat_eth"], "{:.3f}")
print("-- the launch")
row("bundle ETH (e1_multi definition)", lambda f: f["bundle_eth"], "{:.3f}")
row("creation-second ETH (all buys)", lambda f: f["creation_eth"], "{:.3f}")
row("creator's buy, share of supply", lambda f: f["creator_share"], "{:.4f}")
row("tier 3% share (mean)", lambda f: 1.0 if f["tier"] >= 0.0295 else 0.0, "{:.2f}", mn)
row("named wallets", lambda f: f["named"], "{:.1f}")
print("-- the 300 blocks after the seat")
def share(f, cl, h):
    held = f["held"].get(cl, 0); s = f["sold"][str(h)].get(cl, 0)
    return min(1.0, s / held) if held > 0 else None
for cl in ("bundle", "fleet", "other"):
    for h in (15, 60, 300): row(f"{cl}: share of its seat-second tokens sold by E1+{h} (mean)", lambda f, cl=cl, h=h: share(f, cl, h), "{:.2f}", mn)
    row(f"{cl}: first sell, blocks after E1 (median, launches with one)", lambda f, cl=cl: f["first_sell"].get(cl), "{:.0f}")
    row(f"{cl}: ETH out of sells in the hold (mean)", lambda f, cl=cl: f["sell_eth"].get(cl, 0.0), "{:.3f}", mn)
row("outsiders' ETH bought after the seat second (mean)", lambda f: f["buy_eth_after"].get("other", 0.0), "{:.3f}", mn)
row("outsiders' ETH bought after the seat second (median)", lambda f: f["buy_eth_after"].get("other", 0.0), "{:.3f}")
row("fleets' ETH bought after the seat second (mean)", lambda f: f["buy_eth_after"].get("fleet", 0.0), "{:.3f}", mn)
row("distinct outside buyers after the seat second", lambda f: f["n_outsiders"], "{:.0f}")
row("dead (h300 < -40%)", lambda f: 1.0 if R(f) < -0.4 else 0.0, "{:.2f}", mn)
print("-- hour of day (UTC): count and mean h300 return")
for g, S in (("fit", fit), ("recent", rec)):
    b = collections.defaultdict(list)
    for f in S: b[f["hour"] // 6 * 6].append(R(f))
    print(f"  {g:7s} " + "  ".join(f"{h:02d}-{h+5:02d}h: n={len(b[h])} {mn(b[h]):+.0%}" for h in (0, 6, 12, 18)))
print("-- the fleets at k-2: which ones")
cf_fit = collections.Counter(x for f in fit for x in f["f_k2"]); cf_rec = collections.Counter(x for f in rec for x in f["f_k2"])
print(f"  distinct fleets at k-2: fit {len(cf_fit)}, recent {len(cf_rec)}; recent fleets never seen at k-2 of a fit fire: {len(set(cf_rec) - set(cf_fit))}")
top = sorted(set(cf_fit) | set(cf_rec), key=lambda x: -(cf_fit[x] / max(1, len(fit)) + cf_rec[x] / max(1, len(rec))))[:14]
for x in top:
    a = [R(f) for f in fit if x in f["f_k2"]]; b = [R(f) for f in rec if x in f["f_k2"]]
    print(f"  {x[:12]}  fit {cf_fit[x]:3d} ({cf_fit[x]/max(1,len(fit)):4.0%}) mean {mn(a):+6.1%}   recent {cf_rec[x]:3d} ({cf_rec[x]/max(1,len(rec)):4.0%}) mean {mn(b):+6.1%}")
pairs_f = collections.Counter(tuple(sorted(f["f_k2"])) for f in fit); pairs_r = collections.Counter(tuple(sorted(f["f_k2"])) for f in rec)
print("  most common fleet sets at k-2: fit", [(tuple(y[:8] for y in p), n) for p, n in pairs_f.most_common(4)])
print("                                recent", [(tuple(y[:8] for y in p), n) for p, n in pairs_r.most_common(4)])
print("-- serial creators and named-wallet templates (over the whole population of both periods, crowd files)")
pop = c.load(c.FIT) + c.load(c.RECENT); cc = collections.Counter(r["creator"] for r in pop); nc = collections.Counter(tuple(r["named"]) for r in pop)
for g, S in (("fit", fit), ("recent", rec)):
    rep = [f for f in S if cc[f["creator"]] > 1]; tpl = [f for f in S if nc[tuple(f["named_set"])] > 1]
    print(f"  {g:7s} creator with >1 launch in the population: {len(rep)}/{len(S)} mean {mn([R(f) for f in rep]):+.1%} (others {mn([R(f) for f in S if cc[f['creator']] <= 1]):+.1%});  named set reused: {len(tpl)}/{len(S)} mean {mn([R(f) for f in tpl]):+.1%}")
