**Verdict: CHANGE the hold, keep the gate. Sell at 15 blocks, not 300.** Keep the gate as it is (fleets >= 2 at k-2). On the
rule's own fires, at second place, $13, gas $0.33 a burst, a 15-block hold made **+16.2% on the fit windows** (73 fires, t 4.1,
$1.78 a fire) and **+12.6% on the recent windows** (19 fires, bootstrap 95% interval +1.5% to +25.6%, $1.30 a fire). The
300-block hold made +26.3% and +3.0% ($3.09 and $0.06 a fire). The gate's lift over the launches it refuses is +18.5 and
+15.7 points at 15 blocks, against +26.8 and −0.7 at 300; at 60-150 blocks the recent lift is +6 to +8. The 15-block hold is
the reading of the discovery that holds up best in both periods.

The engine change is one setting: HOLD_BLOCKS 300 → 15. A sell landing three blocks late reads +15.5% and +12.0%.

The money is small. At today's supply (0.32 fires an hour) the 15-block rule is worth **$10 a day at full fill, about $3 a day
with the live fill rate and landing mix** (the weekly standard deviation is about $27). The 300-block rule is worth $0.5 a
day at full fill and −$1.6 a day with the live mix.

It is also not proven on the recent data. Without its two best fires the recent mean is +4.9%, and the last six fires read
+2.9% at 15 blocks.

How to settle it:
- Score every new fire on the chain with a fresh sequential test: H1 +16.2% against H0 = break-even +2.5%, sd 0.33. It
  decides in about 32-35 fires, 4-5 days.
- **Go back to paper if that test accepts H0, or if fewer than 3 of the first 10 live bursts fill.** Below a 30% fill rate
  the 15-block rule loses money even at the recent mean, landing third.
- Score the 300-block hold in parallel on paper. Round 1's test on it sits at LLR −1.54 and needs about 14 more fires if the
  edge is gone.

Where these numbers come from, each with its command in the sections below:
- `readings.txt` A (means, t, lifts) and `stats15.txt` 2-4 (interval, $/day, live mix, sequential tests);
- `holdcurve.txt` (h18);
- `checks.txt` (without the two best, the last six, the break-even fill rates).

# Edge check, round 2: reviewer C (Sep 27 2026)

Every script is in `data/derived/edge_check/C/` and runs from the repository root. The scripts' full output is saved next to
them as `*.txt`.

Everything is priced on one yardstick, `stake_scale.model_eff`:
- second place in the E1 block, the surcharge by second, the 3% cap, later buys folded by their ETH;
- $13 at ETH $2,570, gas $0.33 a burst;
- fleets counted with `crowd_rules.cums`; a fire is fleets >= 2 at block k-2.

**Data.** The fit is the four windows Sep 18-23: 563 launches, 73 fires. "Recent" is:
- the eleven committed windows Sep 24-27;
- plus round 1 A's two gap pulls (`A/crowd_raw_gapA`, `gapB`: Sep 26 17:38-22:38 and Sep 27 04:09-09:20);
- 172 launches and 19 fires in all.

**Tapes.** Tapes b0..b0+640 come from round 1's caches: `A/tapes*.json.gz` (real stamps) first, then `B/tapes/`. I pulled
the 85 sep2223 launches B could not reach: `python3 data/derived/edge_check/C/pull_tapes.py` (public RPC, 4 threads, 0.15 s
pacing, exponential back-off), 191 s, no failures, into `C/tapes_extra.json.gz`.

**Features.** `python3 data/derived/edge_check/C/features.py` writes `C/pop.json`, one record per launch: returns at six
holds and three positions, the post-seat crowd, the bundle's sells, the pre-tick features and the causal creator history.

