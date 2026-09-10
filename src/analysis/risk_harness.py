#!/usr/bin/env python3
"""Verification harness for the risk-management research (report section 23). Loads every window once (cached as a pickle
in the data root), then evaluates a configuration on every launch that passes the base rule, per window: mean ROI, the
one-position-at-a-time net at $300 stakes, the compounding path from $300 with the engine's defaults on the window's own
ordering, and the resampled probability of the -50% daily stop (1,000 shuffles of ALL the window's rule-passing trades,
no switch, exactly as sniper_plan.py does; an earlier version resampled only the trades its own path had taken, which
biased the odds by the path's outcome). Split: the seven earliest windows (FIT) and the seven later ones (TEST).

A configuration is a dict: hold, frac, lat, slip, tol, min_out_slip, stop_sell_frac, no_follow, take_profit (sell when the
curve price is up this fraction over our entry price, 0.3 s after it is seen), skip_fn (features -> True to skip),
size_fn (features -> stake multiplier), sizing (fraction of bankroll), clamp (stake floor, cap), daily_stop, switch_n,
switch, stakes (the stake grid), paths.
usage: python3 risk_harness.py [--build] [suite]   (from the data root)
"""
import sys, os, json, pickle, random, statistics as st, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sniper_exact as SE, sniper_core as C
PX = C.PX["native"]; Y0 = SE.Y0; X0 = SE.X0; GAS_ETH = SE.GAS_ETH
WINS = [("2026-08-12", "12-18"), ("2026-08-20", "12-18"), ("2026-08-27", "12-18"), ("2026-08-30", "12-18"), ("2026-08-31", "12-18"), ("2026-09-01", "12-18"),
        ("2026-09-02", "12-18"), ("2026-09-03", "0-6"), ("2026-09-03", "12-18"), ("2026-09-03", "18-24"), ("2026-09-04", "12-18"), ("2026-09-05", "0-6"),
        ("2026-09-05", "12-18"), ("2026-09-06", "12-18")]
FIT = set(WINS[:7]); TEST = set(WINS[7:])
CACHE = "risk_harness_cache_v2.pkl"; CACHE_NEW = "risk_harness_cache_new_v2.pkl"     # v2: every bundled launch, the second-one gate applied per configuration


def new_windows():
    """windows pulled after the round-15 rule was fixed (any rh/v2curve_<day>_<h0>-<h1>.jsonl not in WINS): never used for a choice"""
    import glob, re
    out = []
    for f in sorted(glob.glob("rh/v2curve_*.jsonl")):
        m = re.match(r"rh/v2curve_(\d{4}-\d{2}-\d{2})_(\d+-\d+)\.jsonl$", f)
        if m and (m.group(1), m.group(2)) not in WINS:
            out.append((m.group(1), m.group(2)))
    return out
STAKES = (25, 50, 100, 200, 300)


def features(L):
    """pre-entry observables plus the seat's timing. Row times are interpolated block times relative to the creation's own
    interpolated time, so pos_create (the creation's position inside its whole second) and rival_lag (how long after the
    T+2 boundary the first outsider of that second landed) are both derived from the same clock."""
    tier = L["tier"]; rows = L["rows"]
    first_taxed = next((r[0] for r in rows[1:] if r[1] == "B" and r[5] - tier > 0.001), None)
    bundle = [r for r in rows[1:] if r[1] == "B" and r[0] < min(1.0, first_taxed if first_taxed is not None else 9e9) and r[5] - tier <= 0.0008]
    rival = next((r[0] for r in rows[1:] if r[1] == "B" and r[0] <= 3.0 and 0.0012 <= r[5] - tier <= 0.0035), None)
    pos = L["ts"] % 1.0
    return dict(tier=tier, tk0=rows[0][3] / Y0, q0=rows[0][2], bundle_n=len(bundle), bundle_eth=sum(r[2] for r in bundle),
                bundle_max_share=max((r[3] / Y0 for r in bundle), default=0.0),
                team1_eth=sum(r[2] for r in rows[1:] if r[1] == "B" and 1.0 <= r[0] < 2.0 and r[5] - tier <= 0.0008),
                out1_n=sum(1 for r in rows[1:] if r[1] == "B" and 0.05 <= r[5] - tier <= 0.075),
                hour=(L["ts"] % 86400) / 3600, first_taxed_t=first_taxed, pos_create=pos, rival_t=rival,
                rival_lag=(rival - (2.0 - pos)) if rival is not None else None)


