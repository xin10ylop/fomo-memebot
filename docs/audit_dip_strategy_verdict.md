# Audit conclusion: "Buy sharp dips in liquid, socially-active memecoins"

**Verdict in one line: refuted as stated. The headline numbers are an artifact of a hindsight liquidity filter, a survivor-selected token universe, two bogus candles, and a cost model that understates impact 4-6x. What survives is a generic, latency-critical 15-minute overreaction bounce worth roughly +1% to +3% mean per trade on a ~$500 clip, with a confidence interval that includes zero once you remove the lookahead. That is not a retail-executable edge.**

All five auditors independently refuted the claim (1 fatal, 4 material). Their findings agree on mechanism and largely on magnitude.

---

## 1. Findings by severity

### Fatal (each alone invalidates the claim as stated)

| # | Finding | Evidence | Effect |
|---|---|---|---|
| F1 | **`liq >= $100k` is current (Sep-4) liquidity, not event-time liquidity.** It is a survivorship filter applied to July-August events: it keeps only tokens whose pools were still deep a month later. | `gt_common.py` fills `liq` from GeckoTerminal `reserve_in_usd` at fetch time; no history. Same events, same act24/prior1h filters, split by current liq: liq-now >= $100k (the 65 "core") 1h net +4.8%/62% positive; liq-now $10k-100k (n=33-34) 1h net **-11.3%/29%**; pooled RH by bucket: >= $100k +4.0%, $10k-100k -5.4%, < $10k -60%. Event-time activity of the two groups was comparable. | Replacing with event-time proxy (prior-24h volume >= $100k-250k): 1h median 0.0% to +2.4% (51-56% positive), token-median 1h negative, TP/SL mean +2.0% to +3.4%. The 1h/4h edge collapses. |
| F2 | **Token universe and wallet set are hindsight-selected.** Leaderboards pulled Sep 2026 rank by realized PnL through Sep; OHLCV was pulled only for the ~10% of socially-active tokens most traded by those eventual winners. | 1,930 tokens had >= 2 leaderboard wallets fill in a 24h window; 188 have candles. Tokens with candles: median current liq $133k; without: $8k. 852 uncovered tokens are unknown to GeckoTerminal (dead). Hindsight-free universe (fomoscope boards Aug 27-29, tested Aug 30-Sep 4, Solana, n=76): 1h net **-8.7%**, 4h -9.6%, 24h -18.3%, TP/SL mean -5.7%, worse than the random baseline on the same tokens. RH hindsight-free sample (n=5, too small) also negative. | Sign of the edge flips on an unselected universe. Cannot be corrected from existing files; needs point-in-time universes. |

### Material (each moves the estimate by >= 1-3 pp or invalidates a quoted statistic)

