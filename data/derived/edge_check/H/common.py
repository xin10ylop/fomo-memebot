"""common.py (edge_check/H): the population, both fire counts, the returns, the bundle and the named-wallet sets, for every
reviewer-H script. Run from anywhere; it chdirs to the repo root. No RPC: every number comes from files in the repo.

Population: the crowd files in this order, de-duplicated by curve (first file wins):
  fit    sep1819 sep2021 sep2223 sep23day                                         (data/derived/live_vs_table/crowd_raw_*.json.gz)
  recent sep24paper sep25night sep25am sep25pm sep25eve sep25eve2 sep26night sep26am sep26pm sep26restart sep27night sep27pm
         sep27eve, then gapA gapB (data/derived/edge_check/A/crowd_raw_gap*.json.gz)
Fires:
  tables  crowd_rules.cums/at: fleets >= 2 at block k-2 (reach_table.py's count)
  engine  src/analysis/fleet_variants.py fleets_k2(r, engine=True) >= 2 (shots only in blocks after the first named buy's block);
          the function is exec'd from the file itself, not copied.
Returns: edge_check/G/curves.json.gz r2[h] (second place in E1, $13, exit h blocks after E1, model_eff). sep27pm and sep27eve (24
  launches) are NOT in curves.json.gz and have no tape in the repo; for them h15 is hold_grid_sep27{pm,eve}.json behind1_15_h15
  (second place, $15, same fold; equals r2[15] to a median 0.00007 on the 166 recent launches that have both, max 1.3 points on a
  +167% launch: check.py), and h11 is taken equal to h15 ONLY when the launch is flat (behind1_15 h15 == h30 == h60 to 1e-9 and
  first_15 h15 == behind1_15 h15: no trade after the seat through block 60); otherwise h11 is None and the launch is left out of
  h11 statistics (reported).
Bundle ETH: recomputed from the tape rows exactly as src/analysis/e1_multi.py does (creation-second buys after the first whose fee
  equals the tier within 0.0008); for the 24 tape-less launches, launches_sep27{pm,eve}.json bundle_eth (e1_multi's own output).
  check.py compares the recomputation with the launches files on every recent launch that has both."""
import json, gzip, os, sys, math, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
os.chdir(ROOT); sys.path.insert(0, os.path.join(ROOT, "src/analysis"))
_argv = list(sys.argv); sys.argv = ["x", "0.76", "0.71"]
exec(open("src/analysis/crowd_rules.py").read().split("rules = [")[0])                    # cums, at, US
_fv = open("src/analysis/fleet_variants.py").read()
exec(_fv[_fv.index("def fleets_k2"): _fv.index("seen = set()")])                          # fleets_k2(r, nohelper, engine) verbatim
sys.argv = _argv
LV = "data/derived/live_vs_table/"; EC = "data/derived/edge_check/"; H = EC + "H/"
FIT = ["sep1819", "sep2021", "sep2223", "sep23day"]
REC = ["sep24paper", "sep25night", "sep25am", "sep25pm", "sep25eve", "sep25eve2", "sep26night", "sep26am", "sep26pm", "sep26restart",
       "sep27night", "sep27pm", "sep27eve", "gapA", "gapB"]
NOCURVE = ["sep27pm", "sep27eve"]
STAKE = 13.0; GAS = 0.33; ETHUSD = 2570.0; FIT_HOURS = 96.0
X0, Y0 = 1.68, 1e9
def raw(w): return json.load(gzip.open((EC + "A/" if w.startswith("gap") else LV) + f"crowd_raw_{w}.json.gz", "rt"))
def launches_file(w):
    p = {"gapA": EC + "A/launches_gapA.json", "gapB": EC + "A/launches_gapB.json", "sep24paper": LV + "launches_sep24_paper.json"}.get(w, LV + f"launches_{w}.json")
    L = json.load(open(p)); return L["launches"] if isinstance(L, dict) else L
_C = None
def curves():
    global _C
    if _C is None: _C = {c["cv"]: c for c in json.load(gzip.open(EC + "G/curves.json.gz", "rt"))}
    return _C
