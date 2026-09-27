"""extra_score.py (edge_check/C): scores the launches of C's extension window(s) (extend_window.py tag extra27) on the same
yardstick: fleets and wallets at k-2, fire or not, second place $13 at 15/60/150/300 blocks, the post-seat crowd.
    python3 data/derived/edge_check/C/extra_score.py > data/derived/edge_check/C/extra_score.txt"""
import sys, json, gzip
sys.path.insert(0, "data/derived/edge_check/C"); from common import *
L0 = json.load(open(C + "launches_extra27.json")); print(f"window {hms(L0['t_lo'])} - {hms(L0['t_hi'])}: {L0['creations']} creations, {len(L0['launches'])} qualifying, unresolved {L0['unresolved']}")
for r in json.load(gzip.open(C + "crowd_raw_extra27.json.gz", "rt")):
    L = tape(r["cv"]); f2, w2 = fleets_k2(r); cw, cf = cums(r)
    rets = {h: price(L, h, 1) for h in (15, 60, 150, 300)} if L else {}
    print(f"  {hms(r['T0'])} {r['cv'][:10]} k {r['k']} fleets by block {cf} wallets by block {cw}  fleets@k-2 {f2} -> {'FIRE' if f2 >= 2 else 'refuse'}  "
          + "  ".join(f"h{h} {v:+.1%}" for h, v in rets.items()))
