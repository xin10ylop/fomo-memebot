**Verdict: CHANGE. Keep the gate (fleets >= 2 at block k-2) and the $13 stake, and sell after 15 blocks instead of 300.**
The 15-block version is positive in both periods:
- fit: 73 fires, +16.2% a fire, $1.78 a fire after gas, $32.5 a day;
- recent: 18 fires, +12.8% a fire, $1.33 a fire, $9.6 a day;
- the rule as it runs today (300 blocks) reads +26.3% on the fit and +3.5% recently ($56.4 and $0.9 a day).

**Stop the strategy** when a sequential test on chain-scored 15-block fires crosses its lower boundary. The test is an SPRT with
H0 = +2.5% (the gas break-even) against H1 = +15.5%, sd 0.33, boundaries ±2.94. If the edge is at break-even, that takes about
30 fires: 4 days at the recent 0.32 fires an hour, 2 weeks at the last 10 hours' rate. **Do not raise the stake** until the
test crosses the upper boundary.

The honest expectation at $13 is small. At the recent readings it is +$9 to +$30 a week. It is negative if the 15-block
decline since Sep 18 goes on, but KILL_USD caps the loss at about $10.

# Edge check, round 2, reviewer D (Sep 27 2026)

**How to read the numbers**
- Every number has the command that produces it beside it. The scripts are in `data/derived/edge_check/D/` and run from the
  repository root. Each one writes the `.txt` next to it.
- Yardstick everywhere: `stake_scale.model_eff`, $13 at ETH $2,570, second place in the seat block E1, gas $0.33 a fire, the
  surcharge by second, the 3% cap.
- **Fit** = the four windows Sep 18-23: 563 launches, 73 fires, 96 h.
- **Recent** = the eleven windows Sep 24-27: 160 launches, 18 fires, 60 h.
- A fire is the rule's (fleets >= 2 at k-2, `crowd_rules.cums/at`, as `reach_table.py`).
- "h15" means sold after block E1+15, and likewise for other holds.

## 0. What I rely on, checked

`python3 data/derived/edge_check/D/check_tapes.py` -> `check_tapes.txt`
- B's cached tapes equal A's independent pull on all 91 fires: 0 event lists differ, and the price differs by 0.0000 at
  15 and at 300 blocks.
- The yardstick reproduces `reach_table.txt`: fit 73 fires, +26.3%, $56.4 a day; recent 18 fires, +3.5%, $0.9 a day.

`python3 data/derived/edge_check/D/pull_tapes.py`
- This pulls the 85 fit launches (sep2223) that round 1 had no tape for. The tier comes from `launches_175_sep2223.json`
  and the stamps are synthesised as in B/pull_fast.py. Result: 85 ok, so all 723 launches are priced.

`python3 data/derived/edge_check/D/features.py` -> `features.txt`
- Prices every launch after every block 0..600 in one pass.
- It equals `model_eff` to 0.000000 at 15 and 300 blocks (checked on every 7th launch).

`python3 data/derived/edge_check/D/pull_shots.py`
- This pulls the ETH and gas of every transaction aimed at a curve in the creation second and the seat block (public RPC, 4
  threads, 0.25 s after each call, 392 s).
- The transactions equal crowd_raw's in every block of all 723 launches (0 of 5,348 blocks differ; `check_tapes.py`, last
  line).

`python3 data/derived/edge_check/D/base.py` -> `base.txt` reproduces round 1:

| | h15 | h300 | lift over refused at h15 | at h300 |
|---|---|---|---|---|
| fit | +16.2% | +26.3% | +18.5 | +26.8 |
| recent | +12.8% | +3.5% | +15.3 | −0.7 |

## 1. Question 3 first: a version that names no fleet?

**Answer: no.** No rule that ignores fleet identity beats the rule under 24.34's protocol. The creator's history and the
bundle's own selling add nothing measurable. The only reading that holds up in both periods is the discovery's own: the gate
with a short hold (sections 3-4).

