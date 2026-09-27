Verdict: REAL, not an artefact. The same code on the same definitions, re-derived here from an independent chain pull,
gives the fit +26.3% and Sep 24-27 +3.5% per fire, and the rule's lift over the launches it refuses fell from +27.5 to
-0.7 points. Two causes are measured: the launch supply halved (fires per hour 0.76 -> 0.32), and one operator's
launches, which the rule fires on almost every time, stopped paying (6 of the 18 recent fires, -13.6% mean; two dumps
at E1+269 and E1+279); outside that operator the recent fires average +12.0% against the fit's +28.2%. Whether the
per-fire edge is lower for good cannot be decided on 18 fires: that takes 20 more fires if the recent mean is the true
one, 56 if the fit's is (about Sep 30 to Oct 4 at the recent rate of 7.6 fires a day).

# Edge check, reviewer B

All commands run from the repository root; the scripts are in `data/derived/edge_check/B/`. The tapes (every Buy/Sell on the
curve from b0 to b0+640, block stamps b0..b0+30, the tier) are cached under `B/tapes/`.

    python3 data/derived/edge_check/B/pull_tapes.py fires      # the 91 fires (73 fit + 18 recent), full tapes with real stamps, 212 s
    python3 data/derived/edge_check/B/pull_fast.py fit         # the other launches, one eth_getLogs each (tier from the e1m files,
                                                               # stamps synthesised from k; synth_check.py: identical h300 on 472 launches)
    python3 data/derived/edge_check/B/features.py              # per launch features -> B/features.json (638 launches: 478 fit, 160 recent)

The full-stamp pull (`pull_tapes.py all`) was throttled by the public node after 430 launches (7 launches a minute); the
rest came from `pull_fast.py`. `python3 data/derived/edge_check/B/synth_check.py` checks the synthesised stamps against
the real ones on the 472 launches that have both: h300 identical (max difference 0.0000), outsiders' ETH within 0.09 ETH.
85 fit launches (sep2223, no e1m file with their tier) have no tape; all 73 fit fires and every recent launch do.

"Fit" = the four crowd files sep1819, sep2021, sep2223, sep23day (563 launches, 73 fires). "Recent" = the eleven files
sep24paper .. sep27night, 166 records, 160 distinct launches (the six duplicates are in overlapping windows; none is a fire),
18 fires. A fire = fleets >= 2 at block k-2, `crowd_rules.cums/at`, exactly as reach_table.py.

## 1. Same yardstick (test 1): yes

- My independent pull and pricing (stake_scale.model_eff, $13 at 2570, second place in E1, hold 300, tape to b0+640)
  reproduce reach_table.txt to the decimal: fit 73 fires +26.3% (win 67%, dead 8%), recent 18 fires +3.5% (win 39%,
  dead 11%). `python3 data/derived/edge_check/B/compare3.py` (first two lines) and `holds4.py` (the check line: max abs
  difference 0.0000 against features.json).
- One run of one script prices both sets (reach_table.py, same cums/at, same model_eff, same SUR, CAP, E, GAS, hold);
  its tape runs to b0+330, past E1+300 (E1 <= b0+10). The b0+120 tape bug of Sep 26 was in live_vs_table's own loop
  only; hold_grid.py pulls to b0+620, stake_scale/reach_table to b0+330/340.
- The crowd files of both periods come from the same crowd_raw.py (last change 3ed469d, Sep 24 11:32); the four fit files
  were re-pulled after it (commit 71bed14, Sep 24 11:35); every record of both periods has its token resolved.
- The population filter holds in both sets: every fire has tier 2-3%, bundle >= 0.3 ETH (e1_multi's definition,
  recomputed from the tape), >= 3 named wallets (`python3 data/derived/edge_check/B/pop.py`, second and third lines).
- The fee schedule on the chain is the model's in both periods (section 4).

So the 22.8-point gap is not a scoring artefact: the same code on the same definitions gives +26.3% and +3.5%.

## 2. Statistics (test 2): the drop is unlikely under the fit's distribution, but it sits on few fires

`python3 data/derived/edge_check/B/stats2.py`

