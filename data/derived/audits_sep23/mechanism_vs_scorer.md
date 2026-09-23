# Live E1 mechanism vs e1_multi.score(): independent audit (Sep 23)

Scripts and raw outputs were produced outside the repo; the findings are transcribed here. The auditor's copy of score()
reproduced all 141 launches of data/derived/e1_sep1819 exactly at $10 and $250.

## Summary: the curve model is exact; the gap is regime plus mechanism

On all 23 fills of Sep 19 10:44-20:44 UTC the curve model reproduces the live return to within 0.01%. From the claim to live:

| step | mean | change |
|---|---|---|
| claim: E1 first, h15, $250, Sep 18 13:27 - Sep 19 13:10, 141 launches | +9.27% | |
| same launches at $10-15, our own trades removed from the rows | +8.67% | -0.6 |
| same scorer and filters on the live window, Sep 19 10:43-20:45, 71 launches | +1.85% (median -9.9%, 30% win) | -6.8 (regime) |
| the scorer's front seat on the 23 launches that filled | +3.31% | +1.5 |
| at our real position in the E1 block | -0.27% | -3.58 (position) |
| at our real sell block (= live before gas) | -1.21% | -0.94 (exit) |
| gas | -3.47% | -2.26 (gas) |
| including the burst that did not fill | -3.63% (-$12.17 on 0.1306 ETH staked) | -0.16 |

Live minus the scorer on the same launches: -4.52 pts (standard error 1.63, t = -2.8), plus 2.3 pts of gas.

## Findings
1. Regime: the evening of Sep 19 read 16h -2%, 17h +5%, 18h +1%, 19h +1%, 20h +1%; report 24.27's +12-22% evening did not repeat. Selection is neutral (traded +1.15%, untraded +2.16%, SE about 7). 13 of 23 fills sit within 2 pts of the fee floor ((1-tier-0.0618)(1-tier)-1 = -10.0% at 2%, -11.9% at 3%). A serial launcher (six launches 11:39-11:59, 4 named wallets, 0.88 ETH bundles, all -11.8%) passed the creator-repeat gate (sniper_engine.py:1646); the engine bought two.
2. Position: 17 of 23 fills were the first buy; 6 had 1-2 buys ahead and got 5.4-18.1% fewer tokens (-4.8 to -24.2 pts each; -3.58 pts per trade, SE 1.44). Four of the six came from bursts that straddled the boundary well. Nothing in the engine measures buys ahead: burst_landing logs tx_index (all transactions), exact_score(front=True) places our buy ahead of every E1 row (:1022-1023, forced when the burst is on at :1140). exact_score differs from score() in: gas_usd() at 230k gas floored at $0.05 (0.33% of $15 vs 2.26% real), phantom later buys dropped (:1054), exit at t < t_in + HOLD + 0.3 (:1045), TAKE_PROFIT and the engine's gates.
3. Gas: shot before the boundary 88,594; the filling shot 137,693; shot after the fill (AlreadyBought) 27,021; approve 46,260; sell 78,539. Per filled launch about 1.94M gas (12 early shots, the fill, 21 later shots, approve, sell; range 0.86-3.21M) = $0.33 at 0.063-0.070 gwei and ETH $2,570 = 2.20% of $15 (2.26% measured); $0.275 at today's 0.0551 gwei. The unfilled burst (11:39:56, all 35 shots in E1-2 and E1-1) cost $0.51. The engine's gas_cost_usd() (:813) and gas_usd() assume 230k per round trip: 8.4x too low.
4. Exit: HOLD_S=1.3 from the fill (:1892); sells landed +15 (15 times) or +16 (7 times). One at +37 (17:14): a single sell, no revert, off-chain cause. Fills before engine 6.0 held 24-31 blocks. The sell's minOut is 0 (tx_sell encodes abi_word(0), :1257; live calldata confirms); SLIP is not used in the burst path (:1784 uses BURST_SLIP). The sell always goes through, as the scorer assumes; the tail risk is a delayed sell into a dump. The scorer sells after everyone in the exit block (conservative; before them would score +9.06% vs +8.68%).
5. Timing and gates: the first shot leaves at the predicted E1 arrival minus (85+50+80) ms (:732); a launch is skipped if the gates are not done by then (:1680-1686) and the bundle must be visible on the feed (:1615), so the bundle must cross 0.3 ETH by E1-3. 34 of the 141 (24%) cross in E1-2 or E1-1; they score +12.3%, the 107 the engine could fire on +7.52% (-1.15 pts, SE about 5). Live-only gates: creator already launched today (:1646), creator buy caps (:1652-1654), BUNDLE_MAX_ETH (:1713), tier bps (:1716), safety switch (:1726), open position (:1732, :1772), resolve time (:1734), TRADE_HOURS (:1739), demand floor and DEMAND_ARM_N (:1743), relay float and shooters, slot-model confidence (:684-690). The engine fired on 23 of the 71 qualifying launches plus one outside the scorer's set (17:14: at least 14 blocks in second T0+1, dropped by e1_multi's b0+24 rule).
6. Scorer artifacts: the $250 key is +9.3%, $10 +8.76%; our own trades sit in the rows of 23 launches (removing them: +8.67% at $10, +9.18% at $250); e1_agg lists our wallet as the #2 occupant; folding later buys by ETH paid instead of tokens received gives $250 = +7.07%, $10 = +8.58%.
7. Late fills: the relay deadline is T0+1 (:1792), so a fill anywhere in the seat second passes; minOut at 75% of the sized tokens clears a fill behind everyone in E1+1 on 118 of 141 launches (tokens/minOut live: median 1.36, min 1.12). A late fill costs about 15.7 pts against first. Observed 0 of 23. slot_predict (:688) assumes 10 blocks per second; 9-block seconds are the exposure.
8. Creation-second shots cannot fill: 99% total fee; at $15 the tokens are 1.5% of minOut; a partial fill would need BURST_SLIP >= 0.989. Each costs 88,594 gas (about $0.015).
9. Sizing and fees: amount_in = stake_usd / Coinbase spot (300 s refresh); TIER_ASSUMED and the feed-side curve only loosen minOut; on-chain fees match score() exactly (buy fee fields 7.18% + tier-1%, sells ETH out = gross x (1-tier)); ETH_USD=2500 vs 2640 moves the return +0.01 pt; the 3% cap never binds at $15 (0.065-0.17% of supply).
10. Sample size: last 12 hours (36 launches) mean +5.19%, sd 20.8, SE of a 7-trade mean 7.9 pts, P(7-trade mean <= -0.8%) = 0.235; pooled 141 sd 27.4, SE(7) 10.3, 90% range of a 7-trade mean [-5.4%, +27.9%]. A 10-pt gap needs about 45 trades. All 23 fills: -1.21% before gas (SE 3.2), P = 0.024 pooled. The paired test is the decisive one: -4.52 pts (SE 1.63).
