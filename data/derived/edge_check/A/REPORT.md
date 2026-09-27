**Verdict: REAL, not a measurement artefact. The recent fires are worse than the fit's (rank test p = 0.013, bootstrap
p = 0.034, permutation of means p = 0.055). The rule's lift over the launches it refuses fell from +27 points to −1 point,
while the qualifying population as a whole did not change (+3.3% → +4.3%). The loss is in outsiders' buying after the seat.
How big the edge is now cannot be decided from 18 fires: the recent mean's 95% interval is −14% to +27%.**

# Edge check, reviewer A (Sep 27 2026)

Every number below comes from a script in `data/derived/edge_check/A/`. Each script runs from the repo root, and its full
output is saved next to it (`*.txt`). The one network pull is `pull_tapes.py`: the Buy/Sell tape b0..b0+640 of all 91
fires, public RPC, 4 threads, 208 s, cached in `tapes.json.gz`. Everything after that pull runs offline from the cache,
except `world.py` (9 `eth_getCode` calls) and `extend_window.py` (below). The fit set is the four windows Sep 18-23 (563
launches, 73 fires). "Recent" means Sep 24-27: the 11 committed crowd files, 166 records, 160 unique launches, 18 fires.
Returns are second place in the E1 block, 300-block hold, $13, before gas, unless a line says otherwise.

## 1. Same yardstick: yes. No artefact found.

| check | fit | recent | command |
|---|---|---|---|
| fleets at k-2, independent re-implementation vs `crowd_rules.cums` | 0 mismatches / 563 | 0 / 160 | `python3 data/derived/edge_check/A/check_counts.py` |
| fires (fleets >= 2 at k-2) | 73 | 18 (none of the 6 duplicated records is a fire) | `check_counts.py` |
| mean h300, **my independent model** (`price.py: my_model`) | +26.32% | +3.46% | `python3 data/derived/edge_check/A/price.py` -> `price.txt` |
| mean h300, reach_table's `model_eff` on the same tapes | +26.32% (max per-fire diff 0.0000) | +3.46% (0.0000) | same |
| mean h300, hold_grid's stored `behind1_15_h300` | +26.69% (max diff 2.2 pts, fixed-token folding) | +3.70% (1.3 pts) | same |
| crowd files missing the token (approvals counted as a fleet) | 0 | 0 | `python3 data/derived/edge_check/A/yardstick.py` -> `yardstick.txt` |
| k in the crowd file vs the tape's own stamps (bE1-b0-1) | 0 differ | 0 differ | same |
| tiers / bundle ETH (min, median) | 2.0-3.0% / 0.320, 0.725 | 2.0-3.0% / 0.314, 0.738 | same |
| tape reaches the 300-block exit | 73/73 | 18/18 | same |
| ETH at $1,800 or $3,500 instead of $2,570 (max change per fire) | 0.7 pts | 0.4 pts | same |
| the engine's creator-supply filter (>= 1%) applied to both | 64 fires +28.9% | 16 fires +4.6% | same |
| implied buy fee over tier, by second after creation (median) | s+1 6.18%, s+2 0.19%, s>=3 0.00% | s+1 6.18%, s+2 0.19%, s>=3 0.00% | `price.txt` (curve state before every event) |
| implied sell fee over tier (1st-99th pct) | 0.0000 to 0.0000 | 0.0000 to 0.0000 | `price.txt` |

Both sets go through the same `e1_multi.py`, which has not changed since Sep 18. They use the same `crowd_raw.py`, re-pulled
for the fit windows on Sep 24 after the token fix; no file lacks the token. They use the same k-2 view, the same pricing
(reach_table prices both sets in one run with one function) and the same tape length. The tape-length fix of Sep 26
touched only live_vs_table; `hold_grid.py` reads to b0+620, `paper_day.py` to b0+hold+30, `stake_table.py` and
`reach_table.py` to b0+330, and `e1_multi.py`'s holds stop at 60 blocks. Gas ($0.33) and ETH ($2,570) are constants in
both sets. **Summary:** the two numbers are the same calculation on the same definitions, and both reproduce exactly with
code written separately.

