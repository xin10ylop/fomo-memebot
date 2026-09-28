"""Q5a: the team's own helper counted as a rival fleet. note_attack (engine 6.7 and 6.8) adds a call's target to the fleets whenever
the calldata does not list a named wallet, whoever sends it; the forward-sender bundle templates (a named wallet calling a helper
that buys in its name, 6.6) list none, so the helper contract is a 'fleet'. engine_replay counts the registration block with --reg,
which is exactly the block of those helper calls. Live, the helper calls of the registration block reach the feed BEFORE the curve is
watched (the bundle must be visible first), so note_attack never sees them; helper calls in later blocks it does see. Here: the
replay's count re-done with the named wallets' and the creator's own calls excluded, at the three views, and what moves."""
import sys, time, collections; sys.path.insert(0, "."); from common import *
C = crowd(); V = {v: load_view(v) for v in ("k2", "k1reg", "kreg")}
def fleets(r, upto, reg, drop_team):
    """engine_replay.fleets() logic on the rows: from the first named block (itself only with reg), direct non-team senders plus
    targets of non-direct calls whose calldata lists no named wallet; drop_team skips the team's own calls"""
    j = next((i for i, rw in enumerate(r["blocks"]) if any(t.get("named_fr") or t.get("named_data") for t in rw)), -1)
    tg, sd = set(), set()
    for off, rows in enumerate(r["blocks"][: upto + 1]):
        if off < j or (off == j and not reg): continue
        for t in rows:
            if t["to"] in US or t["fr"] in US or t["to_token"]: continue
            if t["direct"]:
                if not t["named_fr"]: sd.add(t["fr"])
            elif not t["named_data"]:
                if drop_team and t["named_fr"]: continue
                tg.add(t["to"])
    return len(tg) + len(sd)
views = {"k2": (-2, False), "k1reg": (-1, True), "kreg": (0, True)}
chk = collections.Counter()
for v, (d, reg) in views.items():
    moved = collections.defaultdict(list)
    for cv, r in V[v].items():
        if not eligible(r) or cv not in C: continue
        c = C[cv]; k = c["k"]; a = fleets(c, k + d, reg, False); b = fleets(c, k + d, reg, True)
        chk[(v, a == r.get("fleets"))] += 1
        if r.get("fired") and b < 2: moved[period(r["T0"])].append(r)
    print(f"view {v}: replay count reproduced on {chk[(v, True)]} of {chk[(v, True)] + chk[(v, False)]} eligible launches")
    for p in ("fit", "read"):
        fires = [x for x in V[v].values() if x.get("fired") and period(x["T0"]) == p]
        m = moved[p]; um = [usd(x) for x in m if usd(x) is not None]; ua = [usd(x) for x in fires if usd(x) is not None]
        keep = [u for x, u in zip(fires, ua) if x not in m]
        print(f"   {p:4s}: {len(m)} of {len(fires)} fires rest on the team's helper (without it < 2 fleets): ${sum(um):+.2f} ({sum(um) / days(p):+.2f}/day); "
              f"the other {len(keep)} fires ${sum(keep):+.2f} (mean ${st.mean(keep) if keep else 0:+.2f} a fire) vs helper-dependent mean ${st.mean(um) if um else 0:+.2f}")
    if v == "k1reg":
        today = sorted([x for x in moved["read"] if x["T0"] >= SWITCH], key=lambda x: x["T0"])
        print("   since 12:27 today: " + ", ".join(f"{time.strftime('%H:%M', time.gmtime(x['T0']))} {x['cv'][:10]} h11 {x['ret']['11']:+.1%}" for x in today))
