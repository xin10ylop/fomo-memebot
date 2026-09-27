**ADD BUNDLE_MAX_ETH = 3.0; the template filter: NOTHING PROVEN.** On the engine's population at exit block 11 the cap takes the fit from 56 fires, +23.0%, $37.25 a day to 49 fires, +27.8%, $40.29 a day (+$3.04). On the recent windows priced at h11 (Sep 24 12:38 to Sep 27 09:20, 66.8 h) it changes nothing: 13 fires, +22.2%, $11.95 a day, because no engine fire there has a bundle above 3 ETH. With Sep 27 pm/eve added (76.2 h) it removes tonight's two 4.233 ETH fires, both flat at −10.0% at every exit, for +$1.03 a day (h15: 17 → 15 fires, +13.6% → +16.8%, $7.71 → $8.74 a day). The fit alone chooses it at h11 and at h15, on both populations. It never lowers the recent set's dollars. In the null test a random drop of the same number of fires does as well on both periods in 0.1% of 2,000 draws (h11) and 0.0% (h15 with tonight). Every fire above 3 ETH in both periods (10 of 10) sits exactly at the fee floor from the seat to block 300. The causal template filter costs money on the fit at both exits (engine −$1.57 a day at h11, −$1.34 at h15). On the recent set it is worth at most $0.01 a day, because the fires it drops still average +8.4% at h11. The 4.233 ETH operator uses fresh named wallets on every launch, so a named-wallet template never catches it.

# Bundle cap and template filter, reviewer I (Sep 27 2026)

Every command runs from the repository root. The scripts and their outputs are in `data/derived/edge_check/I/`, and each script's docstring gives its command. No RPC was used: every input is a file already in the repo. Folder H was not read.

## 1. Population, yardstick, hours

`common.py` is imported by every script.

**Launches.** The fit is the crowd files sep1819, sep2021, sep2223 and sep23day: 563 launches. The recent set ("rec") is the eleven files sep24paper to sep27night plus A's gapA and gapB: 172 launches. "late" is sep27pm and sep27eve: 24 launches. All sets are de-duplicated by curve, first file wins, which is G's order. rec+late has 196 launches.

**Fires.**
- Engine: `fleet_variants.fleets_k2(r, engine=True) >= 2`. The function is exec'd from `src/analysis/fleet_variants.py` itself.
- Tables: `crowd_rules.cums/at >= 2` at block k−2.
- Counts: fit 56 engine / 73 tables fires; rec 13 / 19; late 4 / 6.

**Returns.**
- `edge_check/G/curves.json.gz` r2[h]: second place in E1, $13, $0.33 gas a burst.
- It reproduces 24.38 to the decimal: engine fit h11 +23.0%, h15 +18.6%, $149.01; rec +22.2%, +18.0%, $33.26. Tables fit +19.5%, +16.2%; rec +15.7%, +12.6% (`price.txt`).
- **The 24 late launches are not in curves.json.gz, and no tape of them is in the repo.** I price them at h15 only, from `hold_grid_sep27{pm,eve}.json` behind1_15_h15. On the 166 recent launches that have both prices, that column minus r2[15] has a median absolute difference of 0.01 points. On the 18 recent tables' fires the largest difference is 0.48 points (`python3 data/derived/edge_check/I/check_late.py` → `check_late.txt`).
- The late launches have no h11 price. The exception is the cap's effect there, which is exact: the fires the cap removes are flat at the fee floor from h15 to h600, so their h11 is the floor too (section 5).

