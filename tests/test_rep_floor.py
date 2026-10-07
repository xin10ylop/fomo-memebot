"""6.23 (runbook 5bd): the helpers' weight table and the reputation floor. rep_sum = the attacking relays' weights summed; logged on
every decision; with REP_GATE=1 the burst gate also needs rep_sum >= rep_min; without the switch (the live default: shadow) the gate
is the fleet count alone. A missing table means no floor."""
import os, sys, json, tempfile
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
WPATH = tempfile.mkdtemp() + "/w.json"
A, B, C, SPR = "0x" + "a1" * 20, "0x" + "b2" * 20, "0x" + "c3" * 20, "0x" + "d4" * 20
json.dump({"fitted": "test", "window_days": 7, "weights": {A: 0.27, B: -0.05, SPR: 0.16}, "rep_min": 0.25}, open(WPATH, "w"))
for k, v in (("SEAT", "E1"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("SHOOTER_KEYS", ""), ("ATTACK_MIN", "3"), ("REP_WEIGHTS_PATH", WPATH), ("REP_GATE", "0")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E
checks = 0
def ok(cond, what):
    global checks
    if not cond: raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)
logged = []; E.log = lambda d: logged.append(d)
E.rep_weights_load(force=True)
ok(E.state.get("rep_weights") == {A: 0.27, B: -0.05, SPR: 0.16} and E.state.get("rep_min") == 0.25, "the table loads: three weights, rep_min 0.25")
ok(any(d.get("ev") == "rep_weights" and d["n"] == 3 for d in logged), "the load is logged")
def w(*targets): return {"attack_targets": set(targets), "attack_senders": set(), "attack_wallets": set()}
ok(E.rep_sum(w(A, C)) == 0.27, "rep_sum: A's weight; an unknown relay counts 0")
ok(E.rep_sum(w(A, B, SPR)) == 0.38, "rep_sum sums every attacking relay, sprayers included, negatives included")
ok(E.rep_sum(w()) == 0.0, "no attackers: 0")
ok(E.rep_ok(w(C)) is True, "REP_GATE off (shadow): rep_ok is always true")
E.REP_GATE = True
ok(E.rep_ok(w(A)) is True and E.rep_ok(w(A, SPR)) is True, "REP_GATE on: at or above the floor passes")
ok(E.rep_ok(w(B, C)) is False and E.rep_ok(w(SPR)) is False, "REP_GATE on: below the floor refused")
E.state["rep_min"] = 0.0
ok(E.rep_ok(w(C)) is True, "a table without a floor (rep_min 0) never refuses")
E.state["rep_weights"] = {}; E.state["rep_min"] = 0.25
ok(E.rep_sum(w(A)) is None and E.rep_ok(w(C)) is True, "no table: rep_sum None, nothing refused")
# a stale or missing file leaves the table as it was
E.state["rep_weights"] = {A: 0.27}; E.state["rep_min"] = 0.25; E.REP_WEIGHTS_PATH = "/nonexistent/w.json"; logged.clear()
E.rep_weights_load(force=True)
ok(E.state["rep_weights"] == {A: 0.27} and any(d.get("ev") == "error" for d in logged), "a missing file: the table stays, the error is logged")
# the refit script's output shape
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "analysis", "helper_weights.py")).read()
ok('"weights"' in src and '"rep_min"' in src and "(len(v) + 4)" in src and "min(x, 1.0)" in src, "helper_weights.py writes weights = sum(min(r,1))/(n+4) and rep_min")
print(f"all {checks} checks passed")
