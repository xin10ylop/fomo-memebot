# Brief K: how to get more fills and a better P&L from the E1 sniper (Sep 28, 2026)

You are one of three independent reviewers answering the same question on the same material; a fourth analysis is done by the
assistant; everything is then cross-checked. Work only from the files named here (no network: the RPC is rate-limited and every
number you need is on disk). Write your report to data/derived/edge_check/K<N>/PROPOSALS.md (N given in your prompt), with
scripts you ran saved next to it. Do not modify any file outside your K<N> folder. Under 1,500 words in the report, tables
welcome. Every proposal must carry a number tested on the data, an out-of-sample check (fit on Sep 21-23, read on Sep 24-28,
or the reverse), and the count it rests on. Say plainly when a sample is too small to conclude.

## The strategy as it runs live (engine 6.6, $13 a fire)
Robinhood Chain, Pons V2 launches. The creation transaction lands in block b0 with the team's bundle (named wallets in the
calldata buying inside the creation second, exempt from the 97% creation-second sniper tax that everyone else pays). Blocks
b0..b0+k share the creation's timestamp second; E1 = b0+k+1 is the first block of the next second, where a buy pays the
token's tier (2-3%) plus a 6.18% surcharge. The engine watches the sequencer's feed, and when at least 2 "fleets" (distinct
relay targets plus direct senders, named wallets and the creator excluded) are visible aiming at the curve before the tick,
it fires a burst of 35 shots spread across the second boundary; the first shot past the tick lands in E1. A minOut guard
(BURST_SLIP 7%) reverts the fill if the tokens at landing are 7% under the tokens sized at the build (two blocks earlier),
which happens whenever the buys ahead of us in E1 moved the price 7% or more. The position is sold 9 feed blocks after the
fill; the sell lands 11-13 blocks after the fill. Pre-gate filters: token tier 100-200 bps, creator buy at least 1% of
supply and at most 2 ETH, a creator's first launch of the UTC day, bundle at least 3 named buyers and 0.3-3.0 ETH.

## What the week's replay on the engine's own chain says (report section 24.41; data/derived/live_vs_table/engine_replay_week_sep21_28.txt)
632 qualifying launches Sep 21 09:40 - Sep 28 09:40 UTC. The engine's gate view ranges from block k-2 to block k (floor /
usual / ceiling). At the usual view (k-1 with the registration block): 129 bursts, 61 reverted by the guard, 68 fills, mean
+15.9% per fill at the 11-block exit, median +5.0%, win 57%, $98 for the week at $13 and $84 of it on Sep 21-22; since
Sep 23 under $3 a day; on Sep 26-28 (live days) -$0.45. Filters before the gate: 147 launches for creator supply < 1%, 20
for the bundle cap, 17 creator repeats, 17 bundles under 3 buyers; the crowd gate refuses 301. Fires fell from 35-38 a day
(Sep 21-22) to 6-11 a day (Sep 26-27): the launch supply halved. Holds 9/11/13 give the same result; 15 is worse.

## Questions (answer all; add your own)
1. The guard reverts half the bursts. What would those fills have returned (second place is already priced with the buy ahead
   folded in: G's r2, the grids' behind1)? Is a looser or a smarter guard (by size of the buy ahead, by fleets count) profitable
   out of sample? What is the gas cost of the reverted bursts against the fills gained?
2. The creator-supply filter removes 147 launches. On this week, what do those launches pay at the engine's gate? Same for the
   bundle-count floor, the tier range (100-200 bps), the cap, the creator-repeat gate: which filters earn their keep now?
