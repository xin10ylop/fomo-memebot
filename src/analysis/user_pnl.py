#!/usr/bin/env python3
"""Realized P&L of every fomo-app wallet in a window (report section 17).

Wallet universe: userOp senders from pull_userops.py. Each wallet's transactions are joined by hash to the Pons V2 curve
Buy/Sell events, every Uniswap v4 Swap (pools priced through v4init_all.json + the day's v4init) and every Uniswap v3
Swap (pool token0/token1 fetched once by eth_call and cached in rh/v3pools.json). A trade is priced when one side of
the pool is a known quote asset (native ETH / WETH / USDG / stock tokens with a price in token_metrics.json).
Per wallet and token: quote spent and received in USD, tokens in and out, entry and exit times, pool age at entry.
Positions opened before the window (sells without buys) are excluded from the realized number and reported apart.
Writes rh/user_pnl_{DAY}.json and prints ranked tables.

usage: python3 user_pnl.py DAY H0 H1 [--rpc]   (run from the data root)
"""
import json, glob, sys, os, bisect, collections, itertools, statistics as st, urllib.request, time, datetime

DAY = sys.argv[1]; H0 = int(sys.argv[2]); H1 = int(sys.argv[3])
HERE = os.path.dirname(os.path.abspath(__file__))
RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fomo-memebot/user-pnl"}
NATIVE = "0x" + "0" * 40; WETH = "0x0bd7d308f8e1639fab988df18a8011f41eacad73"
tm = json.load(open(os.path.join(HERE, "..", "..", "data", "derived", "token_metrics.json")))
DEC = {NATIVE: 18, "native": 18, WETH: 18, "0x5fc5360d0400a0fd4f2af552add042d716f1d168": 6, "0xc1a0957594a80aa55a12e76ae4cdf513e84301c7": 6}
PX = {NATIVE: 2445.0, "native": 2445.0, WETH: 2445.0, "0x5fc5360d0400a0fd4f2af552add042d716f1d168": 1.0, "0xc1a0957594a80aa55a12e76ae4cdf513e84301c7": 1.0}
TICKERS = {"NVDA", "MU", "AAPL", "TSLA", "GME", "AMC", "SPCX", "DJT", "HIMS", "COST", "MSTR", "TSM", "SLV", "GOOGL", "MSFT", "AMZN", "META", "HOOD", "COIN", "PLTR", "AMD", "INTC", "NFLX", "SPY", "QQQ", "GLD", "USDC", "USDT"}
for a, v in tm.items():
    if v.get("chain") == "robinhood" and v.get("symbol") in TICKERS and v.get("price"):
        PX[a.lower()] = float(v["price"]); DEC.setdefault(a.lower(), 18)
QUOTES = set(PX)
FIXED_Q = {NATIVE, "native", WETH, "0x5fc5360d0400a0fd4f2af552add042d716f1d168", "0xc1a0957594a80aa55a12e76ae4cdf513e84301c7"}


def usd(raw, q):
    px = PX.get(q)
    return raw / 10 ** DEC.get(q, 18) * px if px else None


blocks = {}
for f in glob.glob("rh/blocks/blocks*.json"):
    try:
        blocks.update(json.load(open(f)))
    except Exception:
        pass
pts = sorted((int(k, 16), v) for k, v in blocks.items()); xs = [p[0] for p in pts]; ys = [p[1] for p in pts]


def bts(b):
    i = bisect.bisect_left(xs, b)
    if i <= 0:
        return ys[0] - (xs[0] - b) / 9.9
    if i >= len(xs):
        return ys[-1] + (b - xs[-1]) / 9.9
    x0, y0, x1, y1 = xs[i - 1], ys[i - 1], xs[i], ys[i]; return y0 + (y1 - y0) * (b - x0) / (x1 - x0)


def call(batch):
    for i in range(6):
        try:
            req = urllib.request.Request(RPC, data=json.dumps(batch).encode(), headers=H); return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception:
            time.sleep(3 * (i + 1))
    return []


# wallets and their txs
ops = [json.loads(l) for l in open(f"rh/userops_{DAY}_{H0}-{H1}.jsonl")]
tx_sender = {}; multi = set()
for b, tx, s, ok in ops:
    if tx in tx_sender and tx_sender[tx] != s:
        multi.add(tx)
    tx_sender[tx] = s