**The yardstick reproduces round 1 exactly.** Fit +26.32% on 73 fires. Recent +3.46% on the 18 committed fires, +3.01% on 19
with the gap fire. At 15 blocks, +16.22% and +12.81% on the same 73 and 18. These are checked in `readings.txt` section A and
`stats15.txt` section 2; all of them, the 18 committed fires included, are printed by
`python3 data/derived/edge_check/C/checks.py > checks.txt`.

## 1. The discovery against the rule

### 1a. What the real winners had

Command: `python3 data/derived/edge_check/C/discovery.py > discovery.txt`, from `winners_anatomy.json` and
`sep17_20_fills.json`.

The re-derivation matches 24.28 and 24.30:
- Single fills with somebody ahead in the seat block: 12, +17.7% first in the block, +5.8% at our position over 15 blocks,
  +7.4% actual, 67% win.
- Nobody ahead: 22, −1.5% / −1.5% / −3.9%, 27% win.

The 12 winners (over +5%) against the 31 others:

| | winners | the rest |
|---|---|---|
| buys behind us in the seat block | 5.2 | 1.5 |
| buys in the next 15 blocks, distinct wallets | 6.7, 5.5 wallets | 2.2, 2.0 wallets |
| price +15 / +60 / +150 / +600 blocks vs our entry | +36% / +33% / +32% / +32% | +5% / +2% / +16% / +21% |
| somebody ahead of us in the seat block | 58% | 23% |
| wallets firing by k-2 (anatomy's unit), mean / median | 1.0 / 0 | 0.07 / 0 |
| wallets firing by the end of the creation second, mean / median | 7.8 / 4 | 11.9 / 8 |

Three things in these artefacts that the story did not carry forward:

1. **The winners are a 15-block phenomenon.** The winners' price is up +36% by block 15 and does not rise after it. On the
   single fills the gap is sharper:

   | single fills | +15 | +60 | +150 | +600 |
   |---|---|---|---|---|
   | winners (9) | +35% | +22% | +27% | +12% |
   | the rest (25) | +6% | +6% | +24% | +30% |

   The rise at +600 that supported the long hold belonged to the losers, not to the crowd trades. The discovery says to
   sell into the crowd, which the 15-block hold did.
2. **The rule would have caught few of the real winners.** Only 23 of the 43 filled launches are in the fit's population.
   The rule (fleets >= 2 at k-2) fires on 2 of them: both winners, +35% actual. It refuses 21, 5 of those winners, −2.7%
   actual.

   By the anatomy's own count (wallets, which may include shooters of ours through retired relays), the losers had more
   shooters than the winners by the end of the creation second. The rule was not derived from the winning fills. It came
   from the population study of 24.29-24.31.

   On these 23 launches the pre-tick count points the right way. Fleets at k-2 correlate at Spearman +0.54 with the result
   and +0.44 with the post-seat crowd; the post-seat crowd correlates with the result at +0.64. The pre-tick count is a weak
   proxy of the thing that pays, not the thing itself.
3. **The discovery was measured at the position we really got.** "Somebody ahead of us" meant the index-1 bot, and the
   real fills sold after 15-31 blocks. The one piece of real money behind the whole strategy is 12 fills, +$13.34 before
   gas (`story.txt` (a)). All of it came from short holds on crowd launches.

### 1b. Each reading, on both periods

Command: `python3 data/derived/edge_check/C/readings.py > readings.txt`.

**The rule's fires, the refused and every launch, by hold** (section A):

| | fit h15 | fit h300 | recent h15 | recent h300 |
|---|---|---|---|---|
| all launches | +0.2% (563) | +3.0% | −1.4% (172) | +3.6% |
| the rule's fires | **+16.2%** (73), t 4.1 | **+26.3%**, t 3.8 | **+12.6%** (19), t 2.0 | **+3.0%**, t 0.3 |
| refused | −2.2% | −0.5% | −3.1% | +3.7% |
| lift | **+18.5** | +26.8 | **+15.7** | **−0.7** |

The intermediate holds on the fires:

| hold | fit | recent |
|---|---|---|
| h60 | +16.2% | +4.1% |
| h150 | +21.2% | +10.4% |

**The post-seat crowd still pays in both periods.** Section B (an oracle, not tradable) splits launches by the outsiders'
distinct buyers in E1+1..15:

| outsiders' distinct buyers | fit h15 | fit h300 | recent h15 | recent h300 |
|---|---|---|---|---|
| 4 or more | +17.7% (179 launches) | +21.8% | +20.2% (43) | +34.4% |
| 0-1 | −10.9% (276) | −11.4% | −10.3% (91) | −13.1% |

The discovery's mechanism has not changed.

**The gate is still as good a proxy for that crowd as it was** (section C):

| | fit | recent |
|---|---|---|
| outsiders' distinct buyers in E1+1..15, fires vs refused (mean) | 5.0 vs 2.7 | 5.3 vs 2.2 |
| P(4 or more such buyers), fires vs refused | 58% vs 28% | 58% vs 21% |
| outsider ETH in E1+16..60, fires vs refused (mean) | 1.39 vs 0.72 | 0.98 vs 1.01 |
| same, median | 0.57 vs 0.15 | 0.25 vs 0.65 |
| bundle's share sold by +300, fires vs refused (mean) | 0.08 vs 0.22 | 0.20 vs 0.11 |

What the gate no longer predicts is what came after the crowd: the later demand and the bundle's patience.

**This is the answer to "which reading survives".** The gate before the tick survives as a predictor of the discovery's own
variable, the 15-block crowd. The 300-block hold harvested a second, different effect: the gate also picked launches whose
later demand came in and whose bundle held. That second effect is the one that vanished. The discovery never claimed it.

**The combination** (section D): the gate, then a hold decided at E1+12 by the post-seat crowd (hold to H if at least N
outsiders bought in E1+1..12, else sell at 15). It is tradable but adds nothing.
- Fitted on the fit (N 1, H 300): +25.5% there, **+3.9%** recent.
- Fitted on the recent data (N 10, H 300): +15.0% recent, **+19.9%** on the fit, below the fit's plain h300.
- Null test (permute the crowd count among the fires, refit, read): the permuted feature does at least as well on both
  periods in **30.6%** of 2,000 permutations. Not adopted.

The bundle-sell exit does not help either: sell 2 blocks after the named wallets' first sell after the seat. It reads fit
+28.3% and **recent −1.2%**, against h300 +26.3% and +3.0% (`checks.txt`). The
dumps are too fast.

## 2. The 15-block rule in both periods

Commands: `readings.py` (sections E-H), `python3 data/derived/edge_check/C/stats15.py > stats15.txt`,
`python3 data/derived/edge_check/C/holdcurve.py > holdcurve.txt`.

**By window.** The 15-block hold is positive in every fit window and in the one recent window with more than two fires
(`readings.txt` E):

| window | fires | h15 | h60 | h150 | h300 |
|---|---|---|---|---|---|
| sep1819 | 14 | +27.5% | +22.5% | +10.7% | +18.9% |
| sep2021 | 29 | +16.4% | +15.4% | +21.6% | +26.2% |
| sep2223 | 20 | +9.0% | +13.4% | +30.2% | +35.5% |
| sep23day | 10 | +14.4% | +15.4% | +16.5% | +18.9% |
| sep24paper | 9 | +14.8% | +3.1% | +1.8% | +1.5% |
| the other 10 recent fires | 10, one or two per window | +10.5% | +5.0% | +18.2% | +4.3% |

The last row is from `python3 data/derived/edge_check/C/checks.py > checks.txt`.

**The hold curve is a plateau at 8-20 blocks in both periods, not a spike at 15** (`holdcurve.txt`):

| hold | 8 | 10 | 12 | 15 | 18 | 20 | 30 | 60 | 150 | 250 | 300 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| fit fires | +17.6% | +18.6% | +19.1% | +16.2% | +15.5% | +16.7% | +16.1% | +16.2% | +21.2% | +25.6% | +26.3% |
| recent fires | +11.4% | +14.2% | +15.1% | +12.6% | +12.0% | +12.2% | +6.7% | +4.1% | +10.4% | +13.2% | +3.0% |
| fit lift | +20.2 | +20.1 | +20.3 | +18.5 | +18.1 | +18.8 | +18.1 | +17.3 | +21.1 | +25.3 | +26.8 |
| recent lift | +15.4 | +17.2 | +18.0 | +15.7 | +15.0 | +15.0 | +9.4 | +5.8 | +8.4 | +10.2 | −0.7 |

- A sell landing 3 blocks late (h18) costs 0.6 points recent and 0.7 on the fit.
- The recent 300-block number sits on a local low: two dumps at E1+269 and E1+279 (round 1 B's operator, per B's report) drop it
  from +13.2% at 250 to +3.0% at 300. The long hold's recent reading is noisy as well as low.

**Robustness of the recent h15 mean** (`stats15.txt` 2):

| | recent (19) | fit (73) |
|---|---|---|
| mean | +12.6% | +16.2% |
| bootstrap 95% interval | +1.5% to +25.6% | +8.8% to +24.2% |
| median | +0.1% | +8.0% |
| sd per fire | 0.28 | 0.34 |

- P(the recent mean is at or below break-even, +2.5%) is 4.2%.
- Leaving one fire out gives +8.5% to +14.0%; dropping the best and the worst gives +9.8%.
- Without the two best fires (+86%, +70%) the recent mean is +4.9% on 17.
- The paper stretch (Sep 24 12:55 to Sep 26 09:15) reads **+17.0% (13 fires); the fires since read +2.9% (6)**. Six fires
  drawn from the fit's h15 returns average that low 15.9% of the time (`checks.txt`), so this is a warning, not a verdict.
- 19 fires drawn from the fit's 73 read at or below +12.6% in 32.7% of draws, so there is no evidence that h15 fell. At h300
  the same test gives 2.7%.

**Day by day, Sep 18-27** (UTC day of the creation, the rule's fires, $ at $13 after gas; `readings.txt` F):

| day | launches | fires | h15 mean, win | h15 $ (cum) | h300 mean, win | h300 $ (cum) |
|---|---|---|---|---|---|---|
| Sep 18 | 104 | 13 | +28.2%, 85% | +43.36 (+43.36) | +18.6%, 69% | +27.20 (+27.20) |
| Sep 19 | 37 | 1 | +18.1%, 100% | +2.02 (+45.38) | +22.1%, 100% | +2.54 (+29.74) |
| Sep 20 | 42 | 7 | +29.3%, 86% | +24.31 (+69.69) | +28.8%, 71% | +23.91 (+53.65) |
| Sep 21 | 138 | 20 | +14.5%, 60% | +31.17 (+100.86) | +27.1%, 75% | +63.77 (+117.42) |
| Sep 22 | 170 | 19 | +7.9%, 42% | +13.26 (+114.12) | +22.0%, 63% | +48.10 (+165.52) |
| Sep 23 | 72 | 13 | +11.9%, 77% | +15.75 (+129.88) | +38.1%, 54% | +60.13 (+225.65) |
| Sep 24 | 55 | 9 | +14.8%, 44% | +14.35 (+144.23) | +1.5%, 44% | −1.17 (+224.48) |
| Sep 25 | 49 | 4 | +22.0%, 75% | +10.13 (+154.36) | +47.9%, 75% | +23.59 (+248.07) |
| Sep 26 | 54 | 5 | +5.5%, 80% | +1.91 (+156.27) | −22.1%, 0% | −16.02 (+232.04) |
| Sep 27 to 09:20 | 14 | 1 | −10.0%, 0% | −1.63 (+154.64) | −37.6%, 0% | −5.22 (+226.83) |

- The 15-block rule made money on every day but the last, which had one fire.
- The gate's lift at 15 blocks by day (`story.txt` (c)): +27, +16, +27, +16, +13, +19, +17, +23, then **+8.5 (Sep 26, 5
  fires) and +3.8 (Sep 27, 1 fire)**. Its lift at 300 blocks: +17, +26, +36, +26, +19, +50, −4.5, +45, −23, −46.
- The 15-block lift is the steadier of the two, and it is also lower on the last two days.

**Round 1's dumps and thin demand** (`readings.txt` G): the 15-block exit sells before most dumps.

| the rule's fires | h15 | h300 |
|---|---|---|
| recent, bundle dumped (> 10% by +300), 5 fires | +28.6% | −17.8% |
| fit, bundle dumped, 7 fires | +1.3% | −37.1% |
| recent, thin later demand (outsider ETH E1+16..60 < 0.2), 9 fires | +3.9% | −16.4% |
| fit, thin later demand, 35 fires | +6.0% | +8.2% |
| recent, round 1 B's serial template (template prior >= 3), 8 fires | +2.3% | −11.1% |

The last row is from `fleetfree.txt`.

**Paired h15 − h300 on the same fires** (section H):
- fit −10.1 points (t −1.63);
- recent +9.5 (t +1.14);
- all 92 fires −6.0 (t −1.15).

Neither period alone is decisive between the holds. The case for 15 blocks is that it is the reading positive in both
periods and the one the discovery describes. It is not that 15 beats 300 significantly.

**Position costs about the same points at both holds, a larger share of the thinner 15-block edge.** Section E, first /
second / third place in the seat block:

| place | fit h15 | fit h300 | recent h15 | recent h300 |
|---|---|---|---|---|
| first | +27.6% | +40.8% | +25.2% | +13.9% |
| second | +16.2% | +26.3% | +12.6% | +3.0% |
| third | +9.9% | +20.1% | +8.4% | −0.3% |

**The dollars** (`stats15.txt` 3, at 0.32 fires an hour = 7.7 a day). The "live mix" assumes a fill on half the bursts,
landing second two times in three and third otherwise, with gas on every burst. That is the landing mix of 24.29 and the one
fill in two bursts of Sep 26 (24.34).

| | full fill, second place | live mix |
|---|---|---|
| h15 at the recent mean | $1.30 a burst, **$10.0 a day**, $70 a week | $0.40 a burst, **$3.0 a day**, $21 a week |
| h15 at the fit mean | $1.78, $13.7 a day | $0.59, $4.5 a day |
| h300 at the recent mean | $0.06, **$0.5 a day** | −$0.21, **−$1.6 a day** |
| h300 at the fit mean | $3.09, $23.7 a day | $1.25, $9.6 a day |

- Weekly sd at 54 fires: $27 at h15, $45 at h300.
- At $100 (`python3 data/derived/edge_check/C/stake15.py > stake15.txt`) h15 reads +15.5% fit and +12.0% recent ($15.16 and
  $11.68 a fire). h300 reads +24.3% and +1.5%. The 15-block edge scales with the stake; the 300-block one no longer has
  anything to scale.

## 3. The honest expectation for the next week, and the stopping rule (question 4)

Supply as it is now:
- 2.7 qualifying launches an hour and 0.32 fires an hour over the recent windows: about 54 chain-scored fires a week.
- The last 10 hours were thinner: 13 launches in round 1 A's count. In the 100 minutes after 09:20 there was one qualifying
  launch (section 6).

| candidate | per fire (recent / fit) | next week at full fill | next week, live mix | weekly sd |
|---|---|---|---|---|
| keep (h300) | +3.0% / +26.3% | +$3 | −$11 | $45 |
| **h15, same gate** | **+12.6% / +16.2%** | +$70 | **+$21** | $27 |
| h15 if the last six fires are the truth (+2.9%) | | about +$2 | about −$8 | |
| stop | 0 | 0 | 0 | 0 |

The h15 and h300 rows are from `stats15.txt` 3. The "last six" row is `checks.txt`: 54 × ($13 × 2.9% − $0.33) at full fill, and
54 × (0.5 × $13 × 2.9% − $0.33) with the live mix. The live mix uses second place only because no third-place figure exists for those
six.

Stopping is not needed to protect capital; the kill line (KILL_USD 24) already does that. Nor is it needed to learn: every
fire is scored on the chain whether or not the engine sends it, at 7.7 a day against about one live fill a day. Live money
adds one thing the chain cannot give: the fill rate and landing position of the 15-block rule. That matters because the 15-block edge is thin: third place takes 4-6 of its 12-16
points. So the change should stay live at $13, with two stopping rules.

1. **Chain-scored SPRT on h15** (`stats15.txt` 4). Wald test, alpha = beta = 5%, boundaries ±2.94, normal likelihood.
   - H1 is the fit's h15 mean, +16.2%; H0 is break-even after gas, +2.5%; sd 0.326 (pooled).
   - Start it at the next fire. The hold was chosen after seeing the recent data, so those 19 fires cannot count as
     evidence for it; on them the LLR would be +0.78.
   - Expected length, resampled from the fit's returns: **35 fires if H1 is true, 32 if H0**, about 4.1-4.6 days at 7.7 a
     day. It accepts H1 wrongly 6% of the time when H0 holds.
   - Accept H0 → back to paper.
   - Round 1 B's test (the recent mean against the fit's, to 20:1) does not suit the 15-block hold: its two period means
     (+12.6%, +16.2%) are too close to separate. The live question at 15 blocks is whether the rule clears the gas, so H0
     is break-even.
