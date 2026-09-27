**CHANGE to h = 8 (plateau 3-23).** h is the engine's hold setting. The sell lands 2-4 blocks after it, so h = 8 exits at blocks 10-12 after the seat. There it makes **+19.1% on the fit (73 fires) and +15.0% on the recent windows (19 fires)**, against +15.5% and +12.3% for today's 15, which exits at 17-19. The choice is out of sample: made on the recent windows alone, it reads +19.1% on the fit. Fire by fire it beats 15 there by +3.6 points, and 98% of 2,000 bootstraps agree. The long hold does not survive the same test. The fit's own choice (334, plateau 98-389) reads +2.9% on the recent windows.

# Hold sweep, reviewer F (Sep 27 2026)

The rule is unchanged: fleets >= 2 at block k-2, a 35-shot burst for seat E1. Every number uses the same yardstick: `stake_scale.model_eff` imported as `reach_table.py` does, second place in E1, $13 at 2570 $/ETH, the 6.18% surcharge of second +1, the tier fee on buy and sell, the 3% cap, the exit's own impact, and gas $0.33 a burst. The exit folds every buy and sell of the tape up to block E1+h.

The sweep covers every h from 1 to 1,200. What it shows:

- **Every set has the same short hump.** Exit blocks 7-14 peak at 11-13 in the fit, the recent windows, Sep 18-21, Sep 22-27 and the medians, and every curve drops about 3 points between blocks 12 and 15. Today's 15 sits just past that drop.
  - At exit block 11 the fit reads +19.5% and the recent +15.7%. At 15 they read +16.2% and +12.6%.
  - The drop has a mechanism. Snipers who bought in the first two seconds sell 12-17 blocks after their own buy (`drop.txt`). About a third of the fires in both periods have such a sell in E1+11..16.
- **The long hold has broken.** On the fit the curve climbs to +27% at 334-340, with a plateau from 101 to 393. On the recent windows it falls apart. The fires make +13-14% at 200-260, then lose 10 points between 260 and 280 as two fires dump in single blocks (0x80c0efae −92 points at block 279, 0x2b7508b0 −74 at 269). They read +3% at 300 and between −3.6% and +3.2% everywhere from 400 to 1,200.
  - The recent windows' lift over the refused launches is +15.7 points at 15 and −0.7 at 300.
- **Choices and their out-of-sample readings:**
  - Chosen on the fit, the hold is long (334, plateau 98-389) and fails on the recent windows: +2.9%, and +7.0% averaged over its plateau.
  - Chosen on the recent windows, the hold is short (8, plateau 3-23) and holds on the fit: +19.1%.
  - Chosen on Sep 18-21, the hold is long (338) and reads +18.7% on Sep 22-27. All of that comes from Sep 22-23 (+20.4% and +39.4%). On Sep 24-27 alone the same choice reads +3.0%.
- **Two-stage exits.** Six variants were tried and none beats the best fixed hold on both periods. The permutation null gives the trigger variants no information over a random exit. Stops hurt the recent 300-block hold (−3.6% against +3.0%). In 4 of the 6 recent dumps below −40% the mark falls from above −10% within 2 blocks, and a stop fills after the fall.
- **$ a day** at $13, 0.32 fires an hour, with the recent windows' returns. h = 8 makes $12.5 a day at full fill and $4.3 with the live mix. h = 15 makes $9.7 and $2.9. The fit's choice, 334, makes $0.4 and −$1.6.
  - The live mix: half the bursts fill, and a filled burst lands third one time in three.
  - At this stake the move from 15 to 8 is worth about $1.3 a day at the live mix.

Scripts are in `data/derived/edge_check/F/` and run from the repository root. They are offline except `pull_ext.py`. Each writes the `.txt` next to it. The command sits beside each number below.

## 1. Data, pricing and checks

- **Population** (`common.py`): the 15 crowd files plus round 1 A's two gap pulls, deduplicated by curve (C's population).
  - 735 launches: 563 fit and 172 recent.
  - The rule fires on **73 fit launches and 19 recent launches**: 18 in the committed 11 windows, plus 0x45bbf47f of gapA.
  - The four fit windows have 14, 29, 20 and 10 fires. Days are UTC days of the creation.
