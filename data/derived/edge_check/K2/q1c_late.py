"""K2/q1c_late.py: what a looser guard lets through when the sequencer holds the burst and it lands late in the seat second
(first in block E1+j, j = 1..8; the relay's deadline refuses anything past the second). The guard checked there against the tokens
sized at the build; the sell 11 blocks after the fill. Taped usual-view fires."""
import os, sys, json, gzip
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from sim import *
import price_tapes as PT
F = [r["x"] for r in run(guard=False) if r.get("fired") and r["x"]["cv"] in PT.TAPES]
print(f"{len(F)} taped fires (fit {sum(period(x)=='fit' for x in F)}, read {sum(period(x)=='read' for x in F)})")
for j in (0, 1, 2, 3, 5, 8):
    for per in ("fit", "read"):
        c = []
        for slip in (0.07, 0.15, 0.25, 1.0):
            usd = 0; nf = 0; v = []
            for x in F:
                if period(x) != per: continue
                L = PT.TAPES[x["cv"]]; ts = L["ts"]; bE1 = L["b0"] + x["k"] + 1
                if ts.get(bE1 + j, 0) != L["T0"] + 1: usd -= 0.33; continue          # past the seat second: the relay refuses (TooLate)
                vals, tk, g = PT.path(L, 13.0, bE1 + j, 0, (11,))
                if x["tk_build"] and tk < (1 - slip) * x["tk_build"]: usd -= 0.33; continue
                usd += vals[11] * 13 - 0.33; nf += 1; v.append(vals[11])
            c.append(f"slip {slip:4.2f}: {nf:2d} fills {mean(v):+6.1%} ${usd:+6.1f}")
        print(f"  first in E1+{j} {per:4s} | " + " | ".join(c))
