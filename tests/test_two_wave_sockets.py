"""6.19: two shots per shooter need a socket per shot and gas for both shots (6.14 sized the socket pool and the gas cap per shooter:
the 36th shot would have raised IndexError, and the second wave's shot would have been refused on the shooters' summed cost)."""
import os, sys, tempfile
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E1"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("BANKROLL_USD", "50"), ("STAKE_MIN", "25"), ("STAKE_MAX", "25"), ("SHOOTER_KEYS", ""),
             ("BURST_N", "35"), ("SHOTS_PER_SHOOTER", "2"), ("SEND_MODE", "predict"), ("SEQ_URL", "https://sequencer.invalid/"), ("RPC_URL", "https://rpc.invalid/")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E
checks = 0
def ok(cond, what):
    global checks
    if not cond: raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)
ok(E.SHOTS_PER_SHOOTER == 2 and E.BURST_N == 35, "settings: 35 shooters, two shots each")
ok(len(E.SENDER.pool) == 70, f"the sender holds one warm socket per shot: {len(E.SENDER.pool)} (6.14 held 35: shot 36 raised IndexError)")
ok(E.SENDER.pool[69] is not None and E.SENDER.pool[69]["e"] is E.SENDER.eps[0], "shot 70's socket is addressable and points at the sequencer")
E.state["base_fee_hist"].clear(); E.state["base_fee_hist"].extend([22_000_000] * 10); E.state["base_fee"] = 22_000_000
need2 = E.shooter_need_eth()
one_shot = E.RELAY_SHOOT_GAS * 22_000_000 * E.SHOOTER_HEADROOM / 1e18 * 1.1
ok(abs(need2 - max(E.SHOOTER_MIN_ETH, 2 * one_shot)) < 1e-15, "a shooter must hold gas for both of its shots")
eth = 0.001
ok(E.shot_gas_price(10 ** 12, eth) == int(eth * 1e18 / (E.RELAY_SHOOT_GAS * 2) * 0.90), "the per-shot cap leaves the balance enough for the second wave's shot")
ok(E.shot_gas_price(5, eth) == 5, "a cap under the affordable one is kept as is")
print(f"\n{checks} checks passed")
