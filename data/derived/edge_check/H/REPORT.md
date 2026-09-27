**ADD BUNDLE_MAX_ETH = 3.0 (the bundle cap alone; not the template filter).** On the engine's fires at exit block 11 (setting 9 as it lands) the cap takes the fit from 56 fires, +23.0%, $37.3 a day to **49 fires, +27.8%, $40.3 a day**, and the recent set from 15 fires, +17.9%, $11.5 a day to **13 fires, +22.2%, $12.7 a day**. At block 15 it goes from +18.6% ($29.3) to +22.8% ($32.3) on the fit and from +13.6% ($9.4) to +16.8% ($10.6) on the recent set. A random drop of the same number of fires does as well on both periods in 0 of 2,000 draws at block 11 and in 1 of 2,000 at block 15. The cap is chosen on the fit alone and reads better on the recent set. Chosen on the recent set alone it is again the cap, and it reads better on the fit. Every fire the cap removes, in both periods, is the 4.2 ETH operator's flat launch at the fee floor (-10% to -12%). No filter that shares named wallets adds dollars in either period: this operator uses fresh named wallets for almost every launch. Live, the value is small: the minOut guard already refused tonight's two fills, so the cap saves the burst gas and removes the risk of a -10% fill when the guard does not trip.

# Bundle cap and template filter, reviewer H (Sep 27 2026)

Every command runs from the repository root. The scripts and their outputs are in `data/derived/edge_check/H/`. I made no RPC calls, and every number comes from files that were already in the repository. The run order: `check.py` builds the population cache, then `template.py`, then any of the others.

## 1. Population, returns, bundle, hours

`python3 data/derived/edge_check/H/check.py > data/derived/edge_check/H/check.txt`

**Population.**
- Fit: the four fit crowd files, 563 launches.
- Recent: the thirteen recent crowd files plus A's gapA and gapB, de-duplicated by curve with the first file winning, 196 launches.
- The recent set includes sep27pm (16 launches) and sep27eve (8), which G/curves.json.gz does not contain.

**Fires.**
- **Engine**: `fleets_k2(r, engine=True) >= 2`. The function is exec'd verbatim from `src/analysis/fleet_variants.py`.
- **Tables**: `crowd_rules.cums/at`, fleets >= 2 at k-2.
- Counts: fit 56 engine / 73 tables; recent 17 engine / 25 tables. Without sep27pm/eve they are 13 / 19, which matches `fleet_variants.txt` exactly. The engine and tables means on the curves' launches reproduce 24.38: fit +23.0% / +19.5% at h11, recent +22.2% / +15.7%.

**Returns.**
- For the 735 launches in the curves file: G/curves.json.gz `r2[11]` and `r2[15]` (second place in E1, $13, `model_eff`).
- The 24 sep27pm/eve launches have no tape anywhere in the repository.
  - Their h15 is `hold_grid_sep27{pm,eve}.json` `behind1_15_h15`. On the 166 recent launches that have both, this equals r2[15] to a median of 0.00007 (max 0.013, on a +167% launch).
  - Their h11 is set equal to h15 only for the 5 launches that are flat through block 60 (h15 = h30 = h60, and first place = second place).
  - Two recent engine fires therefore have no h11: `0x85a1e161` (h15 −5.2%) and `0x3341b8c1` (h15 +22.7%). They are left out of the h11 statistics. Neither is touched by any filter (bundles 0.73 and 0.42 ETH, no template flag), so the gap affects the level and not the filters' differences.
  - With their h15 substituted, the engine's recent h11 reads +16.8% / $12.1 without the cap and +20.4% / $13.4 with it (`sens.txt` (b)).

**Bundle ETH.**
- Recomputed from the cached tapes with `e1_multi.py`'s rule for all 735 launches: creation-second buys after the first row whose fee equals the tier within 0.0008.
- It equals the `bundle_eth` of the launches files on all 172 recent launches that have both (max difference 0.0000 ETH).
- The fit launches files carry no `bundle_eth`, so the tapes are the only source there.
- The 24 tape-less launches take `bundle_eth` from `launches_sep27{pm,eve}.json`, which is `e1_multi`'s own output.

