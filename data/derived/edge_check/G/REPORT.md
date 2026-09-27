**CHANGE to h = 9 (plateau 7-16).** Setting 9 lands the sell at E1+11 to E1+13, as the seat-block buyers begin their exits at blocks 12-15. At h = 9 the fires make **+17.0% on the fit (73 fires) and +14.0% on the recent set (19 fires)**. Where the sell really lands (the average of h+2, h+3 and h+4) they make **+19.1% and +14.8%**; the current 15 lands at +15.5% and +12.3%. **Out of sample:** chosen on the fit alone (landed exit, 1-60 blocks) the setting is 9, and on the recent set it reads +14.8% against +12.3% for 15 (+2.5 points; bootstrap P(gain > 0) = 91%). Chosen on the recent alone it is 8, which reads +19.1% on the fit against +15.5%. Chosen on Sep 18-21 it is 10, which reads +12.5% on Sep 22-27 against +11.2%. The long holds do not survive: the fit's own optimum over 1-600 is h = 337 (+27.0%), and on the recent set it reads +2.9%.

# Hold sweep, reviewer G (Sep 27 2026)

Every command runs from the repository root. The scripts and their outputs are in `data/derived/edge_check/G/`. Each script's docstring gives its command.

## 1. Data and yardstick

- **Population** (`common.py`). The four fit windows (sep1819, sep2021, sep2223, sep23day) hold 563 launches and 73 fires. The recent windows are the eleven crowd files Sep 24-27 plus round 1 A's two gap pulls (gapA, gapB): 172 launches and 19 fires. "rec18", the eleven files without the gaps, has 160 launches and 18 fires. A fire is fleets >= 2 at block k-2 (`crowd_rules.cums/at`, imported by exec as `reach_table.py` does, `sys.argv` set first).
- **Tapes**. The tapes to b0+640 come from A/ (the 91 fires, with real stamps), A/'s gap and chk27 pulls, C/tapes_extra (85 sep2223 launches, real stamps) and B/tapes (536 launches, stamps synthesised from k and checked by B/synth_check.py). All 735 have a tape.
- **The tail b0+641..b0+1250** came from the public RPC for all 735 launches: `python3 data/derived/edge_check/G/pull_ext.py`, 4 threads, 0.15 s pacing plus live_vs_table's own 0.25 s, back-off on errors. It needed no retries and took 210 s (`pull_ext.log`). Every launch now reaches E1+1200.
- **Pricing**. The model is `stake_scale.model_eff`, imported by exec: second place in E1, $13 at 2570 $/ETH, the surcharge by second, the tier on buy and sell, the 3% cap, later buys folded by ETH and sells by tokens, and the exit's own impact. Gas is $0.33 a burst. `common.curve()` is a one-pass rewrite that returns the exit value after every block E1+h.
- **Check**: `python3 data/derived/edge_check/G/check_curve.py > check_curve.txt`.
  - `curve()` equals `model_eff` on 7,350 (launch, h) pairs up to h600, at third place, and on the extended tapes to h1200; the largest difference is 0.00e+00.
  - It reproduces rounds 1-2 exactly: fit h15 +16.2% and h300 +26.3%; rec18 +12.8% and +3.5%; rec (19 fires) +12.6% and +3.0%.

## 2. The curves (task 1)

`python3 data/derived/edge_check/G/curves.py` prices all 735 launches at every h from 0 to 1200, at second place and at third, into `curves.json.gz`. `python3 data/derived/edge_check/G/sweep.py > sweep.txt` writes every statistic at every h for every set to `sweep_all.csv`. Each set means the fit, each fit window, rec, rec18, Sep 18-21, Sep 22-27, Sep 22-23 and each day Sep 18-27. The refused launches are priced at every block. The tables below come from `python3 data/derived/edge_check/G/report_tables.py > report_tables.md` (no hand transcription).

Legend for the table:
- **$/fire** is after gas, at second place with every burst filled.
- **lift** is the fires' mean minus the refused launches' mean at the same h, in points. There are 490 refused launches on the fit and 153 on the recent set.

