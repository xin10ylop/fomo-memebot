"""yardstick.py (edge_check/A): test 1, the same yardstick for the fit fires and the recent fires. Checks, per set: the crowd
files' token field (the approvals fix of Sep 24), k in the crowd file against the tape's own block stamps, tier and bundle
bands (the population filters), the 3% cap at $13, the ETH-price sensitivity of the return, the tape reaching past the
300-block exit, and the engine's creator-supply pre-gate filter (creator's own creation-block buy >= 1% of supply).
    python3 data/derived/edge_check/A/yardstick.py"""
import sys, json, gzip, statistics as st
sys.path.insert(0, "data/derived/edge_check/A"); from common import *
import price as P   # re-uses the independent model (runs price.py's top level: prints its summary first)
F = json.load(open(A + "fires.json")); T = P.T
print("\n=== yardstick checks")
for name in ("fit", "rec"):
    S = [x for x in F if x["set"] == name]; raw = {r["cv"]: r for r in all_launches(FIT if name == "fit" else REC)}
    tok_none = sum(1 for x in S if not raw[x["cv"]].get("token")); tok_all = sum(1 for r in raw.values() if not r.get("token"))
    kbad = [x["cv"][:10] for x in S if x["bE1"] - x["b0"] - 1 != x["k"]]
    tiers = sorted({round(x["tier"], 4) for x in S}); bund = [x["bundle_eth"] for x in S if x["bundle_eth"] is not None]
    tape_short = [x["cv"][:10] for x in S if T[x["cv"]]["hi"] < x["bE1"] + 300]
    capped = 0; eth_sens = []
    for x in S:
        L = T[x["cv"]]
        r1 = P.my_model(L)[300]; P.ETH = 1800.0; r2 = P.my_model(L)[300]; P.ETH = 3500.0; r3 = P.my_model(L)[300]; P.ETH = 2570.0
        eth_sens.append((r2 - r1, r3 - r1))
    print(f"{name}: fires {len(S)}; crowd files with no token (approvals would count as fleets): fires {tok_none}, all launches {tok_all}; k != tape's (bE1-b0-1): {kbad}")
    print(f"     tiers {tiers}; bundle ETH min {min(bund):.3f} median {st.median(bund):.3f} max {max(bund):.3f} (n {len(bund)}); tapes short of the exit: {tape_short}")
    print(f"     return change if ETH were $1,800 / $3,500 instead of $2,570: max |{max(abs(a) for a, b in eth_sens):.4f}| / |{max(abs(b) for a, b in eth_sens):.4f}|")
# the creator-supply pre-gate filter: the creator's own buys in the creation second, tokens / 1e9
print("\n=== the engine's creator-supply filter (creator buy >= 1% of supply in the creation second) applied to both sets")
for name in ("fit", "rec"):
    S = [x for x in F if x["set"] == name]; keep = []; drop = []
    for x in S:
        L = T[x["cv"]]; ts = {int(k): v for k, v in L["ts"].items()}
        cs = sum(r["tk"] for r in L["rows"] if r["k"] == "B" and r["who"] == x["creator"] and ts.get(r["bn"]) == L["T0"]) / 1e9
        x["creator_share"] = cs; (keep if cs >= 0.01 else drop).append(x["ret"]["300"] if "300" in x["ret"] else x["ret"][300])
    d = lambda v: f"{len(v):3d} mean {st.mean(v):+6.1%} win {sum(y > 0 for y in v)/len(v):4.0%}" if v else "  0"
    print(f"{name}: creator >= 1%: {d(keep)}   creator < 1% (the engine skips): {d(drop)}")