| # | Finding | Evidence | Effect |
|---|---|---|---|
| M1 | **Two of the 64 RH events are candle artifacts, and they are the two largest winners.** SPACEHOOD 08-27 16:30 and 20:30: candle -39%/-30% on $2.4k volume in a $1.96M pool (physically impossible); exact v4 swaps moved -0.6%/+3.2%. Candle 1h +52%/+69%; swap 1h -5%/+15%. Cause: GT candle pool is SPCX/SPACEHOOD with `base=False`, prints bimodally. | `audit_swaps_15m.py` | Removes the top two wins; 62 remaining crashes are real (swap-confirmed). |
| M2 | **Impact term understated 4-6x.** GT reserve-USD overstates effective depth of concentrated v3/v4 pools. Measured $ per 1% move: worth $231, FIRE $139, LIGER $150, YOLO $241, TENDIES $605, AI $1,376 vs model-implied $800-$940+. Median model/empirical depth ratio 5.9. | `impact_check.py`, `exec_audit.py` (28 swap-verified events) | With measured impact: 1h net median +1.6% (55%), 4h +0.1% (50%), Aug+ 1h -5.0% (48%). worth (n=13) and LIGER (n=7) 1h net -11%/-17%. Strategy is capacity-limited to ~$500/event. |
| M3 | **Fees are 3% round trip, not 2%.** fomo app 0.5%/side + pool fee 1% (Pons V1 pools: 9 of 15 tokens), 0.3-0.35% (FIRE, CASHCAT, PONS), 0.7% dynamic via LONG hook (AI, SPACEHOOD). AI/SPACEHOOD are quoted in tokenized stocks (NVDA, SPCX): extra hop each way. Pons V2 hook has 100 bps hook fee + up to 10% creator tax; none of the 15 tokens is V2 but any future universe would hit it. | On-chain `fee()`, decoded v4 Swap `fee` field, `readpons.py` | +1 pp round trip for 9 tokens, +1-1.5 pp for AI/SPACEHOOD (9 events). |
| M4 | **TP/SL "median +11.8%" is mechanically uninformative and reproduces under random entries.** Any rule that hits +15% more than 50% of the time has median ~ +15% - cost. Permutation null 95th pct of median = +11.7% vs observed +11.8%. Only the mean carries information (+6.4% vs null [-5.2%, +2.7%], p<0.001 on claim set) and it depends on wick fills: 22/49 TP hits (45%) closed below +15%. Stops are not level-filled on-chain: FIRE 07-20 triggered -30.4%, next swap -40.3%. | `audit_grid.py`, `audit_null2.py`, `exec_audit.json` | Drop the median figure. Realistic TP/SL mean after fixes: +1% to +4%, tail loss per stop -33% to -40%. |
| M5 | **Missing 4h/24h exits silently dropped.** 10/65 24h returns missing in the core set (15%); 62/293 in the refreshed set (26 right-censored, 36 candle gaps = no trades for >= 15 min after a crash). | Claim 24h +24.6% (n=55). Missing = -100%: median +6.1% (65-set), -2.0% (299-set), -3.3% to -10.3% in other treatments. Next-available fill: +14% to +23%. | 24h median lies between -2% and +14% depending on treatment; +22.8% is not defensible. |
| M6 | **Statistics do not survive clustering or multiple testing.** 65 events = 43 independent 24h clusters, 15 tokens, 2 tokens = 23 events; token-clustered 95% CI of net 1h median [-0.2%, +10.8%], 4h [-1.4%, +15.0%]; token-level sign test 10/15 (p=0.15). Core combo is one cell of a ~360-cell grid (208/246 cells positive; best-of-grid 24h +66%); 48 `rep()` subset reports plus 1m variant and two extra universes. Claim mean does not beat max-of-grid null at any close-exit horizon. Headline "1h median +6.5%" does not reproduce from the saved file (it is +4.8%). | `audit_stats.py`, `audit_grid.py` | 4h and 24h claims are consistent with grid selection on right-skewed tokens. Only the 15m-1h reversal is robust to grid selection, and that one is execution-fragile (see M7). |
| M7 | **The edge is generic symmetric overreaction, not a social-activity effect, and it is realised in the first 15 minutes.** Pumps >= +15% (n=1008) revert -3.3% at 1h; lag-1 autocorrelation of 15m returns is -0.034 across 520k candles; any -15% candle with no filters bounces +2.1% next 15m (n=3134), monotone dose-response. act24<2 events bounce equally (1h +3.7%). 15m return = 76% of the 1h median; entering one candle late gives net -2.2% (40% positive); in exact swaps, net at +60s is -2.2%, at +300s 54% of events are already >1% higher, at +900s +7.4% is gone. fomo app has no price-drop alerts; a human cannot act inside a candle. | `audit_mech.py`, `exec_audit.json`, `fapi/ws_alerts.jsonl` | Raw 15-min reversal (+2% to +4% median) is the same order as the true 3%+ round-trip cost. Only an automated <= 2 min poller has a shot. |
| M8 | **Out-of-sample is negative where it is honest.** The 15 events after the claim's last timestamp (Sep 3 19:15 - Sep 4 05:30): 1h net -7.3% (33% positive), TP/SL mean -3.6%. Solana liq >= $100k dips (n=24): 1h -0.1%, TP/SL mean +0.1%. The effect is Robinhood-only. The 137-event exact-swap verification: net 30m median +1.8% with token-clustered CI [-3.6%, +7.2%]; breakeven round-trip cost 4.7%; at 4% fees the median is -0.2%. | `audit_oos.py`, `audit_swapci.py`, `crash_swaps.py` | The one thing that looks decent OOS (276 new-token events, 1h +4.2%, TP/SL mean +5.3%) is still filtered on current liquidity, i.e. still F1. |

