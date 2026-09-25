"""guard.py: on the cached tapes (tapes.py), (1) the burst's minOut guard: the build quotes our $13 at the curve state after block
k-2 (view "k-1" as the lenient case) with the engine's sizing (size_buy: TIER_ASSUMED 0.05 + SURCHARGE E1 0.0618), minOut = 75%
of it (BURST_SLIP 0.25); the modelled fill (hold_grid.model_path, behind one in the seat block, $13) below minOut = no fill, scored
-gas; (2) the creator's buy as a share of supply (the launch block's first Buy), for MIN_CREATOR_SUPPLY. Re-scores the baseline and
the nine variants with the guard, and tests the creator-supply threshold as an AND-filter on the baseline gate.
    cd /home/user/fomo-memebot && python3 <B>/guard.py"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
sys.path.insert(0, os.path.join(REPO, "src/analysis")); from hold_grid import model_path
from live_vs_table import fold_buy, fold_sell, X0, Y0, OURS
from variants import PASSED
HERE = os.path.dirname(os.path.abspath(__file__)); TD = os.path.join(HERE, "tapes")
E, TIER_ASSUMED, SUR_E1, SLIP = 2570.0, 0.05, 0.0618, 0.25
W = load()
G = {}; chk = []
for n in FIT_NAMES + VAL_NAMES:
    for r in W[n]["rows"]:
        f = os.path.join(TD, r["cv"] + ".json")
        if not os.path.exists(f): continue
        L = json.load(open(f)); L["ts"] = {int(a): b for a, b in L["ts"].items()}; ts, T0, b0 = L["ts"], L["T0"], L["b0"]
        bE1 = next((m for m in range(b0 + 1, b0 + 30) if ts.get(m, 0) == T0 + 1), None)
        if bE1 is None or L["tier"] is None: continue
        rows = [x for x in L["rows"] if x["who"] not in OURS]
        buys0 = [x for x in rows if x["bn"] == b0 and x["k"] == "B"]; cs = buys0[0]["tk"] / Y0 if buys0 else None
        out = {"cs": cs}
        for tag, j in (("k-2", r["k"] - 2), ("k-1", r["k"] - 1)):
            X, Y = X0, Y0
            for x in rows:
                if x["bn"] > b0 + j: break
                if x["k"] == "B":
                    if 0 < x["tk"] < Y: X, Y = fold_buy(X, Y, x["tk"])
                else: X, Y = fold_sell(X, Y, x["tk"])
            stake_eth = STAKE / E; net = stake_eth * (1 - TIER_ASSUMED - SUR_E1); quote = Y * net / (X + net)
            quote = min(quote, 0.03 * Y0)
            info = {}; model_path(L, stake_eth, bE1, 1, (15,), info=info)
            out["refused_" + tag] = info["tk"] < quote * (1 - SLIP); out["ratio_" + tag] = info["tk"] / quote
        o15 = model_path(L, 15.0 / E, bE1, 1, (15,))[15]; chk.append(abs(o15 - r["ret"]["behind1_15_h15"]))
        G[r["cv"]] = out
print(f"tapes read: {len(G)}; model check against hold_grid behind1_15_h15: max |diff| {max(chk):.2e}, launches with |diff|>1e-6: {sum(c > 1e-6 for c in chk)}")
def ret_g(r, key, view):
    g = G.get(r["cv"])
    if g is not None and g["refused_" + view]: return -GAS / STAKE
    return r["ret"][key]
def ev(names, rule, key, view):
    per = collections.OrderedDict(); pool = []; hrs = 0; miss = 0
    for n in names:
        rets = []
        for r in W[n]["rows"]:
            if not rule(r): continue
            if r["cv"] not in G: miss += 1
            rets.append(ret_g(r, key, view) if view else r["ret"][key])
        per[n] = metrics(rets, W[n]["hours"]); pool += rets; hrs += W[n]["hours"]
    return per, metrics(pool, hrs), miss
for view in ("k-2", "k-1"):
    print(f"\n=== minOut guard with the build's quote at block {view}: refused fills scored -gas")
    bf_per, bf, m1 = ev(FIT_NAMES, BASE, "behind1_15_h300", view); bv_per, bv, m2 = ev(VAL_NAMES, BASE, "behind1_15_h300", view)
    ref = [r["cv"][:10] for n in FIT_NAMES + VAL_NAMES for r in W[n]["rows"] if BASE(r) and G.get(r["cv"], {}).get("refused_" + view)]
    print(f"  baseline fires refused by the guard: {len(ref)} of 85 ({', '.join(ref)}); launches without a tape: {m1 + m2}")
    for n, m in list(bf_per.items()) + [("FIT pooled", bf)] + list(bv_per.items()) + [("VAL pooled", bv)]: print("   " + fmt(m, n))
    for label, rule, key in PASSED:
        fp, f, ma = ev(FIT_NAMES, rule, key, view); vp, v, mb = ev(VAL_NAMES, rule, key, view)
        cr = (f["usd_day"] > bf["usd_day"], all(m["n"] and m["usd_burst"] > 0 for m in fp.values()), v["usd_total"] >= bv["usd_total"] and v["mean"] >= bv["mean"],
              f["win"] >= bf["win"] - 0.1 and f["dead"] <= bf["dead"] + 0.05, f["n"] >= 30)
        refd = sum(1 for n in FIT_NAMES + VAL_NAMES for r in W[n]["rows"] if rule(r) and not BASE(r) and G.get(r["cv"], {}).get("refused_" + view))
        print(f"  {label:40s} {key[-5:]}  FIT n={f['n']:3d} {f['mean']:+6.1%} win {f['win']:3.0%} dead {f['dead']:3.0%} ${f['usd_day']:5.1f}/d | VAL n={v['n']:2d} {v['mean']:+6.1%} ${v['usd_total']:+6.1f}"
              f" | {''.join(k_ if ok else '-' for k_, ok in zip('abcde', cr))}  (added launches refused by the guard: {refd}; no tape: {ma + mb})")
print("\n=== the creator-supply filter on the baseline gate (creator's launch-block buy / supply; the engine runs >= 1%)")
dist = sorted(G[r["cv"]]["cs"] for n in FIT_NAMES + VAL_NAMES for r in W[n]["rows"] if BASE(r) and r["cv"] in G and G[r["cv"]]["cs"] is not None)
print(f"  baseline fires: creator share quartiles {[round(dist[int(len(dist) * q)], 4) for q in (0.1, 0.25, 0.5, 0.75, 0.9)]}; below 1%: {sum(x < 0.01 for x in dist)} of {len(dist)}")
bf_per, bf = evaluate(W, FIT_NAMES, BASE); bv_per, bv = evaluate(W, VAL_NAMES, BASE)
for thr in (0.0, 0.005, 0.01, 0.02, 0.03, 0.05):
    rule = lambda r, thr=thr: BASE(r) and (G.get(r["cv"], {}).get("cs") or 0) >= thr
    fp, f = evaluate(W, FIT_NAMES, rule); vp, v = evaluate(W, VAL_NAMES, rule)
    cr = (f["usd_day"] > bf["usd_day"], all(m["n"] and m["usd_burst"] > 0 for m in fp.values()), v["usd_total"] >= bv["usd_total"] and v["mean"] >= bv["mean"], f["win"] >= bf["win"] - 0.1 and f["dead"] <= bf["dead"] + 0.05, f["n"] >= 30)
    print(f"  creator >= {thr:5.1%}: FIT n={f['n']:3d} {f['mean']:+6.1%} win {f['win']:3.0%} dead {f['dead']:3.0%} ${f['usd_day']:5.1f}/d  per-window $/burst " + " ".join(f"{m['usd_burst']:+5.2f}" for m in fp.values())
          + f" | VAL n={v['n']:2d} {v['mean']:+6.1%} ${v['usd_total']:+6.1f} | {''.join(k_ if ok else '-' for k_, ok in zip('abcde', cr))}")

print("\n=== everything the engine does in front of the gate that can be approximated, on BOTH sides: creator buy >= 1% of supply, creator repeat,")
print("    k<=2 (un-aimable), one position at a time (hold/10 s), and the minOut guard (build quote at k-2) scored -gas")
HB = lambda key: 600 if "h600" in key else int(key.split("_h")[-1])
def eng(names, rule, key):
    per = collections.OrderedDict(); pool = []; hrs = 0
    for n in names:
        busy = -1; rets = []
        for r in W[n]["rows"]:
            g = G.get(r["cv"])
            if not rule(r) or r["creator_repeat"] or r["k"] <= 2: continue
            assert g is not None, r["cv"]
            if (g["cs"] or 0) < 0.01 or r["T0"] < busy: continue
            busy = r["T0"] + HB(key) / 10.0; rets.append(-GAS / STAKE if g["refused_k-2"] else r["ret"][key])
        per[n] = metrics(rets, W[n]["hours"]); pool += rets; hrs += W[n]["hours"]
    return per, metrics(pool, hrs)
ebp, ebf = eng(FIT_NAMES, BASE, "behind1_15_h300"); evp, ebv = eng(VAL_NAMES, BASE, "behind1_15_h300")
print("  baseline  " + fmt(ebf, "FIT") + "\n            " + fmt(ebv, "VAL"))
for label, rule, key in PASSED:
    fp, f = eng(FIT_NAMES, rule, key); vp, v = eng(VAL_NAMES, rule, key)
    cr = (f["usd_day"] > ebf["usd_day"], all(m["n"] and m["usd_burst"] > 0 for m in fp.values()), v["usd_total"] >= ebv["usd_total"] and v["mean"] >= ebv["mean"],
          f["win"] >= ebf["win"] - 0.1 and f["dead"] <= ebf["dead"] + 0.05, f["n"] >= 30)
    print(f"  {label:40s} {key[-5:]}  FIT n={f['n']:3d} {f['mean']:+6.1%} win {f['win']:3.0%} dead {f['dead']:3.0%} ${f['usd_day']:5.1f}/d | VAL n={v['n']:2d} {v['mean']:+6.1%} ${v['usd_total']:+6.1f} | {''.join(k_ if ok else '-' for k_, ok in zip('abcde', cr))}")
