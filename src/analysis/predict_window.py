"""predict_window.py: what the paper reading of a window SHOULD show, from the chain alone, written before the engine's log
is read (report 24.33): every qualifying launch of the window (the tables' population), the engine's rule (fleets >= 2 at
the gate's opening) at the exact-block views k-1 and k-2 and at the tick's-shot model view, and the second-place return at
300 blocks for each. The engine's own pre-gate filters (creator supply, creator repeat, one hold at a time, the aim, the
blind window before registration) are not applied here, so the engine fires on a subset of these.
    python3 src/analysis/predict_window.py crowd_raw_X.json[.gz] hold_grid_X.json launches_X.json"""
import json, gzip, sys, os, math, time, statistics as st
sys.argv_saved = list(sys.argv); raw_f, hg_f, la_f = sys.argv[1:4]; sys.argv = ["x", "0.76", "0.71"]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "crowd_rules.py")).read().split("rules = [")[0])   # cums, view, at, US, STAKE, GAS
R = json.load(gzip.open(raw_f, "rt")) if raw_f.endswith(".gz") else json.load(open(raw_f)); H = {r["cv"]: r for r in json.load(open(hg_f))}
L = {l["cv"].lower(): l for l in json.load(open(la_f))}
rows = []
for r in R:
    h = H.get(r["cv"]); x = h.get("behind1_15_h300") if h else None
    if x is None or (isinstance(x, float) and math.isnan(x)): continue
    cw, cf = cums(r); k = r["k"]; rows.append({"cv": r["cv"], "T0": r["T0"], "k": k, "cf": cf, "ret": x, "hour": L.get(r["cv"], {}).get("hour")})
rows.sort(key=lambda r: r["T0"])
print(f"{len(rows)} qualifying launches scored, {time.strftime('%b %d %H:%M', time.gmtime(rows[0]['T0']))} - {time.strftime('%b %d %H:%M', time.gmtime(rows[-1]['T0']))} UTC")
views = {"k-1": lambda r: at(r["cf"], r["k"] - 1), "tick's shot (0.76)": lambda r: at(r["cf"], view(r["k"], 0.76)), "k-2": lambda r: at(r["cf"], r["k"] - 2)}
print(f"{'when':13s} {'launch':11s} {'k':>2s} {'fleets by block':24s} {'k-1':>4s} {'tick':>4s} {'k-2':>4s} {'behind1 h300':>13s}")
for r in rows:
    print(f"{time.strftime('%b %d %H:%M', time.gmtime(r['T0'])):13s} {r['cv'][:10]:11s} {r['k']:2d} {str(r['cf']):24s} {views['k-1'](r):4d} {views[chr(116)+'ick'+chr(39)+'s shot (0.76)'](r) if False else at(r['cf'], view(r['k'], 0.76)):4d} {views['k-2'](r):4d} {r['ret']:+13.1%}")
print()
for name, f in views.items():
    fires = [r["ret"] for r in rows if f(r) >= 2]
    if not fires: print(f"{name:20s} 0 fires"); continue
    usd = [x * STAKE - GAS for x in fires]
    print(f"{name:20s} {len(fires):3d} fires  mean {st.mean(fires):+6.1%}  median {st.median(fires):+6.1%}  win {sum(x>0 for x in fires)/len(fires):3.0%}  dead {sum(x<-0.4 for x in fires)/len(fires):3.0%}  ${sum(usd):+.2f} total at ${STAKE:.0f} after gas")
skipped = [r["ret"] for r in rows if at(r["cf"], r["k"] - 1) < 2]
if skipped: print(f"{'refused (k-1 < 2)':20s} {len(skipped):3d}        mean {st.mean(skipped):+6.1%}  median {st.median(skipped):+6.1%}  win {sum(x>0 for x in skipped)/len(skipped):3.0%}")