- Per-fire sd: 59.1 points (fit), 48.0 (recent), not 45. Fit median +20.7%, recent median -6.6%.
- Bootstrap: 18 fires drawn from the fit's 73 read <= +3.5% in 3.4% of 100,000 draws.
- Permutation of the 91 fires (fit mean - recent mean >= 22.9 points): p = 0.055 one-sided.
- Rank test (Mann-Whitney): z = -2.24, one-sided p = 0.0125. Wins: 7 of 18; the fit's win rate gives <= 7 in 1.3%.
- No run of 18 consecutive fit fires reads below +9.1% (56 runs; max +48.3%); no 60-hour stretch of the fit timeline
  (wrapped, 576 starts) reads below +20.1%.
- Fit windows: sep1819 +18.9% (14), sep2021 +26.2% (29), sep2223 +35.5% (20), sep23day +18.9% (10).
- Day by day (fires, mean): Sep 18 13 +18.6%, 19 1 +22.1%, 20 7 +28.8%, 21 20 +27.1%, 22 19 +22.0%, 23 13 +38.1%,
  Sep 24 9 +1.5%, 25 4 +47.9%, 26 4 -26.4%, 27 1 -37.6%. The recent set is not uniformly bad: Sep 24 is flat, Sep 25 is
  fit-like (one +168% fire), Sep 26-27 is the five straight losses.

## 3. What changed on the chain for the fired launches (test 3)

`python3 data/derived/edge_check/B/compare3.py` (fit 73 fires vs recent 18; medians unless marked mean). The p values are
two-sided permutations of the 91 fires, 20,000 shuffles (`python3 data/derived/edge_check/B/perm3.py`).

The entry did not change; the hold did.
- h15 (sold 15 blocks after E1): fit +16.2%, recent +12.8% (p = 0.69). h300: +26.3% vs +3.5%. The drift from block 15
  to block 300 is +10.1 points in the fit and -9.4 in the recent set (p = 0.14). `holds4.py`.
- The bundle (creator, named wallets, creation-second buyers) sold 7.6% of its tokens by E1+300 in the fit fires (mean)
  and 22.8% in the recent ones (p = 0.031); its ETH out during the hold 0.077 vs 0.256 ETH (p = 0.032). Fires where the
  bundle sold more than 10% of its tokens by E1+300: fit 7 of 73 (mean h300 -37.1%, the other 66 +33.0%), recent 5 of 18
  (mean -17.8%, the other 13 +11.6%). Five or more of 18 at the fit's rate 7/73: binomial p = 0.024 (`perm3.py`, last line).
- The three worst recent fires are bundle dumps: Sep 26 09:24 (-41%, bundle 100% out by E1+18), Sep 26 23:53 (-51%, 95% out,
  first sell E1+269) and Sep 27 00:10 (-38%, 92% out, first sell E1+279). The last two belong to one operator's named-wallet
  template of 15 launches since Sep 21 (section 6).
- Not significantly different: fleets at k-2 (mean 2.51 vs 2.22), fleets by the seat block (7.48 vs 6.78), rival shots in
  the creation second (mean 95.9 vs 60.4, p = 0.17), buys landed in the seat block (5.2 vs 3.9, p = 0.24), ETH in the seat
  block (0.44 vs 0.31, p = 0.21), outsiders' ETH bought after the seat second (mean 1.96 vs 1.58, p = 0.58; median 0.83 vs
  0.70), distinct outside buyers (median 17 vs 20), the fleets' own selling (share sold by E1+15/60/300: 0.17/0.36/0.45 vs
  0.18/0.34/0.46, first sell at E1+15 in both), bundle size (0.725 vs 0.738 ETH), tier-3% share (49% vs 44%), dead rate
  (8% vs 11%).
- Hour of day (UTC, fires and mean h300): fit 00-05h 8 +64%, 06-11h 5 +16%, 12-17h 26 +26%, 18-23h 34 +19%; recent 2 +65%,
  1 -41%, 8 -2%, 7 -2%. The recent afternoon and evening fires, where the fit made most of its money, are the flat ones;
  the hour mix itself is the fit's.
