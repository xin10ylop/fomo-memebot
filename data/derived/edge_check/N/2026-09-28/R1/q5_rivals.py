"""Q5c: who takes the front of the seat block. For every eligible launch of the week, the first rival target (relay or direct sender)
in E1's chain order, by day; today's leaders against the week's (the fixed-size first buyers of 24.42 were 0x924378f2, 0x6c56103c,
0x5051e45b)."""
import sys, collections; sys.path.insert(0, "."); from common import *
C = crowd(); V = load_view("k1reg")
first = collections.defaultdict(collections.Counter); fired_first = collections.defaultdict(collections.Counter); n = collections.Counter(); nf = collections.Counter()
for cv, r in V.items():
    if not eligible(r) or cv not in C: continue
    c = C[cv]; e1 = c["k"] + 1
    if e1 >= len(c["blocks"]): continue
    d = r["day"]; n[d] += 1; nf[d] += bool(r.get("fired"))
    for t in sorted(c["blocks"][e1], key=lambda t: t.get("ix", 0)):
        if t["to"] in US or t["fr"] in US or t["named_fr"] or t["to_token"]: continue
        key = (t["fr"] if t["direct"] else t["to"])[:10]; first[d][key] += 1
        if r.get("fired"): fired_first[d][key] += 1
        break
for d in sorted(n, key=lambda d: time.strptime(d + " 2026", "%b %d %Y")):
    print(f"{d}: {n[d]:3d} eligible, {nf[d]:3d} fires; first rival in E1 on the fires: " + ", ".join(f"{k} {v}" for k, v in fired_first[d].most_common(4)))
