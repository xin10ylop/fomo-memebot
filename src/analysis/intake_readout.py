"""intake_readout.py: for every live burst in the engine's logs, the sequencer's intake delay against the crowd's size.
Per burst: when, the curve, shots sent, the sequencer's reply time to the shots (median / max ms), where they landed
(filled? the fill shot; blocks after the first shot's block), the feed's flip minus the first shot, and the crowd: the
rival shots the feed showed aimed at that curve. Reads plain and rotated logs.
    sudo python3 src/analysis/intake_readout.py /var/log/sniper/engine.jsonl.7 /var/log/sniper/engine.jsonl.6 /var/log/sniper/engine.jsonl"""
import sys, json, gzip, time, statistics as st, collections
answers = {}; bursts = []; landings = {}; rivals = collections.Counter()
for f in sys.argv[1:]:
    op = gzip.open if f.endswith(".gz") else open
    with op(f, "rt", errors="replace") as fh:
        for line in fh:
            try: e = json.loads(line)
            except ValueError: continue
            ev = e.get("ev")
            if ev == "send_answers" and e.get("hash"):
                r = e.get("reply_ms") or []; answers[e["hash"]] = r[0][1] if r and isinstance(r[0], list) and len(r[0]) > 1 else None
            elif ev == "burst_shots": bursts.append(e)
            elif ev == "burst_landing": landings[e["curve"]] = e
            elif ev == "rival": rivals[e.get("curve")] += 1
print(f"{'when (UTC)':16s} {'curve':11s} {'shots':>5s} {'reply med':>9s} {'reply max':>9s} {'filled':>6s} {'fill shot':>9s} {'blocks late':>11s} {'flip-1st ms':>11s} {'rival shots':>11s}")
rows = []
for b in bursts:
    hs = [h for h in b.get("hashes", []) if h]; rep = [answers[h] for h in hs if answers.get(h) is not None]
    L = landings.get(b["curve"], {}); shots = L.get("shots", []); mined = [s for s in shots if s.get("block")]
    fill = next((i + 1 for i, s in enumerate(shots) if s.get("status") == "0x1"), None)
    late = (max(s["block"] for s in mined) - min(s["block"] for s in mined)) if len(mined) > 1 else None
    rows.append((b.get("t", 0), b["curve"], len(hs), rep, L.get("filled"), fill, late, L.get("flip_minus_first_shot_ms"), rivals.get(b["curve"], 0)))
for t, cv, n, rep, filled, fill, late, flip, riv in sorted(rows):
    print(f"{time.strftime('%b %d %H:%M:%S', time.gmtime(t)):16s} {cv[:10]:11s} {n:5d} {(f'{st.median(rep):8.0f}' if rep else '       -'):>9s} {(f'{max(rep):8.0f}' if rep else '       -'):>9s} {str(filled):>6s} {str(fill):>9s} {str(late):>11s} {str(flip):>11s} {riv:11d}")
ok = [r for r in rows if r[3]]
if ok:
    big = [r for r in ok if r[8] >= 300]; small = [r for r in ok if r[8] < 300]
    for name, grp in (("crowd < 300 rival shots", small), ("crowd >= 300 rival shots", big)):
        if grp: print(f"\n{name}: {len(grp)} bursts, sequencer reply median {st.median(st.median(r[3]) for r in grp):.0f} ms, max {max(max(r[3]) for r in grp):.0f} ms, filled {sum(1 for r in grp if r[4])}")