def build(wins=WINS, cache=CACHE):
    data = {}
    for day, win in wins:
        SE.WINDOW = win
        try:
            launches, prior = SE.load_exact(day)
        except FileNotFoundError:
            continue
        keep = {}
        for cv, L in launches.items():
            if prior[L["creator"]][0] != L["ts"]:
                continue
            f = features(L)
            if f["bundle_n"] >= 3 and f["bundle_eth"] >= 0.3 and f["tk0"] >= 0.01:
                keep[cv] = (L, f)
        data[(day, win)] = keep; print("loaded", day, win, len(keep), file=sys.stderr)
    pickle.dump(data, open(cache, "wb")); return data


def load_new():
    """the new windows, cached separately; rebuilt when a window is missing from the cache"""
    wins = new_windows()
    if not wins:
        return {}
    data = pickle.load(open(CACHE_NEW, "rb")) if os.path.exists(CACHE_NEW) and "--build-new" not in sys.argv else {}
    if any(k not in data for k in wins):
        data = build(wins, CACHE_NEW)
    return data


def load():
    if os.path.exists(CACHE) and "--build" not in sys.argv:
        data = pickle.load(open(CACHE, "rb"))
        f = next((f for k in data for cv, (L, f) in data[k].items()), {})
        if "pos_create" in f:
            return data
    return build()


def replay(L, stake_eth, frac=0.03, hold=7.0, entry="E2", tol=0.10, lat=0.3, slip=0.3, stop_sell_frac=None, no_follow=None, min_out_slip=0.25, tp=None):
    """sniper_exact.replay (same code path, checked equal for tp=None) plus a take-profit: when the curve price after an
    event is up tp over our entry price, we sell slip seconds later; everything landing before that sell still applies."""
    rows = L["rows"]; tier = L["tier"]; X, Y = X0, Y0
    t, k, q, tk, net, tax = rows[0]; X += net; Y -= tk
    target, lo, hi, fb = {"E0": (0.0, -1.0, 0.0008, 0.1), "E1": (0.0618, 0.05, 0.075, 1.0), "E2": (0.0019, 0.0012, 0.0035, 2.0)}[entry]
    idx = None
    for i in range(1, len(rows)):
        r = rows[i]
        if r[1] == "B" and r[0] <= 3.0 and lo <= r[5] - tier <= hi:
            idx = i; break
    if idx is None:
        idx = next((i for i in range(1, len(rows)) if rows[i][0] >= fb), len(rows)); t_entry = fb
    else:
        t_entry = rows[idx][0]
    idx_seat = idx
    if lat > 0:
        t_entry += lat; idx = next((i for i in range(1, len(rows)) if rows[i][0] >= t_entry), len(rows))
    for r in rows[1:idx]:
        if r[1] == "B":
            X += r[4]; Y -= r[3]
        else:
            X -= r[4]; Y += r[3]
    fee = tier + target
    if min_out_slip is not None and lat > 0:
        Xs, Ys = X0 + rows[0][4], Y0 - rows[0][3]
        for r in rows[1:idx_seat]:
            if r[1] == "B":
                Xs += r[4]; Ys -= r[3]
            else:
                Xs -= r[4]; Ys += r[3]
        if (X / Y) > (Xs / Ys) * (1 + min_out_slip):
            return -GAS_ETH, 1e-9, t_entry, t_entry, "reverted"
    tk_bot = frac * Y0
    net = X * tk_bot / (Y - tk_bot); gross = net / (1 - fee)
    if gross > stake_eth:
        gross = stake_eth; net = gross * (1 - fee); tk_bot = Y * net / (X + net)
    X += net; Y -= tk_bot; t_in = t_entry; t_exit = t_in + hold + slip; followed = False; p_in = X / Y
    held = Y0 - Y - tk_bot; phantom = 0.0
    for r in rows[idx:]:
        t, k, q, tk, net_obs, tax = r
        if no_follow is not None and not followed and t > t_in + no_follow:
            t_exit = t_in + no_follow; break
        if t >= t_exit:
            break
        if k == "S" and stop_sell_frac is not None and tk >= stop_sell_frac * Y0 and t_exit > t + slip:
            t_exit = t + slip
        if k == "B":
            followed = True
            tokens = Y - X * Y / (X + net_obs)
            if tol is not None and tokens < tk * (1 - tol):
                phantom += tk; continue
            X += net_obs; Y -= tokens; held += tokens
        else:
            share = held / (held + phantom) if held + phantom > 0 else 1.0
            s = min(tk * share, held); g = X - X * Y / (Y + s); X -= g; Y += s; held -= s; phantom = max(0.0, phantom - (tk - s))
        if tp is not None and X / Y >= p_in * (1 + tp) and t_exit > t + slip:
            t_exit = t + slip
    out = (X - X * Y / (Y + tk_bot)) * (1 - tier)
    return out - gross, gross, t_in, t_exit, "ok"


