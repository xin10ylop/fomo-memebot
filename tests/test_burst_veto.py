"""6.26 (runbook 5bk): the send step's veto (the runner's ceiling on the crowd). Asked before every shot from the first; once true no
later shot is sent; a veto that raises stops the burst; without a veto (the sniper) every shot goes as before, and a gate still works.
The engine side: the veto only for an ATTACK_MAX burst, emulated in dry run, a burst vetoed before its first shot is a refusal."""
import os, sys, json, time, types
from eth_account import Account
from eth_utils import to_checksum_address
os.environ["PRIVATE_KEY"] = "0x" + "11" * 32
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "deploy"))
import send_step
checks = 0
def ok(cond, what):
    global checks
    if not cond: raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)
KEYS = ["0x" + ("b%d" % (i % 9 + 1)) * 32 for i in range(6)]
def tx(i): return {"nonce": hex(5), "gasPrice": hex(100 + i), "gas": hex(250_000), "to": to_checksum_address("0xe8e98c3514d5bd83fdd01360896f2382b861a720"), "value": hex(0), "data": "0x" + "ab" * 36, "chainId": 4663}
fired = []; logged = []
engine = types.SimpleNamespace(mono=time.monotonic, state={}, log=lambda d: logged.append(d),
                               SENDER=types.SimpleNamespace(fire_slot=lambda body, i: fired.append(i) or ("0xh%d" % i, [])))
burst = send_step.make_burst(engine)
def run(veto=None, gate=None, open_by=None):
    fired.clear(); logged.clear(); t0 = time.monotonic() - 1.0; at = [t0 + 0.001 * i for i in range(6)]
    kw = {}
    if veto is not None: kw["veto"] = veto
    if gate is not None: kw["gate"] = gate; kw["open_by"] = open_by
    return burst([tx(i) for i in range(6)], at, "test", keys=KEYS, **kw)
out = run()
ok(fired == list(range(6)) and logged[-1]["vetoed_at"] is None, "no veto (the sniper): every shot sent, as before")
n = [0]
def v():
    n[0] += 1; return n[0] > 3                                           # a fleet shows before the 4th shot
out = run(veto=v)
ok(fired == [0, 1, 2] and out[3:] == [(None, None)] * 3, "a veto true from the 4th shot: shots 0-2 sent, 3-5 not")
ok(logged[-1]["vetoed_at"] == 3 and logged[-1]["gated"] == 3, "the log names the shot the veto stopped at")
n[0] = 0; calls = []
def v2():
    calls.append(1); return False
out = run(veto=v2)
ok(fired == list(range(6)) and len(calls) == 6, "a veto never true: asked before every shot, every shot sent")
out = run(veto=lambda: True)
ok(fired == [] and out == [(None, None)] * 6, "a veto true at the first shot: nothing sent")
def boom(): raise RuntimeError("feed state")
out = run(veto=boom)
ok(fired == [] and logged[-1]["vetoed_at"] == 0, "a veto that raises stops the burst (never send blind)")
g = [0]
def gate():
    g[0] += 1; return g[0] > 2
out = run(gate=gate, open_by=time.monotonic() + 10)
ok(fired == [2, 3, 4, 5], "a gate without a veto works as before (opens at the 3rd shot)")
# the engine side (source checks: the branch sits inside the launch thread)
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy", "sniper_engine.py")).read()
ok('veto = veto if (ATTACK_MAX >= 0 and BURST_N > 1) else None' in src and 'gk["veto"] = veto' in src, "the engine passes a veto only for an ATTACK_MAX burst (the sniper's ATTACK_MAX is -1)")
ok("if veto is not None and not vetoed:" in src and "                    vetoed = bool(veto())" in src, "the dry run emulates the veto exactly")
ok('if decision["unsent_shots"] == len(shots) or (SEND is None and decision["vetoed"]):' in src and 'by the first shot (vetoed; no shot sent)' in src, "a burst vetoed before its first shot is a refusal: no position is opened")
ok('if "veto" not in inspect.signature(SEND_BURST).parameters:' in src, "an ATTACK_MAX burst refuses to start with a send step that has no veto")
setup = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "deploy", "runner_setup.sh")).read()
ok('RSEND=/etc/sniper/runner_send_step.py' in setup and 'install -m 600 "$REPO/deploy/send_step.py" "$RSEND"; setkv SEND_MODULE "$RSEND"' in setup, "the runner gets its own copy of the send step; the sniper's file is never touched")
print(f"all {checks} checks passed")
