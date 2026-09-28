# K1: more fills and a better P&L from the E1 sniper (Sep 28)

**Basis.** `engine_replay.py` run in-process, reproduced exactly: 632 launches, 0 disposition mismatches; at the usual view (k-1 with registration) 129 fires, 61 guard reverts, 68 fills, +$97.92 (`check.txt`). Tape pricing matches the grid (median difference 0.0000, 535 launches); guard inputs match exactly. **Fit** = Sep 21 09:40–Sep 23 (399 launches, 62.3 h); **read** = Sep 24–Sep 28 09:40 (233, 105.7 h). Default: second place, exit block 11, $13, $0.33 gas a burst. Position, exit and E2 use taped launches only (fit 363, read 172; nothing from Sep 27 evening on).

## Recommendation: BURST_SLIP 0.07 → 0.20. Nothing else changes.

## Q1. The guard

| slip | fit fills, mean, $ | read fills, mean, $ |
|---|---|---|
| 0.07 (live) | 37, +22.6%, **+82.6** | 31, +7.9%, **+15.3** |
| 0.10 | 41, +21.7%, +89.7 | 37, +10.6%, +34.6 |
| 0.15 | 66, +18.9%, +136.1 | 46, +12.4%, +57.6 |
| **0.20** | 71, +18.1%, **+141.1** | 49, +13.0%, **+66.4** |
| 0.30 | 78, +18.1%, +157.6 | 50, +12.6%, +65.1 |

- **Out of sample.** Chosen on fit: 0.30 → read +$65.1 (live +$15.3). Chosen on read: 0.20 → fit +$141.1 (live +$82.6). Same direction at the floor view (read +$1.1 → +$36.1) and the ceiling (+$5.3 → +$55.3).
- **The reverted bursts at second place:** fit 42 at +13.7% (median +2.2%); read 19 at **+20.2%** (median +11.5%, win 79%), above read's actual fills (+7.9%). At third place: +6.8% / +16.3%.
- **Why they revert.** In 46 of 48 taped reverts it is the buy ahead in E1: the creation second's late buys move the price a median 0.0% and alone exceed 7% twice. The buy ahead has a median of 0.21 ETH (0.02 ETH ahead of the fills). Three fixed-size first-in-E1 buyers account for 34 of the 48: `0x924378f2` (0.21 ETH, 15 reverts, drop about 14%), `0x6c56103c` (0.149 ETH, 14, about 10.5%) and `0x5051e45b` (0.5 ETH, 5). A 7% guard is a position filter that refuses the crowded launches that run, which is what 24.20 warned against.
- **Smarter guards read worse than a plain 20%:** loosening only when fleets ≥ 3 reads +$48.1 on read; sizing at the tick (only the buy ahead counts) reads +$45.0 at 15%.
- **Gas:** reverts cost $13.86 fit + $6.27 read; at 0.20, 9 reverts ($2.97). Every burst pays gas either way; the gain is the fills.
- **Safety:** a creation-second landing still reverts at any slip under ~90% (98% surcharge). The relay's `AlreadyBought` already prevents a double fill, so at $13 the guard has no double-fill role. Guard off (1.0) is unsafe.

**Attack on the position assumption.** Each row assumes every burst lands at that position; $ on taped fires.

| landing | 0.07 fit / read | 0.20 fit / read |
|---|---|---|
| first | +248.1 / +88.9 | +248.7 / +88.9 |
| second | +85.2 / +16.0 | +131.9 / +54.3 |
| third | +5.3 / −2.8 | +68.0 / +29.1 |
| last in E1 | −31.1 / −3.3 | **−46.8** / +4.4 |
| mix 25/45/15/15 | +96.5 / +28.5 | +124.7 / +51.7 |

- If every burst landed last, the change would lose $15.7 on fit. Any mix like the live landings (2 second, 1 first, 1 first in a later block, 1 last) gains on both halves.
- **Bootstrap of the gain:**
  - Read +$51.2 (90% +$25.5 to +$79.5, P≤0 of 0.000; 15/18 changed bursts positive).
  - Fit +$58.4 (+$14.5 to +$104.0, P≤0 of 0.014; only 17/34 positive, so winners carry it).
- **Weak point:** the gain sits on Sep 21–25, while those three buyers were active. On Sep 26–28 only 4 bursts change (+$6.47): too few to conclude.

## Q2. Filters (each off alone; value = $ on minus $ off)

| filter | removes (2nd place, fit / read) | fires it blocks | value fit / read |
|---|---|---|---|
| bundle cap 3.0 | 21 (−11.0% / −10.6%) | 7 / 8 | **+$10.9 / +$13.7**: keep |
| creator supply ≥ 1% | 148 (−9.2% / −5.0%) | 12 / 8 | +$12.0 / −$6.1: mixed, 5 read fills; keep |
| creator repeat | 17 | 3 / 0 | −$1.5 / 0: too small |
| bundle ≥ 3 buyers | 20 | 1 / 0 | −$0.4 / 0: too small |
| tier, bundle ≥ 0.3, creator buy ≤ 2 | 0 | – | untestable: population already inside |

Same ranking at a 20% guard.

## Q3. The gate (fit $ / read $)

