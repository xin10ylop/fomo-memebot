"""crowd_signal.py: is the seat-block crowd visible BEFORE the tick? Bots that want a launch fire at it during the creation
second and their shots revert in those blocks; those blocks reach the feed before the seat's second begins. For every
launch of the tables' file: the distinct wallets with a transaction aimed at the curve (to the curve, or the curve's
address inside the calldata, as with a relay) in the creation second's blocks, by block offset; the seat block's crowd;
how the index-1 bots send (one transaction or a burst). Public RPC, full blocks.

    python3 src/analysis/crowd_signal.py data/derived/live_vs_table/launches_141_creators.json [out.json]"""
import json, urllib.request, time, sys, collections, statistics as st
RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 curl/8"}
BOT = "0x6c56103c6af4891be46cb3666c1fa354cc79eaca"; US = {"0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}
def call(m, p):
    for i in range(6):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(), headers=H), timeout=60)); time.sleep(0.22)
            if "error" in r: raise RuntimeError(r["error"])
            return r["result"]
        except Exception as e:
            if i == 5: raise
            time.sleep(2 * (i + 1))
L = json.load(open(sys.argv[1])); out = sys.argv[2] if len(sys.argv) > 2 else "data/derived/live_vs_table/crowd_signal.json"; res = []
for n, l in enumerate(L):
    cv = l["cv"].lower(); b0 = l["b0"]; k = l["same_second_blocks"]; bE1 = b0 + k + 1
    named = set(w.lower() for w in l.get("named", [])) | {(l.get("creator") or "").lower()}
    per_block = []; bot_txs = []; attackers_cum = set(); cum = []
    for off in range(0, k + 2):                                            # the creation second's blocks and the seat block
        blk = call("eth_getBlockByNumber", [hex(b0 + off), True]); att = set()
        for t in blk["transactions"]:
            fr = t["from"].lower(); to = (t.get("to") or "").lower(); aimed = to == cv or cv[2:] in t.get("input", "")
            if aimed and fr not in named and fr not in US: att.add(fr)
            if fr == BOT or to == BOT: bot_txs.append((off, int(t["transactionIndex"], 16), aimed))
        if off <= k: attackers_cum |= att; cum.append(len(attackers_cum))
        per_block.append(sorted(att))
    res.append({"cv": cv, "b0": b0, "k": k, "hour": l["hour"], "attackers_by_block": cum, "attackers_creation_second": len(attackers_cum), "seat_block_attackers": len(per_block[-1]),
                "e1_buyers": len(l["e1_block_buyers"]), "e1_eth": l["e1_block_eth"], "bot_in_seat": BOT in l["e1_block_buyers"], "bot_txs": bot_txs, "first": l["res"]["E1_first_h15_250"][0], "last": l["res"]["E1_last_h15_250"][0], "bundle_eth": l["bundle_eth"]})
    if n % 10 == 0: print(n, cv[:10], "blocks", k + 2, "attackers by block", cum, "seat crowd", len(l["e1_block_buyers"]), f"{l['e1_block_eth']:.2f} ETH", "bot txs", len(bot_txs), flush=True)
json.dump(res, open(out, "w"), indent=0)
def at(r, j): return r["attackers_by_block"][min(j, len(r["attackers_by_block"]) - 1)] if r["attackers_by_block"] else 0
print("\n=== distinct attackers seen by creation-second block 5 (about 0.4 s before the tick) vs the seat block's crowd")
for lo, hi in ((0, 0), (1, 1), (2, 3), (4, 6), (7, 99)):
    g = [r for r in res if lo <= at(r, 5) <= hi]
    if g: print(f"attackers {lo}-{hi}: n={len(g):3d}  seat buyers mean {st.mean(r['e1_buyers'] for r in g):.1f}  seat ETH mean {st.mean(r['e1_eth'] for r in g):.3f}  bot present {sum(r['bot_in_seat'] for r in g)/len(g):.0%}  FIRST {st.mean(r['first'] for r in g):+.1%}  LAST {st.mean(r['last'] for r in g):+.1%}  win(first) {sum(r['first']>0 for r in g)/len(g):.0%}")
print("\n=== the bot's sending pattern on its launches (block offset, tx index, aimed at the curve):")
for r in res:
    if r["bot_in_seat"]: print("  ", r["cv"][:10], "k", r["k"], r["bot_txs"][:12])