def hold_grid(w): return {h["cv"]: h for h in json.load(open(LV + f"hold_grid_{w}.json"))}
def fold_buy(X, Y, tk): return X + X * tk / (Y - tk), Y - tk
def fold_sell(X, Y, tk): return X - X * tk / (Y + tk), Y + tk
def bundle_from_tape(L):
    """e1_multi.py's bundle_eth on a cached tape: creation-second buys after the first row whose fee equals the tier (0.0008)"""
    rows = sorted(L["rows"], key=lambda r: (r["bn"], r["li"])); ts = {int(k): v for k, v in L["ts"].items()}; T0 = L["T0"]; tier = L["tier"]
    X, Y = X0, Y0; b = 0.0; i = 0
    while i < len(rows) and ts.get(rows[i]["bn"], 9e18) == T0:
        r = rows[i]
        if r["k"] == "B":
            tk, eth = r["tk"], r["eth"]
            if 0 < tk < Y:
                net = X * tk / (Y - tk); fee = 1 - net / eth if eth > 0 else 1; X, Y = fold_buy(X, Y, tk)
                if i > 0 and abs(fee - tier) <= 0.0008: b += eth
        else: X, Y = fold_sell(X, Y, r["tk"])
        i += 1
    return b
_TP = {}
def _tapes():
    """the cached tapes to b0+640 (G/common.py's sources, same priority)"""
    if _TP: return _TP
    for f in ("A/tapes.json.gz", "A/tapes_gapA.json.gz", "A/tapes_gapB.json.gz", "A/tapes_chk27.json.gz", "C/tapes_extra.json.gz"):
        for cv, L in json.load(gzip.open(EC + f, "rt")).items(): _TP.setdefault(cv, L)
    for d in ("B/tapes/", "D/tapes/"):
        for f in os.listdir(EC + d):
            if f.endswith(".json") and f[:-5] not in _TP: _TP[f[:-5]] = json.load(open(EC + d + f))
    return _TP
def load(cache=True):
    """every launch of the population with: cv win set T0 k named creator f_tab f_eng fire_tab fire_eng r11 r15 g bundle bundle_src"""
    cp = H + "pop.json.gz"
    if cache and os.path.exists(cp): return json.load(gzip.open(cp, "rt"))
    C = curves(); TP = _tapes(); seen = set(); out = []
    for w in FIT + REC:
        lf = {l["cv"]: l for l in launches_file(w)} if w not in FIT else {}
        hg = hold_grid(w) if w in NOCURVE else {}
        for r in raw(w):
            if r["cv"] in seen: continue
            seen.add(r["cv"]); cw, cf = cums(r)
            x = {"cv": r["cv"], "win": w, "set": "fit" if w in FIT else "rec", "T0": r["T0"], "k": r["k"], "named": sorted(r["named"]),
                 "creator": r.get("creator"), "f_tab": at(cf, r["k"] - 2), "f_eng": fleets_k2(r, engine=True)[0]}
            x["fire_tab"] = x["f_tab"] >= 2; x["fire_eng"] = x["f_eng"] >= 2
            c = C.get(r["cv"])
            if c is not None:
                x["r11"], x["r15"], x["g"], x["ret_src"] = c["r2"][11], c["r2"][15], c["g"], "G/curves"
            else:
                h = hg[r["cv"]]; v15 = h["behind1_15_h15"]
                flat = abs(h["behind1_15_h30"] - v15) < 1e-9 and abs(h["behind1_15_h60"] - v15) < 1e-9 and abs(h["first_15_h15"] - v15) < 1e-9
                x["r11"], x["r15"], x["g"], x["ret_src"] = (v15 if flat else None), v15, STAKE / ETHUSD, "hold_grid" + ("(flat)" if flat else "")
            if r["cv"] in TP: x["bundle"], x["bundle_src"] = bundle_from_tape(TP[r["cv"]]), "tape"
            else: x["bundle"], x["bundle_src"] = lf[r["cv"]]["bundle_eth"], "launches_file"
            x["bundle_file"] = lf[r["cv"]]["bundle_eth"] if r["cv"] in lf else None
            out.append(x)
    out.sort(key=lambda x: x["T0"])
    json.dump(out, gzip.open(cp, "wt")); return out
def spans(pop, wins):
    """distinct hours covered by the windows' T0 spans [min T0, max T0] (union of intervals)"""
    iv = sorted((min(x["T0"] for x in pop if x["win"] == w), max(x["T0"] for x in pop if x["win"] == w)) for w in wins if any(x["win"] == w for x in pop))
    tot = 0; cur = None
    for a, b in iv:
        if cur is None or a > cur[1]: tot += (cur[1] - cur[0]) if cur else 0; cur = [a, b]
        else: cur[1] = max(cur[1], b)
    tot += cur[1] - cur[0]; return tot / 3600
def usd(ret, g=STAKE / ETHUSD): return ret * g * ETHUSD - GAS
def mean(v): return sum(v) / len(v) if v else float("nan")
def hms(t): return time.strftime("%b %d %H:%M", time.gmtime(t))