- **Tapes** (`common.tape`), b0..b0+640:
  - round 1 A's cache for the 91 fires and the gap pulls (real block stamps);
  - C's `tapes_extra` for the 85 sep2223 launches (real stamps);
  - round 1 A's `tapes_chk27` for 10 recent launches (real stamps);
  - `B/tapes` for the other 536. 155 of those have synthesised stamps, which give the same seat and surcharge by the definition of k. D's tapes are not needed.
- **Extension** (`pull_ext.py` → `ext.json.gz`, `pull_ext.txt`): every Buy/Sell from b0+641 to b0+1240 on all 735 curves. That is 735 paced `eth_getLogs` calls, 12,495 events, zero retries.
  - With the extension, **every launch has a price at every h from 0 to 1,200** (`build.txt`).
  - The same run re-pulled b0..b0+640 for a seeded sample of 40 launches from all four cache sources: 3,221 events, **identical 40/40**.
- **Pricer** (`check_paths.py` → `check_paths.txt`): `common.paths` is `model_eff` unrolled over the hold, so one pass gives every h.
  - It was checked against the imported `model_eff` at every h from 1 to 600, second and third place, on the 92 fires and 60 random refused launches: 182,400 pairs, **max |difference| 0.00e+00**.
  - It reproduces the committed numbers: fit 73 fires **+16.22% at 15 and +26.32% at 300**; recent 18 fires **+12.81% and +3.46%**; with the gap fire, 19 fires +12.56% and +3.01%.
- **Refused launches** (490 fit, 153 recent) are priced at every block, not every 5th.

## 2. The curves (task 1)

`python3 data/derived/edge_check/F/curves.py > data/derived/edge_check/F/curves.txt`

Every h from 1 to 1,200 and every set is in `curves.csv`: fit, rec, rec18, all, each fit window, Sep 18-21, Sep 22-27, each day. The columns are fires, mean, median, win, dead (< −40%), sd, $/fire after gas, refused n, refused mean and lift.

The table below shows the exact exit block E1+h. Lift is the fires' mean minus the refused launches' mean at the same h, in points.

|   h | fit mean | median | win | dead |   sd | $/fire | lift | recent mean | median | win | dead |   sd | $/fire | lift |
|----:|---------:|-------:|----:|-----:|-----:|-------:|-----:|------------:|-------:|----:|-----:|-----:|-------:|-----:|
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

The table starts at 1, 5, 10. The blocks between them matter, so here is the fine curve (`landed.py` prints it by setting; the exact-block values are in `curves.csv`):

- **fit**, blocks 7-16: +16.8, +17.6, +17.0, +18.6, **+19.5**, +19.1, +18.8, +17.9, +16.2, +16.2
- **recent**, blocks 7-16: +10.6, +11.4, +14.0, +14.2, **+15.7**, +15.1, +13.5, +12.5, +12.6, +12.9
- **Sep 18-21**: peak +24.2 at block 13, +21.5 at 15. **Sep 22-27**: peak +15.1 at block 11, +10.6 at 15.
- The medians show the same hump. The fit's median is +12.9% at 11 and +8.0% at 15. The recent median is +5.7% at 11 and +0.1% at 15.

Mean by hold for each fit window, the Sep 18-21 / Sep 22-27 split, the committed 18 recent fires and all 92 fires (`curves.txt`; win, $/fire and lift for each are printed below this table there):

