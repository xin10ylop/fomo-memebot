"""the clock check: for a sample of clean Sep 12-16 launches, fetch the real timestamp of every block from the creation
to +7 s, rebuild the rows on the exact clock (second = block timestamp, phase = position among that second's blocks) and
re-run my simulator; compare with the same simulator on the cache's interpolated clock"""
import pickle, json, os, sys, random, statistics as st, urllib.request, collections, datetime
from concurrent.futures import ThreadPoolExecutor
sys.argv = [sys.argv[0]]; exec(open("/tmp/claude-0/-home-user-fomo-memebot/a7a59693-7c2d-5b6c-b7df-e43fdbe7d612/scratchpad/indep_sim.py").read().split("recs = []")[0])
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

exec(open("e0_seat.py").read().split('print("=== the creation second')[0].split("exec(open(")[0])   # nothing: e0() is defined below
def e0(L, t_after, hold, tp, surcharge=0.0618, stake=25):
    rows = L["rows"]; tier = L["tier"]; X, Y = X0, Y0; i = 0
    for i, r in enumerate(rows):
        if i > 0 and r[0] >= t_after: break
        if r[1] == "B": X += r[4]; Y -= r[3]
        else: X -= r[4]; Y += r[3]
    else: i = len(rows)
    fee = tier + surcharge; stake_eth = stake / PX; tk = 0.03 * Y0; net = X * tk / (Y - tk); gross = net / (1 - fee)
    if gross > stake_eth: gross = stake_eth; net = gross * (1 - fee); tk = Y * net / (X + net)
    X += net; Y -= tk; p_in = X / Y; t_out = t_after + hold + 0.3
    for r in rows[i:]:
        if r[0] >= t_out: break
        if r[1] == "B":
            got = Y - X * Y / (X + r[4])
            if got < r[3] * 0.9: continue
            X += r[4]; Y -= got
        else:
            s_ = min(r[3], Y0 - Y - tk); g = X - X * Y / (Y + s_); X -= g; Y += s_
        if tp and X / Y >= p_in * (1 + tp) and t_out > r[0] + 0.3: t_out = r[0] + 0.3
    out = (X - X * Y / (Y + tk)) * (1 - tier)
    return ((out - gross) * PX - 0.11) / (gross * PX)
pairs = []
for k, cv, L in sample:
    ev = sorted(raw[cv]); b0 = L["b"]; T0 = BT.get(b0)
    if T0 is None or not ev or ev[0][0] != b0: continue
    first_of = {}
    for b in range(b0, b0 + 80):
        t = BT.get(b)
        if t is not None and t not in first_of: first_of[t] = b
    rows = []; crow = L["rows"]; j = 0; bad = 0
    for c in crow:
        while j < len(ev) and not (ev[j][2] == c[1] and abs(ev[j][3] - c[2]) < 1e-9 and abs(ev[j][4] - c[3]) < 1e-6): j += 1
        if j >= len(ev): bad += 1; break
        b = ev[j][0]; j += 1; t = BT.get(b)
        if t is None: break
        rows.append((t + 0.1 * (b - first_of[t]) - (T0 + 0.1 * (b0 - first_of[T0])),) + tuple(c[1:]))   # exact: seconds after the creation BLOCK
    if bad or len(rows) < 3: continue
    Lx = {"rows": rows, "tier": L["tier"], "ts": T0}
    pairs.append((L, Lx))
print(f"{len(pairs)} launches (Sep 12-15, drawn at random among the clean ones) rebuilt on the exact block clock")
print(f"{'enter at':>8s} {'interpolated clock':>19s} {'EXACT clock':>12s} {'win exact':>9s}")
for t in (0.2, 0.3, 0.4, 0.5, 0.7):
    a = [e0(L, t, 2, 0.5) for L, Lx in pairs]; b = [e0(Lx, t, 2, 0.5) for L, Lx in pairs]
    print(f"{t:7.1f}s {100*st.mean(a):+18.1f}% {100*st.mean(b):+11.1f}% {100*sum(x>0 for x in b)/len(b):8.0f}%")
