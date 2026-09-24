"""Engine 6.1: the pre-tick attacker count (report 24.30), the hold in blocks, the measured gas model and the kill line.

    python3 tests/test_attack_gate.py
"""
import os, sys
os.environ.setdefault("LOG_PATH", "/tmp/test_attack_gate.jsonl")
for k, v in (("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("BURST_N", "35"), ("HOLD_S", "1.3"), ("HOLD_BLOCKS", "300"), ("ATTACK_MIN", "2"), ("KILL_USD", "15"),
             ("WALLET", "0xe0686dc72b04c12ceefeea75e286e4ef7c056f01"), ("RELAY", "0xe8e98c3514d5bd83fdd01360896f2382b861a720")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E

CV = "0x" + "ab" * 20; NAMED = {"0x" + "11" * 20, "0x" + "22" * 20}; CREATOR = "0x" + "33" * 20
passed = 0


def check(name, ok):
    global passed
    print(("ok   " if ok else "FAIL ") + name); passed += ok
    assert ok, name


def fresh():
    E.state["watch"].clear(); E.state["buys"].clear(); E.state["sells"].clear()
    return E.watch_curve(CV, 1e7, 1_700_000_000, set(NAMED), CREATOR, blk0=100, tax_bps=200)


# 1. the record and the count
w = fresh()
check("a watched curve starts with no attackers", E.attackers(w) == 0 and w["attack_targets"] == set() and w["attack_senders"] == set())
cb = bytes.fromhex(CV[2:])
E.note_attack(w, "0x" + "8532" * 10, b"", b"\x16\x22\xdb\xe4" + b"\0" * 12 + cb, CV)          # a relay's shot naming the curve
E.note_attack(w, "0x" + "8532" * 10, b"", b"\x16\x22\xdb\xe4" + b"\0" * 12 + cb, CV)          # a second shooter of the same fleet: same relay
E.note_attack(w, "0x" + "f300" * 10, b"", b"\x9c\xbb\x2c\x35" + cb, CV)                        # another fleet
check("two relays firing count as two attackers whatever their shooter count", E.attackers(w) == 2 and len(w["attack_targets"]) == 2)
E.sender_of = lambda t: "0x" + "44" * 20
E.note_attack(w, CV, b"", b"\x59\xa8\x7b\xc1", CV)                                              # a direct call to the curve from a stranger
check("a direct caller counts once", E.attackers(w) == 3 and w["attack_senders"] == {"0x" + "44" * 20})
E.note_attack(w, CV, b"", b"\x59\xa8\x7b\xc1", CV)
check("the same direct caller again does not", E.attackers(w) == 3)
E.sender_of = lambda t: "0x" + "11" * 20
E.note_attack(w, CV, b"", b"\x59\xa8\x7b\xc1", CV)
check("a named wallet's own buy is not an attacker", E.attackers(w) == 3)
E.sender_of = lambda t: CREATOR
E.note_attack(w, CV, b"", b"", CV)
check("the creator is not an attacker", E.attackers(w) == 3)
E.note_attack(w, E.RELAY, b"", b"\x16\x22\xdb\xe4" + b"\0" * 12 + cb, CV)
check("our own shooters' shots (to our relay) are not attackers", E.attackers(w) == 3)
helper = b"\x01\x02\x03\x04" + b"\0" * 12 + bytes.fromhex("11" * 20) + b"\0" * 12 + cb
E.note_attack(w, "0x" + "77" * 20, b"", helper, CV)
check("the bundle's helper call (it names a named wallet) is not an attacker", E.attackers(w) == 3)
check("OUR_ADDRS holds the wallet and the relay", E.OUR_ADDRS == {E.WALLET, E.RELAY})
w["tb"] = bytes.fromhex("99" * 20)
E.note_attack(w, "0x" + "99" * 20, b"", b"\x09\x5e\xa7\xb3" + b"\0" * 12 + cb + b"\xff" * 32, CV)   # approve(curve, amount) on the token
check("an approve on the launch's own token (naming the curve as spender) is not an attacker", E.attackers(w) == 3)

# 1b. engine 6.3: the shooter wallets behind the relays (the unit the tables count), and ATTACK_UNIT
w3 = fresh(); real_sender = E.sender_of
E.sender_of = lambda t: "0x" + "a1" * 20
E.note_attack(w3, "0x" + "8532" * 10, b"", b"\x16\x22\xdb\xe4" + b"\0" * 12 + cb, CV)          # shooter a1 through relay 8532
E.sender_of = lambda t: "0x" + "a2" * 20
E.note_attack(w3, "0x" + "8532" * 10, b"", b"\x16\x22\xdb\xe4" + b"\0" * 12 + cb, CV)          # shooter a2 through the same relay
check("one relay, two shooters: 1 fleet, 2 wallets", E.attack_fleets(w3) == 1 and E.attack_wallets(w3) == 2)
E.note_attack(w3, CV, b"", b"\x59\xa8\x7b\xc1", CV)                                             # a2 also calls the curve directly
check("a direct call by a wallet already counted adds a fleet (direct sender) but not a wallet", E.attack_fleets(w3) == 2 and E.attack_wallets(w3) == 2)
E.sender_of = lambda t: "0x" + "11" * 20
E.note_attack(w3, "0x" + "f300" * 10, b"", b"\x9c\xbb\x2c\x35" + cb, CV)                        # a named wallet through another relay
check("a named wallet behind a relay is not a wallet (the relay still counts as a fleet)", E.attack_fleets(w3) == 3 and E.attack_wallets(w3) == 2)
E.sender_of = lambda t: E.WALLET
E.note_attack(w3, "0x" + "f300" * 10, b"", b"\x9c\xbb\x2c\x35" + cb, CV)
check("our own wallet behind a relay is not a wallet", E.attack_wallets(w3) == 2)
E.sender_of = lambda t: E.WALLET
E.note_attack(w3, "0x" + "4985" * 10, b"", b"\xa5\x9a\xc6\xdd" + b"\0" * 12 + cb, CV)                    # our own wallet through a retired relay (Sep 18-19)
check("our own wallet behind any relay is not a fleet (6.4)", E.attack_fleets(w3) == 3)
check("ATTACK_UNIT defaults to fleets and attackers() counts fleets", E.ATTACK_UNIT == "fleets" and E.attackers(w3) == 3)
E.ATTACK_UNIT = "wallets"
check("ATTACK_UNIT=wallets: attackers() counts the shooter wallets", E.attackers(w3) == 2)
E.ATTACK_UNIT = "fleets"; E.sender_of = real_sender
E.note_attack(w3, "0x" + "f301" * 10, b"", b"\x9c\xbb\x2c\x35" + cb, CV)                        # a relay call whose raw transaction cannot be decoded (b"")
check("an undecodable relay transaction still counts the relay and does not raise", E.attack_fleets(w3) == 4 and E.attack_wallets(w3) == 2)
check("ATTACK_BUILD_MIN defaults to 0 (no count required at the build)", E.ATTACK_BUILD_MIN == 0)

# 2. the gate's wording (the decision path is exercised live; here the threshold arithmetic)
check("ATTACK_MIN read from the environment", E.ATTACK_MIN == 2)
w2 = fresh(); E.note_attack(w2, "0x" + "8532" * 10, b"", cb, CV)
check("one attacker is below a threshold of two", E.attackers(w2) < E.ATTACK_MIN)

# 3. the hold in blocks
check("HOLD_BLOCKS and the effective seconds", E.HOLD_BLOCKS == 300 and abs(E.HOLD_EFF - 300 / 9.9) < 1e-9)
E.state["blocks"] = 1000; t0 = E.mono()
pos = {"blocks_at_fill": 1000}
check("holding while fewer than HOLD_BLOCKS feed blocks have passed", E.still_holding(pos, t0))
E.state["blocks"] = 1299
check("still holding one block short", E.still_holding(pos, t0))
E.state["blocks"] = 1300
check("the hold ends at HOLD_BLOCKS blocks after the fill", not E.still_holding(pos, t0))
E.state["blocks"] = 1000
check("the wall-clock cap ends the hold if the feed stalls", not E.still_holding(pos, t0 - (E.HOLD_EFF + 3.1)))
check("a position without a fill block holds HOLD_S seconds", E.still_holding({}, t0) and not E.still_holding({}, t0 - 1.4))
check("hold_cap is the blocks' seconds plus three", abs(E.hold_cap() - (E.HOLD_EFF + 3.0)) < 1e-9)

# 4. gas
u = E.burst_gas_units(35)
check("the burst's gas: 12 shots before the tick, the fill, 22 after, approve, sell", u == 12 * 88_594 + 137_693 + 22 * 27_021 + 50_000 + 80_000)
check("about 1.9M gas, not 230k", 1_800_000 < u < 2_100_000)
check("a ten-shot burst is about a third of it", 500_000 < E.burst_gas_units(10) < 700_000)
check("no burst: the plain round trip (the engine forces BURST_N to 1 without a send module)", E.BURST_N == 1 and E.burst_gas_units() == 230_000)
E.BURST_N = 35; E.state["base_fee"] = int(0.055e9); E.state["eth_usd"] = 2570.0
check("gas_usd reads about $0.28 at 0.055 gwei with the burst", 0.25 < E.gas_usd() < 0.32)
E.state["gas_price"] = int(0.07e9)
check("gas_cost_usd at the send price", 0.33 < E.gas_cost_usd() < 0.40)
E.BURST_N = 1

# 5. the kill line
E.state["bankroll"] = 22.5; E.state["killed"] = False
check("above the line: no gate", E.kill_gate() is None and E.state["killed"] is False)
E.state["bankroll"] = 14.99
g = E.kill_gate()
check("below the line: the gate names the numbers", g is not None and "14.99" in g and "15.00" in g and E.state["killed"] is True)
check("the alarm fires once", E.kill_gate() is not None and E.state["killed"] is True)
E.state["bankroll"] = 30.0
check("a top-up clears it", E.kill_gate() is None and E.state["killed"] is False)
print(f"\n{passed} checks passed")
