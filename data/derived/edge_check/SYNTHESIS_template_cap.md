**ADD BUNDLE_MAX_ETH = 3.0** (refuse a launch whose creation-second bundle is over 3.0 ETH; the named-wallet template filter is NOTHING PROVEN). Engine fires, exit block 11: fit 56 fires, +23.0%, $37.3/day to 49 fires, +27.8%, $40.3/day; recent 15 fires, +17.9%, $9.4/day to 13 fires, +22.2%, $10.5/day. A random drop of the same number of fires does as well on both periods in 0 of 2,000 draws (exact 2.1e-5).

# Bundle cap and template filter: synthesis of reviewers H and I (Sep 27 2026)

Inputs: `H/REPORT.md`, `I/REPORT.md` and their verifications in `VH/` and `VI/`. The two reviewers worked independently and reached the same verdict, and both verifiers reproduced every number in both reports byte for byte. This synthesis adds no new computation. It reads `VH/v4_operator.txt`, `VI/tmpl_gap.txt` and the 76.23 h column of `H/price.txt`.

## The numbers

Fit is 96 h. Recent is all 196 recent launches: the eleven recent files, A's gapA and gapB, and sep27pm and sep27eve. Recent dollars a day are on the 76.23 h of the scan windows, a figure both reviewers computed. At block 11, two untaped Sep 27 engine fires have no price and are left out; no filter touches them. Returns are for second place at $13 a burst after $0.33 of gas. Each cell gives fires, mean and $/day.

| population, exit | fit, none | fit, cap 3.0 | recent, none | recent, cap 3.0 | $/day gained, fit / recent | random drop as good on both |
|---|---|---|---|---|---|---|
| engine, h11 (live exit) | 56, +23.0%, $37.3 | 49, +27.8%, $40.3 | 15, +17.9%, $9.4 | 13, +22.2%, $10.5 | +3.0 / +1.0 | 0 of 2,000 (exact 2.1e-5) |
| engine, h15 | 56, +18.6%, $29.3 | 49, +22.8%, $32.3 | 17, +13.6%, $7.7 | 15, +16.8%, $8.7 | +3.0 / +1.0 | 1 of 2,000 (exact 1.0e-4) |
| tables, h11 | 73, +19.5%, $40.2 | 66, +22.7%, $43.3 | 21, +13.3%, $9.2 | 18, +17.2%, $10.8 | +3.0 / +1.6 | 0 of 2,000 (exact 2.4e-5) |
| tables, h15 | 73, +16.2%, $32.5 | 66, +19.1%, $35.5 | 25, +10.0%, $7.6 | 22, +12.7%, $9.2 | +3.0 / +1.6 | 0 of 2,000 (exact 5.3e-5) |

| engine, h11 | fit | recent | removed fires' mean, fit / recent | random drop as good on both |
|---|---|---|---|---|
| none | 56, +23.0%, win 73%, $37.3 | 15, +17.9%, win 67%, $9.4 | - | - |
| cap 3.0 | 49, +27.8%, win 84%, $40.3 | 13, +22.2%, win 77%, $10.5 | -10.8% / -10.0% | 0.0% |
| causal template (3+ shared named wallets, template of 5+ earlier launches) | 52, +23.7%, win 71%, $35.7 | 10, +22.7%, win 80%, $8.2 | +14.6% / +8.4% | 7.5% (exact 7.7%) |

| engine, h11, $/day per fit window | sep1819 | sep2021 | sep2223 | sep23day |
|---|---|---|---|---|
| none | 26.5 | 40.9 | 29.9 | 75.6 |
| cap 3.0 | 26.5 | 44.5 | 33.0 | 84.5 |