2. **Live execution check.** After 10 live bursts, fewer than 3 fills means back to paper. The break-even fill rate at h15
   is 0.33 / (13 × 0.126) = 20% landing second, and 0.33 / (13 × 0.084) = 30% landing third, at the recent means
   (`checks.txt`).
3. **The 300-block hold, on paper, in parallel.** Continue round 1 A's SPRT: H1 +26.3%, H0 0, sd 0.573, LLR −1.54 on the 19
   recent fires. It needs **about 14 more fires if the edge is gone** (1.9 days), 39 if it is intact
   (`stats15.txt` 4). If it recovers to H1, the long hold's second effect is back and can be reconsidered.

The order: rule 2 can trip first (10 bursts is 2-4 days of live), rule 3 next (about 2 days), rule 1 last (4-5 days).

The stake stays at $13 until rule 1 accepts H1. The stake is the only lever on the dollars: at $100 the recent h15 mean is
$11.68 a fire (`stake15.txt`). It should not rise on 19 fires.

## 4. A version that does not depend on the fleet roster (question 3)

Command: `python3 data/derived/edge_check/C/fleetfree.py > fleetfree.txt`.

**Features tried** (pre-tick only): wallets shooting by k-2, shots by k-2, relay fleets and direct senders by k-2, the bundle's
ETH / buys / sells in the creation second, the creator's and the named template's prior launches (causal), the tier, k.

