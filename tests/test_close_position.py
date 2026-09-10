"""simulated chain for close_position's live path: fake send step and fake RPC, five scenarios"""
import os, sys, json, time, threading
os.environ["LOG_PATH"] = "/tmp/claude-0/-home-user-fomo-memebot/a7a59693-7c2d-5b6c-b7df-e43fdbe7d612/scratchpad/test_close.jsonl"
os.environ["WALLET"] = "0xE0686DC72b04c12CeEFeea75E286E4Ef7C056f01"; os.environ["PIN_CPU"] = ""
sys.path.insert(0, "src/strategy"); import sniper_engine as E
E.SELL_CONFIRM_S = 0.3; E.SELL_MAX_S = 3.0
class Chain:
    def __init__(s, allowance=2**200, balance=10**21, approve_lands=True, sell_plan=None, refuse_until=0.0):
        s.allowance = allowance; s.balance = balance; s.approve_lands = approve_lands; s.sell_plan = list(sell_plan or ["ok"]); s.refuse_until = refuse_until
        s.nonce = 10; s.receipts = {}; s.sent = []; s.t0 = time.monotonic(); s.n = 0
    def submit(s, tx, label):
        s.n += 1; s.sent.append((label, tx))
        if time.monotonic() - s.t0 < s.refuse_until:
            E.SENDER.last = [("sequencer", {"error": "connection refused"})]; return None
        h = "0x%064x" % s.n; s.nonce = int(tx["nonce"], 16) + 1
        if label == "approve":
            if s.approve_lands or s.n > 1: s.receipts[h] = {"status": "0x1", "blockNumber": "0x10"}; s.allowance = 2**200
            return h
        plan = s.sell_plan.pop(0) if s.sell_plan else "ok"
        if plan == "ok": s.receipts[h] = {"status": "0x1", "blockNumber": "0x11"}; s.balance = 0
        elif plan == "revert": s.receipts[h] = {"status": "0x0", "blockNumber": "0x11"}
        elif plan == "lost": pass
        return h
    def call(s, method, params):
        if method == "eth_getTransactionReceipt": return s.receipts.get(params[0])
        if method == "eth_getTransactionCount": return hex(s.nonce)
        if method == "eth_call":
            d = params[0]["data"]
            if d.startswith("0x70a08231"): return hex(s.balance)
            if d.startswith("0xdd62ed3e"): return hex(s.allowance)
        if method == "eth_gasPrice": return hex(10**8)
        raise RuntimeError(method)
def run(name, chain, expect_open):
    E.SEND = chain.submit; E.rpc.call = chain.call; E.state["base_fee"] = 10**8; E.state["gas_price"] = 2 * 10**8; E.state["nonce"] = 10
    pos = {"curve": "0x14bc77a7007c6e81469167fb6d70ae62b4ba8619", "token": "0xb21e11096a226b3aaad53c44485b3bb07f4399e6", "tokens": 1000.0, "nonce": 9, "t_buy": E.mono(), "buy_hash": "0xbuy", "approved": True, "approve_hash": "0xapprove", "seat_ts": 1}
    if chain.approve_lands: chain.receipts["0xapprove"] = {"status": "0x1", "blockNumber": "0x10"}
    E.state["open"] = pos; open(os.environ["LOG_PATH"], "w").close()
    E.close_position(pos, "test"); time.sleep(0.6)
    if expect_open:
        time.sleep(chain.refuse_until + 2.0)
    time.sleep(0.5)
    evs = [json.loads(l) for l in open(os.environ["LOG_PATH"])]
    names = [e["ev"] for e in evs]; done = [e for e in evs if e["ev"] == "trade_done"]
    print(f"{name:52s} sends {[l for l, t in chain.sent]}  events {names}  open={E.state['open'] is not None}  done={'yes' if done else 'no'}")
    return done
print("=== close_position live path against a simulated chain")
run("A approve landed, sell lands", Chain(), False)
run("B first sell lost, second lands", Chain(sell_plan=["lost", "ok"]), False)
run("C approve never landed, allowance 0 -> re-approve", Chain(allowance=0, approve_lands=False), False)
run("D sell reverted (allowance 0) -> re-approve -> sell", Chain(sell_plan=["revert", "ok"], allowance=0), False)
run("E everything refused 2 s, then accepted (retry)", Chain(refuse_until=2.0), True)