```
    h    sep1819 n14    sep2021 n29    sep2223 n20   sep23day n10      early n41       late n51      rec18 n18        all n92
    1         +15.6%         +11.9%          +6.2%         +15.5%         +14.2%          +5.3%          +0.7%          +9.3%
    5         +18.2%         +15.3%         +12.4%         +18.8%         +17.5%         +11.1%          +8.2%         +13.9%
   10         +20.6%         +20.8%         +11.9%         +23.2%         +22.3%         +14.1%         +13.8%         +17.7%
   15         +27.5%         +16.4%          +9.0%         +14.4%         +21.5%         +10.6%         +12.8%         +15.5%
   20         +25.7%         +14.4%         +13.0%         +17.7%         +19.5%         +12.7%         +12.4%         +15.7%
   30         +29.7%         +11.7%         +13.7%         +14.5%         +18.9%         +10.3%          +6.7%         +14.1%
   60         +22.5%         +15.4%         +13.4%         +15.4%         +19.1%          +9.4%          +4.4%         +13.7%
  100         +17.3%         +18.2%         +24.1%         +20.2%         +19.1%         +13.4%          +0.8%         +15.9%
  150         +10.7%         +21.6%         +30.2%         +16.5%         +19.0%         +18.9%         +11.1%         +18.9%
  200         +12.3%         +24.2%         +32.4%         +17.7%         +21.3%         +21.1%         +14.0%         +21.2%
  300         +18.9%         +26.2%         +35.5%         +18.9%         +24.6%         +19.0%          +3.5%         +21.5%
  400         +23.6%         +12.6%         +28.5%         +13.6%         +16.6%         +13.6%          +1.7%         +14.9%
  600         +26.3%         +13.1%         +28.7%         +11.0%         +17.9%         +13.4%          +2.4%         +15.4%
 1200         +23.3%         +19.4%         +27.3%          -3.3%         +20.3%         +11.3%          +3.8%         +15.3%
```

Mean by day (Sep 19 and Sep 27 have one fire each):

```
    h     Sep 18 n13      Sep 19 n1      Sep 20 n7     Sep 21 n20     Sep 22 n19     Sep 23 n13      Sep 24 n9      Sep 25 n4      Sep 26 n5      Sep 27 n1
   10         +21.2%         +12.8%         +35.3%         +18.9%         +10.7%         +18.9%         +15.1%         +27.1%          +7.2%         -10.0%
   15         +28.2%         +18.1%         +29.3%         +14.5%          +7.9%         +11.9%         +14.8%         +22.0%          +5.5%         -10.0%
   30         +32.0%          -0.2%         +13.9%         +13.2%         +12.1%         +13.0%          +6.0%         +25.7%          -3.9%         -10.0%
   60         +23.3%         +12.6%         +11.7%         +19.3%          +9.0%         +17.7%          +3.1%         +24.1%          -7.3%         -10.0%
  150         +10.5%         +12.9%         +23.0%         +23.5%         +22.1%         +26.6%          +1.8%         +43.8%          -6.2%         +37.7%
  300         +18.6%         +22.1%         +28.8%         +27.1%         +22.0%         +38.1%          +1.5%         +47.9%         -22.1%         -37.6%
  600         +27.5%         +10.8%          -1.7%         +18.8%         +14.9%         +32.1%          +5.0%         +36.2%         -33.3%         -39.1%
```

What the curves say:

- **The short hump is in every set.** Exits at 10-12 beat exits at 15 in both periods, both halves and the medians.
- **The long hump belongs to the fit.** Sep 21, 22 and 23 carry it, at +27%, +22% and +38% at 300. Every recent day except Sep 25 (4 fires) reads worse at 300 than at 15.
- **Recent lift at long holds is gone.** The refused launches drift up at long holds recently (+3.7% at 300, +5.9% at 600), so the recent lift is below +12 points everywhere past 25. At 5-20 it stays +13 to +19.

## 3. The choices and their plateaus (task 2)

