"""The scorer on real second boundaries (engine 6.06): block_clock turns the feed's flips (second -> first block) into a
clock where the seat's second's first block sits at exactly 1.0 s, whatever the creation block's offset inside its second;
the front seat then enters at that block, ahead of its buyers, and the block-offset fallback enters later.

    python3 tests/test_clock.py
"""
import os, sys, tempfile
os.environ["LOG_PATH"] = tempfile.mkdtemp() + "/t.jsonl"
for k, v in (("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("BUNDLE_MIN", "3"), ("BUNDLE_MIN_ETH", "0.02"), ("HOLD_S", "1.3"), ("SEAT", "E1"), ("BURST_N", "35"), ("RELAY", "0x00000000000000000000000000000000000beef3")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E
fails = []
def check(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f"   ({detail})" if detail and not ok else ""))
    if not ok: fails.append(name)

# flips: second 1000 began at block 5000, 1001 at 5010, 1002 at 5019 (a nine-block second), 1003 at 5029, ...
E.state["flip_block"] = {1000: 5000, 1001: 5010, 1002: 5019, 1003: 5029, 1004: 5039, 1005: 5049, 1006: 5059}
E.state["eth_usd"] = 2500.0; E.state["base_fee"] = 10 ** 8
tof = E.block_clock(5007)                                                # the creation block is the 8th block of second 1000
check("clock: built when the flips cover the launch", tof is not None)
check("clock: the creation block sits inside its second (0.7 s)", tof and abs(tof(5007) - 0.7) < 1e-9, str(tof and tof(5007)))
check("clock: the seat's second's first block is exactly 1.0", tof and abs(tof(5010) - 1.0) < 1e-9, str(tof and tof(5010)))
check("clock: the second after that is exactly 2.0, nine-block second and all", tof and abs(tof(5019) - 2.0) < 1e-9, str(tof and tof(5019)))
check("clock: none when the flips end before the launch is over", E.block_clock(5050) is None)
check("clock: none when the flips start after the creation", E.block_clock(4990) is None)

# a launch: the creation buy at 5007, the bundle at 5007-5008, a bot in the seat's first block (5010), buyers in 5011-5020, a sell at 5030
Y0 = E.Y0; tier = 0.02
def buy_row(b, li, eth, tk): return (b, li, True, eth, tk, 0.0)
def sell_row(b, li, tk, eth): return (b, li, False, eth, tk, 0.0)
def net_of(X, Y, tk): return X * tk / (Y - tk)
X, Y = E.X0, Y0; ev = []
tk0 = 0.02 * Y0; q0 = net_of(X, Y, tk0) / (1 - tier); ev.append(buy_row(5007, 0, q0, tk0)); X += net_of(X, Y, tk0); Y -= tk0
for b, li in ((5007, 1), (5007, 2), (5008, 0)):                          # three named buys, tier only
    tk = 0.004 * Y0; q = net_of(X, Y, tk) / (1 - tier); ev.append(buy_row(b, li, q, tk)); X += net_of(X, Y, tk); Y -= tk
tk = 0.006 * Y0; q = net_of(X, Y, tk) / (1 - tier - 0.0618); ev.append(buy_row(5010, 1, q, tk)); X += net_of(X, Y, tk); Y -= tk   # a bot at the seat's first block, surcharged
for b in range(5011, 5021):
    tk = 0.012 * Y0; q = net_of(X, Y, tk) / (1 - tier); ev.append(buy_row(b, 0, q, tk)); X += net_of(X, Y, tk); Y -= tk
r_sec = E.exact_score(ev, 5007, tk0, 0.0057, "E1", gated=True, front=True, readouts=False, tof=tof)
r_off = E.exact_score(ev, 5007, tk0, 0.0057, "E1", gated=True, front=True, readouts=False)
check("the synthetic launch passes the rule (three named buys)", r_sec is not None and r_sec[0] != "filtered", str(r_sec))
if r_sec is None or r_sec[0] == "filtered": print("\nFAILED: filtered"); os._exit(1)
check("front seat on the real clock: enters at 1.0 s, the seat's first block", r_sec and abs(r_sec[2] - 1.0) < 1e-9, str(r_sec and r_sec[2]))
check("front seat on the real clock: pays (ahead of the bot and the ten buyers)", r_sec and r_sec[0] > 0, str(r_sec and r_sec[0]))
check("block-offset fallback: enters later (block 5017, after the bot and six buyers) and earns less", r_off and r_off[0] < r_sec[0], f"{r_off and r_off[0]} vs {r_sec and r_sec[0]}")
r_behind = E.exact_score(ev, 5007, tk0, 0.0057, "E1", gated=True, front=False, readouts=False, tof=tof)
check("behind seat on the real clock: 0.3 s after the bot, earns less than the front", r_behind and r_behind[0] < r_sec[0])
print("\nFAILED: " + str(fails) if fails else "\nall checks passed"); os._exit(1 if fails else 0)