- Which fleets are at k-2: 58 distinct fleets at k-2 of the fit fires, 24 in the recent ones, 12 of those never at k-2 of
  a fit fire. The fit's two best k-2 fleets did not repeat: 0x460b1f818c at k-2 of 22 fit fires averaging +51.9%, of 3
  recent at -4.8%; 0x2ddcda583c 12 at +49.7%, 1 recent. 0xbd7c6f67d5: 16 fit fires +13.7%, 5 recent -14.6% (three of the
  five Sep 26-27 losses). With 1-5 recent fires per fleet none of these differences is testable.
- Serial creators: 5 of 73 fit fires and 1 of 18 recent fires have a creator with more than one launch in the population
  (the recent one is Sep 26 09:24, -41%).

## 4. The world (test 5)

`python3 data/derived/edge_check/B/world.py` (fees and cadence from the tapes), `python3 data/derived/edge_check/B/fleets.py`
(the crowd files, every launch).

- Fee schedule: unchanged. Implied from the curve folded in tape order, the buy fee minus the tier is 0.0618 in second +1
  (99-100% of buys within 0.001), 0.0019 in second +2 (100%), 0 from second +3 (100%); creation-second buys are the bundle's
  and pay the tier only; every sell pays exactly the tier; identical before and after Sep 26 09:24. The curve's constants
  (1.68 ETH, 1e9) hold, or these residuals would not be zero. All creations use the same factory call (selector f85f8e41).
- Cadence: 9.88 blocks per whole second in the fit (91% of seconds have 10), 9.92 and 9.90 in the recent periods; k has
  mean 5.8 (fit) vs 6.2-6.4 (recent), inside the fit's own spread.
- The launch supply fell by half. Qualifying launches per hour: fit 5.86 (563 in 96 h), Sep 24 - Sep 26 09:24 2.70 (118 in
  43.7 h), after 3.24 (42 in 13.0 h). Factory creations per hour in the e1_multi scans: 297-545 per hour in the fit windows
  (382 over 69.8 h), 97-334 per hour since Sep 24 (Sep 24 334, Sep 25 night 181, Sep 26 am 134, Sep 27 night 97). The fire
  share of launches held (13.0% fit, 11.0% and 11.9% since), so fires per hour fell from 0.76 to 0.30-0.39. At the fit's
  +26.3% per fire the recent fire rate pays $23.6/day at $13, not $56 (`settle.py`). Half of the $56 -> $1 fall is the
  launch supply, independent of any change in the per-fire return.
- Our bursts were visible before Sep 26. The crowd files show our relay 0xe8e98c35 firing 28-35-shot bursts (28-35 distinct
  senders) at 9 launches on Sep 19 10:44-13:07 UTC, and our wallet shooting at 28 launches on Sep 18-19 (inside the fit;
  `python3 data/derived/edge_check/B/visibility.py`). The fit windows after Sep 19 13:07 (sep2021 +26.2%, sep2223 +35.5%, sep23day +18.9%) show no damage from that
  exposure. After Sep 26 09:24 the crowds are thinner (fleets by the seat block 2.07 per launch against 3.68 in the fit and
  3.26 before; shots in the creation second 20.8 against 36.8 and 33.2) on 42 launches; 11 of the 40 fleets that shot after
  Sep 26 09:24 were never seen in the fit, at 15 launch-shots.
- Fleet roster churn is constant and mostly outside the gate: 0xa95fe1ca2f shot at 30.6% of fit launches and 0 after
  Sep 26; 0xfb5b10615a 14.9% then 0; 0xf9af9f3881 8.5% then 34-38%; 0x3e7c18b0b1 2.8%, 5.1%, then 38.1%. These shoot at
  block k or the seat block (median first shot k+0/k+1) and do not enter the k-2 count. The early fleets that make the
  gate (0x460b1f818c and 0xbd7c6f67d5 first at k-4/k-5, 0x5b8e11e3b1 k-3.5/k-5.5, 0x19078e5c68 and 0x96d7b1eec8 k-1)
  shoot at the same share of launches and at the same depth before and after Sep 26.
