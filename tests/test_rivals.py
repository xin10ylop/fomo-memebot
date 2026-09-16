"""chain_rivals_loop (engine 5.0) against a scripted provider socket: one Buy-log subscription per watched curve, dropped when
the watch ends; a landed Buy is placed in its second from the feed's flip bookkeeping (flip_block, feed_seq), a Buy the feed has
not passed yet waits, a team wallet's or an unwatched curve's Buy is ignored.

    python3 tests/test_rivals.py
"""
import os, sys, json, asyncio, tempfile, threading, collections
os.environ["LOG_PATH"] = tempfile.mkdtemp() + "/t.jsonl"; os.environ["SEND_MODULE"] = ""; os.environ["PRIVATE_KEY"] = ""
os.environ["PROVIDER_WS"] = "wss://fake.invalid/v2/x"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E

fails = []
def check(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f"   ({detail})" if detail and not ok else ""))
    if not ok: fails.append(name)

TS0 = 1789555700; C = "0x" + "c1" * 20; OTHER = "0x" + "d2" * 20; NAMED = "0x" + "aa" * 20; BOT = "0x" + "bb" * 20
FB = {TS0: 1000, TS0 + 1: 1010, TS0 + 2: 1020}                    # first block of each second
E.state["flip_block"] = dict(FB); E.state["feed_seq"] = 1023
E.state["watch"][C] = {"ts0": TS0, "named": {NAMED}, "creator": "0x" + "ee" * 20, "out1": 0, "out2": 0, "out1_chain": 0, "out2_chain": 0}
events = []; E.log = lambda d: events.append(d)

def buy_log(curve, block, buyer):
    return {"jsonrpc": "2.0", "method": "eth_subscription", "params": {"subscription": "0xsub1", "result": {
        "address": curve, "blockNumber": hex(block), "topics": [E.BUY_EV, "0x" + "0" * 64, "0x" + "0" * 24 + buyer[2:]], "data": "0x" + "%064x" % int(0.05e18)}}}
def advance():                                                     # the feed passes second three
    E.state["flip_block"][TS0 + 3] = 1026; E.state["feed_seq"] = 1030
def drop():
    E.state["watch"].pop(C)

script = [
    "wait",                                                        # the loop sends the subscription first
    {"jsonrpc": "2.0", "id": 2, "result": "0xsub1"},
    buy_log(C, 1013, BOT),                                          # second one, an outsider
    buy_log(C, 1021, NAMED),                                        # second two, the team: ignored
    buy_log(C, 1022, BOT),                                          # second two, an outsider
    buy_log(C, 1024, BOT),                                          # a block the feed has not passed: held
    buy_log(OTHER, 1013, BOT),                                      # not watched: ignored
    "wait", advance, "wait", "wait",                                # the feed catches up: the held Buy lands in second two
    "wait", drop, "wait", "wait",                                   # the watch ends: unsubscribe
    "stop"]
sent = []
class FakeWS:
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    async def send(self, m): sent.append(json.loads(m))
    async def recv(self):
        await asyncio.sleep(0.005)
        item = script.pop(0)
        if item == "wait": raise asyncio.TimeoutError()
        if item == "stop": raise asyncio.CancelledError()
        if callable(item): item(); raise asyncio.TimeoutError()
        return json.dumps(item)
class FakeWebsockets:
    @staticmethod
    def connect(*a, **k): return FakeWS()
try:
    asyncio.run(E.chain_rivals_loop(FakeWebsockets))
except asyncio.CancelledError:
    pass

w = None
rivals = [e for e in events if e.get("ev") == "rival_chain"]
subs = [m for m in sent if m["method"] == "eth_subscribe"]; unsubs = [m for m in sent if m["method"] == "eth_unsubscribe"]
check("one subscription, on the watched curve only, with the Buy topic", len(subs) == 1 and subs[0]["params"] == ["logs", {"address": C, "topics": [[E.BUY_EV]]}], str(subs))
check("the subscription is dropped when the watch ends", len(unsubs) == 1 and unsubs[0]["params"] == ["0xsub1"], str(unsubs))
check("the second-one outsider counted in second one", any(r["second"] == 1 and r["buyer"] == BOT and r["block"] == 1013 for r in rivals), str(rivals))
check("the team's buy is not a rival", not any(r["buyer"] == NAMED for r in rivals))
check("the second-two outsider counted in second two", any(r["second"] == 2 and r["block"] == 1022 for r in rivals))
check("the held Buy landed once the feed passed its block, in second two", any(r["second"] == 2 and r["block"] == 1024 for r in rivals), str(rivals))
check("an unwatched curve's buy is ignored", not any(r["curve"] == OTHER for r in rivals))
check("exactly three rivals counted", len(rivals) == 3, str(len(rivals)))
check("second_of_block: before the feed passed it -> None", E.second_of_block(1031) is None)
check("second_of_block: exact at the boundary", E.second_of_block(1020) == TS0 + 2 and E.second_of_block(1019) == TS0 + 1)
check("no feed_error was logged", not any(e.get("ev") == "feed_error" for e in events), str([e for e in events if e.get("ev") == "feed_error"]))
print("\nall rivals tests pass" if not fails else f"\n{len(fails)} FAILED: {fails}"); sys.exit(1 if fails else 0)
