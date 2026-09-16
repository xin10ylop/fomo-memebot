"""The launch filter, tested on synthetic curves instead of waiting for the market: a launch is built to order and run
through the engine's own scorer, which applies the same thresholds the live gates do.

    python3 tests/test_gates.py
"""
import os, sys
os.environ.setdefault("LOG_PATH", "/tmp/test_gates.jsonl")
for k, v in (("BUNDLE_MIN", "5"), ("BUNDLE_MIN_ETH", "0.3"), ("BUNDLE_MAX_ETH", "1.2"), ("MIN_CREATOR_SUPPLY", "0.03"), ("OUT1_MAX", "0"), ("SEND_MODULE", ""), ("PRIVATE_KEY", "")):
    os.environ[k] = v
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "strategy"))
import sniper_engine as E

X0, Y0 = E.X0, E.Y0


def launch(creator_share, team_n, team_eth, out1=0, tier=0.01):
    """(events, tk0): a creation buy of creator_share of supply, team_n equal buys summing to team_eth in the next block,
    and out1 outsiders paying the second-one surcharge. Prices follow the curve exactly, as the chain would report."""
    ev = []; X, Y = X0, Y0; b = 1000
    tk = creator_share * Y0; net = X * tk / (Y - tk); ev.append((b, 0, True, net / (1 - tier), tk, 0.0)); X += net; Y -= tk; tk0 = tk
    for i in range(team_n):
        q = team_eth / team_n; net = q * (1 - tier); t = Y - X * Y / (X + net)
        ev.append((b + 1, i, True, q, t, 0.0)); X += net; Y -= t
    for i in range(out1):
        q = 0.05; net = q * (1 - tier - 0.0618); t = Y - X * Y / (X + net)
        ev.append((b + 11, i, True, q, t, 0.0)); X += net; Y -= t          # ~1 s later at 9.9 blocks/s: second one
    for i in range(4):                                                      # followers during the hold, then a team sell
        q = 0.08; net = q * (1 - tier - 0.0019); t = Y - X * Y / (X + net)
        ev.append((b + 22 + i, 0, True, q, t, 0.0)); X += net; Y -= t
    return ev, tk0


def verdict(**kw):
    ev, tk0 = launch(**kw)
    r = E.exact_score(ev, 1000, tk0, 25 / 2500.0, "E2", gated=True, tp=0.5)
    return "no launch-block buy" if r is None else ("FILTERED" if r[0] == "filtered" else "traded")


cases = [
    ("the shape the rule wants", dict(creator_share=0.05, team_n=8, team_eth=0.8), "traded"),
    ("team of 4 (under the five-wallet floor)", dict(creator_share=0.05, team_n=4, team_eth=0.8), "FILTERED"),
    ("team puts in 0.2 ETH (under the floor)", dict(creator_share=0.05, team_n=8, team_eth=0.2), "FILTERED"),
    ("team puts in 1.5 ETH (over the new cap)", dict(creator_share=0.05, team_n=8, team_eth=1.5), "FILTERED"),
    ("team puts in 1.19 ETH (just under the cap)", dict(creator_share=0.05, team_n=8, team_eth=1.19), "traded"),
    ("creator holds 2% (under the new floor)", dict(creator_share=0.02, team_n=8, team_eth=0.8), "FILTERED"),
    ("creator holds 3.1% (just over)", dict(creator_share=0.031, team_n=8, team_eth=0.8), "traded"),
    ("a bot bought in second one", dict(creator_share=0.05, team_n=8, team_eth=0.8, out1=1), "FILTERED"),
]
bad = 0
for name, kw, want in cases:
    got = verdict(**kw)
    ok = got == want
    bad += not ok
    print(f"{'ok ' if ok else 'FAIL'} {name:44s} wanted {want:9s} got {got}")
print(("all gate tests pass" if not bad else f"{bad} GATE TESTS FAILED"))
raise SystemExit(1 if bad else 0)
