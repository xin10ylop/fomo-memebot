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
        sk[w[:120]] += 1
print("skip reasons:", dict(sk.most_common(8)))
nt = [e for e in ev if e["ev"] == "eligible_not_traded"]
if nt:
    print("refused after the bundle was seen (last 6):")
    for e in nt[-6:]:
        print(f"  {u(e['t'])} {str(e.get('curve'))[:12]} src {e.get('resolve_src')} wait {e.get('bundle_wait_ms')} ms bundle {e.get('bundle')} / {e.get('bundle_eth')} ETH helper {e.get('bundle_helper')} tax {e.get('tax_bps')} | {'; '.join(str(g)[:70] for g in e.get('gates', []))}")
nb3 = [e for e in ev if e["ev"] == "skip" and "bundle not visible" in str(e.get("why")) and "(0 named" not in str(e.get("why")) and "(1 named" not in str(e.get("why"))]
if nb3:
    print("bundles that showed 2+ named transactions but missed the floor or the block cap (last 6):")
    for e in nb3[-6:]:
        print(f"  {u(e['t'])} named_wallets {e.get('named_wallets')} tax {e.get('tax_bps')} wait {e.get('wait_ms')} ms | {str(e.get('why'))[:140]}")
pre = [e for e in ev if e["ev"] in ("skip", "eligible_not_traded", "trade_decision") and not (e["ev"] == "skip" and "calldata" in str(e.get("why")))]
nb = [e for e in ev if e["ev"] == "skip" and "bundle not visible" in str(e.get("why"))]
if pre:
    print(f"calldata pre-check passed {len(pre)}: bundle visible on the feed in time {len(pre) - len(nb)}, not visible {len(nb)} ({100*(len(pre)-len(nb))/len(pre):.0f}% seen)")
    ws = sorted(e.get("wait_ms") for e in nb if isinstance(e.get("wait_ms"), (int, float)))
    if ws: print(f"  waits that expired: median {ws[len(ws)//2]} ms")
td = [e for e in ev if e["ev"] == "trade_decision"]
print(f"\ntrade decisions ({len(td)}): time UTC | bundle_wait_ms (creation seen -> bundle visible) | resolve_ms | sent_ms (creation seen -> send) | flip_to_send_ms (creation second's first block -> send) | src | tax_bps | team_share | wallets | bundle_eth | blocks_to_seat | helper buys | stake")
for e in td:
    print(f"  {u(e['t'])} | {str(e.get('bundle_wait_ms')):>5} | {e.get('resolve_ms'):>5} | {e.get('sent_ms'):>5} | {str(e.get('seat_flip_to_send_ms')):>7} | {str(e.get('resolve_src'))[:8]:8s} | {str(e.get('tax_bps')):>4} | {e.get('team_share')} | {e.get('bundle_wallets')} | {e.get('bundle_eth')} | {e.get('blocks_to_seat')} | h{e.get('bundle_helper')} | ${e.get('stake_usd')}")
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None
for k in ("bundle_wait_ms", "resolve_ms", "sent_ms", "seat_flip_to_send_ms"):
    xs = [e[k] for e in td if isinstance(e.get(k), (int, float))]
    if xs: print(f"{k:22s}: n {len(xs)} median {st.median(xs):.0f} p75 {q(xs,0.75):.0f} p90 {q(xs,0.9):.0f} max {max(xs):.0f}")
