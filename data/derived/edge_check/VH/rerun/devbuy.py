"""devbuy.py (edge_check/H): the creator's own first buy (the engine's bundle_eth counts it, e1_multi's does not) on the fires near
and above the cap, and over all launches with a tape.  python3 data/derived/edge_check/H/devbuy.py > data/derived/edge_check/H/devbuy.txt"""
import sys, os, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *; from common import _tapes
TP = _tapes(); P = load(); dev = []
for x in P:
    if x["cv"] not in TP: continue
    rows = sorted(TP[x["cv"]]["rows"], key=lambda r: (r["bn"], r["li"])); d = rows[0]["eth"] if rows[0]["k"] == "B" else 0.0; dev.append(d)
    if 2.3 <= x["bundle"] <= 4.5 and (x["fire_eng"] or x["fire_tab"]): print(f"{x['cv'][:10]} bundle {x['bundle']:.3f} dev buy {d:.3f} sum {x['bundle'] + d:.3f}")
print(f"dev buy over all {len(dev)} launches with a tape: median {st.median(dev):.3f} p90 {sorted(dev)[int(0.9 * len(dev))]:.3f} max {max(dev):.3f}")