**Hours.**
- Fit: 96 h. The union of the windows' T0 spans gives 95.96 h.
- Recent: the union of the fifteen windows' T0 spans is **62.65 h**, not the ~80 h the brief expected. The union of the scan windows (`t_lo..t_hi` of the e1m/launches files) is 76.23 h.
- Recent $ a day is given on 62.65 h, with the 76.23 h figure in brackets in `price.txt`. The choice of hours scales both arms of every comparison equally and cannot change a verdict.

## 2. The operator, and why a named-wallet filter cannot see it

`python3 data/derived/edge_check/H/template.py > template.txt` and `python3 data/derived/edge_check/H/bundle.py > bundle.txt`

- **Every launch in the population with a bundle of 4.0 ETH or more is flat at the fee floor.** That is 11 of 11 in the fit and 7 of 7 recent, at h11 −10.6% (fit) and −10.4% (recent). Nobody trades after the seat.
- **The engine fired on 7 of them in the fit and 2 recent.**
  - Fit: Sep 21 01:32, Sep 21 23:51 (6 fleets), Sep 22 00:36, Sep 22 22:27, Sep 23 06:00, 19:28 and 19:52.
  - Recent: Sep 27 21:12 `0xa6929b03` and 21:27 `0x96803325`.
  - All sit at −10.0% to −11.9% at both exits. Bundle plus the creator's buy totals 4.20-4.33 ETH on every one: a fixed template (`devbuy.txt`).
- **The rule does not fire on the 3.0-4.0 ETH launches.** There are 3 (2 fit, 1 recent), all negative, none a fire.
- **The 2.0-3.0 ETH fires are good in the fit.** Five engine fires at +33.5% at h15, including `0x077cccf4` at +105.9%. The recent set has none.
- **The operator almost never reuses its named wallets.** Over its 17 launches at the template's sizes (4.13-4.30, 2.507, 1.64-1.65, 1.37 ETH), the named-wallet sets are disjoint except for two same-evening pairs (Sep 27 21:12/21:27; Sep 26 23:20 with Sep 27 18:42).
  - The causal template filter therefore flags none of its launches (`bundle.txt` (a), `template-flag False`).
  - Reviewer B's template (15 launches Sep 21-27, ~0.7 ETH bundles, 22 named wallets; template 164 in `template.txt`) is a different operator.
  - **The bundle size is the fingerprint; the wallets are not.**
