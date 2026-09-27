"""check_curve.py (edge_check/G): (1) curve() equals stake_scale.model_eff at h = 1, 2, 5, 15, 37, 60, 150, 300, 451, 600 on every launch
(tape to b0+640) and at h = 800, 1000, 1200 on the extended tapes; also at third place (n_ahead=2). (2) The yardstick reproduces
rounds 1-2: fit 73 fires h15 +16.2% / h300 +26.3%; recent 18 fires +12.8% / +3.5%; with the gaps 19 fires +12.6% / +3.0%.
(3) partial() with frac=1 equals the single exit. (4) tape reach: how many launches reach E1+600 and E1+1200.
    python3 data/derived/edge_check/G/check_curve.py > data/derived/edge_check/G/check_curve.txt"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
R = load_all(); dmax = 0.0; dmax_ext = 0.0; dmax3 = 0.0; dpart = 0.0; n = 0; reach600 = reach1200 = 0
res = {"fit": {15: [], 300: []}, "rec": {15: [], 300: []}, "rec18": {15: [], 300: []}}
for r in R:
    L = tape(r["cv"], ext=False); v, g = curve(L, 1, hmax=600)
    if v is None: continue
    e1 = seat_block(L)
    for h in (1, 2, 5, 15, 37, 60, 150, 300, 451, 600):
        if v[h] is not None: dmax = max(dmax, abs(v[h] - model_eff(L, STAKE / E, e1, 1, h)[0])); n += 1
    reach600 += v[600] is not None
    if is_fire(r) or n % 7 == 0:
        v3, _ = curve(L, 2, hmax=300); dmax3 = max(dmax3, abs(v3[60] - model_eff(L, STAKE / E, e1, 2, 60)[0]))
        dpart = max(dpart, abs(partial(L, 40, 40, frac=1.0) - v[40]))
    LX = tape(r["cv"]); vx, _ = curve(LX, 1)
    if vx[1200] is not None:
        reach1200 += 1
        for h in (15, 300, 800, 1000, 1200): dmax_ext = max(dmax_ext, abs(vx[h] - model_eff(LX, STAKE / E, e1, 1, h)[0]))
    if is_fire(r):
        for h in (15, 300):
            res[r["set"]][h].append(v[h])
            if r["rec18"]: res["rec18"][h].append(v[h])
print(f"curve() vs model_eff: {n} (launch, h) pairs up to h600, max |diff| {dmax:.2e}; third place at h60 max {dmax3:.2e}; extended tapes h<=1200 max {dmax_ext:.2e}; partial(frac=1) vs single exit max {dpart:.2e}")
print(f"launches {len(R)}; reach E1+600 on the b0+640 tapes: {reach600}; reach E1+1200 on the extended tapes: {reach1200}")
for k in ("fit", "rec18", "rec"):
    print(f"{k:6s} fires {len(res[k][15]):3d}: h15 {mean(res[k][15]):+.1%}  h300 {mean(res[k][300]):+.1%}")
