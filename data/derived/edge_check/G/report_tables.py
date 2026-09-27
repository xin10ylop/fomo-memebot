"""report_tables.py (edge_check/G): the report's markdown tables, read from sweep_all.csv (sweep.py) so nothing is transcribed by hand.
    python3 data/derived/edge_check/G/report_tables.py > data/derived/edge_check/G/report_tables.md"""
import csv, os
G = os.path.dirname(os.path.abspath(__file__)) + "/"
T = {}
for r in csv.DictReader(open(G + "sweep_all.csv")): T[(r["set"], int(r["h"]))] = r
f = lambda x: float(x)
HS = [1] + list(range(5, 61, 5)) + list(range(80, 301, 20)) + list(range(350, 601, 50)) + [700, 800, 900, 1000, 1100, 1200]
print("| h | fit mean | median | win | dead | sd | $/fire | lift | recent mean | median | win | dead | sd | $/fire | lift |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for h in HS:
    cells = []
    for s in ("fit", "rec"):
        r = T[(s, h)]; cells += [f"{f(r['mean']):+.1%}", f"{f(r['median']):+.1%}", f"{f(r['win']):.0%}", f"{f(r['dead']):.0%}", f"{f(r['sd']):.2f}", f"{f(r['usd_fire']):+.2f}", f"{f(r['lift'])*100:+.1f}"]
    print(f"| {h} | " + " | ".join(cells) + " |")
print()
HC = [1, 5, 10, 11, 15, 20, 30, 60, 150, 300, 600, 1200]
print("| set | fires/refused | " + " | ".join(f"h{h}" for h in HC) + " |")
print("|---|---|" + "---|" * len(HC))
for s in ["fit", "sep1819", "sep2021", "sep2223", "sep23day", "rec", "rec18", "Sep18-21", "Sep22-27"] + [f"Sep {d}" for d in range(18, 28)]:
    if (s, 1) not in T: continue
    print(f"| {s} | {T[(s,1)]['n']}/{T[(s,1)]['n_refused']} | " + " | ".join(f"{f(T[(s,h)]['mean']):+.1%} ({f(T[(s,h)]['lift'])*100:+.0f})" for h in HC) + " |")
