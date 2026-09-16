"""paper_report.py: what the paper days say, from the engine's own log (including the rotated ones).

    /opt/sniper-venv/bin/python3 src/analysis/paper_report.py [/var/log/sniper/engine.jsonl]

For every UTC day and six-hour block since the paper run began: how many launches passed the rule, what our seat (E2)
would have earned on them, what the front seat (E1) would have earned on every team launch, how crowded the launches
were, how much ETH the buyers behind a clean seat brought, and how late the first rival bot landed in second one.
Then the three decisions of Sep 11: E2 back to live, E1 worth a machine, or the seat is over."""
import sys, os, gzip, json, glob, statistics as st, collections, datetime

BLOCKS = [(12, 18, "12-18"), (18, 24, "18-24"), (0, 6, "00-06"), (6, 12, "06-12")]


def read(path):
    """the log and its rotations, oldest first"""
    names = sorted(glob.glob(path + ".*"), key=lambda p: -int("".join(c for c in os.path.basename(p).split(".")[-2] if c.isdigit()) or 0)) + [path]
    for p in names:
        if not os.path.exists(p):
            continue
        op = gzip.open if p.endswith(".gz") else open
        try:
            with op(p, "rt", errors="replace") as f:
                for line in f:
                    try:
                        yield json.loads(line)
                    except Exception:
                        continue
        except OSError:
            continue


def day_of(t):
    return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%m-%d")