3. The gate itself: 2 fleets at the engine's view. Test 1, 2, 3 fleets and the three views; test using the count at the tick's
   block (k) since the engine sometimes sees it. Is there a better signal than fleets (e.g. ETH in the seat block ahead, bundle
   size, tier, hour, the crowd's growth rate block to block, fleets in k vs k-1)?
4. Position: second place is the model; the tapes give first (r2 with n_ahead=0 in hold_grid's model_path) and third (G's r3).
   What does the return look like by landing position and by the size of the buy ahead? Does landing behind a big buy pay?
5. Exit: hold 9-13 is flat. Is there an exit rule that beats the fixed hold out of sample (take-profit, stop, a sell when the
   seat-block buyers start selling, a second-block read)? The grids hold tp/stop variants at 600 blocks; test shorter.
6. Size: $13 now; the model has $15 and $100 columns and the 3% supply cap. Where does the return per fire stop scaling, and does
   the answer change by launch size (bundle ETH) or crowd?
7. More fills per day: E2 (the second after the creation's, surcharge 0.19%: e1_multi's res has E2 columns), a second seat on
   the same launch, a smaller burst step, trading the launches the tables exclude (bundle < 0.3 ETH, tier 1%): anything with
   a positive number out of sample?
8. Your single best recommendation, with its expected effect in $ a day at $13 on the Sep 24-28 supply, and what would be needed
   to verify it live (the sequential test's terms: H0 +2.5%, H1 +19%, sd 0.34).

## Data on disk (all under /home/user/fomo-memebot)
- data/derived/live_vs_table/launches_<piece>.json: the qualifying launches per piece (cv, b0, T0, tier, bundle_eth, named,
  creator, same_second_blocks; older pieces sep2021/sep2223/sep23day carry k instead of same_second_blocks and no bundle_eth).
- data/derived/live_vs_table/crowd_raw_<piece>.json.gz: per launch, per block offset 0..k+1, every transaction aimed at the curve
  {fr, to, direct, named_fr, named_data, to_token, sel}; k; named; token; creator. src/analysis/crowd_rules.py: cums(r) gives the
  cumulative (wallets, fleets) per block; at(c, j); view(k, frac).
- data/derived/live_vs_table/hold_grid_week_<piece>.json: per launch, behind1_13_h{9,11,13,15,30,60,150,300,600} and first_13_h*
  (second and first place at $13), the same at $15 and $100, tp50/stop20 variants at 600, tk0 and init_buy_eth (the creator's
  buy), tk_build_13 / tk_seat1_13 / tk_last_13 (the guard's inputs), bundle_eth_chain, tier, k, bE1, creator.
- data/derived/live_vs_table/tape_bundles.json.gz: for the 735 launches of the edge review's tapes, bundle_eth, tk0, init_buy_eth,
  tier and the guard inputs (identical to the grids where both exist).
- data/derived/edge_check/G/curves.json.gz: 735 launches (Sep 18-27), r2[h] and r3[h] = second and third place return at every
  exit block h = 0..1200 at $13, k, f_k2 (fleets at k-2), fire flag, window.
- data/derived/edge_check/B/tapes/*.json and D/tapes/*.json: the raw trade tapes (rows bn/k/eth/tk/who/li/h, ts, tier, b0, T0)
  for the same 735 launches: price the curve at any position and any exit yourself with src/analysis/hold_grid.py's model_path
  (import hold_grid; it imports live_vs_table for fold_buy/fold_sell; no network at import).
- data/derived/live_vs_table/creations_week.json.gz: every creation Sep 21-28 (creator, cv, block, approximate ts).
- src/analysis/engine_replay.py: the engine's decision chain on the chain (read it; run it with --list to get every launch's
  disposition; --view k-2|k-1|k, --reg, --no-cap, --no-repeat, --hold N, --from/--to). src/analysis/week_backtest.py: the
  tables' count by day. src/analysis/predict_window.py: the reading's prediction. src/strategy/sniper_engine.py: the engine
  (fold_buy, note_attack, attack_fleets, the gates around line 1830, the burst build around 1900-1960, BURST_SLIP line 106).
- docs/REPORT.md sections 24.33-24.41 (grep "### 24.3", "### 24.4"): the discovery, the hold sweep, the engine's population,
  the bundle cap, the burned bundle, the week replay. data/derived/edge_check/BRIEF*.md and folders A-I: earlier reviews.
- Pricing conventions: ETH/USD 2570; gas $0.33 a burst; the 3% supply cap; surcharge 6.18% in E1, 0.19% in E2, 97% in the
  creation second; the tier is the token's own tax on top of the 1% protocol fee.
