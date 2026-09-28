"""V_0: split the affected fires by who closes the 6.7 bundle. The 0x8191c327 -> 0xbd7c6f67 (cce7ec13) call closed it live twice
(Sep 25 16:24 0xd43ed726, Sep 28 12:52 0x98f4e88b: both 'bundle 0 < 3'), so it carries value; a stranger's direct buy closes it
whatever its value (state['buys'] records every buy-selector call). Every other closer is an assumption (the crowd rows carry no value)."""
import json, os, sys, time
sys.path.insert(0, "/home/user/fomo-memebot/data/derived/edge_check/N/2026-09-28/R1"); from common import usd, period, days
HERE = os.path.dirname(os.path.abspath(__file__)); R1 = "/home/user/fomo-memebot/data/derived/edge_check/N/2026-09-28/R1"
B = {r["cv"]: r for r in json.load(open(f"{HERE}/v_bundle_rows.json"))}
V = {v: {x["cv"]: x for x in json.load(open(f"{R1}/rows_{v}.json"))} for v in ("k2", "k1reg", "kreg")}
HZ = {"k2": "floor", "k1reg": "usual", "kreg": "usual"}
BOT = ("0x8191c3278afa0eabf5c20f35c7e9a3a63879db4f", "0xbd7c6f67")
def cls(cv, hz):
    b7, c7, b8, c8 = B[cv][f"{hz}_A"]
    if not (b7 < 3 <= b8): return None
    if B[cv][f"{hz}_B"][0] < 3: return "direct"                  # closed even when no stranger call carries value
    cl = B[cv]["closer"]
    return "bot" if (cl and cl[2] == BOT[0] and cl[3].startswith(BOT[1])) else "other"
for v in ("k2", "k1reg", "kreg"):
    print(f"view {v}")
    for p in ("fit", "read"):
        f = [y for c, y in V[v].items() if y.get("fired") and period(y["T0"]) == p and cls(c, HZ[v])]
        by = {}
        for y in f: by.setdefault(cls(y["cv"], HZ[v]), []).append(usd(y))
        conf = sorted(by.get("bot", []) + by.get("direct", []), reverse=True)
        print(f"  {p:4s}: " + " | ".join(f"{k} n={len(u)} ${sum(u):+.2f}" for k, u in sorted(by.items())) +
              f" || confirmed (bot+direct) n={len(conf)} ${sum(conf):+.2f}, without its largest ${sum(conf[1:]):+.2f}")
    allc = sorted([usd(y) for c, y in V[v].items() if y.get("fired") and cls(c, HZ[v]) in ("bot", "direct")], reverse=True)
    print(f"  week confirmed n={len(allc)} ${sum(allc):+.2f}; without the largest ${sum(allc[1:]):+.2f}; without the two largest ${sum(allc[2:]):+.2f}")
print("\n'other' closers at the usual view:")
for c, y in sorted(V["k1reg"].items(), key=lambda kv: kv[1]["T0"]):
    if y.get("fired") and cls(c, "usual") == "other":
        cl = B[c]["closer"]; print(f"  {time.strftime('%b %d %H:%M', time.gmtime(y['T0']))} {c[:10]} ${usd(y):+.2f} closer {cl[2][:10]} -> {cl[3][:10]} {cl[4]}; 6.7 bundle if that call carries no value: {B[c]['usual_B'][0]}; chain bundle {y['bundle']:.3f} ETH, k {B[c]['k']}")
