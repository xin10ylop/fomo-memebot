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
# like-for-like hours: qualifying launches and creations per covered hour, by UTC hour-of-day bucket (6-h bins)
import collections
def by_hour(files):
    cov = collections.Counter(); q = collections.Counter(); c = collections.Counter()
    for f in files:
        d = json.load(open(f)); t = d["t_lo"]
        while t < d["t_hi"]:
            step = min(d["t_hi"], (t // 3600 + 1) * 3600) - t; cov[time.gmtime(t).tm_hour // 6] += step / 3600; t += step
        for l in d["launches"]: q[l["hour"] // 6] += 1
        c_rate = d["creations"] / ((d["t_hi"] - d["t_lo"]) / 3600)
    return cov, q
ff = sorted(glob.glob("data/derived/e1_sep1819/e1m_*.json") + glob.glob("data/derived/e1_sep2021/e1m_*.json") + glob.glob("data/derived/e1_sep23/e1m_*.json"))
rf = [f for f in sorted(glob.glob("data/derived/e1_sep24/e1m_*.json")) if not f.endswith(("sep25eve.json", "sep26restart.json"))]
(fc, fq), (rc, rq) = by_hour(ff), by_hour(rf)
print("qualifying launches per covered hour, by UTC hour bucket (fit vs recent):")
for b in range(4):
    print(f"  {b*6:02d}-{b*6+5:02d} UTC: fit {fq[b]:4d} in {fc[b]:5.1f} h = {fq[b]/fc[b]:4.2f}/h   recent {rq[b]:4d} in {rc[b]:5.1f} h = {rq[b]/rc[b]:4.2f}/h")
exp = sum(fq[b] / fc[b] * rc[b] for b in range(4)) / sum(rc[b] for b in range(4))
print(f"  the fit's hourly rates on the recent windows' hours: {exp:.2f}/h expected, {sum(rq.values())/sum(rc.values()):.2f}/h observed")
