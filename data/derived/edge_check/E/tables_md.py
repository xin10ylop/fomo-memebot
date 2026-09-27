"""tables_md.py (edge_check/E): the report's markdown tables from curves.csv (run curves.py first): the two periods side by side
at h = 1, 5..60 by 5, 80..300 by 20, 350..600 by 50, 700..1200 by 100; and every group at h = 9, 15, 60, 300, 600.
    python3 data/derived/edge_check/E/tables_md.py > data/derived/edge_check/E/tables_md.txt"""
import csv, os
R = {}
for r in csv.DictReader(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "curves.csv"))): R[(r["group"], int(r["h"]))] = {k: (float(v) if k not in ("group",) else v) for k, v in r.items()}
TAB = [1] + list(range(5, 61, 5)) + list(range(80, 301, 20)) + list(range(350, 601, 50)) + list(range(700, 1201, 100))
print("| h | fit mean | median | win | dead | sd | $/fire | lift | recent mean | median | win | dead | sd | $/fire | lift |")
print("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for h in TAB:
    row = f"| {h} |"
    for g in ("fit", "rec"):
        s = R[(g, h)]; row += f" {s['mean']:+.1%} | {s['median']:+.1%} | {s['win']:.0%} | {s['dead']:.0%} | {s['sd']:.2f} | {s['usd']:+.2f} | {s['lift']:+.1%} |"
    print(row)
print()
groups = list(dict.fromkeys(g for g, _ in R)); HS = (9, 15, 60, 300, 600)
print("| group | fires / refused | " + " | ".join(f"h {h}: mean, win, dead, $/fire, lift" for h in HS) + " |")
print("|---|---:|" + "---|" * len(HS))
for g in groups:
    s1 = R[(g, 1)]; row = f"| {g} | {int(s1['n'])} / {int(s1['n_ref'])} |"
    for h in HS:
        s = R[(g, h)]; row += f" {s['mean']:+.1%}, {s['win']:.0%}, {s['dead']:.0%}, {s['usd']:+.2f}, {s['lift']:+.1%} |"
    print(row)
