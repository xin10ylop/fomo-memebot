"""tmpl_variants.py (verifier VI): causal template filters with other linkage (share 1/2/3, min 3/5/10) scored in $/day
on fit and rec (h11) and rec+late (h15), engine and tables.   python3 data/derived/edge_check/VI/tmpl_variants.py"""
import sys
sys.path.insert(0, "/home/user/fomo-memebot/data/derived/edge_check/I"); import common as c
P = c.load(); H = {p: c.period_hours(p) for p in ("fit", "rec", "rec+late")}
for share in (1, 2, 3):
    for mn in (3, 5, 10):
        F, _ = c.template_flags(P, share=share, min_n=mn)
        row = []
        for pop in ("engine", "tables"):
            for h, per in ((11, "fit"), (11, "rec"), (15, "fit"), (15, "rec+late")):
                fs = c.fires(pop, per); b = c.stats(fs, h, H[per])["day"]; k = c.stats([d for d in fs if not F[d["cv"]]], h, H[per])["day"]
                row.append(f"{k - b:+6.2f}")
        print(f"share>={share} min>={mn:2d}: engine h11 fit/rec {row[0]}/{row[1]}  h15 fit/rec+late {row[2]}/{row[3]} | tables h11 fit/rec {row[4]}/{row[5]}  h15 fit/rec+late {row[6]}/{row[7]}")