| view | 7% guard, ≥1 | ≥2 | ≥3 | 20% guard, ≥2 | ≥3 |
|---|---|---|---|---|---|
| k-2 floor | 42 / 2 | 44 / 1 | 23 / 2 | 104 / 36 | 49 / 7 |
| k-1 usual | 45 / 4 | **83 / 15** | 50 / 9 | **141 / 66** | 104 / 42 |
| k ceiling | 6 / −16 | 75 / 5 | 77 / 26 | 120 / 55 | 147 / 61 |

- Two fleets is best at the usual view under both guards.
- At view k, three beats two on both halves. I do not propose it: the engine cannot know a block is k before E1, and it saw k on 1 of 8 live bursts.
- Extra conditions on top of two fleets (wallets, curve-aimed txs, growth from k-2 to k-1, the change from k-1 to k, bundle ETH, named wallets, k, hour, tier, creator supply), each chosen on one half and read on the other: none improves both halves under both guards. The best, hour ≥ 5, is +$4 / +$3 at 7%; at 20% the hour rule chosen on fit loses $8 on read.
- ETH per pending shot is not on disk.

## Q4. Position (fires at k-1, taped, exit 11)

| | first | second | third | fourth | last |
|---|---|---|---|---|---|
| fit (71) | +29.6% | +18.6% | +12.6% | +8.3% | −0.4% |
| read (32) | +23.9% | +15.3% | +10.8% | +9.2% | +4.0% |

- First to second costs 9–11 points; each later place 2–6.
- Behind a big buy, second place pays: behind 0.14–0.25 ETH, +12.8% (fit, 22) and +16.7% (read, 10); behind over 0.25 ETH, +21.3% (9) and +13.1% (3).
- The seat block's crowd matters more: with 2–3 other buys, −1.0% (20) and +12.8% (12); with 7 or more, +37.9% (23) and +37.6% (3).

## Q5. Exit

- **80 rules tested** at sell lags 2 and 4, on the 7% and the 20% fills: take-profit, stop, both combined, a sell on the seat-block buyers' first sell, a read at block 1–3, momentum. None beats the fixed exit at 11 on both halves in both fill sets.
- **Momentum** (hold to 30 if the price is still rising at 9): +1.7 read and +9.5 fit on the 7% fills, but −2.7 read on the 20% fills. Not robust.
- **Keep HOLD_BLOCKS 9.**

## Q6. Size (second place, exit 11)

| stake | $13 | $50 | $100 | $200 |
|---|---|---|---|---|
| fit, 20% fills (63) | +19.0% | +18.7% | +18.2% | +17.4% |
| read (31) | +16.1% | +15.8% | +15.5% | +14.8% |

- About 1.5 points lost up to $200, with the same slope by bundle size and by crowd. The limit is the 3% cap, near $300 (24.38).
- This assumes other buyers ignore our size (untested).
- **No stake increase before the sequential test crosses H1.**

## Q7. More fills

| try | fit | read |
|---|---|---|
| E2 first, instead of E1 | −5.4% (71) | −6.9% (32) |
| E2 retry after a guard revert | −9.5% (34) | −9.2% (14) |
| E2 on gate-refused launches | −6.6% (183) | −5.9% (79) |
| E1+1 first (second seat) | −0.5% | +3.5% |
| E1+2 first | −5.3% | +1.7% |

- E2 is negative at every hold from 0 to 40.
- Gating E2 on the seat block (its buys, its ETH, its fleets) holds nothing out of sample; every positive cell rests on 1–6 launches.
- Bundle < 0.3 ETH and the 1% tier are not in any crowd file or tape: untestable.
- The burst step cannot be priced from the chain; Q4 prices a better place at 2–11 points.

**Nothing positive out of sample.**

## Q8. Single best recommendation: BURST_SLIP 0.20

**Expected effect** at $13 on the read supply (`q8_slip_stress.txt`):
- At second place, $3.5 → $15.1 a day (**+$11.6**). Fires stay at 11.4 a day; fills rise from 7.0 to 11.1.
- Under the landing mix, **+$5.3 a day**.
- Sep 26–28 alone: −$0.2 → +$2.5 a day on 18 fires. The recent edge is thin (+5.1% a fill) either way. The change does not fix the supply fall; it stops the engine throwing away its best-crowded fires.

**Verifying it live**
- The sequential test already scores every fire at modelled second place (read's 50 fires: +12.6%). At 0.20 the wallet earns what the test scores. At 0.07 it does not: realised fills are +7.9% on read, where the test drifts −0.041 a fill.
- At 0.20's read mean (+13.0% a fill, sd 0.27) the drift is +0.032 a fill. Crossing +2.94 takes about 92 fills: about 8 days at the read fill rate, 12 at Sep 26–28's. At Sep 26–28's own mean (+5.1%) it drifts down.
- **The change itself is checked by landing position**, which each fill shows without noise. Log each new fill (7–20% under the build's sizing) with its tx index and the buys ahead.
- **Go back to 0.07 if most of the first 10 new fills land last in E1 or in a later block**, where the model reads −4% to +5%. Otherwise the realised return should match the model at the landed position, as on all five live fills.

## Not concluded

- The gain rests on three fixed-size buyers who faded after Sep 25.
- The landing mix of today's reverts is known from one live case (Sep 27 17:06, last).
- The supply filter's read cost is 5 fills; Sep 26–28 is 18 fires.

**Scripts** (this folder, each with a `.txt` output): `build.py`, `k1.py`, `tokens.py`, `check.py`, `q1_guard.py` … `q7_more.py`, `q8_slip_stress.py`.
