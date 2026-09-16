"""the live hours replayed: every bundled launch of Sep 16 12-18 UTC on the chain, with the chain's own reading of the seat
(bundle, ETH, outsiders in second one, first rival in second two), the current rule's verdict, and what the engine would have
taken with the filter and one position at a time"""
import sys, pickle, datetime, statistics as st, os
os.chdir("/tmp/claude-0/-home-user-fomo-memebot/a7a59693-7c2d-5b6c-b7df-e43fdbe7d612/scratchpad")
sys.path.insert(0, "/home/user/fomo-memebot/src/analysis"); import risk_harness as RH
exec(open("/home/user/fomo-memebot/src/analysis/indep_replay.py").read().split("recs = []")[0])   # sim(), feats(), data
PX = RH.PX
k = ("2026-09-16", "12-18")
launches = data.get(k) or pickle.load(open("risk_harness_cache_new_v2.pkl", "rb")).get(k, {})
print(f"Sep 16 12-18 UTC on the chain: {len(launches)} bundled launches (3+ wallets, 0.3+ ETH, creator 1%+)")
rows = []
for cv, (L, f) in sorted(launches.items(), key=lambda kv: kv[1][0]["ts"]):
    g = feats(L); t = datetime.datetime.fromtimestamp(L["ts"], datetime.timezone.utc)
    clean = g["out1"] == 0 and not (g["rival_lag"] is not None and g["rival_lag"] < 0.3)
    rule = g["n"] >= 5 and 0.3 <= g["eth"] <= 1.2 and g["tk0"] >= 0.03
    x = RH.replay(L, 25 / PX, hold=5.0, tp=0.5); roi_h = (x[0] * PX - 0.10) / (x[1] * PX) if x[1] > 1e-6 else None
    rows.append((t, cv, g, clean, rule, sim(L, "E2", stake_usd=10)["roi"], roi_h))
    print(f"  {t:%H:%M:%S} {cv[:10]} bundle {g['n']:2d} eth {g['eth']:.3f} creator {100*g['tk0']:.1f}% out1 {g['out1']:3d} rival_lag {g['rival_lag'] if g['rival_lag'] is None else round(g['rival_lag'],2)} "
          f"-> {'CLEAN' if clean else 'crowded'} {'rule ok' if rule else 'filtered'} | paper $10: {100*rows[-1][5]:+.1f}%")
take = [r for r in rows if r[3] and r[4]]
print(f"\nthe rule would have traded: {len(take)} launch(es)" + (f"; mean {100*st.mean(r[5] for r in take):+.1f}% at $10 = {sum(10*r[5] for r in take):+.2f} $" if take else ""))
print("crowded share among bundled launches:", f"{100*sum(1 for r in rows if not r[3])/len(rows):.0f}%" if rows else "n/a")
