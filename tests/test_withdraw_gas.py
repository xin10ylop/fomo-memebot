"""Oct 9: withdraw.py's gas limit is the node's estimate plus POSTING_HEADROOM (the chain charges the parent-chain posting cost as
gas in about half the blocks; a transfer capped at exactly 21,000 was refused "intrinsic gas too low"). Driven end to end against a
fake node: the signed transaction decoded (to, value, gas, nonce, chain id), the balance check, the estimate's failure fallback, the
bookkeeping per instance (the sniper: TG_PNL_WITHDRAWN in telegram.env; a second instance: PNL_WITHDRAWN in its own env file)."""
import os, sys, tempfile, json, importlib
from eth_account import Account
import rlp
checks = 0
def ok(cond, what):
    global checks
    if not cond: raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)
D = tempfile.mkdtemp(); acct = Account.create(); KEY = acct.key.hex(); KEY = KEY if KEY.startswith("0x") else "0x" + KEY
RUNNER = os.path.join(D, "runner.env")
open(RUNNER, "w").write(f"PRIVATE_KEY={KEY}\nWALLET={acct.address}\nRPC_URL=http://fake\nPNL_BASE=0.011\nPNL_WITHDRAWN=0\n")
os.environ["SNIPER_ENV"] = RUNNER
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "deploy"))
import withdraw as W
ok(W.ENV == RUNNER and W.POSTING_HEADROOM == 30_000, "SNIPER_ENV selects the instance's env file; headroom 30,000 gas")
sent = []; estimate = {"v": "0x5208", "fail": False}
def fake_rpc(url, m, p):
    if m == "eth_getBalance": return hex(int(0.019124e18))
    if m == "eth_gasPrice": return hex(20_220_000)
    if m == "eth_estimateGas":
        if estimate["fail"]: raise RuntimeError("estimate refused")
        return estimate["v"]
    if m == "eth_getTransactionCount": return hex(1407)
    if m == "eth_sendRawTransaction": sent.append(p[0]); return "0x" + "ab" * 32
    if m == "eth_getTransactionReceipt": return {"status": "0x1", "blockNumber": "0x10"}
    raise RuntimeError(m)
W.rpc = fake_rpc; W.time.sleep = lambda s: None
TO = "0x4c662C38729dB298730c80fae8736621bc536B9a"
def run(amount="0.0111"):
    sys.argv = ["withdraw.py", "--to", TO, "--amount", amount, "--yes"]; W.main()
    raw = bytes.fromhex(sent[-1][2:]); f = rlp.decode(raw)          # legacy: nonce, gasPrice, gas, to, value, data, v, r, s
    return {"nonce": int.from_bytes(f[0], "big"), "gasPrice": int.from_bytes(f[1], "big"), "gas": int.from_bytes(f[2], "big"), "to": "0x" + f[3].hex(), "value": int.from_bytes(f[4], "big"),
            "v": int.from_bytes(f[6], "big"), "sender": Account.recover_transaction(raw)}
tx = run()
ok(tx["gas"] == 21000 + 30000, f"estimate 21,000: the limit is 51,000 (got {tx['gas']})")
ok(tx["to"] == TO.lower() and tx["value"] == int(0.0111e18), "to the runner's address, exactly 0.0111 ETH")
ok(tx["nonce"] == 1407 and tx["gasPrice"] == 2 * 20_220_000 and tx["v"] in (4663 * 2 + 35, 4663 * 2 + 36), "nonce from the node, twice the gas price, EIP-155 chain 4663")
ok(tx["sender"] == acct.address, "signed by the instance's own key")
ok("PNL_WITHDRAWN=0.011100" in open(RUNNER).read() and "TG_PNL_WITHDRAWN" not in open(RUNNER).read(), "a second instance records the withdrawal as PNL_WITHDRAWN in its own env file")
estimate["v"] = hex(26_000); tx = run("0.001")
ok(tx["gas"] == 56_000, "a posting charge in the estimate (26,000) is kept and the headroom added on top")
ok("PNL_WITHDRAWN=0.012100" in open(RUNNER).read(), "withdrawals accumulate")
estimate["fail"] = True; tx = run("0.001")
ok(tx["gas"] == 51_000, "the estimate refused: 21,000 plus the headroom")
estimate["fail"] = False
try:
    sys.argv = ["withdraw.py", "--to", TO, "--amount", "0.019124", "--yes"]; n = len(sent); W.main(); ok(False, "over the balance must refuse")
except SystemExit as e:
    ok(len(sent) == n and "cannot cover" in str(e), "an amount the balance cannot cover with the gas is refused before signing")
# the sniper's instance: the record goes to telegram.env as TG_PNL_WITHDRAWN
os.environ.pop("SNIPER_ENV"); importlib.reload(W)
ok(W.ENV == "/etc/sniper/engine.env", "without SNIPER_ENV it is the sniper's env file")
TG = os.path.join(D, "telegram.env"); open(TG, "w").write("TG_TOKEN=x\nTG_PNL_WITHDRAWN=0.007800\n")
W.record_withdrawal(0.0111, path=TG)
ok("TG_PNL_WITHDRAWN=0.018900" in open(TG).read() and "TG_TOKEN=x" in open(TG).read(), "the sniper's withdrawal adds to TG_PNL_WITHDRAWN and keeps the other lines")
src = open(os.path.join(os.path.dirname(W.__file__), "relay_ops.py")).read()
ok("SWEEP_GAS = 51_000" in src and '"gas": SWEEP_GAS' in src and "fee = SWEEP_GAS * gp * 2" in src, "the shooter sweep: the same headroom, the fee it keeps back matches its limit")
print(f"all {checks} checks passed")
