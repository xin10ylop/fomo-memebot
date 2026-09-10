# Independent audit of report section 23.6 (September 7–10, ten unseen windows)

Method: everything below is from my own loader and my own constant-product replay
(`audit_sep_opus/rep.py`, `c1.py`–`c8.py`), written against the raw `rh/creates_v2_*.jsonl`,
`rh/v2curve_*.jsonl` and `rh/blocks/blocks*.json`. No repository module is imported and no
repository script was re-run; the repo's cached pickles were not read. Constants as specified:
X0 = 1.68 ETH, Y0 = 1e9, ETH $2,445, $1 of gas per round trip. Rule as specified: bundle ≥ 3
tax-free buys in the creation second totalling ≥ 0.3 ETH, creator's launch buy ≥ 1% of supply,
no second-one outsider, send 0.3 s into second two only if no outsider has bought, 3% of supply
capped by the stake, hold 5 s or +50%, 15% of bankroll with a $25 floor, −50% daily stop.

---

## Claim 1 — the per-window table on the ten new windows. **Confirmed, to the digit.**

| window | rule-passing (report / mine) | kept (report / mine) | mean ROI (report / mine) | tail <−40% | one-at-a-time $300 (report / mine) | from $300 (report / mine) |
|---|---|---|---|---|---|---|
| Sep 7 night | 193 / 193 | 136 / 136 | +9.3% / +9.3% | 11% / 11% | $3,589 / $3,589 | $906 / $906 |
| Sep 7 day | 128 / 128 | 74 / 74 | −0.6% / −0.6% | 7% / 7% | −$92 / −$92 | $321 / $321 |
| Sep 7 evening | 276 / 276 | 200 / 200 | +5.8% / +5.8% | 8% / 8% | $3,614 / $3,614 | $1,426 / $1,426 |
| Sep 8 night | 81 / **82** | 61 / 61 | +12.5% / +12.5% | 8% / 8% | $2,128 / $2,128 | $726 / $726 |
| Sep 8 day | 103 / 103 | 75 / 75 | +3.2% / +3.2% | 5% / 5% | $713 / $713 | $395 / $395 |
| Sep 8 evening | 188 / 188 | 145 / 145 | +5.0% / +5.0% | 11% / 11% | $1,831 / $1,831 | $516 / $516 |
| Sep 9 night | 94 / 94 | 72 / 72 | +6.3% / +6.3% | 3% / 3% | $1,363 / $1,363 | $466 / $466 |
| Sep 9 day | 67 / 67 | 43 / 43 | +7.4% / +7.4% | 5% / 5% | $912 / $912 | $438 / $438 |
| Sep 9 evening | 35 / 35 | 21 / 21 | +1.5% / +1.5% | 10% / 10% | $110 / $110 | $301 / $301 |
| Sep 10 night | 48 / 48 | 28 / 28 | +15.1% / +15.1% | 0% / 0% | $1,178 / $1,178 | $527 / $527 |

Totals: report "855 trades, +6.2%, nine of ten positive, worst −0.6%, tail 7.7%, one-at-a-time
$15.3k, compounding gains $3.0k (median +$200, best +$1,126, worst +$1), stop odds 0.1%".
Mine: **855 kept launches of which 840 executed** (15 minOut refusals), **+6.21%**, **9/10
positive**, worst **−0.6%**, tail **7.6%**, one-at-a-time **$15,346**, compounding gains
**$3,022** (median **+$191**, best **+$1,126**, worst **+$1**), resampled stop odds mean
**0.05%**, max 0.4% (Sep 8 evening). Verdict: **confirmed**; the only discrepancies are one
launch on Sep 8 night and rounding.

Two labelling points that matter to a reader, not to the arithmetic:
* "855 trades" is 855 *kept launches*; 840 were executed. The +6.2% is the mean over the 840,
  while the $ columns carry the 15 refusals at −$0.49 of gas each. Small, but the two columns
  are not over the same set.
* The "from $300" column is an **ending bankroll**, not a gain. Sep 7 day's "$321" is +$21.
  The section text says so ("worst +$1"); the table heading does not.

## Claim 2 — the flow shift. **Confirmed in direction; the second range is overstated.**

Bundled launches, per window (mine):