`python3 data/derived/edge_check/F/choose.py > data/derived/edge_check/F/choose.txt` (exact exit block) and
`python3 data/derived/edge_check/F/landed.py > data/derived/edge_check/F/landed.txt` (the engine's setting S, which lands at S+2..S+4, each fire averaged over the three).

The plateau is every h whose mean on the choosing set is at least the optimum's mean minus one standard error (sd/√n at the optimum). The tables give the contiguous run around the optimum. "Anywhere" counts every qualifying h in 1..600.

Exact exit block:

| chosen on | optimum | there | plateau (anywhere) | read on | at the optimum | over the plateau (range) | read-on set at 15 |
|---|---:|---:|---|---|---:|---|---:|
| fit (73) | 337 | +27.0% (se 7.0) | 101-393 (329 of 600) | recent | **+2.9%** | +7.0% (−2.9 .. +14.2) | +12.6% |
| recent (19) | 11 | +15.7% (se 6.4) | 7-23 (155 of 600; also 131-268) | fit | **+19.5%** | +17.1% (+15.4 .. +19.5) | +16.2% |
| Sep 18-21 (41) | 334 | +26.1% (se 7.9) | 149-374 (344; also 7-30, 95-145) | Sep 22-27 | **+18.7%** | +20.0% (+16.2 .. +23.5) | +10.6% |
| Sep 22-27 (51, reverse) | 228 | +23.5% (se 8.5) | 123-393 | Sep 18-21 | +21.4% | +22.0% | +21.5% |

As the engine runs it, by setting S (landed):

| chosen on | S | there | plateau | read on | at S | over the plateau | read-on set at S = 15 |
|---|---:|---:|---|---|---:|---|---:|
| fit | 334 | +27.0% | 98-389 | recent | **+2.9%** | +7.0% | +12.3% |
| recent | **8** | +15.0% (se 6.2) | **3-23** | fit | **+19.1%** | +16.9% | +15.5% |
| Sep 18-21 | 338 | +26.0% | 145-370 | Sep 22-27 | +18.7% | +20.0% | +11.2% |

The choices over 1..1,200 are the same (`choose.txt`); nothing past 600 beats them. The 11-block running-mean optima are 337 on the fit, 243 on the recent windows and 248 pooled.

How to read the three choices:

1. **Choose on the fit, read on the recent windows: the long hold fails.** 334-337 reads +2.9% on the recent windows, 9.4 points below 15. A hold drawn anywhere in the fit's plateau reads +7.0% on average.
2. **Choose on the recent windows, read on the fit: the short hold holds.** S = 8 (exit 10-12) reads +19.1% on the fit, 3.6 points above 15. The plateau 3-23 contains 15.
   - The plateau is wide because it is measured against the level's standard error (6.2 points on 19 fires).
   - Two holds priced on the same fires differ by far less than that. Section 4 does the paired test.
3. **Choose on Sep 18-21, read on Sep 22-27: the long hold reads well, but only on the fit's two days.** It reads +20.4% on Sep 22 and +39.4% on Sep 23, then +3.0% on the 19 recent fires (`checks.txt`).

## 4. Robustness (task 3)

`python3 data/derived/edge_check/F/robust.py > data/derived/edge_check/F/robust.txt`; paired tests and leave-one-out on the landed curve in `landed.txt`.

**Bootstrap, 2,000 resamples of the fires (seed 7), exact exit block** (`robust.txt` a):

| set | optimal h: 5/25/50/75/95th pct | share 10-30 | 201-300 | 301-400 | mean at 15 [95%] | mean at 11 [95%] | P(11 > 15) |
|---|---|---:|---:|---:|---|---|---:|
| fit | 11 / 262 / 311 / 334 / 341 | 8% | 23% | 59% | +16.2% [+8.8, +24.1] | +19.5% [+11.9, +27.2] | 98% |
| recent | 11 / 11 / 13 / 241 / 241 | 56% | 38% | 0% | +12.6% [+1.4, +25.5] | +15.7% [+4.3, +28.9] | 98% |
| all 92 | 11 / 238 / 248 / 277 / 340 | 14% | 61% | 17% | +15.5% [+9.0, +22.3] | +18.7% [+12.2, +25.5] | 100% |

**The same bootstrap on the landed curve** (`robust.txt` e):

| set | optimal S (median) | mean at S = 8 [95%] | S = 15 | S = 334 | P(8 > 15) | P(334 > 8) |
|---|---:|---|---|---|---:|---:|
| fit | 307 | +19.1% [+11.6, +26.5] | +15.5% [+8.2, +23.2] | +27.0% [+14.4, +40.8] | 98% | 91% |
| recent | 16 (46% in 1-9, 40% in 201-300) | +15.0% [+4.2, +27.6] | +12.3% [+0.5, +26.5] | +2.9% [−15.1, +25.9] | 92% | 7% |

- The optimal h is bimodal in every set. Most fit resamples pick the long hold, and most recent resamples pick the short one.
- When a fit resample picks a short hold, it picks 11 (5.2% of resamples). When a recent resample picks a long one, it picks 241 (23%) or 210-235.
- The recent 95% interval for S = 8 is +4.2% to +27.6%. For S = 334, 45% of recent resamples are negative.

**Fire by fire against S = 15** (`landed.txt`, paired bootstrap, gain in points [95%], P(gain > 0)):

| set | S = 8 | S = 9 | S = 240 | S = 300 |
|---|---|---|---|---|
| fit (73) | **+3.6 [+0.3, +6.7] 98%** | +3.6 [+0.7, +6.4] 99% | +9.7 [−0.2, +21.0] 97% | +10.8 [+0.2, +23.2] 98% |
| recent (19) | +2.7 [−1.2, +6.3] 92% | +2.5 [−1.3, +6.0] 91% | +1.8 [−13.5, +19.1] 58% | −9.3 [−23.6, +7.6] 12% |
| Sep 18-21 (41) | +3.7 [−1.2, +8.6] 92% | +4.3 [−0.1, +8.9] 97% | +2.9 65% | +5.2 76% |
| Sep 22-27 (51) | +3.1 [+0.8, +5.5] 100% | +2.6 [+0.7, +4.6] 100% | +12.2 99% | +7.8 90% |

- **The short gain holds in every set, with a spread of a few points.** It is positive in 3 of the 4 fit windows: +6.4, +2.8 and +5.1, with −2.4 on sep1819.
- **By day it is positive on 6 of the 8 days with 3 or more fires.** The exceptions are Sep 18 at −3.9 and Sep 24 at −1.1.
- **The long gain comes from the fit and does not hold.** It is +9.7 to +12 on the fit and on Sep 22-27 (which includes Sep 22-23), and a coin flip or worse on the recent windows.

**Leave one fit window out** (`robust.txt` b, `landed.txt`). Choosing over all settings on three windows gives 307-338 every time. On the window left out that choice reads +18.5% on sep1819, +26.9% on sep2021, +33.9% on sep2223 and +20.1% on sep23day. S = 15 reads +26.1%, +14.1%, +9.7% and +16.4% on the same windows.

- The long hold wins 3 of 4 held-out fit windows. Inside the fit period the long hold was real. It stopped on Sep 24.
- Restricted to settings 1-60, the three-window choice is S = 8, 26, 9 and 9. Those read +23.7%, +11.7%, +12.3% and +19.8% on the window left out, against 15's +26.1%, +14.1%, +9.7% and +16.4%. That beats 15 on 2 of the 4 held-out windows.
- The fixed S = 8 beats 15 on 3 of the 4, as the per-window gains above show.

**The sell landing late** (`robust.txt` c; exact-block mean at h, h+2, h+4):

| setting | fit h / h+2 / h+4 | recent h / h+2 / h+4 |
|---:|---|---|
| 8 | +17.6 / +18.6 / +19.1 (lag 1-5: +17.0 .. +19.5) | +11.4 / +14.2 / +15.1 (lag 1-5: +13.5 .. +15.7) |
| 9 | +17.0 / +19.5 / +18.8 | +14.0 / +15.7 / +13.5 |
| 11 | +19.5 / +18.8 / +16.2 | +15.7 / +13.5 / +12.6 |
| 15 | +16.2 / +15.4 / +15.7 | +12.6 / +12.9 / +12.0 |
| 20 | +16.7 / +16.8 / +16.3 | +12.2 / +9.4 / +9.1 |
| 240 | +25.2 / +25.2 / +25.2 | +13.5 / +14.2 / +14.0 |
| 300 | +26.3 / +26.4 / +26.4 | +3.0 / +3.0 / +2.9 |
| 337 | +27.0 / +26.9 / +27.0 | +2.9 / +2.8 / +3.0 |

- **S = 8 beats S = 15 at every lag from 1 to 5 blocks in both periods** (`landed.txt`, last lines).
- The late sell is why the recommendation is 8 and not the exact-block optimum 11. A setting of 11 lands at 13-15, on the drop.
- The late sell costs 15 almost nothing, because 15 already sits past the drop.

**The drop between blocks 12 and 15** (`python3 data/derived/edge_check/F/drop.py > data/derived/edge_check/F/drop.txt`). Wallets that bought in the creation second or the seat block sell most often 12-17 blocks after their own buy.

- On the fit that window holds 76 of their 167 sells within E1+40: 20 at 12 blocks, 13 at 13, 4 at 14, 11 at 15, 11 at 16 and 17 at 17.
- 26 of the 73 fit fires and 7 of the 19 recent fires have such a sell in E1+11..16. The same wallets appear in both periods: 0x26558f89, 0x924378f2, 0x6c56103c.
- Exiting at 10-12 means selling before this cohort of first-second snipers. The edge depends on those bots keeping their ~15-block holds. If they shorten them, the hump moves earlier, and the curve will show it.

## 5. Two-stage exits (task 4)

`python3 data/derived/edge_check/F/twostage.py > data/derived/edge_check/F/twostage.txt`

Six variants were tried and no others:

- The trigger reads the mark at the end of each block, and the sell lands 2 blocks after the trigger.
- The fixed exits land 2 blocks late too.
- The partial exits sell half with its own impact on the curve, then fold the rest of the tape.

The best fixed hold is each period's own in-sample optimum: fit 337 at +27.0%, recent 11 at +15.7%.

| variant | fit | recent | base hold (same lag) fit / recent | triggered fit / recent | beats best fixed on both | null P(gain ≥ real) fit / recent |
|---|---:|---:|---|---|---|---|
| V1 take profit +30% else 300 | +23.0% | +8.3% | +26.4% / +3.0% | 51% / 32% | no | 33% / 21% |
| V2 take profit +60% else 300 | +25.9% | −0.6% | +26.4% / +3.0% | 30% / 11% | no | 19% / 92% |
| V3 stop −30% else 300 | +26.9% | −3.6% | +26.4% / +3.0% | 8% / 26% | no | 16% / 96% |
| V4 stop −20% else 15 | +15.4% | +12.9% | +15.4% / +12.9% | 3% / 0% | no | 53% / 100% |
| V5 half at 9, half at 300 | +23.0% | +9.4% | 9: +19.5% / +15.7%; 300: +26.4% / +3.0% | – | no | – |
| V6 half at 15, half at 300 | +20.9% | +8.0% | 15: +15.4% / +12.9%; 300: +26.4% / +3.0% | – | no | – |

**Null test (24.34 discipline).** Each permutation pairs every fire's exit decision with another fire's path in the same period, and reads the result on the fire's own path (1,000 permutations). The table gives the share of null draws that gain at least as much over the base hold as the real trigger.

- No trigger is informative in both periods. The best case is V1 on the recent windows, where 21% of random exit timings do as well.
- The null variants beat the best fixed hold on both periods in 0.0-0.1% of draws, and the real variants in 0 of 6.

**Stops.** Of the fires whose mark falls below −40% within 600 blocks, the fall from above −10% to below −40% takes one block in 8 of 12 on the fit and 3 of 6 on the recent windows (4 of 6 within 2 blocks). Two more fit fires never rose above −10% after the seat. A stop fills after the fall, which is why V3 costs the recent 300-block hold 6.6 points.

**Take-profit and partial exits.** The partial and take-profit variants only average the two humps. Each lands between the short and the long hold on each period, and none beats the short hold on the recent windows.

## 6. $ a day at $13 (task 5)

`python3 data/derived/edge_check/F/dollars.py > data/derived/edge_check/F/dollars.txt`

The assumptions:

- 0.32 fires an hour, which is 7.68 bursts a day.
- Each setting's sell lands at S+2..S+4.
- Full fill: every burst fills, at second place.
- Live mix: half the bursts fill, and a filled burst lands second 2 times in 3 and third 1 time in 3 (third place priced with n_ahead 2).
- Gas is $0.33 on every burst.

| setting | returns of | 2nd place | 3rd place | $/day full fill | $/day live mix | $/week live mix | weekly sd |
|---:|---|---:|---:|---:|---:|---:|---:|
| 15 (today) | recent | +12.3% | +8.3% | +9.74 | +2.93 | +20.5 | 20.3 |
| 15 | fit | +15.5% | +9.4% | +12.95 | +4.19 | +29.3 | 22.6 |
| 334 (fit's choice) | recent | +2.9% | −0.4% | +0.40 | −1.62 | −11.3 | 31.3 |
| 334 | fit | +27.0% | +20.8% | +24.39 | +9.91 | +69.3 | 41.3 |
| **8 (recent's choice, recommended)** | recent | +15.0% | +10.8% | **+12.46** | **+4.25** | +29.8 | 18.8 |
| 8 | fit | +19.1% | +12.5% | +16.51 | +5.89 | +41.2 | 23.3 |
| 240 (reference) | recent | +14.1% | +10.6% | +11.58 | +3.94 | +27.6 | 30.5 |
| 300 (reference) | recent | +3.0% | −0.3% | +0.41 | −1.61 | −11.3 | 30.8 |

- **At the recent returns and the live mix, h = 8 is worth $4.3 a day against $2.9 for 15.** That is +$9 a week, with a weekly standard deviation near $19-20.
- The money is small either way. The change is worth making because it is free: one setting, and a lower spread than 15.
- 240 reads about as well as 8 on the recent windows and better on the fit, but it is not recommended:
  - it was not the choice of any single period;
  - its recent reading sits 20-40 blocks before a 10-point cliff;
  - its recent weekly sd is $31 against $19.

## 7. What the verdict rests on, and what would change it

- **The rest:**
  - The recommendation is the recent windows' own choice, confirmed out of sample on the fit.
  - It is inside the plateau around 15, but paired fire by fire it beats 15 in every set.
  - It is robust to the sell landing 1-5 blocks late.
  - It has a mechanism on the tapes: the first-two-seconds snipers' 12-17 block exits.
- **What would move it back to 15 or later:** the hump migrating on new fires. Watch the chain-scored fires' marks at E1+10..12 against E1+17..19. A drift of the snipers' exits to under 10 blocks would erase the gain.
- **What would bring back the long hold:** the recent lift at 200-300 returning to the fit's +22-27 points. It stands at −0.7 at 300 and +9 to +11 at 200-240.
  - The data show when the long hold worked: Sep 21-23, on 52 fires.
  - They do not show it working after Sep 23.

## Commands (repository root)

```
python3 data/derived/edge_check/F/pull_ext.py   > data/derived/edge_check/F/pull_ext.txt     # RPC: tapes to b0+1240, cache check (40/40)
python3 data/derived/edge_check/F/check_paths.py > data/derived/edge_check/F/check_paths.txt # pricer == model_eff; committed numbers reproduced
python3 data/derived/edge_check/F/build.py      > data/derived/edge_check/F/build.txt        # paths.npz + meta.json: 735 launches x h 0..1200, 2nd and 3rd place
python3 data/derived/edge_check/F/curves.py     > data/derived/edge_check/F/curves.txt       # task 1 (and curves.csv, every h, every set)
python3 data/derived/edge_check/F/choose.py     > data/derived/edge_check/F/choose.txt       # task 2, exact exit block
python3 data/derived/edge_check/F/landed.py     > data/derived/edge_check/F/landed.txt       # tasks 2-3 by engine setting (lag 2-4), paired tests, LOWO, lag 1-5
python3 data/derived/edge_check/F/robust.py     > data/derived/edge_check/F/robust.txt       # task 3: bootstrap, LOWO, late sell, days
python3 data/derived/edge_check/F/drop.py       > data/derived/edge_check/F/drop.txt         # the sells at E1+11..16
python3 data/derived/edge_check/F/twostage.py   > data/derived/edge_check/F/twostage.txt     # task 4
python3 data/derived/edge_check/F/dollars.py    > data/derived/edge_check/F/dollars.txt      # task 5
python3 data/derived/edge_check/F/checks.py     > data/derived/edge_check/F/checks.txt       # rec18, the Sep 18-21 choice by day, refused at S8, medians
```
