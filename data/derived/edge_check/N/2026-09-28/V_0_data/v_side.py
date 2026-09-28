"""V_0: side effects of 6.8 outside R1's set. (a) launches 6.7 counted >=3 but closed early (partial bundle ETH vs the caps);
(b) the replay's own 'bundle 0 < 3' / 'bundle ETH' refusals (rows the crowd files cannot see: helpers that do not name the curve)."""
import json, os, sys, time, collections
sys.path.insert(0, "/home/user/fomo-memebot/data/derived/edge_check/N/2026-09-28/R1"); from common import usd, period
HERE = os.path.dirname(os.path.abspath(__file__)); R1 = "/home/user/fomo-memebot/data/derived/edge_check/N/2026-09-28/R1"
B = {r["cv"]: r for r in json.load(open(f"{HERE}/v_bundle_rows.json"))}
V = {v: {x["cv"]: x for x in json.load(open(f"{R1}/rows_{v}.json"))} for v in ("k2", "k1reg", "kreg")}
print("(a) 6.7 bundle >= 3 but closed with fewer named buys than 6.8 counts (usual horizon, mode A): 6.7's bundle ETH ~ chain ETH x b7/b8")
n = 0
for cv, b in B.items():
    b7, c7, b8, c8 = b["usual_A"]
    if b7 >= 3 and c7 and b7 < b8:
        y = V["k1reg"][cv]; e = y["bundle"]; e7 = e * b7 / b8; n += 1
        flip = ("6.7 < 0.3 ETH, 6.8 passes" if e7 < 0.3 <= e else "") + ("6.7 <= 3.0, 6.8 over the cap" if e7 <= 3.0 < e else "")
        if flip or y.get("fired"):
            print(f"  {time.strftime('%b %d %H:%M', time.gmtime(y['T0']))} {cv[:10]} 6.7 {b7}/6.8 {b8} chain {e:.3f} ETH ~6.7 {e7:.3f} | {y['why']} {flip}")
print(f"  {n} launches partially counted by 6.7")
print("\n(b) the replay's own bundle refusals at the usual view (the crowd rows show fewer than 3 named buyers or the ETH is out of range)")
for cv, y in sorted(V["k1reg"].items(), key=lambda kv: kv[1]["T0"]):
    if y["why"].startswith("GATE bundle"):
        r = (y.get("ret") or {}).get("11"); f = y.get("fleets")
        print(f"  {period(y['T0']):4s} {time.strftime('%b %d %H:%M', time.gmtime(y['T0']))} {cv[:10]} {y['why']:28s} chain {y['bundle']:.3f} ETH fleets {f} tier {y.get('tier')} h11 {'' if r is None else f'{r:+.1%}'}")