| h | fit mean | median | win | dead | sd | $/fire | lift | recent mean | median | win | dead | sd | $/fire | lift |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | +11.5% | +5.7% | 59% | 0% | 0.25 | +1.17 | +15.6 | +0.7% | -3.1% | 32% | 0% | 0.20 | -0.24 | +7.7 |
| 5 | +15.5% | +10.2% | 66% | 0% | 0.29 | +1.69 | +19.4 | +7.8% | +0.0% | 53% | 0% | 0.23 | +0.68 | +13.1 |
| 10 | +18.6% | +11.6% | 66% | 3% | 0.35 | +2.09 | +20.1 | +14.2% | +5.7% | 63% | 0% | 0.25 | +1.52 | +17.2 |
| 15 | +16.2% | +8.0% | 66% | 3% | 0.34 | +1.78 | +18.5 | +12.6% | +0.1% | 58% | 0% | 0.28 | +1.30 | +15.7 |
| 20 | +16.7% | +8.0% | 64% | 3% | 0.35 | +1.84 | +18.8 | +12.2% | +0.0% | 53% | 0% | 0.31 | +1.25 | +15.0 |
| 25 | +16.4% | +9.3% | 64% | 3% | 0.34 | +1.80 | +17.9 | +9.1% | -0.5% | 47% | 0% | 0.32 | +0.86 | +12.0 |
| 30 | +16.1% | +8.5% | 64% | 3% | 0.34 | +1.76 | +18.1 | +6.7% | -0.7% | 42% | 0% | 0.32 | +0.54 | +9.4 |
| 35 | +16.5% | +8.3% | 66% | 3% | 0.35 | +1.81 | +18.5 | +4.9% | -3.0% | 42% | 0% | 0.30 | +0.30 | +7.9 |
| 40 | +15.9% | +7.4% | 66% | 3% | 0.35 | +1.73 | +18.0 | +4.0% | -3.0% | 47% | 0% | 0.30 | +0.19 | +7.8 |
| 45 | +15.3% | +9.3% | 64% | 3% | 0.33 | +1.66 | +17.1 | +4.6% | -3.0% | 47% | 0% | 0.30 | +0.27 | +8.5 |
| 50 | +16.7% | +9.3% | 66% | 3% | 0.35 | +1.84 | +18.3 | +4.7% | -3.0% | 42% | 0% | 0.29 | +0.28 | +8.6 |
| 55 | +16.6% | +9.3% | 66% | 3% | 0.36 | +1.83 | +18.1 | +3.9% | -3.0% | 42% | 0% | 0.29 | +0.18 | +6.3 |
| 60 | +16.2% | +9.3% | 66% | 3% | 0.36 | +1.78 | +17.3 | +4.1% | -3.0% | 42% | 0% | 0.29 | +0.20 | +5.8 |
| 80 | +16.6% | +6.1% | 63% | 4% | 0.41 | +1.83 | +17.9 | -2.9% | -1.0% | 42% | 5% | 0.26 | -0.71 | -2.5 |
| 100 | +19.9% | +11.8% | 64% | 5% | 0.45 | +2.26 | +21.0 | +0.7% | -1.0% | 47% | 5% | 0.37 | -0.23 | +1.5 |
| 120 | +21.6% | +11.9% | 67% | 5% | 0.46 | +2.48 | +22.1 | +2.4% | -1.0% | 47% | 5% | 0.38 | -0.02 | +2.7 |
| 140 | +22.1% | +12.9% | 67% | 5% | 0.48 | +2.54 | +22.0 | +9.8% | +2.8% | 53% | 0% | 0.39 | +0.94 | +8.7 |
| 160 | +20.4% | +11.6% | 66% | 7% | 0.49 | +2.33 | +20.3 | +10.0% | +2.8% | 53% | 0% | 0.39 | +0.97 | +6.6 |
| 180 | +21.8% | +13.0% | 66% | 7% | 0.50 | +2.50 | +21.3 | +11.9% | +2.8% | 53% | 0% | 0.45 | +1.21 | +8.1 |
| 200 | +23.3% | +13.0% | 67% | 7% | 0.52 | +2.70 | +22.7 | +13.2% | +2.9% | 58% | 0% | 0.45 | +1.38 | +9.1 |
| 220 | +23.9% | +15.5% | 66% | 7% | 0.55 | +2.77 | +23.4 | +13.8% | +2.9% | 53% | 0% | 0.45 | +1.46 | +11.3 |
| 240 | +25.2% | +15.5% | 68% | 7% | 0.56 | +2.95 | +24.8 | +13.5% | -1.0% | 47% | 0% | 0.45 | +1.43 | +10.7 |
| 260 | +25.3% | +15.5% | 64% | 7% | 0.57 | +2.96 | +24.8 | +12.8% | +0.8% | 53% | 5% | 0.45 | +1.33 | +9.7 |
| 280 | +26.3% | +15.7% | 64% | 8% | 0.59 | +3.09 | +27.1 | +3.6% | -4.9% | 42% | 11% | 0.47 | +0.14 | -0.0 |
| 300 | +26.3% | +20.7% | 67% | 8% | 0.59 | +3.09 | +26.8 | +3.0% | -4.9% | 37% | 11% | 0.47 | +0.06 | -0.7 |
| 350 | +25.3% | +18.3% | 63% | 11% | 0.61 | +2.96 | +25.4 | +2.9% | -4.5% | 42% | 11% | 0.48 | +0.04 | -0.1 |
| 400 | +19.2% | +13.5% | 59% | 16% | 0.64 | +2.16 | +19.8 | -1.4% | -11.0% | 37% | 21% | 0.54 | -0.51 | -4.0 |
| 450 | +19.8% | +14.5% | 59% | 18% | 0.64 | +2.24 | +21.1 | -0.5% | -11.0% | 37% | 26% | 0.54 | -0.40 | -4.8 |
| 500 | +18.6% | +12.8% | 58% | 19% | 0.65 | +2.09 | +19.8 | -3.4% | -11.0% | 37% | 26% | 0.55 | -0.77 | -8.7 |
| 550 | +19.5% | +5.6% | 55% | 19% | 0.66 | +2.20 | +19.9 | -1.9% | -11.0% | 42% | 26% | 0.55 | -0.57 | -8.4 |
| 600 | +19.6% | +10.8% | 52% | 19% | 0.67 | +2.22 | +20.0 | -0.9% | -14.4% | 42% | 26% | 0.59 | -0.44 | -6.8 |
| 700 | +16.7% | +0.3% | 51% | 21% | 0.67 | +1.84 | +18.3 | -2.6% | -11.0% | 37% | 26% | 0.57 | -0.66 | -7.2 |
| 800 | +17.3% | -1.7% | 48% | 23% | 0.73 | +1.92 | +18.8 | +2.3% | -11.0% | 37% | 32% | 0.65 | -0.03 | -1.7 |
| 900 | +17.7% | +1.2% | 51% | 25% | 0.73 | +1.97 | +18.5 | -1.7% | -13.8% | 37% | 37% | 0.66 | -0.56 | -5.1 |
| 1000 | +18.1% | +9.2% | 52% | 25% | 0.74 | +2.03 | +19.6 | -2.8% | -12.9% | 37% | 37% | 0.64 | -0.70 | -5.7 |
| 1100 | +20.2% | +9.4% | 52% | 26% | 0.75 | +2.29 | +22.0 | -3.3% | -12.9% | 37% | 37% | 0.63 | -0.76 | -5.4 |
| 1200 | +19.2% | +9.4% | 53% | 25% | 0.75 | +2.17 | +21.1 | +0.5% | -12.9% | 37% | 37% | 0.67 | -0.27 | -1.7 |

