#!/usr/bin/env python3
"""Week-by-week realized P&L of fomo-app wallets from their full on-chain histories (report section 17).

Input: rh/history/{wallet}.jsonl from pull_wallet_history.py (curve Buy/Sell, v4 Swap, v3 Swap events per wallet).
Pricing: the same rules as user_pnl.py. Quote assets = ETH/WETH/USDG plus the stock tokens and other currencies priced
in rh/quote_prices_{DAY}.json (day-derived; stock tokens barely move, AI/PONS-quoted pools are flagged). Curve events
map to tokens through rh/launches_all.json (venue ponsV2: t1 token, t2 curve) and to quote assets through the
creation receipts (fetched once per curve, cached in rh/curve_quotes.json). v3 pools are resolved by eth_call and
cached in rh/v3pools.json; v4 pools through rh/v4init_all.json.
Per wallet: FIFO round trips per token (a sell closes the oldest open buys), weekly realized P&L, trade counts,
win rate, hold times, entry ages (pool or curve age at first buy), trade sizes, venue mix, and the unsold remainder
marked at the wallet's last trade price for that token. Prints the consistency ranking and writes
data/derived/wallet_history_{tag}.json.

usage: python3 wallet_history_pnl.py DAY_FOR_QUOTES [tag] [wallet-list.json]   (run from the data root)
"""
import json, glob, sys, os, bisect, collections, statistics as st, urllib.request, time, datetime

HERE = os.path.dirname(os.path.abspath(__file__)); DAY = sys.argv[1]; TAG = sys.argv[2] if len(sys.argv) > 2 else DAY
RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fomo-memebot/history-pnl"}
NATIVE = "0x" + "0" * 40; WETH = "0x0bd7d308f8e1639fab988df18a8011f41eacad73"; TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
DEC = {NATIVE: 18, "native": 18, WETH: 18, "0x5fc5360d0400a0fd4f2af552add042d716f1d168": 6, "0xc1a0957594a80aa55a12e76ae4cdf513e84301c7": 6}
PX = {NATIVE: 2445.0, "native": 2445.0, WETH: 2445.0, "0x5fc5360d0400a0fd4f2af552add042d716f1d168": 1.0, "0xc1a0957594a80aa55a12e76ae4cdf513e84301c7": 1.0}
FIXED_Q = set(PX)
derived = json.load(open(f"rh/quote_prices_{DAY}.json"))
for c, v in derived.items():
    PX[c] = v["price"]; DEC.setdefault(c, 18)
QUOTES = set(PX)
VOLATILE_Q = {c for c in derived if derived[c]["n_pools"] < 2000 and c not in FIXED_Q}   # AI, PONS, CASHCAT-like quotes: price not constant over weeks


def usd(raw, q):
    px = PX.get(q); return raw / 10 ** DEC.get(q, 18) * px if px else None


def call(p):
    for i in range(6):
        try:
            req = urllib.request.Request(RPC, data=json.dumps(p).encode(), headers=H); return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception:
            time.sleep(3 * (i + 1))
    return None


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


# pool / curve metadata
pools4 = {}
for src in glob.glob("rh/v4init_*.json"):
    try:
        d = json.load(open(src)); d = d["pools"] if isinstance(d, dict) else d
        for x in d:
            pools4[x["pid"].lower()] = (x["c0"].lower(), x["c1"].lower(), x["b"])
    except Exception:
        pass
v3meta = json.load(open("rh/v3pools.json")) if os.path.exists("rh/v3pools.json") else {}
curves = {}
for x in json.load(open("rh/launches_all.json")):
    if x.get("venue") == "ponsV2":
        curves["0x" + x["t2"].lower()] = ("0x" + x["t1"].lower(), x["b"], x["tx"])
cq_f = "rh/curve_quotes.json"; curve_q = json.load(open(cq_f)) if os.path.exists(cq_f) else {}
for f in glob.glob(f"rh/launch_quotes_*.json"):
    for cv, q in json.load(open(f)).items():
        curve_q.setdefault(cv.lower(), q if q == "native" else q.lower())

