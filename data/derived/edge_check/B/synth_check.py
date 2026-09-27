"""synth_check.py (reviewer B): the synthesised stamps of pull_fast.py against the real ones, on every launch that has a real
tape: the h300 return and the outsiders' ETH after the seat second with each. python3 data/derived/edge_check/B/synth_check.py"""
import sys, os, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
import features as fe
R = {r["cv"]: r for r in c.load(c.FIT) + c.load(c.RECENT)}; d300 = []; dout = []
for r in R.values():
    L = c.tape(r["cv"])
    if L is None or L.get("ts_synth"): continue
    real = fe.feat(r, "x"); b0, k, T0 = r["b0"], r["k"], r["T0"]
    ts = {str(b0 + i): T0 for i in range(k + 1)}
    for i in range(k + 1, 31): ts[str(b0 + i)] = T0 + 1 + (i - k - 1) // 10
    L["ts"] = ts; orig = c.tape; c.tape = lambda cv, L=L: json.loads(json.dumps(L)); syn = fe.feat(r, "x"); c.tape = orig
    if real and syn:
        d300.append(abs(real["ret"][300] - syn["ret"][300])); dout.append(abs(real["buy_eth_after"].get("other", 0) - syn["buy_eth_after"].get("other", 0)))
print(f"{len(d300)} launches: h300 |real - synth| max {max(d300):.4f}, share > 0.001: {sum(x > 0.001 for x in d300)/len(d300):.3f}; outsiders' ETH |diff| max {max(dout):.3f}, mean {sum(dout)/len(dout):.4f}")
