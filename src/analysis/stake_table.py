"""stake_table.py: the rule the engine runs (fleets >= 2 by block k-2, second place, 300 blocks) re-priced at larger stakes with
the audited model (fixed-ETH buyers behind us, the 3% supply cap, the exit's own impact), on the fit windows' fires and the
paper windows' fires, tapes pulled in parallel from the public RPC.   python3 src/analysis/stake_table.py [workers=6]"""
import json, gzip, sys, os, math, statistics as st, concurrent.futures as futures, time
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); sys.path.insert(0, "src/analysis")
import live_vs_table as lv
W = int(sys.argv[1]) if len(sys.argv) > 1 else 6; sys.argv = ["x", "0.76", "0.71"]
exec(open("src/analysis/crowd_rules.py").read().split("rules = [")[0])                    # cums, at
exec(open("src/analysis/stake_scale.py").read().split("\nfor name, cf, hours in W:")[0])   # model_eff, E, GAS
D = "data/derived/live_vs_table/"; HOLD = 300; STAKES = (13, 25, 50, 100, 150, 200, 250, 300)
SETS = {"fit (4 windows, 96 h)": (96.0, ["crowd_raw_sep1819", "crowd_raw_sep2021", "crowd_raw_sep2223", "crowd_raw_sep23day"]),
        "paper (5 windows, 34 h)": (34.0, ["crowd_raw_sep24paper", "crowd_raw_sep25night", "crowd_raw_sep25am", "crowd_raw_sep25pm", "crowd_raw_sep25eve2"])}
def fires(files):
    out = []
    for f in files:
        for r in json.load(gzip.open(D + f + ".json.gz", "rt")):
            cw, cf_ = cums(r)
            if at(cf_, r["k"] - 2) >= 2: out.append((r["cv"], r["b0"]))
    return out
def price(item):
    cv, b0 = item
    for attempt in range(3):
        try:
            L = lv.launch(cv, b0 + 12)
            if L is None or L["tier"] is None: return None
            more = lv.call("eth_getLogs", [{"fromBlock": hex(b0 + 121), "toBlock": hex(b0 + HOLD + 30), "address": cv, "topics": [[lv.BUY, lv.SELL]]}])
            L["rows"] = sorted(L["rows"] + [lv.row_of(x) for x in more], key=lambda r: (r["bn"], r["li"])); ts = L["ts"]; T0 = L["T0"]
            bE1 = next((n for n in range(b0 + 1, b0 + 30) if ts.get(n, 0) == T0 + 1), None)
            if bE1 is None: return None
            return {s: model_eff(L, s / E, bE1, 1, HOLD) for s in STAKES}
        except Exception as e:
            time.sleep(2 * (attempt + 1))
    return None
for name, (hours, files) in SETS.items():
    items = fires(files); t0 = time.time()
    with futures.ThreadPoolExecutor(W) as ex: res = [x for x in ex.map(price, items) if x]
    print(f"\n=== {name}: {len(res)} of {len(items)} fires priced in {time.time()-t0:.0f} s; fixed-ETH buyers behind us, the 3% cap, the exit's impact; gas ${GAS:.2f}")
    print(f"{'stake':>6s} {'in (avg)':>9s} {'capped':>7s} {'return':>8s} {'win':>5s} {'$/burst':>8s} {'$/day':>7s} {'best':>8s} {'worst':>8s}")
    for s in STAKES:
        v = [(r * g * E - GAS, g * E, r) for r, g in (x[s] for x in res)]
        print(f"${s:<5d} ${st.mean(p for _, p, _ in v):8.0f} {sum(1 for _, p, _ in v if p < s * 0.98):7d} {st.mean(r for _, _, r in v):+8.1%} {sum(u > 0 for u, _, _ in v)/len(v):5.0%} {st.mean(u for u, _, _ in v):+8.2f} {sum(u for u, _, _ in v)/hours*24:+7.0f} {max(u for u, _, _ in v):+8.1f} {min(u for u, _, _ in v):+8.1f}")