## 2. Statistics: the drop is unlikely to be chance (p = 0.01-0.05). The size of the drop is not pinned down.

`python3 data/derived/edge_check/A/stats.py 300` -> `stats_h300.txt` (seeded; 200,000 draws)

| | fit | recent |
|---|---|---|
| fires, mean, median | 73, +26.3%, +20.7% | 18, +3.5%, −6.6% |
| sd per fire, se of the mean | 0.591, 0.069 | 0.480, 0.113 |
| wins, dead (< −40%) | 49/73, 6/73 | 7/18, 2/18 |

- Difference of means: +22.9 points, Welch t 1.72.
- Bootstrap: 18 fires drawn from the fit's 73 average ≤ +3.5% in **3.4%** of draws. 95% interval of the recent mean
  **[−14.5%, +27.3%]**; of fit − recent [−4.0%, +46.4%], P(difference ≤ 0) = 4.6%.
- Permutation (pool the 91, split 73/18): difference of means ≥ 22.9 in **5.5%**; difference of medians ≥ 27.3 points in
  **1.0%**.
- Mann-Whitney U: z 2.24, one-sided **p 0.0125**. Wins, Fisher one-sided: **p 0.028**.
- Random 60-hour stretches of the fit: the four windows are laid end to end (96 h), the start slides in 15-minute steps
  with wrap-around, 384 stretches. Each stretch holds 33-61 fires, the lowest mean is +20.1%, and **0 of 384** read
  ≤ +3.5%. Runs of 18 consecutive fit fires in time order: 56 runs, means from +9.1% to +48.3%, **0 of 56** at
  ≤ +3.5%.
- Five losers in a row: the fit has one run of 5 as well (its longest). P(a run of ≥ 5 losers within 18 fires drawn from
  the fit) = 3.8%.
- Sequential log-likelihood ratio on the 18 recent fires, "fit mean" against "mean 0" (normal, sd 0.576): −1.39. That
  leans to 0 but has not crossed the 95/5 boundary of ±2.94.
- The recent set is not uniform. The paper windows of Sep 24-25 have 12 fires at +15.0% (median −1.1%). From Sep 25 22:27
  on there are 6 fires at **−19.6%** (median −24.3%, 1 win, 2 dead).
- The fit is in-sample. Fleets ≥ 2 at k-2 was chosen on these four windows among about 15 gate variants, which scored
  +19% to +30% (`crowd_rules.txt`), so some shrinkage out of sample is expected. The 12 paper fires (+15%) are the first
  clean out-of-sample reading, and the 6 after them are the second.

Day by day. This table prices every launch with hold_grid's `behind1_15_h300`, which is within 2.2 points of my model on
every fire. `python3 data/derived/edge_check/A/population.py` -> `population.txt`:

| UTC day | launches | fires | fired mean | refused mean |
|---|---|---|---|---|
| Sep 18 | 104 | 13 | +19.0% | +2.0% |
| Sep 19 | 37 | 1 | +22.5% | −3.6% |
| Sep 20 | 42 | 7 | +29.2% | −7.0% |
| Sep 21 | 138 | 20 | +27.4% | +1.8% |
| Sep 22 | 170 | 19 | +22.4% | +3.6% |
| Sep 23 | 72 | 13 | +38.5% | −11.5% |
| Sep 24 | 55 | 9 | +1.8% | +6.3% |
| Sep 25 | 49 | 4 | +48.4% | +3.0% |
| Sep 26 | 47 | 4 | −26.3% | +0.8% |
| Sep 27 (to 04:09) | 9 | 1 | −37.5% | +21.0% |

**The gate's lift is the cleanest single measure.** It is the fired mean minus the refused mean, and it removes whatever
the whole market did (`population.txt`):

