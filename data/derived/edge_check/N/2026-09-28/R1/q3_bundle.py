"""Q3a: the 12:52 0x98f4e88b skip "bundle 0 < 3". Replays the LIVE engine 6.7 (engine67.py = git show 34265b9:src/strategy/sniper_engine.py; the repo moved to 6.8 during this review)'s own watch_curve / fold_buy on the chain's rows of that launch
(every tx naming the curve, chain order = the feed's order), then counts the same failure on the whole week: an outsider's
transaction naming the curve that the feed shows before the third named buyer inside blocks b0..b0+9 closes the bundle
(fold_buy: `bundle_closed`), whatever happens to that transaction on the chain."""
import os, sys, time, collections; sys.path.insert(0, ".")
LIVE = {"SEND_MODULE": "", "PRIVATE_KEY": "", "LOG_PATH": os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine67_log.jsonl"), "SEAT": "E1", "ATTACK_MIN": "2", "TIER_MIN_BPS": "100", "TIER_MAX_BPS": "200", "BUNDLE_MIN": "3",
        "BUNDLE_MIN_ETH": "0.3", "BUNDLE_MAX_ETH": "3.0", "MIN_CREATOR_SUPPLY": "0.01", "MAX_CREATOR_BUY_ETH": "2", "HOLD_BLOCKS": "9", "BURST_SLIP": "0.20", "BURST_N": "35",
        "STAKE_MIN": "13", "STAKE_MAX": "13", "WALLET": "0xe0686dc72b04c12ceefeea75e286e4ef7c056f01", "RELAY": "0xe8e98c3514d5bd83fdd01360896f2382b861a720"}
for k, v in LIVE.items(): os.environ[k] = v
from common import *
HERE_ = os.path.dirname(os.path.abspath(__file__)); os.chdir(ROOT); sys.path.insert(0, HERE_); import engine67 as E
C = crowd()
def engine_bundle(r, outsider_value):
    """the engine's w['bundle'] from watch_curve on the rows the feed had shown (all rows of blocks 0..k+1, in chain order)"""
    cv = r["cv"].lower(); named = set(a.lower() for a in r["named"]); creator = r["creator"].lower(); ts0 = 1_700_000_000; blk0 = 1000
    E.state["valtx"].clear(); E.state["buys"].clear(); E.state["sells"].clear(); E.state["watch"].clear(); seen = 0.0
    for off, rows in enumerate(r["blocks"]):
        for t in sorted(rows, key=lambda t: t.get("ix", 0)):
            if t["fr"] in US or t["to"] in US or t["to_token"]: continue
            seen += 0.001; ts = ts0 if off <= r["k"] else ts0 + 1; fr = t["fr"]
            outsider = not t["named_fr"]
            if t["direct"]:
                if t["sel"][2:] == E.BUY_SEL.hex(): E.state["buys"][cv].append((ts, fr, 0.01, seen, blk0 + off, cv, t["sel"][2:]))
                continue
            val = (0.01 if outsider_value else 0.0) if outsider else 0.03
            if val <= 0: continue
            data = bytes.fromhex(t["sel"][2:]) + b"\0" * 12 + bytes.fromhex(cv[2:]) + (b"".join(b"\0" * 12 + bytes.fromhex(a[2:]) for a in named) if t["named_data"] else b"")
            E.state["valtx"].append([seen, ts, fr, val, data, b"", blk0 + off, t["to"], t["sel"][2:]])
    w = E.watch_curve(cv, 1e7, ts0, named, creator, blk0=blk0, tax_bps=200)
    return w["bundle"], w.get("bundle_closed", False)
r = C["0x98f4e88b30c2e0acd1dfb6723502c6d93376ea48"]
print("12:52 0x98f4e88b, block 2 in chain order:", [("OUT " if not t["named_fr"] else "named ") + t["to"][:10] for t in sorted(r["blocks"][2], key=lambda t: t["ix"])][:4], "...")
for ov in (True, False):
    b, closed = engine_bundle(r, ov)
    print(f"  engine watch_curve, outsider's tx {'carries value (valtx)' if ov else 'carries no value (not recorded)'}: bundle {b}, closed {closed}")
V = {v: load_view(v) for v in ("k2", "k1reg", "kreg")}
print("\nthe week (Sep 21 09:40 - Sep 28 21:00): launches that reach the crowd gate in the replay, the engine's bundle count on the chain's rows")
out = collections.defaultdict(list)
for cv, x in V["k1reg"].items():
    if not eligible(x) or cv not in C: continue
    r = C[cv]; bA, _ = engine_bundle(r, True); bB, _ = engine_bundle(r, False)
    cls = "ok" if bA >= 3 else ("closed by a direct buy" if bB < 3 else "closed by a value tx")
    out[cls].append(cv)
for cls, cvs in out.items():
    line = f"  {cls:24s} {len(cvs):4d} launches"
    for v in ("k2", "k1reg", "kreg"):
        f = [V[v][c] for c in cvs if V[v][c].get("fired")]
        u = [usd(y) for y in f if usd(y) is not None]
        fp = collections.Counter(period(y["T0"]) for y in f)
        line += f" | {v}: {len(f)} fires (fit {fp['fit']}, read {fp['read']}) ${sum(u):+.2f}"
    print(line)
print("\nfires at risk (usual view):")
for cls in ("closed by a value tx", "closed by a direct buy"):
    for c in sorted(out[cls], key=lambda c: V["k1reg"][c]["T0"]):
        y = V["k1reg"][c]
        if y.get("fired"): print(f"  {cls:22s} {time.strftime('%b %d %H:%M', time.gmtime(y['T0']))} {c[:10]} {y['why']:14s} h11 {y['ret']['11']:+.1%}  ${usd(y):+.2f}")
print("\nwhat engine 6.8 (no close) adds over 6.7 on these launches, $ at 0.20 by period (fit 2.59 days, read 4.85 days):")
for v in ("k2", "k1reg", "kreg"):
    s = {}
    for p in ("fit", "read"):
        f = [V[v][c] for cls in ("closed by a value tx", "closed by a direct buy") for c in out[cls] if V[v][c].get("fired") and period(V[v][c]["T0"]) == p]
        u = [usd(y) for y in f if usd(y) is not None]; s[p] = (len(f), sum(u), sum(u) / days(p))
    print(f"  {v:6s} fit {s['fit'][0]} fires ${s['fit'][1]:+.2f} (${s['fit'][2]:+.2f}/day) | read {s['read'][0]} fires ${s['read'][1]:+.2f} (${s['read'][2]:+.2f}/day)")
