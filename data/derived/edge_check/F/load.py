"""load.py (edge_check/F): the priced paths (build.py) as numpy arrays, and the sets every script uses. No RPC, no pricing.
Sets: fit (Sep 18-23, 4 windows), rec (Sep 24-27 with the gap pulls: 172 launches, 19 fires), each fit window, each UTC day of T0."""
import json, os, numpy as np, math, time
F = os.path.dirname(os.path.abspath(__file__)) + "/"
_z = np.load(F + "paths.npz"); P2, P3, G = _z["P2"], _z["P3"], _z["G"]; META = json.load(open(F + "meta.json"))
FIRE = np.array([m["fire"] for m in META]); SET = np.array([m["set"] for m in META]); WIN = np.array([m["win"] for m in META])
DAY = np.array([m["day"] for m in META]); T0 = np.array([m["T0"] for m in META])
E, GAS, STAKE = 2570.0, 0.33, 13.0
FITW = ["sep1819", "sep2021", "sep2223", "sep23day"]
DAYS = ["Sep 18", "Sep 19", "Sep 20", "Sep 21", "Sep 22", "Sep 23", "Sep 24", "Sep 25", "Sep 26", "Sep 27"]
def mask(name):
    """a set of launches by name: fit, rec, rec18 (the committed 11 windows, no gap pulls), a window name, a day 'Sep 18',
    'early' (Sep 18-21 by day), 'late' (Sep 22-27), 'all'"""
    if name == "fit": return SET == "fit"
    if name == "rec": return SET == "rec"
    if name == "rec18": return (SET == "rec") & ~np.isin(WIN, ["gapA", "gapB"])
    if name == "all": return np.ones(len(META), bool)
    if name == "early": return np.isin(DAY, DAYS[:4])
    if name == "late": return np.isin(DAY, DAYS[4:])
    if name in DAYS: return DAY == name
    return WIN == name
def usd(ret_row, g_row): return ret_row * g_row[:, None] * E - GAS if ret_row.ndim == 2 else ret_row * g_row * E - GAS
def stats(M, g):
    """per hold (columns): n, mean, median, win, dead, sd, se, $/fire after gas"""
    n = M.shape[0]; m = M.mean(0); sd = M.std(0, ddof=1) if n > 1 else np.full(M.shape[1], np.nan)
    return {"n": n, "mean": m, "median": np.median(M, 0), "win": (M > 0).mean(0), "dead": (M < -0.4).mean(0), "sd": sd, "se": sd / math.sqrt(n) if n > 1 else sd,
            "usd": (M * g[:, None] * E).mean(0) - GAS}
