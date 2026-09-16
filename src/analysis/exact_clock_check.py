"""Needs ALCH=<alchemy key> in the environment (12,000 block reads once; cached in exact_clock_bt.pkl).
the clock check: for a sample of clean Sep 12-16 launches, fetch the real timestamp of every block from the creation
to +7 s, rebuild the rows on the exact clock (second = block timestamp, phase = position among that second's blocks) and
re-run my simulator; compare with the same simulator on the cache's interpolated clock"""
import pickle, json, os, sys, random, statistics as st, urllib.request, collections, datetime
from concurrent.futures import ThreadPoolExecutor
sys.argv = [sys.argv[0]]; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "indep_replay.py")).read().split("recs = []")[0])
RPC = "https://robinhood-mainnet.g.alchemy.com/v2/" + os.environ["ALCH"]
def rpc(m, p):
    q = json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(RPC, q, {"content-type": "application/json"}), timeout=60).read())["result"]

eng = open("/home/user/fomo-memebot/src/strategy/sniper_engine.py").read()
BUY = eng.split('BUY_EV = "')[1].split('"')[0]; SELL = eng.split('SELL_EV = "')[1].split('"')[0]
random.seed(7)
oos_keys = [k for k in data if k[0] >= "2026-09-12" and k[0] <= "2026-09-15"]
pool = [(k, cv, L) for k in oos_keys for cv, (L, f) in data[k].items() if feats(L)["out1"] == 0 and not ((feats(L)["rival_lag"] or 9) < 0.3)]
sample = random.sample(pool, 150)
filt_of = {cv: (lambda g: g["n"] >= 5 and 0.3 <= g["eth"] <= 1.2 and g["tk0"] >= 0.03)(feats(L)) for _, cv, L in sample}
raw = collections.defaultdict(list)                               # curve -> [(b, li, kind, q, tk, fee)]
want = {cv for _, cv, _ in sample}
for k in oos_keys:
    for line in open(S + f"rh/v2curve_{k[0]}_{k[1]}.jsonl"):
        b, li, tx, addr, t0, d = json.loads(line)
        if addr in want:
            w = [int(d[2:][i:i + 64], 16) / 1e18 for i in range(0, len(d) - 2, 64)]
            raw[addr].append((b, li, "B", w[0], w[1]) if t0 == BUY[:10] else (b, li, "S", w[1], w[0]))   # the pull stores the topic's first 10 chars
blocks = sorted({b for _, cv, L in sample for b in range(L["b"], L["b"] + 80)})
print("fetching", len(blocks), "block timestamps")
def ts_of(b):
    for _ in range(4):
        try: return b, int(rpc("eth_getBlockByNumber", [hex(b), False])["timestamp"], 16)
        except Exception: pass
    return b, None
BT = pickle.load(open(S + "exact_clock_bt.pkl", "rb")) if os.path.exists(S + "exact_clock_bt.pkl") else {}
todo = [b for b in blocks if b not in BT]
with ThreadPoolExecutor(8) as ex: BT.update(dict(ex.map(ts_of, todo)))
pickle.dump(BT, open(S + "exact_clock_bt.pkl", "wb"))
rows_cmp = []
for k, cv, L in sample:
    ev = sorted(raw[cv]); b0 = L["b"]; T0 = BT[b0]
    if T0 is None or ev[0][0] != b0: continue
    first_of = {}                                                  # first block of each second in the fetched range
    for b in range(b0, b0 + 80):
        t = BT.get(b)
        if t is not None and t not in first_of: first_of[t] = b
    # the creation's own phase inside its second (like the cache's pos_create)
    pos0 = 0.1 * (b0 - first_of[T0]); ts_exact = T0 + pos0
    rows = []; tier = L["tier"]; crow = L["rows"]; j = 0; bad = 0
    for c in crow:                                                 # the cache's own amounts, net and tax (exact, from load_exact); only the time is replaced
        while j < len(ev) and not (ev[j][2] == c[1] and abs(ev[j][3] - c[2]) < 1e-9 and abs(ev[j][4] - c[3]) < 1e-6):
            j += 1                                                 # a raw event the cache dropped
        if j >= len(ev):
            bad += 1; break
        b = ev[j][0]; j += 1; t = BT.get(b)
        if t is None:
            break
        rows.append((t + 0.1 * (b - first_of[t]) - ts_exact,) + tuple(c[1:]))
    if bad or len(rows) < 3:
        print("could not align", cv[:10], len(crow), len(ev), "rows", len(rows)); continue
    Lx = {"rows": rows, "tier": tier, "ts": ts_exact}
    gx = feats(Lx); gc = feats(L)
    a = sim(Lx, "E2")["roi"]; c = sim(L, "E2")["roi"]
    clean_x = gx["out1"] == 0 and not (gx["rival_lag"] is not None and gx["rival_lag"] < 0.3)
    rows_cmp.append((k[0], cv, a, c, clean_x, gc["rival_lag"], gx["rival_lag"], len(rows), 0))
print(f"\n{len(rows_cmp)} launches rebuilt on the exact clock")
ex_ = [r[2] for r in rows_cmp]; ca = [r[3] for r in rows_cmp]
print(f"E2 clean, $25: exact clock mean {100*st.mean(ex_):+.1f}%  |  cache clock mean {100*st.mean(ca):+.1f}%  |  mean difference {100*st.mean(a-c for a,c in zip(ex_,ca)):+.1f} pts, "
      f"|diff| > 5 pts on {sum(abs(a-c)>0.05 for a,c in zip(ex_,ca))} of {len(ex_)}")
cx = [r for r in rows_cmp if r[4]]
def ci(xs, n=3000):
    random.seed(1); b = sorted(st.mean(random.choice(xs) for _ in xs) for _ in range(n)); return b[int(0.025 * n)], b[int(0.975 * n)]
lo, hi = ci([r[2] for r in cx])
share = len(cx) / len(rows_cmp); se = (share * (1 - share) / len(rows_cmp)) ** 0.5
print(f"still clean on the exact clock (the engine would have sent): {len(cx)} of {len(rows_cmp)} = {100*share:.0f}% (+-{200*se:.0f} pts); on those, exact clock mean {100*st.mean(r[2] for r in cx):+.1f}% [{100*lo:+.1f}%, {100*hi:+.1f}%], cache clock mean {100*st.mean(r[3] for r in cx):+.1f}%")
fx = [r for r in cx if filt_of[r[1]]]
print(f"of those, passing the re-fitted filter: {len(fx)}, exact clock mean {100*st.mean(r[2] for r in fx) if fx else 0:+.1f}%")
nx = [r for r in rows_cmp if not r[4]]
print(f"not clean on the exact clock (a rival inside the 0.3 s wait: the engine would not have sent): {len(nx)}; their cache-clock returns: " + ", ".join(f"{100*r[3]:+.0f}%" for r in nx))
print("worst disagreements (day, curve, exact, cache, clean_exact, rival_lag cache -> exact):")
for r in sorted(rows_cmp, key=lambda r: -abs(r[2]-r[3]))[:6]:
    print(f"   {r[0]} {r[1][:10]} exact {100*r[2]:+6.1f}%  cache {100*r[3]:+6.1f}%  clean {r[4]}  lag {r[5] if r[5] is None else round(r[5],2)} -> {r[6] if r[6] is None else round(r[6],2)}")
