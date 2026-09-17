"""Needs ALCH=<alchemy key> in the environment and data/derived/engine_scores_0910_0916.txt (the T lines) next to the caches.
the six real Sep 11 trades from their receipts: ETH in, ETH out, gas, landing block relative to the creation block, hold
length; against the chain replay's prediction for the same launch (entry 0.3 s into second two, hold 5 s, +50% take-profit)"""
import json, os, sys, urllib.request, pickle, statistics as st
os.chdir("/tmp/claude-0/-home-user-fomo-memebot/a7a59693-7c2d-5b6c-b7df-e43fdbe7d612/scratchpad")
sys.path.insert(0, "/home/user/fomo-memebot/src/analysis"); import risk_harness as RH
exec(open("/home/user/fomo-memebot/src/analysis/indep_replay.py").read().split("recs = []")[0])
PX = RH.PX; RPC = "https://robinhood-mainnet.g.alchemy.com/v2/" + os.environ["ALCH"]
eng = open("/home/user/fomo-memebot/src/strategy/sniper_engine.py").read()
BUY = eng.split('BUY_EV = "')[1].split('"')[0]; SELL = eng.split('SELL_EV = "')[1].split('"')[0]; FACTORY = "0x" + eng.split('FACTORY = bytes.fromhex("')[1].split('"')[0]
def rpc(m, p):
    q = json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(RPC, q, {"content-type": "application/json"}), timeout=60).read())["result"]
trades = [l.split() for l in open("engine_scores.txt") if l.startswith("T ")]
by_curve = {cv: (k, L, f) for k in data for cv, (L, f) in data[k].items()}
print(f"{'trade':6s} {'curve':12s} {'in ETH':>8s} {'out ETH':>8s} {'gas $':>6s} {'REAL':>8s} {'replay':>8s} {'indep':>8s}  {'land s':>6s} {'hold s':>6s}  note")
reals, reps, inds = [], [], []
for t in trades:
    when, cv, tokens, held, exitwhy, bh, sh = t[1] + " " + t[2], t[3].lower(), float(t[4]), float(t[5]), t[6], t[7], t[8]
    rb = rpc("eth_getTransactionReceipt", [bh]); rs = rpc("eth_getTransactionReceipt", [sh]); tb = rpc("eth_getTransactionByHash", [bh])
    eth_in = int(tb["value"], 16) / 1e18
    gas = (int(rb["gasUsed"], 16) * int(rb["effectiveGasPrice"], 16) + int(rs["gasUsed"], 16) * int(rs["effectiveGasPrice"], 16)) / 1e18
    sell_logs = [l for l in rs["logs"] if l["topics"][0] == SELL and l["address"].lower() == cv]
    buy_logs = [l for l in rb["logs"] if l["topics"][0] == BUY and l["address"].lower() == cv]
    if not sell_logs or not buy_logs:
        print(f"{when[6:]} {cv[:12]}  receipt without the curve's event: buy status {rb['status']} sell status {rs['status']}"); continue
    w = [int(sell_logs[0]["data"][2:][i:i + 64], 16) / 1e18 for i in range(0, len(sell_logs[0]["data"]) - 2, 64)]
    eth_out = w[1]                                                     # quoteOut (net), as load_exact reads it
    tk_bought = int(buy_logs[0]["data"][2:][64:128], 16) / 1e18
    real = (eth_out - eth_in - gas) / eth_in
    bb, sb = int(rb["blockNumber"], 16), int(rs["blockNumber"], 16)
    # the creation block: the factory's log naming this curve, within 400 blocks before the buy
    cl = rpc("eth_getLogs", [{"fromBlock": hex(bb - 400), "toBlock": hex(bb), "address": FACTORY, "topics": [None, None, "0x" + "0" * 24 + cv[2:]]}])
    cb = int(cl[0]["blockNumber"], 16) if cl else None
    land = (bb - cb) / 10 if cb else None; hold = (sb - bb) / 10
    note = ""
    if cv in by_curve:
        k, L, f = by_curve[cv]; x = RH.replay(L, eth_in, hold=5.0, tp=0.5); rep = (x[0] * PX - 0.10) / (x[1] * PX) if x[1] > 1e-6 else float("nan")
        ind = sim(L, "E2", stake_usd=eth_in * PX)["roi"]; g = feats(L)
        note = "clean" if (g["out1"] == 0 and not (g["rival_lag"] is not None and g["rival_lag"] < 0.3)) else f"crowded (out1 {g['out1']}, rival lag {g['rival_lag'] if g['rival_lag'] is None else round(g['rival_lag'], 2)})"
        reals.append(real); reps.append(rep); inds.append(ind)
    else:
        rep = ind = float("nan"); note = "not in the replay windows"
    print(f"{when[6:]} {cv[:12]} {eth_in:8.5f} {eth_out:8.5f} {gas*PX:6.3f} {100*real:+7.1f}% {100*rep:+7.1f}% {100*ind:+7.1f}%  {land if land is None else '%.1f' % land:>6s} {hold:6.1f}  {note}")
print(f"\nmatched {len(reals)}: REAL mean {100*st.mean(reals):+.1f}%  replay {100*st.mean(reps):+.1f}%  independent {100*st.mean(inds):+.1f}%;  real minus replay per trade: " + ", ".join(f"{100*(a-b):+.1f}" for a, b in zip(reals, reps)) + " pts")
print("real money: %+.2f $ on %d trades" % (sum(r * 25 for r in reals), len(reals)))
