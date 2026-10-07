"""6.21 (runbook 5bc): the grouped relays (the sprayer contracts) count as ONE fleet between them in attack_fleets(), so the
3-fleet gate needs two real snipers when a sprayer is attacking; without a group the count is unchanged (6.1/6.2)."""
import os, sys, tempfile
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
SPR = ["0x" + "a1" * 20, "0x" + "a2" * 20, "0x" + "a3" * 20]
for k, v in (("SEAT", "E1"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("SHOOTER_KEYS", ""), ("ATTACK_MIN", "3"),
             ("ATTACK_GROUP", ",".join(SPR[:2]) + " , " + SPR[2].upper())):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E
checks = 0
def ok(cond, what):
    global checks
    if not cond: raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)
ok(E.ATTACK_GROUP == set(SPR), "the group is parsed lower-cased, spaces and case ignored")
def w(targets=(), senders=(), tb=None):
    return {"attack_targets": set(targets), "attack_senders": set(senders), "attack_wallets": set(), "tb": tb}
R1, R2, R3 = "0x" + "b1" * 20, "0x" + "b2" * 20, "0x" + "b3" * 20
ok(E.attack_fleets(w()) == 0, "nothing attacking: 0")
ok(E.attack_fleets(w([R1, R2, R3])) == 3, "three real relays: 3")
ok(E.attack_fleets(w([SPR[0], SPR[1], SPR[2]])) == 1, "three sprayers and nobody else: 1 (the gate stays shut)")
ok(E.attack_fleets(w([R1, SPR[0], SPR[1]])) == 2, "one real relay and two sprayers: 2 (the Oct 2-6 losing kind, 0 wins of 7 fills)")
ok(E.attack_fleets(w([R1, R2, SPR[0]])) == 3, "two real relays and one sprayer: 3 (fires)")
ok(E.attack_fleets(w([R1, R2, SPR[0], SPR[1], SPR[2]])) == 3, "two real relays and three sprayers: still 3")
ok(E.attack_fleets(w([R1, SPR[0]], senders=["0x" + "c1" * 20])) == 3, "a direct sender counts as a fleet beside a relay and the group")
ok(E.attack_fleets(w([R1, SPR[0], "0x" + "dd" * 20], tb=bytes.fromhex("dd" * 20))) == 2, "the token's own address never counts, grouped or not")
ok(E.attackers(w([R1, SPR[0], SPR[1]])) == 2, "attackers() (the gate's count in fleets mode) uses the grouped count")
# the group off: the old count
E.ATTACK_GROUP = set()
ok(E.attack_fleets(w([R1, SPR[0], SPR[1]])) == 3, "no group configured: every relay is a fleet, as before")
# the replay passes the group through its env (REPLAY_ATTACK_GROUP -> ATTACK_GROUP, REPLAY_BUILD_MIN -> ATTACK_BUILD_MIN)
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "analysis", "engine_replay.py")).read()
ok('"ATTACK_GROUP": os.environ.get("REPLAY_ATTACK_GROUP", "")' in src and '"ATTACK_BUILD_MIN": os.environ.get("REPLAY_BUILD_MIN", "0")' in src, "engine_replay maps REPLAY_ATTACK_GROUP and REPLAY_BUILD_MIN into the engine's env")
ok("at the build" in src and "k - 2" in src, "engine_replay applies the build minimum on the k-2 count")
print(f"all {checks} checks passed")
