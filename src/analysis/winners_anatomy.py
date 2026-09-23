"""winners_anatomy.py: what did our profitable launches have that the losers did not, and what happened after we sold.

    python3 src/analysis/winners_anatomy.py

For every launch we filled (data/derived/live_vs_table/sep17_20_fills.json): the creation calldata (creator, named wallets,
the token's name and symbol), the wallets already firing at the curve in the creation second (the pre-tick crowd), the seat
block's buyers behind us, the buys in the 15 blocks after the seat (count, ETH, distinct wallets), the curve price at
+15/+30/+60/+150/+600 blocks against our entry, and whether the named wallets recur on other launches of the tables'
files (an operator). Public RPC."""
import json, urllib.request, time, sys, collections, statistics as st, re
sys.path.insert(0, "src/analysis"); from live_vs_table import launch, fold_buy, fold_sell, X0, Y0, OURS, call, V2F, pad, stamps
BUY = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; SELL = "0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"
R = json.load(open("data/derived/live_vs_table/sep17_20_fills.json")); E = 2570.0
tables = json.load(open("data/derived/live_vs_table/launches_141_creators.json")) + json.load(open("data/derived/live_vs_table/launches_175_sep2223.json"))
named_index = collections.defaultdict(set)
for l in tables:
    for w in l.get("named", []): named_index[w.lower()].add(l["cv"].lower())
first_of = {l["cv"].lower(): l["res"]["E1_first_h15_250"][0] for l in tables}
def strings(data):
    out = []
    for m in re.finditer(rb"[ -~]{3,}", data): 
        s = m.group().decode(); out.append(s)
    return out
