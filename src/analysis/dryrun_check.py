"""dryrun_check.py: is the dry run doing what the tables assume? One screen, from the engine's log.

    python3 src/analysis/dryrun_check.py /var/log/sniper/engine.jsonl

Reads every event, and prints: how long it ran and what it saw; every would-be trade with its timings (the send must be
about 300 ms after the seat's second opened, the wake-up under a millisecond, the resolution under 1500 ms and from the
feed); whether the feed's gate readings agreed with the chain's; the scores and the paper bankroll; errors, alarms and
feed trouble; the latest demand and crowding readouts; and a verdict per check."""
import sys, json, statistics as st, collections, time


def med(v):
    return st.median(v) if v else None


def main(path):
    evs = []
    for line in open(path):
        try:
            evs.append(json.loads(line))
        except Exception:
            pass
    if not evs:
        print("empty log"); return
    if "--all" not in sys.argv:                                              # by default: only what the current build did (since the last start)
        last = max((i for i, e in enumerate(evs) if e.get("ev") == "start"), default=0); evs = evs[last:]
    by = collections.defaultdict(list)
    for e in evs:
        by[e.get("ev")].append(e)
    t0 = evs[0]["t"]; t1 = evs[-1]["t"]; hours = (t1 - t0) / 3600
    starts = by["start"]; last_start = starts[-1] if starts else {}
    print(f"=== {path}: {hours:.1f} h since the last start{' (whole file)' if '--all' in sys.argv else ''}, {len(starts)} start(s), engine {last_start.get('version')}, seat {last_start.get('seat')}, dry_run {last_start.get('dry_run')}, wallet {last_start.get('wallet')}")
    print(f"    creations {len(by['creation'])}, skipped {len(by['skip'])}, resolved from the feed {sum(1 for e in by['feed_resolution_ok'])}, mismatches {len(by['feed_resolution_mismatch'])}, "
          f"gated {len(by['eligible_not_traded'])}, would-be trades {len(by['trade_decision'])}, scored {sum(1 for e in by['score'] if 'roi' in e)}, outside the rule on the chain {sum(1 for e in by['score'] if e.get('result'))}")
    checks = []
    # 1) timings of the would-be trades
    td = by["trade_decision"]
    if td:
        print("\n--- would-be trades (E2: send 300 ms after the seat's second opens, wake under 1 ms, resolved from the feed)")
        print(f"{'time':8s} {'bundle':>6s} {'ETH':>5s} {'out1':>4s} {'out2':>4s} {'resolve':>7s} {'src':>4s} {'flip->send':>10s} {'wake':>6s} {'stake':>6s} {'px/creator':>10s}")
        for e in td:
            print(f"{time.strftime('%H:%M:%S', time.gmtime(e['t'])):8s} {e.get('bundle', 0):6d} {e.get('bundle_eth', 0):5.2f} {e.get('out1', 0):4d} {e.get('out2', 0):4d} {e.get('resolve_ms', 0):7d} {str(e.get('resolve_src'))[:4]:>4s} "
                  f"{(e.get('seat_flip_to_send_ms') if e.get('seat_flip_to_send_ms') is not None else float('nan')):10.1f} {e.get('wake_to_send_ms', 0):6.2f} {e.get('stake_usd', 0):6.0f} {e.get('price_vs_creator', 0):10.2f}")
        flips = [e["seat_flip_to_send_ms"] for e in td if e.get("seat_flip_to_send_ms") is not None]; wakes = [e.get("wake_to_send_ms", 0) for e in td]; res = [e.get("resolve_ms", 0) for e in td]
        ok_flip = flips and all(250 <= x <= 400 for x in flips); ok_wake = all(x < 1.0 for x in wakes); ok_res = all(x < 1500 for x in res)
        n_feed = sum(1 for e in td if e.get("resolve_src") == "feed"); ok_src = n_feed >= 0.8 * len(td) and ok_res   # the RPC path is a fallback: fine when rare and under the gate
        checks.append(("send 300 ms after the seat's second (250-400)", ok_flip, f"median {med(flips):.1f} ms, worst {max(flips) if flips else 0:.1f}" if flips else "no flip timing recorded"))
        checks.append(("wake-up under 1 ms", ok_wake, f"median {med(wakes):.2f} ms, worst {max(wakes):.2f}"))
        checks.append(("resolution under 1500 ms", ok_res, f"median {med(res):.0f} ms, worst {max(res)}"))
        checks.append(("resolved from the feed (RPC fallback under 20%)", ok_src, f"{n_feed} of {len(td)} from the feed"))
    else:
        checks.append(("would-be trades", False, "none yet: wait for a busy hour"))
    # 2) feed vs chain on the gates
    gc = [e for e in by["gate_check"] if e.get("src") == "feed"]           # only launches the feed resolved: the ones it could have traded
    if gc:
        blind = [e for e in gc if e["chain"].get("out1", 0) > 0 and e["feed"].get("out1", 0) == 0]          # the chain saw a rival the feed missed: the one that matters
        cautious = [e for e in gc if e["feed"].get("out1", 0) > 0 and e["chain"].get("out1", 0) == 0]       # the feed counted an attempt that never landed: a skipped trade, not a loss
        bundle_off = [e for e in gc if abs(e["feed"].get("bundle", 0) - e["chain"].get("bundle", 0)) > 1]
        print(f"\n--- feed against chain on {len(gc)} feed-resolved launches: rival missed by the feed {len(blind)}, rival counted that never landed {len(cautious)}, bundle count off by more than one {len(bundle_off)}")
        if blind:
            print(f"    missed e.g. feed {blind[0]['feed']} chain {blind[0]['chain']}")
        if bundle_off:
            hi = sum(1 for e in bundle_off if e["feed"].get("bundle", 0) > e["chain"].get("bundle", 0)); lo = len(bundle_off) - hi
            print(f"    bundle count: feed higher on {hi}, chain higher on {lo}; pairs (feed n/ETH vs chain n/ETH): " + ", ".join(f"{e['feed'].get('bundle')}/{e['feed'].get('bundle_eth')} vs {e['chain'].get('bundle')}/{e['chain'].get('bundle_eth')}" for e in bundle_off[:8]))
        checks.append(("feed misses no rival the chain saw (under 10%)", len(blind) <= 0.1 * len(gc), f"{len(blind)} of {len(gc)}"))
        checks.append(("feed's bundle count matches the chain (under 10% off)", len(bundle_off) <= 0.1 * len(gc), f"{len(bundle_off)} of {len(gc)} off by more than one"))
        if cautious:
            checks.append(("rivals counted that never landed (skipped trades)", None, f"{len(cautious)} of {len(gc)}: engine 4.3 learns these senders after three misses; not a loss"))
    rv = by["rival"]
    if rv:
        senders = collections.Counter(e.get("sender") for e in rv); learned = [e.get("sender") for e in by["reverter_learned"]]
        print(f"--- rivals counted: {len(rv)} ({sum(1 for e in rv if e.get('ignored'))} ignored as learned reverters); most frequent senders: " + ", ".join(f"{k[:10]} x{v}" for k, v in senders.most_common(4)) + (f"; learned reverters {[x[:10] for x in learned]}" if learned else ""))
    checks.append(("no wrong-curve resolutions", len(by["feed_resolution_mismatch"]) == 0, f"{len(by['feed_resolution_mismatch'])} mismatches"))
    # 3) scores and the paper bankroll
    sc = [e for e in by["score"] if "roi" in e]
    if sc:
        rois = [e["roi"] for e in sc]; traded = [e for e in sc if e.get("traded_dry_run")]
        print(f"\n--- scores: {len(sc)} rule-passing launches, mean {100*st.mean(rois):+.1f}% a trade, median {100*st.median(rois):+.1f}%, share below -40% {100*sum(1 for r in rois if r < -0.4)/len(rois):.0f}%, "
              f"switch on at the end: {sc[-1].get('switch_on')}; paper trades {len(traded)}, bankroll {sc[0].get('bankroll')} -> {sc[-1].get('bankroll')}")
        if len(rois) >= 20:
            checks.append(("mean score above +3% (gas is covered)", st.mean(rois) > 0.03, f"{100*st.mean(rois):+.1f}% over {len(rois)}"))
        else:
            checks.append(("mean score above +3% (gas is covered)", None, f"{100*st.mean(rois):+.1f}% over {len(rois)}: fewer than 20, too few to judge"))
    # 4) gates that stopped trades
    gates = collections.Counter()
    for e in by["eligible_not_traded"]:
        for g in e.get("gates", []):
            gates[g.split(" ")[0] + " " + " ".join(g.split(" ")[1:4])] += 1
    if gates:
        print("\n--- why eligible launches were not traded: " + ", ".join(f"{k} x{v}" for k, v in gates.most_common(8)))
    # 5) trouble
    errs = collections.Counter(e.get("stage") for e in by["error"]); alarms = [e.get("what") for e in by["alarm"]]
    if by["error"]:
        print(f"    last error: {by['error'][-1].get('stage')}: {str(by['error'][-1].get('err'))[:160]}")
    reconnects = max(0, len(by["feed_connected"]) - len(starts))
    print(f"\n--- trouble: errors {dict(errs) if errs else 'none'}; alarms {alarms if alarms else 'none'}; feed errors {len(by['feed_error'])}, feed stalls {len(by['feed_stall'])}, reconnects {reconnects} (restarts {len(starts)})")
    checks.append(("no alarms", not alarms, "; ".join(alarms)[:120] if alarms else "none"))
    checks.append(("feed stable", len(by["feed_error"]) <= 3 * max(1, hours) and reconnects <= 3 * max(1, hours), f"{len(by['feed_error'])} feed errors, {reconnects} reconnects in {hours:.1f} h"))
    # 6) readouts
    fl = by["flow"]
    if fl:
        f = fl[-1]
        print(f"--- latest readouts: rule-passing last 6 h {f.get('rule_passing_last_6h')}, mean score last 60 {f.get('mean_score_last_60')}, demand (follow-on ETH, last 60) {f.get('follow_eth_last_60')}, crowding (second-one share, last 60) {f.get('out1_share_last_60')}, bankroll {f.get('bankroll_usd')}")
    rt = by["sender_rtt"]
    if rt:
        print("--- round trips: " + ", ".join(f"{x['host'].split('.')[0]} {x['warm_rtt_ms']} ms" for x in rt[-1]["endpoints"]))
    print("\n=== checks")
    for name, ok, detail in checks:
        print(f"   {'WAIT' if ok is None else ('PASS' if ok else 'FAIL'):4s}  {name:48s} {detail}")
    fails = [n for n, ok, _ in checks if ok is False]; waiting = [n for n, ok, _ in checks if ok is None and n.startswith("mean score")]
    if fails:
        print("verdict: not yet: " + "; ".join(fails))
    elif waiting or not sc:
        print(f"verdict: machine and gates fine; waiting for 20 scores ({len(sc) if sc else 0} so far) before judging the market")
    else:
        print("verdict: ready for the first five $25 trades" if st.mean(rois) > 0.03 else "verdict: machine fine, market not paying right now: do not fund yet")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sniper_engine.jsonl")