**Protocol:**
- Each feature, both directions, thresholds at the fitting period's 5% quantiles, holds 15 and 300.
- The fitted rule is the best by $/day on one period with enough fires (fit >= 30, recent >= 8); it is then read on the other
  period.
- $/day is priced at today's supply for both periods: $ per launch × 64.8 launches a day.
- A pass: on the reading period, $/day at or above the rule's and a positive lift.
- Null test: permute the feature within each period, refit, read, count passes; 300 permutations per feature.

**Results:**
- **At 15 blocks, fitted on the fit:** 2 of 11 features pass; the permuted features pass 0% of the time. Both passes are
  still counts of shooters:
  - wallets >= 2 at k-2: fit 73 fires +12.2%, $10.6 a day; recent 21 fires +12.8%, $10.6 a day (the rule: $9.3). Null
    pass rate 1%.
  - relay fleets >= 2 at k-2: the rule itself, less the direct senders.
- **Nothing independent of the shooters passes at 15 blocks in either direction.** The bundle's size, its buys, its sells in
  the creation second, the creator's or the template's history, the tier and k all fail. Example: bundle ETH >= 1.03 goes
  from +5.6% on the fit to −1.9% recent.
- **At 300 blocks the "passes" (10 of 11 fitted on the fit) mean nothing.** The rule's own recent $/day at h300 is $0.4, the
  whole population makes +3.6% there, and the permuted features pass 59% of the time.

