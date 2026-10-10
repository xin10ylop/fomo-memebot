"""6.26 (runbook 5bk): the guards that keep a second instance (the runner) from hurting the sniper or itself.
TIER_EARLY refuses by the tier from the creation's calldata before any lookup; FEED_LOCAL_ADDR binds the feed sockets to a second
address and REQUIRE_FEED_LOCAL_ADDR refuses to start without one the machine owns; the state file records its mode, and a change of
mode starts the bankroll, the day's stop and the scores fresh, drops a dry position, and refuses a dry start over a live position."""
import os, sys, json, tempfile, time
D = tempfile.mkdtemp(); LOG = D + "/r.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E1"), ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("SHOOTER_KEYS", ""), ("TIER_EARLY", "1"), ("TIER_MIN_BPS", "0"), ("TIER_MAX_BPS", "99"), ("BUNDLE_MIN", "3")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E
checks = 0
def ok(cond, what):
    global checks
    if not cond: raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)
logged = []; E.log = lambda d: logged.append(d)
looked = []
E.resolve_rpc = lambda *a, **k: looked.append("resolve_rpc") or None
E.watch_curve = lambda *a, **k: looked.append("watch_curve") or {}
NAMED = {"0x" + "%040x" % i for i in range(1, 6)}; CREATOR = "0x" + "c" * 40
def creation(tax):
    logged.clear(); looked.clear()
    E._handle_creation(CREATOR + str(tax)[-1], E.ZERO, int(0.3e18), E.mono(), 1791500000, NAMED, 1000, tax_bps=tax)
    return [d for d in logged if d.get("ev") == "skip"]
sk = creation(200)
ok(sk and "TIER_EARLY" in sk[0]["why"][0] and not looked, "a 2% token: refused from the calldata, before any lookup")
sk = creation(None)
ok(sk and "TIER_EARLY" in sk[0]["why"][0] and not looked, "an unreadable tax: refused (fail closed, as the late gate)")
sk = creation(0)
ok(not any("TIER_EARLY" in str(d.get("why")) for d in sk), "an untaxed token passes the early refusal")
E.TIER_EARLY = False; sk = creation(200)
ok(not any("TIER_EARLY" in str(d.get("why")) for d in sk), "TIER_EARLY off (the sniper): no early refusal, the old path")
E.TIER_EARLY = True
# the feed's local address
E.FEED_LOCAL_ADDR = ""; E.REQUIRE_FEED_LOCAL_ADDR = False
ok(E.feed_local() == {} and E.check_feed_local() is None, "unset (the sniper): no local address, nothing checked")
E.REQUIRE_FEED_LOCAL_ADDR = True
try: E.check_feed_local(); ok(False, "must refuse")
except SystemExit as e: ok("REQUIRE_FEED_LOCAL_ADDR" in str(e), "required but unset: refuses to start")
E.FEED_LOCAL_ADDR = "127.0.0.1"
ok(E.feed_local() == {"local_addr": ("127.0.0.1", 0)} and E.check_feed_local() is None, "an address the machine owns: bound as local_addr")
E.FEED_LOCAL_ADDR = "203.0.113.77"
try: E.check_feed_local(); ok(False, "must refuse")
except SystemExit as e: ok("not an address of this machine" in str(e), "an address the machine does not own: refuses to start")
E.FEED_LOCAL_ADDR = ""; E.REQUIRE_FEED_LOCAL_ADDR = False
src = open(E.__file__).read()
ok(src.count("compression=FEED_COMPRESSION, **feed_local()) as ws:") == 2, "both feed sockets leave from the local address")
ok("if (refused >= 5 or blocked) and not PROVIDER_WS and REQUIRE_FEED_LOCAL_ADDR:" in src and "await asyncio.sleep(window); refused = 0" in src, "refused or blocked with no provider: one alarm and a wait (an hour for a 403), not a 5 s retry loop")
ok(src.index("    load_state()\n    try:\n        check_feed_local()") > src.index("    load_send_step()\n") and 'close_position(state["open"], "recovered after restart (feed address missing)")' in src, "the address is checked at start after the state loads (6.27): a lost address sells an open live position before the stop, before the feed opens")
# the state file's mode
today = str(E.datetime.datetime.utcnow().date())
def load(saved, now_mode):
    json.dump(saved, open(E.STATE_PATH, "w")); os.environ["SEND_MODULE"] = "/etc/sniper/send_step.py" if now_mode == "live" else ""
    E.state.update({"bankroll": 30.0, "day_start": 30.0, "stopped": False, "open": None}); E.state["scores"].clear(); logged.clear()
    E.load_state(); return E.state
st = load({"mode": "dry", "day": today, "bankroll": 12.0, "day_start": 30.0, "stopped": True, "scores": [-0.5], "open": None}, "live")
ok(st["stopped"] is False and st["bankroll"] == 30.0 and not st["scores"] and any(d.get("ev") == "state_mode_changed" for d in logged), "dry -> live: the paper stop, bankroll and scores do not carry over")
st = load({"mode": "dry", "day": today, "bankroll": 30.0, "day_start": 30.0, "stopped": False, "scores": [], "open": {"curve": "0xab", "tokens": 1.0}}, "live")
ok(st["open"] is None, "dry -> live: a dry position is dropped (nothing on the chain to sell)")
try:
    load({"mode": "live", "day": today, "bankroll": 30.0, "day_start": 30.0, "stopped": False, "scores": [], "open": {"curve": "0xab", "buy_hash": "0x" + "1" * 64}}, "dry")
    ok(False, "must refuse")
except SystemExit as e:
    ok("LIVE position" in str(e), "live -> dry with a live position open: refuses to start (the dry exit would forget the tokens)")
st = load({"day": today, "bankroll": 12.0, "day_start": 30.0, "stopped": True, "scores": [0.1], "open": None}, "live")
ok(st["stopped"] is True and st["bankroll"] == 12.0 and list(st["scores"]) == [0.1], "a state file without a mode (the sniper's today): loaded as before")
st = load({"mode": "live", "day": today, "bankroll": 25.0, "day_start": 30.0, "stopped": False, "scores": [0.2], "open": None}, "live")
ok(st["bankroll"] == 25.0 and list(st["scores"]) == [0.2], "same mode: loaded as before")
E.state["day"] = E.datetime.datetime.utcnow().date(); E.save_state()
ok(json.load(open(E.STATE_PATH)).get("mode") == "live", "the state file records its mode")
print(f"all {checks} checks passed")
