"""6.10: the relay under the stake is refilled from the background loop, the shooters' gas float follows the typical base fee and
each shot's cap is trimmed to its shooter's balance (Sep 29 20:08-02:41: one short refill after an exit, 32 launches refused,
20:49 +61% and 21:34 +118% among them; 23:27: a one-launch fee ramp marked all 35 shooters out of gas)."""
import os, sys, json, time, tempfile
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E1"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("BANKROLL_USD", "50"), ("STAKE_MIN", "25"), ("STAKE_MAX", "25"),
             ("GAS_HEADROOM", "6"), ("SHOOTER_KEYS", "")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E
checks = 0


def ok(cond, what):
    global checks
    if not cond:
        raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)


S = E.state; S["eth_usd"] = 2700.0; S["base_fee"] = 23_000_000; S["gas_price"] = int(S["base_fee"] * 6); S["base_fee_hist"].clear()
# ---- the shooters' gas float on the typical base fee, not the instant one --------------------------------------------
ok(E.base_fee_typical() == S["base_fee"], "under ten polls, the latest base fee is the typical one")
for _ in range(20):
    S["base_fee_hist"].append(23_000_000)
S["base_fee"] = 230_000_000; S["gas_price"] = int(S["base_fee"] * 6)                    # a 10x ramp on one poll
S["base_fee_hist"].append(S["base_fee"])
ok(E.base_fee_typical() == 23_000_000, "one ramped poll does not move the ten-minute median")
ok(E.shooter_need_eth() == E.SHOOTER_MIN_ETH, "at 0.023 gwei the float is the minimum (0.00004), the same as before 6.10")
ok(abs(E.shooter_target_eth() - 3 * E.SHOOTER_MIN_ETH) < 1e-15, "and the top-up target stays 3x the minimum (0.00012), as in 6.9: no extra capital in the shooters")
# ---- each shot's cap trimmed to its shooter's balance ----------------------------------------------------------------
cap = E.shot_gas_price(S["gas_price"], 0.00008)                                       # a shooter holding 0.00008 ETH (the fleet's level Sep 30)
ok(cap < S["gas_price"] and cap * E.RELAY_SHOOT_GAS <= 0.00008 * 1e18, "a shooter that cannot afford the 6x cap gets the cap its balance covers")
ok(cap >= S["base_fee"], "and that cap still clears a 10x ramped base fee (0.00008 ETH covers 0.29 gwei at 250k gas with 10% spare)")
ok(E.shot_gas_price(S["gas_price"], 0.001) == S["gas_price"], "a shooter with the balance keeps the full cap")
S["shooter_nonce"] = {"a": 1, "b": 2, "c": 3}; S["shooter_eth"] = {"a": 0.00008, "b": 0.00001, "c": 0.00008}
ok(E.shooter_ready("a") and not E.shooter_ready("b") and not E.shooter_ready("d"), "ready: a nonce, the float and a cap over the base fee; an empty or unknown shooter is not")
S["base_fee"] = 400_000_000; S["gas_price"] = int(S["base_fee"] * 6)
ok(not E.shooter_ready("a"), "a ramp past what the balance covers (0.4 gwei x 250k > 0.00008 ETH) takes the shooter out until it passes")
S["base_fee"] = 23_000_000; S["gas_price"] = int(S["base_fee"] * 6)
# ---- the relay short of the stake, and the refill from the loop --------------------------------------------------------
S["relay_eth"] = None
ok(E.relay_short() == 0.0, "no relay read yet: nothing to refill")
S["relay_eth"] = 0.005565
ok(abs(E.relay_short() - (0.98 * 30 / 2700.0 - 0.005565)) < 1e-12, "the relay at 0.00557 ETH is short of its float ($30 x 0.98) by the difference")
S["relay_eth"] = 0.0112
ok(E.relay_short() == 0.0, "at the float (0.0112 ETH) it is not short")
ok(abs(E.relay_float_eth() - 30 / 2700.0) < 1e-12, "the float is 1.2 stakes ($30) by default")
# relay_topup with a fake chain: the relay short, the wallet able; the send is recorded, the nonce re-read, the relay read back
E.SEND = lambda tx, label: "0xhash"; E.SHOOTERS = ["a", "b", "c"]; E.RELAY = "0x" + "1" * 40; E.WALLET = "0x" + "2" * 40
bal = {E.RELAY.lower(): 0.005565, E.WALLET.lower(): 0.010635}; calls = {"nonce": 7}; sent = []
class FakeRpc:
    def call(self, method, params, **kw):
        if method == "eth_getBalance":
            return hex(int(bal[params[0].lower()] * 1e18))
        if method == "eth_getTransactionCount":
            return hex(calls["nonce"])
        raise RuntimeError(method)