- Contracts: `python3 data/derived/edge_check/B/code_check.py`. Curves created Sep 18, Sep 23, Sep 24 and Sep 27 all have
  10,229 bytes of runtime code and differ from each other in 40-44 bytes in 3-7 32-byte words (the per-launch immutables:
  the Sep 23 fit curve differs from the Sep 18 one as much as the recent ones do). One implementation throughout.

## 5. Alternatives the rule does not see (test 4), on the fires

`python3 data/derived/edge_check/B/holds4.py` (model_eff pricing, $13, second place in E1; a stop sells 3 blocks after
the block where the position's sale value first crosses the level, else the 300-block exit).

| hold / exit | fit 73: mean, median, win | recent 18: mean, median, win |
|---|---|---|
| 15 blocks | +16.2%, +8.0%, 66% | +12.8%, +0.1%, 56% |
| 30 | +16.1%, +8.5%, 64% | +6.7%, -4.1%, 39% |
| 60 | +16.2%, +9.3%, 66% | +4.4%, -3.7%, 44% |
| 150 | +21.2%, +12.4%, 66% | +11.1%, +3.6%, 56% |
| 300 (the rule) | +26.3%, +20.7%, 67% | +3.5%, -6.6%, 39% |
| 600 | +19.6%, +10.8%, 52% | +2.4%, -12.7%, 44% |
| stop -20% else 300 | +22.8%, +20.1%, 62% | -4.1%, -10.8%, 28% |
| stop -30% else 300 | +26.8%, +20.7%, 67% | -3.6%, -9.7%, 33% |

On the recent fires the 15-block hold would have made +12.8% against +3.5% ($1.33 against $0.12 per fire at $13 after
gas); on the fit it gives up 10 points. The recent sample cannot pick a hold: the h300-h15 gap on the 18 recent fires is -9.4 points with a
standard error of 8.9 (fit: +10.1, se 6.2). A stop does not help in either period (the dumps are one-block events that pass any
stop level). The recent windows do not overturn 24.34's answer; they reward the shortest hold, which the fit penalises.

## 6. Every launch, fires and refused: the rule's selection stopped working at 300 blocks

`python3 data/derived/edge_check/B/pop.py` (478 fit launches, 160 recent; h300 and h15 at $13, second place in E1).

| | fit h300 | recent h300 | fit h15 | recent h15 |
|---|---|---|---|---|
| all launches | +3.0% (478) | +4.1% (160) | +0.9% | -0.7% |
| fires | +26.3% (73) | +3.5% (18) | +16.2% | +12.8% |
| refused | -1.2% (405) | +4.1% (142) | -1.8% | -2.5% |
| lift, fires - refused | +27.5 | -0.7 | +18.0 | +15.3 |

- The market did not get worse for the seat: the whole population returns +4.1% at 300 blocks since Sep 24 against +3.0%
  in the fit, and the refused launches do better (+4.1% against -1.2%). What vanished is the rule's selection at 300 blocks.
  At 15 blocks the selection still works (+15.3 points against +18.0).
- The bundle dump (the bundle sells more than 10% of its tokens by E1+300) is the mechanism. Fit: 25% of all launches,
  28% of the refused, 10% of the fires; the fleets at k-2 picked launches whose bundle held. Recent: 14% of all launches,
  12% of the refused, 28% of the fires. The dump costs the same in both periods (fit dumps -34.2%, recent -44.8%).
- By period with the live split: Sep 24 - Sep 26 09:24, fires +15.8% (13, median +2.3%) against all launches +5.3%; after,
  fires -28.7% (5, 40% dead) against all launches +0.7%.
- Other variants on the recent set (h300): fleets >= 2 at k-1 41 launches +13.0%; at the tick's shot 24 +3.3%; at k-3
  13 -5.2%; fleets >= 3 at k-2 4 +2.2%; wallets >= 2 at k-2 20 +11.8%; fleets >= 1 at k-2 41 +8.9%. In the fit the order
  is the reverse (k-3 +29.8% > k-2 +26.3% > tick +21.7% > k-1 +17.5%). No variant separates from the population's +4.1%
  by more than one standard error (about 11 points on 18-41 launches) on the recent set; the deeper the view, the worse
  it did, which is the opposite of the fit. 24.34's answer (keep the rule) rested on the fit ordering; the recent windows
  do not support a different rule either, they remove the evidence for this one's h300 premium.

### The operator the rule keeps firing on

`python3 data/derived/edge_check/B/template.py` (launches linked by a shared named wallet; `pop.py` prints the templates).
One operator's named-wallet template has 15 launches from Sep 21 17:15 to Sep 27 00:10, and 14 of them were fires (the
early fleets shoot at every one). h300 by launch: Sep 21-22 +30.6, +21.9, +27.3, +24.3; Sep 22 17:53 onward -7.1, +8.4,
-3.3, -15.0 (fit), then +2.3, -8.7, +3.7, +9.0, -50.5, -37.6 (recent). Its share of the fires rose from 8 of 73 (11%) to
6 of 18 (33%); the recent six average -13.6%, and the last two are the dumps at E1+269 and E1+279, 21-31 blocks before
the 300-block exit. The template's fit fires averaged +10.9% (8). Without this template the recent fires average +12.0% (12) and the fit
fires +28.2% (65) (`template.py`, last two lines). Fires in any template of >= 5 launches: fit 21 of 73 at +14.2%,
recent 9 of 18 at -9.6%; outside templates +31.2% and +16.5%.

