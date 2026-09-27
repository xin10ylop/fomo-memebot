"""dollars.py (edge_check/F), task 5: $ a day at $13 at the recent supply, 0.32 fires an hour (7.68 bursts a day), for the settings
S = 15 (today), 334 (the fit's choice), 8 (the recent's choice = the recommendation), and 240 / 300 for reference; each setting's sell
lands at S+2..S+4 (each fire averaged over the three). Full fill: every burst fills at second place. Live mix: half the bursts fill,
a filled burst lands second two times in three and third one time in three (n_ahead 2); gas $0.33 on every burst. Returns per set:
recent (19 fires) and fit (73 fires). The weekly spread is the per-burst sd times sqrt(53.8 bursts).
    python3 data/derived/edge_check/F/dollars.py > data/derived/edge_check/F/dollars.txt"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from load import *
RATE = 0.32 * 24; FILL = 0.5; THIRD = 1 / 3
def landed(P): L = np.full_like(P, np.nan); L[:, :1197] = (P[:, 2:1199] + P[:, 3:1200] + P[:, 4:1201]) / 3; return L
L2, L3 = landed(P2), landed(P3)
print(f"{RATE:.2f} bursts a day; $13 stake; gas $0.33 a burst")
print(f"{'setting':>8s} {'returns of':>10s} {'2nd':>7s} {'3rd':>7s} {'$/burst full':>12s} {'$/day full':>10s} {'$/burst mix':>11s} {'$/day mix':>9s} {'$/week mix':>10s} {'wk sd':>6s}")
for S in (15, 334, 8, 240, 300):
    for s in ("rec", "fit"):
        f = mask(s) & FIRE; usd_eff = G[f] * E; r2 = L2[f][:, S]; r3 = L3[f][:, S]
        full = r2 * usd_eff - GAS
        # live mix per burst: a mixture draw; its mean and sd from the per-fire values (unfilled bursts cost the gas)
        mix_mean = FILL * np.mean(((1 - THIRD) * r2 + THIRD * r3) * usd_eff) - GAS
        ex2 = FILL * ((1 - THIRD) * np.mean((r2 * usd_eff - GAS) ** 2) + THIRD * np.mean((r3 * usd_eff - GAS) ** 2)) + (1 - FILL) * GAS ** 2
        sd_mix = np.sqrt(ex2 - mix_mean ** 2)
        print(f"{S:8d} {s:>10s} {r2.mean():+7.1%} {r3.mean():+7.1%} {full.mean():+12.2f} {full.mean()*RATE:+10.2f} {mix_mean:+11.2f} {mix_mean*RATE:+9.2f} {mix_mean*RATE*7:+10.1f} {sd_mix*np.sqrt(RATE*7):6.1f}")
