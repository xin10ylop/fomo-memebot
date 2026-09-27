"""q1b.py (reviewer D): the readings of the discovery side by side, same yardstick ($13, second place in E1, gas $0.33),
fit (96 h) against recent (60 h): the gate (the rule) at each hold; the crowd after the seat as an oracle (not tradable: at
least 3 buys behind us in the seat block or 4 outsider wallets in the next 15 blocks), alone and with the gate; the tradable
proxy (hold to H only if the crowd showed in 15 blocks: q3.py's best by the fit); and the no-gate population.
    python3 data/derived/edge_check/D/q1b.py > data/derived/edge_check/D/q1b.txt"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import kit as K
def ca(f): return f["behind_n"] >= 3 or f["ow15"] >= 4
rows = [("every qualifying launch, h15", lambda f: 15), ("every qualifying launch, h300", lambda f: 300)]
for h in (15, 60, 150, 300): rows.append((f"GATE (the rule), h{h}", (lambda h: lambda f: h if f["fire"] else None)(h)))
for h in (15, 300): rows.append((f"ORACLE crowd after the seat, h{h}", (lambda h: lambda f: h if ca(f) else None)(h)))
for h in (15, 300): rows.append((f"ORACLE gate & crowd after, h{h}", (lambda h: lambda f: h if f["fire"] and ca(f) else None)(h)))
rows.append(("PROXY gate, h300 if ow15>=3 else h15", lambda f: (300 if f["ow15"] >= 3 else 15) if f["fire"] else None))
rows.append(("PROXY gate, h150 if ow15>=3 else h15", lambda f: (150 if f["ow15"] >= 3 else 15) if f["fire"] else None))
for n, p in rows: print(K.line(n, K.evaluate(p)))
