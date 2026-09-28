# K0: the assistant's own analysis for brief K (written before reading K1-K3)

Data: `engine_replay.py --dump` rows at the three gate views (`rows_k2.json`, `rows_k1reg.json`, `rows_kreg.json`), G's curves for
exit rules, `k0_analysis.py` / `k0_analysis.txt`, `slip_sweep.txt`. Fit = Sep 21-23, test = Sep 24-28. $13 a fire, gas $0.33.

## 1. The minOut guard is the largest lever (the single recommendation)
At BURST_SLIP 7% the guard reverts a burst whenever the buy ahead of us moved the price 7% or more. Those bursts, had they filled at
second place (the model folds the buy ahead in), pay in both periods and at every view:

| view | period | reverted bursts as fills | actual fills |
|---|---|---|---|
| usual (k-1) | fit | n=27 +9.5%, +$24 | n=32 +24.9%, +$93 |
| usual (k-1) | test | n=34 +20.7%, win 71%, +$80 | n=36 +7.9%, +$25 |
| floor (k-2) | fit | n=8 +40.9%, +$40 | n=7 +51.3%, +$44 |
| floor (k-2) | test | n=19 +28.5%, win 84%, +$64 | n=11 +9.3%, +$10 |

By the size of the move ahead (seat tokens / sized tokens): 0.85-0.93 n=44 +16.7%; 0.75-0.85 n=12 +12.6%; under 0.75 n=5 +14.4%.
The guard's designed job (24.20: reject a second fill of our own) is done by the relay's one-buy-per-curve rule at any stake, and at
$13 the engine itself notes the guard cannot do it (`burst_note`, line 1956). A creation-second landing still reverts at any slip
under 90% (the 97% tax leaves 3% of the tokens). Sweep on Sep 24-28 (`slip_sweep.txt`):

| slip | floor $ (fills) | usual $ (fills) | ceiling $ (fills) |
|---|---|---|---|
| 0.07 (live) | +1.13 (9 of 18) | +15.29 (31 of 50) | +5.29 (45 of 78) |
| 0.15 | +27.96 (16) | +57.59 (46) | +46.44 (66) |
| 0.25 | +36.06 (18) | +65.12 (50) | +53.97 (70) |
| 0.40 | +36.06 (18) | +65.12 (50) | +51.36 (72) |

Fit period, usual view: $83 -> $148 (37 -> 74 fills, mean +22.6% -> +18.1%). The whole week at the usual view: $98 -> $213, every
day positive but Sep 28's single fill. **Recommendation: BURST_SLIP 0.25.** Expected on the Sep 24-28 supply at $13: about +$10 a
day (usual view +$3.5 -> +$14.8; floor +$0.3 -> +$8.2). Dead tail at 25%: 2% of fills under -40% (0% at 7%).

## 2. Filters
- Creator supply < 1% (147 removed): would fill 9 at -6.5% in fit, 6 at +10.6% in test. Mixed, small; keep.
- Cap 3.0 ETH (20): the removed launches fill at -10.6% (n=11 test), -11.3% (n=3 fit). Earns its keep.
- Creator repeat (17), bundle count (18): nothing to measure.
- Tier 2% fills: fit +8.1% (n=10, win 40%), test -3.5% (n=8, win 25%); tier 3%: +25.4% / +12.6%. A watch item, not a change (n=18).
- Bundle under 0.6 ETH pays more in both periods (fit +53% n=8, test +11% n=14) than 0.6-1.2 (+5.8% / +6.5%); small counts.

## 3. Gate threshold, view, position, exit, size
- Fleets >= 2 stands: >= 1 gives test +2.5% on 69 (-$0.38); >= 3 gives test +12.3% on 15 (+$19, fewer dollars than 2's +$25).
- Exit: fixed 13 beats 11 by 1-2 points in both periods (fit +25.9 vs +24.9; test +12.3 vs +10.6); take-profit rules lose in both
  (they cut the winners); stops change nothing. HOLD_BLOCKS 9 lands at 11-13: leave it.
- First place beats second by 3 points (test +11.0 vs +7.9, n=32): landing is timing, not a setting.
- Size: not re-tested here (24.38's table stands: linear to about $300).
- More fills per day beyond the guard: E2 not tested here; the launches under 0.3 ETH bundle are outside every population on disk.

## 4. What to watch live after the switch
Fills per burst (should rise from about half to nearly all), the guard's reverts (`buy_reverted` events should become rare), the
fill's landing index and the buy ahead (live_vs_table prints both), and the sequential test on the chain-scored fires as before.

## 5. The looser guard's downside, measured (added after the E2 check)
The guard also reverts a burst that lands deep: last in E1 behind the whole crowd (e1_multi's E1_last: -3.4% mean on the week's fired
launches, win 22%) or in the next second E2 (E2_first -8.0%, win 16%). What passes at each tolerance, on the 129 fired launches with
sizing on disk (fit / test):

| slip | second place passes | a LAST-in-E1 landing passes (its return) | an E2 landing passes (its return) |
|---|---|---|---|
| 0.07 | 32/59, 36/70 | 14, 15 (-0.3%, +0.2%) | 19, 27 (+0.2%, -5.1%) |
| 0.15 | 51/59, 61/70 | 22, 35 (-2.9%, -2.6%) | 36, 46 (-4.6%, -7.2%) |
| 0.25 | 55/59, 69/70 | 39, 53 (-6.4%, -1.4%) | 44, 60 (-4.1%, -7.6%) |

A deep landing that fills at 0.15 loses about what the revert costs in gas (-2.6% of $13 = -$0.34 against $0.33; an E2 fill -$0.94),
while each second-place fill gained pays +$1.5 to +2.7. Live, one burst in ten landed deep (the late gate of Sep 27 17:06) and one in
twenty is held by the sequencer into E1+2. **Recommendation refined: BURST_SLIP 0.15** (nine tenths of the gain: Sep 24-28 usual
view +$58 of +$65, floor +$28 of +$36) with 0.25 as the ceiling to move to once the landing indices of the first fills are read.