| | Aug 30 | Aug 31 | Sep 1 | Sep 2 | Sep 3 day | Sep 5 day | Sep 6 | Sep 7 n/d/e | Sep 8 d/e | Sep 9 n/d/e | Sep 10 n |
|---|---|---|---|---|---|---|---|---|---|---|---|
| second-one outsider | 28% | **14%** | 30% | 24% | 38% | 64% | 40% | 36/55/51% | 65/54% | 61/**69**/84% | 75% |
| seat rival <0.3 s among the rest | 11% | 9% | 7% | 8% | 19% | 23% | 54% | 30/42/28% | 27/23% | 23/36/40% | 42% |

* "about 14% (Aug 31) → about 67% (Sep 9)": mine is 14.3% (46/322) and 68.5% (146/213) on
  Sep 9 day, 71% over all three Sep 9 windows. **Confirmed.**
* "8–11% → 30–55%": the fit half is 7–11% (mine), so the lower figure is right. The upper is
  **overstated**: across the ten new windows the seat-rival share is **23–42%**, not 30–55%;
  only Sep 6 (an old window) reaches 54%. Report says "30–55%", true range on the new windows
  is 23–42%. The report's own summary sentence ("a rival in second two within 0.3 s on a third
  of the rest") is the accurate one — mine is 359/1,214 = **29.6%**.

**Is the "outsider" classification sound?** Largely yes, with one soft spot.
* The tier is read from the creator's launch-block buy and is a clean grid: 73% of bundled
  launches sit at exactly 1%, then 3%, 2%, 4%, 2.5%, 1.5%, 5%. Only **49 of ~5,000** bundled
  launches (1.0%) land off a 0.5% grid point, and those are the launches where the inference
  could be wrong: several at 6.0% (above the documented 1–5% range) and singletons at 3.23%,
  2.8%, 2.75%, 2.7%, 2.4%, 1.25%. These are cases where either the creator's own buy was not
  purely tier-taxed or the X0/Y0 fit is off for that curve.
* Robustness of the bands to a mis-specified surcharge model: if the surcharge compounds with
  the tier rather than adding to it, a +6.18% buy shows 0.0581–0.0612 over tier (band is
  0.05–0.075) and a +0.19% buy shows 0.00179–0.00188 (band 0.0012–0.0035). Both survive. **The
  +6.18% band is safe.** The **+0.19% band is not**: it is only 0.23 pp wide, so a tier error
  above ~0.17 pp moves a genuine second-two rival out of the band and the launch is kept as
  "clean". Any launch on the odd-tier list is a candidate for exactly that.
* The one survivorship worry I could rule out: the loader has no `launch_quotes_*.json` for the
  new windows and falls back to "keep the curve only if the creator's buy fits one of 14 tier
  values". I hid the quote file on three days that have one and re-ran both paths: the fallback
  loses 11–14 curves in ~2,500 and **zero rule-passing launches** on Sep 3, Sep 2 and Aug 27.
  The 650–2,700 "tier not in list" drops per window are non-native-quoted curves, correctly
  excluded. **Not a survivorship problem.** Nor is there any mid-replay drop: my loader counted
  zero launches abandoned part-way through their event list.

## Claim 3 — the E1 seat. **Numbers confirmed; the framing is apples-to-oranges and the EV is over-stated.**

| configuration | report | mine (n) |
|---|---|---|
| E1 at the front, hold 7, no take-profit, all bundled | +13.1%, 2,970 launches, $92.8k one-at-a-time, 10/10 | **+13.1%, 2,970, $92,825, 10/10** |
| E1 one block behind (0.1 s), hold 5, take-profit | +3.8% | **+3.8%** (n 2,804) |
| E1 0.3 s behind, hold 5, take-profit | ≈ 0 / −0.1% | **−0.04%** (n 2,622) |

**Confirmed** as arithmetic. Three problems with what is made of it.

1. **The comparison mixes the seat with the exit.** +13.1% is hold 7 with no take-profit — an
   exit engine v4 does not run. At the engine's own exit (hold 5, +50% take-profit) the *same
   front seat* is **+8.7%**, not +13.1%. So the "knife edge" from +13.1% to +3.8% to 0% is
   partly an exit effect. Like for like at hold 5 + TP: **+8.7% → +3.8% → −0.0%.** The headline
   "the seat they moved into pays +13%" (also in runbook 2d) is 4.4 points richer than what the
   engine as configured would collect.
