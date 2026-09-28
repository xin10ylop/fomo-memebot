"""Q3b: the 19:44:59 0x057d1ffe skip "nonce/gas not fresh (RPC)". In engine 6.7 the gate is `state["nonce"] is None or chain_at older
than 30 s` (line 1942). release_reservation() (line 1664) sets nonce None and chain_at 0 after EVERY burst that ends without a fill
(the gate never opened, line 2053; a guard revert, 2132; no fill, 2097; the aim skip, 1870), so the next launch is refused until
chain_loop's next successful read (sleep CHAIN_POLL_S = 3 s between reads; longer when a read fails or the every-100th pass runs
refresh_shooters and the ETH price fetch). 19:44:51 0x2c38692a (fleets [0, 2, 5], a gate refusal live) released 8 s before
0x057d1ffe. Engine 6.8 (committed during this review) raises 30 -> 60 s and retries a failed read in 2 s: neither touches the
release path. On the week: how many eligible launches follow a release closely enough to be refused, and what they are worth."""
import sys, time; sys.path.insert(0, "."); from common import *
V = {v: load_view(v) for v in ("k2", "k1reg", "kreg")}
for view in ("k2", "k1reg", "kreg"):
    R = sorted([r for r in V[view].values() if eligible(r)], key=lambda r: r["T0"])
    exp_n = 0.0; exp_usd = 0.0; hits = []
    for i, b in enumerate(R):
        # the latest release before b's gate check (b's check at T0+0.5 s; a refusal releases at T0+1.0 s, a guard revert at T0+2.5 s)
        rel = [a["T0"] + (2.5 if a["why"] == "GUARD no fill" else 1.0) for a in R[:i] if a["why"] != "FILL" and a["T0"] < b["T0"]]
        if not rel: continue
        g = b["T0"] + 0.5 - max(rel)
        if g <= 0 or g > 12: continue
        p = max(0.0, 1 - g / 3.2)                                     # the normal loop: the next read uniformly within 3.2 s of the release
        u = usd(b) if b.get("fired") else 0.0
        exp_n += p * (1 if b.get("fired") else 0); exp_usd += p * (u or 0.0)
        hits.append((b["T0"], b["cv"], g, p, b.get("fired"), u))
    fires12 = [h for h in hits if h[4]]
    print(f"view {view}: {len(hits)} eligible launches within 12 s of a release ({len(fires12)} of them fires, ${sum(h[5] or 0 for h in fires12):+.2f}); "
          f"expected refused by the normal 3 s loop: {exp_n:.2f} fires, ${exp_usd:+.2f} on the week (178 h)")
    if view == "k1reg":
        for T0, cv, g, p, f, u in hits:
            print(f"   {time.strftime('%b %d %H:%M:%S', time.gmtime(T0))} {cv[:10]} {g:4.1f} s after a release  p(refused, normal loop) {p:.2f}  {'fire ' + format(u, '+.2f') if f else 'no fire'}")
