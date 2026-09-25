"""variants.py: the nine variants that met all five criteria in search.py (as printed by search.py), as rules."""
from common import BASE
def bundle_or(c, hi=True): return lambda r: BASE(r) or (r["f_k2"] == 1 and r["bundle_eth"] is not None and (r["bundle_eth"] >= c if hi else r["bundle_eth"] < c))
PASSED = [("BASE | (f@k-2==1 & bundle_eth<0.446)", bundle_or(0.445572476, False), "behind1_15_h300"),
          ("BASE | (f@k-2==1 & bundle_eth<0.446)", bundle_or(0.445572476, False), "behind1_15_h150"),
          ("BASE | (f@k-2==1 & bundle_eth>=1.5)", bundle_or(1.5), "behind1_15_h300"),
          ("BASE | (f@k-2==1 & bundle_eth>=1.0)", bundle_or(1.0), "behind1_15_h300"),
          ("BASE | (f@k-2==1 & bundle_eth>=0.836)", bundle_or(0.8355597830901723), "behind1_15_h300"),
          ("BASE & not creator repeat", lambda r: BASE(r) and not r["creator_repeat"], "behind1_15_h300"),
          ("BASE & relay fleets@k-2>=1", lambda r: BASE(r) and r["fr_k2"] >= 1, "behind1_15_h300"),
          ("BASE & maxshots@k-2>=3", lambda r: BASE(r) and r["maxshots_k2"] >= 3, "behind1_15_h300"),
          ("BASE | (f@k-2==1 & k<=5)", lambda r: BASE(r) or (r["f_k2"] == 1 and r["k"] <= 5), "behind1_15_h300")]

# stage 2 (extra.py section 4): every AND-filter x OR-branch pair among the fit-qualified components of search.py, all nine holds
from common import RET_KEYS
ANDS = {"not creator repeat": lambda r: not r["creator_repeat"], "relay fleets@k-2>=1": lambda r: r["fr_k2"] >= 1, "maxshots@k-2>=3": lambda r: r["maxshots_k2"] >= 3,
        "fleets>=1@k-3": lambda r: r["f_k3"] >= 1}
ORS = {"f==1 & bundle<0.446": lambda r: r["f_k2"] == 1 and r["bundle_eth"] < 0.445572476, "f==1 & bundle>=1.5": lambda r: r["f_k2"] == 1 and r["bundle_eth"] >= 1.5,
       "f==1 & bundle>=1.0": lambda r: r["f_k2"] == 1 and r["bundle_eth"] >= 1.0, "f==1 & bundle>=0.836": lambda r: r["f_k2"] == 1 and r["bundle_eth"] >= 0.8355597830901723,
       "f==1 & k<=5": lambda r: r["f_k2"] == 1 and r["k"] <= 5, "f==1 & named>=15": lambda r: r["f_k2"] == 1 and r["named"] >= 15,
       "f==1 & only h06-11": lambda r: r["f_k2"] == 1 and 6 <= r["hour"] <= 11, "f==0 & named<4": lambda r: r["f_k2"] == 0 and r["named"] < 4, "f<2 & named<4": lambda r: r["f_k2"] < 2 and r["named"] < 4}
# k >= 3: aimable (as in search.py)
STAGE2 = [(f"(BASE & {an}) | ({on})", (lambda af, of: lambda r: r["k"] >= 3 and ((BASE(r) and af(r)) or of(r)))(af, of), key) for an, af in ANDS.items() for on, of in ORS.items() for key in RET_KEYS[:9]]