rows = []
for r in R:
    if r["actual"] is None: continue
    cv = r["cv"]; L = launch(cv, r["T0"] and 0 or 0) if False else None
    cl = [x for x in call("eth_getLogs", [{"fromBlock": hex(int(r.get("b0", 0)) or 0), "toBlock": "latest", "address": V2F, "topics": [None, None, pad(cv)]}]) if len(x["topics"]) > 3] if r.get("b0") else None
    if cl is None:
        # find the creation from the first of our buys: search 400 blocks back from a block near T0 (we have T0 only): use the curve's earliest Buy event instead
        ev = call("eth_getLogs", [{"fromBlock": hex(66_000_000), "toBlock": "latest", "address": cv, "topics": [[BUY]]}])
        b_first = min(int(e["blockNumber"], 16) for e in ev)
        cl = [x for x in call("eth_getLogs", [{"fromBlock": hex(b_first - 5), "toBlock": hex(b_first), "address": V2F, "topics": [None, None, pad(cv)]}]) if len(x["topics"]) > 3]
    b0 = int(cl[0]["blockNumber"], 16); creator = ("0x" + cl[0]["topics"][3][-40:]).lower()
    tx = call("eth_getTransactionByHash", [cl[0]["transactionHash"]]); data = bytes.fromhex(tx["input"][2:]); words = [data[4 + 32 * i: 4 + 32 * (i + 1)] for i in range((len(data) - 4) // 32)]
    named = sorted({"0x" + w[12:].hex() for w in words if w[:12] == b"\0" * 12 and int.from_bytes(w[12:], "big") > 2 ** 100} - {creator})
    txt = [s for s in strings(data) if not s.startswith("http")][:3]; uri = next((s for s in strings(data) if s.startswith("http")), "")
    recur = {w: len(named_index[w]) for w in named if len(named_index[w]) > 1}
    ts = stamps(b0, b0 + 30); T0 = ts[b0]; k = next((n for n in range(b0 + 1, b0 + 30) if ts.get(n, 0) == T0 + 1), b0 + 10) - b0 - 1; bE1 = b0 + k + 1
    # pre-tick attackers in the creation second's blocks
    att = set(); crowd_blocks = []
    for off in range(0, k + 1):
        blk = call("eth_getBlockByNumber", [hex(b0 + off), True]); a = set()
        for t in blk["transactions"]:
            fr = t["from"].lower(); to = (t.get("to") or "").lower()
            if (to == cv or cv[2:] in t.get("input", "")) and fr not in named and fr != creator and fr not in OURS and to not in OURS: a.add(fr)   # our shooters send to the relay
        att |= a; crowd_blocks.append(len(att))
    # the tape to +600
    ev = call("eth_getLogs", [{"fromBlock": hex(b0), "toBlock": hex(b0 + 620), "address": cv, "topics": [[BUY, SELL]]}])
    tape = []
    for e in sorted(ev, key=lambda e: (int(e["blockNumber"], 16), int(e["logIndex"], 16))):
        d = e["data"][2:]; w = [int(d[i:i + 64], 16) / 1e18 for i in range(0, len(d), 64)]; kk = "B" if e["topics"][0] == BUY else "S"
        tape.append((int(e["blockNumber"], 16), kk, w[0] if kk == "B" else w[1], w[1] if kk == "B" else w[0], ("0x" + e["topics"][2][-40:]).lower() if len(e["topics"]) > 2 else None))
    ours = [t for t in tape if t[4] in OURS and t[1] == "B"]; b_in = ours[0][0] if ours else bE1
    X, Y = X0, Y0; p_in = None; marks = {}; after = []; seat_behind = []
    seen_ours = False
    for bn, kk, eth, tk, who in tape:
        if kk == "B":
            if 0 < tk < Y: X, Y = fold_buy(X, Y, tk)
        else: X, Y = fold_sell(X, Y, tk)
        if who in OURS and kk == "B" and not seen_ours: seen_ours = True; p_in = X / Y
        elif seen_ours and kk == "B" and who not in OURS:
            if bn == b_in: seat_behind.append((who, eth))
            elif bn <= b_in + 15: after.append((who, eth, bn - b_in))
        for h in (15, 30, 60, 150, 600):
            if seen_ours and bn <= b_in + h: marks[h] = X / Y
    p_now = X / Y
    row = {"when": time.strftime("%b %d %H:%M", time.gmtime(r["T0"])), "cv": cv, "actual": r["actual"], "first": r["first"], "fills": r["fills"], "ahead": r["ahead"], "creator": creator, "named": len(named), "recur": recur,
           "name": txt, "attackers": crowd_blocks, "seat_behind_n": len(seat_behind), "seat_behind_eth": sum(e for _, e in seat_behind), "after_n": len(after), "after_eth": sum(e for _, e, _ in after), "after_wallets": len({w for w, _, _ in after}),
           "after_bots": sum(1 for w, _, _ in after if w in named_index or w.startswith("0x6c56") ), "marks": {h: (m / p_in - 1) if p_in else None for h, m in marks.items()}, "end": (p_now / p_in - 1) if p_in else None, "tier_first": first_of.get(cv)}
    rows.append(row)
    print(f"{row['when']} {cv[:10]} actual {row['actual']:+5.0%} (first {row['first']:+4.0%}) ahead {row['ahead']} | named {row['named']} recur {len(recur)} | attackers by block {crowd_blocks} | seat behind {row['seat_behind_n']} ({row['seat_behind_eth']:.2f} ETH) | +15 blocks: {row['after_n']} buys {row['after_eth']:.2f} ETH {row['after_wallets']} wallets | price vs entry +15 {row['marks'].get(15, 0):+.0%} +60 {row['marks'].get(60, 0):+.0%} +600 {row['marks'].get(600, 0):+.0%} | {' / '.join(txt)}", flush=True)
json.dump(rows, open("data/derived/live_vs_table/winners_anatomy.json", "w"), indent=0)
W = [x for x in rows if x["actual"] > 0.05]; Lo = [x for x in rows if x["actual"] <= 0.05]
def m(rows, f): v = [f(x) for x in rows if f(x) is not None]; return st.mean(v) if v else float("nan")
print(f"\n=== winners (>5%) n={len(W)} vs the rest n={len(Lo)}")
for name, f in (("named wallets", lambda x: x["named"]), ("recurring named wallets", lambda x: len(x["recur"])), ("attackers by block 3", lambda x: x["attackers"][min(3, len(x['attackers'])-1)]), ("attackers at the last creation block", lambda x: x["attackers"][-1]),
                ("seat buys behind us", lambda x: x["seat_behind_n"]), ("ETH behind us in the seat block", lambda x: x["seat_behind_eth"]), ("buys in the next 15 blocks", lambda x: x["after_n"]), ("ETH in the next 15 blocks", lambda x: x["after_eth"]), ("distinct wallets next 15", lambda x: x["after_wallets"]),
                ("price +60 vs entry", lambda x: x["marks"].get(60)), ("price +600 vs entry", lambda x: x["marks"].get(600)), ("price now vs entry", lambda x: x["end"])):
    print(f"  {name:36s} winners {m(W, f):8.3f}   rest {m(Lo, f):8.3f}")
print("winners' hours:", sorted(x["when"][-5:] for x in W))
