"""6.21 (runbook 5bc, review F3/P4): the first sell goes out at the nonce the build reserved (the approve's + 1) with no node asked
and no approve-receipt wait in front of it; a retry, or a sell without a reserved approve, reads the chain as before."""
import os, sys, tempfile
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
logged = []; E.log = lambda d: logged.append(d); E.save_state = lambda: None; E.refresh_wallet = lambda why="": None; E.SEND = lambda tx, label: "0xsent"   # live path, not the dry run
calls = {"approved": 0, "sent": [], "nonce_reads": 0}
E.ensure_approved = lambda pos, amount, max_s: calls.__setitem__("approved", calls["approved"] + 1) or True
E.token_balance = lambda token: 4_534_579_780_362_193_500_000_000
# ---- send_confirmed itself: a passed nonce is used and no node is asked; without one, next_nonce() runs --------------------
E.next_nonce = lambda: calls.__setitem__("nonce_reads", calls["nonce_reads"] + 1) or 1300
E.submit = lambda tx, label: "0xh"; E.SENDER = type("S", (), {"mine": staticmethod(lambda: [])})()
E.wait_receipt = lambda h, s, ans=None: {"status": "0x1", "blockNumber": "0x10"}
built = []
rec, h = E.send_confirmed(lambda cap, nonce: built.append(nonce) or {"nonce": nonce}, "sell", 2.0, nonce=1218)
ok(built == [1218] and calls["nonce_reads"] == 0 and rec["status"] == "0x1", "send_confirmed(nonce=1218): built at 1218, no node asked")
t = next(d for d in logged if d.get("ev") == "send_timing"); ok(t["nonce"] == 1218 and t["query_ms"] < 5, "send_timing logged with a ~0 ms query")
built.clear(); logged.clear()
rec, h = E.send_confirmed(lambda cap, nonce: built.append(nonce) or {"nonce": nonce}, "sell", 2.0)
ok(built == [1300] and calls["nonce_reads"] == 1, "send_confirmed() without a nonce: next_nonce() read once, as before")
# ---- close_position: the first sell at pos.nonce + 2, no ensure_approved even though the watcher has not confirmed ---------
def fake_send(build, label, max_s, effect=None, nonce=None):
    tx = build(100, nonce if nonce is not None else 9999); calls["sent"].append((label, nonce, tx)); return {"status": "0x1", "blockNumber": hex(78_594_216)}, "0xsellhash"
E.send_confirmed = fake_send
def fresh(**kw):
    pos = {"curve": CURVE, "token": TOKEN, "creator": "0x" + "11" * 20, "tokens": 4534579.7803621935, "tokens_wei": "4534579780362193500000000", "buy_block": 78_594_194,
           "nonce": 1216, "t_buy": E.mono() - 1.1, "buy_hash": "0xbuy", "approve_hash": "0xappr", "approved": True, "approve_ok": False}
    pos.update(kw); E.state["open"] = pos; calls.update({"approved": 0, "sent": []}); logged.clear(); return pos
pos = fresh(); E.close_position(pos, "hold")
ok(calls["approved"] == 0, "approve_ok unset but the approve was sent: no ensure_approved (no receipt wait) before the first sell")
ok(len(calls["sent"]) == 1 and calls["sent"][0][1] == 1218 and int(calls["sent"][0][2]["nonce"], 16) == 1218, "the first sell is built at the reserved nonce 1216 + 2")
ok(any(d.get("ev") == "trade_done" and d.get("hold_blocks") == 22 for d in logged) and E.state["open"] is None, "trade_done, position closed")
# ---- a position with no approve hash (the approve's submit failed): the old path, ensure_approved and a read nonce ----------
pos = fresh(approve_hash=None); E.close_position(pos, "hold")
ok(calls["approved"] == 1 and calls["sent"][0][1] is None, "no approve hash: ensure_approved runs and the sell's nonce is read")
# ---- a retry after an earlier sell attempt (sell_hash set): the old path as well -------------------------------------------
pos = fresh(sell_hash="0xold"); E.close_position(pos, "hold")
ok(calls["approved"] == 1 and calls["sent"][0][1] is None, "a retry (sell_hash set): ensure_approved and a read nonce, as before")
# ---- the first attempt reverted: the second attempt reads the nonce -------------------------------------------------------
seq = [({"status": "0x0", "blockNumber": "0x1"}, "0xrev"), ({"status": "0x1", "blockNumber": hex(78_594_230)}, "0xsell2")]
def fake_send2(build, label, max_s, effect=None, nonce=None):
    build(100, nonce if nonce is not None else 9999); calls["sent"].append((label, nonce, None)); return seq.pop(0)
E.send_confirmed = fake_send2; E.token_allowance = lambda token, curve: 10 ** 30
pos = fresh(); E.close_position(pos, "hold")
ok([s[1] for s in calls["sent"]] == [1218, None], "first attempt at 1218 reverted; the second attempt reads the nonce")
print(f"all {checks} checks passed")
