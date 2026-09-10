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
    by = collections.defaultdict(list)
    for e in evs:
        by[e.get("ev")].append(e)
    t0 = evs[0]["t"]; t1 = evs[-1]["t"]; hours = (t1 - t0) / 3600
    starts = by["start"]; last_start = starts[-1] if starts else {}
    print(f"=== {path}: {hours:.1f} h of log, {len(starts)} start(s), engine {last_start.get('version')}, seat {last_start.get('seat')}, dry_run {last_start.get('dry_run')}, wallet {last_start.get('wallet')}")
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
        ok_flip = flips and all(250 <= x <= 400 for x in flips); ok_wake = all(x < 1.0 for x in wakes); ok_res = all(x < 1500 for x in res); ok_src = all(e.get("resolve_src") == "feed" for e in td)
        checks.append(("send 300 ms after the seat's second (250-400)", ok_flip, f"median {med(flips):.1f} ms, worst {max(flips) if flips else 0:.1f}" if flips else "no flip timing recorded"))
        checks.append(("wake-up under 1 ms", ok_wake, f"median {med(wakes):.2f} ms, worst {max(wakes):.2f}"))
        checks.append(("resolution under 1500 ms", ok_res, f"median {med(res):.0f} ms, worst {max(res)}"))
        checks.append(("resolved from the feed, not the RPC", ok_src, f"{sum(1 for e in td if e.get('resolve_src') == 'feed')} of {len(td)} from the feed"))
    else:
        checks.append(("would-be trades", False, "none yet: wait for a busy hour"))
    # 2) feed vs chain on the gates
    gc = by["gate_check"]
    if gc:
        agree = sum(1 for e in gc if e["feed"].get("bundle") == e["chain"].get("bundle") and (e["feed"].get("out1", 0) > 0) == (e["chain"].get("out1", 0) > 0))
        bad = [e for e in gc if not (e["feed"].get("bundle") == e["chain"].get("bundle") and (e["feed"].get("out1", 0) > 0) == (e["chain"].get("out1", 0) > 0))]
        checks.append(("feed and chain agree on the gates", agree >= 0.9 * len(gc), f"{agree} of {len(gc)} agree" + (f"; disagreements e.g. feed {bad[0]['feed']} chain {bad[0]['chain']}" if bad else "")))
    checks.append(("no wrong-curve resolutions", len(by["feed_resolution_mismatch"]) == 0, f"{len(by['feed_resolution_mismatch'])} mismatches"))
    # 3) scores and the paper bankroll
    sc = [e for e in by["score"] if "roi" in e]
    if sc:
        rois = [e["roi"] for e in sc]; traded = [e for e in sc if e.get("traded_dry_run")]
        print(f"\n--- scores: {len(sc)} rule-passing launches, mean {100*st.mean(rois):+.1f}% a trade, median {100*st.median(rois):+.1f}%, share below -40% {100*sum(1 for r in rois if r < -0.4)/len(rois):.0f}%, "
              f"switch on at the end: {sc[-1].get('switch_on')}; paper trades {len(traded)}, bankroll {sc[0].get('bankroll')} -> {sc[-1].get('bankroll')}")
        checks.append(("mean score above +3% (gas is covered)", st.mean(rois) > 0.03, f"{100*st.mean(rois):+.1f}% over {len(rois)}"))
    # 4) gates that stopped trades
    gates = collections.Counter()
    for e in by["eligible_not_traded"]:
        for g in e.get("gates", []):
            gates[g.split(" ")[0] + " " + " ".join(g.split(" ")[1:4])] += 1
    if gates:
        print("\n--- why eligible launches were not traded: " + ", ".join(f"{k} x{v}" for k, v in gates.most_common(8)))
    # 5) trouble
    errs = collections.Counter(e.get("stage") for e in by["error"]); alarms = [e.get("what") for e in by["alarm"]]
    print(f"\n--- trouble: errors {dict(errs) if errs else 'none'}; alarms {alarms if alarms else 'none'}; feed errors {len(by['feed_error'])}, feed stalls {len(by['feed_stall'])}, reconnects {len(by['feed_connected']) - 1}")
    checks.append(("no alarms", not alarms, "; ".join(alarms)[:120] if alarms else "none"))
    checks.append(("feed stable", len(by["feed_error"]) <= 3 * max(1, hours) and len(by["feed_connected"]) <= 3 * max(1, hours) + 1, f"{len(by['feed_error'])} feed errors, {len(by['feed_connected'])} connections in {hours:.1f} h"))
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
        print(f"   {'PASS' if ok else 'FAIL':4s}  {name:48s} {detail}")
    print("verdict: " + ("ready for the first five $25 trades" if all(ok for _, ok, _ in checks) else "not yet: fix the FAIL lines first (or wait, if the only FAIL is 'none yet')"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sniper_engine.jsonl")
