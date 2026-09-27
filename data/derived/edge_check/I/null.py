"""null.py (reviewer I): the null test of docs/REPORT.md 24.34 for every filter variant. A filter drops m_fit fires on the fit
and m_rec on the recent set; a random filter drops the same numbers of fires at random (2,000 draws, seed 11). The score is
the $ total of the kept fires after gas (at an equal count it orders the draws as the kept mean does; the mean is shown).
p_fit / p_rec = share of draws whose kept $ is >= the filter's on that period; p_both = share >= on BOTH periods at once.
Recent = rec (11 files + gaps; h11 and h15) and rec+late (with sep27pm/eve; h15 only).
    python3 data/derived/edge_check/I/null.py > data/derived/edge_check/I/null.txt"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
N = 2000; rng = random.Random(11); EPS = 1e-9
def kept_usd(fs, h): return sum(c.usd(d, h) for d in fs)
V = c.variants()
print(f"{'pop':7s} {'h':>3s} {'recent':9s} {'filter':12s} {'drop fit':>8s} {'drop rec':>8s}  {'fit mean kept':>13s} {'rec mean kept':>13s}  {'d$ fit':>7s} {'d$ rec':>7s}   p_fit  p_rec  p_both")
for pop in ("engine", "tables"):
    for h, rp in ((11, "rec"), (15, "rec"), (15, "rec+late")):
        Ff = c.fires(pop, "fit"); Fr = c.fires(pop, rp)
        for name, keep in V:
            if name == "none": continue
            kf = [d for d in Ff if keep(d)]; kr = [d for d in Fr if keep(d)]; mf = len(Ff) - len(kf); mr = len(Fr) - len(kr)
            of, orr = kept_usd(kf, h), kept_usd(kr, h)
            uf = [c.usd(d, h) for d in Ff]; ur = [c.usd(d, h) for d in Fr]; tf, tr = sum(uf), sum(ur)
            hf = hr = hb = 0
            for _ in range(N):
                a = tf - sum(rng.sample(uf, mf)) if mf else tf
                b = tr - sum(rng.sample(ur, mr)) if mr else tr
                A = a >= of - EPS; B = b >= orr - EPS; hf += A; hr += B; hb += A and B
            sf = c.stats(kf, h, 1); sr = c.stats(kr, h, 1)
            print(f"{pop:7s} {h:3d} {rp:9s} {name:12s} {mf:3d}/{len(Ff):3d} {mr:4d}/{len(Fr):3d}  {sf['mean']:+13.1%} {sr['mean']:+13.1%}  {of - tf:+7.2f} {orr - tr:+7.2f}   {hf/N:.3f}  {hr/N:.3f}  {hb/N:.3f}")
        print()
