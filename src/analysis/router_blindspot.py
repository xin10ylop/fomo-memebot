"""how many crowded launches look clean to the feed: for every bundled launch with an outsider buy in second one (chain), fetch
that buy's transaction and classify it: direct call to the curve, router call naming the curve in its calldata (both visible to
the feed decoder), or a router call that names neither (invisible: the engine would trade the launch as clean)"""
import sys, json, glob, collections, urllib.request, time
sys.path.insert(0, '/home/user/fomo-memebot/src/analysis'); import risk_harness as RH
ALCH = "https://robinhood-mainnet.g.alchemy.com/v2/alch_MHqmX5rCT1l0U_flVcJoG"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
def call(m, p, tries=4):
    for i in range(tries):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(ALCH, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(), headers=H), timeout=60))["result"]
        except Exception: time.sleep(1 + i)
    return None
wins = [w for w in sys.argv[1:]] or ["2026-09-11_15-22", "2026-09-10_18-24"]
data = RH.load(); data.update(RH.load_new())
BUY = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"
for win in wins:
    day, hh = win.rsplit("_", 1); k = (day, hh)
    if k not in data: print("no cache for", k); continue
    txs = collections.defaultdict(list)
    for line in open(f"rh/v2curve_{win}.jsonl"):
        b, li, tx, addr, t0, d = json.loads(line)
        if t0 == BUY[:10]: txs[addr].append((b, li, tx, d))
    cls = collections.Counter(); routers = collections.Counter(); n = 0; hidden_launches = 0
    for cv, (L, f) in data[k].items():
        if f["out1_n"] == 0: continue
        tier = L["tier"]; b0 = L["rows"][0]
        # second-one outsider buys: the rows with the 6.18% surcharge; match them to transactions by order among this curve's buys
        buys = sorted(txs.get(cv, []))
        brow = [r for r in L["rows"] if r[1] == "B"]
        if len(buys) != len(brow): cls["unmatched"] += 1; continue
        seen_visible = False; seen_any = False; kinds = []
        for r, (b, li, tx, d) in zip(brow, buys):
            if not (0.05 <= r[5] - tier <= 0.075): continue
            seen_any = True; t = call("eth_getTransactionByHash", [tx])
            if t is None: kinds.append("?"); continue
            if t["to"].lower() == cv: kinds.append("direct")
            elif cv[2:] in t["input"].lower(): kinds.append("router naming curve")
            else: kinds.append("router, curve not named"); routers[t["to"][:10] + " " + t["input"][:10]] += 1
        if not seen_any: continue
        n += 1
        for x in kinds: cls[x] += 1
        if all(x == "router, curve not named" for x in kinds): hidden_launches += 1
    print(f"{win}: crowded launches checked {n}; second-one buys by kind {dict(cls)}; launches where EVERY second-one buy is invisible to the feed: {hidden_launches} ({100*hidden_launches/max(n,1):.0f}%)")
    print("   invisible routers:", dict(routers.most_common(6)))
