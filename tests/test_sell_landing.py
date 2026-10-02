"""6.11: the exit reads the chain from two nodes. Sep 30 16:53: the provider's node ran 20 s behind, the engine re-sent a landed
sell thirteen times, held the position open and refused a launch; the sequencer's own RPC had the receipt all along."""
import os, sys, time, tempfile
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E1"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("BANKROLL_USD", "50"), ("STAKE_MIN", "25"), ("STAKE_MAX", "25"), ("SHOOTER_KEYS", "")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E
checks = 0
def ok(cond, what):
    global checks
    if not cond: raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)
W = "0x" + "e0" * 20; TOKEN = "0x" + "aa" * 20; CURVE = "0x" + "cc" * 20
class Node:
    """a fake node: its confirmed nonce, pending nonce, the wallet's token balance and the receipts it can see"""
    def __init__(self, latest, pending, balance, receipts=None, allowance=0):
        self.latest, self.pending, self.balance, self.receipts, self.allowance, self.calls = latest, pending, balance, receipts or {}, allowance, 0
    def call(self, method, params, tries=3):
        self.calls += 1
        if method == "eth_getTransactionReceipt": return self.receipts.get(params[0])
        if method == "eth_getTransactionCount": return hex(self.latest if params[1] == "latest" else self.pending)
        if method == "eth_call":
            data = params[0]["data"]
            if data.startswith("0x70a08231"): return hex(self.balance)
            if data.startswith("0xdd62ed3e"): return hex(self.allowance)
        raise RuntimeError(method)
E.WALLET = W; E.state["eth_usd"] = 2700.0; E.state["base_fee"] = 22_000_000; E.state["gas_price"] = 132_000_000; E.state["nonce"] = 1216
logged = []; E.log = lambda d: logged.append(d)
# ---- wait_receipt: the second node is asked on the alternate polls ---------------------------------------------------------
lag = Node(1215, 1216, 10 ** 24); cur = Node(1217, 1217, 0, {"0xsell1": {"status": "0x1", "blockNumber": "0x10"}})
E.rpc, E.rpc_logs, E.rpc_logs_quick = lag, cur, cur
t0 = time.time(); r = E.wait_receipt("0xsell1", 1.0)
ok(r and r["status"] == "0x1" and time.time() - t0 < 0.5, "a receipt the lagging node does not show is found on the sequencer's node within 100 ms")
ok(E.wait_receipt("0xnone", 0.2) is None, "no receipt anywhere: None after the timeout")
# ---- next_nonce: the higher of the two nodes ---------------------------------------------------------------------------------
ok(E.next_nonce() == 1217, "the pending nonce is the higher of the two nodes' answers (the lagging node hands out a used one)")
# ---- landed_on_chain: a node behind the transaction never counts, even with a zero balance ---------------------------------
behind = Node(1215, 1216, 0); E.rpc, E.rpc_logs, E.rpc_logs_quick = behind, behind, behind
ok(E.landed_on_chain(1216, E.sold_on(TOKEN)) is False, "a node whose confirmed nonce is not past the sell's does not count (its zero balance predates the buy)")
E.rpc, E.rpc_logs, E.rpc_logs_quick = lag, cur, cur
ok(E.landed_on_chain(1216, E.sold_on(TOKEN)) is True, "a node past the sell's nonce with the tokens gone: landed")
cur.balance = 5
ok(E.landed_on_chain(1216, E.sold_on(TOKEN)) is False, "past the nonce but the tokens still there (the sell reverted): not landed")
cur.balance = 0
# ---- send_confirmed: no receipt visible on either node, the sequencer says 'nonce too low', the chain shows the tokens gone --
class Ans(list):
    pass
class FakeSender:
    def __init__(self): self.n = 0
    def mine(self):
        a = Ans(); a.meta = {"complete": True}
        a.append(("seq", {"jsonrpc": "2.0", "id": 1, "result": "0xs"} if self.n == 1 else {"jsonrpc": "2.0", "id": 1, "error": {"code": -32000, "message": "nonce too low"}})); return a
    def answers(self, out, timeout=0.5): return out
    def rejected(self, out): return False
E.SENDER = FakeSender(); sent = []
cur.latest = cur.pending = 1216; cur.balance = 10 ** 24                   # before the send: both nodes at nonce 1216, the tokens in the wallet
def submit(tx, label):
    E.SENDER.n += 1; sent.append((label, tx["nonce"]))
    cur.latest = cur.pending = 1217; cur.balance = 0                      # the send lands at once on the chain: the current node moves past it, the lagging one does not
    return f"0xh{E.SENDER.n}"
E.submit = submit; E.SELL_CONFIRM_S = 0.1
cur.receipts = {}; lag.receipts = {}; logged.clear()
t0 = time.time(); rec, h = E.send_confirmed(lambda cap, nonce: {"nonce": nonce, "cap": cap}, "sell", 10.0, effect=E.sold_on(TOKEN))
ok(rec and rec.get("status") == "0x1" and rec.get("inferred"), "the sell is taken as landed from the chain's state, with an inferred receipt")
ok(time.time() - t0 < 1.5 and len(sent) <= 2, f"within a second and at most two sends (was 13 over 21 s): {len(sent)} sends in {time.time() - t0:.2f} s")
ok(any(d["ev"] == "landed_inferred" and d["label"] == "sell" for d in logged), "and it is logged as inferred")
# the same when the sequencer never says 'nonce too low' (the socket busy): the inferred check runs on the plain miss too
E.SENDER = FakeSender(); E.SENDER.n = 5; sent.clear(); logged.clear(); cur.latest = cur.pending = 1216; cur.balance = 10 ** 24
class Busy(FakeSender):
    def mine(self):
        a = Ans(); a.meta = {"complete": True}; a.append(("seq", {"error": "endpoint busy: skipped"})); return a
E.SENDER = Busy()
rec, h = E.send_confirmed(lambda cap, nonce: {"nonce": nonce, "cap": cap}, "sell", 10.0, effect=E.sold_on(TOKEN))
ok(rec and rec.get("inferred") and len(sent) <= 2, "a missed receipt with a busy socket: still closed from the chain's state")
# the approve: the allowance in place on a node past the nonce
cur.allowance = 10 ** 24; cur.latest = cur.pending = 1216; sent.clear()
def submit_a(tx, label):
    E.SENDER.n += 1; sent.append((label, tx["nonce"])); cur.latest = cur.pending = 1217; return f"0xa{E.SENDER.n}"
E.submit = submit_a
rec, h = E.send_confirmed(lambda cap, nonce: {"nonce": nonce, "cap": cap}, "approve", 10.0, effect=E.approved_on(TOKEN, CURVE, 10 ** 23))
ok(rec and rec.get("inferred"), "an approve whose receipt is invisible but whose allowance a node past it shows: landed")
# no effect known (a plain send): the old behaviour, the loop runs to max_s
sent.clear(); t0 = time.time(); cur.latest = cur.pending = 1216; E.submit = submit
rec, h = E.send_confirmed(lambda cap, nonce: {"nonce": nonce, "cap": cap}, "other", 0.5)
ok(rec is None and time.time() - t0 >= 0.5, "without an effect to check, the old loop (re-send until max_s) is unchanged")
print(f"\n{checks} checks passed")