- **The engine can see the bundle in time.** On every launch of 2.5 ETH or more that has a tape and k >= 3, the whole bundle is already in the blocks up to k-2, the gate's view (`python3 data/derived/edge_check/H/gate_view.py > gate_view.txt`). A 3.0 ETH cap on the k-2 view drops exactly the same 7 fit fires as on the whole second. Tonight's two cannot be checked by block because they have no tape.
- **The engine's own bundle count** (`sniper_engine.py` `fold_buy`: named wallets and the creator within 9 blocks) adds the creator's buy. That buy has a median of 0.026 ETH and at most 0.19 on these fires. The gap between the largest fire below the cap (2.83 ETH with the creator's buy) and the smallest above it (4.20) absorbs the difference.
- **The setting exists.** `BUNDLE_MAX_ETH` is in the engine (0 = off, the current live value), checked as `bundle_eth > BUNDLE_MAX_ETH`.

## 3. The prices (`python3 data/derived/edge_check/H/price.py > price.txt`)

Columns:
- **fires**, **mean**, **win** (> 0) and **dead** (< −40%) describe the kept fires.
- **$/day**: the kept fires' $ after $0.33 gas, divided by the hours × 24 (fit 96 h, recent 62.65 h).
- **drop f/r**: fires removed on the fit and on the recent set, with the removed fires' mean.
- **null**: the share of 2,000 random drops of the same number of fires per period (seed 11) whose kept mean is at least the filter's. Given for the fit, the recent set, and **both** at once.

**Engine's fires, exit block 11** (recent: 15 fires with a known h11, 2 more without):

| filter | fit fires | mean | win | dead | $/day | recent fires | mean | win | dead | $/day | drop f/r (their mean) | null fit / rec / **both** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 56 | +23.0% | 73% | 2% | $37.3 | 15 | +17.9% | 67% | 0% | $11.5 | - | - |
| cap 1.0 | 34 | +23.7% | 82% | 3% | $23.4 | 9 | +15.8% | 78% | 0% | $6.0 | 22/6 (+22.0%/+21.1%) | 44% / 61% / 27.2% |
| cap 1.5 | 42 | +27.1% | 81% | 2% | $33.5 | 11 | +20.0% | 82% | 0% | $9.6 | 14/4 (+10.8%/+12.1%) | 6% / 35% / 2.2% |
| cap 2.0 | 44 | +26.5% | 82% | 2% | $34.2 | 13 | +22.2% | 77% | 0% | $12.7 | 12/2 (+10.4%/−10.0%) | 9% / 5% / 0.4% |
| **cap 3.0** | **49** | **+27.8%** | **84%** | **2%** | **$40.3** | **13** | **+22.2%** | **77%** | **0%** | **$12.7** | **7/2 (−10.8%/−10.0%)** | **0% / 4% / 0.0%** |
| template | 52 | +23.7% | 71% | 2% | $35.7 | 10 | +22.7% | 80% | 0% | $10.0 | 4/5 (+14.6%/+8.4%) | 36% / 22% / 7.5% |
| template + cap 1.0 | 30 | +24.9% | 80% | 3% | $21.8 | 5 | +17.3% | 100% | 0% | $3.7 | 26/10 | 35% / 51% / 17.9% |
| template + cap 1.5 | 38 | +28.4% | 79% | 3% | $31.9 | 7 | +23.5% | 100% | 0% | $7.3 | 18/8 | 5% / 27% / 1.8% |
| template + cap 2.0 | 40 | +27.6% | 80% | 2% | $32.6 | 8 | +30.8% | 100% | 0% | $11.3 | 16/7 | 7% / 4% / 0.4% |
| template + cap 3.0 | 45 | +29.0% | 82% | 2% | $38.7 | 8 | +30.8% | 100% | 0% | $11.3 | 11/7 | 0% / 4% / 0.1% |

**Engine's fires, exit block 15** (17 recent fires):

| filter | fit fires | mean | win | $/day | recent fires | mean | win | $/day | null both |
|---|---|---|---|---|---|---|---|---|---|
| none | 56 | +18.6% | 68% | $29.3 | 17 | +13.6% | 53% | $9.4 | - |
| cap 1.5 | 42 | +22.4% | 76% | $27.1 | 13 | +15.0% | 62% | $8.1 | 3.2% |
| cap 2.0 | 44 | +21.6% | 75% | $27.3 | 15 | +16.8% | 60% | $10.6 | 0.5% |
| **cap 3.0** | **49** | **+22.8%** | **78%** | **$32.3** | **15** | **+16.8%** | **60%** | **$10.6** | **0.05% (1 of 2,000)** |
| template | 52 | +19.1% | 65% | $27.9 | 12 | +18.2% | 58% | $9.4 | 8.1% |
| template + cap 3.0 | 45 | +23.7% | 76% | $31.0 | 10 | +23.9% | 70% | $10.6 | 0.0% |

**The tables' fires** (full grid in `price.txt`):

| | fit none → cap 3.0 | recent none → cap 3.0 | null both | template alone, fit / recent $/day |
|---|---|---|---|---|
| exit block 11 | 73 +19.5% $40.2 → 66 +22.7% $43.3 | 21 +13.3% $11.2 → 18 +17.2% $13.1 | 0.0% | $35.8 / $9.5 (none $40.2 / $11.2) |
| exit block 15 | 73 +16.2% $32.5 → 66 +19.1% $35.5 | 25 +10.0% $9.2 → 22 +12.7% $11.2 | 0.0% | $28.8 / $9.7 (none $32.5 / $9.2) |

**Per fit window** (engine, exit block 11; $ a day on the window's T0 span: 23.14, 34.76, 29.30 and 8.75 h). The other three grids are in `price.txt`.

| filter | sep1819 | sep2021 | sep2223 | sep23day |
|---|---|---|---|---|
| none | 11 +20.4% $26.5 | 20 +25.3% $40.9 | 15 +21.3% $29.9 | 10 +23.7% $75.6 |
| cap 3.0 | 11 +20.4% $26.5 | 17 +31.7% $44.5 | 13 +26.4% $33.0 | 8 +32.2% $84.5 |
| template | 11 +20.4% $26.5 | 19 +25.3% $38.9 | 15 +21.3% $29.9 | 7 +29.2% $66.5 |
| template + cap 3.0 | 11 +20.4% $26.5 | 16 +32.1% $42.4 | 13 +26.4% $33.0 | 5 +44.9% $75.4 |

The 3.0 cap is never worse in any fit window, for either population at either exit. It acts on Sep 21, 22, 23 and 27 and nowhere else (`sens.txt` (c)).

## 4. Choices and the null test

**Choice on one period, read on the other.** The objective is $ a day at full fill, among the ten variants including no filter.

| population, exit | chosen on the fit | read on the recent set (vs none) | chosen on the recent set | read on the fit (vs none) |
|---|---|---|---|---|
| engine, 11 | cap 3.0 ($40.3 vs $37.3) | $12.7 vs $11.5, +22.2% vs +17.9% | cap 3.0 ($12.7) | $40.3 vs $37.3 |
| engine, 15 | cap 3.0 ($32.3 vs $29.3) | $10.6 vs $9.4 | template + cap 3.0 ($10.6, a tie with cap 3.0 to the cent) | $31.0 vs $29.3 (cap 3.0 alone: $32.3) |
| tables, 11 | cap 3.0 ($43.3 vs $40.2) | $13.1 vs $11.2 | cap 3.0 ($13.1) | $43.3 vs $40.2 |
| tables, 15 | cap 3.0 ($35.5 vs $32.5) | $11.2 vs $9.2 | template + cap 3.0 ($11.6 vs cap 3.0 $11.2) | **$31.8 vs $32.5: fails** |

**The plateau.** The fine sweep of the cap on the engine's fires (`bundle.txt` (c)) gives the same result for every cap from 3.0 to 4.1 ETH on both periods and at both exits: fit $40.3, recent $12.7 at block 11. From 2.25 to 2.75 the fit is $39.3. A cap at or below 2.0 drops the fit's good 2.1-2.8 ETH fires and loses fit dollars. The cap sits in a gap in the data (no fire between 2.77 and 4.14 ETH), not on a spike.

**The null test** (24.34's discipline: permute the filter by dropping the same number of random fires, 2,000 draws).
- A random drop of 7 fit and 2 recent engine fires matches the cap's kept mean on both periods in 0 of 2,000 draws at block 11.
  - On the fit alone that is 0 of 2,000.
  - On the recent set alone it is 4%, because two dropped fires are few.
- At block 15 it is 1 of 2,000. On the tables' fires it is 0 of 2,000 at both exits (exact values in `price.json`, key `null`).
- Ten variants were tried at two exits on two populations: 40 cells, plus the 18-cell template grid in `sens.py`. The cap's P(both) stays far below 1/40 after that count.
- **24.34's other failure mode is absent here.** The cap's gain does not rest on one launch. Every dropped fire is at the fee floor, −10.0% to −11.9%, so each is worth +$1.63 to +$1.88 to drop, and removing any one of them from the evidence leaves the sign unchanged in both periods.

**The template filter fails.** The brief's filter: 3 or more shared named wallets with a template of 5 or more earlier launches, causal.
- It removes fires that pay: +14.6% (fit) and +8.4% (recent) at block 11 on the engine's fires. It loses dollars on both periods: $35.7 vs $37.3 and $10.0 vs $11.5.
- Its null P(both) is 7.5% at block 11 and 8.1% at block 15.
- The same holds over the grid of 2, 3 or 5 shared wallets and templates of 3, 5 or 8 launches, alone, on both populations at block 11: −$0.1 to −$6.6 a day on the fit and −$1.3 to −$1.7 on the recent set (`python3 data/derived/edge_check/H/sens.py > sens.txt` (a)).
- Reviewer B's hindsight components (any shared wallet, all launches, 5 or more) are worse: engine h11 −$4.7 fit and −$1.9 recent.
- **Why this differs from B's reading.** B's template fires, −9.6% recent at 300 blocks, are a 300-block reading. At the 9-11 block exit the same fires make +6% to +15%, above the $0.33 gas.

## 5. What it is worth, and the caveats

- **Modelled gain at full fill in second place.**
  - Block 11, engine: +$3.0 a day on the fit and +$1.25 recent (62.65 h; +$1.03 on 76.23 h).
  - Block 15: +$3.0 and +$1.25.
  - At the live mix (about half the bursts fill, a third of those land third: 24.38) it is roughly 40% of that.
- **Live, the gain is smaller still.** Tonight's two fires on the template (21:12, 21:27) were refused by the minOut guard, so their real cost was $0.38 of gas, not −$1.63 each. The cap turns that $0.38 into zero, about $0.15 a day at the recent rate.
  - Its real value is insurance: a fill at −10% whenever the guard does not trip.
  - The guard caught 2 of 2 live. Whether it would catch the fit's seven cannot be measured from these files. On their tapes the whole bundle was in by k-2, a case where the build-time quote need not be stale, so the guard might have let them fill.
- **The recent evidence is thin.** It is two launches from one operator on one evening. The fit's is seven, from the same fingerprint, on Sep 21-23. Together that is 9 of 9 engine fires. Of the launches of 4.0 ETH or more, 18 of 18 are negative, and all 21 above 3.0 ETH are too, at h11 −8.6% to −13.0% and h15 −8.6% to −19.9%. There is no exception in either period.
- **The cap is an operator fingerprint, not a law of bundle size.** Among the engine's fires, the bundle bins from 1.0 to 3.0 ETH average +6% to +43% at h15 (`bundle.txt` (b)). If the operator changes its size, the cap stops working. If an honest team spends 3.0-4.1 ETH, the data has no fire there to price.
- **h11 on the recent set is missing for 2 of 17 engine fires** (the tape-less sep27pm/eve). Neither is touched by the filters, and with h15 substituted the conclusions are the same (section 1).

## Reproduce

    python3 data/derived/edge_check/H/check.py     > data/derived/edge_check/H/check.txt      # population, fire counts, proxies, bundle check, hours
    python3 data/derived/edge_check/H/template.py  > data/derived/edge_check/H/template.txt   # causal template flags (+ template_flags.json)
    python3 data/derived/edge_check/H/price.py     > data/derived/edge_check/H/price.txt      # every table of section 3-4, null test, choices
    python3 data/derived/edge_check/H/bundle.py    > data/derived/edge_check/H/bundle.txt     # the big-bundle fires, bundle bins, fine cap sweep
    python3 data/derived/edge_check/H/gate_view.py > data/derived/edge_check/H/gate_view.txt  # bundle visible by block k-2
    python3 data/derived/edge_check/H/devbuy.py    > data/derived/edge_check/H/devbuy.txt     # the creator's own buy (engine's count)
    python3 data/derived/edge_check/H/sens.py      > data/derived/edge_check/H/sens.txt       # template grid, B hindsight, h11 substitution, by day
