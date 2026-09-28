# K3: more fills and a better P&L from the E1 sniper (Sep 28)

**Basis.** `build_dump.py` runs `engine_replay.py`'s loaders and the engine's own fleet count on the 632 launches and reproduces the replay exactly (usual view: 129 bursts, 61 reverts, 68 fills, +15.9%, $97.92; k-2 and k too). 535 have tapes; my pricing equals G's r2/r3 exactly and the grids to 0.0002 median (`check_pricing.txt`). **A** = Sep 21 09:40-23 (399 launches, 2.6 days), **B** = Sep 24 - 28 09:40 (233, 4.4 days). Default: usual view (k-1 with registration), exit E1+11, $13, a fill pays ret x 13 - $0.33, a revert -$0.33.

**Verdict: one change, BURST_SLIP 0.07 -> 0.20. Everything else: keep, or not proven.**

## 1. The guard (`q1_guard.txt`, `q1b_guard_position.txt`)

| h11, second place | A | B |
|---|---|---|
| fills at 7% | +22.6% (37) | +7.9% (31) |
| reverted bursts, had they filled | +13.7% (42) | **+20.2% (19)** |

The reverts pay what the fills pay (week +15.7% vs +15.9%). The guard trips on the one buy ahead, not the curve before E1 (44 of 48 reverts with tapes): all 44 fires with >= 0.12 ETH first in E1 revert, none under 0.03 ETH does; at first place it binds on 2 fires of 103.

| slip | 0.07 | 0.10 | 0.15 | 0.20 | 0.30 | off |
|---|---|---|---|---|---|---|
| A $ (79 bursts) | 82.63 | 89.65 | 136.06 | 141.05 | 157.60 | 157.57 |
| B $ (50 bursts) | 15.29 | 34.60 | 57.59 | 66.43 | 65.12 | 65.12 |

**Out of sample:** chosen on A (0.30) it adds $49.83 on B; chosen on B (0.20) it adds $58.42 on A. "Smarter" guards lose to the flat one (no guard at >= 3 fleets: A $147.89, B $48.09; bundle ETH: no pattern that holds across periods). Gas: the 61 reverts cost $20.13 a week; the 52 bursts that 20% turns into fills earn $109.57 on that same gas.

"Off" is unsafe: the minOut is what reverts shots landing in the creation second (about 2% of the sized tokens); 20% still refuses them. A second fill is stopped by the BuyOnce relay (`AlreadyBought`), not the guard; a direct-wallet burst must keep 7%.

## 2. Filters (launches removed by that filter alone, then gate + 7% guard; `q2_filters.txt`)