By window and by day: the mean, with the lift over that set's refused launches in brackets. Win, dead, median and $ a fire for each window and day at h15, h60, h300 and h600 are at the end of `sweep.txt`.

| set | fires/refused | h1 | h5 | h10 | h11 | h15 | h20 | h30 | h60 | h150 | h300 | h600 | h1200 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fit | 73/490 | +11.5% (+16) | +15.5% (+19) | +18.6% (+20) | +19.5% (+21) | +16.2% (+18) | +16.7% (+19) | +16.1% (+18) | +16.2% (+17) | +21.2% (+21) | +26.3% (+27) | +19.6% (+20) | +19.2% (+21) |
| sep1819 | 14/127 | +15.6% (+17) | +18.2% (+20) | +20.6% (+20) | +22.9% (+22) | +27.5% (+26) | +25.7% (+24) | +29.7% (+29) | +22.5% (+24) | +10.7% (+10) | +18.9% (+19) | +26.3% (+29) | +23.3% (+31) |
| sep2021 | 29/160 | +11.9% (+17) | +15.3% (+20) | +20.8% (+22) | +21.1% (+22) | +16.4% (+17) | +14.4% (+16) | +11.7% (+13) | +15.4% (+15) | +21.6% (+20) | +26.2% (+27) | +13.1% (+11) | +19.4% (+16) |
| sep2223 | 20/155 | +6.2% (+11) | +12.4% (+16) | +11.9% (+14) | +12.6% (+15) | +9.0% (+14) | +13.0% (+17) | +13.7% (+17) | +13.4% (+14) | +30.2% (+31) | +35.5% (+33) | +28.7% (+28) | +27.3% (+23) |
| sep23day | 10/48 | +15.5% (+21) | +18.8% (+24) | +23.2% (+28) | +23.7% (+29) | +14.4% (+21) | +17.7% (+26) | +14.5% (+22) | +15.4% (+22) | +16.5% (+21) | +18.9% (+29) | +11.0% (+19) | -3.3% (+21) |
| rec | 19/153 | +0.7% (+8) | +7.8% (+13) | +14.2% (+17) | +15.7% (+19) | +12.6% (+16) | +12.2% (+15) | +6.7% (+9) | +4.1% (+6) | +10.4% (+8) | +3.0% (-1) | -0.9% (-7) | +0.5% (-2) |
| rec18 | 18/142 | +0.7% (+8) | +8.2% (+13) | +13.8% (+16) | +15.4% (+18) | +12.8% (+15) | +12.4% (+14) | +6.7% (+9) | +4.4% (+6) | +11.1% (+9) | +3.5% (-1) | +2.4% (-5) | +3.8% (+1) |
| Sep18-21 | 41/280 | +14.2% (+17) | +17.5% (+21) | +22.3% (+22) | +23.3% (+23) | +21.5% (+21) | +19.5% (+19) | +18.9% (+19) | +19.1% (+19) | +19.0% (+18) | +24.6% (+25) | +17.9% (+18) | +20.3% (+21) |
| Sep22-27 | 51/363 | +5.3% (+11) | +11.1% (+16) | +14.1% (+17) | +15.1% (+19) | +10.6% (+15) | +12.7% (+17) | +10.3% (+14) | +9.4% (+12) | +18.9% (+19) | +19.0% (+18) | +13.4% (+12) | +11.3% (+12) |
| Sep 18 | 13/91 | +15.8% (+15) | +18.6% (+20) | +21.2% (+20) | +23.3% (+22) | +28.2% (+27) | +27.8% (+26) | +32.0% (+31) | +23.3% (+26) | +10.5% (+10) | +18.6% (+17) | +27.5% (+29) | +25.0% (+32) |
| Sep 19 | 1/36 | +12.8% (+20) | +12.8% (+16) | +12.8% (+13) | +17.7% (+17) | +18.1% (+16) | -0.6% (-3) | -0.2% (-0) | +12.6% (+12) | +12.9% (+14) | +22.1% (+26) | +10.8% (+15) | +1.7% (+9) |
| Sep 20 | 7/35 | +24.0% (+25) | +28.0% (+28) | +35.3% (+32) | +34.3% (+30) | +29.3% (+27) | +27.5% (+28) | +13.9% (+16) | +11.7% (+13) | +23.0% (+24) | +28.8% (+36) | -1.7% (+4) | -3.3% (+8) |
| Sep 21 | 20/118 | +9.9% (+16) | +13.5% (+19) | +18.9% (+21) | +19.6% (+21) | +14.5% (+16) | +12.3% (+13) | +13.2% (+13) | +19.3% (+17) | +23.5% (+20) | +27.1% (+26) | +18.8% (+14) | +26.5% (+17) |
| Sep 22 | 19/151 | +6.1% (+11) | +12.4% (+17) | +10.7% (+13) | +11.5% (+14) | +7.9% (+13) | +11.7% (+17) | +12.1% (+16) | +9.0% (+9) | +22.1% (+22) | +22.0% (+19) | +14.9% (+13) | +15.6% (+10) |
| Sep 23 | 13/59 | +10.9% (+17) | +13.9% (+20) | +18.9% (+24) | +19.3% (+25) | +11.9% (+19) | +15.0% (+23) | +13.0% (+20) | +17.7% (+27) | +26.6% (+34) | +38.1% (+50) | +32.1% (+41) | +21.0% (+46) |
| Sep 24 | 9/46 | +5.7% (+12) | +14.2% (+20) | +15.1% (+17) | +15.6% (+18) | +14.8% (+17) | +17.2% (+20) | +6.0% (+8) | +3.1% (+6) | +1.8% (-2) | +1.5% (-4) | +5.0% (-2) | +16.5% (+13) |
| Sep 25 | 4/45 | -4.0% (+3) | +4.4% (+8) | +27.1% (+29) | +32.3% (+34) | +22.0% (+23) | +23.0% (+23) | +25.7% (+26) | +24.1% (+29) | +43.8% (+47) | +47.9% (+45) | +36.2% (+28) | +15.9% (+3) |
| Sep 26 | 5/49 | -2.5% (+5) | +2.5% (+7) | +7.2% (+10) | +7.7% (+11) | +5.5% (+9) | -1.3% (-0) | -3.9% (-3) | -7.3% (-10) | -6.2% (-11) | -22.1% (-23) | -33.3% (-32) | -32.3% (-20) |
| Sep 27 | 1/13 | -10.0% (+1) | -10.0% (+1) | -10.0% (+1) | -10.0% (+1) | -10.0% (+4) | -10.0% (+12) | -10.0% (+11) | -10.0% (-8) | +37.7% (+39) | -37.6% (-46) | -39.1% (-62) | -41.1% (-58) |