**The template's history, as a restriction on the rule** (the operator round 1 B found, measured causally):

| the rule's fires | fit h15 | recent h15 | fit h300 | recent h300 |
|---|---|---|---|---|
| template prior <= 2 | +17.8% (57 fires) | +20.0% (11) | +28.5% | +13.3% |
| template prior >= 3 | +10.5% (16) | +2.3% (8) | +18.6% | −11.1% |

On the fit it lowers $/day ($13.0 against $14.9 at h15), so the fit-first discipline does not select it. It is a hypothesis
for the daily reading (11 and 8 recent fires), not a rule.

**Answer.** The wallet count (wallets >= 2 at k-2) is the version that does not depend on which fleets exist or on how they
are grouped. It reads +12.2% and +12.8% at 15 blocks on the two periods, as good as the fleet rule recently and worse on the
fit. It could replace the fleet count if the fleet unit breaks down (for example, one operator splitting across relays). But
every version that works still counts snipers shooting before the tick. The strategy follows the snipers' collective
judgement. No version found here works without them.

## 5. What the whole story shows that the pieces did not

Command: `python3 data/derived/edge_check/C/story.py > story.txt`.

1. **The 300-block hold was one window's result, carried forward.** 72% of the fit's summed h300-over-h15 premium on the
   rule's fires comes from sep2223, the window the hold was chosen on (24.30's gate × hold table).

   | window | h300 − h15 on the rule's fires |
   |---|---|
   | sep1819 | −8.6 points |
   | sep2021 | +9.8 |
   | sep2223 | +26.4 |
   | sep23day | +4.5 |
   | recent | −9.5 |

   Without sep2223 the fit reads h15 +18.9% against h300 +22.9% (53 fires). 24.31 described Sep 20-21 as confirming the long
   hold out of sample. Under the gate of the day (2+ attacker wallets by block 5) that window was a tie at 15 blocks
   against 300: +11.2% / +10.9% behind one in 24.31's table, a citation, not recomputed here. Under today's rule it reads
   +16.4% / +26.2% (`readings.txt` E). What carried over was the gate; the hold was a bet on a regime, "the crowd comes over 30 s", seen in one 30-hour window.
