"""Engine 6.5: the watch's replay folds the feed's earlier buys in chronological order. Before, direct buys came first, so a
stranger's (reverting) shot at block 2 closed the bundle before the helper's named buys at block 1 were folded, and the
launch was refused with "bundle 0 < 3" (Sep 25: 0xd43ed726, the afternoon's only sure fire; 0xba059c17; Sep 24: 0x56e76663).

    python3 tests/test_bundle_order.py
"""
import os, sys
os.environ.setdefault("LOG_PATH", "/tmp/test_bundle_order.jsonl")
for k, v in (("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("BURST_N", "35"), ("WALLET", "0xe0686dc72b04c12ceefeea75e286e4ef7c056f01"), ("RELAY", "0xe8e98c3514d5bd83fdd01360896f2382b861a720")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E
CV = "0x" + "ab" * 20; cb = bytes.fromhex(CV[2:]); NAMED = {"0x" + "11" * 20, "0x" + "22" * 20, "0x" + "33" * 20}; CREATOR = "0x" + "44" * 20; STRANGER = "0x" + "55" * 20
passed = 0
def check(name, ok):
    global passed
    print(("ok   " if ok else "FAIL ") + name); passed += ok; assert ok, name
E.state["watch"].clear(); E.state["buys"].clear(); E.state["sells"].clear(); E.state["valtx"].clear()
T0 = 1_700_000_000
helper_data = b"\x6f\x49\x22\x7e" + b"".join(b"\0" * 12 + bytes.fromhex(a[2:]) for a in sorted(NAMED)) + b"\0" * 12 + cb   # one call naming the three buyers and the curve
E.sender_of = lambda t: CREATOR
E.state["valtx"].append([1, T0, None, 0.4, helper_data, b"raw-helper", 101, "0x" + "77" * 20, "6f49227e"])       # seen 1, block 1: the bundle's helper, 0.4 ETH
E.state["buys"][CV].append((T0, STRANGER, 0.02, 2, 102, CV, "59a87bc1"))                                          # seen 2, block 2: a stranger's direct shot (it reverts on chain)
order = E.curve_buys(CV)
check("curve_buys returns the helper (block 1) before the stranger's shot (block 2)", [b[4] for b in order] == [101, 102])
w = E.watch_curve(CV, 1e7, T0, set(NAMED), CREATOR, blk0=100, tax_bps=200)
check("the bundle is the helper's three named buyers", w["bundle"] == 3 and w["wallets"] == NAMED)
check("the bundle's ETH is the helper's value", abs(w["bundle_eth"] - 0.4) < 1e-9)
check("the stranger's later shot closes the bundle after it was counted", w.get("bundle_closed") is True)
# the old order (direct buys first) must not come back: a second stranger shot at block 3 must not reopen or zero anything
E.fold_buy(w, T0, STRANGER, 0.02, 103, CV, "59a87bc1")
check("later strangers change nothing", w["bundle"] == 3 and abs(w["bundle_eth"] - 0.4) < 1e-9)
print(f"\n{passed} checks passed")
