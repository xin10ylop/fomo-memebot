"""build.py (edge_check/F): prices every launch of the population (735: 563 fit, 172 recent) at every hold h = 0..1200 blocks after
the seat, second place (n_ahead 1, the yardstick) and third place (n_ahead 2, for the live mix), with common.paths (= model_eff at
every h, check_paths.py), on the tapes b0..b0+1240 (the caches + ext.json.gz). Writes F/paths.npz (P2 second place, P3 third
place, G effective stake in ETH) and F/meta.json (cv, set, window, T0, day, k, fleets at k-2, fire).
    python3 data/derived/edge_check/F/build.py"""
import sys, os, json, multiprocessing as mp, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
R = load_all()
def one(r):
    L = tape(r["cv"]); p2, g = paths(L, 1); p3, _ = paths(L, 2)
    return [np.nan if x is None else x for x in p2], [np.nan if x is None else x for x in p3], g, L["reach"] - L["b0"]
if __name__ == "__main__":
    with mp.Pool(4) as pool: res = pool.map(one, R)
    P2 = np.array([x[0] for x in res]); P3 = np.array([x[1] for x in res]); G = np.array([x[2] for x in res])
    meta = [{"cv": r["cv"], "set": r["set"], "win": r["win"], "T0": r["T0"], "day": day(r["T0"]), "k": r["k"], "f_k2": fleets_k2(r), "fire": is_fire(r)} for r in R]
    np.savez_compressed(F + "paths.npz", P2=P2, P3=P3, G=G); json.dump(meta, open(F + "meta.json", "w"))
    reach = [x[3] for x in res]
    print(f"{len(R)} launches priced at h 0..{HMAX}; tape reach b0+{min(reach)}..b0+{max(reach)}; holds with a price on every launch: 0..{int(np.where(np.isnan(P2).any(axis=0))[0].min()) - 1 if np.isnan(P2).any() else HMAX}")