**Bundle.** `bundle_eth` comes from the `launches_*.json` files (the e1m pull's own number) and `A/launches_gap*.json`. `bundle_check.py` recomputes it from the tape rows exactly as `e1_multi.py` does: creation-second buys after the first, with fee equal to the tier within 0.0008. On all 735 launches with a tape the two agree: the largest difference is 0.0000 ETH (`bundle_check.txt`).

**Hours.**
- The fit uses 96.0 h. The union of the four windows' launch-T0 spans is 95.96 h.
- For the recent set I take the union of the windows' pulled bounds [t_lo, t_hi], from the e1m files and A's gap files: **66.8 h** for rec (Sep 24 12:38 to Sep 27 09:20) and **76.2 h** for rec+late (to 21:40).
- The launches' own T0 spans give 54.4 h and 62.6 h. First recent launch to last is 80.5 h; 4.3 h of that is covered by no window (for example Sep 27 09:20-11:54).
- This choice only scales the recent $ a day. It changes no comparison.
- Fire rates, engine: fit 14.0 a day, rec 4.7, rec+late 5.4.
- Output: `python3 data/derived/edge_check/I/price.py` → `price.txt` (first line).

## 2. The filters

**Bundle cap.** The engine keeps a launch only if bundle_eth ≤ cap, for cap = 1.0, 1.5, 2.0 or 3.0 ETH. This is the engine's existing `BUNDLE_MAX_ETH` knob (`src/strategy/sniper_engine.py` lines 83 and 1826), which is off (0) by default.

**Template filter (causal).** Launches are processed in T0 order. A launch is excluded when its named-wallet set shares at least 3 wallets with the wallet union of a template of at least 5 launches, all with a strictly earlier T0. A template grows by the same test: a launch joins, and merges, every template whose union it shares at least 3 wallets with. Launches in the gaps between windows are unseen, so templates can only form from launches inside the windows.
- It flags 52 of 563 fit launches (4 of 56 engine fires, 11 of 73 tables fires) and 13 of 172 rec launches (5 of 13 engine fires, 9 of 19 tables fires) (`python3 data/derived/edge_check/I/templates.py` → `templates.txt`).
- It catches B's operator (the ~0.7 ETH, 22-named-wallet template of `B/template.py`) from Sep 22 17:53 onward.

**The 4.233 ETH operator is not a named-wallet template.** No two of its seven 4.233 ETH launches (Sep 18 14:41 to Sep 27 21:27) share a single named wallet. The one exception is tonight's pair at 21:12 and 21:27, which share all 15. So neither the causal filter nor B's any-shared-wallet linkage can see it before the fact; its fingerprint is the bundle size (`templates.txt`, last block). The fires with bundles of 4.137-4.304 ETH behave identically (section 5). The 2.507, 1.647 and 1.376 ETH variants were never fires by either count.

**Variants tried.** Nine filters plus no filter, on 2 populations, at 2 exits, on 2 recent sets. Nothing else was searched.

## 3. Prices by period

`price.txt`. Columns: fires, mean, win, dead (< −40%), $ a day at $13 after gas. The fit is 96.0 h. "Recent" is rec (66.8 h) at h11 and rec+late (76.2 h) at h15. `price.txt` also has rec at h15 and what each filter removes.

**Engine, exit h11 (setting 9 as it lands)**

| filter | fit n | mean | win | dead | $/day | recent n | mean | win | dead | $/day |
|---|---|---|---|---|---|---|---|---|---|---|
| none | 56 | +23.0% | 73% | 2% | 37.25 | 13 | +22.2% | 77% | 0% | 11.95 |
| cap 1.0 | 34 | +23.7% | 82% | 3% | 23.36 | 9 | +15.8% | 78% | 0% | 5.59 |
| cap 1.5 | 42 | +27.1% | 81% | 2% | 33.52 | 11 | +20.0% | 82% | 0% | 8.99 |
| cap 2.0 | 44 | +26.5% | 82% | 2% | 34.20 | 13 | +22.2% | 77% | 0% | 11.95 |
| **cap 3.0** | **49** | **+27.8%** | **84%** | **2%** | **40.29** | **13** | **+22.2%** | **77%** | **0%** | **11.95** |
| template | 52 | +23.7% | 71% | 2% | 35.68 | 8 | +30.8% | 100% | 0% | 10.58 |
| tmpl+cap 1.0 | 30 | +24.9% | 80% | 3% | 21.79 | 5 | +17.3% | 100% | 0% | 3.45 |
| tmpl+cap 1.5 | 38 | +28.4% | 79% | 3% | 31.95 | 7 | +23.5% | 100% | 0% | 6.85 |
| tmpl+cap 2.0 | 40 | +27.6% | 80% | 2% | 32.63 | 8 | +30.8% | 100% | 0% | 10.58 |
| tmpl+cap 3.0 | 45 | +29.0% | 82% | 2% | 38.72 | 8 | +30.8% | 100% | 0% | 10.58 |

The late windows have no h11 price, but the cap's effect on them is exact: +$3.26, or +$1.03 a day over 76.2 h (`cap_robust.txt`).

**Engine, exit h15**

| filter | fit n | mean | win | dead | $/day | rec+late n | mean | win | dead | $/day |
|---|---|---|---|---|---|---|---|---|---|---|
| none | 56 | +18.6% | 68% | 2% | 29.29 | 17 | +13.6% | 53% | 0% | 7.71 |
| cap 1.0 | 34 | +19.7% | 76% | 3% | 18.93 | 11 | +9.9% | 55% | 0% | 3.32 |
| cap 1.5 | 42 | +22.4% | 76% | 2% | 27.07 | 13 | +15.0% | 62% | 0% | 6.64 |
| cap 2.0 | 44 | +21.6% | 75% | 2% | 27.30 | 15 | +16.8% | 60% | 0% | 8.74 |
| **cap 3.0** | **49** | **+22.8%** | **78%** | **2%** | **32.33** | **15** | **+16.8%** | **60%** | **0%** | **8.74** |
| template | 52 | +19.1% | 65% | 2% | 27.94 | 12 | +18.2% | 58% | 0% | 7.72 |
| tmpl+cap 1.0 | 30 | +20.6% | 73% | 3% | 17.59 | 7 | +11.8% | 57% | 0% | 2.66 |
| tmpl+cap 1.5 | 38 | +23.4% | 74% | 3% | 25.73 | 9 | +18.8% | 67% | 0% | 5.98 |
| tmpl+cap 2.0 | 40 | +22.5% | 72% | 2% | 25.95 | 10 | +23.9% | 70% | 0% | 8.74 |
| tmpl+cap 3.0 | 45 | +23.7% | 76% | 2% | 30.98 | 10 | +23.9% | 70% | 0% | 8.74 |

At h15 on rec alone (66.8 h): none 13 fires, +18.0%, $9.39 a day. cap 3.0 is the same. The template filter gives 8 fires, +27.7%, $9.40.

**Tables, exit h11**

| filter | fit n | mean | win | dead | $/day | rec n | mean | win | dead | $/day |
|---|---|---|---|---|---|---|---|---|---|---|
| none | 73 | +19.5% | 68% | 3% | 40.23 | 19 | +15.7% | 68% | 0% | 11.70 |
| cap 1.0 | 50 | +18.9% | 74% | 4% | 26.57 | 14 | +11.7% | 71% | 0% | 5.97 |
| cap 1.5 | 59 | +21.6% | 73% | 3% | 36.49 | 16 | +15.1% | 75% | 0% | 9.37 |
| cap 2.0 | 61 | +21.3% | 74% | 3% | 37.17 | 18 | +17.2% | 72% | 0% | 12.33 |
| **cap 3.0** | **66** | **+22.7%** | **76%** | **3%** | **43.27** | **18** | **+17.2%** | **72%** | **0%** | **12.33** |
| template | 62 | +20.3% | 68% | 3% | 35.79 | 10 | +24.1% | 90% | 0% | 10.09 |
| tmpl+cap 2.0 | 50 | +22.7% | 74% | 4% | 32.74 | 9 | +28.0% | 100% | 0% | 10.73 |
| tmpl+cap 3.0 | 55 | +24.3% | 76% | 4% | 38.83 | 9 | +28.0% | 100% | 0% | 10.73 |

**Tables, exit h15, recent = rec+late:**
- none: fit 73 fires, +16.2%, $32.47 a day; recent 25 fires, +10.0%, $7.58.
- **cap 3.0: fit 66, +19.1%, $35.51; recent 22, +12.7%, $9.16.**
- template: fit 62, +16.8%, $28.79; recent 15, +15.5%, $7.94.
- tmpl+cap 3.0: fit 55, +20.3%, $31.83; recent 12, +21.9%, $9.52.
- Every other row is in `price.txt`.

**Per fit window** (engine, h11; hours = the window's T0 span; `price.txt`):

| window | none | cap 3.0 | template |
|---|---|---|---|
| sep1819 (23.1 h) | 11, +20.4%, 91% win, 0% dead, $26.55/day | same 11 | same 11 |
| sep2021 (34.8 h) | 20, +25.3%, 60%, 0%, $40.93 | 17, +31.7%, 71%, 0%, $44.48 | 19, +25.3%, 58%, 0%, $38.89 |
| sep2223 (29.3 h) | 15, +21.3%, 73%, 7%, $29.95 | 13, +26.4%, 85%, 8%, $33.02 | same 15 |
| sep23day (8.8 h) | 10, +23.7%, 80%, 0%, $75.60 | 8, +32.2%, 100%, 0%, $84.55 | 7, +29.2%, 71%, 0%, $66.49 |

- The cap improves or leaves unchanged every fit window, at h11 and at h15, on both populations.
- The lower caps (1.0-2.0) lose money on the fit because the 1.5-3 ETH fires pay: +105.9%, +56.3%, +22.1%, +14.9%, +13.3%. On sep2223, cap 1.0 turns the engine's h11 window from +21.3% to +6.3%.

## 4. Choose on one period, read on the other

`python3 data/derived/edge_check/I/choose.py` → `choose.txt`.

**Criterion, fixed before looking:** the highest $ a day on the choosing set. A tie within $0.05 goes to the candidate that removes fewer fires, then to the looser one. The candidates are no filter plus the nine filters.

| population, exit | chosen on the fit | read on the recent | chosen on the recent | read on the fit |
|---|---|---|---|---|
| engine, h11 (rec) | **cap 3.0** (+$3.04/day) | +$0.00 (13 fires, +22.2%, unchanged) | none (cap 3.0 ties it) | +$0.00 |
| engine, h15 (rec+late) | **cap 3.0** (+$3.04) | **+$1.03** (+13.6% → +16.8%) | **cap 3.0** (+$1.03; tmpl+cap +$1.04 ties, removes 7 not 2) | **+$3.04** |
| tables, h11 (rec) | **cap 3.0** (+$3.04) | **+$0.63** (+15.7% → +17.2%) | **cap 3.0** (+$0.63) | **+$3.04** |
| tables, h15 (rec+late) | **cap 3.0** (+$3.04) | **+$1.58** (+10.0% → +12.7%) | tmpl+cap 3.0 (+$1.94) | **−$0.64** |

- **24.34's six pass criteria.** These are: beat no filter's $ a day on the fit, stay positive on every fit window, match or beat on the recent set, keep win and dead within 10 and 5 points, and fire at least 30 times on the fit. cap 3.0 passes all six in every row.
- At engine h15 only, tmpl+cap 3.0 also passes. It is worth $1.34 a day less than cap 3.0 on the fit, because the template part removes profitable fires.
- The template filter alone passes in no row.
- The one reverse choice that fails on the fit (tables h15, tmpl+cap 3.0) does so through its template part.

## 5. Why the cap works, and how solid it is

`python3 data/derived/edge_check/I/cap_robust.py` → `cap_robust.txt`; `python3 data/derived/edge_check/I/bundle_view.py` → `bundle_view.txt`.

- **What it removes.** Every fire above 3 ETH has a bundle of 4.137-4.304 ETH.
  - Fit: 7 fires, Sep 21 01:32 to Sep 23 19:52.
  - Recent: 0xee486806 on Sep 26 16:05 (tables only), plus tonight's 0xa6929b03 and 0x96803325.
  - All 10 sit exactly at the fee floor, (1 − tier − 6.18%)(1 − tier) − 1, at h11, h15 and h300: −10.0% at tier 2% and −11.9% at 3%. **Nobody trades after the seat.**
  - Over all launches, fires and refused: 21 of 21 above 3 ETH return −8.6% or worse at h15, and 17 of 21 are exactly flat from h15 to h300.
  - For comparison, launches of 2-3 ETH are flat at h15 in 5% of cases, and the fit's five 2-3 ETH fires average +40.1% at h11 (`price.txt`, removed-fires column of cap 2.0 vs cap 3.0).
  - A bundle of four ETH or more leaves no buyers behind the seat.
- **Not tuned.** Every cap from 2.772 to 4.137 ETH keeps the same fit fires, and every cap from 1.899 to 4.233 keeps the same rec+late fires. 3.0 sits inside both ranges.
- **Not one launch.** The fit gain is $12.16 in total, from 7 fires. Leaving any one launch out still leaves +$10.28, or +$2.57 a day.
- **Measurable in time.** On all 8 capped fires that have a tape, the whole bundle is on chain by block k−2 (the gate's own view). It is on chain by block k−5 on only 6 of the 8, and not on the two with k = 4. The engine's check (`sniper_engine.py` line 1826) reads its feed-tracked `bundle_eth` once, before the burst. If it runs before the bundle's last buys, it will see less than the full bundle. Tonight's pair bought through the whole creation second (24.38). The cap does its job only if the engine applies it on the bundle as seen when the gate opens.
- **The guard already takes part of the gain.** Live, the minOut guard refused both of tonight's 4.233 ETH fills: no fill, $0.38 of gas for the two (24.38). Where the guard refuses, the cap saves only the burst's gas: $0.33 a day on the fit, $0.12 on rec+late. The model's +$3.04 and +$1.03 a day are the value where these launches fill, as the fit's five full-bundle-by-k−5 fires would have.

## 6. Null test (24.34's discipline)

`python3 data/derived/edge_check/I/null.py` → `null.txt`.

**Method.** Each filter drops m fires on the fit and m′ on the recent set. A random filter drops the same numbers of fires at random (2,000 draws, seed 11), scored on the kept fires' $ after gas. p is the share of draws that do as well on both periods at once.

| filter (engine) | h11 dropped fit / rec | p_fit | p_rec | **p_both** | h15 (rec+late) dropped | p_fit | p_rec | **p_both** |
|---|---|---|---|---|---|---|---|---|
| cap 1.0 | 22 / 4 | 0.419 | 0.864 | 0.356 | 22 / 6 | 0.393 | 0.755 | 0.293 |
| cap 1.5 | 14 / 2 | 0.071 | 0.712 | 0.048 | 14 / 4 | 0.091 | 0.409 | 0.035 |
| cap 2.0 | 12 / 0 | 0.093 | 1.000 | 0.093 | 12 / 2 | 0.107 | 0.039 | 0.005 |
| **cap 3.0** | 7 / 0 | **0.001** | 1.000 | **0.001** | 7 / 2 | **0.002** | **0.032** | **0.000** |
| template | 4 / 5 | 0.360 | 0.108 | 0.038 | 4 / 5 | 0.417 | 0.172 | 0.077 |
| tmpl+cap 2.0 | 16 / 5 | 0.070 | 0.094 | 0.006 | 16 / 7 | 0.099 | 0.032 | 0.004 |
| tmpl+cap 3.0 | 11 / 5 | 0.001 | 0.103 | 0.000 | 11 / 7 | 0.006 | 0.031 | 0.001 |

- Tables: cap 3.0 gives p_both 0.001 at h11 and 0.000 at h15 on rec+late, with p_fit 0.003-0.009 and p_rec 0.107 (rec, 1 fire dropped) or 0.012 (rec+late).
- **How to read it.** A random drop of fires costs money, because the average fire pays. So a filter can beat random drops and still lose dollars. tmpl+cap 2.0 does exactly that: p_both 0.006, but −$4.63 a day on the fit.
- cap 3.0 is the only filter that beats random drops on both periods and also gains dollars on both.
- With nine filters tried, the Bonferroni bound on cap 3.0's worst p_both (0.004, engine h15 on rec) is 0.04.

## 7. The template filter, and reviewer B's finding

- **The template filter is NOTHING at h11 and h15.** On the engine's fit it drops 4 fires averaging +14.6% at h11, costing $1.57 a day. On rec it drops 5 averaging +8.4%, costing $1.37 a day. At h15 it moves $0.01 a day on the recent set and costs $1.34 on the fit. The template fires are below average but still clearly positive at the short exit.
- **B's split was at h300 and not causal.** Components linked by any shared wallet, sizes counted over both periods, h300. I re-ran it on this population (`templates.txt`, last lines): fit 25/73 in templates at +11.9% against +33.8% outside; rec 10/19 at −9.1% against +16.5% (B: 21/73 at +14.2%, 9/18 at −9.6%).
- The same split at h11 on the engine's fires is +18.5% vs +23.9% (fit) and +9.0% vs +33.6% (rec). Its recent gap is not reproduced by the causal rule. The dumps B found land at E1+269 and E1+279, long after an 11-block exit.

## 8. Limits

- **The late windows have no h11 price** (no tape in the repo, and no RPC was allowed). Their effect on the cap is exact, but their contribution to the h11 levels is missing: 4 engine fires, of which 2 are the capped flat ones.
- The engine's count comes from `fleet_variants.py`'s conservative registration proxy. It gives 0 for 0x4fed869a (Sep 27 17:06), which the live engine counted at 2 (24.38). That fire's bundle is 0.957 ETH, so it does not touch the cap.
- **The cap rests on one fingerprint.** All ten fires it removes carry the ~4.2 ETH bundle and nothing else. The evidence is 7 fit fires plus 3 recent, 21 launches in all. If that operator changes its size, the cap stops mattering; if a different large bundle ever pays, the cap would cost it. Neither has happened in the 759 launches here.
- The gain is small at $13: $1-3 a day on the model, and $0.1-0.3 a day where the guard already refuses the fill.

## Commands

    python3 data/derived/edge_check/I/check_late.py   > data/derived/edge_check/I/check_late.txt    # late launches' h15 price vs curves.json
    python3 data/derived/edge_check/I/bundle_check.py > data/derived/edge_check/I/bundle_check.txt  # bundle_eth: file vs tape recompute; launches and fires by bundle
    python3 data/derived/edge_check/I/templates.py    > data/derived/edge_check/I/templates.txt     # templates, causal flags, the 4.233 ETH launches, B's rule
    python3 data/derived/edge_check/I/price.py        > data/derived/edge_check/I/price.txt         # every filter x population x exit x period, per fit window, hours
    python3 data/derived/edge_check/I/choose.py       > data/derived/edge_check/I/choose.txt        # choose on fit / recent, read on the other, 24.34 criteria
    python3 data/derived/edge_check/I/null.py         > data/derived/edge_check/I/null.txt          # 2,000-draw random-drop null test
    python3 data/derived/edge_check/I/cap_robust.py   > data/derived/edge_check/I/cap_robust.txt    # the cap's plateau, removed fires, leave-one-out, late h11, guard
    python3 data/derived/edge_check/I/bundle_view.py  > data/derived/edge_check/I/bundle_view.txt   # bundle on chain by k-5 / k-2; flatness by bundle size
