"""seat_positions_report.py S [view]: the guard grid at each position, from seat_positions.py's positions.json (runbook 5az)"""
import json, sys, statistics as st
S = sys.argv[1]; view = sys.argv[2] if len(sys.argv) > 2 else "k-1"
A = [y for y in json.load(open(f"{S}/positions.json")) if y.get("pos") and "err" not in y["pos"] and view in y["views"]]
print(f"view {view}: {len(A)} fired launches priced; errors {sum(1 for y in json.load(open(f'{S}/positions.json')) if y.get('pos') and 'err' in y['pos'])}")
def stake(y): return y["stake"] if y.get("stake") and 5 < y["stake"] < 200 else 25.0
for pos in ("s1", "s3", "s5", "sL", "L2", "L5", "L9", "L13", "L24", "L33"):
    line = [pos]
    base = None
    for g in (0.20, 0.25, 0.30, 0.35):
        F = [y for y in A if y["pos"][pos][0] >= 1 - g and y["pos"][pos][1] is not None]
        usd = sum(stake(y) * y["pos"][pos][1] for y in F)
        if base is None: base = (set(y["cv"] for y in F), usd); line.append(f"g{g:.2f} n{len(F)} ${usd:+.0f}")
        else:
            X = [y for y in F if y["cv"] not in base[0]]; r = [y["pos"][pos][1] for y in X]
            line.append(f"g{g:.2f} +{len(X)} fills {sum(v > 0 for v in r)}w med {100*st.median(r):+.0f}% ${usd-base[1]:+.0f}" if r else f"g{g:.2f} +0")
    print(" | ".join(line))
