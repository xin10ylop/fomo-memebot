"""K1/q1_guard.py: the minOut guard. (a) what the reverted bursts would have returned (second place, and third / first as bounds);
(b) where the drop comes from (the creation second's late buys vs the buy ahead in E1); (c) the slip threshold swept, chosen on
one half and read on the other; (d) 'smart' guards: by fleets, by the buy ahead only (minOut sized at the tick), by the creation
second only. Usual view (k-1 with registration) unless noted; exit block 11; $13; gas $0.33 a burst."""
import sys, os, json, statistics as st, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from k1 import *
R = load(); TK = json.load(open(os.path.join(HERE, "tokens.json")))
def drop(r): return 1 - r["tk_seat1"] / r["tk_build"] if r["tk_build"] and r["tk_seat1"] else 0.0
print("== (a) the reverted bursts, priced (exit 11) ==")
for view in ("k-2", "k-1", "k"):
    D = decide(R, view=view)
    for part in ("fit", "read"):
        g = [d["r"] for d in D if d["why"] == "GUARD" and d["r"]["set"] == part]; f = [d["r"] for d in D if d["why"] == "FILL" and d["r"]["set"] == part]
        v2 = [r2(r, 11) for r in g]; v3 = [r["g_r3"][11] for r in g if r.get("g_r3")]; v1 = [r["p1"][11] for r in g if r.get("p1")]
        vf3 = [r["g_r3"][11] for r in f if r.get("g_r3")]
        print(f"  view {view:4s} {part:4s}: reverted {len(g):3d}  2nd {mean(v2):+6.1%} (med {st.median(v2) if v2 else float('nan'):+6.1%}, win {sum(x>0 for x in v2)/max(1,len(v2)):3.0%}, {len(v2)})"
              f"  3rd {mean(v3):+6.1%} ({len(v3)})  1st {mean(v1):+6.1%} ({len(v1)})  | fills {len(f):3d} 2nd {mean([r2(r,11) for r in f]):+6.1%} 3rd {mean(vf3):+6.1%} ({len(vf3)})")
print("\n== (b) the drop at second place against the build, split (taped launches that fire at k-1) ==")
D = decide(R, view="k-1"); fired = [d["r"] for d in D if d["why"] in ("FILL", "GUARD")]
rows = []
for r in fired:
    t = TK.get(r["cv"])
    if not t: continue
    cs = 1 - t["first"] / t["build"]; ah = 1 - t["seat1"] / t["first"]; tot = drop(r); a1 = (r.get("e1_buys") or [[None]])[0][0]
    rows.append((r, cs, ah, tot, a1))
for lab, sel in (("guard passes (fills)", lambda x: x[3] < 0.07), ("guard reverts", lambda x: x[3] >= 0.07)):
    s = [x for x in rows if sel(x)]
    print(f"  {lab:22s} n={len(s):3d}: creation-second part median {st.median([x[1] for x in s]):6.1%}, buy-ahead part median {st.median([x[2] for x in s]):6.1%}; "
          f"reverts caused by the creation second alone (>=7% before the buy ahead): {sum(x[1] >= 0.07 for x in s)}; first E1 buy median {st.median([x[4] for x in s if x[4] is not None]):.4f} ETH")
print("  the buy ahead's size (ETH) among the reverted, sorted:", sorted(round(x[4], 4) for x in rows if x[3] >= 0.07 and x[4] is not None))
print("\n== (c) the slip threshold (view k-1): fit | read ==")
SL = (0.05, 0.07, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30, 0.40, 1.0)
res = {}
for sl in SL:
    D = decide(R, view="k-1", slip=sl); res[sl] = (summ(D, "fit"), summ(D, "read"))
    print(f"  slip {sl:4.2f}: fit {fmt(res[sl][0])} | read {fmt(res[sl][1])}")
