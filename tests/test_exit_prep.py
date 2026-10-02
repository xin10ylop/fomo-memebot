"""6.17: the first sell goes out with no query in front of it (the exact amount from the buy's event, the approve confirmed by the
watcher during the hold); the retry paths still read the chain; the sell's landing block is logged."""
import os, sys, time, tempfile, types
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
E.WALLET = W; E.state["eth_usd"] = 2700.0; E.state["base_fee"] = 22_000_000; E.state["gas_price"] = 132_000_000; E.state["nonce"] = 1216
logged = []; E.log = lambda d: logged.append(d); E.save_state = lambda: None; E.refresh_wallet = lambda why="": None; E.SEND = lambda tx, label: "0xsent"
calls = {"balance": 0, "approved": 0, "sent": []}
def fake_balance(token): calls["balance"] += 1; return 4_534_579_780_362_193_500_000_000
def fake_ensure(pos, amount, max_s): calls["approved"] += 1; return True
def fake_send(build, label, max_s, effect=None):
    tx = build(100, 1217); calls["sent"].append((label, tx)); return {"status": "0x1", "blockNumber": hex(78_594_216)}, "0xsellhash"
E.token_balance = fake_balance; E.ensure_approved = fake_ensure; E.send_confirmed = fake_send
def fresh(**kw):
    pos = {"curve": CURVE, "token": TOKEN, "creator": "0x" + "11" * 20, "tokens": 4534579.7803621935, "tokens_wei": "4534579780362193500000000", "buy_block": 78_594_194,
           "nonce": 1216, "t_buy": E.mono() - 1.1, "buy_hash": "0xbuy", "approve_hash": "0xappr", "approved": True, "approve_ok": True}
    pos.update(kw); E.state["open"] = pos; calls.update({"balance": 0, "approved": 0, "sent": []}); logged.clear(); return pos
amt = lambda: int(calls["sent"][0][1]["data"][10:74], 16)
# ---- the first attempt, the watcher confirmed the approve: no query before the sell --------------------------------------
pos = fresh(); E.close_position(pos, "hold")
ok(calls["balance"] == 0 and calls["approved"] == 0, "no balance read and no approve check in front of the first sell")
ok(calls["sent"] and calls["sent"][0][0] == "sell" and amt() == 4534579780362193500000000, "the sell carries the exact amount the buy's event reported")
d = next(e for e in logged if e["ev"] == "trade_done")
ok(d["hold_blocks"] == 22 and d["exit_prep_s"] < 0.05 and E.state["open"] is None, f"trade_done logs the landing (hold {d['hold_blocks']} blocks) and the prep time ({d['exit_prep_s']} s); the position is closed")
# ---- the approve not seen by the watcher: the check runs first ------------------------------------------------------------
pos = fresh(approve_ok=False); E.close_position(pos, "hold")
ok(calls["approved"] == 1 and calls["balance"] == 0 and amt() == 4534579780362193500000000, "approve unconfirmed: ensure_approved runs, the amount still comes from the event")
# ---- a retry after a sell hash exists: the real balance is read -----------------------------------------------------------
pos = fresh(sell_hash="0xold"); E.close_position(pos, "retry")
ok(calls["balance"] == 1, "a retry reads the wallet's balance from the chain")
# ---- an old position without the exact amount (state from before 6.17): the balance is read ---------------------------------
pos = fresh(); del pos["tokens_wei"]; E.close_position(pos, "hold")
ok(calls["balance"] == 1 and amt() == 4534579780362193500000000, "no exact amount in the state: the balance read, as before")
# ---- the receipt without a block number, or no buy block: hold_blocks is None, nothing raises ----------------------------------
E.send_confirmed = lambda build, label, max_s, effect=None: (build(100, 1217) and ({"status": "0x1"}, "0xh"))
pos = fresh(); E.close_position(pos, "hold"); d = next(e for e in logged if e["ev"] == "trade_done")
ok(d["hold_blocks"] is None and E.state["open"] is None, "a receipt without a block number: hold_blocks None, the trade still closes")
# ---- the alternate node in the receipt poll is the bounded one -------------------------------------------------------------
import inspect
src = inspect.getsource(E.wait_receipt)
ok("rpc_logs_quick" in src and E.rpc_logs_quick.timeout == 0.7, "wait_receipt alternates onto the 0.7 s-bounded public node")
print(f"\n{checks} checks passed")