| | all launches | fired | refused | lift | lift, bootstrap 95% |
|---|---|---|---|---|---|
| fit | 563, +3.3% | 73, +26.7% | 490, −0.2% | **+26.9** | [+12.6, +42.1] |
| recent | 160, +4.3% | 18, +3.7% | 142, +4.4% | **−0.7** | [−20.6, +24.9] |

Fit lift minus recent lift: 95% [−1.4, +53.0], P(≤ 0) = 3.0%. The recent bootstrap reaches the fit's point lift (+26.9)
in 1.9% of draws. Second place at 300 blocks is worth the same on the whole population now as before. What is gone is
the extra return of the launches with 2+ fleets at k-2. By fleets at k-2 the recent means are 0: +2.7%, 1: +13.4%,
2: +4.1%, 3+: +2.5%. The fit's were −0.5%, +1.1%, +27.1%, +26.0%.

## 3. What changed on the chain for the launches the rule fires on

`python3 data/derived/edge_check/A/chain_change.py` -> `chain_change.txt`. A trader on the tape is the Buy/Sell event's
address, which is msg.sender on the curve: the relay for relay shots and the sender for direct shots. **named** = the
launch's named wallets plus the creator; **fleet** = any relay or sender that shot at the curve in blocks 0..k+1;
**early** = any other buyer up to the seat block; **outsider** = everyone else.

| per fire (mean / median) | fit (73) | recent (18) |
|---|---|---|
| k | 6.6 / 6 | 6.3 / 6 |
| fleets at k-2 | 2.51 / 2 | 2.22 / 2 |
| fleets at the end of the creation second | 4.2 / 4 | 4.3 / 3.5 |
| fleets including the seat block | 7.2 / 7 | 6.4 / 4.5 |
| rival shots by k-2 (known at the decision) | 22.1 / 9 | 16.9 / 6.5 |
| rival shots in the whole creation second | 90 / 48 | 54 / 28 |
| rival shots in the seat block | 50 / 27 | 30 / 21 |
| buys in the seat block | 5.2 / 5 | 3.9 / 2.5 |
| ETH bought in the seat block | 0.44 / 0.40 | 0.31 / 0.27 |
| bundle ETH (e1_multi) | 1.18 / 0.73 | 1.04 / 0.74 |
| named wallets | 12.6 / 13 | 13.7 / 14 |
| creator's own buy, share of supply | 2.2% / 1.7% | 1.8% / 1.5% |
| share of the named's tokens sold by seat+300 | 7.6% / 0 | 22.8% / 0 |
| ETH sold by the named by seat+300 | 0.077 / 0 | 0.256 / 0 |
| fires with a named sell by seat+300 | 15/73 | 8/18 |
| share of fleet+early tokens sold by seat+60 / +300 | 38% / 51% | 44% / 69% |
| **outsider ETH bought, seat+16..60** | **1.39 / 0.57** | **0.94 / 0.095** |
| outsider ETH bought, seat+61..300 | 0.49 / 0.25 | 0.58 / 0.25 |
| outsider ETH bought, total to seat+300 | 1.95 / 0.83 | 1.56 / 0.70 |

**Where the 23 points went** (`python3 data/derived/edge_check/A/decompose.py` -> `decompose.txt`). This is a
counterfactual on the same tapes with the same model:
- The bundle dumped (the named sold ≥ 50% of their tokens within 300 blocks of the seat) on **5/73 fit fires and 4/18
  recent** (Fisher one-sided p 0.072). Fit fires with a dump averaged −58.2% and those without +32.5%. Recent: −17.9%
  and +9.5%. **Recent fires without a dump are still 23 points below fit fires without one.**
- 0xe65b85ad is left out because removing its bundle's 92% sale makes the counterfactual meaningless. Without it,
  removing the named wallets' sells lifts the fit mean from +26.3% to +30.1% and the recent mean from +0.2% to +9.0%. The
  bundle therefore accounts for **about 5 of the 26 points**.