### Minor (real but not decisive)

- Wick dependence of the TP rule: -1 pp on mean (closes-only sim: mean +6.7% -> +5.4%).
- "1h" exit is actually 75 minutes after entry (close of candle i+5).
- 10/62 real events had < 20 swaps in the crash candle; the single Solana event is unverified.
- Gas: negligible on the sponsored ERC-4337 app path; ~$0.26 round trip direct on-chain normally; intra-hour spikes to $20-60/tx would be -4 to -12% per leg on a $500 clip if hit.
- SL-first vs TP-first ordering within a candle: immaterial (1-4 ambiguous candles, mean +6.5% vs +7.2%).

### Checked and clean (no fix needed)

- GeckoTerminal candle timestamps are candle-start (ts % 900 == 0; last candle 02:00 at 02:06 pull; confirmed against swaps candle-by-candle).
- Entry at next open equals crash close in 98% of events (max diff +0.2%); first swap after t+900 within +0.08%.
- act24 uses fills in [t-24h, t) only; block-time interpolation error median 0.3s, p99 2.1s; excluding the last hour before the crash changes 3/65 events. No fill-timestamp leakage.
- One-event-per-2h rule is index-based and causal.
- 62/64 RH crashes are real trades; swap-implied crash within 0.95 pp of candle crash.

---

## 2. Corrected expectancy after applying every valid fix

Fixes applied: drop SPACEHOOD artifacts (M1); event-time liquidity proxy instead of current liq (F1); per-pool fees 2 x (0.5% + pool fee) + stock hop where relevant (M3); impact = size / measured event-time depth (M2); TP/SL fills at first swap after trigger, not at level (M4); 60s reaction latency (M7); token-clustered CIs (M6). F2 cannot be fixed from the data, so every number below is still an **upper bound** on the true universe.

| Exit rule, $500 clip, automated 60s reaction | Median | Mean | % positive | Tail |
|---|---|---|---|---|
| 1h close (75 min) | +1.5% to +3.4% | +2.6% to +4.5% | 55-61% | worst events -30% to -40% |
| 4h close | 0% to +0.6% | ~0% to +7% (outlier-driven) | 50% | same |
| 24h close | undefined: -2% (missing = -100%) to +14% (next-available fill) | outlier-driven (3 trades supply most of it) | 48-62% | dead tokens not counted |
| TP +15% / SL -30% / 4h | +6.7% to +9.2% (mechanical, ignore) | **+1% to +5%; central ~+3%** | 77-82% hit | stopped trades fill at -33% to -40%, not -30% |

Token-clustered CI on the TP/SL mean without the current-liquidity lookahead: roughly **[0%, +3%]**. Post-claim events (n=15): mean -3.6%. Aug+ subset with measured impact: 1h median -5.0%.

Sensitivity that kills it:

- **Clip size:** $2,000 -> TP/SL median +2.9%, mean -0.4%; $5,000 -> median -7.7%, mean -12%, 36% positive.
- **Reaction time:** 5 min -> $500 mean +3.2%, $2k mean -2.6%; 15 min (manual) -> most of the bounce is gone, net ~ -2%.
- **Activity regime:** depth/3 -> $500 mean +1.5% (Aug+ +0.9%); $2k median -11% to -17%.
- **Universe:** hindsight-free Solana set -> all horizons negative, TP/SL mean -5.7%.
- **Concentration:** only liq >= $500k (n=19, July-heavy) is clearly positive (1h +8%, 79%); worth, LIGER, FIRE, YOLO per-token 1h net are negative under measured impact.

Blunt summary: a $500 automated clip on the same 3-4 surviving tokens made about +3% mean per trade in July-August with a heavy left tail; everything larger, slower, later, or on a universe chosen without hindsight is zero or negative.

---

## 3. Minimum changes to make this live-safe (i.e. not lose money on known defects)