**The shape.** The curve has two humps.

- **The short hump** appears in both periods. It rises to a peak at h = 10-13 and then falls over blocks 12-15. The fit peaks at +19.5% (h11) and drops to +16.2% by h15. The recent set peaks at +15.7% (h11) and drops to +12.6%. The sweep shows this peak in all four fit windows except sep1819 (which keeps rising to h30), and on 7 of the 8 days with more than one fire (Sep 18 is the exception). At h11 the lift over the refused launches is +21 points on the fit and +19 on the recent set, the recent set's highest at any hold.
- **The long hump** (h 100-350, +20% to +27% on the fit) belongs to Sep 20-23. It is gone on the recent set: +3.0% at h300, with lift −0.7 points, and it turns negative past h400. Past block 600 nothing comes back: at the tabled holds out to h1200 the recent set is between −3.3% and +2.3%, and the dead rate reaches 37%.

Block by block for the first 40 blocks, with paired steps, one-block drops, the refused launches and the landed exit: `python3 data/derived/edge_check/G/fine.py > fine.txt`.

## 3. The choices and their plateaus (task 2)

`python3 data/derived/edge_check/G/choose.py > choose.txt`. The optimum is the argmax of the fires' mean. The plateau is every h whose mean is within one standard error (the optimum's) of the optimum, on the choosing set. The report gives the contiguous run around the optimum and, in brackets, every h that qualifies. The paired difference against h15 is taken over the same fires.

