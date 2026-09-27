"""live_fills_holds.py: the September live fills (Sep 17-20, the trades the discovery came from) re-priced at EVERY hold from
1 to 60 blocks and at 100/150/300/600, from OUR real entry (block, position, ETH) on the chain's tape. Answers "what hold
did the real winners want" without any table: mean over the single fills, over the fills with a crowd ahead of us in the
block (the rule's ancestors) and over the 12 winners; the real sells for comparison.

    python3 src/analysis/live_fills_holds.py [--eth-usd 2570]"""
import json, sys, os, time, statistics as st, collections
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); sys.path.insert(0, "src/analysis")
import live_vs_table as lv
F = json.load(open("data/derived/live_vs_table/sep17_20_fills.json"))
HOLDS = list(range(1, 61)) + [80, 100, 150, 300, 600]
rows = []
for f in F:
    cv = f["cv"]
    # our Buy/Sell events on this curve (topics[2] = the buyer/seller: wallet or relay)
    ev = []
    for who in lv.OURS:
        ev += lv.call("eth_getLogs", [{"fromBlock": "0x0", "toBlock": "latest", "address": cv, "topics": [[lv.BUY, lv.SELL], None, lv.pad(who)]}])
    ours = sorted((lv.row_of(e) for e in ev), key=lambda r: (r["bn"], r["li"]))
    buys = [r for r in ours if r["k"] == "B"]; sells = [r for r in ours if r["k"] == "S"]
    if len(buys) != 1 or not sells: continue                                   # single fills with a sell, as 24.28
    b = buys[0]; blk = b["bn"]; sell_blk = sells[-1]["bn"]
    L = lv.launch(cv, blk, blk + 620)
    if L is None or L["tier"] is None: continue
    ahead = [r for r in L["rows"] if r["bn"] == blk and r["k"] == "B" and r["li"] < b["li"] and r["who"] not in lv.OURS]
    L["rows"] = [r for r in L["rows"] if r["who"] not in lv.OURS]               # our own events off the tape before modelling
    curve = {h: lv.model(L, b["eth"], blk, len(ahead), exit_block=blk + h) for h in HOLDS}
    actual = sells[-1]["eth"] / b["eth"] - 1
    rows.append({"cv": cv, "T0": L["T0"], "ahead": len(ahead), "actual": actual, "real_hold": sell_blk - blk, "curve": curve})
    print(f"  {time.strftime('%b %d %H:%M', time.gmtime(L['T0']))} {cv[:10]} ahead {len(ahead)} real hold {sell_blk - blk:3d} actual {actual:+.1%} | h9 {curve[9]:+.1%} h11 {curve[11]:+.1%} h15 {curve[15]:+.1%} h30 {curve[30]:+.1%} h300 {curve[300]:+.1%}", flush=True)
json.dump(rows, open("data/derived/live_vs_table/live_fills_holds.json", "w"))
def line(name, rs):
    if not rs: return
    print(f"\n{name}: {len(rs)} fills, real holds {min(r['real_hold'] for r in rs)}-{max(r['real_hold'] for r in rs)} blocks, real result mean {st.mean(r['actual'] for r in rs):+.1%}")
    print("  hold:   " + " ".join(f"{h:>6d}" for h in HOLDS if h <= 30 or h in (40, 50, 60, 100, 150, 300, 600)))
    print("  mean:   " + " ".join(f"{st.mean(r['curve'][h] for r in rs):+6.1%}" for h in HOLDS if h <= 30 or h in (40, 50, 60, 100, 150, 300, 600)))
    print("  win:    " + " ".join(f"{sum(r['curve'][h] > 0 for r in rs)/len(rs):6.0%}" for h in HOLDS if h <= 30 or h in (40, 50, 60, 100, 150, 300, 600)))
    best = max(HOLDS, key=lambda h: st.mean(r["curve"][h] for r in rs)); m = st.mean(r["curve"][best] for r in rs)
    se = st.pstdev([r["curve"][best] for r in rs]) / max(1, len(rs)) ** 0.5
    plateau = [h for h in HOLDS if st.mean(r["curve"][h] for r in rs) >= m - se]
    print(f"  best hold {best} at {m:+.1%}; within one standard error: blocks {min(plateau)}-{max(plateau)}")
line("all single fills", rows)
line("fills with a crowd ahead of us in the block (the rule's ancestors)", [r for r in rows if r["ahead"] >= 1])
line("fills with nobody ahead", [r for r in rows if r["ahead"] == 0])
line("the winners (real result > +5%)", [r for r in rows if r["actual"] > 0.05])