E.rpc = FakeRpc(); logged = []; E.log = lambda d: logged.append(d)
def send(tx, label):
    sent.append((label, int(tx["value"], 16) / 1e18, int(tx["nonce"], 16))); calls["nonce"] += 1
    bal[E.RELAY.lower()] += int(tx["value"], 16) / 1e18; bal[E.WALLET.lower()] -= int(tx["value"], 16) / 1e18; return "0xh"
E.SEND = send; E.wait_receipt = lambda h, t=10.0, **kw: {"status": "0x1"}; E.to_checksum_address = lambda a: a
E.relay_topup("under the stake")
ok(len(sent) == 1 and sent[0][0] == "relay_float" and abs(sent[0][1] - (30 / 2700.0 - 0.005565)) < 1e-9, "the wallet sends the relay back to its float: 0.00555 ETH")
ok(S["nonce"] == 8 and S["relay_eth"] > 0.0111 and E.relay_short() == 0.0, "the local nonce follows the send, the relay is read back at the float, no longer short")
ok(logged[-1]["ev"] == "relay_topup" and logged[-1]["landed"] and logged[-1]["short_of_float"] == 0, "and the refill is logged as landed, not short")
# the stale-wallet case: the first read predates the sell's proceeds, the second (2 s later) has them
bal[E.RELAY.lower()] = 0.0007; bal[E.WALLET.lower()] = 0.0018; sent.clear(); reads = {"n": 0}
class LagRpc(FakeRpc):
    def call(self, method, params, **kw):
        if method == "eth_getBalance" and params[0].lower() == E.WALLET.lower():
            reads["n"] += 1
            if reads["n"] == 2:
                bal[E.WALLET.lower()] = 0.0018 + 0.00923                              # the proceeds arrive on this endpoint between the two reads
        return super().call(method, params, **kw)
E.rpc = LagRpc(); E.time.sleep = lambda s: None
E.relay_topup("after exit")
ok(len(sent) == 1 and sent[0][1] > 0.009, "a wallet read before the proceeds is read again: the refill is sized on the second read (0.0095 ETH, not 0.0003)")
# the wallet unable: one alarm, then silence for 30 minutes
bal[E.RELAY.lower()] = 0.0007; bal[E.WALLET.lower()] = 0.0016; sent.clear(); logged.clear(); E.rpc = FakeRpc()
E.relay_topup("under the stake"); E.relay_topup("under the stake")
ok(not sent and sum(1 for d in logged if d["ev"] == "alarm") == 1, "a wallet that cannot cover 10% of the need: no send, one alarm (not one a minute)")
# ---- shooter_topup funds what the wallet covers, the emptiest first ------------------------------------------------------
S["wallet_eth"] = 0.00061; S["shooter_eth"] = {"a": 0.00001, "b": 0.00003, "c": 0.00002}; S["shooter_nonce"] = {"a": 1, "b": 1, "c": 1}; sent.clear(); logged.clear()
E.refresh_shooters = lambda **kw: None; E.next_nonce = lambda: 9
E.shooter_topup(["a", "b", "c"])
ok([lab for lab, _, _ in sent] == ["shooter_gas"] and abs(sent[0][1] - (3 * E.SHOOTER_MIN_ETH - 0.00002)) < 1e-12, "wallet 0.00061 (0.00011 spare): the emptiest (needs 0.00011) fits exactly; funded, the others wait")
ok(logged[-1]["ev"] == "shooter_topup" and logged[-1]["funded"] == 1 and logged[-1]["shooters"] == 3, "and the log says 1 of 3 funded")
S["wallet_eth"] = 0.00051; sent.clear(); logged.clear(); S["shooter_alarm_at"] = -1e9
E.shooter_topup(["a", "b", "c"]); E.shooter_topup(["a", "b", "c"])
ok(not sent and sum(1 for d in logged if d["ev"] == "alarm") == 1, "nothing affordable: one alarm, then silence")


# ---- 6.12: the team-bundle gate (off by default) --------------------------------------------------------------------------
E.NAMED_MAX = 0
ok(E.team_bundle(["a"] * 30) is False, "NAMED_MAX 0: the gate is off, thirty named wallets pass")
E.NAMED_MAX = 12
ok(E.team_bundle(["a"] * 12) is False and E.team_bundle(["a"] * 13) is True, "NAMED_MAX 12: twelve pass, thirteen are a team bundle")
print(f"\n{checks} checks passed")