## 7. What is being missed

1. The launch supply. Qualifying launches per hour fell from 5.86 to 2.70-3.24 and factory creations from about 382 to
   about 200 per hour. At the fit's per-fire return the recent fire rate pays $23.6/day at $13, not $56 (`settle.py`).
   The $/day comparison in the brief mixes this with the per-fire drop; the supply alone accounts for $33 of the $55 fall.
2. The rule's h300 premium was the fleets' selection against dumping bundles (10% dumps among fires against 28% among the
   refused in the fit). Since Sep 24 that selection is gone (28% against 12%), while the 15-block selection is intact
   (lift +15.3 against +18.0). The number to watch is the dump rate among the fires against the refused, per day.
3. Concentration: a third of the recent fires are one operator. The rule has no per-operator cap; that operator's last
   four launches went -15.0 (fit), -8.7, +9.0, -50.5, -37.6 with dumps timed inside our hold.
4. The fleets' view of us is not new: our relay fired 32-35-shot bursts at 9 launches on Sep 19 10:44-13:07 and our
   wallet shot at 28 launches on Sep 18-19 (`visibility.py`); the fit's later windows returned +18.9% to +35.5%. No
   evidence ties the Sep 26-27 losses to our visibility: the two worst were never fired by the engine (aim-skipped).
5. The coverage: the recent "60 h" is 56.6 h of distinct time (the e1m windows overlap; `settle.py`), with a 5-hour gap
   on Sep 26 17:38-22:38 UTC.

## 8. What would settle it, and by when

`python3 data/derived/edge_check/B/settle.py` (normal model, pooled per-fire sd 57.6 points; the recent fire rate
0.32/hour = 7.6/day of full coverage).
- The 18 recent fires favour the recent mean (+3.5%) over the fit mean (+26.3%) by 4.1:1 (log likelihood ratio +1.42).
- To 20:1: about 20 more fires if the recent mean is the true one (2.6 days of full coverage, about Sep 30), about 56 if
  the fit's is (7.3 days, about Oct 4). To 100:1: 40 fires (5.3 days) or 76 (10 days).
- A 95% interval of +-15 points on the period's mean needs 57 fires in all: 39 more, 5.1 days.
- The sharper test, on every launch and not only fires: the lift of the fires over the refused at h300 and the dump rate
  among fires against refused, per day, from the crowd files and tapes the daily protocol already produces
  (`features.py` + `pop.py` on each new window). If the fires' dump rate stays above the refused one for another 20 fires,
  the h300 selection is gone; the h15 lift (+15.3 points on the recent set) is then the part of the edge that remains.