**Protocol.** `python3 data/derived/edge_check/D/q3.py 300` -> `q3_h300.txt`, and `q3.py 15` -> `q3_h15.txt` (the baseline
held 15 blocks).
- Each family is fitted on the fit windows and read on the recent set.
- A variant passes if it:
  - beats the baseline's $/day on the fit;
  - is positive on each fit window;
  - keeps its win rate within 10 points and its dead rate within 5 points of the baseline;
  - fires at least 30 times;
  - matches or beats the baseline's $/day on the recent set.
- The reverse direction (fitted on the recent set, read on the fit) is also printed.
- Null test: the feature is permuted across launches within each period, 200 times. For each permutation I record (a) the
  number of passes and (b) the recent gain of the variant the fit would have picked.

| family (all tradable when they act) | passes vs the 300-block rule | permuted mean | passes vs the 15-block rule | fit-picked variant, recent $/day gain vs the 300-block rule (p against permuted) |
|---|---|---|---|---|
| wallets >= t at k-2, as the gate | 0/6 | 0.00 | 0/6 | wallets>=1: +11.8 (0.01) |
| shots >= t at k-2 | 0/6 | 0.00 | 0/6 | shots>=1: +12.7 (0.01) |
| direct senders >= t at k-2 | 0/3 | 0.00 | 0/3 | none positive on every fit window |
| relays >= t at k-2 | 0/3 | 0.00 | 0/3 | relays>=1: +16.1 (0.01) |
| ETH shot by k-2 >= e | 0/5 | 0.00 | 0/5 | eth>=0.01: +21.6 (0.00) |
| the rule and ETH shot >= e | 0/5 | 0.00 | 0/5 | +5.5 (0.00) |
| the rule, skip creators or named wallets seen before (history as of the launch) | 0/1 | 0.00 | 0/1 | none positive on every fit window |
| the rule, skip a template (shared named wallet or creator) whose earlier launches averaged < m | 2/4 | 0.26 (P(>=2) 0.06) | 0/4 | +0.0 (0.83) |
| the rule, skip a template with >= n earlier launches | 0/4 | 0.14 | 0/4 | +5.7 (0.06) |
| the rule, sell 3 blocks after the bundle has sold >= x, else at H | 0/15 | 1.08 | 0/15 | −4.5 (0.93) |
| the rule, hold to H only if >= m outsider wallets bought in E1+1..15, else sell at 15 | 0/18 | 0.49 | 0/18 | +0.1 (0.72) |
| the same on outsider ETH in E1+1..15 | 0/8 | 0.23 | 1/8 (null 1.84) | +2.1 (0.63) |

- **The two template passes are trivial.** They remove one fit fire and leave the recent set as it was ($0.9 to $0.9 or
  $1.6 a day).
- **The low p values of the gate families mean something narrow.** A crowd count by k-2 carries information, in both periods,
  compared with a random selection of launches. That is not the same as being better than the rule.
- **The looser counts do better recently but fail on the fit.** At 300 blocks (`q3_h300.txt`):

  | gate at k-2 | fit | recent |
  |---|---|---|
  | relays >= 1 | 152 fires, +15.8%, $65.8/day, win 55%, dead 13% | 39 fires, +10.9%, $16.9/day |
  | wallets >= 2 | 73 fires, +20.6%, $42.8/day | 20 fires, +11.8%, $9.7/day |
  | ETH shot >= 0.01 | 104 fires, +13.8%, $38.1/day | 18 fires, +26.5%, $22.4/day |

  They fail because they buy their fit $/day with win and dead rates the protocol forbids, or they lose to the rule on the fit.
- **At 15 blocks none of them beats the rule on the fit** (`q3_h15.txt`). The rule makes $32.5/day. The closest are relays >= 2
  at $32.4 (almost the same launches) and the template filters at $32.2. Among the counts that differ from the rule, the best is
  $26.1.

