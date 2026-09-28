"""K2/q7_e2.py: more fills. E2 (the first block of the second after E1: surcharge 0.19%, not 6.18%) priced from the tapes at first,
second and last place and every hold 0..30 from the E2 entry, on the launches that pass every pre-gate. By then the E1 block is on
the feed, so an E2 rule may read it (the ETH bought in E1, its buyers, the fleets that shot through it). Three uses: (a) instead of
E1 on the fires; (b) a second chance after a guard revert; (c) the launches refused at the gate (crowd seen only at the tick).
Rules chosen on one period and read on the other. The launch files' own E2 column (e1_multi's res, first place, hold 15) is shown
where no tape exists."""
import os, sys, json, gzip, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from sim import *
P = json.load(gzip.open(os.path.join(HERE, "prices.json.gz"), "rt")); PR = P["rows"]; I = P["HS"].index(11)
live = {r["x"]["cv"]: r for r in run()}
pre = [r for r in run(amin=0) if r.get("fired")]                       # every launch through the pre-gates and bundle gates (fleets ignored)
pre = [r["x"] for r in pre]
print(f"launches through every pre-gate: fit {sum(period(x)=='fit' for x in pre)}, read {sum(period(x)=='read' for x in pre)}; with a tape and an E2 block: {sum(1 for x in pre if x['cv'] in PR and PR[x['cv']].get('e2p1'))}")
def e1eth(x):
    p = PR.get(x["cv"]); return sum(b[0] for b in p["e1_buys"]) if p else (x["e1_block_eth"] or 0.0)
def e2(x, pos="e2p1", h=11):
    p = PR.get(x["cv"])
    if not p or not p.get(pos): return None
    return p[pos][h]
print("\n== (a) the live fires: E1 second place h11 against E2 at each place and hold (taped, E2 block known) ==")
for per in ("fit", "read"):
    F = [x for x in pre if period(x) == per and live[x["cv"]].get("fired") and e2(x) is not None]
    print(f"  {per} n {len(F)}: E1 second h11 {mean([PR[x['cv']]['p2'][I] for x in F]):+.1%}; " + "; ".join(f"E2 {pos[2:]} " + " ".join(f"h{h} {mean([e2(x, pos, h) for x in F]):+.1%}" for h in (3, 5, 8, 11, 15, 20, 30)) for pos in ("e2p1", "e2p2", "e2last")))
print("\n== (b) after a guard revert (7%): E2 first / second place ==")
for per in ("fit", "read"):
    F = [x for x in pre if period(x) == per and live[x["cv"]]["why"] == "GUARD" and e2(x) is not None]
    print(f"  {per} n {len(F)}: E1 second h11 (what the revert cost) {mean([PR[x['cv']]['p2'][I] for x in F]):+.1%}; E2 first " + " ".join(f"h{h} {mean([e2(x, 'e2p1', h) for x in F]):+.1%}" for h in (5, 8, 11, 15)) + "; E2 second " + " ".join(f"h{h} {mean([e2(x, 'e2p2', h) for x in F]):+.1%}" for h in (5, 8, 11, 15)))
print("\n== (c) refused at the gate (fleets < 2 at k-1+reg), E2 taken when the E1 block shows a crowd; $ at $13 after $0.33 gas ==")
R = [x for x in pre if live[x["cv"]]["why"] == "GATE fleets" and e2(x) is not None]
for per in ("fit", "read"):
    sub = [x for x in R if period(x) == per]
    print(f"  {per}: {len(sub)} refused launches with a tape; E2 first h11 all {mean([e2(x) for x in sub]):+.1%}, second {mean([e2(x,'e2p2') for x in sub]):+.1%}, last {mean([e2(x,'e2last') for x in sub]):+.1%}")
    for lab, f in (("E1 ETH >= 0.1", lambda x: e1eth(x) >= 0.1), ("E1 ETH >= 0.3", lambda x: e1eth(x) >= 0.3), ("E1 ETH >= 0.5", lambda x: e1eth(x) >= 0.5), ("E1 ETH >= 1.0", lambda x: e1eth(x) >= 1.0),
                   ("fleets through E1 >= 2", lambda x: x["f_E1r"] >= 2), ("fleets through E1 >= 4", lambda x: x["f_E1r"] >= 4), ("E1 buys >= 5", lambda x: len(PR[x["cv"]]["e1_buys"]) >= 5), ("E1 buys >= 10", lambda x: len(PR[x["cv"]]["e1_buys"]) >= 10)):
        s = [x for x in sub if f(x)]
        c = " ".join(f"{pos[2:]}: h8 {mean([e2(x,pos,8) for x in s]):+6.1%} h11 {mean([e2(x,pos,11) for x in s]):+6.1%} ${sum(e2(x,pos,11)*13-0.33 for x in s):+6.2f}" for pos in ("e2p1", "e2p2", "e2last"))
        print(f"     {lab:24s} n {len(s):3d} | {c}")
print("\n== (c') the same rules on EVERY launch through the pre-gates, E2 in addition to E1 (a second seat) ==")
for per in ("fit", "read"):
    sub = [x for x in pre if period(x) == per and e2(x) is not None]
    for lab, f in (("all", lambda x: True), ("E1 ETH >= 0.3", lambda x: e1eth(x) >= 0.3), ("E1 ETH >= 1.0", lambda x: e1eth(x) >= 1.0), ("fleets through E1 >= 4", lambda x: x["f_E1r"] >= 4)):
        s = [x for x in sub if f(x)]
        print(f"  {per} {lab:24s} n {len(s):3d} | " + " ".join(f"{pos[2:]}: h11 {mean([e2(x,pos,11) for x in s]):+6.1%} ${sum(e2(x,pos,11)*13-0.33 for x in s):+6.2f}" for pos in ("e2p1", "e2p2", "e2last")))
# the launch files' E2 column where there is no tape (e1_multi res, first place, hold 15, stake 10)
print("\n== the launch files' own columns (e1_multi: first place, hold 15): E1 vs E2, launches through the pre-gates that carry them ==")
for per in ("fit", "read"):
    s = [x for x in pre if period(x) == per and x.get("res_E2_first_h15_10") is not None]
    print(f"  {per} n {len(s)}: E1 first h15 {mean([x['res_E1_first_h15_10'] for x in s]):+.1%}, E1 last {mean([x.get('res_E1_last_h15_10', float('nan')) for x in s]):+.1%}, E2 first h15 {mean([x['res_E2_first_h15_10'] for x in s]):+.1%}, E2 last {mean([x.get('res_E2_last_h15_10', float('nan')) for x in s]):+.1%}")