| choose on | range | optimum | plateau (contiguous; all h within) | read on | reading at the optimum | reading at h15 |
|---|---|---|---|---|---|---|
| fit (73) | 1-600 | **h337, +27.0%** (se 7.0) | 101-393 (329 of 600 h) | recent (19) | **+2.9%** | +12.6% |
| fit (73) | 1-60 | **h11, +19.5%** (se 4.1) | 7-16 (52 of 60) | recent | **+15.7%** | +12.6% |
| recent (19) | 1-600 | **h11, +15.7%** (se 6.4) | 7-23 (also 131-268) | fit | **+19.5%** | +16.2% |
| Sep 18-21 (41) | 1-600 | **h334, +26.1%** (se 7.9) | 149-374 (also 7-30, 32-62, 95-145) | Sep 22-27 (51) | **+18.7%** | +10.6% |
| Sep 18-21 (41) | 1-60 | **h13, +24.2%** (se 4.8) | 7-17 | Sep 22-27 | **+12.4%** | +10.6% |

- **Up to h1200 the optima do not move** (337, 11, 334).
- **The fit alone picks the long hump, which fails on the recent set.** Paired against h15, h337 is +10.8 points on the fit (se 6.3) and −9.6 on the recent set (se 8.4).
- **The Sep 18-21 choice (h334) holds on Sep 22-27 only because of Sep 22-23.** Split, h334 reads +28.1% on the 32 Sep 22-23 fires and +2.8% on the 19 recent fires (the first lines of `choose.txt`). The long hump belongs to the Sep 20-23 windows. It is not a property of the rule.
- **The recent alone picks h11.** On the fit, h11 is the fit's own short-range optimum and beats h15 by +3.3 points (paired se 1.5). On the recent set it beats h15 by +3.2 (se 1.6).
- **1-60 is not fitted here.** It is the discovery's horizon, fixed in round 2 (24.36) before this sweep. Within it the fit alone chooses h11, and that reads +15.7% on the recent set, the recent set's own maximum.
- **The level plateau is too wide to separate the short holds.** Within 1-60 almost every hold is within one standard error of the optimum on the fit (52 of 60), and h15 is inside the plateau on both periods (7-16 and 7-23). What separates 10-13 from 15 is the paired difference over the same fires, which is measured about three times more precisely than the level. That difference is positive on every choosing set and every reading set (+1.8 to +4.4 points).

