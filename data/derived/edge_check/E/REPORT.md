**Verdict: CHANGE to h = 9 (plateau 3-23).** Set HOLD_BLOCKS to 9 instead of 15; the sell then lands at E1+11 to E1+13.

At h = 9 the fires make **+19.1% on the fit** (73 fires) and **+14.8% on the recent set** (19 fires), with the sell landing 2-4 blocks late as the engine sells. The setting 15 makes +15.5% and +12.3% on the same basis. Sold exactly at E1+9, the means are +17.0% and +14.0%.

Out of sample:
- **Chosen on the recent set alone** (setting 8, plateau 3-23), the short hold reads **+19.1% on the fit**, 3.6 ± 1.6 points above 15 (paired, per fire).
- **The fit's own choice fails.** Chosen on the fit alone, the best hold is 337 blocks (plateau 101-393). It reads **+2.9% on the recent set**, against +12.6% at 15.

The long hold is out, and the short end is the answer. Inside the short end, 9 beats 15 by about 3 points on both periods for one reason: 36-42% of fires lose more than 2 points between their block 11-15 peak and block 16. A 15-block setting sells into that dip; a 9-block setting sells ahead of it.

# Hold sweep, reviewer E (Sep 27 2026)

All scripts are in `data/derived/edge_check/E/` and run from the repository root. Each one's output is saved next to it as `.txt`, and each section below names the command behind its numbers.

## 0. Data, yardstick, reproduction

**Population.** The fit is the four crowd files of Sep 18-23: 563 launches, 73 fires. The recent set is the eleven committed files of Sep 24-27 plus round 1 A's two gap pulls (gapA, gapB): 172 launches, 19 fires. The committed files alone are 160 launches and 18 fires, and the tables list them as `rec18`.

