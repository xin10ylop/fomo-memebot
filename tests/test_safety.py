"""The safety fixes of Sep 16, each tested rather than asserted. Every one of these is a way the engine used to be able
to buy a token and never sell it, or spend without bound, or stop trading for ever with no alarm.

    python3 tests/test_safety.py
"""
import os, sys, json, time, threading, tempfile
os.environ["LOG_PATH"] = tempfile.mkdtemp() + "/t.jsonl"
os.environ["SEND_MODULE"] = ""; os.environ["PRIVATE_KEY"] = ""
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E

fails = []
def check(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f"   ({detail})" if detail and not ok else ""))
    if not ok: fails.append(name)

def answers(*replies, complete=True):
    a = E._Answers((f"host{i}", r) for i, r in enumerate(replies))
    a.meta = {"complete": complete, "done": threading.Event()}
    return a

# 1. a send is only "rejected" when every endpoint really refused it
check("a transaction already in the pool is not a refusal",
      not E.SENDER.rejected(answers({"error": "already known"}, {"error": "timeout"})))
check("'nonce too low' (already mined) is not a refusal",
      not E.SENDER.rejected(answers({"error": {"message": "nonce too low"}}, {"error": "boom"})))
check("a real refusal from every endpoint is a refusal",
      E.SENDER.rejected(answers({"error": "insufficient funds"}, {"error": "insufficient funds"})))
check("an accepted transaction is not a refusal", not E.SENDER.rejected(answers({"result": "0xabc"}, {"error": "x"})))
check("replies still outstanding are never read as a refusal",
      not E.SENDER.rejected(answers({"error": "insufficient funds"}, complete=False)))

# 2. the answers a thread reads are its own, not another thread's
E.SENDER._local.last = answers({"result": "0xmine"})
other = []
t = threading.Thread(target=lambda: (setattr(E.SENDER._local, "last", answers({"result": "0xtheirs"})), other.append(E.SENDER.mine())))
t.start(); t.join()
check("each thread reads the answers of its own send",
      E.SENDER.mine()[0][1]["result"] == "0xmine" and other[0][0][1]["result"] == "0xtheirs")

# 3. the exit's retries replace the stuck transaction instead of queueing behind it, and the fee is capped
seen = []
E.state["base_fee"] = 10 ** 8; E.state["gas_price"] = 2 * 10 ** 8; E.state["eth_usd"] = 2500.0
E.next_nonce = lambda: 41
E.wait_receipt = lambda h, timeout=10.0, ans=None: None
E.SEND = lambda tx, label: (seen.append((tx["nonce"], int(tx["gasPrice"], 16))), "0x" + "%064x" % len(seen))[1]
E.SELL_CONFIRM_S = 0.01
rec, h = E.send_confirmed(lambda cap, nonce: {"nonce": nonce, "gasPrice": hex(int(cap))}, "sell", 0.6)
check("every retry re-sends at the same nonce", len({n for n, _ in seen}) == 1, f"nonces {sorted({n for n, _ in seen})}")
worst = max(g for _, g in seen) * E.GAS_SELL / 1e18 * 2500.0
check("the exit's fee is capped near the configured ceiling", worst <= E.SELL_FEE_MAX_USD * 1.01, f"worst ${worst:.2f}")
check("the retries did happen", len(seen) >= 2, f"{len(seen)} attempts")

# 4. a position saved while it is being sold must be sellable again after a restart
E.SEND = None
E.state["open"] = {"curve": "0xc", "token": "0xt", "tokens": 1.0, "closing": True, "nonce": 7}
E.save_state()
saved = json.load(open(E.STATE_PATH))
check("the in-flight 'closing' flag is not written to disk", "closing" not in saved["open"])
E.state["open"] = None; E.load_state()
check("a restart restores the position without the flag", isinstance(E.state["open"], dict) and "closing" not in E.state["open"])

# 5. a reserved but unused nonce is given back, and the next launch waits for a fresh one
E.state["nonce"] = 50; E.state["chain_at"] = E.mono(); E.state["busy_until"] = E.mono() + 99
E.release_reservation()
check("the nonce is released and marked stale", E.state["nonce"] is None and E.mono() - E.state["chain_at"] > 30)
check("the engine is not left marked busy", E.state["busy_until"] == 0.0)

# 6. a crash in the launch thread after the buy sells the position instead of stranding it
closed = []
E.close_position = lambda pos, why: closed.append((pos["curve"], why))
E.state["open"] = {"curve": "0xdead", "token": "0xt", "tokens": 1.0}
E._handle_creation = lambda *a: (_ for _ in ()).throw(RuntimeError("simulated crash after the buy"))
E.handle_creation("0xcreator", E.ZERO, 0, E.mono(), int(time.time()), set(), 0)
time.sleep(0.3)
check("a crash after the buy triggers the sell", len(closed) == 1 and closed[0][0] == "0xdead", f"closed={closed}")
alarm = [json.loads(l) for l in open(E.LOG_PATH) if '"alarm"' in l]
check("and it is logged as an alarm, not swallowed", any("crashed" in str(a.get("what")) for a in alarm))
# and with no position open it only gives the nonce back
closed.clear(); E.state["open"] = None; E.state["nonce"] = 60; E.state["chain_at"] = E.mono()
E.handle_creation("0xcreator", E.ZERO, 0, E.mono(), int(time.time()), set(), 0)
check("a crash before the buy strands nothing", not closed and E.state["nonce"] is None)

print("\n" + ("all safety tests pass" if not fails else f"{len(fails)} SAFETY TESTS FAILED: " + ", ".join(fails)))
raise SystemExit(1 if fails else 0)