- Removing the outsiders' buys as well puts both sets at the same number: fit −37.7%, recent −36.1%, gap −1.6 points.
  **The rest of the gap, about 21 points, is outsiders' demand after the seat.** Without follow-on buyers the seat loses
  about 37% in both periods. The cost of the seat (fees, the buy ahead of us, the fleets' own buying and selling) has not
  changed; the buyers who come after it have.

**Composition does not explain it.** Take the fit's mean in each bucket and weight it by the recent fires' mix (hour of
day, tier, k, bundle size, fleets at k-2); every variable predicts **+25% to +27%** for the recent set. The crowd-size
variables predict at most 6 points of the drop: rival shots by k-2 → +25.3%, rival shots in the creation second
→ +22.1%, seat-block buys → +20.3%, fleets including the seat block → +24.3%. Serial launchers: 5/73 fit fires and 1/18
recent come from repeat creators, and no recent fire's creator launched in the fit windows. Dead rate: 6/73 fit, 2/18
recent.

**The fleets changed.** Across all qualifying launches the average number of distinct shooters per launch is the same
(1.62 fit, 1.58 recent), but who shoots is not:
- 0xa95fe1ca shot at 27.9% of fit launches and 4.4% of recent ones. 0xf9af9f38 went from 8.2% to 33.1%. Neither is ever
  among the k-2 fleets of a fire; both arrive late.
- 0x460b1f81 was the fit's most frequent k-2 fleet: 22 fires, +51.9%. Recently it has 3 fires at −4.8%. 0xbd7c6f67 went
  from 16 fit fires at +13.7% to 5 recent fires at −14.6%, and it is in both fires of the Sep 26-27 night (−50.5%, −37.6%).
- 12 of the 24 addresses counted at k-2 in recent fires were never counted at k-2 in a fit fire. The 11 recent fires with
  such an address averaged −12.7%; the 7 whose fleets all date from the fit averaged +28.8%.
- A like-for-like check in time order, with Sep 18-19 as burn-in, finds no such split in the fit: fires with a
  first-seen fleet averaged +28.3% (33) and those with only known fleets +27.8% (26). The recent split is therefore new.
  It is also found after looking at the data and rests on 11 and 7 fires, so it is a hypothesis to test on future fires,
  not a finding.

**Before and after our own bursts became visible** (Sep 26 09:15, `world.py`). The 13 recent fires before it averaged
+15.8% at h300 and +17.0% at h15. The 5 after it averaged **−28.7%** at h300 and +1.8% at h15. Those 5 had fewer rival
shots by k-2 (9.4 against 19.8), fewer seat-block buys (2.6 against 4.5), less outsider ETH (0.36 against 2.02), and the
named sold 57% of their tokens by +300 (against 9%). Our relay filled on only one of these launches, so this is 5 fires
and 1 visible fill: it cannot separate a reaction to us from a bad day.

## 4. Alternatives the rule does not see

`python3 data/derived/edge_check/A/alternatives.py` -> `alternatives.txt`. Parts (a), (c) and (d) use my model on the
fires' tapes; part (b) uses hold_grid's stored columns on the whole population.

The rule's own fires, second place, $13, by exit (mean, win; $/day after gas over 96 h and 60 h):

| exit | fit | recent |
|---|---|---|
| 15 blocks | +16.2%, 66%, $32.5/day | **+12.8%, 56%, $9.6/day** |
| 60 blocks | +16.2%, 66%, $32.5/day | +4.4%, 44%, $1.7/day |
| 150 blocks | +21.2%, 66%, $44.2/day | +11.1%, 56%, $8.0/day |
| 300 blocks (the rule) | +26.3%, 67%, $56.4/day | +3.5%, 39%, $0.9/day |
| 600 blocks | +19.6%, 52%, $40.5/day | +2.4%, 44%, −$0.2/day |
| −20% stop, else 300 | +27.7%, 66%, $59.7/day | −0.7%, 33%, −$3.1/day |
| first place instead of second, 300 | +40.8%, 70% | +14.8%, 72% |

- **The first 15 blocks held up; the drop is after them.** At h15 fit and recent differ by 3.4 points. At h300 they
  differ by 22.8.
- Paired on the same fires, h15 minus h300: fit −10.1 points (t −1.63), recent +9.4 (t +1.06), all 91 −6.2 (t −1.18).
  The recent fires lean towards the short hold but not significantly, and the pooled 91 still lean to h300. **The recent
  windows do not overturn 24.34's choice of h300. They do remove its support:** on the recent data h300 is the worst
  exit but one.
- The −20% stop does not help on the recent fires (−0.7% against +3.5%).

Other gates on the whole population (hold_grid `behind1_15_h300`, recent, against fit):

| gate | fit | recent |
|---|---|---|
| fleets ≥ 2 at k-2 (the rule) | 73, +26.7% | 18, +3.7% |
| fleets ≥ 2 at k-1 (not executable) | 147, +19.5% | 41, +13.3% |
| fleets ≥ 2 at k-3 | 52, +30.1% | 13, −5.0% |
| fleets ≥ 2 at the tick's shot (0.76) | 83, +22.1% | 24, +3.5% |
| fleets ≥ 1 at k-2 | 164, +12.5% | 41, +9.2% |
| fleets ≥ 3 at k-2 | 27, +26.0% | 4, +2.5% |
| wallets ≥ 2 at k-2 | 73, +20.9% | 20, +12.1% |
| wallets ≥ 3 at k-2 | 46, +20.8% | 12, +6.2% |
| no gate | 563, +3.3% | 160, +4.3% |

No alternative view or unit restores the fit's level on the recent set. The earlier views (k-3, the tick's shot) are no
better than k-2. The later or looser gates (k-1, wallets ≥ 2, fleets ≥ 1) read +9% to +13% on 20-41 fires. That is
consistent with the fleet signal carrying less information than it did, and it is not a significant improvement: each
gap to the rule is inside one standard error of about 11 points.

