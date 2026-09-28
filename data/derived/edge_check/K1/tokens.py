"""K1/tokens.py: the guard's decomposition. For every taped launch, the tokens $13 buys (hold_grid.model_path, the grid's own
function) at the build (k-2 view: rows <= bE1-3), at the tick with the whole creation second folded (first place in E1), behind
one, behind two; so the guard's drop splits into the creation second's late buys (build -> first) and the buy ahead (first -> second).
Writes K1/tokens.json."""
import os, sys, io, json, contextlib, runpy
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")); os.chdir(ROOT)
sys.path.insert(0, "src/analysis"); import hold_grid as hg
sys.argv = ["x"]
with contextlib.redirect_stdout(io.StringIO()):
    GC = runpy.run_path("data/derived/edge_check/G/common.py", run_name="gcommon")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from k1 import load
out = {}
for r in load():
    L = GC["tape"](r["cv"], ext=False)
    if L is None: continue
    bE1 = GC["seat_block"](L)
    if bE1 is None: continue
    o = {}
    for nm, na in (("first", 0), ("seat1", 1), ("seat2", 2), ("last", 10 ** 6)):
        info = {}; hg.model_path(L, 13.0 / 2570.0, bE1, na, (11,), info=info); o[nm] = info.get("tk")
    Lb = dict(L); Lb["rows"] = [x for x in L["rows"] if x["bn"] <= bE1 - 3]; info = {}; hg.model_path(Lb, 13.0 / 2570.0, bE1, 0, (11,), info=info); o["build"] = info.get("tk")
    Lk = dict(L); Lk["rows"] = [x for x in L["rows"] if x["bn"] <= bE1 - 2]; info = {}; hg.model_path(Lk, 13.0 / 2570.0, bE1, 0, (11,), info=info); o["build_k1"] = info.get("tk")   # sized one block later (k-1 view)
    out[r["cv"]] = o
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tokens.json"), "w"))
m = [(abs(out[r["cv"]]["seat1"] / r["tk_seat1"] - 1), abs(out[r["cv"]]["build"] / r["tk_build"] - 1)) for r in load() if r["cv"] in out and r["tk_seat1"] and r["tk_build"]]
print(f"{len(out)} taped launches; vs the grid's guard inputs on {len(m)}: max |seat1 ratio - 1| {max(a for a, b in m):.2e}, max |build ratio - 1| {max(b for a, b in m):.2e}")