sc = {e["curve"]: e for e in ev if e["ev"] == "score" and "roi" in e}
lag_ok = (s0.get("provider_lag_ms") or 0) > 0 and s0.get("e0_allow_provider")      # 5.46: provider-path seats are scored with the measured lag, so they count
traded = [sc[e["curve"]] for e in td if e["curve"] in sc and (lag_ok or e.get("detect", "sequencer") != "provider")]
srcs = collections.Counter(e.get("resolve_src") for e in td)
if td: print("resolve source of the seats taken:", dict(srcs), "| detection path of the seats taken:", dict(collections.Counter(e.get("detect", "sequencer") for e in td)))
fc = [e for e in ev if e["ev"] == "feed_connected"]
if fc: print(f"detection now: {fc[-1].get('source', 'sequencer')} feed, connected {u(fc[-1]['t'])} UTC ({(time.time() - fc[-1]['t'])/60:.0f} min ago); connections this run: {dict(collections.Counter(e.get('source', 'sequencer') for e in fc))}")
prov = [e for e in td if e.get("detect") == "provider"]
if prov: print(f"!! {len(prov)} seat(s) taken on the provider path (the sequencer feed was down): " + (f"scored with the measured lag of {s0.get('provider_lag_ms')} ms, counted" if lag_ok else "their timing is not the seat's, excluded from the decision count"))
if traded:
    rs = [x["roi"] for x in traded]; pn = [x["pnl_usd"] for x in traded]; tb = [x.get("roi_table", x["roi"]) for x in traded]
    rv = sum(1 for x in traded if x.get("would_revert")); bf = sum(1 for x in traded if x.get("bot_first"))
    print(f"\npaper on the seats taken{'' if lag_ok else ' on the sequencer feed'}, scored at OUR estimated landing (5.44): n {len(rs)} mean {100*st.mean(rs):+.1f}% median {100*st.median(rs):+.1f}% wins {sum(r>0 for r in rs)} losses {sum(r<=0 for r in rs)} pnl ${sum(pn):+.2f} worst {100*min(rs):+.1f}% best {100*max(rs):+.1f}%")
    print(f"  would have reverted on our minimum output: {rv} of {len(rs)} | a bot ahead of the bundle: {bf} | the tables' 0.3 s assumption on the same seats: mean {100*st.mean(tb):+.1f}%")
    print(f"  sorted returns: {' '.join(f'{100*v:+.0f}' for v in sorted(rs))}")
    for x in traded: print(f"  {u(x['t'])} landing {100*x['roi']:+6.1f}% (table {100*x.get('roi_table', x['roi']):+6.1f}%) pnl ${x['pnl_usd']:+6.2f} t_land {x.get('t_landing', x.get('t_in_s'))} revert {x.get('would_revert')} got/min {x.get('got_vs_min')} bot_first {x.get('bot_first')} tier {x.get('tier')} rolling {x.get('rolling_mean')} switch {x.get('switch_on')}")
ref = {e["curve"]: e for e in ev if e["ev"] == "score" and "roi" not in e}
un = [e for e in td if e["curve"] not in sc]
if un: print(f"decisions without a numeric score: {len(un)}" + "".join(f"\n  {u(e['t'])} {e['curve'][:12]}: " + (str(ref[e["curve"]].get("result")) if e["curve"] in ref else "not scored yet") for e in un))
b = [e for e in ev if e["ev"] == "boundary"]
if b: print(f"\nboundary (feed's second boundary on our clock): theta_ms {b[-1].get('theta_ms')} confidence {b[-1].get('confidence')} bracket_width_ms {b[-1].get('bracket_width_ms')} samples {b[-1].get('samples')}")
r = [e for e in ev if e["ev"] == "sender_rtt"]
if r:
    hosts = collections.defaultdict(list)
    for e in r[-20:]:
        for x in e.get("endpoints", []):
            if isinstance(x.get("warm_rtt_ms"), (int, float)): hosts[x.get("host")].append(x["warm_rtt_ms"])
    print("sender rtt, last 20 samples:", {h: f"median {st.median(v):.0f} max {max(v):.0f} ms" for h, v in hosts.items()}, "| latest:", [(x.get("host"), x.get("warm_rtt_ms"), x.get("ok")) for x in r[-1].get("endpoints", [])])
fl = [e for e in ev if e["ev"] == "flow"]
if fl: print(f"flow: creations_seen {fl[-1].get('creations_seen')} rule_passing_last_6h {fl[-1].get('rule_passing_last_6h')} silent_min {fl[-1].get('silent_min')} wallet_eth {fl[-1].get('wallet_eth')} bankroll {fl[-1].get('bankroll_usd')}")
al = [e for e in ev if e["ev"] in ("alarm", "feed_stall", "feed_error", "note")]
for e in al[-5:]:
    print(f"{e['ev']} {u(e['t'])}: {str(e.get('what') or e.get('err') or e.get('note') or {k: v for k, v in e.items() if k not in ('ev', 't')})[:220]}")
if any(e["ev"] == "alarm" and "tax schedule" in str(e.get("what")) for e in al):
    print("!! the tax-schedule alarm has fired: the engine refuses every seat until it is restarted")
er = collections.Counter((e.get("stage"), str(e.get("err"))[:50]) for e in ev if e["ev"] == "error")
if er: print("errors:", er.most_common(5))