files = sorted(glob.glob("rh/history/*.jsonl"))
if len(sys.argv) > 3:
    keep = {w.lower() for w in json.load(open(sys.argv[3]))}; files = [f for f in files if f.split("/")[-1][:-6] in keep]
events = {}
need_v3 = set(); need_cq = set()
for f in files:
    w = f.split("/")[-1][:-6]; ev = [json.loads(l) for l in open(f)]; events[w] = ev
    for b, tx, kind, addr, x, y in ev:
        if kind == "v3" and addr not in v3meta:
            need_v3.add(addr)
        if kind.startswith("curve") and addr in curves and addr not in curve_q:
            need_cq.add(addr)
need_v3 = sorted(need_v3); need_cq = sorted(need_cq)
print(f"wallets {len(events)}, v3 pools to resolve {len(need_v3)}, curve quotes to resolve {len(need_cq)}", file=sys.stderr)
for i in range(0, len(need_v3), 25):
    ch = need_v3[i:i + 25]; batch = []
    for j, p in enumerate(ch):
        batch += [{"jsonrpc": "2.0", "id": 2 * j, "method": "eth_call", "params": [{"to": p, "data": "0x0dfe1681"}, "latest"]}, {"jsonrpc": "2.0", "id": 2 * j + 1, "method": "eth_call", "params": [{"to": p, "data": "0xd21220a7"}, "latest"]}]
    r = call(batch) or []; got = {x["id"]: "0x" + x["result"][-40:] for x in r if x.get("result") and len(x["result"]) >= 42}
    for j, p in enumerate(ch):
        if 2 * j in got and 2 * j + 1 in got:
            v3meta[p] = [got[2 * j].lower(), got[2 * j + 1].lower()]
    time.sleep(0.2)
json.dump(v3meta, open("rh/v3pools.json", "w"))
for i in range(0, len(need_cq), 20):
    ch = need_cq[i:i + 20]
    r = call([{"jsonrpc": "2.0", "id": j, "method": "eth_getTransactionReceipt", "params": [curves[cv][2]]} for j, cv in enumerate(ch)]) or []
    for x in r:
        rc = x.get("result") or {}; cv = ch[x["id"]]; tok = curves[cv][0]; q = "native"
        for l in rc.get("logs", []):
            if l["topics"][0] == TRANSFER and len(l["topics"]) > 2 and ("0x" + l["topics"][2][-40:]).lower() == cv and l["address"].lower() != tok:
                q = l["address"].lower(); break
        curve_q[cv] = q
    time.sleep(0.2)
json.dump(curve_q, open(cq_f, "w"))