**Yardstick.** A fire is fleets >= 2 at block k-2 (`crowd_rules.cums/at`, exec'd as in `reach_table.py`). Pricing is `stake_scale.model_eff`, exec'd with `sys.argv` set first:
- second place in the E1 block, $13 at 2570 $/ETH;
- the 6.18% surcharge of second +1, the tier on the buy and on the sell, the 3% cap;
- later buys folded by their ETH, the exit's own impact;
- gas $0.33 a burst.

"h" is the block of the sell: the position is valued at the end of block E1+h, after every Buy and Sell up to that block.

**Tapes.** Blocks b0..b0+640 come from A's caches (the 91 fires and the gaps, real stamps), then C's `tapes_extra` (85 sep2223 launches, real stamps), then `B/tapes` (536 launches). Every one of the 735 launches has a tape.
- To reach 1,200 blocks I pulled every launch's Buy/Sell events for b0+641..b0+1240 myself: `python3 data/derived/edge_check/E/pull_ext.py` → `tapes_ext.json.gz`.
- The pull used the public RPC, 4 threads, 0.15 s after each call, and exponential back-off. It took 120 s, hit 128 responses of 429 (all retried) and lost no launch.
- All 735 launches now reach E1+1200.

**One pass per launch.** `common.path()` is `model_eff` made incremental over the hold, so each launch is priced once for every h.
- `python3 data/derived/edge_check/E/check_path.py` compares it with the imported `model_eff` 16,170 times (every launch, 11 holds, second and third place). The largest difference is 0.00e+00.
- The same run reproduces rounds 1-2 exactly: fit h15 +16.22%, h300 +26.32%; recent 19 fires h15 +12.56%, h300 +3.01%; the committed 18 fires h15 +12.81%, h300 +3.46%.

**The sweep.** `python3 data/derived/edge_check/E/sweep.py` prices every launch at every h from 0 to 1200, at second place and at third place. It writes `paths.json.gz`, which every later script reads.

## 1. The curves

Commands:
- `python3 data/derived/edge_check/E/curves.py > curves.txt` writes every group at every h from 1 to 1200 into `curves.csv`. The refused launches are priced at every block, not every fifth.
- `python3 data/derived/edge_check/E/tables_md.py > tables_md.txt` prints the two tables below.
- `python3 data/derived/edge_check/E/days.py > days.txt` gives every group at h = 9, 11, 15, 300.

Column definitions:
- Dead means below −40%.
- $/fire is after $0.33 gas, at $13.
- Lift is the fires' mean minus the refused launches' mean at the same h (fit 490 refused, recent 153).

| h | fit mean | median | win | dead | sd | $/fire | lift | recent mean | median | win | dead | sd | $/fire | lift |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | +11.5% | +5.7% | 59% | 0% | 0.25 | +1.17 | +15.6% | +0.7% | -3.1% | 32% | 0% | 0.20 | -0.24 | +7.7% |
| 5 | +15.5% | +10.2% | 66% | 0% | 0.29 | +1.69 | +19.4% | +7.8% | +0.0% | 53% | 0% | 0.23 | +0.68 | +13.1% |
| 10 | +18.6% | +11.6% | 66% | 3% | 0.35 | +2.09 | +20.1% | +14.2% | +5.7% | 63% | 0% | 0.25 | +1.52 | +17.2% |
| 15 | +16.2% | +8.0% | 66% | 3% | 0.34 | +1.78 | +18.5% | +12.6% | +0.1% | 58% | 0% | 0.28 | +1.30 | +15.7% |
| 20 | +16.7% | +8.0% | 64% | 3% | 0.35 | +1.84 | +18.8% | +12.2% | +0.0% | 53% | 0% | 0.31 | +1.25 | +15.0% |
| 25 | +16.4% | +9.3% | 64% | 3% | 0.34 | +1.80 | +17.9% | +9.1% | -0.5% | 47% | 0% | 0.32 | +0.86 | +12.0% |
| 30 | +16.1% | +8.5% | 64% | 3% | 0.34 | +1.76 | +18.1% | +6.7% | -0.7% | 42% | 0% | 0.32 | +0.54 | +9.4% |
| 35 | +16.5% | +8.3% | 66% | 3% | 0.35 | +1.81 | +18.5% | +4.9% | -3.0% | 42% | 0% | 0.30 | +0.30 | +7.9% |
| 40 | +15.9% | +7.4% | 66% | 3% | 0.35 | +1.73 | +18.0% | +4.0% | -3.0% | 47% | 0% | 0.30 | +0.19 | +7.8% |
| 45 | +15.3% | +9.3% | 64% | 3% | 0.33 | +1.66 | +17.1% | +4.6% | -3.0% | 47% | 0% | 0.30 | +0.27 | +8.5% |
| 50 | +16.7% | +9.3% | 66% | 3% | 0.35 | +1.84 | +18.3% | +4.7% | -3.0% | 42% | 0% | 0.29 | +0.28 | +8.6% |
| 55 | +16.6% | +9.3% | 66% | 3% | 0.36 | +1.83 | +18.1% | +3.9% | -3.0% | 42% | 0% | 0.29 | +0.18 | +6.3% |
| 60 | +16.2% | +9.3% | 66% | 3% | 0.36 | +1.78 | +17.3% | +4.1% | -3.0% | 42% | 0% | 0.29 | +0.20 | +5.8% |
| 80 | +16.6% | +6.1% | 63% | 4% | 0.41 | +1.83 | +17.9% | -2.9% | -1.0% | 42% | 5% | 0.26 | -0.71 | -2.5% |
| 100 | +19.9% | +11.8% | 64% | 5% | 0.45 | +2.26 | +21.0% | +0.7% | -1.0% | 47% | 5% | 0.37 | -0.23 | +1.5% |
| 120 | +21.6% | +11.9% | 67% | 5% | 0.46 | +2.48 | +22.1% | +2.4% | -1.0% | 47% | 5% | 0.38 | -0.02 | +2.7% |
| 140 | +22.1% | +12.9% | 67% | 5% | 0.48 | +2.54 | +22.0% | +9.8% | +2.8% | 53% | 0% | 0.39 | +0.94 | +8.7% |
| 160 | +20.4% | +11.6% | 66% | 7% | 0.49 | +2.33 | +20.3% | +10.0% | +2.8% | 53% | 0% | 0.39 | +0.97 | +6.6% |
| 180 | +21.8% | +13.0% | 66% | 7% | 0.50 | +2.50 | +21.3% | +11.9% | +2.8% | 53% | 0% | 0.45 | +1.21 | +8.1% |
| 200 | +23.3% | +13.0% | 67% | 7% | 0.52 | +2.70 | +22.7% | +13.2% | +2.9% | 58% | 0% | 0.45 | +1.38 | +9.1% |
| 220 | +23.9% | +15.5% | 66% | 7% | 0.55 | +2.77 | +23.4% | +13.8% | +2.9% | 53% | 0% | 0.45 | +1.46 | +11.3% |
| 240 | +25.2% | +15.5% | 68% | 7% | 0.56 | +2.95 | +24.8% | +13.5% | -1.0% | 47% | 0% | 0.45 | +1.43 | +10.7% |
| 260 | +25.3% | +15.5% | 64% | 7% | 0.57 | +2.96 | +24.8% | +12.8% | +0.8% | 53% | 5% | 0.45 | +1.33 | +9.7% |
| 280 | +26.3% | +15.7% | 64% | 8% | 0.59 | +3.09 | +27.1% | +3.6% | -4.9% | 42% | 11% | 0.47 | +0.14 | -0.0% |
| 300 | +26.3% | +20.7% | 67% | 8% | 0.59 | +3.09 | +26.8% | +3.0% | -4.9% | 37% | 11% | 0.47 | +0.06 | -0.7% |
| 350 | +25.3% | +18.3% | 63% | 11% | 0.61 | +2.96 | +25.4% | +2.9% | -4.5% | 42% | 11% | 0.48 | +0.04 | -0.1% |
| 400 | +19.2% | +13.5% | 59% | 16% | 0.64 | +2.16 | +19.8% | -1.4% | -11.0% | 37% | 21% | 0.54 | -0.51 | -4.0% |
| 450 | +19.8% | +14.5% | 59% | 18% | 0.64 | +2.24 | +21.1% | -0.5% | -11.0% | 37% | 26% | 0.54 | -0.40 | -4.8% |
| 500 | +18.6% | +12.8% | 58% | 19% | 0.65 | +2.09 | +19.8% | -3.4% | -11.0% | 37% | 26% | 0.55 | -0.77 | -8.7% |
| 550 | +19.5% | +5.6% | 55% | 19% | 0.66 | +2.20 | +19.9% | -1.9% | -11.0% | 42% | 26% | 0.55 | -0.57 | -8.4% |
| 600 | +19.6% | +10.8% | 52% | 19% | 0.67 | +2.22 | +20.0% | -0.9% | -14.4% | 42% | 26% | 0.59 | -0.44 | -6.8% |
| 700 | +16.7% | +0.3% | 51% | 21% | 0.67 | +1.84 | +18.3% | -2.6% | -11.0% | 37% | 26% | 0.57 | -0.66 | -7.2% |
| 800 | +17.3% | -1.7% | 48% | 23% | 0.73 | +1.92 | +18.8% | +2.3% | -11.0% | 37% | 32% | 0.65 | -0.03 | -1.7% |
| 900 | +17.7% | +1.2% | 51% | 25% | 0.73 | +1.97 | +18.5% | -1.7% | -13.8% | 37% | 37% | 0.66 | -0.56 | -5.1% |
| 1000 | +18.1% | +9.2% | 52% | 25% | 0.74 | +2.03 | +19.6% | -2.8% | -12.9% | 37% | 37% | 0.64 | -0.70 | -5.7% |
| 1100 | +20.2% | +9.4% | 52% | 26% | 0.75 | +2.29 | +22.0% | -3.3% | -12.9% | 37% | 37% | 0.63 | -0.76 | -5.4% |
| 1200 | +19.2% | +9.4% | 53% | 25% | 0.75 | +2.17 | +21.1% | +0.5% | -12.9% | 37% | 37% | 0.67 | -0.27 | -1.7% |

**Reading the curves.**
- **Where the two periods agree.** Both rise from block 1 to a peak at h = 10-12, and both dip at 13-19. The fit's curve is at +19.5% at h 11 and +16.2% at 15; the recent curve is at +15.7% and +12.6%.
- **Where they part.** Past block 20 they separate:
  - The fit stays near +16% to block 80, climbs to +26-27% at 280-350, and drops once dumps accumulate past 350 (dead 8% at 300, 19% at 600, 25% at 1,200).
  - The recent curve falls to +4% by block 35. Its hump at 140-260 (+10-14%) rests on one fire: `0x9f834b70` is +168% at 200-300, and without it h 220 reads +5.2% (`short_end.txt`). The curve is +3.0% at 300 and negative from 400 on.
- **Lift over the refused.** Fit: +15.6 to +27.8 points at every h from 1 to 1,200. Recent: +13.1 to +18.7 at h 5-20, then +5.6 to +9.3 at 35-60, −2.8 to +11.4 across 80-279 (the one-fire hump), and at most +0.2 from 280 on, negative on 902 of the 921 holds (`checks.txt`).
- **The refused.** The refused launches drift from −4% to −7% at h 1 up to about 0% (fit) or +2% to +6% (recent) over hundreds of blocks. That drift is the market, not the gate.

Every group at five holds (mean, win, dead, $/fire, lift). Day groups are UTC dates of the creation. The full curves for every group are in `curves.txt` and `curves.csv`, and every statistic at h 9, 11, 15 and 300 is in `days.txt`.

| group | fires / refused | h 9 | h 15 | h 60 | h 300 | h 600 |
|---|---:|---|---|---|---|---|
| fit | 73 / 490 | +17.0%, 66%, 3%, +1.88, +19.4% | +16.2%, 66%, 3%, +1.78, +18.5% | +16.2%, 66%, 3%, +1.78, +17.3% | +26.3%, 67%, 8%, +3.09, +26.8% | +19.6%, 52%, 19%, +2.22, +20.0% |
| sep1819 | 14 / 127 | +19.2%, 86%, 0%, +2.17, +20.1% | +27.5%, 86%, 0%, +3.24, +26.0% | +22.5%, 64%, 0%, +2.60, +24.2% | +18.9%, 71%, 21%, +2.12, +18.7% | +26.3%, 71%, 21%, +3.09, +28.6% |
| sep2021 | 29 / 160 | +19.1%, 59%, 0%, +2.15, +21.5% | +16.4%, 62%, 0%, +1.80, +17.5% | +15.4%, 66%, 0%, +1.67, +14.5% | +26.2%, 72%, 0%, +3.07, +27.3% | +13.1%, 48%, 21%, +1.37, +10.8% |
| sep2223 | 20 / 155 | +9.4%, 55%, 10%, +0.90, +12.4% | +9.0%, 50%, 10%, +0.85, +14.1% | +13.4%, 65%, 10%, +1.41, +14.3% | +35.5%, 65%, 15%, +4.28, +32.8% | +28.7%, 55%, 20%, +3.40, +27.8% |
| sep23day | 10 / 48 | +22.9%, 80%, 0%, +2.64, +27.9% | +14.4%, 80%, 0%, +1.54, +21.3% | +15.4%, 70%, 0%, +1.67, +22.3% | +18.9%, 50%, 0%, +2.13, +29.0% | +11.0%, 30%, 10%, +1.10, +19.2% |
| rec | 19 / 153 | +14.0%, 63%, 0%, +1.49, +17.2% | +12.6%, 58%, 0%, +1.30, +15.7% | +4.1%, 42%, 0%, +0.20, +5.8% | +3.0%, 37%, 11%, +0.06, -0.7% | -0.9%, 42%, 26%, -0.44, -6.8% |
| rec18 | 18 / 142 | +13.6%, 61%, 0%, +1.43, +16.4% | +12.8%, 56%, 0%, +1.33, +15.3% | +4.4%, 44%, 0%, +0.24, +6.1% | +3.5%, 39%, 11%, +0.12, -0.7% | +2.4%, 44%, 22%, -0.02, -4.8% |
| Sep18-21 | 41 / 280 | +20.6%, 71%, 0%, +2.34, +21.9% | +21.5%, 73%, 0%, +2.46, +21.0% | +19.1%, 68%, 0%, +2.15, +19.0% | +24.6%, 73%, 7%, +2.86, +24.7% | +17.9%, 56%, 22%, +1.99, +17.6% |
| Sep22-27 | 51 / 363 | +13.0%, 61%, 4%, +1.36, +16.6% | +10.6%, 57%, 4%, +1.05, +15.4% | +9.4%, 55%, 4%, +0.89, +11.7% | +19.0%, 51%, 10%, +2.15, +18.0% | +13.4%, 45%, 20%, +1.41, +11.6% |
| Sep 18 | 13 / 91 | +19.7%, 85%, 0%, +2.23, +20.6% | +28.2%, 85%, 0%, +3.34, +26.9% | +23.3%, 62%, 0%, +2.70, +26.0% | +18.6%, 69%, 23%, +2.09, +16.9% | +27.5%, 69%, 23%, +3.25, +29.0% |
| Sep 19 | 1 / 36 | +12.8%, 100%, 0%, +1.33, +13.5% | +18.1%, 100%, 0%, +2.02, +16.2% | +12.6%, 100%, 0%, +1.30, +11.5% | +22.1%, 100%, 0%, +2.54, +25.9% | +10.8%, 100%, 0%, +1.07, +14.9% |
| Sep 20 | 7 / 35 | +35.5%, 86%, 0%, +4.29, +33.3% | +29.3%, 86%, 0%, +3.47, +27.0% | +11.7%, 71%, 0%, +1.20, +13.1% | +28.8%, 71%, 0%, +3.42, +36.0% | -1.7%, 43%, 43%, -0.55, +4.4% |
| Sep 21 | 20 / 118 | +16.3%, 55%, 0%, +1.79, +19.1% | +14.5%, 60%, 0%, +1.56, +15.6% | +19.3%, 70%, 0%, +2.18, +16.8% | +27.1%, 75%, 0%, +3.19, +25.5% | +18.8%, 50%, 15%, +2.11, +13.9% |
| Sep 22 | 19 / 151 | +9.1%, 47%, 11%, +0.86, +12.3% | +7.9%, 42%, 11%, +0.70, +13.3% | +9.0%, 58%, 11%, +0.83, +9.1% | +22.0%, 63%, 16%, +2.53, +18.7% | +14.9%, 53%, 21%, +1.61, +13.0% |
| Sep 23 | 13 / 59 | +17.2%, 77%, 0%, +1.91, +22.9% | +11.9%, 77%, 0%, +1.21, +19.0% | +17.7%, 69%, 0%, +1.97, +27.0% | +38.1%, 54%, 0%, +4.63, +49.8% | +32.1%, 38%, 8%, +3.84, +41.3% |
| Sep 24 | 9 / 46 | +15.0%, 56%, 0%, +1.62, +17.4% | +14.8%, 44%, 0%, +1.59, +17.4% | +3.1%, 33%, 0%, +0.07, +6.2% | +1.5%, 44%, 0%, -0.13, -4.5% | +5.0%, 56%, 22%, +0.32, -1.7% |
| Sep 25 | 4 / 45 | +26.8%, 100%, 0%, +3.16, +28.6% | +22.0%, 75%, 0%, +2.53, +22.6% | +24.1%, 75%, 0%, +2.80, +29.1% | +47.9%, 75%, 0%, +5.90, +45.2% | +36.2%, 50%, 0%, +4.38, +27.6% |
| Sep 26 | 5 / 49 | +6.6%, 60%, 0%, +0.53, +9.8% | +5.5%, 80%, 0%, +0.38, +8.5% | -7.3%, 40%, 0%, -1.28, -9.9% | -22.1%, 0%, 40%, -3.20, -23.2% | -33.3%, 20%, 60%, -4.67, -31.6% |
| Sep 27 | 1 / 13 | -10.0%, 0%, 0%, -1.63, +0.5% | -10.0%, 0%, 0%, -1.63, +3.8% | -10.0%, 0%, 0%, -1.63, -8.2% | -37.6%, 0%, 0%, -5.22, -46.2% | -39.1%, 0%, 0%, -5.42, -62.4% |

**By day and by window.**
- At h 9 and h 15 every day but Sep 27 is positive. Sep 27 has one fire, at −10.0%.
- At h 300, Sep 26 and 27 lose; Sep 24 makes +1.5%, below the gas.
- Lift over the refused at h 9 is positive on every day and every window: +9.8 to +33.3 points, and +0.5 on Sep 27's single fire.

## 2. Choose on one set, read on the other

Commands: `python3 data/derived/edge_check/E/choose.py > choose.txt`, which works on the sell block h (1..600), and `robust.py > robust.txt` section (b), which works on the engine setting: the mean of the sell landing at h+2, h+3 and h+4.

Method:
- The choice is the h with the highest mean on the choosing set.
- The plateau is every h whose mean lies within one standard error of the optimum's mean on that set, where the standard error is the fires' sd at the optimum over √n.

| chosen on | h* (sell block) | mean, se | plateau | read on | at h* | h*+2 | h*+4 | the reading set at 15 |
|---|---:|---|---|---|---:|---:|---:|---:|
| fit (73) | 337 | +27.0%, 7.0 | 101-393 (+ 427-431, 471-486, 582-596) | recent | +2.9% | +2.8% | +3.0% | +12.6% |
| recent (19) | 11 | +15.7%, 6.4 | 7-23 (+ 131-268) | fit | +19.5% | +18.8% | +16.2% | +16.2% |
| Sep 18-21 (41) | 334 | +26.1%, 7.9 | 7-374 with gaps | Sep 22-27 | +18.7% | +18.8% | +18.7% | +10.6% |

On the engine setting (landing 2-4 blocks late):
- Fit → 334 (+27.0%, plateau 98-389); reads +2.9% on the recent set, where 15 reads +12.3%.
- Recent → 8 (+15.0%, plateau 3-23 and 127-274); reads +19.1% on the fit, where 15 reads +15.5%.
- Sep 18-21 → 338 (+26.0%); reads +18.7% on Sep 22-27. Split, that is +28.1% on Sep 22-23 and +3.0% on the recent days, where 15 reads +10.6% and +12.3%.

**Reading the choices.**
- **The fit's choice fails.** Its long plateau (101-393) reads +2.9% on the recent set, and averaged over its whole plateau it reads +6.1% there.
- **The recent choice passes.** It reads +19.5% on the fit, 3.3 points above the fit's own 15.
- **The Sep 18-21 split is not a pass for the long hold.** Its +18.7% out of sample is Sep 22-23 alone; on the recent days the same hold reads +3.0%.

**The short end chosen alone.** Restricted to settings 1..60, the fit chooses setting 9 (+19.1%, plateau 2-60) and Sep 18-21 chooses setting 10. Read out of sample against setting 15, with the paired difference per fire (`short_end.txt`):
- fit → setting 9 → recent: +14.8% against +12.3%, a gain of 2.5 ± 1.9;
- recent → setting 8 → fit: +19.1% against +15.5%, 3.6 ± 1.6;
- Sep 18-21 → setting 10 → Sep 22-27: +12.5% against +11.2%, 1.3 ± 0.9.

**The recommendation's plateau is 3-23**, the recent set's plateau around its optimum (7-23 in sell blocks). The fit's short-end plateau (2-60) contains it. The setting 15 lies inside both plateaus. The change is therefore a move along the same plateau to its ridge, not a new horizon. It is still worth making, for the reasons in section 3.

## 3. Robustness

Commands: `python3 data/derived/edge_check/E/robust.py > robust.txt` and `python3 data/derived/edge_check/E/short_end.py > short_end.txt`.

**Bootstrap (2,000 resamples of the fires, seed 7).**
- **Where the optimal h falls (1..600):**
  - Fit: median 311; 59% of resamples in 301-400, 23% in 201-300, 8% in 101-200, 7% in 10-13.
  - Recent: median 13; 51% in 10-13, 38% in 201-300, 4% in 14-20, 4% in 401-600.
  - Pooled 92 fires: 61% in 201-300, 17% in 301-400, 14% in 10-13.
- Every set's optimum is either short (10-13, or 14-20 in 4% of recent resamples) or long (200-400). The middle (21-100) wins in at most 1% of resamples.
- **The means (2.5-97.5%):**

| | fit | recent |
|---|---|---|
| h 15 | +16.4% (+8.8 to +24.1) | +12.3% (+1.4 to +25.5) |
| h 11 | +19.6% (+11.9 to +27.2) | +15.5% (+4.3 to +28.9) |
| setting 9, landing 2-4 blocks late | +19.3% (+11.5 to +26.7) | +14.6% (+3.8 to +27.2) |
| setting 15, same basis | +15.6% | +12.0% |
| h 300 | +26.5% | +2.8%, below zero in 44.5% of resamples |

- **Setting 9 against setting 15:** 9 comes out ahead in 99% of the fit's resamples, 91% of the recent's and 100% of the pooled.

**Leave one window out of the fit.**
- **Over 1..600:** the other three windows always choose 311-341. The left-out window reads +18.5% (sep1819), +26.9% (sep2021), +33.9% (sep2223) and +20.0% (sep23day). Within Sep 18-23 the long hold generalises across windows; it is the recent period that breaks it.
- **The short end alone (1..60, landing):** the choice is setting 8, 26, 9 and 9. It reads −2.4 ± 5.9 on sep1819 and −2.4 ± 3.1 on sep2021 (where the choice was 26), and +2.6 ± 1.7 on sep2223 and +3.3 ± 2.1 on sep23day, all against setting 15.
- **Setting 9 against 15 directly, by window:** +0.1, +6.1, +2.6, +3.3 points. By day it is ahead on 7 days, behind on 2, level on 1. By fire it is ahead on 29 and behind on 20 (fit), and ahead on 10 and behind on 2 (recent).

**The sell landing late.** The engine counts HOLD_BLOCKS feed blocks after the fill and its sell lands after that; the one live 300-block trade was sold 302 blocks after its fill. Setting s against setting 15, both landing d blocks late (paired):

| d | 0 | 2 | 4 | 6 | 8 |
|---|---|---|---|---|---|
| fit, setting 9 − 15 | +0.8 ± 1.8 | +4.1 ± 2.0 | +3.1 ± 1.4 | −0.7 ± 1.3 | −1.5 ± 1.2 |
| recent, setting 9 − 15 | +1.4 ± 1.7 | +2.8 ± 1.6 | +1.5 ± 2.6 | +0.1 ± 2.1 | +3.4 ± 3.0 |

- If the sell lands anywhere from 2 to 8 blocks late with equal odds, setting 9 gives +17.6% against +16.3% (fit) and +13.6% against +11.5% (recent).
- **The downside is bounded.** No delay costs more than 1.5 points on the fit; at the measured delay of 2-4 the gain is 3-4 points.
- **The long candidates barely move with the delay.** h 300 moves by 0.1 points from h to h+4; h 337 reads +2.8% to +3.0% on the recent set at h+2 and h+4.

**Why the ridge is at 9-11.**
- **A general dip, not one launch.** From their peak in blocks 11-15 to block 16, 36% of fit fires and 42% of recent fires lose more than 2 points. The average per-block change is negative in blocks 12-14 on both periods (the fit through 15; `checks.txt`). These are the first sells by the seat's own crowd, about 1.2-1.9 s after the seat.
- **Not carried by a few fires.** Leave-one-out on the fit's gain of setting 9 over 15 (+3.6) ranges from +3.1 to +4.1; without its two largest gains it is +2.65.
- **Thinner on the recent set.** Its gain of +2.5 ranges from +1.5 to +3.7 leave-one-out, and is +0.85 without its two largest gains.

## 4. Two-stage exits

Command: `python3 data/derived/edge_check/E/twostage.py > twostage.txt`.

**Eight variants, fixed before looking and not tuned:**
- take-profit at +25% or +50% with a 300-block hold;
- take-profit at +25% with a 60-block hold;
- stop at −20% with a 300- or a 60-block hold;
- half at setting 9, half at 60, 150 or 300.

**How they are priced.**
- A trigger is read on the block-end value, and the sell lands 2-4 blocks later: the mean over d = 2, 3, 4, as for the fixed settings.
- The partial exits fold our own first sale into the curve. The same exits without our own impact differ by at most 0.1 point.

**Benchmarks.** Each period's best fixed setting, chosen in-sample (fit 334: +27.0%; recent 8: +15.0%), and the candidate setting 9.

| exit | fit | recent | vs best fixed (fit, recent) | vs setting 9 (fit, recent) |
|---|---:|---:|---|---|
| setting 9 | +19.1% | +14.8% | −7.9, −0.2 | 0, 0 |
| setting 15 | +15.5% | +12.3% | −11.5, −2.7 | −3.6, −2.5 |
| take-profit +25%, hold 300 | +22.8% | +13.6% | −4.1, −1.4 | +3.7, −1.2 |
| take-profit +50%, hold 300 | +25.4% | +4.1% | −1.5, −10.9 | +6.3, −10.7 |
| take-profit +25%, hold 60 | +17.8% | +10.4% | −9.1, −4.7 | −1.3, −4.4 |
| stop −20%, hold 300 | +23.3% | −2.5% | −3.7, −17.6 | +4.1, −17.3 |
| stop −20%, hold 60 | +13.7% | +4.6% | −13.2, −10.4 | −5.4, −10.1 |
| half at 9, half at 60 | +17.6% | +9.2% | −9.3, −5.8 | −1.5, −5.5 |
| half at 9, half at 150 | +19.9% | +12.5% | −7.0, −2.5 | +0.8, −2.3 |
| half at 9, half at 300 | +22.8% | +8.9% | −4.2, −6.1 | +3.7, −5.8 |

**None of the eight beats the best fixed hold on both periods, and none beats setting 9 on both periods.**
- **The null test.** For the five triggered variants I read the trigger on another fire's path (paths permuted across fires within each period, 1,000 permutations) and applied it to the fire's own path.
  - A permuted variant beats setting 9 on both periods in 0-1.5% of permutations, for any of the five in 1.5%.
  - The real variants never do.
- **The one near miss is informative, not a pass.** Take-profit +25% with a 300-block hold has an informative trigger on the recent set (permuted ≥ real in 3%), but it still trails setting 9 there by 1.2 points.
- **The stops confirm the earlier finding.** Among fires that cross −20% within 300 blocks, the block of the crossing drops by a median of 26.8 points (fit, 10 fires) and 44.7 points (recent, 6 fires). The stop's sell lands at a median of −34.5% and −30.2%. Dumps happen in one block, and a stop sells after them.

## 5. $ a day at $13, at the recent supply

Command: `python3 data/derived/edge_check/E/dollars.py > dollars.txt`.

**Assumptions.**
- Supply: 0.32 fires an hour, 7.68 a day.
- Full fill: every burst fills at second place.
- Live mix (as C/stats15.py): half the bursts fill; of the fills, two thirds land at second place and one third at third place.
- Gas: $0.33 on every burst.
- Basis: the engine setting, with the sell landing 2-4 blocks late.

| hold | on the fit returns: full fill | live mix | on the recent returns: full fill | live mix |
|---|---:|---:|---:|---:|
| h = 15 | $13.0/day | $4.2/day | $9.7/day | $2.9/day |
| fit optimum (setting 334) | $24.4/day | $9.9/day | $0.4/day | −$1.6/day |
| recent optimum (setting 8) | $16.5/day | $5.9/day | $12.5/day | $4.3/day |
| **recommendation, h = 9** | **$16.5/day** | **$5.9/day** | **$12.2/day** | **$4.1/day** |

- The same numbers with the sell exactly at E1+h are in `dollars.txt`. At h 15 they are $13.7 and $10.0 at full fill, and $4.5 and $3.0 with the live mix, identical to round 2.
- Moving from 15 to 9 adds about $2.5-3.5 a day at full fill and about $1.2-1.7 a day with the live mix.
- The long hold is worth −$1.6 a day with the live mix on the recent returns.

## 6. What this means for the rule

**Keep the gate.** It still separates at the short end in every window and on every day (lift at h 9: +9.8 to +33.3 points, +0.5 on Sep 27's single fire).

**Keep the sequential test.** Round 2 started it on the 15-block return. It should now be read on the return at the sell that setting 9 actually delivers (E1+11..13), with the same parameters: H0 is the break-even +2.5%, H1 the fit's +19% at that setting, sd 0.34.

**Beyond block 20 the two periods disagree, and the recent one is the market we trade.**
- The long hold made its money in Sep 18-23 on outsiders who kept buying after block 15. Round 2 measured that buying (the median, after block 15) falling from 0.57 to 0.19 ETH.
- The recent set loses from block 280 on, and the only recent hump past 100 blocks is one fire.
- Holding past block 20 is a bet that the fit's market comes back. The data give no sign that it has.

## Commands

Every script is in `data/derived/edge_check/E/`; run from the repository root:

```
python3 data/derived/edge_check/E/pull_ext.py > data/derived/edge_check/E/pull_ext.log      # tapes b0+641..b0+1240 (public RPC, paced)
python3 data/derived/edge_check/E/check_path.py > data/derived/edge_check/E/check_path.txt  # path() == model_eff; reproduction of rounds 1-2
python3 data/derived/edge_check/E/sweep.py                                                  # paths.json.gz: every launch, h 0..1200, 2nd and 3rd place
python3 data/derived/edge_check/E/curves.py > data/derived/edge_check/E/curves.txt          # curves.csv: every group, every h, fires and refused
python3 data/derived/edge_check/E/tables_md.py > data/derived/edge_check/E/tables_md.txt    # the tables of section 1
python3 data/derived/edge_check/E/days.py > data/derived/edge_check/E/days.txt              # every group at h 9, 11, 15, 300
python3 data/derived/edge_check/E/choose.py > data/derived/edge_check/E/choose.txt          # section 2 and leave-one-window-out (sell block)
python3 data/derived/edge_check/E/robust.py > data/derived/edge_check/E/robust.txt          # late landing, choices on the setting, bootstrap
python3 data/derived/edge_check/E/short_end.py > data/derived/edge_check/E/short_end.txt    # setting 9 vs 15 by delay, window, day; short-end choices
python3 data/derived/edge_check/E/twostage.py > data/derived/edge_check/E/twostage.txt      # section 4 with the null test
python3 data/derived/edge_check/E/dollars.py > data/derived/edge_check/E/dollars.txt        # section 5
python3 data/derived/edge_check/E/checks.py > data/derived/edge_check/E/checks.txt          # the lift ranges and the dip after block 11
```

`common.py` holds the population, the tape loaders, the exec'd `crowd_rules` and `stake_scale` code, and `path()`.