**The ETH shot, split** (`python3 data/derived/edge_check/D/q3b.py` -> `q3b.txt`). A split that holds in only one period is
not a rule.
- Inside the rule's fires, ETH >= 0.01 against < 0.01 at 300 blocks:
  - fit: +22.0% (61) against +48.4% (12);
  - recent: +11.7% (12) against −13.0% (6).

  The sign flips between periods. At 15 blocks: fit +16.2% against +16.3%, recent +14.5% against +9.4%.
- The recent strength of the ETH gate comes from 6 one-fleet launches at +56.1% (300 blocks). The same class on the fit was
  +2.3% at 300 blocks and +1.5% at 15, below the 2.5% gas break-even.

**Other readings of the same tables:**
- Direct senders at k-2 lose in both periods (fit 20 launches, −5.2% at 300 and −8.0% at 15).
- The bundle-exit family never helps: a dump is one block, and the bundle's first sell is the dump.
- The crowd-hold family (the discovery's crowd made into a hold rule) never beats a fixed hold.

## 2. Question 5: what the whole story shows that the pieces did not

**1. The 300-block hold was never part of the discovery.** Re-deriving 24.30 from the real fills
(`python3 data/derived/edge_check/D/q1.py` -> `q1.txt`):
- The 12 winners' curve price against our entry was +36.4% at +15 blocks, +32.5% at +60 and +31.6% at +600. Their gain was
  complete by block 15.
- The 31 others went from +5.0% at +15 to +20.5% at +600. That drift is the market's, not the crowd's.
- The discovery's horizon was 15 blocks. The 300-block hold came later, from the tables' Sep 22-23 window (24.30), where the
  crowd came over 30 s. Its out-of-sample check on Sep 20-21 was a tie (+11.2% at 15 blocks against +10.9% at 300 for that
  gate; REPORT 24.31, not re-run here).

**2. What the discovery measured survived. What it never measured failed.**
- The gate still predicts the crowd after the seat. That crowd is defined as >= 3 buys behind us in the seat block, or >= 4
  outsider wallets in the next 15 blocks, the midpoints of 24.30's winner/loser means. Share of launches with it (`q1.txt`):

  | | fit | recent |
  |---|---|---|
  | fires | 77% (56/73) | 78% (14/18) |
  | refused | 41% | 33% |

- The buying inside a 15-block hold is unchanged. The buying after it fell (`python3 data/derived/edge_check/D/q2b.py` ->
  `q2b.txt`). Outsiders' ETH per fire, mean / median:

  | | fit | recent |
  |---|---|---|
  | E1+1..15 | 0.235 / 0.132 | 0.274 / 0.137 |
  | E1+16..60 | 1.392 / 0.568 | 0.957 / 0.190 |

- Bundle dumps (the bundle sold >= 10% of its tokens):

  | | fit | recent |
  |---|---|---|
  | by E1+15 | 2 of 73 fires | 0 of 18 |
  | by E1+300 | 7 of 73 | 5 of 18 |

  The five recent fires with a dump made **+28.6% at 15 blocks and −17.8% at 300** (`q2b.txt`).
- The discovery itself still holds for every qualifying launch, not only the fires. Launches with the crowd after the seat
  (`python3 data/derived/edge_check/D/q1b.py` -> `q1b.txt`):

  | launches with the crowd after | fit (255) | recent (61) |
  |---|---|---|
  | 15 blocks | +12.1% | +13.3% |
  | 300 blocks | +17.7% | +21.2% |

  What moved is who collects the long hold. For the refused launches with that crowd, 300 blocks went from +12.9% to +25.1%.
  For the fires with it, from +34.7% to +7.9% (`q1.txt`).

**3. The 300-block hold hid a slow decay of the 15-block edge.**
- The rule's fires at 15 blocks, by day (`python3 data/derived/edge_check/D/q2.py` -> `q2.txt`):

  | Sep 18 | Sep 19 | Sep 20 | Sep 21 | Sep 22 | Sep 23 | Sep 24 | Sep 25 | Sep 26 | Sep 27 |
  |---|---|---|---|---|---|---|---|---|---|
  | +28.2% | +18.1% | +29.3% | +14.5% | +7.9% | +11.9% | +14.8% | +22.0% | +4.8% | −10.0% |

- The move to 300 blocks (Sep 23) came when the 15-block return had fallen to +8-12%, while 300 blocks read +22% and +38%
  on Sep 22-23.
- Over all 91 fires, the 15-block return falls 2.47 points a day (Spearman −0.20, one-sided permutation p 0.059). The
  300-block return falls 2.96 points a day (p 0.15). The refused launches show no trend (−0.74 and +0.45 points a day)
  (`python3 data/derived/edge_check/D/q5.py` -> `q5.txt`).
- Since Sep 25 22:27 the six fires make +1.5% at 15 blocks and −19.6% at 300 (`q2.txt`).

**4. The real fills already contained the gate.**
- On the 43 launches filled on Sep 17-20, 4 had >= 2 pre-tick wallets at k-2. All four were winners (+27.3%); none of the 31
  losers had them.
- On the 23 fills inside a crowd file, the rule would have fired on 2 (+35.2%) and refused 21 (−2.7%).
- The count over the whole creation second is higher for the losers (11.9 against 7.75 wallets). A late crowd is the race we
  lose. An early crowd is the one that pays (`q1.txt`).

**5. The supply is still falling** (`q5.txt`: covered hours from the union of the scan windows):

| day | Sep 18 | Sep 19 | Sep 20 | Sep 21 | Sep 22 | Sep 23 | Sep 24 | Sep 25 | Sep 26 | Sep 27 |
|---|---|---|---|---|---|---|---|---|---|---|
| qualifying launches an hour | 9.9 | 2.8 | 4.0 | 5.8 | 7.2 | 4.3 | 4.9 | 2.1 | 2.6 | 2.2 |
| fires an hour | 1.23 | 0.08 | 0.66 | 0.83 | 0.80 | 0.78 | 0.80 | 0.17 | 0.22 | 0.24 |

Over the fit, 5.75 launches and 0.75 fires an hour; over the recent set, 2.84 and 0.32. Round 1 A reads 1.3 launches and 0.1
fires an hour for the last 10 hours.

**6. Second place is optimistic, and the 15-block hold loses less for it.** The fires at second / third / fourth place
(`q5.txt`):

| | second | third | fourth |
|---|---|---|---|
| fit, 15 blocks | +16.2% | +9.9% | +4.9% |
| fit, 300 blocks | +26.3% | +20.1% | +15.1% |
| recent, 15 blocks | +12.8% | +9.0% | +7.3% |
| recent, 300 blocks | +3.5% | +0.5% | −1.0% |

**7. The recent 15-block mean rests on two fires** (`q5.txt`). Without its largest fire (+86%) it is +8.5%. Without the two
largest it is +4.6%. The median is +0.1%. The fit's is +13.3% without its two largest, median +8.0%. This is the main reason
the verdict carries a stop line rather than a promise.

## 3. Question 1: the discovery against the rule

**What the real winners had.** `q1.txt` reproduces 24.30's table: 12 winners (actual > +5%) against 31 others.

| | winners | others |
|---|---|---|
| buys behind us in the seat block | 5.17 | 1.45 |
| buys in the next 15 blocks | 6.67 | 2.23 |
| wallets in the next 15 blocks | 5.5 | 2.03 |
| ETH in the next 15 blocks | 0.234 | 0.053 |
| price +60 blocks vs entry | +32.5% | +1.9% |
| price +600 blocks vs entry | +31.6% | +20.5% |
| pre-tick wallets at k-2 (a reading 24.30 did not print) | 1.0 | 0.065 |

**The readings side by side** (`q1b.txt`; $/day at $13 after gas; the last column is $/day on the four fit windows, in order):

| reading | fit | recent | fit windows |
|---|---|---|---|
| gate (the rule), 15 blocks | 73 fires, +16.2%, win 66%, dead 3%, $32.5/day | 18, +12.8%, win 56%, dead 0%, $9.6/day | +47 +36 +14 +42 |
| gate, 60 | 73, +16.2%, $32.5/day | 18, +4.4%, $1.7/day | +38 +33 +23 +46 |
| gate, 150 | 73, +21.2%, $44.2/day | 18, +11.1%, $8.0/day | +15 +50 +59 +50 |
| gate, 300 (as run) | 73, +26.3%, dead 8%, $56.4/day | 18, +3.5%, dead 11%, $0.9/day | +31 +61 +70 +58 |
| crowd after the seat (oracle, not tradable), 15 | 255, +12.1% | 61, +13.3% | |
| the same, 300 | 255, +17.7% | 61, +21.2% | |
| gate and crowd after (oracle), 15 | 56, +23.9% | 14, +19.7% | |
| gate and crowd after (oracle), 300 | 56, +34.7% | 14, +7.9% | |
| proxy: gate, 300 if >= 3 outsider wallets in 15 blocks, else 15 | 73, +25.9%, $55.5/day | 18, +3.6%, $1.0/day | |
| proxy: the same with 150 | 73, +20.6%, $42.7/day | 18, +7.3%, $4.4/day | |
| every qualifying launch, 15 / 300 | +0.2% / +3.0% | −0.7% / +4.1% | |

- **The crowd before the tick (the gate) is a correct, tradable reading of the discovery.** It predicts the crowd after the
  seat as well now as in the fit (78% against 77%).
- **The crowd after the seat works as an oracle, not as a proxy.** As a rule that waits 15 blocks and then decides the hold,
  it adds nothing to a fixed hold (`q3_h300.txt`: 0 of 18 variants pass; the fit-picked one gains +$0.1 a day recently).
- **The hold is the part that is not the discovery's.** Only the gate with a 15-block hold is positive in both periods and on
  every fit window (+$47, +$36, +$14 and +$42 a day).

## 4. Question 2: what the recent windows say about each reading

**The day series for both holds** (`q2.txt`, the rule's fires; lift = fires minus refused, in points):

| day | fires | 15 blocks (lift) | 300 blocks (lift) |
|---|---|---|---|
| Sep 18 | 13 | +28.2% (+26.9) | +18.6% (+16.9) |
| Sep 19 | 1 | +18.1% (+16.2) | +22.1% (+25.9) |
| Sep 20 | 7 | +29.3% (+27.0) | +28.8% (+36.0) |
| Sep 21 | 20 | +14.5% (+15.6) | +27.1% (+25.5) |
| Sep 22 | 19 | +7.9% (+13.3) | +22.0% (+18.7) |
| Sep 23 | 13 | +11.9% (+19.0) | +38.1% (+49.8) |
| Sep 24 | 9 | +14.8% (+17.4) | +1.5% (−4.5) |
| Sep 25 | 4 | +22.0% (+22.6) | +47.9% (+45.2) |
| Sep 26 | 4 | +4.8% (+7.7) | −26.4% (−27.0) |
| Sep 27 | 1 | −10.0% (−0.2) | −37.6% (−58.2) |

**Is the 15-block version an edge in both periods?** On the mean, yes (`q2.txt`):

| 15 blocks | fires | mean | sd | se | median |
|---|---|---|---|---|---|
| fit | 73 | +16.2% | 0.338 | 0.040 | +8.0% |
| recent | 18 | +12.8% | 0.286 | 0.067 | +0.1% |

- The gap is not significant: Welch t 0.44; 18 fires drawn from the fit read at or below +12.8% in 34.5% of draws.
- The recent mean's bootstrap 95% interval is [+1.1%, +26.8%]. The chance that it sits at or below the 2.5% gas break-even
  is 0.047.
- A's extra fire from the stretches the windows skipped (+8.2% at 15 blocks) makes the recent set 19 fires at +12.6%, lift
  +15.7 (`python3 data/derived/edge_check/D/gaps.py` -> `gaps.txt`).
- Worst of the five windows (the four fit windows and the recent set), per hold (`q2.txt`):

  | h15 | h30 | h60 | h150 | h300 | h600 |
  |---|---|---|---|---|---|
  | +9.0% | +6.7% | +4.4% | +10.7% | +3.5% | +2.4% |

  24.31 chose the hold by exactly this "worst window" test. Applied now, it no longer picks 300.

**Why 15 blocks and not 150.** The data cannot separate the two. The paired difference 15 − 150 is −3.6 points over all 91
fires (t −0.83), and 15 − 300 is −6.2 points (t −1.18); `q2.txt`. I take 15 for three reasons:
- It is the discovery's horizon, fixed before either period.
- Its spread is the smallest: sd 0.33 against 0.48 at 150 and 0.58 at 300. That halves the weekly swing and makes the stop
  test faster (section 5).
- Both mechanisms round 1 found act after block 15:
  - the buying that fell is in E1+16..60;
  - the recent bundles' first sells came at E1+16, 18, 29, 69, 112, 269, 279, 358 and 446, with one at E1+5 that was not
    a dump (`q2b.txt`).

**Would it have survived round 1's dumps and the thinner follow-on demand?** Yes, both are outside the 15-block window (section
2, point 2).
- Round 1 B's operator template (15 launches, 14 fires) is weak at 15 blocks in both periods: fit 8 fires +0.9%, recent 6
  +5.6%.
- Outside that template, 15 blocks makes +18.1% on the fit and +16.4% recently (`q2b.txt`).

**Does it depend on where the sell lands?** No. The engine decides after E1+15 and its sell lands some blocks later
(`python3 data/derived/edge_check/D/q2c.py` -> `q2c.txt`):
- sold anywhere from E1+10 to E1+20: fit +15.4% to +19.1%, recent +12.2% to +14.7%;
- recent drops only past E1+25 (+9.2%) and E1+30 (+6.7%).

**Money at $13** (`q2.txt`: per fire after $0.33 gas, then per day):

| 15 blocks | per fire | at its own rate | at 0.32 fires/h | at 0.10 fires/h |
|---|---|---|---|---|
| fit | $1.78 | $32.5 a day | $13.7 a day | $4.3 a day |
| recent | $1.33 | $9.6 a day | $10.3 a day | $3.2 a day |

At 300 blocks the recent reading is $0.12 a fire, $0.9 a day.

## 5. Question 4: the expectation for next week, and the stopping rule

`python3 data/derived/edge_check/D/q4.py` -> `q4.txt`

**Assumptions.**
- Return per fire at the position mix live got: two thirds at second place, one third at third (24.29).
- Reach: the engine fires on 0.7 of the chain's fires (24.33 addendum 3).
- Fill: three bursts in four fill. An unfilled burst still pays $0.33.
- Supply: 0.32 chain fires an hour (38 bursts a week), or 0.10 (12 bursts).

**Per-fire return, three readings:**

| | fit | recent | trend line of all 91 fires, extrapolated to Oct 1 |
|---|---|---|---|
| 15 blocks | +14.1% | +11.5% | −8.9% |
| 300 blocks | +24.3% | +2.5% | −7.0% |

**Dollars a week** (sd of a week's fills at 0.32 fires an hour: $23 at 15 blocks, $40 at 300):

| candidate | 0.32/h: fit | 0.32/h: recent | 0.32/h: trend | 0.10/h: fit | 0.10/h: recent | 0.10/h: trend |
|---|---|---|---|---|---|---|
| keep (300 blocks) | +$77 | −$3 | −$38 | +$24 | −$1 | −$12 |
| 15 blocks | +$39 | +$30 | −$45 | +$12 | +$9 | −$14 |
| stop | $0 | $0 | $0 | $0 | $0 | $0 |

KILL_USD (24 on the current capital, about $10 of loss) caps every negative column at about −$10.

- **Keep** needs the fit to be true. The 300-block evidence says it is not: the lift is −0.7 points; round 1's p is
  0.01-0.05.
- **15 blocks** is positive under both measured readings. It is negative only if the linear decline continues. That decline
  has p 0.06 and is an extrapolation, not a measurement.

**Stopping rules.** Both use chain-scored fires: every fire the rule takes, priced on the chain, whether or not the engine was
live. Each is a Wald SPRT with a normal likelihood and boundaries ±2.94 (5%/5%), and each starts at 0 on the first new fire.
The chain prices every hold for every fire, so both tests run at once and the hold question needs no live money.

1. **The decision test (15 blocks).** H0 = +2.5%, the gas break-even; H1 = +15.5%, all 91 fires; sd 0.327.
   - About 34 fires expected either way.
   - Resampled from the fit's fires shifted to +2.5%: median 28 fires, 90th percentile 66, wrongly accepts H1 6% of the time.
   - Resampled from the fit's fires: median 29, accepts H1 98%.
   - Resampled from the recent fires: median 51, accepts H1 94%.
   - With H1 set at the recent +12.8% instead: 54 fires expected.

   **Crossing −2.94 stops the strategy. Crossing +2.94 allows a higher stake.** At 0.32 fires an hour, 28-34 fires is about 4
   days; at the last 10 hours' 0.10, about two weeks.
2. **The revert test (round 1 A's 300-block test, kept).** H1 = +26.3% (the fit), H0 = 0; sd 0.576.
   - About 25 fires either way.
   - Resampled from the fit shifted to 0: median 21.
   - The 18 recent fires would put it at −1.38.

   Crossing +2.94 would mean the late-hold premium is back: go back to 300 blocks. Crossing −2.94 closes that question.
3. **Also printed per day:** the lift of fires over refused at 15 blocks, and the share of fires with a bundle sell before
   E1+15. Their fit/recent values are +18.5/+15.3 points and 2/73 against 0/18. A lift near 0, or dumps moving inside 15
   blocks, would kill the 15-block reading before the SPRT does.

**Live or paper, at $13.** The evidence accrues on the chain at the same speed either way. Live adds only the execution check,
which already matched the model to the decimal on 34 fills in September and one on Sep 26. At the recent readings live adds
+$9 to +$30 a week, with the loss capped at about $10. Either choice is defensible. The stake should not rise before test 1
crosses +2.94. One seat is worth $400-500 of stake at most (24.33), and at the current supply that is the only route to money
that matters.

## Files (all in `data/derived/edge_check/D/`)

- **Shared code:** `common.py` (loaders, the rule, tapes, pricing), `kit.py` (policies, $/day).
- **Checks and pulls:** `check_tapes.py`, `pull_tapes.py` -> `tapes/` (85 fit tapes), `pull_shots.py` -> `shots.json.gz`,
  `features.py` -> `features.json.gz`.
- **Analysis:** `base.py`, `q3.py`, `q3b.py`, `q1.py`, `q1b.py`, `q2.py`, `q2b.py`, `q2c.py`, `q5.py`, `q4.py`, `gaps.py`.
  Each writes the `.txt` of the same name (`q3.py` writes `q3_h300.txt` and `q3_h15.txt`).
- **Reproducing.** The scripts built on `kit.py` run from the committed `features.json.gz`. `features.py`, `check_tapes.py`,
  `q2b.py`, `q4.py`, `q5.py` and `gaps.py` also need the tape caches, which are not committed. To rebuild them, run
  `python3 data/derived/edge_check/B/pull_tapes.py fires`, then `python3 data/derived/edge_check/B/pull_fast.py fit` (fills
  `B/tapes/`), then `python3 data/derived/edge_check/D/pull_tapes.py` (the 85 sep2223 launches, into `D/tapes/`).
- **Not modified:** `src/`, `deploy/`, `docs/`. I committed nothing. Folder C was not read.