2. **The mean is not the trade.** At the front, hold 7, no TP: mean +13.1%, **median +0.8%**,
   17.4% of trades below −40%. Half the launches are flat or worse and the number is carried by
   a thin right tail. At hold 5 + TP the median is +4.8% and the tail 10.1% — the exit the
   engine runs is the one that makes E1 look like a repeatable trade, and it is the one that
   returns +8.7%, not +13.1%.
3. **What "front" assumes.** The replay finds the first buy whose implied surcharge is in the
   +6.18% band and inserts us immediately before it, applying the creator's buy and the whole
   creation-second bundle ahead of us and nothing else. So it assumes (a) we beat *every*
   outsider in second one, not just the first; (b) all of them still buy at the same gross ETH
   behind us and simply receive fewer tokens (they are dropped only if their shortfall exceeds
   10%, which at this size never binds — see claim 6); (c) no minOut refusal is even evaluated,
   because the code only checks it when `lat > 0`; and (d) our own 3%-of-supply buy does not
   deter anyone.

   **My own EV under a stated landing distribution.** I re-ran the seat indexed by *blocks*
   rather than by the interpolated clock (land in the seat's first block, +1, +2, +3, +5), at
   the engine's exit (hold 5, TP +50%): **+9.9%, +4.0%, +1.4%, −0.4%, −1.0%.** Using the
   report's own inference that the first outsider of second one sits in that second's very first
   block on one third of launches, a sender that lands in the first block is in front on 2/3
   (+8.7%) and in a coin flip on 1/3 (≈ (8.7+4.0)/2 = +6.4%) → **+7.9% conditional on landing in
   the first block**; landing one to three blocks late averages **+1.7%**.

   | landing distribution | EV per attempt |
   |---|---|
   | 85% first block, 14% later block, 1% early (minOut refuses, gas only) | **+7.0%** |
   | 80/13/7 — the early rate section 23.4 says the v4 controller actually equilibrates at | **+6.5%** |
   | 80/13/7 but the minOut does **not** catch the early landing (creation second, 93–98% tax, my replay: **−93.4%**) | **+0.1%** |
   | 50% first block, 50% later (no better than a coin flip on the boundary) | **+4.8%** |

   So my expected value is **+5% to +7% per attempt**, against the report's "+8% to +10%".
   The report's figure is high because it prices the front seat at the hold-7 exit. And the
   whole seat lives or dies on one un-modelled thing: an early landing at the second-0/second-1
   boundary buys at 93–98% tax and loses the stake. The runbook (line 94) does set
   `minOut = tokens × (1 − 25%)`, which would revert such a landing for gas, so the exposure is
   probably covered — but **no table in section 23 models it, and section 23.4 concedes the
   controller sits at 6–8% early landings, not 1%.** That is the single number to verify from
   live receipts before any capital reaches E1, and the report does not say so.

## Claim 4 — "every input to the skip decision is visible before the send". **Essentially confirmed; one input is not measurable to the stated precision (see claim 5).**

I looked for look-ahead in each of the four inputs.
* **Bundle (≥ 3 wallets, ≥ 0.3 ETH)** — read from buys in the creation second whose implied tax
  equals the tier, capped at the first surcharged buy. All pre-send. *But*: the raw curve logs
  are topic-filtered with **no sender address** (`pull_v2_curve.py` stores
  `[block, logIndex, txHash, curve, topic0, data]`), so `bundle_n` counts **tax-free buys, not
  distinct wallets**. One exempt wallet buying three times satisfies "three or more named
  wallets" everywhere in the report and the runbook. Not a leak — the live engine would count
  the same thing — but the rule is misdescribed, and nothing in this dataset can verify the
  wallet count.
* **Creator ≥ 1% of supply** — the creation-block Buy event. Pre-send.
* **No outsider in second one (`out1_n`)** — this is the one place with a real look-ahead
  *shape*: the code counts buys in the +6.18% band **anywhere in the launch's event list, with
  no time bound**. A buy 60 s later whose implied surcharge happened to land in that band would
  retro-actively veto the launch. I measured it: of the 1,756 bundled launches vetoed on the ten
  new windows, **2 (0.1%)** have their first band buy after our 2.3 s send; deciles of the band
  buys are 0.40–1.35 s, 0.1% beyond 3 s. **Immaterial. Confirmed executable.**
* **Seat rival within 0.3 s** — the *event* is pre-send, but the *quantity the gate thresholds*
  (`rival_lag = rival_t − (2 − pos_create)`) is a derived timing that this dataset cannot
  measure to 0.3 s. See claim 5. Not a leak of future information; a leak of precision.

No other leak found: the "creator's first launch of the day" filter looks only backwards, the
tier and reserves come from the creation block, and the take-profit trigger uses the curve price
after each event with our own impact already in the entry price (conservative).

## Claim 5 — interpolated timing. **The report understates this. A conclusion does depend on it.**

Anchor density over each window's own block range (mine):

| window | anchors | median gap | max gap | blocks/s (median, min–max) |
|---|---|---|---|---|
| Aug 31 12-18 | 154 | 62 s | 1,041 s | 9.88 (7.3–13.5) |
| Sep 3 12-18 | 203 | 12 s | 2,051 s | 9.55 (5.0–12.2) |
| **Sep 5 12-18** | **5** | **6,050 s** | 6,054 s | 9.92 |
| **Sep 6 12-18** | **4** | **6,049 s** | 6,049 s | 9.92 |
| Sep 7 / 9 / 10 (new) | 785 | **30 s** | 32 s | 10.000 (8.0–13.7) |

The new windows are indeed much denser, as claimed — but note that **Sep 5 and Sep 6, two of the
seven TEST windows on which the rule was "confirmed", have four or five anchors across six
hours (1.7 h apart)**. Section 23's "median 36 s apart" is not true of them.

Two different errors, and they behave differently:
* **Relative** timing inside a launch is good. Using the tax bands as ground truth (a +6.18% buy
  *must* be in second one, a +0.19% buy in second two), the first band-1 buy falls in its
  feasible (0, 2) s window on **100.0%** of new-window launches and 99.9% of old ones; the first
  band-2 buy falls in (1, 3) s on **99.7%** of both. So the clock is fine for the hold, the exit
  and the entry offset.
* **Absolute phase** is bad, and it is exactly what the gate uses. `rival_lag` must lie in
  [0, 1) by construction. It does not on **35.4% of old-window launches and 43.7% of new-window
  launches** (min −1.47, max +1.73). The whole error is in `pos_create = ts mod 1`, the
  creation's position inside its own second, which linear interpolation over a 30 s bracket at a
  locally 8–13.7 blocks/s rate cannot recover. **The gate's discriminator carries ±0.3–0.5 s of
  error against a 0.3 s threshold.**

There is also an internal inconsistency: the gate decides on "0.3 s past the boundary at
2 − pos", but the replay then always enters at relative t = 2.3 s, i.e. at 0.3 + pos seconds
past the boundary. The report calls the resulting extra buys ahead of us "pessimistic", which is
true of the *entry*, but the *gate* and the *entry* are then keyed to two different clocks.

**Does a conclusion depend on it?** Yes — the trade count and the dollar total, on the ten new
windows (same replay, only the rival test changed):

| rival test | kept | mean ROI | tail | one-at-a-time |
|---|---|---|---|---|
| the report's (`rival_lag < 0.3`, interpolated phase) | 855 | +6.21% | 7.6% | **$15,346** |
| the same made self-consistent with the 2.3 s entry (pos = 0) | 523 | **+8.43%** | 5.8% | $12,416 |
| block-based: rival within 3 blocks of the boundary block | 473 | +8.31% | 5.3% | $11,279 |
| look-ahead upper bound: skip if any rival ever | 473 | +8.31% | 5.3% | $11,279 |
| no rival gate at all | 1,214 | +3.62% | 9.5% | $13,114 |

So the gate is real and worth 2.6–4.8 ROI points over no gate — that part is robust. But the
headline **$15.3k is the top of a $11.3k–$15.3k range** that depends on which reading of a clock
the data cannot resolve, and the **+6.2% per trade is the bottom** of a +6.2%–+8.4% range. Note
also that under a block-based reading the "0.3 s" threshold does no work at all: it becomes
identical to the look-ahead "skip any launch a rival ever takes", because essentially every
rival is within three blocks of the boundary. The sensitivity to the nominal threshold is mild
in the report's own coordinates (0.2 s: +5.95%/$15.7k; 0.5 s: +6.57%/$14.3k), which is itself a
sign that the coordinate is noise-dominated.

## Claim 6 — bugs, double counts, survivorship, look-ahead, optimistic exits

Ranked by size of effect on the 23.6 headline.

1. **The two tuned exit parameters lost money on the windows they were never shown.** Same gate,
   same universe, ten new windows:

   | exit | mean ROI | tail <−40% | one-at-a-time |
   |---|---|---|---|
   | **adopted (hold 5 + take-profit +50%)** | **+6.21%** | **7.6%** | **$15,346** |
   | hold 6 + TP | +6.72% | 9.2% | $16,651 |
   | hold 7 + TP | +7.15% | 10.1% | $17,199 |
   | hold 5, no TP | +6.81% | 8.3% | $16,400 |
   | **hold 7, no TP (the untuned section-22 exit)** | **+8.58%** | 11.5% | **$20,242** |

   Section 23.5 says the hold and the take-profit "hold on the half of the data they were not
   chosen on". On the ten windows that were *genuinely* never seen they cost **2.4 ROI points
   and $4.9k**. They do buy what they were adopted for — the tail falls from 11.5% to 7.6% and
   the stop odds to ~0 — so the choice is defensible as risk control. It is not defensible as
   "the rule held out of sample"; the *gate* held out of sample, the exit tuning did not.

2. **The attrition assumption is a knife edge between 5% and 10%.** "Later buyers revert beyond
   a 10% token shortfall" is a modelling choice, not data. At 10%, 20% or no tolerance at all
   the answer is *identical* (+6.21%, $15,346) — the constraint never binds at 3% of supply.
   At **5%** it binds hard: **+3.00% and $7,328**, less than half. So the headline is insensitive
   to loosening the assumption and halves on tightening it by 5 pp. Rival snipers commonly run
   1–5% slippage. Nothing in the data pins this number, and the report does not report the 5%
   case for the round-15 rule.

3. **Optimism in the exit: checked, and it is genuinely pessimistic.** Selling later than the
   modelled 0.3 s *helps* (+6.93% at 0.6 s, +7.63% at 1.0 s), so the exit-lag assumption is
   conservative, as the report claims. Tightening the minOut refusal from +25% to +10% costs
   almost nothing (+6.20%, 17 more refusals). And I checked the exit tax directly: over 360k
   observed sells the implied sell tax minus tier has a median of 0.0000 to four decimals both
   inside and outside the first 10 s, so the replay's `out × (1 − tier)` is right and there is no
   hidden early-sell penalty. **Confirmed.**

4. **Gas.** $1 per round trip is the whole assumption; at $3 the headline falls to **+5.50% and
   $13,718**. On windows paying 2–3% this is the difference between a trade and no trade, which
   is precisely the report's own reason for withdrawing the $100 start.

5. **Two population definitions differ across windows, which distorts window-to-window
   comparison** (not a bug, an artefact):
   * the "creator's first launch of the day" filter is evaluated against the *whole day's*
     creations while the trade data is a *six-hour* window. It therefore removes almost nothing
     from a 0–6 window and a great deal from an 18–24 window. Sep 9 evening's 35 rule-passing
     launches versus Sep 9 night's 94 is partly this, not only "thin flow".
   * five of the sixteen windows have a `launch_quotes` file and are filtered on the true quote
     token; the other eleven fall back to the 14-value tier list. I verified this costs zero
     rule-passing launches, so it is harmless here — but the class table in 23.6 puts Sep 3 day
     (quote-filtered) next to Sep 7–9 (fallback) as if the universes were built the same way.

6. **Small accounting items.** 15 of the 855 kept launches are minOut refusals; they are excluded
   from the ROI mean and included in the dollar columns. The "one at a time, $300" column assumes
   $300 is always available, which a $300 bankroll cannot do — the same windows compound to
   +$3.0k, a fifth of $15.3k; both numbers are in the report but $15.3k is the one in the summary
   sentence. No double count found: each launch enters once, the seat index and the entry index
   are separate variables, and the held/phantom bookkeeping conserves tokens.

---

## Ranked weakest points of the whole case

1. **E1 is priced at an exit the engine does not run.** "+13% a trade on the seat the bots moved
   into" is hold 7 with no take-profit; at hold 5 + TP the same front seat is +8.7%, its median
   trade is +4.8%, and my landing-mix EV is **+5% to +7% per attempt**, not the report's
   +8–10%. And the one catastrophic branch — landing back in the creation second at 93–98% tax,
   which my replay prices at **−93%** — is nowhere in the tables, while section 23.4 concedes the
   margin controller equilibrates at 6–8% early landings. It is covered *if* the runbook's
   `minOut = tokens × 0.75` behaves as described. That is an untested single point of failure
   sitting under the report's most attractive number.
2. **The gate's threshold is not measurable in this data.** `rival_lag` is provably outside its
   feasible range on 35–44% of launches. The "0.3 s" is nominal; resolving the clock differently
   moves the ten-window result between **+6.2%/$15.3k and +8.4%/$12.4k** and, under a block-based
   reading, collapses the executable gate into the look-ahead one. The gate's *existence* is
   robust (it beats no gate by 2.6–4.8 points on every reading); its *calibration* is not.
3. **The tuned exit failed the only genuinely unseen data.** Hold 7 with no take-profit beats the
   adopted hold 5 + TP by 2.4 points and $4.9k on Sep 7–10. The section's claim that these choices
   "hold on the half of the data they were not chosen on" is now contradicted by the newer half.
4. **The result halves if later buyers use 5% slippage instead of 10%.** +6.2% → +3.0%,
   $15.3k → $7.3k. An unpinned modelling constant with more leverage on the answer than anything
   the section actually tuned.
5. **"Three or more named wallets" is three or more tax-free buys.** No sender address exists in
   this dataset. A single exempt wallet splitting a buy satisfies the filter, and both the
   backtest and the live engine would be fooled the same way — so the backtest is self-consistent,
   but the rule is not what the report and runbook say it is, and its economic story (a *team* of
   named wallets) is unverified.
6. **Everything rests on one launchpad, one chain, twenty six-hour windows over 29 days, and a
   regime that is visibly deteriorating inside the sample** — second-one outsiders went 14% → 84%
   between Aug 31 and Sep 9 evening, and the last window in the data (Sep 10 night) keeps 28
   launches. Extrapolating "+6% per trade" forward assumes the deterioration stops where the data
   stops; nothing in the data suggests it does.
7. **The +6.18% band is safe; the +0.19% band is 0.23 pp wide.** A tier error above ~0.17 pp
   silently converts a real second-two rival into a clean launch. 1% of bundled launches have a
   tier off the expected grid (including 6%, above the documented 1–5% range) and are exactly the
   candidates for that failure.
8. **The one-at-a-time headline is unreachable from the stated bankroll.** $15.3k needs a
   permanent $300 per trade; the same windows compound to $3.0k from $300, and the report's own
   "median about +$200 per window" is the number an operator would live on.
9. **Two of the seven TEST windows (Sep 5, Sep 6) have four or five block anchors in six hours**,
   1.7 h apart. Section 23's "median 36 s apart" does not describe them; the confirmation half is
   timed worse than either the fit half or the new windows.

## What I could not test

* Anything requiring a sender address: distinct bundle wallets, whether the same bots recur,
  whether a rival would adapt to a wallet that stands down, and whether "named/exempt" is really
  a creator-declared list rather than a fee-tier artefact.
* The live landing distribution — the entire E1 case, and the "0.3 s into second two" send for
  E2, rest on where a box in Ohio actually lands. Nothing in these files measures it, and my EV
  above is only as good as its stated distribution.
* Whether the minOut as configured really reverts an early landing (the claim that makes the
  93–98% branch survivable), and whether a revert really costs only ~half a round trip of gas.
* The tax schedule itself (93–98% / +6.18% / +0.19%) and X0 = 1.68, Y0 = 1e9: I took them as
  given. They are strongly corroborated internally — implied taxes cluster tightly on the bands,
  sells reprice to the tier at four decimals, and the curve predicts every later event — but they
  are inferred, not read from the contract.
* Price impact at real size: every table replays a 3%-of-supply buy into an order book that is
  assumed not to react beyond the 10% shortfall drop. Two operators running this rule at once, or
  one at 10× the size, is outside what the replay can say.
* ETH at $2,445 and the $1 gas: both flat constants across 29 days.
* Any claim about engine v4's code paths, latency, the feed, or the boundary estimator
  (sections 23.4 and the runbook's machine sections) — outside this brief and not re-run.