bf = max(SL, key=lambda s: res[s][0]["usd"]); br = max(SL, key=lambda s: res[s][1]["usd"])
print(f"  chosen on fit: {bf} -> read ${res[bf][1]['usd']:+.2f} vs 0.07 ${res[0.07][1]['usd']:+.2f};  chosen on read: {br} -> fit ${res[br][0]['usd']:+.2f} vs 0.07 ${res[0.07][0]['usd']:+.2f}")
for view in ("k-2", "k"):
    a = [summ(decide(R, view=view, slip=s), p) for s in (0.07, 1.0) for p in ("fit", "read")]
    print(f"  view {view}: slip 0.07 fit ${a[0]['usd']:+.2f} read ${a[1]['usd']:+.2f} | guard off fit ${a[2]['usd']:+.2f} read ${a[3]['usd']:+.2f} ({a[2]['fills']}/{a[3]['fills']} fills, mean {a[2]['mean']:+.1%}/{a[3]['mean']:+.1%})")
print("  the same with the reverted-and-now-filled priced at THIRD place (G r3; untaped kept at 2nd):")
for sl in (0.07, 0.10, 0.15, 0.20, 1.0):
    def rf(r, sl=sl): return (r["g_r3"][11] if (drop(r) >= 0.07 and r.get("g_r3")) else r2(r, 11))
    D = decide(R, view="k-1", slip=sl, ret_fn=rf); a, b = summ(D, "fit"), summ(D, "read")
    print(f"    slip {sl:4.2f}: fit ${a['usd']:+7.2f} ({a['fills']} fills {a['mean']:+.1%}) | read ${b['usd']:+7.2f} ({b['fills']} fills {b['mean']:+.1%})")
print("\n== (d) smart guards (view k-1) ==")
def by_fleets(nf, hi):
    return lambda r: drop(r) < (hi if r["f_k1r"] >= nf else 0.07)
cands = {f"slip 20% when fleets>={nf} else 7%": by_fleets(nf, 0.20) for nf in (3, 4, 5, 6)}
cands.update({f"off when fleets>={nf} else 7%": by_fleets(nf, 1.0) for nf in (3, 4, 5, 6)})
def ahead_only(sl):
    def f(r):
        t = TK.get(r["cv"])
        if not t: return drop(r) < 0.07
        return 1 - t["seat1"] / t["first"] < sl
    return f
def build_k1(sl):
    def f(r):
        t = TK.get(r["cv"])
        if not t: return drop(r) < 0.07
        return 1 - t["seat1"] / t["build_k1"] < sl
    return f
for sl in (0.07, 0.10, 0.15): cands[f"sized at the tick (buy ahead only) {int(sl*100)}%"] = ahead_only(sl)
cands["sized one block later (k-1 view) 7%"] = build_k1(0.07)
base = (summ(decide(R, view="k-1"), "fit"), summ(decide(R, view="k-1"), "read"))
print(f"  {'current 7%':46s} fit {fmt(base[0])} | read {fmt(base[1])}")
for nm, fn in cands.items():
    D = decide(R, view="k-1", guard_fn=fn); a, b = summ(D, "fit"), summ(D, "read")
    print(f"  {nm:46s} fit {fmt(a)} | read {fmt(b)}")
print("\n== (e) the reverted bursts by drop bucket, second place h11 (all views' k-1 fires) ==")
D = decide(R, view="k-1", slip=1.0); fr = [d["r"] for d in D if d["why"] == "FILL"]
for lo, hi in ((0, 0.07), (0.07, 0.10), (0.10, 0.15), (0.15, 0.20), (0.20, 0.30), (0.30, 1.0)):
    for part in ("fit", "read"):
        v = [r2(r, 11) for r in fr if lo <= drop(r) < hi and r["set"] == part]
        print(f"  drop {lo:4.2f}-{hi:4.2f} {part:4s}: n={len(v):3d} mean {mean(v):+6.1%} median {st.median(v) if v else float('nan'):+6.1%} win {sum(x>0 for x in v)/max(1,len(v)):3.0%}")
print("\n== (f) gas: every fired burst pays $0.33 whether it fills or reverts ==")
for part in ("fit", "read"):
    a = base[0] if part == "fit" else base[1]; print(f"  {part}: {a['guard']} reverted bursts = ${a['guard']*GAS:.2f} of gas; {a['fills']} fills")
