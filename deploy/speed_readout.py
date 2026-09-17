"""Step 2 readout for the creation-second seat dry run (runbook 5d): every trade_decision since the last engine start with its
timing fields, the gate and skip tallies, the paper scores (the scorer assumes a 0.3 s landing), the feed boundary and the
sender RTT. Rotation-safe: reads engine.jsonl.1 then engine.jsonl. Usage: sudo python3 speed_readout.py [/var/log/sniper/engine.jsonl]"""
import json, os, statistics as st, collections, time, sys
P = sys.argv[1] if len(sys.argv) > 1 else "/var/log/sniper/engine.jsonl"
ev = []
for f in (P + ".1", P):
    if os.path.exists(f):
        for line in open(f, errors="replace"):
            try: ev.append(json.loads(line))
            except Exception: pass
starts = [i for i, e in enumerate(ev) if e.get("ev") == "start"]
if not starts: print("no start line found"); raise SystemExit
ev = ev[starts[-1]:]; s0 = ev[0]; now = time.time(); hrs = (now - s0["t"]) / 3600
u = lambda t: time.strftime("%m-%d %H:%M:%S", time.gmtime(t))
print(f"engine {s0.get('version')} seat {s0.get('seat')} e0_outsider {s0.get('e0_outsider')} dry_run {s0.get('dry_run')} hold {s0.get('hold')} tp {s0.get('take_profit')} tiers {s0.get('tier_min_bps')}-{s0.get('tier_max_bps')} started {u(s0['t'])} UTC, running {hrs:.2f} h")
c = collections.Counter(e["ev"] for e in ev)
print(f"creations {c['creation']} ({c['creation']/max(hrs,1e-9):.1f}/h)  skip {c['skip']}  eligible_not_traded {c['eligible_not_traded']}  trade_decision {c['trade_decision']}  trade_done {c['trade_done']}  score {c['score']}  error {c['error']}  feed_stall {c['feed_stall']}  alarm {c['alarm']}")
tiers = collections.Counter(e.get("tax_bps") for e in ev if e["ev"] == "creation")
print("creation tax_bps seen:", dict(sorted(tiers.items(), key=lambda kv: (kv[0] is None, kv[0]))))
g = collections.Counter()
for e in ev:
    if e["ev"] == "eligible_not_traded":
        for r in e.get("gates", []): g[r.split(" (")[0][:60]] += 1
print("gate reasons:", dict(g.most_common(12)))
sk = collections.Counter()
for e in ev:
    if e["ev"] == "skip":
        w = e.get("why"); w = w if isinstance(w, str) else "; ".join(map(str, w))
        sk[w[:70]] += 1
print("skip reasons:", dict(sk.most_common(8)))
td = [e for e in ev if e["ev"] == "trade_decision"]
print(f"\ntrade decisions ({len(td)}): time UTC | resolve_ms | sent_ms (creation seen -> send) | flip_to_send_ms (creation second's first block -> send) | src | tax_bps | team_share | wallets | bundle_eth | blocks_to_seat | stake")
for e in td:
    print(f"  {u(e['t'])} | {e.get('resolve_ms'):>5} | {e.get('sent_ms'):>5} | {str(e.get('seat_flip_to_send_ms')):>7} | {str(e.get('resolve_src'))[:8]:8s} | {str(e.get('tax_bps')):>4} | {e.get('team_share')} | {e.get('bundle_wallets')} | {e.get('bundle_eth')} | {e.get('blocks_to_seat')} | ${e.get('stake_usd')}")
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None
for k in ("resolve_ms", "sent_ms", "seat_flip_to_send_ms"):
    xs = [e[k] for e in td if isinstance(e.get(k), (int, float))]
    if xs: print(f"{k:22s}: n {len(xs)} median {st.median(xs):.0f} p75 {q(xs,0.75):.0f} p90 {q(xs,0.9):.0f} max {max(xs):.0f}")
sc = {e["curve"]: e for e in ev if e["ev"] == "score" and "roi" in e}
traded = [sc[e["curve"]] for e in td if e["curve"] in sc]
if traded:
    rs = [x["roi"] for x in traded]; pn = [x["pnl_usd"] for x in traded]
    print(f"\npaper scores on the seats taken (scorer assumes a 0.3 s landing): n {len(rs)} mean roi {100*st.mean(rs):+.1f}% median {100*st.median(rs):+.1f}% wins {sum(r>0 for r in rs)} losses {sum(r<=0 for r in rs)} pnl ${sum(pn):+.2f} worst {100*min(rs):+.1f}% best {100*max(rs):+.1f}%")
    for x in traded: print(f"  {u(x['t'])} roi {100*x['roi']:+6.1f}% pnl ${x['pnl_usd']:+6.2f} cost ${x['cost_usd']} tier {x.get('tier')} t_in {x.get('t_in_s')} rolling_mean {x.get('rolling_mean')} switch_on {x.get('switch_on')}")
un = [e for e in td if e["curve"] not in sc]
if un: print(f"decisions without a score yet: {len(un)}")
b = [e for e in ev if e["ev"] == "boundary"]
if b: print(f"\nboundary (feed's second boundary on our clock): theta_ms {b[-1].get('theta_ms')} confidence {b[-1].get('confidence')} bracket_width_ms {b[-1].get('bracket_width_ms')} samples {b[-1].get('samples')}")
r = [e for e in ev if e["ev"] == "sender_rtt"]
if r: print("sender rtt:", [(x.get("host"), x.get("warm_rtt_ms"), x.get("ok")) for x in r[-1].get("endpoints", [])])
fl = [e for e in ev if e["ev"] == "flow"]
if fl: print(f"flow: creations_seen {fl[-1].get('creations_seen')} rule_passing_last_6h {fl[-1].get('rule_passing_last_6h')} silent_min {fl[-1].get('silent_min')} wallet_eth {fl[-1].get('wallet_eth')} bankroll {fl[-1].get('bankroll_usd')}")
er = collections.Counter((e.get("stage"), str(e.get("err"))[:50]) for e in ev if e["ev"] == "error")
if er: print("errors:", er.most_common(5))
