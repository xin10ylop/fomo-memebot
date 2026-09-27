"""common.py (reviewer B): the crowd files, the rule's fires (fleets >= 2 at k-2, exactly as src/analysis/reach_table.py),
the cached tapes. Imported by every other script here. Run from the repository root."""
import json, gzip, os, sys, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
os.chdir(ROOT); sys.path.insert(0, os.path.join(ROOT, "src/analysis"))
_saved = list(sys.argv); sys.argv = ["x", "0.76", "0.71"]
exec(open("src/analysis/crowd_rules.py").read().split("rules = [")[0])          # cums, at, view, US
sys.argv = _saved
D = "data/derived/live_vs_table/"; B = "data/derived/edge_check/B/"
FIT = ["sep1819", "sep2021", "sep2223", "sep23day"]
RECENT = ["sep24paper", "sep25night", "sep25am", "sep25pm", "sep25eve", "sep25eve2", "sep26night", "sep26am", "sep26pm", "sep26restart", "sep27night"]
HOURS = {"fit": 96.0, "recent": 60.0}
def load(files, dedup=True):
    out, seen = [], set()
    for f in files:
        for r in json.load(gzip.open(D + f"crowd_raw_{f}.json.gz", "rt")):
            if dedup and r["cv"] in seen: continue
            seen.add(r["cv"]); r["win"] = f; out.append(r)
    return out
def fleets_by_block(r):
    """per block offset 0..k+1, the set of fleet ids (relay target for relayed shots, sender for direct), the engine's exclusions"""
    out = []
    for rows in r["blocks"]:
        s = []
        for t in rows:
            if t["to"] in US or t["to_token"] or t["fr"] in US: continue
            if t["direct"]:
                if not t["named_fr"]: s.append(("D", t["fr"]))
            elif not t["named_data"]: s.append(("R", t["to"]))
        out.append(s)
    return out
def is_fire(r):
    cw, cf = cums(r); return at(cf, r["k"] - 2) >= 2
def fires(files): return [r for r in load(files) if is_fire(r)]
def tape(cv):
    p = B + f"tapes/{cv}.json"
    return json.load(open(p)) if os.path.exists(p) else None
def hhmm(T): return time.strftime("%b %d %H:%M", time.gmtime(T))