| filter | launches | bursts A / B | $ A / B | verdict |
|---|---|---|---|---|
| bundle cap 3.0 ETH | 20 | 7 / 8 | -10.86 / -13.67 (0 of 14 fills win) | keep |
| creator supply >= 1% | 144 | 12 / 8 | -12.00 / +6.08 | keep (B's +$6 is 5 fills) |
| bundle >= 3 buyers | 18 | 1 / 0 | +0.38 / 0 | too small; ungated they make -7.5% / -10.1% |
| creator repeat | 16 | 3 / 0 | +1.54 / 0 | too small |

Supply thresholds 0.25-3% swap rank between periods (0.5%: A -$4, B +$9). Tier 100-200 bps, bundle >= 0.3 ETH and creator buy <= 2 ETH never bind here and nothing outside them has a return on disk: untestable.

## 3. The gate (`q3_gate.txt`; $ A / B)

| | >= 1 fleet | >= 2 | >= 3 |
|---|---|---|---|
| k-1, 7% | 44.75 / 3.71 | **82.63 / 15.29** | 50.06 / 9.08 |
| k, 7% | 5.85 / -16.19 | 75.36 / 5.29 | 76.87 / 25.63 |
| k-1, 20% | 77.74 / 49.59 | **141.05 / 66.43** | 103.86 / 41.88 |
| k, 20% | 42.38 / 26.03 | 120.33 / 55.29 | 146.82 / 60.63 |

Two fleets at k-1 is the best k-1 threshold in both periods at both guards (the k-2 floor: $44.04 / $1.13); 3 at the tick's block is about equal (ranks swap by period). Nine second signals on the gate (growth k-2 to k-1, shots, bundle ETH, tier, blocks in the second, named wallets, creator supply, hour, fleet count), each chosen on one period and read on the other: none gains both ways (best: hour, +$4.31 on A when chosen on B, -$5.05 on B when chosen on A). Keep the gate.

## 4. Position (fires, guard off, 71 A / 32 B with tapes; `q4_position.txt`)

| h11 | first | second | third | fifth | last |
|---|---|---|---|---|---|
| A | +29.6% | +18.6% | +12.6% | +5.9% | -0.4% |
| B | +23.9% | +15.3% | +10.8% | +7.3% | +4.0% |

Behind a big buy (>= 0.12 ETH), second place pays A +15.3% (31), B +15.9% (13); first place there +34-37%. It pays, and it is what the 7% guard throws away.

## 5. Exit (`q5_exit.txt`)
Rules read block h, sell 2 blocks later (3 as a check), against fixed E1+11 (20% fills: A +19.0% n=63, B +16.1% n=31). Take-profit 10-80%, stops 5-30%, selling when a seat-block buyer sells, a read at blocks 1-5: none beats the fixed exit in both periods at either guard (take-profit 20%: -3.3 / -1.4 points; stop 10%: -0.6 / -3.9). The one both-way gain, "if >= +50% at the sell's send, hold to E1+30" (+3.4 / +2.6), triggers 10 times in A and 4 in B, rests on one or two fires, and is +0.6 on B at a 3-block lag. Not proven. Keep hold 9.

## 6. Size (`q6_size.txt`; later buys folded by their ETH, 3% cap)

| mean per fill | $13 | $50 | $100 | $200 | $400 |
|---|---|---|---|---|---|
| A (20% fills, 63) | +19.0% | +18.7% | +18.2% | +17.4% | +16.5% |
| B (20% fills, 31) | +16.1% | +15.8% | +15.5% | +14.8% | +13.9% |

Near-linear to $200 (-1.3 to -1.6 points); at $400 the cap binds on 81% / 68% of fills. Same slope by bundle ETH and by fleets. Untested: later buyers' reaction to a bigger buy. Raise nothing before the test's upper bound.

## 7. More fills (`q7_more_fills.txt`)
- E2 first place: -6.0% (A, 255 launches), -6.1% (B, 111); on the guard's reverts -9.5% / -9.2%.
- E2 on a read of the seat block (E1 buys or ETH): chosen on A it trades 1 launch on B; chosen on B it loses $17.10 on A.
- A second seat (E2 after our E1 fill): -1.7% / -5.1% (37 / 18).
- A finer burst step: one place earlier is worth +10.9 / +8.6 points a fire, but nothing on disk says where a new step lands the shot. Untestable.
- Excluded launches (bundle < 0.3 ETH, tier 1%): no returns on disk.

## 8. Recommendation: BURST_SLIP = 0.20 (`q8_recommend.txt`)

**Tested effect on the Sep 24-28 supply:** 31 -> 49 fills (7.0 -> 11.1 a day), $15.29 -> $66.43, **+$11.6 a day at $13**. Positive at every view and holds 9-13 in both periods (one negative cell: view k, hold 15, A, -$6.82). Switched bursts: B 18 at +21.9%, win 83%, bootstrap P(gain > 0) 1.00; A 34 at +13.2%, median -0.4%, P 0.986; without the two largest +$30 / +$33. 0.20 sits in both periods' plateau (0.15-0.30).

**Where it can be wrong.** (1) The replay lands every burst second. On the tapes, the Sep 26-28 live landing mix (first 1/2, second 1/3, last 1/6) gains $13-14 per period, a deep mix $24-31; always last loses $15.70 on A. Scaled to B's bursts, the live mix is about **+$5 a day**. (2) Sep 26-28's supply is thinner and its fires weaker (about +5% at second place): +$6.46 over 2.4 days, **+$2.7 a day**. (3) The live record holds one burst of this class (22:09, landed first in E1+2); the four live reverts were three 4.2 ETH templates (now capped) and one last-place landing 12% short (17:06), which 20% would have filled at about -2.5%. Live evidence on the switched class is nil.

**Expected: +$3 to +$12 a day at $13.**

**To verify live.** Log tokens received over tokens sized per fill; fills under 0.93 are the switched class. Run the sequential test on their realized 11-block returns (H0 +2.5%, H1 +19%, sd 0.34, +/-2.94): at the replay's +22% about 20 such fills reach the upper bound, at +2.5% about 25 the lower; a week at B's rate (4 a day), two at Sep 26-28's. Back to 7% on the lower bound, or if 3 of the first 10 switched fills land behind 3+ buys. The main test on the fires is unaffected (it scores every fire at second place) and stays the master switch; it is set for more edge than B shows: at B's +12.6% a fire it needs about 110 fires to accept, and at Sep 26-28's +5% it hits the lower bound in about 36.

*Side effect:* importing the engine (as `engine_replay.py` does) starts its keep-alive, which pinged the sequencer and RPC hosts during my two 3-second dump runs. No commits.