def check_replay(data, n=300):
    """the local replay must equal sniper_exact.replay when no take-profit is set"""
    random.seed(3); bad = 0; tot = 0
    for k in data:
        for cv, (L, f) in list(data[k].items())[:n // len(data) + 1]:
            for stk in (50, 300):
                a = SE.replay(L, stk / PX, frac=0.03, hold=7.0, entry="E2", tol=0.10, lat=0.3, slip=0.3, min_out_slip=0.25)
                b = replay(L, stk / PX)
                tot += 1
                if abs(a[0] - b[0]) > 1e-12 or abs(a[1] - b[1]) > 1e-12 or a[4] != ("reverted" if b[4] == "reverted" else a[4]):
                    bad += 1
    return bad, tot


def trade_book(cfg, data):
    """per window: list of per-launch dicts {stake: (pnl_usd, cost_usd, t_in_abs, t_out_abs, kind)} plus the features"""
    kw = dict(frac=cfg.get("frac", 0.03), hold=cfg.get("hold", 7.0), entry=cfg.get("entry", "E2"), tol=cfg.get("tol", 0.10), slip=cfg.get("slip", 0.3), lat=cfg.get("lat", 0.3),
              min_out_slip=cfg.get("min_out_slip", 0.25), stop_sell_frac=cfg.get("stop_sell_frac"), no_follow=cfg.get("no_follow"), tp=cfg.get("take_profit"))
    stakes = cfg.get("stakes", STAKES); book = {}
    for k, keep in data.items():
        trades = []
        for cv, (L, f) in keep.items():
            if f["out1_n"] > 0 and not cfg.get("include_out1"):                # the section 21.6 gate: no outsider in second one
                continue
            if cfg.get("skip_fn") and cfg["skip_fn"](f):
                continue
            mult = cfg["size_fn"](f) if cfg.get("size_fn") else 1.0
            if mult <= 0:
                continue
            by = {}
            for stk in stakes:
                pnl, cost, t_in, t_out, kind = replay(L, stk * mult / PX, **kw)
                by[stk] = (pnl * PX - (C.GAS if kind != "reverted" else 0.0), cost * PX if kind != "reverted" else 1e-9, L["ts"] + t_in, L["ts"] + t_out, kind)
            trades.append((by, f))
        book[k] = trades
    return book


def evaluate(cfg, data, book=None):
    sizing = cfg.get("sizing", 0.2); clamp = cfg.get("clamp", (50.0, 300.0)); stop = cfg.get("daily_stop", 0.50); n_sw = cfg.get("switch_n", 15); thr = cfg.get("switch", -0.10)
    stakes = cfg.get("stakes", STAKES); start = float(cfg.get("start", 300.0)); book = book or trade_book(cfg, data); out = {}
    for k, trades in book.items():
        if len(trades) < 10:
            out[k] = None; continue
        rows = [t[0][300] for t in trades]; taken = [r for r in rows if r[4] != "reverted"]; v = [r[0] / r[1] for r in taken]
        seq = sorted(range(len(trades)), key=lambda i: trades[i][0][300][2]); busy = -1e9; net1 = 0.0
        for i in seq:
            r = trades[i][0][300]
            if r[2] >= busy:
                net1 += r[0]; busy = r[3]
        # the window's own ordering with the engine's defaults: switch on every rule-passing launch, one position at a time, daily stop
        bank = start; busy = -1e9; scored = []; stopped = False; n_taken = 0
        for i in seq:
            r = trades[i][0][300]; t_in = r[2]
            avail = [x[1] for x in scored if x[0] <= t_in]; on = len(avail) < n_sw or st.mean(avail[-n_sw:]) >= thr
            scored.append((r[3] + 20.0, r[0] / r[1] if r[1] > 1e-6 else 0.0))
            if bank < (1 - stop) * start:
                stopped = True
            if not on or t_in < busy or stopped or bank < clamp[0]:
                continue
            stake = min(max(bank * sizing, clamp[0]), min(clamp[1], bank)); near = min(stakes, key=lambda s_: abs(s_ - stake)); rr = trades[i][0][near]
            dep = min(stake, rr[1]) if rr[1] > 1e-6 else 0.0; bank += dep * (rr[0] / rr[1]) if rr[1] > 1e-6 else rr[0]; busy = rr[3]; n_taken += 1
        own = bank
        # resampled orderings of ALL the window's trades (sniper_plan.py's method): no switch, stop at -50%
        random.seed(7); stops = 0; ends = []; idx = list(range(len(trades)))
        for _ in range(cfg.get("paths", 1000)):
            random.shuffle(idx); bank = start; stopped = False
            for i in idx:
                if bank < (1 - stop) * start:
                    stopped = True; break
                stake = min(max(bank * sizing, clamp[0]), min(clamp[1], bank)); near = min(stakes, key=lambda s_: abs(s_ - stake)); rr = trades[i][0][near]
                bank += (min(stake, rr[1]) * (rr[0] / rr[1]) if rr[1] > 1e-6 else rr[0])
            ends.append(bank); stops += stopped
        ends.sort()
        out[k] = dict(n=len(rows), refused=len(rows) - len(taken), roi=st.mean(v) if v else 0.0, tail=sum(1 for x in v if x < -0.4) / max(1, len(v)), net1=net1, own=own, n_taken=n_taken,
                      med=ends[len(ends) // 2], p10=ends[len(ends) // 10], pstop=stops / len(ends))
    return out


def evaluate_adaptive(cfg, data, classes=("clean", "out1"), n_roll=20, thr=0.03, start=300.0):
    """the engine's switch per class of launch ('clean' = no outsider in second one, 'out1' = one present; seat rivals are
    always skipped): every bundled launch is scored 20 s after its exit, in the window's own time order, and a class is
    traded only while the mean of its last n_roll scores is at least thr (trade until proven bad: fewer than n_roll scores
    counts as on). Returns per window: trades taken per class, mean ROI of taken trades, own-path end from start."""
    kw = dict(frac=cfg.get("frac", 0.03), hold=cfg.get("hold", 5.0), tol=0.10, slip=0.3, lat=0.3, min_out_slip=0.25, tp=cfg.get("take_profit"))
    sizing = cfg.get("sizing", 0.15); clamp = cfg.get("clamp", (25.0, 300.0)); stop = 0.50; stakes = cfg.get("stakes", STAKES); out = {}
    for k, keep in data.items():
        rows = []
        for cv, (L, f) in keep.items():
            if G_WAIT(0.3)(f):
                continue
            cls = "out1" if f["out1_n"] > 0 else "clean"
            by = {}
            for stk in stakes:
                pnl, cost, t_in, t_out, kind = replay(L, stk / PX, **kw)
                by[stk] = (pnl * PX - (C.GAS if kind != "reverted" else 0.0), cost * PX if kind != "reverted" else 1e-9, L["ts"] + t_in, L["ts"] + t_out, kind)
            rows.append((by, cls))
        if len(rows) < 10:
            out[k] = None; continue
        rows.sort(key=lambda r: r[0][300][2]); bank = start; busy = -1e9; scored = {"clean": [], "out1": []}; stopped = False; taken = {"clean": [], "out1": []}
        for by, cls in rows:
            r = by[300]; t_in = r[2]
            avail = [x[1] for x in scored[cls] if x[0] <= t_in]; on = cls in classes and (len(avail) < n_roll or st.mean(avail[-n_roll:]) >= thr)
            scored[cls].append((r[3] + 20.0, r[0] / r[1] if r[1] > 1e-6 else 0.0))
            if bank < (1 - stop) * start:
                stopped = True
            if not on or t_in < busy or stopped or bank < clamp[0]:
                continue
            stake = min(max(bank * sizing, clamp[0]), min(clamp[1], bank)); near = min(stakes, key=lambda s_: abs(s_ - stake)); rr = by[near]
            dep = min(stake, rr[1]) if rr[1] > 1e-6 else 0.0; roi = (rr[0] / rr[1]) if rr[1] > 1e-6 else 0.0; bank += dep * roi if rr[1] > 1e-6 else rr[0]; busy = rr[3]; taken[cls].append(roi)
        out[k] = dict(n=len(rows), own=bank, taken={c: (len(v), st.mean(v) if v else 0.0) for c, v in taken.items()},
                      clsroi={c: (sum(1 for by, cl in rows if cl == c), st.mean([by[300][0] / by[300][1] for by, cl in rows if cl == c and by[300][1] > 1e-6] or [0.0])) for c in ("clean", "out1")})
    return out


def print_adaptive(res, label, start=300.0):
    print(f"{label}: per window, launches scored per class (clean = no second-one outsider, out1 = one present; seat rivals skipped), mean ROI per class, trades taken per class with their mean, own-path end from ${start:.0f}")
    tot = 0.0
    for k in sorted(res):
        r = res[k]
        if not r:
            continue
        tot += r["own"] - start
        print(f"   {k[0][5:]} {k[1]:5s} clean {r['clsroi']['clean'][0]:3d} {100*r['clsroi']['clean'][1]:+6.1f}%  out1 {r['clsroi']['out1'][0]:3d} {100*r['clsroi']['out1'][1]:+6.1f}%  | taken clean {r['taken']['clean'][0]:3d} ({100*r['taken']['clean'][1]:+5.1f}%) out1 {r['taken']['out1'][0]:3d} ({100*r['taken']['out1'][1]:+5.1f}%) | end {r['own']:7,.0f}")
    print(f"   sum of gains over the windows: {tot:,.0f}"); sys.stdout.flush()


def summarize(res, label, per_window=False, start=300.0):
    def agg(keys):
        r = [res[k] for k in keys if res.get(k)]
        if not r:
            return "n/a"
        n = sum(x["n"] for x in r)
        return (f"n {n:4d} ROI {100*sum(x['roi']*x['n'] for x in r)/n:+5.1f}% worst {100*min(x['roi'] for x in r):+5.1f}% tail {100*sum(x['tail']*x['n'] for x in r)/n:4.1f}% "
                f"net1 {sum(x['net1'] for x in r):7,.0f} own {sum(x['own']-start for x in r):7,.0f} P(stop) {100*st.mean(x['pstop'] for x in r):4.1f}% max {100*max(x['pstop'] for x in r):3.0f}% +win {sum(1 for x in r if x['roi']>0)}/{len(r)}")
    print(f"{label:44s} FIT  {agg([k for k in res if k in FIT])}")
    print(f"{'':44s} TEST {agg([k for k in res if k in TEST])}")
    if any(k not in FIT and k not in TEST for k in res):
        print(f"{'':44s} NEW  {agg([k for k in res if k not in FIT and k not in TEST])}")
    if per_window:
        for k in sorted(res):
            r = res[k]
            if r:
                print(f"   {k[0][5:]} {k[1]:5s} n={r['n']:3d} ROI {100*r['roi']:+5.1f}% tail {100*r['tail']:3.0f}% net1 {r['net1']:7,.0f} own {r['own']:6,.0f} ({r['n_taken']:3d} trades) med {r['med']:6,.0f} p10 {r['p10']:5,.0f} P(stop) {100*r['pstop']:3.0f}%")
    sys.stdout.flush()


def table_2d(data, hold, label):
    """mean ROI at $300 by the creation's position in its second x the first outsider's lag behind the T+2 boundary"""
    pb = [(0.0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 1.01)]
    lb = [("none", None), ("<0.10", (-9, 0.10)), ("0.10-0.30", (0.10, 0.30)), ("0.30-0.60", (0.30, 0.60)), (">=0.60", (0.60, 9))]
    for half, keys in (("FIT", FIT), ("TEST", TEST)):
        cells = collections.defaultdict(list)
        for k in data:
            if k not in keys:
                continue
            for cv, (L, f) in data[k].items():
                pnl, cost, t_in, t_out, kind = replay(L, 300 / PX, hold=hold)
                if kind == "reverted":
                    continue
                pi = next(i for i, (a, b) in enumerate(pb) if a <= f["pos_create"] < b)
                li = 0 if f["rival_lag"] is None else next(i for i, (nm, rg) in enumerate(lb) if rg and rg[0] <= f["rival_lag"] < rg[1])
                cells[(pi, li)].append(pnl / cost)
        print(f"{label} hold {hold} {half}: rows = creation position in its second, columns = first outsider's lag behind the T+2 boundary (n, mean ROI, share < -40%)")
        print(f"{'':12s}" + "".join(f"{nm:>22s}" for nm, _ in lb))
        for pi, (a, b) in enumerate(pb):
            print(f"{a:.2f}-{b:.2f}   " + "".join((f"{len(c):4d} {100*st.mean(c):+6.1f}% {100*sum(1 for x in c if x<-0.4)/len(c):3.0f}%   " if (c := cells.get((pi, li), [])) else f"{'-':>22s}") for li in range(len(lb))))
        allc = [x for (pi, li), c in cells.items() for x in c]
        print(f"   all: n {len(allc)} mean {100*st.mean(allc):+.1f}%")
    sys.stdout.flush()


G_NE = lambda f: f["first_taxed_t"] is not None and f["first_taxed_t"] < 2.0            # Opus: skip if the first surcharged buy is stamped before 2.0 s
G_FIRSTBLOCK = lambda f: f["rival_lag"] is not None and f["rival_lag"] < 0.10           # skip if an outsider sits in the first block of T+2 (visible before a react send)
G_RIVAL = lambda f: f["rival_t"] is not None                                            # skip if any outsider takes the seat (look-ahead: reference only)


def G_WAIT(w):
    """the executable form: wait w seconds into the seat's second watching the feed; send only if no outsider has bought"""
    return lambda f: f["rival_lag"] is not None and f["rival_lag"] < w


def suite(name, data):
    if name == "check":
        print("replay equality vs sniper_exact.replay (bad, total):", check_replay(data))
        pos = [f["pos_create"] for k in data for cv, (L, f) in data[k].items()]
        print("creation position in its second: deciles", [round(x, 2) for x in st.quantiles(pos, n=10)])
        lags = [f["rival_lag"] for k in data for cv, (L, f) in data[k].items() if f["rival_lag"] is not None]
        print(f"first outsider lag behind the T+2 boundary: n {len(lags)} of {len(pos)}, deciles", [round(x, 3) for x in st.quantiles(lags, n=10)])
        return
    if name == "table":
        table_2d(data, 7.0, "E2 0.3 s behind"); table_2d(data, 5.0, "E2 0.3 s behind"); return
    cfgs = {
        "base": [("baseline: hold 7, 20%/$50", {})],
        "hold": [("hold 6", {"hold": 6.0}), ("hold 5", {"hold": 5.0}), ("hold 4", {"hold": 4.0})],
        "tp": [("hold 7 + take-profit +50%", {"take_profit": 0.5}), ("hold 5 + take-profit +50%", {"hold": 5.0, "take_profit": 0.5}), ("hold 5 + take-profit +35%", {"hold": 5.0, "take_profit": 0.35}),
               ("hold 7 + take-profit +60%", {"take_profit": 0.6})],
        "size": [("hold 5, 15%/$25", {"hold": 5.0, "sizing": 0.15, "clamp": (25.0, 300.0)}), ("hold 5 + TP 50%, 15%/$25", {"hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0)}),
                 ("hold 7, 15%/$25", {"sizing": 0.15, "clamp": (25.0, 300.0)}), ("hold 5, 20%/$25", {"hold": 5.0, "clamp": (25.0, 300.0)})],
        "gate": [("gate NE (Opus), hold 7", {"skip_fn": G_NE}), ("gate NE, hold 5", {"skip_fn": G_NE, "hold": 5.0}), ("gate NE, hold 4", {"skip_fn": G_NE, "hold": 4.0}),
                 ("gate first-block rival, hold 7", {"skip_fn": G_FIRSTBLOCK}), ("gate first-block rival, hold 5", {"skip_fn": G_FIRSTBLOCK, "hold": 5.0}),
                 ("gate any rival (look-ahead), hold 7", {"skip_fn": G_RIVAL}), ("gate any rival (look-ahead), hold 5", {"skip_fn": G_RIVAL, "hold": 5.0}),
                 ("gate creation late in second (>0.5), hold 7", {"skip_fn": lambda f: f["pos_create"] > 0.5}), ("gate creation late in second (>0.5), hold 5", {"skip_fn": lambda f: f["pos_create"] > 0.5, "hold": 5.0}),
                 ("gate first-block rival + TP 50%, hold 5", {"skip_fn": G_FIRSTBLOCK, "hold": 5.0, "take_profit": 0.5}),
                 ("gate first-block rival, hold 5, 15%/$25", {"skip_fn": G_FIRSTBLOCK, "hold": 5.0, "sizing": 0.15, "clamp": (25.0, 300.0)})],
        "final": [("FINAL: wait 0.3 s, hold 5, TP 50%, 15%/$25", {"skip_fn": G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0)}),
                  ("FINAL at 20%/$50", {"skip_fn": G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5}),
                  ("FINAL without the take-profit", {"skip_fn": G_WAIT(0.3), "hold": 5.0, "sizing": 0.15, "clamp": (25.0, 300.0)})],
        "new": [("baseline: hold 7, 20%/$50", {}), ("hold 5, 20%/$50", {"hold": 5.0}), ("wait 0.3 s, hold 5, 20%/$50", {"skip_fn": G_WAIT(0.3), "hold": 5.0}),
                ("FINAL: wait 0.3 s, hold 5, TP 50%, 15%/$25", {"skip_fn": G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0)}),
                ("FINAL at 20%/$50", {"skip_fn": G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5}),
                ("FINAL from $100", {"skip_fn": G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0), "start": 100})],
        "classes": [("FINAL (clean launches only)", {"skip_fn": G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0)}),
                    ("all bundled launches (second-one outsider allowed), wait 0.3 s, hold 5, TP 50%", {"skip_fn": G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0), "include_out1": True}),
                    ("only launches with a second-one outsider, wait 0.3 s, hold 5, TP 50%", {"skip_fn": lambda f: G_WAIT(0.3)(f) or f["out1_n"] == 0, "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0), "include_out1": True}),
                    ("E1 seat at the front (first in second one), all bundled, hold 5, TP 50%", {"entry": "E1", "lat": 0.0, "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0), "include_out1": True}),
                    ("E1 seat one block behind (0.1 s), all bundled, hold 5, TP 50%", {"entry": "E1", "lat": 0.1, "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0), "include_out1": True}),
                    ("E1 seat 0.3 s behind, all bundled, hold 5, TP 50%", {"entry": "E1", "lat": 0.3, "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0), "include_out1": True}),
                    ("E1 seat at the front, all bundled, hold 7, no TP", {"entry": "E1", "lat": 0.0, "hold": 7.0, "sizing": 0.15, "clamp": (25.0, 300.0), "include_out1": True})],
        "switch": [("FINAL, switch 15/-10% (default)", {"skip_fn": G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0)}),
                   ("FINAL, switch 30/+3%", {"skip_fn": G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0), "switch_n": 30, "switch": 0.03}),
                   ("FINAL, switch 30/+5%", {"skip_fn": G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0), "switch_n": 30, "switch": 0.05}),
                   ("FINAL, switch 20/+5%", {"skip_fn": G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0), "switch_n": 20, "switch": 0.05}),
                   ("FINAL 20%/$50, switch 30/+5%", {"skip_fn": G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "switch_n": 30, "switch": 0.05})],
        "start": [(f"FINAL from ${s0}", {"skip_fn": G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0), "start": s0}) for s0 in (50, 100, 150, 200)],
        "wait": [(f"wait {w:.1f} s for a rival, hold {h:.0f}", {"skip_fn": G_WAIT(w), "hold": h}) for w in (0.2, 0.3, 0.4, 0.5) for h in (7.0, 5.0)]
                + [("wait 0.3 s, hold 5, 15%/$25", {"skip_fn": G_WAIT(0.3), "hold": 5.0, "sizing": 0.15, "clamp": (25.0, 300.0)}),
                   ("wait 0.3 s, hold 5 + TP 50%", {"skip_fn": G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5}),
                   ("wait 0.3 s, hold 5 + TP 50%, 15%/$25", {"skip_fn": G_WAIT(0.3), "hold": 5.0, "take_profit": 0.5, "sizing": 0.15, "clamp": (25.0, 300.0)}),
                   ("wait 0.3 s, hold 4", {"skip_fn": G_WAIT(0.3), "hold": 4.0}), ("wait 0.3 s, hold 6", {"skip_fn": G_WAIT(0.3), "hold": 6.0})],
    }
    if name == "adaptive":
        for label, kw in (("adaptive: both classes, roll 20, on while >= +3%", dict(n_roll=20, thr=0.03)), ("adaptive: both classes, roll 20, on while >= 0%", dict(n_roll=20, thr=0.0)),
                          ("adaptive: both classes, roll 30, on while >= +3%", dict(n_roll=30, thr=0.03)), ("clean class only, roll 20, on while >= +3%", dict(classes=("clean",), n_roll=20, thr=0.03)),
                          ("static: clean class always on", dict(classes=("clean",), n_roll=10**9, thr=-9)), ("static: both classes always on", dict(n_roll=10**9, thr=-9))):
            print_adaptive(evaluate_adaptive({"take_profit": 0.5}, data, **kw), label)
        return
    for label, cfg in cfgs[name]:
        summarize(evaluate(cfg, data), label, per_window=("--windows" in sys.argv), start=float(cfg.get("start", 300.0)))


if __name__ == "__main__":
    names = [a for a in sys.argv[1:] if not a.startswith("--")] or ["check", "base"]
    data = load_new() if names == ["new"] else load()
    if "new" in names and names != ["new"]:
        data = dict(data); data.update(load_new())
    for nm in names:
        suite(nm, data)