Across both periods the cap removes 10 fires and nothing else. They are 7 fit fires (Sep 21-23, the same launches for the engine and the tables), tonight's two engine fires (Sep 27 21:12 `0xa6929b03` and 21:27 `0x96803325`), and one recent tables fire (Sep 26 16:05 `0xee486806`). All 10 carry the serial operator's 4.137-4.304 ETH bundle (4.20-4.33 ETH with the creator's buy). All 10 sit at the fee floor from the seat through block 300, because nobody buys after them. The setting already exists in `src/strategy/sniper_engine.py` (defined at line 83, checked at line 1826) and is 0 (off) today.

## Where they agree

Both reviewers built the same population. The fit is 563 launches with 56 engine and 73 tables fires. The recent set is 196 launches with 17 engine and 25 tables fires. Both priced these from G's curves, recomputed bundle_eth from the tapes with e1_multi's rule (exact on all 735 taped launches) and tested the same ten variants.

Both choose cap 3.0 on the fit alone for every population at both exits, and every time it raises the recent set's dollars. Neither tuned the level. No fire lies between 2.77 and 4.14 ETH, so every cap in that gap selects the same fires. Caps of 2.0 or below drop the fit's five paying 2-3 ETH fires (+40.1% at h11) and lose fit dollars. Every launch above 3.0 ETH is negative (21 of 21, h15 at -8.6% or worse), and every launch at 4.0 ETH or more is flat.

Both reject the causal template filter. It drops fires that still pay at the short exit, and it loses dollars on the fit at both exits and on the recent set at h11. Both conclude that a named-wallet filter cannot catch this operator and that its fingerprint is the bundle size. Both also find the live value small, because the minOut guard already refused tonight's two fills, which cost $0.38 of gas.

## Where they differ, and which is right

**The recent set at block 11.** H prices tonight's two capped fires at h11. Both are flat through block 60, so their h11 equals their h15 exactly, and H reports the recent engine set as 15 fires falling to 13. I prices h11 only on the taped windows, where the engine's cap removes nothing: 13 fires at +22.2%, unchanged. I then reports tonight's effect separately as exact, +$1.03/day. The fires and the arithmetic are identical. H's table is the right way to present it, because the removed fires' h11 is known to the cent. I's framing still records a fact worth keeping: at the live exit, the engine's recent evidence for the cap is tonight's two fires and nothing else.

**Recent hours.** H uses 62.65 h, the launches' T0 spans. I uses 66.8 h for the recent windows and 76.2 h with sep27pm and sep27eve added. Both also report 76.23 h. The hours scale both sides of every comparison equally and change none of them. This synthesis uses 76.23 h.

**The operator's wallets.** H says the operator's 17 launches share named wallets only in two same-evening pairs. VH finds 22 launches at H's own sizes and 6 overlapping pairs, each reusing the full wallet set:
- Sep 22 00:36 and 00:55 share 20 of 20.
- Sep 25 20:05, Sep 26 01:25 and Sep 26 16:05 form a cluster sharing 20-22 wallets.
- Sep 26 23:20 and Sep 27 18:42 share 11 of 11, 19 h apart.
- Tonight's 21:12 and 21:27 share 15 of 15.

I's narrower claim is true: the seven launches at exactly 4.233 ETH share no wallet except tonight's pair. But it leaves out the near-copies, which do reuse wallets. The correct statement is that the operator reuses a full wallet set only within clusters of two or three launches inside about 20 hours, never five, so no 5-launch template ever forms. 8 of the 10 capped fires had no earlier launch sharing 3 or more named wallets, and the causal filter flags none of the 10. Both reviewers' conclusion stands. Both descriptions need this correction before they go into the docs.

**Why reviewer B's template signal does not become a filter.** I says B's recent gap came from the 300-block exit and the non-causal linkage, and that the causal rule does not reproduce it. VI shows this is wrong: the causal flags reproduce the gap.

| slice | flagged | not flagged | B's figures (flagged / not) |
|---|---|---|---|
| engine, recent, h11 | +8.4% (5 fires) | +30.8% (8 fires) | not given |
| tables, recent, h300 | -9.6% | +14.4% | -9.1% / +16.5% |

H's explanation is the right one. The flagged fires are worse than the rest, but they still clear the $0.33 of gas at the short exit: +14.6% on the fit and +8.4% recent at h11. On the fit the difference covers only 4 fires. Dropping them therefore raises the recent mean and lowers the dollars on both periods. The template signal is real, but used as a filter it costs money.

**Smaller errors.**
- I says cap 3.0 is the only filter that beats random drops and gains on both periods. At engine h15, template + cap 3.0 does too (null 0.001). It is still $1.34/day worse than the cap alone on the fit, so the choice does not change.
- H says the full bundle is visible by block k-2 on every taped launch above 3.0 ETH. That is false for 4 launches with k of 1 or 2, which cannot fire anyway. For k of 3 or more it holds: on the k-2 view, both e1_multi's rule and the engine's own fold_buy rule drop exactly the same fires.
- `0xee486806` sits at -11.0%, the floor for the 2.5% tier, not at -10.0% or -11.9%.

## What survived refutation

H is refuted only on the operator-wallet description above; I is not refuted at all. Everything the verdict rests on reproduced:
- Both reviewers' scripts reran byte-identical, and VI's independent recompute matches to the cent.
- The populations match `src/analysis/fleet_variants.py` and its committed output.
- The tape bundle equals the launches files to 0.0000 ETH.
- A brute-force causal rebuild of the template flags disagrees on 0 of 759 launches, and all 9 linkage variants VI tried lose fit dollars.
- The null test drops the same number of fires per period and scores both periods jointly, and the exact enumeration agrees with the Monte Carlo.
- On the gate's k-2 view, and under the engine's own closed-bundle rule, the cap drops exactly the same fires. Under the engine rule the largest fire below 3.0 ETH is 2.826 ETH and the smallest above is 4.197 ETH.
- Leaving any one launch out still gains $2.57/day on the fit.
- The independent hold_grid pipeline puts the 7 dropped fit fires at -10.0% and -11.9%, with h15 equal to h30.

The evidence that carries the most weight is the fit: a random drop of 7 fires matches the cap's fit mean in 0.056% of cases. The recent period agrees, but tonight's two engine fires are the launches that raised the question (24.38), so they are not independent evidence. The independent recent evidence is `0xee486806` plus the 8 of 8 recent launches above 3 ETH that sit at the fee floor, against 5% flat among launches of 2-3 ETH.

## What it is worth

| | fit | recent |
|---|---|---|
| modelled, every capped launch fills in second place | +$3.0/day | +$1.0/day |
| live, where the minOut guard already refuses the fill (tonight's two) | +$0.33/day (gas only) | +$0.12/day (gas only) |

The cap removes no fire that pays in either period, so turning it on costs nothing. Its live value is the burst gas it saves, plus protection against a -10% to -12% fill on a template launch where the guard does not trip. It stops mattering if the operator changes its bundle size.

## Next step

Set `BUNDLE_MAX_ETH=3.0`. Then confirm that the engine sees the whole bundle when it applies the gate. The engine checks the cap once, before the burst (`sniper_engine.py` line 1826), against its feed-tracked `bundle_eth`. 24.38 records that on tonight's two launches the template kept buying through the whole creation second, and that the price at the seat was far above the price at the build. So the engine's view at the build did not yet hold the whole bundle, and neither launch has a tape that shows how much it did hold.

Read the `bundle_eth` in the engine's logged decision for Sep 27 18:21 `0x86d1ab77`, 21:12 `0xa6929b03` and 21:27 `0x96803325`. The live log is not in the repo. If the value is 3.0 or more on all three, the cap works as set. If it is below 3.0, the check has to be repeated on the bundle as seen at the last moment before the shots leave. Until then the cap does nothing live on this template.