2. **The discovery and the rule measured different things, and the difference was the hold.** The discovery (24.30) was about
   the crowd within 15 blocks of the seat. Its own winners' price was flat after block 15, and the late rise belonged to the
   losers (§1a). The rule kept the discovery's selection and replaced its horizon with one taken from the population's late
   drift. The selection is intact (lift +18.5 → +15.7 at 15 blocks); the horizon is what failed.
3. **The gate's prediction of the post-seat crowd has not moved, window by window.** The outsiders' distinct buyers in
   E1+1..15, fires against refused (`story.txt` (d)):

   | window | fires vs refused |
   |---|---|
   | sep1819 | 6.4 vs 3.4 |
   | sep2021 | 4.4 vs 2.6 |
   | sep2223 | 4.5 vs 2.4 |
   | sep23day | 5.7 vs 2.2 |
   | recent | 5.3 vs 2.2 |

   What moved is the later demand and the dumps:

   | window | median outsider ETH in E1+16..60, fires vs refused | dumps, fires vs refused |
   |---|---|---|
   | sep1819 | 1.30 vs 0.11 | 14% vs 32% |
   | sep2021 | 0.08 vs 0.08 | 7% vs 27% |
   | sep2223 | 0.68 vs 0.22 | 15% vs 25% |
   | sep23day | 0.19 vs 0.34 | 0% vs 31% |
   | recent | 0.25 vs 0.65 | **26% vs 12%** |

   The fit's low dump rate among fires is the one fit-period property the recent windows reversed.
