"""reach_table.py: the tables' fires (fleets >= 2 at k-2) split by whether the engine's aim can reach the seat: the burst
must be built before the seat's second opens, and the build waits for the curve to resolve, which happens when the first
named buy shows on the feed. From the chain: the creation block b0 has k more blocks in its second, so it sits about
(9 - k) blocks into the second; the first named buy is j blocks after b0; feed lag about two blocks, the build about
half a block. Reachable when (9 - k) + j + 2.5 < 10, i.e. j <= k - 2 (a stricter j <= k - 3 is shown too). Sep 27: the
two two-fleet launches of the night (k = 6, j = 4-5) were aim-skipped exactly there. Prices every fire as stake_table.py.

    python3 src/analysis/reach_table.py [workers=6]"""
import json, gzip, sys, os, statistics as st, concurrent.futures as futures, time
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); sys.path.insert(0, "src/analysis")
import live_vs_table as lv
NWORK = int(sys.argv[1]) if len(sys.argv) > 1 else 6; sys.argv = ["x", "0.76", "0.71"]
exec(open("src/analysis/crowd_rules.py").read().split("rules = [")[0])                    # cums, at
exec(open("src/analysis/stake_scale.py").read().split("\nfor name, cf, hours in W:")[0])   # model_eff, E, GAS
D = "data/derived/live_vs_table/"; HOLD = 300; STAKES = (13, 200)
SETS = {"fit (4 windows, 96 h)": (96.0, ["sep1819", "sep2021", "sep2223", "sep23day"]),
        "paper+live (Sep 24-27, 60 h)": (60.0, ["sep24paper", "sep25night", "sep25am", "sep25pm", "sep25eve", "sep25eve2", "sep26night", "sep26am", "sep26pm", "sep26restart", "sep27night"])}
def first_named_block(r):
    for j, rows in enumerate(r["blocks"]):
        if any(x.get("named_fr") or x.get("named_data") for x in rows): return j
    return None
def fires(files):
    out = []
    for f in files:
        p = D + f"crowd_raw_{f}.json.gz"
        if not os.path.exists(p): continue
        for r in json.load(gzip.open(p, "rt")):
            cw, cf_ = cums(r)
            if at(cf_, r["k"] - 2) >= 2:
                j = first_named_block(r); out.append({"cv": r["cv"], "b0": r["b0"], "k": r["k"], "j": j, "T0": r["T0"]})
    return out
def price(it):
    cv, b0 = it["cv"], it["b0"]
    for attempt in range(3):
        try:
            L = lv.launch(cv, b0 + 12)
            if L is None or L["tier"] is None: return None
            more = lv.call("eth_getLogs", [{"fromBlock": hex(b0 + 121), "toBlock": hex(b0 + HOLD + 30), "address": cv, "topics": [[lv.BUY, lv.SELL]]}])
            L["rows"] = sorted(L["rows"] + [lv.row_of(x) for x in more], key=lambda r: (r["bn"], r["li"])); ts = L["ts"]; T0 = L["T0"]
            bE1 = next((n for n in range(b0 + 1, b0 + 30) if ts.get(n, 0) == T0 + 1), None)
            if bE1 is None: return None
            out = dict(it); out.update({s: model_eff(L, s / E, bE1, 1, HOLD) for s in STAKES}); return out
        except Exception as e:
            err = e; time.sleep(2 * (attempt + 1))
    print(f"  unpriced {cv[:10]}: {str(err)[:90]}", file=sys.stderr); return None
def line(name, rows, hours):
    if not rows: print(f"{name:34s} 0 fires"); return
    r13 = [x[13][0] for x in rows]; u13 = [x[13][0] * x[13][1] * E - GAS for x in rows]; u200 = [x[200][0] * x[200][1] * E - GAS for x in rows]
    print(f"{name:34s} {len(rows):3d} fires  mean {st.mean(r13):+6.1%}  win {sum(x > 0 for x in r13)/len(r13):3.0%}  dead {sum(x < -0.4 for x in r13)/len(r13):3.0%}  $/day at $13 {sum(u13)/hours*24:+6.0f}  at $200 {sum(u200)/hours*24:+6.0f}")
for name, (hours, files) in SETS.items():
    items = fires(files); t0 = time.time()
    with futures.ThreadPoolExecutor(NWORK) as ex: res = [x for x in ex.map(price, items) if x]
    print(f"\n=== {name}: {len(res)} of {len(items)} fires priced in {time.time()-t0:.0f} s")
    line("all fires (the tables)", res, hours)
    line("reachable, j <= k-2", [x for x in res if x["j"] is not None and x["j"] <= x["k"] - 2], hours)
    line("reachable, j <= k-3 (stricter)", [x for x in res if x["j"] is not None and x["j"] <= x["k"] - 3], hours)
    line("not reachable (j > k-2)", [x for x in res if x["j"] is None or x["j"] > x["k"] - 2], hours)
    if "paper" in name:
        print("  per fire (the engine's real disposition is in engine_vs_chain):")
        for x in sorted(res, key=lambda x: x["T0"]): print(f"   {time.strftime('%b %d %H:%M', time.gmtime(x['T0']))} {x['cv'][:10]} k {x['k']} j {x['j']} reachable {x['j'] is not None and x['j'] <= x['k'] - 2}  h300 {x[13][0]:+.1%}")