for tx in multi:
    tx_sender.pop(tx, None)
txs = set(tx_sender)
print(f"wallets {len(set(tx_sender.values()))}, txs {len(txs)} (dropped {len(multi)} multi-sender bundles)", file=sys.stderr)

# curve tokens created today
creates = {}; curve_of_tok = {}
for line in open(f"rh/creates_v2_{DAY}.jsonl"):
    b, tx, topics, data = json.loads(line)
    if len(topics) < 4:
        continue
    cv = "0x" + topics[2][-40:].lower(); tok = "0x" + topics[1][-40:].lower(); creates[cv] = {"tok": tok, "b": b}; curve_of_tok[tok] = cv
quotes = json.load(open(f"rh/launch_quotes_{DAY}.json"))
# v4 pools
pools4 = {}
for src in (f"rh/v4init_{DAY}.json", "rh/v4init_all.json"):
    try:
        d = json.load(open(src)); d = d["pools"] if isinstance(d, dict) else d
        for x in d:
            pools4[x["pid"].lower()] = (x["c0"].lower(), x["c1"].lower(), x["b"])
    except Exception as e:
        print("pool meta", src, e, file=sys.stderr)
print(f"v4 pools known {len(pools4)}", file=sys.stderr)

# quote assets beyond ETH/WETH/USDG: currencies that sit on >= 8 distinct pools (stock tokens, AI, PONS, ...), priced at the
# median of the day's own swaps against a fixed quote (cached per day)
qp_f = f"rh/quote_prices_{DAY}.json"
if os.path.exists(qp_f):
    derived = json.load(open(qp_f))