## 4. Why the value falls after block 11

`python3 data/derived/edge_check/G/sellers.py > sellers.txt` splits the tokens sold in each block after E1 by where the seller bought.

- **On the fit**, 80%, 100%, 97% and 99% of the tokens sold in blocks E1+12, 13, 14 and 15 are sold by wallets that bought in the seat block E1: 27 sells over 73 fires, 10 of them at block 12 and 10 at block 15. A few seat-block buyers sell at blocks 2-5; between blocks 6 and 11 they sell almost nothing, and the sells of blocks 6-10 come from the creation second.
- **On the recent set** it is the same: 100%, 88%, 63% and 100% in blocks 12-15, from 9 sells.
- **`fine.txt` shows the damage block by block.** Eight fit fires lose more than 5 points in block 12 alone, and 7 in block 15.
- **This matches 24.29.** The wallet that takes the first seat held its seats 14.5 blocks. The first seats leave at E1+12..15, and a sell that lands at E1+11..13 is out before most of them.

## 5. Robustness (task 3)

`python3 data/derived/edge_check/G/robust.py > robust.txt` (bootstrap 2,000, seed 7).

- **Bootstrap of the optimal h over 1-600.**
  - Fit: 80.5% of resamples pick 201-400 and 10.3% pick 1-20 (median 311).
  - Recent: 54.8% pick 1-20 and 36.7% pick 201-400 (median 13).
  - Pooled 92: 76.7% pick 201-400 (median 249).
  - Over 1-60 the median optimum is 11 on every set. It falls in 7-16 in 75.7% of fit resamples, 91.5% of recent and 90.5% of pooled.
- **Bootstrap of the means.**
  - h15: fit +16.3% (2.5-97.5%: +8.9% to +24.4%); recent +12.5% (+1.3% to +25.1%).
  - h11: fit +19.5% (+11.9% to +27.6%), gain over h15 +3.3 points (+0.3 to +6.1), P(gain > 0) 98.4%. The recent gain is +3.2 (+0.1 to +6.1), P 98.2%.
  - h337: recent +2.8% (−15.0% to +24.9%), P(gain over h15 > 0) 12.3%.
- **Bootstrap of the landed gain of setting 9 over setting 15** (sell at h+2..h+4): fit +3.6 points (+0.8 to +6.4, P 99.5%); recent +2.5 (−1.3 to +6.1, P 90.8%); pooled +3.4 (+1.0 to +5.7, P 99.8%).
- **Leave one fit window out.**
  - Over 1-600, the other three windows choose 311-341 every time. On the window left out, that choice reads +18.5% vs +27.5% at h15 (sep1819), +26.9% vs +16.4% (sep2021), +33.9% vs +9.0% (sep2223) and +20.0% vs +14.4% (sep23day). Inside Sep 18-23 the long hold did win three windows of four; it is the recent period where it fails.
  - Over 1-60 the choices are 11, 29, 11 and 12. On the window left out they beat h15 on sep2223 and sep23day and lose on sep1819 and sep2021.
  - For setting 9 landed against setting 15 landed, the gain by fit window is +0.1, +6.1, +2.6 and +3.3 points. By day it is positive on 7 of the 10 days, −1.3 on Sep 18 and Sep 24, and 0.0 on Sep 27 (`robust.txt` (d)).