## 5. The world

- **Fees:** unchanged. The implied fee is computed from the curve state before every event on the 91 tapes: fit 4,495
  buys and 2,664 sells, recent 1,008 buys and 682 sells (`price.txt`). Buys pay the tier +6.18% in second +1, +0.19% in
  second +2 and +0.00% from second +3; sells pay exactly the tier. Both periods, to four decimals.
- **Contracts:** unchanged. The factory is the same (0xe33e9e47; every launch in both sets was found through it), and all
  91 creation transactions use selector f85f8e41. Four fit and four recent curves share one 10,229-byte runtime. The only
  differences are two 20-byte addresses and four single bytes, i.e. the per-launch immutables (`world.py` ->
  `world.txt`).
- **Sequencer cadence:** unchanged. Second +1 has 9.85 blocks on fit fires and 9.94 on recent ones; second +2 has 9.95 and
  9.89. Over every qualifying launch, k (blocks after b0 in the creation second) averages 5.46 in the fit and 5.17
  recently.
- **The market halved** (`python3 data/derived/edge_check/A/market.py` -> `market.txt`, e1_multi's own counts). Pons V2
  creations went from 382 to 204 an hour, and qualifying launches from 5.56 to 2.72 an hour. The qualifying share of
  creations is about the same (1.46%, 1.33%). The recent windows include more night hours, which accounts for part of
  this.
- **Around our exit:** nobody is selling in front of the 300-block exit. Sells per block at seat+297..303 are 0.048
  against 0.068 at seat+200..296 on recent fires, and 0.025 against 0.034 on fit fires (`world.txt`). With 2 bursts and 1
  fill, the fleets' response to our bursts cannot be measured.