else:
    npools = collections.Counter()
    for pid, (c0, c1, ib) in pools4.items():
        npools[c0] += 1; npools[c1] += 1
    v3meta0 = json.load(open("rh/v3pools.json")) if os.path.exists("rh/v3pools.json") else {}
    for pl, (c0, c1) in v3meta0.items():
        npools[c0] += 1; npools[c1] += 1
    cand = {c for c, n in npools.items() if n >= 60 and c not in FIXED_Q}
    series = collections.defaultdict(list)
    for line in itertools.chain.from_iterable(open(p) for p in sorted(glob.glob(f"rh/v4swaps_{DAY}.p*.jsonl"))):
        try:
            b, li, tx, pid, a0, a1, sp, liq = json.loads(line)
        except Exception:
            continue
        m = pools4.get(pid.lower())
        if not m:
            continue
        c0, c1, ib = m
        for cq, ct, aq, at in ((c0, c1, a0, a1), (c1, c0, a1, a0)):
            if cq in FIXED_Q and ct in cand and aq and at:
                u = usd(abs(aq), "native" if cq == NATIVE else cq)
                if u and abs(at) > 0:
                    series[ct].append(u / (abs(at) / 1e18))
    v3f0 = f"rh/v3swaps_{DAY}_{H0}-{H1}.jsonl"
    if os.path.exists(v3f0):
        for line in open(v3f0):
            b, li, tx, pool, a0, a1, sp, liq, tick = json.loads(line)
            m = v3meta0.get(pool)
            if not m:
                continue
            c0, c1 = m
            for cq, ct, aq, at in ((c0, c1, a0, a1), (c1, c0, a1, a0)):
                if cq in FIXED_Q and ct in cand and aq and at:
                    u = usd(abs(aq), cq)
                    if u and abs(at) > 0:
                        series[ct].append(u / (abs(at) / 1e18))
    derived = {}
    for c, v in series.items():
        if len(v) < 10:
            continue
        v.sort(); med = v[len(v) // 2]
        if med > 0 and v[len(v) // 10] > 0.7 * med and v[9 * len(v) // 10] < 1.4 * med:   # a quote asset has a stable price across its pools
            derived[c] = {"price": med, "n": len(v), "n_pools": npools[c]}
    json.dump(derived, open(qp_f, "w"))
for c, v in derived.items():
    PX[c] = v["price"]; DEC.setdefault(c, 18)
QUOTES = set(PX)
print(f"quote assets: {len(QUOTES)} ({len(derived)} priced from the day's swaps)", file=sys.stderr)

# events per user tx; last price per token from the whole stream
trades = collections.defaultdict(list)   # tx -> [(token, quote, quote_raw_delta(+recv/-paid), token_raw_delta, block, pool_age_s or None)]
last_px = {}                              # token -> (block, usd per token unit)
unpriced_pools = collections.Counter()


def note_px(tok, q, qraw, traw, b):
    if traw and qraw:
        u = usd(abs(qraw), q)
        if u:
            last_px[tok] = (b, u / (abs(traw) / 1e18))


for line in open(f"rh/v2curve_{DAY}_{H0}-{H1 - 1}.jsonl") if os.path.exists(f"rh/v2curve_{DAY}_{H0}-{H1 - 1}.jsonl") else open(f"rh/v2curve_{DAY}_12-18.jsonl"):
    b, li, tx, addr, t0, data = json.loads(line)
    cv = addr.lower(); m = creates.get(cv)
    if not m:
        continue
    d = data[2:]; w = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]; buy = t0 == "0xec36bf57"
    q = quotes.get(cv, "native"); q = "native" if q == "native" else q.lower()
    qraw, traw = (w[0], w[1]) if buy else (w[1], w[0])
    note_px(m["tok"], q, qraw, traw, b)
    if tx in txs:
        age = bts(b) - bts(m["b"])
        trades[tx].append((m["tok"], q, -qraw if buy else qraw, traw if buy else -traw, b, age))
print(f"curve done; user txs with curve trades {sum(1 for t in trades)}", file=sys.stderr)

for line in itertools.chain.from_iterable(open(p) for p in sorted(glob.glob(f"rh/v4swaps_{DAY}.p*.jsonl"))):
    try:
        b, li, tx, pid, a0, a1, sp, liq = json.loads(line)
    except Exception:
        continue
    m = pools4.get(pid.lower())
    if not m:
        if tx in txs:
            unpriced_pools["v4 unknown pool"] += 1
        continue
    c0, c1, ib = m
    if c0 in QUOTES and c1 not in QUOTES:
        q, tok, qd, td = c0, c1, a0, a1
    elif c1 in QUOTES and c0 not in QUOTES:
        q, tok, qd, td = c1, c0, a1, a0
    elif c0 in QUOTES and c1 in QUOTES:
        if c0 in FIXED_Q and c1 in FIXED_Q:
            continue                                       # currency conversion, not a trade
        q, tok, qd, td = (c0, c1, a0, a1) if (c0 in FIXED_Q or (c1 not in FIXED_Q and derived.get(c0, {}).get("n_pools", 0) >= derived.get(c1, {}).get("n_pools", 0))) else (c1, c0, a1, a0)
    else:
        if tx in txs:
            unpriced_pools["v4 no quote side"] += 1
        continue
    q = "native" if q == NATIVE else q
    note_px(tok, q, qd, td, b)
    if tx in txs:
        trades[tx].append((tok, q, qd, td, b, bts(b) - bts(ib)))     # v4: positive delta = user received
print(f"v4 done; user txs with trades {len(trades)}", file=sys.stderr)

v3f = f"rh/v3swaps_{DAY}_{H0}-{H1}.jsonl"
if os.path.exists(v3f):
    v3meta_f = "rh/v3pools.json"; v3meta = json.load(open(v3meta_f)) if os.path.exists(v3meta_f) else {}
    need = set()
    for line in open(v3f):
        b, li, tx, pool, a0, a1, sp, liq, tick = json.loads(line)
        if tx in txs and pool not in v3meta:
            need.add(pool)
    need = sorted(need); print(f"v3 pools to resolve {len(need)}", file=sys.stderr)
    for i in range(0, len(need), 25):
        ch = need[i:i + 25]; batch = []
        for j, p in enumerate(ch):
            batch.append({"jsonrpc": "2.0", "id": 2 * j, "method": "eth_call", "params": [{"to": p, "data": "0x0dfe1681"}, "latest"]})
            batch.append({"jsonrpc": "2.0", "id": 2 * j + 1, "method": "eth_call", "params": [{"to": p, "data": "0xd21220a7"}, "latest"]})
        r = call(batch); got = {}
        for x in r:
            res = x.get("result")
            if res and len(res) >= 42:
                got[x["id"]] = "0x" + res[-40:]
        for j, p in enumerate(ch):
            if 2 * j in got and 2 * j + 1 in got:
                v3meta[p] = [got[2 * j].lower(), got[2 * j + 1].lower()]
        time.sleep(0.2)
    json.dump(v3meta, open(v3meta_f, "w"))
    for line in open(v3f):
        b, li, tx, pool, a0, a1, sp, liq, tick = json.loads(line)
        m = v3meta.get(pool)
        if not m:
            continue
        c0, c1 = m
        if c0 in QUOTES and c1 not in QUOTES:
            q, tok, qd, td = c0, c1, -a0, -a1
        elif c1 in QUOTES and c0 not in QUOTES:
            q, tok, qd, td = c1, c0, -a1, -a0
        elif c0 in QUOTES and c1 in QUOTES:
            if c0 in FIXED_Q and c1 in FIXED_Q:
                continue                                   # currency conversion, not a trade
            q, tok, qd, td = (c0, c1, -a0, -a1) if (c0 in FIXED_Q or (c1 not in FIXED_Q and derived.get(c0, {}).get("n_pools", 0) >= derived.get(c1, {}).get("n_pools", 0))) else (c1, c0, -a1, -a0)
        else:
            if tx in txs:
                unpriced_pools["v3 no quote side"] += 1
            continue
        q = "native" if q == NATIVE else q
        note_px(tok, q, qd, td, b)
        if tx in txs:
            trades[tx].append((tok, q, qd, td, b, None))             # v3: pool deltas negated = user deltas
    print(f"v3 done; user txs with trades {len(trades)}", file=sys.stderr)
print("unpriced user swaps:", dict(unpriced_pools), file=sys.stderr)

# per wallet, per token
users = collections.defaultdict(lambda: collections.defaultdict(lambda: {"spent": 0.0, "recv": 0.0, "tk_in": 0.0, "tk_out": 0.0, "n_buy": 0, "n_sell": 0, "buys": [], "sells": [], "age0": None, "unpriced": 0}))
for tx, evs in trades.items():
    w = tx_sender[tx]
    for tok, q, qd, td, b, age in evs:
        p = users[w][tok]; u = usd(abs(qd), q)
        if u is None:
            p["unpriced"] += 1; continue
        t = bts(b)
        if qd < 0:
            p["spent"] += u; p["tk_in"] += td / 1e18; p["n_buy"] += 1; p["buys"].append((t, u))
            if p["age0"] is None:
                p["age0"] = age
        else:
            p["recv"] += u; p["tk_out"] += -td / 1e18; p["n_sell"] += 1; p["sells"].append((t, u))
rows = []
for w, toks in users.items():
    closed = []; open_ = []; pre = 0.0; spent = 0.0; recv = 0.0; sizes = []; holds = []; ages = []; mark = 0.0; mark0 = 0.0
    for tok, p in toks.items():
        if p["tk_in"] <= 0:
            pre += p["recv"]; continue
        spent += p["spent"]; recv += p["recv"]; sizes += [u for t, u in p["buys"]]
        if p["age0"] is not None:
            ages.append(p["age0"])
        rem = max(0.0, p["tk_in"] - p["tk_out"])
        frac = min(1.0, p["tk_in"] / p["tk_out"]) if p["tk_out"] > 0 else 1.0   # share of sold tokens that were bought in the window
        recv_in = p["recv"] * frac; pre += p["recv"] - recv_in; recv += recv_in - p["recv"]
        if p["tk_out"] >= 0.9 * p["tk_in"]:
            closed.append(recv_in - p["spent"])
            t_first_buy = min(t for t, u in p["buys"]); later = [t for t, u in p["sells"] if t >= t_first_buy]
            if later:
                holds.append(st.median(later) - t_first_buy)
        else:
            lp = last_px.get(tok); v = rem * lp[1] if lp else 0.0
            open_.append(recv_in + v - p["spent"]); mark += v
    if not sizes:
        continue
    rows.append({"wallet": w, "n_tokens": len(toks), "n_tx": sum(1 for tx, e in trades.items() if tx_sender[tx] == w), "spent": spent, "recv": recv, "closed_n": len(closed), "closed_pnl": sum(closed), "closed_win": (sum(1 for x in closed if x > 0) / len(closed)) if closed else None,
                 "open_n": len(open_), "open_pnl_marked": sum(open_), "total_unsold0": recv - spent, "total_marked": recv + mark - spent, "pre_window_sells": pre, "median_buy": st.median(sizes), "hold_med_s": st.median(holds) if holds else None, "age_med_s": st.median(ages) if ages else None,
                 "share_age_lt_1h": (sum(1 for a in ages if a < 3600) / len(ages)) if ages else None, "share_age_lt_10m": (sum(1 for a in ages if a < 600) / len(ages)) if ages else None})
json.dump({"rows": rows, "detail": {w: {tok: {k: v for k, v in p.items() if k not in ("buys", "sells")} | {"buys": p["buys"][:50], "sells": p["sells"][:50]} for tok, p in toks.items()} for w, toks in users.items()}}, open(f"rh/user_pnl_{DAY}_{H0}-{H1}.json", "w"))
n = len(rows); print(f"\nwallets with priced buys: {n}; total spent ${sum(r['spent'] for r in rows):,.0f}, received ${sum(r['recv'] for r in rows):,.0f}, net (unsold=0) ${sum(r['total_unsold0'] for r in rows):,.0f}, net marked ${sum(r['total_marked'] for r in rows):,.0f}")
pos = sum(1 for r in rows if r["total_marked"] > 0); print(f"wallets net positive (marked): {pos} ({100 * pos / n:.0f}%); with >= 5 closed positions: {sum(1 for r in rows if r['closed_n'] >= 5)}; closed-positive with >= 5 closed: {sum(1 for r in rows if r['closed_n'] >= 5 and r['closed_pnl'] > 0)}")


def win_s(r):
    return "n/a" if r["closed_win"] is None else "%.0f%%" % (100 * r["closed_win"])


def age_s(r):
    return "n/a" if r["share_age_lt_10m"] is None else "%.0f%%" % (100 * r["share_age_lt_10m"])


def table(title, rs):
    print(f"\n{title}\n{'wallet':12s} {'tokens':>6s} {'txs':>4s} {'spent $':>9s} {'closed n':>8s} {'closed $':>9s} {'win':>4s} {'open n':>6s} {'open $ mkd':>10s} {'total mkd $':>11s} {'unsold=0 $':>10s} {'med buy $':>9s} {'hold med':>8s} {'age med':>8s} {'<10m':>5s}")
    for r in rs:
        f = lambda x, d=0: "n/a" if x is None else (f"{x:.{d}f}")
        print(f"{r['wallet'][:12]} {r['n_tokens']:6d} {r['n_tx']:4d} {r['spent']:9,.0f} {r['closed_n']:8d} {r['closed_pnl']:9,.0f} {win_s(r):>4s} {r['open_n']:6d} {r['open_pnl_marked']:10,.0f} {r['total_marked']:11,.0f} {r['total_unsold0']:10,.0f} {r['median_buy']:9,.0f} {f(r['hold_med_s'] and r['hold_med_s'] / 60) + 'm':>8s} {f(r['age_med_s'] and r['age_med_s'] / 60) + 'm':>8s} {age_s(r):>5s}")


table("top 25 wallets by realized P&L on positions closed inside the window (>= 3 closed)", sorted([r for r in rows if r["closed_n"] >= 3], key=lambda r: -r["closed_pnl"])[:25])
table("top 25 wallets by total P&L with open positions marked at last price", sorted(rows, key=lambda r: -r["total_marked"])[:25])
table("consistent: >= 5 closed, win rate >= 60%, closed P&L > 0, total (unsold=0) > 0, sorted by closed P&L", sorted([r for r in rows if r["closed_n"] >= 5 and (r["closed_win"] or 0) >= 0.6 and r["closed_pnl"] > 0 and r["total_unsold0"] > 0], key=lambda r: -r["closed_pnl"])[:40])
