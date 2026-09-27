"""check.py (edge_check/H): the population's checks.  python3 data/derived/edge_check/H/check.py > data/derived/edge_check/H/check.txt
(a) fire counts against src/analysis/fleet_variants.py (fit 73/56, recent without sep27pm/eve 19/13);
(b) hold_grid behind1_15_h15 against G/curves r2[15] on the recent launches that have both (the proxy for the 24 tape-less launches);
(c) bundle_eth recomputed from the tapes (e1_multi's rule) against the launches files, every recent launch with both;
(d) the distinct hours of each period from the windows' T0 spans, and from the e1m files' t_lo..t_hi where they exist."""
import sys, os, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
P = load(cache=False)
print(f"population: {len(P)} launches; fit {sum(x['set']=='fit' for x in P)}, recent {sum(x['set']=='rec' for x in P)} "
      f"(of which sep27pm+sep27eve {sum(x['win'] in NOCURVE for x in P)}, not in G/curves)")
for s in ("fit", "rec"):
    S = [x for x in P if x["set"] == s]; S0 = [x for x in S if x["win"] not in NOCURVE]
    print(f"  {s}: tables fires {sum(x['fire_tab'] for x in S)}, engine fires {sum(x['fire_eng'] for x in S)};"
          f" without sep27pm/eve: tables {sum(x['fire_tab'] for x in S0)}, engine {sum(x['fire_eng'] for x in S0)}  (fleet_variants.txt: fit 73/56, recent 19/13)")
    for lab, key in (("tables", "fire_tab"), ("engine", "fire_eng")):
        F = [x for x in S0 if x[key]]
        print(f"     {lab} on the curves' launches: h11 {mean([x['r11'] for x in F]):+.1%}  h15 {mean([x['r15'] for x in F]):+.1%}")
C = curves(); d = []
for w in [w for w in REC if not w.startswith("gap") and w not in NOCURVE]:
    try: hg = hold_grid(w if w != "sep24paper" else "sep24paper")
    except FileNotFoundError: print("  no hold_grid for", w); continue
    for cv, h in hg.items():
        if cv in C and h.get("behind1_15_h15") is not None: d.append(abs(h["behind1_15_h15"] - C[cv]["r2"][15]))
print(f"\n(b) hold_grid behind1_15_h15 vs G r2[15]: {len(d)} launches, median |diff| {st.median(d):.5f}, max {max(d):.4f}, > 0.005: {sum(x > 0.005 for x in d)}")
N = [x for x in P if x["win"] in NOCURVE]
print(f"    the 24 tape-less launches: {sum(x['r11'] is not None for x in N)} flat (h11 = h15), {sum(x['r11'] is None for x in N)} not flat (no h11);"
      f" engine fires among them {sum(x['fire_eng'] for x in N)}, of which h11 known {sum(x['fire_eng'] and x['r11'] is not None for x in N)}")
b = [(x["bundle"], x["bundle_file"], x["cv"]) for x in P if x["bundle_src"] == "tape" and x["bundle_file"] is not None]
dd = [abs(a - f) for a, f, _ in b]
print(f"\n(c) bundle_eth from the tape vs launches file: {len(b)} launches, median |diff| {st.median(dd):.6f} ETH, max {max(dd):.4f}, > 0.01 ETH: {sum(x > 0.01 for x in dd)}")
for a, f, cv in sorted(b, key=lambda t: -abs(t[0] - t[1]))[:5]: print(f"    {cv[:10]} tape {a:.4f} file {f:.4f}")
print(f"    bundle source: tape {sum(x['bundle_src']=='tape' for x in P)}, launches file {sum(x['bundle_src']=='launches_file' for x in P)}")
print(f"\n(d) distinct hours from the windows' T0 spans: fit {spans(P, FIT):.2f} h (brief: 96 h), recent {spans(P, REC):.2f} h")
for w in FIT + REC: 
    S = [x['T0'] for x in P if x['win'] == w]
    if S: print(f"    {w:12s} {len(S):3d} launches  {hms(min(S))} - {hms(max(S))}  {(max(S)-min(S))/3600:5.2f} h")
iv = []
for w in REC:
    p = {"gapA": EC + "A/launches_gapA.json", "gapB": EC + "A/launches_gapB.json", "sep24paper": "data/derived/e1_sep24/e1m_sep24.json"}.get(w, f"data/derived/e1_sep24/e1m_{w}.json")
    if os.path.exists(p): J = json.load(open(p)); iv.append((J["t_lo"], J["t_hi"]))
iv.sort(); tot = 0; cur = None
for a, bb in iv:
    if cur is None or a > cur[1]: tot += (cur[1] - cur[0]) if cur else 0; cur = [a, bb]
    else: cur[1] = max(cur[1], bb)
tot += cur[1] - cur[0]
print(f"    recent from the e1m files' t_lo..t_hi (the scan windows, {len(iv)} files): {tot/3600:.2f} h")
