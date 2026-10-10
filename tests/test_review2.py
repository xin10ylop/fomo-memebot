"""6.27 (runbook 5bn): the second review's fixes, behind the runner's switches and inert for the sniper. The HTTP clients leave from
RPC_LOCAL_ADDR (the feed's second address by default); a lost address at start clears the binding so a recovery sell still leaves;
with the crowd ceiling on, an approve on the not-yet-learned token is not a fleet (the sniper's count unchanged); the exit's bankroll
reads the relay before the wallet; the back-fill runs after the curve is registered. Plus the tooling's string contracts."""
import os, sys, json, tempfile
D = tempfile.mkdtemp(); os.environ["LOG_PATH"] = D + "/r.jsonl"
for k, v in (("SEAT", "E1"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("SHOOTER_KEYS", ""), ("FEED_LOCAL_ADDR", ""), ("RPC_LOCAL_ADDR", "")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E
checks = 0
def ok(cond, what):
    global checks
    if not cond: raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
# the HTTP clients' source address
E.RPC_BIND[0] = ""; c = E.Rpc("https://node.invalid/v2/x")._conn(); ok(c.source_address is None, "no local address (the sniper): the RPC pool binds nothing, as before")
E.RPC_BIND[0] = "10.9.9.9"; c = E.Rpc("https://node.invalid/v2/x")._conn(); ok(c.source_address == ("10.9.9.9", 0), "RPC_LOCAL_ADDR: every pooled connection leaves from the second address")
E.RPC_BIND[0] = "203.0.113.9"; E.FEED_LOCAL_ADDR = "203.0.113.9"
try:
    E.check_feed_local(); ok(False, "an address this machine does not own must refuse the start")
except SystemExit:
    ok(E.RPC_BIND[0] == "", "a lost address refuses the start and clears the binding, so the recovery sell leaves from the default address")
E.FEED_LOCAL_ADDR = ""; E.RPC_BIND[0] = ""
src = open(f"{R}/src/strategy/sniper_engine.py").read()
ok(src.index("    load_state()\n    try:\n        check_feed_local()") > src.index("    load_send_step()\n") and "recovered after restart (feed address missing)" in src, "the address check runs after the state loads and sells an open live position before stopping")
# an approve is never a shot
def w0(): return {"tb": None, "named": set(), "creator": "0x" + "c" * 40, "attack_senders": set(), "attack_wallets": set(), "attack_targets": set(), "cb": bytes.fromhex("ab" * 20)}
curve = "0x" + "ab" * 20; token = "0x" + "de" * 20; approve = bytes.fromhex(E.APPROVE_SEL) + bytes(12) + bytes.fromhex("ab" * 20) + bytes(32)
E.ATTACK_MAX = 0; w = w0(); E.note_attack(w, token, b"\x02" + bytes(60), approve, curve)
ok(not w["attack_targets"] and not w["attack_wallets"], "ATTACK_MAX on: a named wallet's approve on the not-yet-learned token is not a fleet (no false veto)")
E.ATTACK_MAX = -1; w = w0(); E.note_attack(w, token, b"\x02" + bytes(60), approve, curve)
ok(token in w["attack_targets"], "ATTACK_MAX off (the sniper): the same call is recorded exactly as before (attack_fleets drops it once the token is learned)")
# the exit's bankroll reads the relay first
calls = []
class FakeRpc:
    def call(self, m, p, **k): calls.append(p[0]); return hex(10 ** 16) if p[0] == "0xr" else hex(2 * 10 ** 16)
E.rpc = FakeRpc(); E.SEND = object(); E.SHOOTERS = ["0xs"]; E.RELAY = "0xr"; E.WALLET = "0xw"; E.state["eth_usd"] = 2700.0; E.state["relay_eth"] = 0.5
E.refresh_wallet("t"); ok(calls == ["0xr", "0xw"] and abs(E.state["relay_eth"] - 0.01) < 1e-9 and abs(E.state["bankroll"] - 0.03 * 2700) < 1e-6, "refresh_wallet: the relay's balance read before the wallet's, the bankroll on both as they are now (not the pre-buy float)")
calls.clear(); E.SHOOTERS = []; E.refresh_wallet("t"); ok(calls == ["0xw"], "without shooters (no relay float) only the wallet is read, as before")
# the back-fill after the registration; the timer cleared before the sell; the dry run's veto; the feed wait's gate
ok(src.index('    state["watch"][curve] = w\n') < src.index('for to_hex, t, data in list(state["recent_calls"]):'), "the back-fill runs after state['watch'][curve] is set: a call indexed meanwhile is counted by one path")
ok(src.index('state["busy_until"] = 0.0                                                                           # 6.27') < src.index('    close_position(pos, why)\n    if EXIT_MARK:\n        state["watch"].pop(curve, None)'), "the 33 s timer is cleared under the lock before the sell")
ok('or (SEND is None and decision["vetoed"])' in src, "dry run: any veto is a refusal (no paper fill live would mostly not get)")
ok("and not PROVIDER_WS and REQUIRE_FEED_LOCAL_ADDR:" in src, "the no-provider wait belongs to the second instance only")
ok('"release": "6.27"' in src and '"rpc_local_addr": RPC_LOCAL_ADDR' in src, "release 6.27, the start line shows the HTTP clients' address")
# the tooling's contracts
ro = open(f"{R}/deploy/relay_ops.py").read(); ok("registration incomplete" in ro and "sys.exit(f\"registration incomplete" in ro, "shooters-register fails when the relay did not take every shooter")
rd = open(f"{R}/deploy/relay_deploy.py").read(); ok(rd.index("RELAY={relay}") < rd.index("eth_getLogs") and "PUBLIC_RPC" in rd and "no recent curve to simulate on" in rd, "relay_deploy writes RELAY before the simulation; the log read is on the public node and cannot fail the deploy")
wd = open(f"{R}/deploy/withdraw.py").read(); ok("REFUSED_BEFORE_ACCEPT" in wd and "polling its hash, never sending again blind" in wd and '"already known"' not in wd, "withdraw: only a refusal before acceptance means nothing was sent; any other error polls the hash")
sc = open(f"{R}/deploy/sniper-check.sh").read(); ok('LABEL=$([ "$NAME" = engine ] && echo sniper || echo "$NAME")' in sc and 'export BLIND_H=0' in sc and "BLIND_H <= 0: raise SystemExit(0)" in sc, "the watchdog labels the runner's alerts 'runner:' and skips the blind-gauge rule for it")
tp = open(f"{R}/deploy/runner.env.template").read(); ok("LATE_SEND_MIN_MS=70" in tp, "the template makes the 6.24 late start reachable (70 < SLOT_LEAD_MS+BURST_LEAD_MS)")
print(f"all {checks} checks passed")
