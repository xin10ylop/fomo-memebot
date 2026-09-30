"""The creation-second seat (engine 5.3) enters only once the bundle is visible on the feed: the named wallets' buys resolve
the curve and fill the gates; a launch whose bundle never shows within E0_BUNDLE_WAIT_S is skipped without an RPC call and
without a send. Driven on a scripted feed state, no network.

    python3 tests/test_e0_wait.py
"""
import os, sys, json, time, threading, tempfile
LOG = tempfile.mkdtemp() + "/t.jsonl"; os.environ["LOG_PATH"] = LOG
for k, v in (("SEAT", "E0"), ("E0_OUTSIDER", "1"), ("BUNDLE_MIN", "3"), ("BUNDLE_MIN_ETH", "0.3"), ("BUNDLE_MAX_ETH", "0"), ("MIN_CREATOR_SUPPLY", "0.01"),
             ("TIER_MIN_BPS", "100"), ("TIER_MAX_BPS", "200"), ("E0_BUNDLE_WAIT_S", "0.4"), ("E0_BUNDLE_MAX_BLOCKS", "3"), ("MAX_RESOLVE_MS", "300"), ("HOLD_S", "0.3"), ("TAKE_PROFIT", "0"),
             ("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("TRADE_HOURS", ""), ("MIN_FOLLOW_ETH_60", "0"), ("BANKROLL_USD", "300"), ("STAKE_MIN", "10"), ("STAKE_MAX", "10")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E

# ---- engine 6.9: two feed sockets, one index ------------------------------------------------------------------------
E.index_message = lambda inner, ts, seen: E.state.setdefault("_indexed", []).append((ts, seen))
E.score_flip = lambda ts, wall, seen: None
E.prune = lambda seen: None
E._frame_stat = lambda seen: None
checks = 0


def ok(cond, what):
    global checks
    if not cond:
        raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)


def frame(seq, ts, kind=3):
    return json.dumps({"messages": [{"sequenceNumber": seq, "message": {"message": {"header": {"kind": kind, "timestamp": ts}}}}]})


S = E.state; now = time.time(); base = 1000.0
S.update({"ingested_seq": 0, "blocks": 0, "last_seen_ts": 0, "feed_ts": 0, "feed_seq": 0, "prev_seen": None, "prev_ts": 0, "ref": None, "_indexed": []}); S["brackets"].clear(); S["flip_at"].clear(); S["arrivals"].clear()
ts0 = int(now) - 1
# socket A delivers block 101 (second ts0) at t=base, socket B the same block 4 ms earlier; then B delivers 102 (second ts0+1) first, A's copy later
E._ingest_frame(frame(101, ts0), base - 0.004, now, sock=2)
E._ingest_frame(frame(101, ts0), base, now, sock=1)
ok(S["blocks"] == 1 and S["ingested_seq"] == 101 and len(S["_indexed"]) == 1, "the same block from both sockets is counted and indexed once")
ok(S["_indexed"][0][1] == base - 0.004, "at the earlier of the two arrivals")
E._ingest_frame(frame(102, ts0 + 1), base + 0.096, now + 0.1, sock=2)
E._ingest_frame(frame(102, ts0 + 1), base + 0.100, now + 0.1, sock=1)
ok(S["blocks"] == 2 and S["feed_seq"] == 102 and S["feed_ts"] == ts0 + 1, "the next block advances the counters once")
ok(S["flip_at"].get(ts0 + 1) == base + 0.096, "the second's flip is stamped at the earlier socket's arrival")
ok(len(S["brackets"]) == 1 and abs((S["brackets"][0][1] - S["brackets"][0][0]) - 0.1) < 1e-9, "one bracket per flip, from the earliest arrivals")
# a reconnect replay (old blocks, warm) on either socket: nothing indexed, counters untouched, sequence not moved backwards
E._ingest_frame(frame(100, ts0 - 1), base + 0.2, now + 0.2, sock=2)
ok(S["blocks"] == 2 and S["ingested_seq"] == 102 and len(S["_indexed"]) == 2, "an older block from a reconnect's replay is dropped")
# a genuinely new but warm block (delivered 3 s late) is counted but not indexed, as before 6.9
E._ingest_frame(frame(103, ts0 + 2), base + 3.3, now + 3.3, sock=1)
ok(S["blocks"] == 3 and len(S["_indexed"]) == 2 and S["ingested_seq"] == 103, "a late-delivered block is counted, not indexed")
# batch reports (kind != 3) never move the sequence
E._ingest_frame(frame(200, ts0 + 5, kind=1), base + 3.4, now + 3.4, sock=2)
ok(S["ingested_seq"] == 103, "a batch report does not move the sequence")

# ---- the venue guard -----------------------------------------------------------------------------------------------
answers = {}
class FakeRpc:
    def call(self, method, params, **kw):
        sel = params[0]["data"]
        if sel not in answers: raise RuntimeError("rpc down")
        return hex(answers[sel])
E.rpc = FakeRpc(); logged = []; E.log = lambda d: logged.append(d)
E.venue_check(first=True)
ok(S["venue_ok"] is True and S.get("venue") is None, "a failed read at start leaves the guard open with no answer recorded")
answers[E._VENUE_SELS[0]] = 3; answers[E._VENUE_SELS[1]] = 9900
E.venue_check(first=True)
ok(S["venue_ok"] is True and S["venue"] == [3, 9900], "3 s / 9900 bps: the schedule the seat model was built on")
answers[E._VENUE_SELS[0]] = 5
E.venue_check()
ok(S["venue_ok"] is False and S["venue"] == [5, 9900], "5 s: the guard closes")
last = logged[-1]
ok(last["ev"] == "alarm" and last["snipe_tax_seconds"] == 5, "and one alarm is logged")
del answers[E._VENUE_SELS[0]]
E.venue_check()
ok(S["venue_ok"] is False, "a failed read keeps the last answer (still closed)")
answers[E._VENUE_SELS[0]] = 3
E.venue_check()
ok(S["venue_ok"] is True, "back to 3 s: the guard opens")

# ---- gas: the cost estimate on the base fee, the shooters' need on the cap -----------------------------------------
S["base_fee"] = 20_000_000; S["gas_price"] = int(S["base_fee"] * 6.0); S["eth_usd"] = 2700.0
ok(abs(E.gas_cost_usd() - E.burst_gas_units() * 20_000_000 / 1e18 * 2700.0) < 1e-9, "the gas gate prices the round trip at the base fee, not the cap")
S["base_fee_hist"].clear()
ok(abs(E.shooter_need_eth() - max(E.SHOOTER_MIN_ETH, E.RELAY_SHOOT_GAS * S["base_fee"] * E.SHOOTER_HEADROOM / 1e18 * 1.1)) < 1e-15 and E.shooter_need_eth() <= 0.0001, "6.10: a shooter's need follows the typical base fee (x2), not the 6x cap, and stays under its target float today")
for _ in range(20):
    S["base_fee_hist"].append(S["base_fee"])
S["base_fee"] = int(0.5e9); S["gas_price"] = int(S["base_fee"] * 6.0)
ok(E.shooter_need_eth() == E.SHOOTER_MIN_ETH, "one ramped poll does not raise the need (the ten-minute median holds)")
S["base_fee_hist"].clear()
for _ in range(20):
    S["base_fee_hist"].append(S["base_fee"])
ok(E.shooter_need_eth() > E.SHOOTER_MIN_ETH and E.shooter_target_eth() == 3 * E.shooter_need_eth(), "a ramp that lasts ten minutes raises the need and the top-up target together")
print(f"\n{checks} checks passed")
