"""check_paths.py (edge_check/F): proves the one-pass pricer (common.paths) equal to the imported yardstick
(stake_scale.model_eff) at every hold 1..600 on all 92 fires and on a seeded sample of 60 refused launches, second place and
third place; checks the partial-exit arithmetic at its two limits; reproduces the committed numbers (reach_table.txt: fit 73 fires
+26.3% at 300 blocks, recent 18 fires +3.5%; round 2: +16.2% / +12.8% at 15).
    python3 data/derived/edge_check/F/check_paths.py > data/derived/edge_check/F/check_paths.txt"""
import sys, os, random, multiprocessing as mp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
R = load_all(); FI = [r for r in R if is_fire(r)]; random.seed(5); RF = random.sample([r for r in R if not is_fire(r)], 60)
def one(r):
    L = tape(r["cv"], ext=False); bE1 = seat_block(L); worst = 0.0; n = 0
    for na in (1, 2):
        p, g = paths(L, na, hmax=600)
        for h in range(1, 601):
            m, gg = model_eff(L, STAKE / E, bE1, na, h); worst = max(worst, abs(m - p[h]), abs(gg - g)); n += 1
    p, g = paths(L, 1, hmax=600); a, _ = paths(L, 1, hmax=600, partial=(15, 0.0)); b, _ = paths(L, 1, hmax=600, partial=(15, 1.0))
    part = max(max(abs(x - y) for x, y in zip(a[1:], p[1:])), max(abs(x - p[15]) for x in b[15:]))
    return r["cv"], worst, n, part, p[15], p[300], r["set"], r["win"]
with mp.Pool(6) as pool: res = pool.map(one, FI + RF)
print(f"paths vs model_eff: {len(res)} launches (92 fires + 60 refused), {sum(x[2] for x in res)} (launch, hold, place) pairs, max |difference| {max(x[1] for x in res):.2e}")
print(f"partial exit limits (fraction 0 = the fixed hold; fraction 1 at 15 = the 15-block exit at every later h): max |difference| {max(x[3] for x in res):.2e}")
fires = res[:len(FI)]
for s, wins in (("fit", FIT), ("recent, committed 11 windows", REC), ("recent with the gap fire", REC + GAPS)):
    v = [x for x in fires if x[7] in wins]
    print(f"{s:30s} {len(v):3d} fires  h15 {mean([x[4] for x in v]):+.2%}  h300 {mean([x[5] for x in v]):+.2%}")
