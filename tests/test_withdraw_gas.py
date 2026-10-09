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
# 6.26 (5bk): the engine that sends from this wallet must be stopped
W.engine_active = lambda: True
try:
    run("0.001"); ok(False, "must refuse")
except SystemExit as e:
    ok("runner-engine is running" in str(e), "runner.env: refused while runner-engine runs (the nonce race)")
W.engine_active = lambda: False
# a send that times out (the node may have taken it): the hash is polled, and recorded once it lands
real_rpc = W.rpc; state = {"n": 0}
def flaky(url, m, p):
    if m == "eth_sendRawTransaction": sent.append(p[0]); raise TimeoutError("read timed out")
    if m == "eth_getTransactionReceipt":
        state["n"] += 1
        if state["n"] <= 2: raise ConnectionError("reset")                 # two failed polls, then the receipt
    return fake_rpc(url, m, p)
W.rpc = flaky; before = open(RUNNER).read()
sys.argv = ["withdraw.py", "--to", TO, "--amount", "0.0005", "--yes"]; W.main()
ok("PNL_WITHDRAWN=0.013600" in open(RUNNER).read(), "a send that timed out but landed is polled through two failed polls and recorded")
led = W.ledger_path(); lines = open(led).read().splitlines()
ok(len(lines) == 4 and all(l.startswith("0x") and len(l.split()[0]) == 66 for l in lines), "every recorded withdrawal is in the ledger by its hash")
# the same hash recorded twice is refused
h0 = lines[0].split()[0]; v = open(RUNNER).read()
ok(W.record_withdrawal(0.0111, tx_hash=h0) is True and open(RUNNER).read() == v, "a hash already in the ledger is not counted twice")
# a node refusal: nothing sent, nothing recorded, non-zero exit
def refuse(url, m, p):
    if m == "eth_sendRawTransaction": raise RuntimeError({"code": -32000, "message": "intrinsic gas too low"})
    return fake_rpc(url, m, p)
W.rpc = refuse; v = open(RUNNER).read()
try:
    sys.argv = ["withdraw.py", "--to", TO, "--amount", "0.0004", "--yes"]; W.main(); ok(False, "must exit non-zero")
except SystemExit as e:
    ok("refused by the node, nothing sent" in str(e) and open(RUNNER).read() == v, "a refusal by the node: non-zero exit, nothing recorded")
# no receipt within the wait: non-zero exit with the --record command
W.RECEIPT_WAIT_S = 0.01
def never(url, m, p):
    if m == "eth_getTransactionReceipt": return None
    return fake_rpc(url, m, p)
W.rpc = never
try:
    sys.argv = ["withdraw.py", "--to", TO, "--amount", "0.0004", "--yes"]; W.main(); ok(False, "must exit non-zero")
except SystemExit as e:
    ok("--record 0x" in str(e) and "do NOT send again" in str(e), "no receipt: non-zero exit naming the hash and the --record command")
W.RECEIPT_WAIT_S = 120.0
# --record: from this wallet, landed, a plain transfer, recorded once
HX = "0x" + "cd" * 32
def chain(url, m, p):
    if m == "eth_getTransactionByHash": return {"from": acct.address, "to": TO, "value": hex(int(0.002e18)), "input": "0x"}
    if m == "eth_getTransactionReceipt": return {"status": "0x1", "blockNumber": "0x20"}
    return fake_rpc(url, m, p)
W.rpc = chain
try:
    sys.argv = ["withdraw.py", "--record", HX]; W.main()
except SystemExit as e:
    ok(e.code == 0 and "PNL_WITHDRAWN=0.015600" in open(RUNNER).read(), "--record: a landed transfer from this wallet is recorded")
def other(url, m, p):
    if m == "eth_getTransactionByHash": return {"from": "0x" + "99" * 20, "to": TO, "value": hex(10 ** 15), "input": "0x"}
    return chain(url, m, p)
W.rpc = other
try:
    sys.argv = ["withdraw.py", "--record", "0x" + "ef" * 32]; W.main(); ok(False, "must refuse")
except SystemExit as e:
    ok("not from this wallet" in str(e), "--record refuses a transaction from another wallet")
W.rpc = real_rpc
ok(oct(os.stat(RUNNER).st_mode & 0o777) == "0o600" and not os.path.exists(RUNNER + ".tmp"), "the env file is rewritten whole, mode 0600, no temporary left")
# the sniper's instance: the record goes to telegram.env as TG_PNL_WITHDRAWN
os.environ.pop("SNIPER_ENV"); importlib.reload(W)
ok(W.ENV == "/etc/sniper/engine.env", "without SNIPER_ENV it is the sniper's env file")
TG = os.path.join(D, "telegram.env"); open(TG, "w").write("TG_TOKEN=x\nTG_PNL_WITHDRAWN=0.007800\n")
W.record_withdrawal(0.0111, path=TG)
ok("TG_PNL_WITHDRAWN=0.018900" in open(TG).read() and "TG_TOKEN=x" in open(TG).read(), "the sniper's withdrawal adds to TG_PNL_WITHDRAWN and keeps the other lines")
src = open(os.path.join(os.path.dirname(W.__file__), "relay_ops.py")).read()
ok("SWEEP_GAS = 51_000" in src and '"gas": SWEEP_GAS' in src and "fee = SWEEP_GAS * gp * 2" in src, "the shooter sweep: the same headroom, the fee it keeps back matches its limit")
print(f"all {checks} checks passed")
