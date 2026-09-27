"""market.py (edge_check/A): the market's activity from e1_multi's own outputs: Pons V2 creations per hour and qualifying
launches per hour, fit windows (data/derived/e1_sep1819, e1_sep2021, e1_sep23; Sep 22-23 has no e1m file with creations) vs
the recent windows (data/derived/e1_sep24). Overlapping recent files (sep25eve inside sep25eve2, sep26restart) are left out.
    python3 data/derived/edge_check/A/market.py"""
import json, glob, time, statistics as st
def rows(files):
    out = []
    for f in files:
        d = json.load(open(f)); h = (d["t_hi"] - d["t_lo"]) / 3600
        out.append((f.split("/")[-2] + "/" + f.split("/")[-1], time.strftime("%b %d %H:%M", time.gmtime(d["t_lo"])), h, d["creations"], len(d["launches"])))
    return out
fit = rows(sorted(glob.glob("data/derived/e1_sep1819/e1m_*.json") + glob.glob("data/derived/e1_sep2021/e1m_*.json") + glob.glob("data/derived/e1_sep23/e1m_*.json")))
rec = rows([f for f in sorted(glob.glob("data/derived/e1_sep24/e1m_*.json")) if not f.endswith(("sep25eve.json", "sep26restart.json"))])
for name, R in (("fit", fit), ("recent", rec)):
    for f, t, h, c, q in R: print(f"  {name:6s} {f:34s} from {t}  {h:5.2f} h  creations {c:5d} ({c/h:4.0f}/h)  qualifying {q:4d} ({q/h:4.1f}/h, {q/c:5.2%} of creations)")
    H = sum(h for _, _, h, _, _ in R); C = sum(c for _, _, _, c, _ in R); Q = sum(q for _, _, _, _, q in R)
    print(f"  {name}: {H:.1f} h, creations {C/H:.0f}/h, qualifying {Q/H:.2f}/h, {Q/C:.2%} of creations\n")
