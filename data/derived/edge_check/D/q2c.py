"""q2c.py (reviewer D): how sensitive the short hold is to where the sell really lands (the engine decides after block E1+15 and
its sell lands some blocks later): the rule's fires sold after E1+h for h = 10..40, fit against recent.
    python3 data/derived/edge_check/D/q2c.py > data/derived/edge_check/D/q2c.txt"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c, kit as K
for h in (10, 12, 15, 17, 18, 20, 25, 30, 40):
    a = [f["path"][h] for f in K.FIT if f["fire"]]; b = [f["path"][h] for f in K.REC if f["fire"]]
    print(f"  sold after E1+{h:<3d} fit {c.mean(a):+6.1%} (win {sum(x>0 for x in a)/len(a):3.0%})   recent {c.mean(b):+6.1%} (win {sum(x>0 for x in b)/len(b):3.0%})")