- **The late sell.** Each candidate at h / h+2 / h+4 / landed:

| setting | fit | recent |
|---|---|---|
| 15 (now) | +16.2 / +15.4 / +15.7 / **+15.5%** | +12.6 / +12.9 / +12.0 / **+12.3%** |
| 8 | +17.6 / +18.6 / +19.1 / **+19.1%** | +11.4 / +14.2 / +15.1 / **+15.0%** |
| **9** | +17.0 / +19.5 / +18.8 / **+19.1%** | +14.0 / +15.7 / +13.5 / **+14.8%** |
| 10 | +18.6 / +19.1 / +17.9 / **+18.6%** | +14.2 / +15.1 / +12.5 / **+13.7%** |
| 11 (recent optimum) | +19.5 / +18.8 / +16.2 / **+17.6%** | +15.7 / +13.5 / +12.6 / **+12.9%** |
| 337 (fit optimum) | +27.0 / +26.9 / +27.0 / **+26.9%** | +2.9 / +2.8 / +3.0 / **+3.0%** |

A late sell is what makes h11 the wrong setting: landing at 13-15, it sells into the seat-block exits. Chosen on the landed curve, the setting is:

| chosen on | setting, landed | reads on the other set | setting 15 there |
|---|---|---|---|
| fit (1-60) | 9, +19.1% (plateau 2-60) | recent: +14.8% | +12.3% |
| recent (1-600) | 8, +15.0% (plateau 3-23) | fit: +19.1% | +15.5% |
| Sep 18-21 (1-60) | 10, +23.9% (plateau 4-21) | Sep 22-27: +12.5% | +11.2% |

The pooled 92 fires choose 8 (plateau 4-21). Setting 9 sits in the middle of the landed optima (8-10), and its landing (11-13) sits on the exit plateau 7-16.

## 6. Two-stage exits (task 4)

`python3 data/derived/edge_check/G/twostage.py > twostage.txt` runs 8 variants, declared before running. There are 6 triggered exits:
- take-profit +20% and +50%, each with hold 9 and hold 300;
- a −20% stop with hold 9 and with hold 300.