week = lambda ts: (datetime.datetime.utcfromtimestamp(ts) - datetime.timedelta(days=datetime.datetime.utcfromtimestamp(ts).weekday())).strftime("%m-%d")
out = {}; rows = []
for w, ev in events.items():
    ev.sort(key=lambda e: e[0])
    per = collections.defaultdict(lambda: {"lots": [], "closed": [], "buys": 0, "sells": 0, "spent": 0.0, "recv": 0.0, "age0": None, "venue": None, "last_px": None, "volatile_q": False})
    unpriced = 0; conv = 0
    for b, tx, kind, addr, x, y in ev:
        t = bts(b)
        if kind.startswith("curve"):
            m = curves.get(addr)
            if not m:
                unpriced += 1; continue
            tok, cb, ctx = m; q = curve_q.get(addr, "native"); buy = kind == "curve_buy"
            qraw, traw = (x, y) if buy else (y, x); u = usd(qraw, q)
            if u is None:
                unpriced += 1; continue
            qd = -u if buy else u; td = traw / 1e18 if buy else -traw / 1e18; age = t - bts(cb); venue = "curve"
        else:
            if kind == "v4":
                m = pools4.get(addr.lower())
                if not m:
                    unpriced += 1; continue
                c0, c1, ib = m; a0, a1 = x, y; sgn = 1; age_b = ib; venue = "v4"
            else:
                m = v3meta.get(addr)
                if not m:
                    unpriced += 1; continue
                c0, c1 = m; a0, a1 = x, y; sgn = -1; age_b = None; venue = "v3"
            if c0 in QUOTES and c1 not in QUOTES:
                q, tok, qa, ta = c0, c1, a0, a1
            elif c1 in QUOTES and c0 not in QUOTES:
                q, tok, qa, ta = c1, c0, a1, a0
            elif c0 in QUOTES and c1 in QUOTES:
                if c0 in FIXED_Q and c1 in FIXED_Q:
                    conv += 1; continue
                q, tok, qa, ta = (c0, c1, a0, a1) if (c0 in FIXED_Q or (c1 not in FIXED_Q and derived.get(c0, {}).get("n_pools", 0) >= derived.get(c1, {}).get("n_pools", 0))) else (c1, c0, a1, a0)
            else:
                unpriced += 1; continue
            qn = "native" if q == NATIVE else q; u = usd(abs(qa), qn)
            if u is None:
                unpriced += 1; continue
            qd = sgn * (u if qa > 0 else -u); td = sgn * ta / 1e18; age = (t - bts(age_b)) if age_b else None
            if q in VOLATILE_Q:
                per[tok]["volatile_q"] = True
        p = per[tok]; p["venue"] = p["venue"] or venue
        if td > 0 and qd < 0:      # buy
            p["lots"].append([td, -qd, t]); p["buys"] += 1; p["spent"] += -qd; p["last_px"] = -qd / td
            if p["age0"] is None:
                p["age0"] = age
        elif td < 0 and qd > 0:    # sell: FIFO against open lots
            amt = -td; proceeds = qd; p["sells"] += 1; p["recv"] += qd; p["last_px"] = qd / amt
            while amt > 1e-12 and p["lots"]:
                lot = p["lots"][0]; take = min(lot[0], amt); cost = lot[1] * take / lot[0]; pr = proceeds * take / (-td)
                p["closed"].append({"t_in": lot[2], "t_out": t, "cost": cost, "proceeds": pr, "pnl": pr - cost})
                lot[0] -= take; lot[1] -= cost; amt -= take
                if lot[0] <= 1e-12:
                    p["lots"].pop(0)
            # amt left over = sold tokens acquired outside the priced history (airdrop, transfer): ignored
    closed = [c for p in per.values() for c in p["closed"]]
    if not closed and not any(p["buys"] for p in per.values()):
        continue
    weekly = collections.defaultdict(float); wk_n = collections.Counter()
    for c in closed:
        weekly[week(c["t_out"])] += c["pnl"]; wk_n[week(c["t_out"])] += 1
    open_val = sum(sum(l[0] for l in p["lots"]) * (p["last_px"] or 0) for p in per.values()); open_cost = sum(sum(l[1] for l in p["lots"]) for p in per.values())
    spent = sum(p["spent"] for p in per.values()); recv = sum(p["recv"] for p in per.values())
    holds = [c["t_out"] - c["t_in"] for c in closed]; sizes = [c["cost"] for c in closed]
    ages = [p["age0"] for p in per.values() if p["age0"] is not None]
    wk = sorted(weekly); pos_w = sum(1 for k in wk if weekly[k] > 0)
    tok_pnl = {tok: sum(c["pnl"] for c in p["closed"]) for tok, p in per.items() if p["closed"]}
    top_tok = max(tok_pnl.values()) if tok_pnl else 0.0; realized = sum(closed_c["pnl"] for closed_c in closed)
    r = {"wallet": w, "n_events": len(ev), "unpriced": unpriced, "tokens": len(per), "closed_trips": len(closed), "realized": realized, "win_rate": (sum(1 for c in closed if c["pnl"] > 0) / len(closed)) if closed else None,
         "gross_profit": sum(c["pnl"] for c in closed if c["pnl"] > 0), "gross_loss": -sum(c["pnl"] for c in closed if c["pnl"] < 0), "top_token_share": (top_tok / realized) if realized > 0 else None,
         "weeks_active": len(wk), "weeks_positive": pos_w, "weekly": dict(weekly), "open_cost": open_cost, "open_marked": open_val, "spent": spent, "recv": recv,
         "hold_med_min": (st.median(holds) / 60) if holds else None, "hold_p25_min": (sorted(holds)[len(holds) // 4] / 60) if holds else None, "size_med": st.median(sizes) if sizes else None, "size_p90": (sorted(sizes)[9 * len(sizes) // 10]) if sizes else None,
         "age_med_min": (st.median(ages) / 60) if ages else None, "share_age_lt_10m": (sum(1 for a in ages if a < 600) / len(ages)) if ages else None, "share_age_lt_1h": (sum(1 for a in ages if a < 3600) / len(ages)) if ages else None,
         "venues": dict(collections.Counter(p["venue"] for p in per.values() if p["venue"])), "volatile_quote_tokens": sum(1 for p in per.values() if p["volatile_q"]), "first_t": bts(ev[0][0]), "last_t": bts(ev[-1][0])}
    rows.append(r); out[w] = {"summary": r, "tokens": {tok: {"closed": p["closed"], "buys": p["buys"], "sells": p["sells"], "spent": p["spent"], "recv": p["recv"], "age0": p["age0"], "venue": p["venue"], "open_tokens": sum(l[0] for l in p["lots"]), "open_cost": sum(l[1] for l in p["lots"]), "last_px": p["last_px"]} for tok, p in per.items()}}
json.dump(out, open(os.path.join(HERE, "..", "..", "data", "derived", f"wallet_history_{TAG}.json"), "w"))


def show(title, rs):
    print(f"\n{title}\n{'wallet':12s} {'trips':>5s} {'realized $':>10s} {'win':>4s} {'PF':>5s} {'top tok':>7s} {'wk act/pos':>10s} {'open cost/mkd $':>16s} {'hold med':>8s} {'size med':>8s} {'age med':>9s} {'<10m':>5s} {'venues':22s} weekly $")
    for r in rs:
        pf = (r["gross_profit"] / r["gross_loss"]) if r["gross_loss"] > 0 else float("inf")
        wk = " ".join(f"{k}:{v:+.0f}" for k, v in sorted(r["weekly"].items()))
        print(f"{r['wallet'][:12]} {r['closed_trips']:5d} {r['realized']:10,.0f} {('n/a' if r['win_rate'] is None else '%.0f%%' % (100 * r['win_rate'])):>4s} {pf:5.1f} {('n/a' if r['top_token_share'] is None else '%.0f%%' % (100 * r['top_token_share'])):>7s} {r['weeks_active']:4d}/{r['weeks_positive']:<5d} {r['open_cost']:7,.0f}/{r['open_marked']:8,.0f} {('n/a' if r['hold_med_min'] is None else '%.0fm' % r['hold_med_min']):>8s} {('n/a' if r['size_med'] is None else '%.0f' % r['size_med']):>8s} {('n/a' if r['age_med_min'] is None else '%.0fm' % r['age_med_min']):>9s} {('n/a' if r['share_age_lt_10m'] is None else '%.0f%%' % (100 * r['share_age_lt_10m'])):>5s} {str(r['venues'])[:22]:22s} {wk}")


rows.sort(key=lambda r: -r["realized"])
print(f"wallets scored {len(rows)}; realized total ${sum(r['realized'] for r in rows):,.0f}; positive {sum(1 for r in rows if r['realized'] > 0)}")
show("top 40 by realized P&L over the whole history (FIFO round trips)", rows[:40])
cons = [r for r in rows if r["closed_trips"] >= 20 and r["weeks_active"] >= 3 and r["weeks_positive"] >= 0.75 * r["weeks_active"] and r["realized"] >= 2000 and (r["top_token_share"] or 1) <= 0.5]
show("consistent: >= 20 round trips, >= 3 active weeks, >= 75% of weeks positive, realized >= $2k, no single token > 50% of it", sorted(cons, key=lambda r: -r["realized"]))