def block_of(t):
    h = datetime.datetime.fromtimestamp(t, datetime.timezone.utc).hour
    for a, b, name in BLOCKS:
        if a <= h < b:
            return name
    return "??"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/var/log/sniper/engine.jsonl"
    scores = []            # rule-passing launches: (t, roi, traded_paper, pnl_usd)
    e1 = []                # every scored team launch: (t, roi_e1)
    flows = []; starts = []; alarms = collections.Counter(); errors = collections.Counter()
    gates = collections.Counter(); rivals_chain = 0; creations = 0
    for e in read(path):
        ev = e.get("ev"); t = e.get("t")
        if ev == "start":
            starts.append((t, e.get("version"), e.get("dry_run")))
        elif ev == "creation":
            creations += 1
        elif ev == "score":
            if e.get("roi_e1") is not None:
                e1.append((t, e["roi_e1"]))
            if "roi" in e:
                scores.append((t, e["roi"], bool(e.get("traded_dry_run")), e.get("pnl_usd") or 0.0))
        elif ev == "flow":
            flows.append(e)
        elif ev == "eligible_not_traded":
            for g in e.get("gates", []):
                gates[g.split(" >")[0].split(" (")[0][:52] if not g[0].isdigit() else g.split(" ", 1)[1].split(" >")[0][:52]] += 1
        elif ev == "rival_chain":
            rivals_chain += 1
        elif ev == "alarm":
            alarms[str(e.get("what"))[:70]] += 1
        elif ev == "error":
            errors[str(e.get("stage")) + ": " + str(e.get("err"))[:60]] += 1
    if not scores and not e1:
        print("no scored launches in the log: is the engine running? (systemctl status sniper-engine)"); return
    t0 = min([s[0] for s in scores] + [x[0] for x in e1]); t1 = max([s[0] for s in scores] + [x[0] for x in e1])
    hrs = (t1 - t0) / 3600
    print(f"paper run: {datetime.datetime.fromtimestamp(t0, datetime.timezone.utc).strftime('%b %d %H:%M')} -> "
          f"{datetime.datetime.fromtimestamp(t1, datetime.timezone.utc).strftime('%b %d %H:%M')} UTC ({hrs:.0f} h, {hrs/24:.1f} days); "
          f"{creations:,} launches seen, {len(e1):,} team launches scored, {len(scores):,} passed the rule; restarts {len(starts)}"
          + (f"; versions {sorted({v for _, v, _ in starts if v})}" if starts else ""))
    if any(d is False for _, _, d in starts):
        print("  WARNING: the log contains a live start (dry_run false): some of this was real money")

    def line(label, rows, e1rows, fl):
        if not rows and not e1rows:
            return
        r = [x[1] for x in rows]; taken = [x for x in rows if x[2]]
        crowd = [f["out1_share_last_60"] for f in fl if f.get("out1_share_last_60") is not None]
        dem = [f["follow_eth_last_60"] for f in fl if f.get("follow_eth_last_60") is not None]
        race = [f["race_first_rival_ms_median"] for f in fl if f.get("race_first_rival_ms_median") is not None]
        pc = lambda v: f"{100*v:+.1f}%" if v is not None else "-"
        num = lambda v, f: (f % v) if v is not None else "-"
        print(f"{label:12s} {len(r):6d} {pc(st.mean(r) if r else None):>8s} {pc(st.median(r) if r else None):>8s} "
              f"{num(100*sum(1 for x in r if x < -0.4)/len(r) if r else None, '%.0f%%'):>6s} {len(taken):6d} {sum(x[3] for x in taken):+8.0f} "
              f"{len(e1rows):6d} {pc(st.mean(x[1] for x in e1rows) if e1rows else None):>8s} "
              f"{num(st.mean(crowd) if crowd else None, '%.2f'):>7s} {num(st.mean(dem) if dem else None, '%.3f'):>7s} {num(st.median(race) if race else None, '%.0f'):>8s}")

    hdr = (f"\n{'':12s} {'rule-passing launches (our E2 seat)':>39s} {'paper trades':>16s} {'E1 front':>15s} {'crowd':>7s} {'demand':>7s} {'race ms':>8s}\n"
           f"{'day UTC':12s} {'n':>6s} {'mean':>8s} {'median':>8s} {'<-40%':>6s} {'n':>6s} {'$':>8s} {'n':>6s} {'mean':>8s}")
    print(hdr)
    days = sorted({day_of(x[0]) for x in scores} | {day_of(x[0]) for x in e1})
    for d in days:
        line(d, [x for x in scores if day_of(x[0]) == d], [x for x in e1 if day_of(x[0]) == d], [f for f in flows if day_of(f["t"]) == d])
    line("ALL", scores, e1, flows)
    print(f"\n{'block UTC':12s} {'n':>6s} {'mean':>8s} {'median':>8s} {'<-40%':>6s} {'n':>6s} {'$':>8s} {'n':>6s} {'mean':>8s} {'crowd':>7s} {'demand':>7s} {'race ms':>8s}")
    for _, _, name in BLOCKS:
        line(name, [x for x in scores if block_of(x[0]) == name], [x for x in e1 if block_of(x[0]) == name], [f for f in flows if block_of(f["t"]) == name])

    last = flows[-1] if flows else {}
    races = [f["race_first_rival_ms_median"] for f in flows if f.get("race_first_rival_ms_median") is not None]
    firstblk = [f["race_first_block_share"] for f in flows if f.get("race_first_block_share") is not None]
    rp1h = [f.get("rule_passing_last_1h", 0) for f in flows if f.get("rule_passing_last_1h") is not None and 12 <= datetime.datetime.fromtimestamp(f["t"], datetime.timezone.utc).hour < 24]
    print(f"\nlatest readout: " + ", ".join(f"{k} {last.get(k)}" for k in ("rule_passing_last_1h", "out1_share_last_60", "follow_eth_last_60", "follow_eth_all_60", "mean_score_last_60", "mean_score_e1_last_60") if k in last))
    if gates:
        print("why launches were not traded: " + ", ".join(f"{k} x{v}" for k, v in gates.most_common(6)))
    print(f"chain-sourced rivals the feed did not see: {rivals_chain}")
    if alarms:
        print("ALARMS: " + ", ".join(f"{k} x{v}" for k, v in alarms.most_common(4)))
    if errors:
        print("errors: " + ", ".join(f"{k} x{v}" for k, v in errors.most_common(3)))

    # the three decisions of Sep 11
    avg = lambda xs: st.mean(xs) if xs else None
    med = lambda xs: st.median(xs) if xs else None
    e2_mean = avg([x[1] for x in scores]); e1_mean = avg([x[1] for x in e1])
    dem = avg([f["follow_eth_last_60"] for f in flows if f.get("follow_eth_last_60") is not None])
    clean_per_h = med(rp1h)
    print(f"\n{'test':58s} {'now':>10s} {'needed':>10s}  verdict")
    rows = [("E2: mean paper score over every rule-passing launch", None if e2_mean is None else 100 * e2_mean, "> +5%", lambda v: v > 5),
            ("E2: ETH the buyers bring behind a clean seat", dem, "> 0.30", lambda v: v > 0.30),
            ("E2: rule-passing launches an hour, 12-24 UTC", clean_per_h, ">= 10", lambda v: v >= 10),
            ("E1: mean paper score of the front on team launches", None if e1_mean is None else 100 * e1_mean, "> +5%", lambda v: v > 5),
            ("E1: first rival's lag after second one opens (ms)", med(races), "> 50", lambda v: v > 50),
            ("E1: share of first rivals inside the first block", avg(firstblk), "< 0.50", lambda v: v < 0.50)]
    verdicts = {}
    for name, val, need, ok in rows:
        state = "no data" if val is None else ("PASS" if ok(val) else "fail")
        verdicts[name[:2]] = verdicts.get(name[:2], []) + [state]
        print(f"{name:58s} {('%10.2f' % val) if val is not None else '         -':>10s} {need:>10s}  {state}")
    e2_ok = all(v == "PASS" for v in verdicts.get("E2", ["no data"]))
    e1_ok = all(v == "PASS" for v in verdicts.get("E1", ["no data"]))
    if any(v == "no data" for vs in verdicts.values() for v in vs):
        print("(a test with no data means the engine logged nothing for it: check it ran the whole four days)")
    print("\nDECISION: " + ("E2 goes back to live at $25 (set SEND_MODULE, restart, run live_check at five trades)" if e2_ok else
                            "E1 is worth the Ohio machine and a race test with $60; E2 stays in paper" if e1_ok else
                            "neither seat pays on these four days: withdraw the wallet to Phantom and keep the engine on paper as a watcher"))


if __name__ == "__main__":
    main()