4. **Every real dollar of this strategy came from short holds on crowd launches, and every tables' dollar since has come
   from a model.**
   - The real fills of Sep 17-20 net −$23.42 before gas (`story.txt` (a)): single fills +$0.81, multi-fills −$24.23. The 12
     crowd fills made +$13.34, held 15-31 blocks.
   - Since then, live has one fill (−2.6%, the model's number). The fit's "$56 a day" was never observed in money.
   - The live haircuts are fill rate, landing position and gas on empty bursts. Priced in, they turn $10 a day into about
     $3 at h15 and $0.5 into −$1.6 at h300.
   - In the Sep 17-20 fills that same gap was +17.7% first in the block against +7.4% actual.
5. **The rule depends on the snipers, and they are the part of the market that turns over.** The gate follows fleets whose
   picks drew a crowd. The fleets changed and the market halved, yet their picks still draw the 15-block crowd (point 3). So
   the part of the edge that belongs to the discovery is the one that survived the turnover. The part that depended on
   particular fleets' taste for patient bundles did not.

## 6. The 100 minutes after the last window (Sep 27 09:20-11:00)

`python3 data/derived/edge_check/C/extend_window.py "2026-09-27 09:20" "2026-09-27 11:00" extra27` is round 1 A's script,
writing into C/: 240 creations, 0 unresolved, **1 qualifying launch**.

`python3 data/derived/edge_check/C/extra_score.py > extra_score.txt` scores it: 10:38 `0x04ebdf1b`, k 2, 0 fleets at k-2
(1 at k-1, 2 at k). The rule refuses it; second place would have made −6.3% at 15 blocks and −5.1% at 300. Nothing changes.
Supply is 0.6 qualifying launches an hour this morning, against 2.7 over the recent windows and 5.9 on the fit. The
sequential tests above take 2 times longer at the last 10 hours' 1.3 launches an hour, and 4.5 times longer at this
morning's rate. Rule 2's ten live bursts could take a week.

## Files

All files are in `data/derived/edge_check/C/`; each script's docstring gives its command.
- `common.py`: loaders and the yardstick. It imports `crowd_rules.cums` and `stake_scale.model_eff` unchanged.
- `pull_tapes.py`: `tapes_extra.json.gz` (85 tapes), `pull_tapes.log`.
- `features.py`: `pop.json` (735 launches).
- `discovery.py` → `discovery.txt` · `readings.py` → `readings.txt` · `stats15.py` → `stats15.txt`
- `holdcurve.py` → `holdcurve.txt` · `stake15.py` → `stake15.txt` · `fleetfree.py` → `fleetfree.txt` · `story.py` → `story.txt`
- `checks.py` → `checks.txt`
- `extend_window.py`: round 1 A's script, writing into C/. It produced `launches_extra27.json`, `crowd_raw_extra27.json.gz` and
  `tapes_extra27.json.gz`; its log is `extend_extra27.log`. `extra_score.py` → `extra_score.txt`.

Numbers quoted from elsewhere, not recomputed here:
- the 24.31 table (+11.2% / +10.9%);
- the live fill of Sep 26 (−2.6%) and the live P&L (−$0.68), from docs/REPORT.md 24.34;
- the landing mix behind the "live mix" (24.29);
- round 1 A's LLR −1.54 (reproduced in `stats15.txt` 4) and its 10-hour launch count.
