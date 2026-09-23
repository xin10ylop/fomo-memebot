"""pnl_timeline.py: the cumulative P&L burst by burst from the chain (trades) and the race readout (bursts), with what each
launch had behind us. python3 src/analysis/pnl_timeline.py > data/derived/live_vs_table/pnl_timeline.txt"""
import json, re, time
E = 2570.0; GAS = 0.33
F = {r["cv"][:10]: r for r in json.load(open("data/derived/live_vs_table/sep17_20_fills.json"))}
A = {r["cv"][:10]: r for r in json.load(open("data/derived/live_vs_table/winners_anatomy.json"))}
bursts = []
for line in open("data/derived/live_vs_table/race_readout_sep18_20.txt"):
    m = re.match(r"(Sep \d\d \d\d:\d\d:\d\d) (0x[0-9a-f]{8})\s+(\S+ ms|-)\s+(\S+)\s+(\S+)\s+(\d+)/\s*(\d+)/(\d+)", line)
    if m: t, cv, _, fill_shot, idx, inc, rej, n = m.groups(); bursts.append((t, cv, fill_shot != "none"))
rows = [(time.strftime("%b %d %H:%M:%S", time.gmtime(r["T0"])), r["cv"][:10], True, r) for r in F.values() if time.strftime("%b %d %H:%M:%S", time.gmtime(r["T0"])) < "Sep 18 15:14"]
rows += [(t, cv, filled, F.get(cv)) for t, cv, filled in bursts]; rows.sort(key=lambda x: x[0]); cum = 0.0; peak = (-1e9, None)
print(f"{'when (UTC)':16s} {'launch':10s} {'trade $':>8s} {'gas $':>6s} {'cum $':>8s}  note")
for t, cv, filled, r in rows:
    trade = (r["net"] * E) if (filled and r and r["net"] is not None) else 0.0; gas = GAS * (1 + (r["fills"] - 1) * 0.3 if r and filled else 1); cum += trade - gas; a = A.get(cv, {})
    note = (f"{r['actual']:+.0%} {'x%d fills' % r['fills'] if r['fills'] > 1 else ''} ahead {r['ahead']} | seat behind {a.get('seat_behind_n','?')} ({a.get('seat_behind_eth',0):.2f} ETH), next 15 blocks {a.get('after_n','?')} buys {a.get('after_eth',0):.2f} ETH, price +60 {a.get('marks',{}).get('60',a.get('marks',{}).get(60,0)) or 0:+.0%}" if r and filled else "no fill (gas only)")
    if cum > peak[0]: peak = (cum, t)
    print(f"{t:16s} {cv:10s} {trade:+8.2f} {gas:6.2f} {cum:+8.2f}  {note}")
print(f"\npeak cumulative {peak[0]:+.2f} at {peak[1]}; final {cum:+.2f} (trades + $0.33 gas a burst)")