1. **Never filter or cost on `pools_v3.json` `liq`.** Use event-time depth: on-chain pool reserves / V3-V4 `sqrtPrice` and `L` at the signal block, or empirical $ per 1% from the last N swaps. Require depth >= ~$1,000 per 1% move at signal time.
2. **Fix the universe rule up front and freeze it.** Universe = tokens that meet the depth rule at signal time, on Robinhood chain only (Solana shows nothing). Do not use "traded by today's leaderboard" as an input; act24 adds nothing and is hindsight-contaminated.
3. **Reject implausible candles.** Skip any token whose GT pool has `base=False` or a non-WETH/USDG quote (AI, SPACEHOOD class); require |return| <= k x volume/depth and >= 20 swaps in the crash candle; confirm the crash from swap logs before entering.
4. **Cost model:** fees = 2 x (0.5% app + actual pool fee) + any hop, read `creatorTaxBps`/`hookFeeBps` from the Pons V2 hook before touching a V2 token; impact = clip / measured depth, both legs. Skip if projected round trip > 4%.
5. **Size:** cap at $500 per event (<= 2% of measured depth), no averaging down.
6. **Execution:** automated poller only, entry within 120s of the 15m candle close; abort if price already > +2% above crash close at fill time. Manual trading on the fomo app is not viable (no price-drop alerts, 15 min reaction removes the edge).
7. **Exits:** treat TP and SL as market orders at next observable price with impact; model stop fills at -35% not -30%; a gas guard for direct on-chain (skip when baseFee > ~2 gwei on a $500 clip).
8. **Drop the 24h hold and the "median" reporting.** Pre-register one rule (TP15/SL30/4h or 1h close) and score it on the mean and the sum of P&L, with token-clustered CIs.

---

## 4. What paper trading still has to verify (cannot be settled from the backtest)

- **Does the bounce exist on a universe chosen without hindsight?** Run the frozen rule from item 2 forward on every qualifying token, including ones that die. This is the F2 test; the only hindsight-free data so far is negative.
- **Realised fill vs signal:** actual entry price vs crash close at +60/120s, and actual TP/SL fills vs trigger levels (gap size on stops).
- **Realised round-trip cost** per pool (app fee + pool fee + hook/creator tax + impact) versus the 3-4% assumption; breakeven for the swap-verified median is 4.7%.
- **Capacity:** whether a $500 clip itself moves these pools 2-4% one-way as the depth measurements imply, and whether repeated clips degrade.
- **Regime:** July-August activity may have been the peak; measure depth and event frequency weekly. A 3x drop in depth turns the $500 clip to ~+1% mean.
- **Tail control:** frequency and depth of -30%+ stops and dead-token events over >= 60 independent events (one per token per 24h), not 65 overlapping ones.
- **Post-claim drift:** the 15 events after Sep 3 were negative; need >= 100 clustered events before any positive mean is believable at the 95% level.

---

## 5. Overall verdict

**Not a real, retail-executable edge.**

- The claimed numbers (+6.5% 1h, +22.8% 24h, TP/SL +11.8% median) are not reproducible (+4.8% from the saved file), are built on a filter that uses September liquidity to pick July trades, on a universe of the 10% of socially-active tokens that survived, on two fabricated candle winners, and on a cost model that understates impact by 4-6x and fees by 1 pp.
- Once those are corrected the short-horizon (15-75 min) median is 0% to +2% and the token-clustered CIs include zero; the 24h and 4h results are grid-selection noise on right-skewed tokens; the only honest out-of-sample tests (post-claim events, hindsight-free universe, Solana) are flat to negative.
- What is real is a generic AMM overreaction bounce of +2% to +4% in the 15 minutes after any -15% candle, symmetric with pumps and unrelated to leaderboard activity. It is of the same size as the true round-trip cost, is gone within 5-15 minutes, and exceeds costs only for an automated bot trading ~$500 per event on a handful of deep pools during an active regime. That is a capacity-limited scalp worth perhaps a few hundred dollars a week at best, not a retail strategy, and it has not yet been shown to work on any universe selected without hindsight.

Recommendation: do not trade it as described. If pursued at all, rebuild as the automated $500-clip rule in section 3 and treat the forward paper-trading results in section 4 as the first real evidence; the current backtest provides none.