There are 2 partial exits (exact, with the first sale's impact on the curve): half at 9 and half at 60; half at 9 and half at 300.

Each runs at lag 0 and lag 2, where the trigger reads the mark at each block end. The yardstick is the fixed setting 9 at the same lag. Null test: 1,000 permutations per variant in which each fire exits at the time the trigger fired on another fire's path.

- **Stops do not help.** The −20% stop with hold 300 is +23.4% on the fit and −2.4% on the recent set (lag 2); it loses on the recent set as badly as the fixed 300. The dumps are one-block events:
  - Fit: at the 10 crossings the mark went from +2.0% the block before to −32.5% at the crossing and −37.5% two blocks later; 5 of the 10 fell more than 20 points in one block.
  - Recent: at the 6 crossings, +16.0% → −28.5% → −35.9%.

  With hold 9 the stop fires once in 92 fires and changes nothing.
- **Partial exits lose to the short hold on the recent set.** Half at 9 and half at 60 gives +17.9% fit and +9.6% recent. Half at 9 and half at 300 gives +23.0% and +9.4%. Each is the average of its two single exits, to 0.1 point.
- **Take-profit with the short hold loses** (tp +20% / hold 9: +15.5% and +15.1%), because it cuts the fires that were still rising to block 11.
- **One variant beats setting 9 on both periods: take-profit +20% with hold 300.**
  - At lag 2 it gives +20.2% fit and +18.8% recent, against +19.5% and +15.7%.
  - At lag 0 it gives +18.7% and +16.6%, against +17.0% and +14.0%.
  - Its null test passes: permuted wins 1.2% and 3.6%, permuted margin at least the real one 0.4% and 0.6%.

  It does not pass the rest of the discipline (`python3 data/derived/edge_check/G/tp_check.py > tp_check.txt`):
  - It is a spike. In its neighbourhood (take-profit 10-40% × hold 60-600, 24 cells) it is the only cell that beats setting 9 on both periods. Tp +25% / 300 reads +13.7% on the recent set, and tp +20% / 600 reads +14.2%.
  - The bootstrap gain over setting 9 at lag 2 is +0.7 points on the fit (P 61%) and +3.0 on the recent set (P 81%), with a median per-fire gain of 0.0.
  - One Sep 27 fire (+26.3% against −10.0%) carries 1.9 of the recent set's 3.0 points.
  - It loses on the sep2223 and sep23day windows and on Sep 20 and Sep 23.
  - It holds 8 of the 19 recent fires (24 of the 73 fit fires) for 300 blocks, the hold that failed.
- **Variants tried in all: 32** (8 declared plus the 24 neighbourhood cells), each at 2-3 lags. With 32 tries, one pass at p ≈ 0.5% is what chance delivers about one time in seven (one in four counting both lags). Nothing two-stage is adopted.

## 7. $ a day (task 5)

`python3 data/derived/edge_check/G/dollars.py > dollars.txt`. The recent supply is 0.32 fires an hour, 7.68 a day, at $13 and $0.33 of gas a burst.
- **Full fill**: every burst fills in second place.
- **Live mix**: half the bursts fill; a fill lands second two times in three and third one time in three (third place priced); gas is paid on every burst.

The returns are the landed exit (h+2..h+4).

| setting | per-fire returns from | 2nd place | 3rd place | $/day, full fill | $/day, live mix |
|---|---|---|---|---|---|
| 15 (now) | recent | +12.3% | +8.3% | +9.74 | +2.93 |
| 15 (now) | fit | +15.5% | +9.4% | +12.95 | +4.19 |
| **9 (recommended)** | recent | +14.8% | +10.5% | **+12.21** | **+4.13** |
| **9 (recommended)** | fit | +19.1% | +12.5% | +16.55 | +5.91 |
| 11 (recent optimum) | recent | +12.9% | +8.7% | +10.30 | +3.19 |
| 11 (recent optimum) | fit | +17.6% | +11.1% | +15.07 | +5.19 |
| 337 (fit optimum) | recent | +3.0% | −0.3% | +0.44 | −1.60 |
| 337 (fit optimum) | fit | +26.9% | +20.8% | +24.37 | +9.90 |

`dollars.txt` also has each setting at the exit block itself and h300 as it ran until Sep 27. At the recent returns, the change from 15 to 9 is worth about $2.50 a day at full fill and $1.20 a day at the live mix, at $13. The fit's optimum would lose $1.60 a day at the recent returns.

## 8. What the verdict rests on, and what it does not claim

- **The gain is small and measured precisely.** Setting 9 beats setting 15 by +2.5 to +3.6 points landed, in both periods, in all four fit windows (sep1819 by 0.1) and on 7 of 10 days. All three out-of-sample readings go the same way.
- **The level is not measured precisely.** The recent mean at setting 9 has a 95% bootstrap interval of +3.9% to +25.1% at the block. The change moves the rule's expected $ a day by about a dollar; it does not make the rule a large one.
- **The mechanism is another bot's hold.** The seat-block buyers exit at E1+12..15. If they shorten their hold, the peak moves with them, so the evening reading should add the landed return at settings 9 and 15 per fire.
- **Keep the engine's landing lag near 2-4 blocks.** At a lag of 6 blocks, setting 9 sells at E1+15, inside the sell wave, and is worth what 15 is now.
- **Nothing beyond 60 blocks survives the recent period**: not 300, not 337, not the stops, not the partial exits, not the take-profits.

## Files

All files are in `data/derived/edge_check/G/`.

- `common.py`: loaders, tapes, `curve()` and `partial()`. It imports `crowd_rules` and `stake_scale.model_eff` unchanged, by exec.
- `pull_ext.py` → `tapes_ext.json.gz`, `pull_ext.log`
- `check_curve.py` → `check_curve.txt`
- `curves.py` → `curves.json.gz`
- `sweep.py` → `sweep.txt`, `sweep_all.csv`
- `report_tables.py` → `report_tables.md`
- `fine.py` → `fine.txt`
- `choose.py` → `choose.txt`
- `sellers.py` → `sellers.txt`
- `robust.py` → `robust.txt`
- `twostage.py` → `twostage.txt`
- `tp_check.py` → `tp_check.txt`
- `dollars.py` → `dollars.txt`

Quoted from elsewhere and not recomputed here:
- the recent supply of 0.32 fires an hour and the live mix (half filled, a third of the fills third): the brief, 24.35-24.36;
- the first-seat wallet's 14.5-block hold: 24.29.
