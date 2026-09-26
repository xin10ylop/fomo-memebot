# The Big Treasure — fomo leaderboard research report

Session: 2026-09-03 20:45 UTC → 2026-09-04 (Robinhood Chain / Solana memecoins as traded on fomo).
Everything below was computed from data collected in this session; scripts are in `src/`, derived data in `data/derived/`, raw pulls in `data/raw/` (large raw files stayed in the session scratch area and are described in `docs/DATA_SOURCES.md`).

## 0. Executive summary

1. **The fomo leaderboards do not rank traders, they rank bags.** `pnlUsd` is mark-to-market on current holdings (24h PnL ÷ modelled holdings move: median ratio 0.97, p25–p75 0.84–1.09 across 90 traders). No price impact, no realized/unrealized split. Median top-100 trader has 78% of their portfolio in one token; the constant-product liquidation haircut on their top holdings is 29% at the median and 60% for the #1 trader.
2. **Realized trading by the "top traders" is mostly negative.** In the last-25 closed trades fomo exposes, the median win rate is 32% and 63% of the 147 traders have a negative realized sum. On-chain (Robinhood Chain ERC-20 transfers, 45,865 real fills after stripping 114k airdrop-spam transfers; Solana via Helius, 238k signatures) the picture is the same: the money is a handful of early, never-sold bags (PONS, AI, CASHCAT, BONER, MARSCOIN), often acquired before the token was tradable on fomo, plus founder/allocation supply (LONG co-founder Natan_benish: $5.2M "PnL" on $12.6K fomo volume).
3. **Following the leaderboard is not an edge.** After a leader's buy (276 precisely matched on-chain fills, exact pool-swap prices), price rises a median +2.7% within 60 s versus 0.0% in placebo windows — real, but the leader's own fill already moved price +3.4% and a $500 follower pays ~2% fees plus impact in ~$30k pools: net −4.6% median. Buying on the app's buy alert 1–3 min later: +2.5% median at 1 h before costs, ~0 after, and ~0 at 4 h. Multi-trader "consensus" entries: no edge. The feed only prints profitable sells (281/281 sells with a realized figure were gains), so the app's social proof is one-sided.
4. **The one candidate that looked like an edge, buying sharp dips in liquid leaderboard-active tokens, did not survive the adversarial audit.** The first-pass numbers (+7.8% median at 1 h, +27.7% at 24 h, 83% hit rate on a take-profit/stop rule) came from a liquidity filter that used September liquidity to select July trades, a token universe made of the survivors that today's winners traded, two candle artifacts that happened to be the two biggest wins, and a cost model that understated price impact 4–6× and fees by a point. Corrected, what remains is a generic 15-minute overreaction bounce of about +2–4% after any −15% candle (symmetric with pumps, unrelated to leaderboard activity), worth roughly +1% to +3% mean per trade for an automated $500 clip with a confidence interval that includes zero; larger clips, slower reaction, or a universe chosen without hindsight are flat to negative. Section 5 keeps the full record, section 8 the audit.
5. **Bottom line: no big, sustainable, retail-executable trading edge was found in the fomo leaderboards in this session, and every positive-looking result was falsified on audit.** The report states this plainly rather than shipping silver as gold. What was learned is still valuable: what the boards measure, who the top names actually are, which mechanisms make the money (early bags, allocations, audiences, creator fees), and a frozen, hindsight-free forward test (section 7) that is the only way to turn the surviving overreaction lead into evidence.
6. **Where the "big edge" actually sits on Robinhood Chain is structural, not a trade**: Pons creators receive 70% of a 1% fee on every trade forever (creators were paid ~$20.9M in 47 days); insiders/whitelisted wallets own the first seconds of every launch; audiences of 100k–500k followers move thin pools 60–140% in seconds. None of these is available to a retail trader with no special access, and the report says so rather than dressing them up as a strategy.
7. **Memecoin fundamentals at entry were checked for every priced entry (docs/TOKEN_METRICS.md, section 3b).** By count, half of the leaders' app positions are opened below $1M FDV; by dollars, 76% of their priced meme capital goes in above $10M FDV and 82% into tokens older than a week. No entry-market-cap, age, launchpad or holder-count bucket has a significantly positive realized (bag-at-zero) return; the only clear result is that late entries above $100M FDV lost money (−29%, CI −49% to −14%), and pump.fun / Solana entries lose on a realized basis (−10% and −21%). Dev involvement is rare: fomoapi's `isDev` flag is false on every tracked holder and marks a dev on 3 tokens' theses (none a leaderboard handle); on-chain, exactly one traded meme was deployed by a leaderboard wallet (SANDIH by LehmanFarters).
8. **Round 2 (the viral "95% lose, buy the revenue protocols" clip) was tested and does not change the verdict.** The 6.16%-profitable figure is DWF Ventures' realized-PnL count over 292k wallets and matches this data. Following leaderboard traders into fresh launches and holding for the runner had a real positive expectancy only in the July launch wave (+326% mean at 24h with dead tokens at −100%, four tokens carrying it); since mid-August it is −41% to −75%, and for big-audience posters it is −55% throughout. The "revenue protocol" trade is PONS: real fee cash flow, but the buyback that reaches holders is about 45% of protocol revenue (not 80%), lumpy, and roughly 7% of gross fees; on actual burns PONS is priced like pump.fun's PUMP (≈13% trailing buyback yield), its price is a same-day function of the fee cycle (correlation 0.32, no lead), the buyback flow is too small to front-run, and the gas subsidy that made the fee cycle ends in early October. Section 10 has the numbers; it is a beta bet on the casino staying open, not an edge.
9. **Round 3 went mechanism by mechanism with the tails, not the medians, and found one thing that survives every trap: a delta-neutral funding carry on the mania tokens' Hyperliquid perps.** CASHCAT's perp has paid positive funding on 100% of hourly prints since July 11, 17.7% of notional in 55 days; long Robinhood spot against a 1.4×-margined short earned +16% on capital net of costs and basis (≈108%/yr), with every two-week window positive and a −15% equity drawdown from basis swings. It is executable inside the fomo app (which carries Hyperliquid perps), capacity is tens of millions, and its source is the long-only leverage demand of the very traders who lose. It is a yield, not a jackpot, it is one to three names, and it lasts as long as the crowd stays long. The other mechanisms were quantified and closed: the audience-pump scalp is +12% gross in the first minute but a $250 clip in a $30k pool nets zero and $500 nets −8%; realized winners and losers pick the same market caps and ages, and the only behavioural difference is exits; cross-pool arbitrage on PONS is already bot-tight (spread p5–p95 ±1%, six 4-minute episodes above 1.5% in a $28M day); new-venue first-days baskets are inconsistent. Section 11. The factory census also fixes the base rate: 658,367 tokens were launched on Robinhood Chain in eight weeks (≈ 28,000 a day now); 0.077% ever had a tracked pool.
10. **Round 4 replayed every launch of one day and tested the community's "filter new coins and scalp" playbook on the whole universe, not on survivors.** All 5.9M Uniswap v4 swaps of Sep 3 and 419k Pons V2 bonding-curve trades (12:00–18:00 UTC) were pulled from the chain and joined to the 46,218 tokens launched that day. Every filter that can be computed at entry time (buys in the first 30–60 s, buy/sell ratio, quote collected, price momentum, post-snipe dip, one-off vs serial creator, creator's initial buy, venue) and every exit (60 s to 30 min, take-profit/stop variants) loses money on both the fitting hours and the holdout hours: −10% to −46% per trade on the Pons V2 curve, −11% to −48% on the 0x7ed5 pad and LONG, win rates 7–37%. The base rates explain why: of 6,108 V2 launches, 3.8% ever double after the 60-second mark, 0.7% ever 5×, 92% end below their first price, and 4.6% graduate; 43% of launches come from creators who launch ten or more a day. Graduation is predictable (a quarter to a half of launches with ≥2 quote units collected and 2:1 buys in five minutes graduate), but buying on that signal is −21% and buying the moment a pool graduates is +2–7% mean with the confidence interval through zero and a −5% to −30% median. Section 12 has the tables. The playbook does not work on this chain; the only measured, positive, retail-executable expectancy in this repository remains the funding carry of section 11.5.
11. **Round 5 priced the seat on the other side of every losing scalp, the creator's, and then audited it against the launchers' own wallets.** In the six-hour Pons V2 window creators as a group took ≈ $562k (fees + the sale of their launch-block buy), ≈ $2M a day at that pace; the counterparties are 185 sniper-bot wallets (one of them bought 953 launches from 254 creators in six hours) and organic buyers, i.e. exactly the trades section 12 shows losing 20–46%. The audit changed the reading for serial launchers: 77–95% of their launches have their own wallets among the first five buyers, and their EOAs net roughly zero for the day, so most of their "sale" is circular and their real income is the fee share on whatever organic volume the fake activity attracts. For one-off creators, whose first buyers are 38% known sniper bots and 62% others, the seat is real: median stake ≈ $100–240, fees + sale ≈ $137 mean and $14 median per launch, 99% of launches non-negative (the curve refunds the stake minus 1% if nobody buys). Across five windows (section 14.2) the seat never goes negative in aggregate but its size is the day's flow: $14 mean / $3 median per launch in Pons V2's second week, $35 / $1 at the fee trough, $137 / $14 at the peak. It is a launch-and-dump seat, measured here as a finding and not built or tuned, and it shrinks to nothing when the bots' flow does. Section 13. Section 13.3 then prices the fee share without the dump, which is the only version that is not a rug: a first launch from a fresh wallet with a dust initial buy earns $4–23 mean and $0–2.7 median per launch; the second to ninth launches from the same wallet in a day earn a quarter of that and the tenth onward about the launch fee or less, because the bots buy first-time creators; and a held stake loses more than its fee earns in every bucket of $25 or more on every day. The no-dump seat is worth a few dollars a day per wallet, not an income.
13. **Round 7 tested the second clip's three strategies ("scalp the viral high", "catch the tokenized-stock memes early", "trench for the 100× with a Twitter tracker").** Buying a token that makes a new 24-hour high on a volume surge above $1M, $3M or $10M FDV and selling +50% higher (or −25%, or after 4–24 h) is negative net of costs on every variant, on both halves of the period, and on a universe of the leaderboard's own survivors that should flatter it: −1.5% to −5% per trade, medians −3% to −6%, no better than random candles of the same tokens; the literal "first $10M cross, sell at $15M" rule is +0.1% mean with a −28% median on 58 tokens. The tokenized-stock story is one token: of 21,598 LONG stock-paired launches in eight weeks, 7.9% have a pair today, 22 are above $1M, 5 above $10M, one above $100M (AI, $270M, launched in the launchpad's first week), none above $500M; a $100 ticket on every launch of a week pays ×11–35 for the first week (95% of it AI), ×1.6–5 for one August week (98% BONER), and loses 50–99% in the other six. The tracker strategy is the follower seat, already measured three ways (sections 4, 10.2, 11.1, 12): positive only in the July wave, zero to negative since. Section 15.
14. **Round 8 priced the one seat no earlier round had: providing liquidity on the mania token's pool, delta-hedged with the perp short (section 16).** On the CASHCAT/WETH 0.3% v3 pool the in-range liquidity read from the swap events is a $13M virtual full-range TVL against a $3.4M pool TVL, so a full-range dollar earns 0.13–0.50% a day in fees depending on the period; an LP rehedged every 15 minutes loses 0.52–1.10% a day to the price path; the funding a short collects adds 0.11–0.22%. Net: −0.75% a day in July, −0.26% in early August, +0.11% in the last fifteen days, before hedge costs and basis risk. The fee income on this chain goes to the launchpads' own locked positions and their hooks; an outside LP is paid less than the volatility costs.
15. **Round 9 left the leaderboard behind and scored the whole app: every fomo wallet that traded in a seven-hour window, then eight weeks of history for the ones that looked consistent, and a random sample as the base rate (section 17).** 11,738 wallets traded through the fomo entry point on Sep 3, 12:00–19:00 UTC; the 5,431 with priced buys spent $5.0M and received $1.6M, net −$3.5M with unsold tokens at zero and +$0.17M with them marked; the best wallet realized $4.5k in the window. The 251 that looked best were followed back to Jul 13: $1.07M realized between them, 89% of it in the week of Aug 31, and negative in five of the six weeks before Aug 24. Four wallets in 251 were positive in all but one of five or more weeks with $5k or more; one was consistent before the mania ($24k over five weeks, then $102k in it). A random sample of 120 app wallets realized a median of $0 over the eight weeks, none above $5k. What the winners do is the same for all of them: days-old, liquid, leaderboard memes, never the first hour, hold hours to days, small clips, many partial exits, with the profit in two or three tokens per wallet. Random timing on the same tokens over the same holds earns what they earned (pooled timing alpha −3.5% median), so the money is being long the right names in the two mania weeks. The one wallet whose behaviour is a rule, buying 20–25% dips in liquid names and turning $1.3M over for $63k, made 117% of its profit in its ten best trades, and its rule fails on a hindsight-free universe (−0.5% to −7.7% on every v4 pool of Sep 3) exactly as section 5's did. Nobody in the sampled population is making $30–100k a month from a repeatable rule.
16. **Round 10 tested the influencer-catalyst scalp exactly as its author describes it (section 18): the second an influential, trustworthy person does something, size in, stop −22%, sell into the crowd at +50% or on a trailing stop.** On the 276 leaderboard fills matched to exact pool swaps, with every swap of the pool for the following half hour, the rule is −1.6% per trade for a $500 clip entering 3 s behind the fill (bot speed), −5.8% at 15 s, −11.0% at 60 s (app speed); for the audience over 100k followers −2.4%, −7.1%, −12.9%; at $2,000 clips −19% to −29%, at $5,000 −55% to −64%, because the median pool is $30k deep. The only cohorts near zero are the deepest pools (+2.9% at $500, −0.3% at $5,000) and the three posters above 300k followers (+6.5% on 16 trades, interval −9% to +25%). Entering ten to thirty minutes *before* the fill, which only the poster can do, returns +11.6%: the strategy is the poster's seat seen from behind. The author's own fomo handle draws 3,124 follower swaps within ten minutes of a fill and sells inside ten minutes two times in three; his scanned Solana wallet shows 53 completed tokens, 36% winners, $137k net over seven months, $125k of it one token. A live shadow on the real-time feed is running.
17. **Round 11 made the sniper executable from a $300 bankroll (section 19, `docs/SNIPER_RUNBOOK.md`, `src/strategy/sniper_engine.py`).** A simulator bug that valued the seven-second exit after the next event was found and fixed; corrected, the first-in-line rule is positive on four of five windows (Aug 20 +4%, Aug 27 +7%, Sep 2 +17%, Sep 3 +35% per trade at $300 stakes, Aug 12 flat) and every window is non-negative with a regime switch that trades only while the mean of the last 30 scored launches is above +5%. Gas is ≈ $1 a round trip, which sets a $50 floor on the stake; returns are flat from $100 to $300 and fall above $500. The creator-stake filter (launch-block buy ≥ 5% of supply) earns +24% and +48% per trade on the two flow days on a quarter of the launches. Compounding from $300 with 20% sizing, one position at a time, switch and a −30% daily stop: $32k–83k on Sep 3, $15.6k on Sep 2 with the filter, $5.5k on Aug 27, $600 on Aug 20, a stop on Aug 12. The engine detects creations from the sequencer feed, filters, sizes, builds the exact unsigned buy/approve/sell transactions and scores every launch for the switch; from this sandbox it resolves a creation in 630–1,150 ms, which its own gate refuses, so the machine must sit near the sequencer. The send step is left to the operator, and the subsidy that makes gas cheap ends in October.
18. **Round 12 audited the sniper with three independent auditors and an exact rebuild of the bonding curve (section 20), and the answer changed.** The curve is constant-product with 1.68 ETH / 1e9 virtual reserves (exact to 1e-15); every token has a creator-set 1–5% fee on both legs; the snipe tax is keyed to whole seconds (93–98% in the creation second, +6.18% the next, +0.19% the one after) and **wallets the creator names in the creation calldata are exempt**: all sampled untaxed first-block buyers are on their launch's list. The first-in-line seat of sections 14 and 19 (+36% a trade on the exact curve on Sep 3) is therefore the launch team's own bundle, not a seat an outsider can take. The first legal outside seat (next second, +6.18%) is −5% to +3% across the five windows and negative 0.3 s behind; filtered to launches whose bundle bought with three or more wallets it earns +5% to +10% a trade on the two peak days from Ohio latency (about $8k in six hours on $300 stakes, in-sample filter), about zero otherwise, and from $50 all-in it reaches $300 one time in three at best. Engine v2 shares the curve, fee, seat, filter, sizing and scoring with the simulator, sells the receipt's balance, and refuses the creation-second seat without the exemption.
19. **Round 13 answered the reader's three questions (section 21): more days, the machine, the chain.** Sep 4 and Sep 5, never looked at before, confirm the bundle filter out of sample (E2 seat 0.3 s behind: +9.6% and +4.2% a trade on bundled launches, $2.7k and $4.3k switched net in six hours; the unfiltered outsider seat stays near zero), with more windows landing in `sniper_oos.txt`. The engine's critical path no longer needs an RPC call: the creator's exempted wallets, listed in the creation calldata, buy the new curve inside the creation second, and matching feed buyers to that list gives the curve address exactly. The machine is a small EC2 in Ohio on the public feed with a provider RPC for bookkeeping, not a full node. The seat exists on Robinhood Chain because ordering is first-come with no priority fee and the tax is per second; on Solana the same slot is bought with Jito tips by sub-50 ms bare-metal bots and was not tested.
20. **Round 14 put the whole thing in front of two independent auditors with one brief (section 22).** They agreed on the essentials: the mechanism is real and the tables reproduce, but the engine only saw about 40% of the buyers whose absence is the rule's main gate, the rule is in-sample, the compounding paths were single orderings, one gas-gate constant had been swallowed by a comment, and the setup had a dozen operational holes. Engine v3 decodes every transaction type and router buys and checks its own feed readings against the chain at score time (they match); state is persisted and an open position is closed on restart; the setup script is hardened; the simulator's universe on the newer windows was corrected (the event's fee field is the protocol fee, not the token's tax). The corrected rule stays positive on all eleven windows (+1.8% to +18.6% per trade), but the planning number is now +5% to +8% per trade on busy windows with a 10–34% chance of a −50% day on flat ones, +$100 to +$800 per busy six hours from $300, and nothing has been sent live.
21. **Round 15 asked two things of four researchers (section 23): lose less, and land where the tables assume.** Both risk researchers found the same fat left tail (one trade in five ends near −70%, no clustering) and the same remedies: hold 5 s instead of 7, a +50% take-profit, 15% sizing with a $25 floor, and, from one of them, a gate that skips launches where a rival is already in the seat. The gate's threshold turned out to be an artefact of the replay's interpolated clock, but the signal under it is real and executable (launches nobody else takes earn +10%/+20%, launches a rival took lose), so the rule now sends 0.3 s into second two only if no outsider has bought. Fit half +10.7% a trade, test half +16.4%, every window above +7.6%, one-at-a-time $22.0k and $37.4k, and a resampled chance of the −50% stop of zero at either sizing; from $100 the stop odds stay under 7%. The speed engineers found a signing landmine (lowercase addresses), a feed loop busy 17% of the time, a curve state rebuilt after the boundary, polling wakes and cold sockets; engine v4 fixes all of it (0.26 ms per frame, 0.5 µs of post-boundary work) and the new rule makes the send a fixed 300 ms after the second opens, which the first live receipts must confirm. Ten more windows (Sep 7–10) that no choice ever touched keep the rule positive (nine of ten, +6.2% a trade, stop odds 0.1%) at a third of the earlier level, because two thirds of bundled launches now carry a bot in second one; the money moved to the first-in-second-one seat (+13% a trade on 2,970 launches, but +4% one block late and zero 0.3 s late), which only live receipts can test. Section 23.7 then measured the nine ways it could die: real gas is $0.10 a round trip (a $100 start is back), the sequencer takes raw transactions from unknown senders, the contracts carry no blacklist, a fee-headroom landmine that would have refused the first live buy is fixed, and alarms for a changed tax schedule, a silent factory and a thinning flow are in the engine.
22. **Why the edge thinned (section 23.11).** The September return, taken apart on the exact curve: fees and the teams' dumps are unchanged; the buyers who come after us bring 28% less ETH per hold, and that alone is the drop in return per trade (+0.88 correlation across twenty-one windows; the competition does not correlate with a kept launch's return). The competition costs trades instead: clean launches fell from 67% to 29% of bundled launches. It depends on the day and the hour: September's US-morning hours pay +3% a trade, its nights +10%, where the earlier windows paid +15% at any hour. Sizing to a live demand gauge, reacting to dumps and changing the exit were tested and rejected; 20% sizing is the most the September windows allow under 1% stop odds; and the seat the crowd moved to, first in second one, pays +8.7% a trade on every bundled launch in September (twelve times the E2 gain, stop odds 1.3%) if the box lands first, loses to E2 on the August windows, and collapses one block late. The engine now prints the demand and the crowding as `follow_eth_last_60` and `out1_share_last_60`.
23. **The first live trade (Sep 18, $10) reverted on its minOut and closed the creation-second seat (section 24.19).** The curve offered 1.1% of the fair tokens: the snipe tax is keyed to the block's clock second, so a buy in any block carrying the creation block's timestamp pays ~98%, whatever the block offset; 24.13 had measured time in block offsets and mistaken next-second buys for creation-second buys. With real timestamps every outsider buy at 6.2% on Sep 18 sat in a later second. The next-second seat scored honestly on the engine's filters pays +8% (today) to +20% (two days ago) a trade if our buy is first in the next second's first block and −4.6% to +5% behind the two or three bots that queue for it; the position is the edge and only real sends can measure it. Engine 5.51 refuses the creation-second seat without the exemption again.
24. **Five days on the true clock (section 24.20).** The next-second seat pays +16.1% a trade first in its block (+3.7% median, 56% win, 148 launches a day, about $5,900 a day at $250), +3.7% behind the block's other buys, and the second-two seat is dead. The value is the crowd: alone in the block −3.2%, ahead of two or more bots +19% to +49%, behind a big crowd still +6.8%; a tight minOut as a position filter destroys that. Engine 5.6 adds the burst send, several shots at consecutive nonces straddling the predicted boundary so the first past the tick fills without a safety margin, tested on the scripted feed; the share of contested blocks it wins is measured by a ten-launch landing test on an Ohio box, and decides whether the seat pays +4%, +10% or +16% a trade.
25. **The burst filled six and five times at $15 and the wallet, not the stake, was the bet (section 24.24).** The 3% guard cannot see a $15 fill's own impact, so every shot after the first also fills until the wallet cannot fund one more; one launch at −56% on the whole wallet cost $42 of the night's $54. Engine 5.93 sizes every buy to the wallet less a gas reserve so the sequencer itself drops a second fill, makes `STAKE_MAX` the wallet's ceiling, and starts the hold clock at the fill (the sells had landed 31–36 blocks after the buy instead of 15). Nine live fills so far, four wins, a mean near +1%: too few to judge the seat's +16% either way.
26. **The BuyOnce relay makes the bet a setting again (section 24.25).** A 20-line contract owned by the wallet buys at most once per curve and forwards the tokens to the wallet; the curve accepts contract buyers (checked by simulation), the relay's logic was exercised on a live curve's state before deployment, and engine 5.94 routes every shot through it. `STAKE_MIN`/`STAKE_MAX` are the bet, the wallet may hold any amount.
27. **Shooters (section 24.26).** One wallet's consecutive nonces on parallel sockets are refused as "nonce too high" when the sequencer is under load (29 of 35 shots on Sep 19); engine 6.0 fires every shot from its own gas-only shooter wallet and the third relay buys with the stake it holds, once per curve, before the seat's deadline. No shot depends on another, and the exit no longer depends on how many landed.
35. **Can the rule be improved? No, not provably (section 24.34).** Three independent searches on one strict protocol (fit on the four backtest windows, validate on the five paper windows, executable views only): 47, 383 and 3,420 variants; the same baseline to the cent; every pass rests on a single launch, random features pass as often as real ones, the k−1 view is the only material gain and the feed cannot show it in time. Keep the rule. One trade-off recorded (a −20% stop: 1% dead, $51 instead of $57 a day).
34. **Is the engine doing what the tables priced? No, in three ways, then audited at the seam (section 24.33).** The tables counted shooter wallets and the token's own approvals; the engine counts fleets and excludes the token. The tables priced a block index; the engine sees time. The safety switch, the trade hours, the demand floor and the gas cap stood in front of the gate unpriced. Every shot aimed at the 563 launches was pulled raw, the engine's own count replayed against the tables' (0 differences, a permanent test), and its rule re-priced: fleets ≥ 2 at the gate's opening pays +19% to +30% a fire, 60-67% wins, 3.4-3.9 standard errors above zero, positive on all four windows on every view from block k−1 to k−3, about $2.2-3.6 a burst at $13. Engine 6.4 measures its view in chain-numbered blocks at every ask of the gate, closes the gate at the actual tick (GATE_CLOSE_MS), and runbook 5o sets every pre-gate filter to the tables' population.
33. **The paper day, and the gate moved into the burst (section 24.32).** Twelve hours of engine 6.1 in dry run: 16 launches reached the gate, all refused (0-1 attackers), all 16 would have lost (−15% at second place). The chain, scored like the windows, says the signal was there: 25 of the day's 58 qualifying launches had 2+ fleets by block 5 and the first seat paid +13% to +37%. The engine counts at the burst's build, about 300 ms before the tick, where the feed shows only block k−5 of the creation second: 3% of launches pass at that view on every window; at the tick's shot (block k−2) 24% pass at the same return. Engine 6.2 decides the gate shot by shot inside the burst (the shots before the tick revert anyway): a shot is sent only once two snipers are visible, a burst whose gate never opens sends nothing and costs nothing. Second place, 300 blocks, at that view: +23.0% / +18.0% / +30.0% on the three windows, 14-29 fires a window, $37-60 a day at $13. The other filters let only 16 of 58 launches reach the gate: the next leak to measure.
32. **Out of sample, and the rule (section 24.31).** On Sep 20 13:26 to Sep 22 01:02 UTC (189 qualifying launches, a window nothing was fitted on) the pre-tick gate separates as before: 0 attackers −1.0% first seat (29% win), 2-3 attackers +30.2% (67%), 4-6 +13.9% (89%). On the 65 gated launches, second place is +11.2% at 15 blocks and +10.9% at 300; across the three windows second place at 300 blocks is +13.7%, +10.9%, +26.9% (at 15 blocks +18.0%, +11.2%, +4.9%), so 300 blocks is the hold whose worst window is still above +10%. Third and fourth place are weaker out of sample (+6.5%, +1.9% at 300), last is negative on every window, and the second-second seat is negative on two of three: the burst stays dense and the guard stays. Engine 6.1 carries the gate (ATTACK_MIN), the hold in blocks (HOLD_BLOCKS), the measured gas model and a kill line (KILL_USD), all off by default; the next step is a paper day on the box, scored by `paper_day.py` from the chain, then $13 stakes with KILL_USD=15 on the $22 the box holds.
31. **What the profitable trades had, and what it points to (section 24.30).** The P&L peaked at +$24 on Sep 18 18:44 UTC and lost $51 in the next five minutes to two multi-fill launches. Every winner had a crowd buying behind us in the 15 blocks after the seat (5.5 wallets, 0.23 ETH, against 2 wallets and 0.05 ETH on the losers); the three big ones were multi-fills (size on winners +$48, size on losers −$72); and the tokens we sold were up 20-30% a minute later. On the population, the current regime pays later than 1.5 s: on the last 30 hours' 175 launches, the first seat held 15 blocks is +1.2% and held 300 blocks +12.6%; with the pre-tick crowd gate (60 launches) and second place, +4.3% at 15 blocks and **+25% at 300 blocks (median +15%, 63% winners, 10% dead, standard error 8)**: +$3.43 a burst at $15 after gas, about $200 a day on paper, in sample. Sep 18-19 did not need the long hold (+17% at 15 blocks, +13% at 300). Out of sample on Sep 20-21 pending; not to be traded before it and a paper day.
30. **Verdict (section 24.29).** Three independent audits and two more chain tests. The seat's ground truth from events: the bots that take index 1 realise about 0% (the one that beats us: +0.08% on 2.97 ETH over 20 seats in the last 30 hours; +2.0% on Sep 18-19 where the tables said +24%). The tables' own model fell from +9.3% (Sep 18-19) to +1.5% (Sep 22-23). Pons changed nothing; Sep 20 was a 1%-tier lull. The crowd is visible before the tick (wallets already firing at the curve by creation-second block 5: 0 of them = −6%, 2 or more = +13% first seat now, +27% then), which removes the leftover launches; landing second on those is +4.9% before gas today (median −3%, 46% win), +18% four days ago. At $100 a stake that is of the order of $80-150 a day expected with swings of the same size, on an edge that halved in four days, with $22 on the box. The seat as built does not meet the brief; the gated version is a capped experiment at best, not a business.
29. **Why live does not pay: the seat we get is not the seat the tables price (section 24.28).** Every real fill of Sep 17-20 re-run through the tables' own model for the same launch: the model reproduces the wallet to the decimal on all 34 single fills, so the engine is right and none of the fixed bugs was the cause. The tables assume we are first on every launch. Live: first only when nobody faster wants the launch (26 of 38 fills, worth −1.5% even when first), behind one bot on the launches that pay (12 fills, +17.7% if first, +7.4% got; 13 more bursts on its launches filled nothing at all). Plus 2.3% gas a burst at $15. As executed: about −2% a trade. The bot straddles the second's tick finer than our 3 ms grid and picks 13% of launches whose first seat is +19% with 92% winners; nothing in the calldata says which. Following it one block later is −10%. Not a code fix.
28. **The seat still pays, less (section 24.27).** The tables' unchanged script on the last 24 hours: 141 qualifying launches, front seat +9.3% mean, 51% winners, +10.5% in the evening half and +5.6% in the small hours; behind the crowd −5.9%. The engine's two readings of −8.5% and −3.9% the same day were its own errors (the wrong column, then a block-offset clock), fixed in 6.05 and 6.06. Live: seven clean trades at −0.8%, in the weak hours, within noise of the script.
12. **Round 6 found the treasure's real owner and measured its seat: the first-block sniper.** The 185 sniper-bot wallets that pay the creators are not all losers. Reconstructing the dollar P&L of the fifteen busiest from their transfers, curve trades and pool swaps: the bots that buy 0.3–3 seconds after launch and sell 3–21 seconds later are net positive (the fastest: +$30.8k on $107k of turnover in six hours, +28.7% per trade, 175 launches, nothing left unsold); every bot that holds minutes or hours loses (−44% to −94%). Simulating that seat on every launch of the window with launch-time filters (creator's first launch of the day, ETH-quoted, stake min(3% of supply, $300), sell 7 s later into whoever bought next, exact curve exits, 1% fees each way) gives +27% on $97k in the fitting hours and +32% on $98k in the holdout hours, per-launch mean +27%/+33% with confidence intervals of +20% to +41%, median −2%, 46–48% of launches positive, worst case one stake. That is $26k and $31k of profit per three hours on a working capital of a few thousand dollars, and it reproduces the fastest real bot's holdout result (+31%). The sensitivity analysis says what it is: paying 10% more than first-in-line still earns +18–23%, paying 25% more earns +6–10%, paying 50% more or landing half a second late loses. It is a latency race for the first block after creation, on a chain with 100 ms blocks, sponsored gas and a first-come sequencer; the winner takes +30% a trade several hundred times a day and everyone behind them pays. Out of sample on Sep 2 (a lower-flow day) the same untouched rule made +0.4% in the first three hours and +15% in the next three. Three further windows across the fee cycle (section 14.2) then showed the seat is a peak-flow phenomenon: −13% in Pons V2's second week (Aug 12), flat at the trough (Aug 20) and on the ramp (Aug 27), positive only on the two peak days. It is not a structural edge. Section 14 has the tables and a live shadow tester that scores every new launch against the rule without capital.

## 1. Data access and what was analysed

* The fomo web app has no public leaderboard route; boards live in the mobile app behind a login (Privy token). fomoapi.io (the `fapi_…` key) mirrors the app live (`source: fomo-live`) and was the source for the four boards (24h/7d/30d/all, top 100 each, 147 unique handles), per-trader open positions plus last 25 closed trades, live holdings, and the realtime app feed via WebSocket (2,380 alerts collected: 1,067 buys, 1,002 sells, 261 theses; 74% Robinhood Chain).
* Real wallets from the boards were followed on-chain: 128 Robinhood Chain EVM wallets (public RPC `rpc.mainnet.chain.robinhood.com`, ERC-20 Transfer logs, block timestamps, token mint blocks) and 117 Solana wallets (Helius enhanced transactions, ~100k credits used of 850k).
* Prices: GeckoTerminal 15-minute candles for 281 traded tokens (base-token pools only; the pull is still running), 1-minute candles for 139 feed tokens, exact Uniswap v3/v4 swap logs for event studies; DexScreener for liquidity.
* fomoscope.xyz (free mirror) turned out stale and bugged (9e19 PnL rows) and was not used beyond a sanity check.
* External research (six parallel researchers, 100+ sourced findings): `docs/research_round1.json`, synthesis in `docs/research_synthesis_round1.md`.

## 2. How the leaderboard PnL is made (audit)

| Check | Result |
|---|---|
| 24h PnL vs Σ holding value × (1 − 1/(1+change24h)) | median ratio 0.97 (n=90); the 24h board is the day's mark-to-market of bags |
| all-time vs 30d PnL | equal for almost everyone; the boards are the Robinhood Chain wave since July 2026 |
| PnL ÷ cumulative fomo volume | median 0.93; 16% of traders ≥3× (impossible from trading; unrealized appreciation on tokens bought early or transferred in) |
| Top holding share of portfolio | median 78% |
| Liquidity haircut (constant-product exit of top-10 holdings) | median 29%; unipcs 60% ($15.8M shown → $6.4M) |
| Last-25 closed trades (fomo's own numbers) | median win rate 32%; 63% of traders negative |
| Feed sells with a realized figure | 281 of 281 positive; losing sells print without a number |

## 3. Trader-by-trader

Full table: `docs/TRADERS.md` (147 rows, rule-based classes from on-chain and fomo data) and `docs/trader_dossiers_agents.json` (deep dives on the top 10 by an analyst pass). Class counts (rule-based): luck/one-bag 68, active churner with negative realized 24, concentrated bag 20, KOL flow-mover 10, insider/allocation 4, skill candidate 4, insufficient priced data 17.

Top of the boards, in one line each:

* **unipcs (#1 everywhere, 466k followers)** — KOL flow-mover. $12.3M PnL is $10.1M unrealized, 64% in PONS bought Jul 14–17 for ~$67k (95× paper, never sold). Realized wherever measurable is negative (last-25 −$209k; Solana −$118k; fomo `otherPnl` −$445k). His Sep 3 VOXEL buy drew 3,804 swaps in 10 minutes and +141% at 15 s: the audience is the edge, and it is not copyable.
* **DumbCrayonEater (#2)** — one bag: 29.3M AI bought 71 minutes after mint for ~$21k, 357× paper, 94% of PnL; his other ~120 tokens lost money (25% token win rate).
* **Salem1299534 (#3)** — swing-traded one early LONG-launched runner (AI) for weeks and actually realized ~$1.6M; non-AI trading shows no edge.
* **Natan_benish (#4)** — LONG launchpad co-founder; half the AI position transferred in from private wallets; $12.6k fomo volume. Insider supply, not a trader.
* **brrrgrrrz (#5)**, **notanicecat69 (#8–9)**, **AvgJoesCrypto (#6)** — the closest thing to process: buy survivors 1–4 weeks after launch at $3–10M FDV in $1–5k clips, scale out into strength in fixed clips, cut losers within a day. notanicecat69's published rules (skip the launch window, one-sentence thesis, 2–3 positions, incremental sells, moon bag) match his on-chain record (0% of buys within 1 h of launch, median launch age 36 days).
* **ogle (#8–10)** — one venture-style bet: 10.6M PONS for ~$5k on day two of the launchpad, never sold (~1,300×). Everything else he bought is a negative signal.
* **change (#8 all-time, 337k followers)** — high-churn scalper (median hold 1 h, ~40% win rate); signature wins coincide with tokens transferred to him; his follower buys do not produce a tradable flow bump.
* **frogmanhaha (#7)** — display wallet: CASHCAT and AI arrived by transfer from another address; nothing verifiable to copy.
* **frankdegods, 0xAvast, ether_monk, PoorGoat_, Aurelius0121** — audience accounts; documented dump/insider episodes in the research file; treat as flow, not signal.
* **Visi235, Quanterty, The__Solstice, bluntz_capital** — sold $0.4–1.1M of tokens they never bought on-chain (allocations/airdrops), the clearest "insider or allocation" fingerprint in the data.

Common thread of the few skill candidates: they never buy in the launch window, they buy liquidity (survivors), they size small relative to pool depth, and they sell in fixed small clips into strength. Their edge is discipline and selection, not information, and it is modest.

## 3b. Memecoin fundamentals at entry: market cap, age, launchpad, holders, dev

The trader-by-trader work above was done on prices and fills; this section adds the memecoin-native metrics per entry. Method, per-token and per-trader tables are in `docs/TOKEN_METRICS.md`; the columns `entry_fdv_usd`, `age_at_entry_min`, `launchpad`, `token_created`, `trader_is_dev`, `fdv_now` are on every row of `data/derived/positions_all.csv.gz`.

**Where the leaders enter (11,765 priced meme entries across 145 traders; 2,219 memes)**

| Metric | Result |
|---|---|
| fomo app positions with an entry price (3,276): entry FDV p10 / p25 / median / p75 / p90 | $77k / $228k / $1.0M / $5.1M / $30M; 50% opened below $1M |
| Priced on-chain capital by entry FDV ($48.9M with known supply) | <$100k 0%, $100k–1M 3%, $1M–10M 21%, $10M–100M 41%, >$100M 35% |
| Priced on-chain capital by token age at first buy | <1h 1%, 1h–24h 7%, 1–7d 8%, >7d 82% |
| Per-trader median entry FDV (145 traders) | p10 $458k, median $4.6M, p90 $43M; share of entries <$1M: median 22%, p90 62%; share within 1h of creation: median 6%, p90 28% |
| Dead-token bucket (no supply/pool anywhere; entry FDV unknowable) | 1,073 of 1,826 fully priced (trader, token) positions, $8.9M invested, realized −26% [−40%, −16%]; almost all Solana |

So the picture is bimodal. By count the leaders take many small, early shots (half of app positions below $1M FDV, and the sub-$1M / sub-24h entries are where the dead tokens are); by dollars they are size buyers of established tokens that are a week or more old and already above $10M. The money on the boards is the second kind of position marked to market, not the first kind realized.

**Does any of it predict the realized result?** One row per (trader, token) with every buy and sell priced, remaining bags at zero (`cons`) or at today's price (`mtm`), token-clustered bootstrap CI on the pooled conservative ROI (full tables in `docs/TOKEN_METRICS.md`):

| Bucket | positions / tokens | win % (mtm) | pooled ROI cons [95% CI] | pooled ROI mtm |
|---|---|---|---|---|
| entry FDV <$100k | 11 / 7 | 64% | +27% [−52%, +181%] | +875% |
| entry FDV $100k–1M | 141 / 53 | 67% | +9% [−17%, +43%] | +277% |
| entry FDV $1M–10M | 326 / 73 | 64% | +29% [−11%, +67%] | +1147% |
| entry FDV $10M–100M | 197 / 31 | 70% | −5% [−29%, +12%] | +630% |
| entry FDV >$100M | 78 / 10 | 72% | **−29% [−49%, −14%]** | +270% |
| age <1h | 46 / 21 | 59% | +84% [−3%, +148%] | +218% |
| age 1h–24h | 111 / 34 | 56% | −14% [−39%, −1%] | +22% |
| age >7d | 422 / 65 | 73% | −7% [−22%, +16%] | +628% |
| pump.fun | 841 / 320 | 30% | **−10% [−21%, −3%]** | +11% |
| Solana, other venues | 540 / 169 | 31% | **−21% [−37%, −7%]** | −1% |
| pre-Pons v3 factory (Robinhood; CASHCAT, TENDIES…) | 146 / 10 | 92% | −14% [−44%, +14%] | +407% |
| Pons V1 (Robinhood, v3 pool) | 93 / 7 | 98% | −8% [−33%, +8%] | +1193% |
| Pons V2 (Robinhood, v4 curve) | 56 / 16 | 70% | −33% [−73%, +23%] | +155% |
| LONG stock-paired (Robinhood) | 90 / 14 | 84% | +45% [−84%, +54%] | +2054% |
| fomo holder count ≥10k today (hindsight) | 252 / 10 | 87% | +1% [−12%, +38%] | +818% |

Reading: no bucket is significantly positive once unsold bags are counted at zero; the sub-$1M and sub-1h buckets that look best are small, survivor-biased (their dead siblings are in the "unknown" row) and have CIs through zero; the mega-cap late entries are the one clearly negative bucket; every large green number is in the mark-to-market column, i.e. the same bag-holding effect as section 2. Entry market cap and age are descriptors of *how* the leaders got their paper PnL, not a filter that produces realized edge.

**Holders.** fomo's token boards give a total holder count only for the ~60 tokens that make the trending / most-held / graduated boards (PONS 61k, CASHCAT 102k, ANSEM 136k, AI 29k, BONER, MarsCoin…); the ≥10k-holder tokens are the crowd tokens whose realized ROI is +1%. fomoapi's tracked top-holder endpoint returned data for 18 of the 160 most-traded memes (top-50 fomo-tracked holders hold 8–27% of supply in AI, BONER, CASHCAT, DELTA; leaderboard handles are 43 of AI's 50 tracked top holders). The long tail has no cheap holder count on Robinhood Chain (Blockscout gated), so holder count could not be used as an entry feature without hindsight; it is reported, not tested.

**Dev / creator.** Mint transactions were resolved for all 2,865 Robinhood tokens the leaderboard touched (deployer = `from` of the mint tx, or the ERC-4337 userOp sender for the 38 tokens launched from the fomo app; factories mapped to launchpads in `docs/TOKEN_METRICS.md`). Exactly one traded meme was deployed by a leaderboard wallet (SANDIH, LehmanFarters). Serial deployers exist: one wallet deployed 17 of the memes the leaderboard traded and seven wallets deployed 30–54 Robinhood tokens each. The Pons locker `feeRedirects` read is zero for every token; fomoapi's `isDev` flag is false on every tracked holder row and true for the thesis author on 3 of 116 tokens with theses (FIRE, STONKBROKER, NASDANQ; none a leaderboard handle). So "the trader is the dev" is answered: almost never, for the handles on the boards; the creator-fee income documented in section 0.6 accrues to Pons creators as a group, not to the leaderboard handles. Solana creators were not resolved (pump.fun creator sits in the bonding-curve account; not worth the Helius credits for a feature that could not be tested forward).

**Bundling / insiders / snipers.** Not measured per position: it needs holder snapshots at launch (first-block buyers, same-funder clusters), which the public Robinhood RPC can provide only by replaying every token's first blocks. The audit's earlier finding stands: whitelisted / first-second wallets own Pons launches, and none of the leaderboard handles is in that group by their fill timing (median first fill many hours after mint).

## 4. Hypotheses tested

| # | Hypothesis | Test | Result |
|---|---|---|---|
| H1 | Front-run the follower wave after a leader's buy (public sequencer feed ≈0.1–1 s vs app feed ≈15 s) | 276 exactly matched leader buys, swap-level prices, placebo windows 10 min earlier | +2.7% median at 60 s (66% positive) vs 0.0% placebo; leader impact +3.4%; entry at N+2, N+10, N+30 blocks similar; net of fees+impact −4.6% median; 12% of leaders sell within 10 min. Real, too small to trade. |
| H2 | Fade/exit on leader sells | same data; sell alerts in feed (693) | −0.5% to −1% drift over 15–30 min after sell alerts; nothing tradable |
| H-alert | Buy on the app's buy alert 1–3 min later | 600 alerts, 1m candles | +2.5% median at 1 h on Robinhood before costs (59–62% positive), ~0 after costs, ~0 at 4 h |
| H-consensus | ≥2–3 leaderboard traders entering within 1 h | 1,568 entries | no edge; more entrants → worse |
| H3 | 48 h survivor entries | 22 events | inconclusive, positive |
| H-momentum | 5-min breakout +10–20% with volume | 40,596 candle-minutes | negative after costs |
| H-pump | 15-min pump ≥30% | 280 events (liquid, known universe) | reverses: −4 to −6% median over 1–4 h |
| **H-dip** | 15-min drop ≥15% in liquid, leaderboard-active tokens | 1,793 events (15m), 285 (1m), 137 swap-verified | **positive, see section 5** |
| Sequencer feed | Is the on-chain head start real for retail? | live test | connects, catches up in 1.3 s, median 0.66 s behind sequencer timestamp from this sandbox; tx sender/target decodable in Python |

## 5. Candidate strategy (refuted on audit): dip-reversion in liquid, socially active memecoins

**Status after the adversarial audit (section 8): refuted as stated.** The numbers in 5.2 are the pre-audit backtest and are kept as the record of what was tested; the corrected expectancy is in section 8. Do not trade the rule below as written.

### 5.1 Rule

* Universe (known in real time): tokens with pool liquidity ≥ $100k in which ≥2 distinct leaderboard wallets had fills in the prior 24 h (source: on-chain transfer logs for the 128 tracked wallets, or the fomo feed's buy alerts from leaderboard handles).
* Signal: a 15-minute candle closes ≥15% below the previous close with ≥$2k volume, and the close before the drop is not above the close 1 h earlier (no blow-off top). One entry per token per 2 h.
* Entry: market buy at the next available price (next candle open in the backtest; next 30-second poll in the paper trader). Size: $500 per event, max 5 open.
* Exit: +15% take-profit or −30% stop, else after 4 h (variant B: hold 24 h with −30% stop).
* Costs modelled: 2% round trip (fomo 0.5%/side + Pons 1%/side) plus constant-product impact 2·size/(liquidity/2).

### 5.2 Backtest (15-minute candles, 2026-07-08 → 2026-09-03)

| Set | n | 1h median (p>0) | 4h median | 24h median (p>0) | net 1h | net TP15/SL30/4h |
|---|---|---|---|---|---|---|
| random entries, same liquid tokens (baseline) | 1,560 | −0.3% (45%) | −0.4% | +0.3% (51%) | — | — |
| all dips ≥15%, liq ≥100k, act24 ≥2 | 198 | +2.4% (61%) | +3.5% | +14.7% (60%) | −0.1% | +11.7% median, 72% hit, mean +3.6% |
| + prior 1h ≤ 0 (core) | 65 | +7.8% (74%) | +7.2% | +27.7% (67%) | +4.8% (62%) | +11.8% median, 83% hit, mean +6.5% |
| + crash ≤ −25% | 23 | +8.0% (77%) | +8.5% | +43% (83%) | +5.3% (64%) | +11.9% median, 87% hit |
| liq ≥100k, act24 ≥1, crash ≤ −20% | 96 | +6.3% | +7.7% | +26% (70%) | +6.3% (58%) | +11.7% median, 77% hit |

Robustness: equal-weighting by token gives a +8.0% median of token medians (9 of 15 tokens positive); leaving out the two most frequent tokens keeps +2.4% to +6.7% medians; by month (exit 4 h, −30% stop) July +6.7% (57% positive, n=42), August +1.4% (62%, n=21), September n=2. Dips coinciding with a leaderboard sell in the ±15 min window do not bounce (24 h median −5%); dips without one do (+17%). Larger drops bounce more (−15/−20%: +5.5% at 24 h; −20/−25%: +25%; −25/−35%: +56%). 137 events re-measured on exact pool swap prices: +4.1% at 5 min, +5.6% at 15 min, +7.5% at 60 min (60–64% positive), net 30 min +1.8%; liquidity ≥ $500k: +23.7% at 60 min.

Nuance: the leaderboard-activity filter is a liquidity/attention proxy, not the source of the edge. Dips in liquid tokens with **no** leaderboard fills in the prior 24 h bounce just as well (n=247: +2.2% at 1 h, +4.1% at 4 h, +25.8% at 24 h, 66% positive), and 5-minute dips in feed tokens without leaderboard activity show +8.8% net at 30 min (n=62). What matters is a real, liquid pool and a sharp move; the leaderboard mainly tells you which tokens have a crowd to bring the price back.

### 5.3 Why it should exist and why it might stop

Mechanism: a market of impatient retail flow (fomo ≈64k daily addresses, ~$1.5k each), manual copy-trading, sponsored gas, and pools of $100k–$5M. A single $20–50k sell moves price 10–30%; the crowd sees red and sells, then dip-buyers and the token's community (the same leaderboard names, who are net holders) restore the price. The pump mirror (sharp pumps revert) says the same thing: short-horizon overreaction. It stops working when liquidity leaves (the September 29 gas-subsidy end, a regulatory hit to card-funded buys, or simply the end of the Robinhood Chain wave), which is why the universe rule requires live leaderboard activity and real liquidity, and why the paper trade must run through a regime change before any size.

### 5.4 Executability for a retail trader

* Detection: 30-second polling of DexScreener (free) or GeckoTerminal for the tracked tokens; the universe comes from the fomo feed (leaderboard handles' buy alerts) or from on-chain transfer logs of the 128 wallets (free public RPC). No paid stream is required; the 15-second app lag is irrelevant at a 15-minute signal.
* Execution: in the fomo app (0.5% fee, gas sponsored, auto slippage) or directly on Uniswap v4/v3 on Robinhood Chain (1% pool fee, gas normally < $0.05 but $20–60 during the Sep 1–2 congestion). Stops are not native on-chain: the trader or bot must sell at market when the stop level prints, so gap risk is real; the backtest assumes the stop fills at the stop level.
* Sizing: keep clips ≤ 1% of pool liquidity; at $100k liquidity that is $500–1,000.
* Same rule, same data, same costs are implemented in `src/strategy/dip_reversion_paper_trader.py`, which is running as a paper trader (log in `data/derived/paper_trades.jsonl` when copied). Backtest → paper → live consistency is enforced by using only data available at each 30-second poll.

### 5.5 What is still unproven (read before risking money)

* Sample size: 65 core events on 15 tokens over 8 weeks; two tokens give a third of the events.
* Regime: July–September 2026 is a launch-and-blow-off regime on a new chain; August already shows a smaller edge than July.
* Survivorship: the token universe is "tokens the current top-100 touched"; the real-time activity filter and the same-token random baseline control most of it, but events followed by a token dying with no further trades are dropped rather than counted as −100%, so 24 h figures are optimistic.
* Candle data: GeckoTerminal candles can print artifacts; 137 events were re-verified on swap logs, the rest were not.
* Fees: Pons v2 creator taxes (up to 10%) were not read per token; the 2% round-trip assumption is the floor.
* Timing: the edge is gone if you are late. Entering at the open of the candle after the dip: net +4.8% (1 h), +5.2% (4 h). Entering one 15-minute candle later: −1.5% and −3.0%. Two candles later: −0.5% and −1.1%. The bounce is largely over within 15–30 minutes, so the rule must be executed within a few minutes of the signal (the 1-minute and swap-level tests show the first 5–15 minutes carry +3.5% to +4.5%). A trader who checks the app occasionally cannot run this; a 30-second polling script can.
* Event-time liquidity is unobserved (GeckoTerminal liquidity is current); using prior-1h candle volume as a proxy, both high-volume (≥$20k, n=38, 84% hit, +7.5% mean) and low-volume (n=27, 74% hit, +5.0% mean) events remain positive under the TP15/SL30/4h rule.

## 6. Audit log

* Leaderboard PnL definition reverse-engineered and confirmed numerically (section 2).
* On-chain ledgers: fomo fills settle through relay `0xb92fe9…` in bundled transactions; 114k of 288k inbound transfers to the tracked wallets are airdrop spam and were excluded by counterparty behaviour; fills are priced from candles at the block time (block timestamps exact for 34k anchors, interpolated elsewhere with median error 0.3 s).
* Every forward-return figure uses the open of the first candle after the event; no candle containing the event is used.
* Placebo and random-entry baselines were run for the two positive results (leader-buy wave; dip reversion).
* Sell-alert survivorship (only winners printed) was detected and reported rather than used.
* Known limitations: GeckoTerminal coverage was still incomplete when this report was written (281 of ~1,900 traded tokens with candles); the fomoapi free key allows 25 handle resolutions per month, so profiles came from the leaderboard rows and trade endpoints only.
* An adversarial audit workflow (five independent lenses: look-ahead, survivorship, data artifacts, costs, statistics) was launched; its verdict is appended in section 8 when available.

## 7. Recommendation

1. Do not copy the leaderboard, and do not trade the dip rule as backtested here; there is no proven edge to size into.
2. The only lead worth carrying forward is the generic 15-minute overreaction bounce, and only as a frozen, hindsight-free forward test: universe = every Robinhood Chain token whose pool depth at the signal time is ≥ ~$1,000 per 1% move (measured from on-chain reserves or the last swaps, never from a current-liquidity snapshot); signal = 15-minute candle ≤ −15% confirmed on swap logs (≥ 20 swaps, plausible volume/depth); automated entry within 120 s at ≤ +2% above the crash close; $500 clip maximum; fees = 2 × (0.5% + actual pool fee) plus any hook or creator tax read on-chain, skip if the projected round trip exceeds 4%; exit at +15% take-profit or −35% modelled stop or 4 h; score on the mean and sum of P&L with token-clustered confidence intervals over at least 100 independent token-days, including tokens that die. The paper trader in `src/strategy/` is a starting point but still uses a live DexScreener liquidity number and the 2% cost model; it must be changed to the rule above before its log means anything.
3. Keep the process lessons from the few disciplined traders (no launch-window buys, survivors only, fixed-clip scaling in and out, moon bag, cut losers within a day), and treat KOL buy alerts as exit liquidity for positions already held, never as entries.
4. The real money on this chain is made by creators (70% of a 1% fee on every trade, forever), insiders and whitelisted wallets at launch, and audiences that move thin pools. None of that is a retail trading strategy; anyone selling it as one should be asked for point-in-time, clustered, out-of-sample evidence.

## 8. Adversarial audit verdict

Five independent auditors (look-ahead, survivorship, data artifacts, costs/executability, statistics/regime) each tried to refute the dip result with their own code on the same data; all five refuted it (one fatal, four material). Full verdicts: `docs/audit_dip_strategy.json`; conclusion: `docs/audit_dip_strategy_verdict.md`. The findings that matter:

| Finding | Effect |
|---|---|
| The `liquidity ≥ $100k` filter was current (Sep 4) liquidity applied to July–August events, i.e. survivorship. Same events with liquidity-now < $100k: 1 h net −11% (29% positive). With an event-time proxy the 1 h median is 0% to +2% and the token-median is negative. | Fatal: this filter created the short-horizon edge. |
| Token universe and wallet set are hindsight-selected (today's winners' most-traded tokens, ~10% of eligible tokens). A hindsight-free universe (fomoscope boards Aug 27–29, tested Aug 30–Sep 4, Solana, n=76) is negative at every horizon (1 h −8.7%, TP/SL mean −5.7%). | Fatal: sign flips off the selected universe. |
| Two of 64 Robinhood events were candle artifacts (a pool with the token as quote) and were the two largest winners. The other 62 crashes are real on swap prices. | Material. |
| Price impact understated 4–6× (GeckoTerminal reserve USD vs measured $ per 1% move); fees are ~3% round trip, not 2%. With measured impact: 1 h net median +1.6%, 4 h +0.1%, Aug+ −5%. | Material; strategy capacity ≈ $500 per event. |
| The take-profit/stop "median +11.8%, 83% hit" statistic reproduces under random entries; only the mean carries information, and 45% of take-profit hits were wick-only. Stops fill at −33% to −40%, not −30%. | Material. |
| 15% (core) to 26% (refreshed) of 24 h returns were silently missing (dead tokens, censoring); counting them as −100% puts the 24 h median between −2% and +6%. | Material. |
| Clustering: 65 events = 43 independent 24 h clusters on 15 tokens; token-clustered 1 h CI [−0.2%, +10.8%], 4 h [−1.4%, +15%]; the "core" filter is one cell of a ~360-cell grid. Post-claim events (n=15) were negative. | Material. |

Corrected expectancy for an automated $500 clip with 60 s reaction on the (still survivor-biased) universe: 1 h close mean +2.6% to +4.5% (55–61% positive), TP15/SL35/4 h mean +1% to +5% with a token-clustered interval of roughly [0%, +3%] once the look-ahead is removed; $2,000 clips ≈ 0%, $5,000 clips negative; 5-minute reaction halves it, 15-minute reaction removes it. Verdict: not a real, retail-executable edge; a capacity-limited scalp that has not yet been shown to work on any universe chosen without hindsight.

## 9. What this session got right and wrong (audit of the process)

* Right: reverse-engineering the leaderboard PnL, separating realized from paper PnL on-chain, exact swap-level event studies with placebos, and submitting the only positive result to independent refutation before recommending it.
* Wrong (caught by the audit): using a current-liquidity snapshot as a filter, pulling candles only for the tokens today's winners traded, reporting medians of a take-profit rule, dropping missing returns, and quoting 24 h figures from a survivor set. These are exactly the traps the research phase had listed; the checklist in `docs/ANALYSIS_GUIDE.md` now carries them explicitly.

## 10. Round 2: the "95% lose, buy the revenue protocols" clip

The clip's claims: most fomo traders lose; the top P&Ls come from big-audience traders buying microscopic market caps and letting the rare runner pay for the rest; the intelligent play is revenue-generating infrastructure on Robinhood Chain. Each was tested.

### 10.1 Do 95% lose? Yes, on realized PnL

DWF Ventures counted 292,531 fomo wallets over 90 days: 6.16% in profit on realized gains, an estimated $1.26B lost, 25 wallets above $10k net profit ([yellow.com](https://yellow.com/phoenix.html/news/fomo-copy-trading-94-percent-wallet-losses), original post by @MidCurveMortal). This report's own numbers agree: 63% of the 147 leaderboard traders have a negative realized sum in their last-25 closed trades, and the pooled realized ROI of fully priced (trader, token) positions is negative in every venue bucket except the stock-paired LONG tokens (section 3b). DWF's structural explanation is the same as section 4's: public call posters get follower buying pressure before they sell.

### 10.2 The lottery: follow leaders into fresh launches and hold for the runner

`src/analysis/lottery_bound.py`, output `data/derived/lottery_rh.json`. Universe: every Robinhood token where a leaderboard wallet made its first on-chain buy within 24 hours of the mint (155 tokens; supply is 1B for every launchpad token, so FDV = price × 1e9). Follower entry = open of the first candle after the leader's buy; dead tokens (no candles, no pool) = −100%; returns at 1h…30d on closes; token-clustered bootstrap CI on the mean.

| Cohort (leader buy ≤ 24h after mint) | n / dead | mean 24h return, dead = −100% [95% CI] | ≥10× share (all) | mean after 25% round-trip cost |
|---|---|---|---|---|
| all, Jul 13 → Sep 3 | 155 / 74 | +61% [−34%, +190%] | 3.5% | +21% |
| events in July | 48 / 19 | +326% [−83%, +838%] | 12% | +220% |
| events Aug 1–15 | 27 / 14 | +11% [−74%, +120%] | 0% | −17% |
| events Aug 16–31 | 52 / 22 | +11% [−54%, +97%] | 2.4% | −17% |
| events Sep 1–3 | 28 / 19 | −75% [−97%, −35%] | 0% | −81% |
| buyer has ≥30k followers (the clip's KOLs) | 94 / 65 | −55% [−91%, −3%] | 1.3% | −67% |
| buyer has <30k followers | 61 / 9 | +310% [+33%, +681%] | 8.3% | +207% |
| all-time-board buyer, events after Aug 15 | 65 / 39 | −41% [−79%, +15%] | 1.8% | −56% |
| 7-day hold, events after Aug 15 | 80 / 41 | −45% [−78%, +6%] | 1.6% | −59% |

Reading: the clip is right about the mechanism and right that following the big audiences loses (−55%, CI excludes zero). The positive expectancy is entirely the July launch wave (BRODIE 432×, worth 99×, CHILL 95×, GME 28× from $7k–$50k FDV) and the small-audience cohort, which is survivorship: those wallets are on today's board *because* those buys ran. Restricted to events after Aug 15, every cohort is negative before costs. The 25% cost line is the realistic round trip on a Pons V2 curve in the first hour (1% pool fee, 0.5% app fee, launch-window taxes, $500 into $2–30k depth). This is not a strategy; it was a regime.

### 10.3 The "revenue protocols": PONS, INDEX, and what actually reaches holders

Revenue-generating tokens on Robinhood Chain are few: PONS (launchpad; 1% pool fee split 70% creator / 30% protocol on V1 launches; docs say 80% of the protocol share funds TWAP buybacks that go to the burn address) and The Index (INDEX, "converts trading fees into tokenized assets", $0.37M protocol revenue in 30 days, ~$31–65M market cap). GMGN, LONG, Uniswap's Pools and the fomo app itself earn the rest of the chain's app revenue and have no Robinhood-Chain token. The leaderboard's live balances are 20% PONS and 28% AI (a LONG stock-paired meme), so "I made top 50 by holding infrastructure" is consistent with this data.

**The fee cycle** (DefiLlama, `data/raw/defillama/`): Pons fees $1.5M/day on Jul 21 → $0.25M on Aug 20 → $6.4M on Sep 3 (25× in two weeks); protocol revenue $9.1M in 30 days, $1.26M on Sep 3; chain fees $1.4M/day on Aug 16 → $21M on Sep 4. PONS repriced with it: $0.039 on Aug 22 → $0.62 on Sep 3 (FDV $424M, circulating market cap ≈ $302M after burns), +17% more on Sep 4 when Uniswap Labs disclosed an undisclosed-size PONS purchase ([crypto.news](https://crypto.news/uniswap-labs-buys-pons-as-robinhood-chain-launchpad-fees-surge/)).

**What actually reaches PONS holders** (`src/analysis/pons_burns.py`, every PONS transfer to the dead address since mint, priced at the candle at burn time; `data/derived/pons_burns_daily.csv`): 294.8M PONS burned in total, of which 171M on Jul 13–14 were launch-time supply burns, not fee buybacks. Since Jul 15, $6.1M of burns against $13.5M of protocol revenue = 45% (the docs say 80%; a community tracker reports 60% and notes that V2 launches, now most of the volume, buy back the launched token rather than PONS). Burns are lumpy: 2–8% of revenue on Aug 29–30 and Sep 2–3, 92% on Sep 1, $832k on Sep 4. Aug 5 → Sep 3: $3.2M burned on $9.1M revenue and $46.8M fees, i.e. about 7% of gross fees reach the token.

| Valuation | PONS | PUMP (pump.fun, benchmark) |
|---|---|---|
| Market cap | ≈ $302M circulating ($424M FDV) | $1.73B |
| Protocol revenue, trailing 30d | $9.1M | ≈ $33M |
| Actual buyback, trailing 30d | $3.2M (annualized 13% of market cap) | 50% of revenue ≈ $16M (annualized ≈ 12%) |
| Market cap / annualized 30d revenue | 2.8× | ≈ 4.4× |

So PONS is priced roughly like PUMP on what it actually returns to holders. The apparent cheapness (0.7× on Sep 3's revenue run-rate) is the market discounting the spike, which is the right thing to do: the fee series is memecoin volume, the volume is subsidised (90-day gas subsidy from Jul 1, ending in early October; [crypto.news](https://crypto.news/robinhood-chain-vs-solana-flippening-math/)), and the previous fee peak (Jul 21) was followed by an 84% fee decline in a month.

**Is there a tradable rule in it?** `src/analysis/house_token_fees.py`: hold the house token while 7-day fees exceed 30-day fees, else cash.

| Token | Window | Rule | Buy-and-hold | Next week after a fee-up week vs fee-down week |
|---|---|---|---|---|
| PUMP (pump.fun fees) | Oct 2025 → Sep 2026, 334 d | ×1.26, max DD −51%, in market 42% | ×0.61, max DD −82% | +5.2% (n=23) vs −1.3% (n=23) |
| BONK (letsbonk fees; weak link) | same | ×0.63 | ×0.16 | −1.2% vs −3.3% |
| PONS (3d > 14d, only 33 usable days) | Aug 1 → Sep 3 | ×6.9, in market 52% | ×24.7 | not testable (n=1 cycle) |

On PONS the price and the fees move the same day (log-change correlation 0.32; fees leading price by a day 0.32, price leading fees 0.26): the fee print is not a signal you get ahead of the market. On PUMP the rule beats holding over one 11-month sample and still drew down 51%. That is a plausible risk-management overlay for someone who wants this beta, not a proven edge, and it says nothing about the first half of October.

**Front-running the buyback**: not viable. On Sep 3 the PONS/USDG v4 pool did 23,092 swaps, $14.9M bought and $13.5M sold (`data/derived/pons_swaps_2026-09-03.json`); the day's burns were $70k (0.5% of buy volume) and the largest actual burner clips (Sep 1, Sep 4) come in a few large lumps at unannounced times. Even the largest steady buy-only router on the day (fomo's own swap path, $1.0M in 141 clips of ~$1.3k) moved price 0.03% per clip, below one side of the fees.

### 10.4 Verdict on round 2

* "95% lose": true on realized PnL, and this dataset's leaderboard is not the exception on a realized basis.
* "Buy the tiny caps the KOLs buy and let the runner pay": worked in the July launch wave, has lost money since, and loses on every horizon for the big-audience posters. Survivorship explains the rest.
* "Buy the revenue protocols": PONS is a real fee business priced like its Solana peer, with a discretionary, under-delivered buyback and a subsidy cliff four weeks out. Holding it is a directional bet on Robinhood Chain memecoin volume. That may be a fine bet; it is not the treasure, because nothing here gives a retail trader an expectancy the market has not already priced.

No angle in either round produced a strategy that is simultaneously profitable after costs, sustainable across regimes, and executable at retail. The one item still worth money is the hindsight-free forward test of the 15-minute overreaction bounce (section 7), and the one item worth watching is what Pons fees do in the two weeks after the gas subsidy ends.

## 11. Round 3: how the money is actually made, mechanism by mechanism

The instruction was: when something fails, find out why, look from other angles, use the tails. Rounds 1–2 mostly reported medians and populations. This round takes each way the top handles made money, quantifies it as a strategy with its tail, its costs and its capacity, and adds three mechanisms that had never been tested here: the carry on the mania perps, cross-pool arbitrage, and the creator seat.

### 11.1 The audience pump, costed (the poster's edge, and whether a fast follower can take it)

276 leaderboard fills matched to exact pool swaps (`data/derived/kol_swap_events2.jsonl`), follower entry two blocks (0.2 s) after the fill via the public sequencer feed, exit at the pool price 60 s or 300 s later, costs = 1% pool fee each side + constant-product impact of the clip on the pool's measured depth.

| Cohort | n | gross mean 60 s | net mean, $250 clip [CI] | net mean, $500 clip | net mean, $1,000 clip |
|---|---|---|---|---|---|
| all fills | 276 | +7.8% | −0.1% [−2.9%, +2.7%] | −6.0% | −17.8% |
| ≥100k followers, pool < $50k | 80 | +12.2% (median +7.0%, MFE60 +27.8%) | +1.1% [−5.1%, +7.2%] | −8.0% | −26.2% |
| ≥30k followers, pool < $30k | 123 | +11.0% | −1.4% [−6.4%, +3.8%] | −11.8% | −32.6% |
| ≥100k & <$50k, events after Aug 15 | 8 | −5.6% | | −22.6% | |

The pump is real and large (57% of big-audience fills print +10% within a minute, 35% print +30%), which is exactly the poster's edge: they are in before their own audience and they pay no impact to enter the move they cause. A follower in the same pool pays the impact both ways; at $250 the expectancy is zero, at $500 it is −8%, and the mechanism has faded since mid-August. The audience is the edge; the trade is not transferable.

### 11.2 What the realized winners do differently (selection, sizing, exits)

`src/analysis/behavior.py`, `data/derived/behavior_positions.json`: 1,826 fully priced (trader, token) meme positions with every fill, 126 traders. Traders with ≥15 positions are ranked by realized ROI with unsold bags at zero. Only four traders clear +15% ROI with a ≥35% win rate (GuavaGuy2001, Samisa_btc, cryptochi3f_, montyMole44; 99 positions between them); 19 are below −15%.

| Dimension (p25 / median / p75) | winners | losers |
|---|---|---|
| entry FDV | $1.1M / $3.0M / $7.0M | $1.3M / $3.6M / $13.6M |
| token age at first buy | 38h / 10d / 22d | 27h / 9d / 29d |
| 24h price change before entry | −30% / +42% / +42% (n=3) | +14% / +64% / +1229% (n=24) |
| position size | $400 / $800 / $2.8k | $525 / $2.5k / $10k |
| first buy as share of position | 35% / 100% / 100% | 22% / 57% / 100% |
| hold to first sell | 16m / 11.5h / 2.2d | 34m / 5.8h / 30h |
| share of sells below cost | 21% | 46% |
| share of sells at ≥2× cost | 60% | 21% |
| best exit ÷ 7-day peak (captured) | 20% / 33% / 33% (n=3) | 35% / 49% / 73% (n=31) |

Selection does not separate them: same market caps, same ages, same venues (pump.fun dominates both). Sizing does: winners buy smaller, in one clip, and average down less (across all traders, positions with 4+ buys return −15% pooled versus −10% for single-clip entries; positions above $50k return −20%). Exits separate them by construction (a sell at 2× is what a realized win is), so the non-circular content is: winners are not better at catching the peak (they capture a third of it, losers half), they simply hold the ones that go up and do not add to the ones that go down. Time to first sell does not predict outcome in the pooled data (every bucket from <30 min to >10 days has a negative median). There is no rulebook to extract beyond "small, single clip, no averaging, let winners run"; that is position management, and it does not create expectancy on its own: the pooled realized ROI of all 1,765 clean positions is negative in every size bucket except $500–50k (+5–11% pooled, median −25%).

### 11.3 New-venue first-days baskets

`data/derived/venue_first_days.json`: for each launch factory on Robinhood Chain, the three tokens with the most 72-hour candle volume among those created in the venue's first 72 hours, bought at the day-3 close. Pons V1 (Jul 13): ×2.8 at 30 days, ×0.9 today; Pons V2 (Aug 5): ×1.9 at 30 days; the 0x7ed5 pad (Aug 4): ×4.7; the 0x0000ff pad (Aug 5): ×11 on one token (HOOKR) and ×0.4 on another; the Aug 26–Sep 2 pads: ×0.9–1.0. Day-14 and day-28 placebo cohorts range from ×0.4 to ×4.6. Cohorts are 4–80 tokens with most dead tokens unrankable, so this is a handful of lottery tickets per venue, not a strategy; the July ones paid, the late-August ones did not.

### 11.4 Cross-pool arbitrage (PONS: WETH v3 pool vs USDG v4 pool, Sep 3)

`src/analysis/pool_swaps2.py`, `data/derived/swaps_PONS_WETH_v3_2026-09-03.json`: 9,023 swaps in the WETH pool ($7.8M) against 23,092 in the USDG pool ($28M), ETH/USD from hourly CoinGecko. Spread between the two pools' PONS prices: mean +0.01%, p5 −0.87%, p95 +1.00%; 0.4% of prints beyond ±1.5% (six episodes, median 224 s, mean 1.7% at the start), none beyond 3%. With 0.3% + 1% pool fees the round trip is 1.3%, so the bots that already run this leave nothing for a slower entrant, even with sponsored gas. CASHCAT is the same picture (WETH v3 pool vs USDG v4 pool, 6,961 vs 16,952 swaps on Sep 3): spread p5 −1.00%, p95 +0.93%, four episodes above 1.5%, none above 3%.

### 11.5 The carry on the mania perps (the one that survived)

Hyperliquid lists CASHCAT and PONS perpetuals at 3× max leverage (`data/raw/hyperliquid/`). Funding history:

| Perp | since | hourly prints positive | mean funding (annualized) | cumulative funding | 30-day funding |
|---|---|---|---|---|---|
| CASHCAT | Jul 11 (1,333 h) | 100% | 118%/yr | 18.0% | 7.7% (next best on the exchange: XMR 4.6%, PURR 3.2%, FARTCOIN 2.0%, PUMP 1.5%) |
| PONS | Aug 31 (110 h) | 85% | 63%/yr | 0.8% | |

Simulation (`src/analysis/hl_carry.py`): long CASHCAT spot on Robinhood Chain (the CASHCAT/WETH pool has $3.4–6M depth; Hyperliquid has no CASHCAT spot), short an equal notional on the perp with 70% margin (survives a 70% adverse move; the largest perp up-move from entry was 53%, and the perp wicked −60% in minutes on listing day, which hurts longs, not this short), funding accrued hourly, basis marked to market hour by hour, costs 1.2% of notional (0.3% pool fee each side, 0.5% impact, 0.035% perp fee each side).

| | CASHCAT, Jul 11 → Sep 3 |
|---|---|
| funding collected | +17.7% of notional |
| basis P&L at exit (noise, range −5% … +20%) | +10.9% |
| costs | −1.2% |
| net | +27.5% of notional = +16.2% on capital (spot + 70% margin) ≈ 108%/yr |
| max equity drawdown | −15.5% of notional (basis swings) |
| 14-day trades started each week, net of costs | +10.1%, +3.1%, +8.5%, +2.9%, +3.8%, +1.8% (all positive) |
| weekly funding | 2.0%, 4.7%, 2.1%, 1.2%, 2.3%, 1.1%, 1.7%, 2.2%, 0.5% |

Why it exists: the perp is crowded long by the same traders section 10.1 counts as losers, funding is what longs pay shorts, and Robinhood Chain spot is where the hedge sits. Why it is executable at retail: the fomo app itself carries Hyperliquid perp accounts (137 of 147 leaderboard balances expose a perp margin summary), so both legs sit in one app; capacity is the perp's open interest ($55M CASHCAT, $71M PONS) against $3–6M of spot depth per pool, i.e. six-figure size without moving either. Why it is not the jackpot: it is a yield of 1–2% a week, on one to three names, with ±15% basis swings that require sizing for, and it stops the day the crowd flips short or the perp is delisted. Funding on PUMP decayed from mania levels to 12%/yr within months; CASHCAT is nine weeks in and still at 24% for the last 30 days annualized 94%.

Execution spec (frozen, for the forward test): enter when the perp's trailing 7-day funding annualizes above 40% and the perp trades within ±3% of Robinhood spot; size the short at 1.4× leverage or less; rebalance the hedge when the spot leg drifts more than 10% from the perp notional; exit when 7-day funding annualizes below 15% or the basis exceeds ±8% against the position; never hold through a delisting notice. Paper-trade it with the same rule for two weeks before sizing. `src/strategy/carry_paper_trader.py` runs exactly this rule hourly (DexScreener spot, Hyperliquid mark and funding); it entered CASHCAT (7-day funding annualizing 57%) and PONS (42%) on Sep 4 at a 0.2% basis, and logs to `data/derived/carry_trades.jsonl`. On Sep 3 the perp-to-Robinhood-spot basis stayed within −0.3% … +0.8% every hour, so the ±15% swings in the 55-day series are the listing-week chaos, not the steady state.

**Forward print, Sep 4 → Sep 5 21:00 UTC (46 hours).** The paper trader's two entries at a 0.2% basis: CASHCAT collected 0.41% of notional in funding (100% of prints positive, 78%/yr average), spot 0.2507 → 0.251 and perp 0.2513 → 0.250, so about +1.1% of notional in two days; PONS collected 0.54% (89% positive, 103%/yr average) but the perp premium widened from 0.2% to 1.3% while spot rose 28% (0.7087 → 0.9074 against a 0.9190 mark), so about −0.9%. Combined roughly flat: the funding is real and the basis noise is the same size over two days. Live at the time of writing PONS funding prints 109%/yr on $115M of open interest and $170M of daily volume, CASHCAT's hourly print has decayed to 11%/yr (78%/yr over the last two days), XMR 40%, PUMP 31%, PURR 23%. At the last-30-day realized funding and 1.4× margin, the carry pays about 4.2% a month on capital in CASHCAT, 2.3% in XMR (no spot leg in the app), 1.5% in PURR, under 1% in PUMP and FARTCOIN; PONS at its current rate would pay about 5% a month if the rate persists, five days into its listing. So the seat is $2k–10k a month on $50–200k while the crowd stays long, and it is the only measured positive expectancy in this repository that a retail account can hold.

### 11.6 The creator seat and the true base rate of a launch

Every swap on a Pons token pays 0.7% to the creator, forever, from a $1 launch, and the creator's initial buy is the only trade that executes in the launch block. The lockers pay creators on every swap, which made the full payout history too dense to pull from the public RPC (the query cap is hit at 4,000-block windows); the factory creation events were pulled instead (`src/collect/pull_factory_logs.py`, `data/derived/launches_per_venue.json`; each creation event carries the token address, verified against the mint-transaction census 200/200).

| Launchpad | launches Jul 13 → Sep 4 | week of Aug 31 |
|---|---|---|
| Pons V1 (closed Aug 15) | 266,207 | 0 |
| Pons V2 | 145,759 | 80,542 |
| LONG | 21,598 | 10,532 |
| pad 0x7ed5 | 224,803 | 106,211 |
| total | **658,367** | 197,285 (≈ 28,000 a day) |

The base rate: the 147 leaderboard traders touched 1,768 of these launches (0.27%); 510 of those ever had a pool GeckoTerminal tracks (0.077% of launches); the tokens that reached the boards are a few dozen. The clip's "less than 5% chance of catching one" is generous by a factor of about sixty; the honest number for a random launch is under 0.1%, which is why nothing built on entering launches survives once dead tokens are counted (sections 10.2, 11.3).

Creator economics from the same census: about $44M of the $63M all-time Pons fees went to creators. The 510 tracked launchpad tokens did $2.75B of candle volume, i.e. ≈ $19M of creator fees, with the top 10 tokens taking 46% and the top 100 taking 86% (CASHCAT ≈ $4.2M, TENDIES $0.85M, JUGGERNAUT $0.81M, AI $0.78M, DELTA $0.47M). The remaining ≈ $28M spread over 658,000 launches is $42 per launch on average and $0 at the median, because the median launch never trades. Eight wallets deployed 30–54 of the tokens the leaderboard traded and one wallet deployed 17 of the memes with two or more leaderboard buyers: serial launching is a volume business run by a handful of operators with distribution (bots, audiences, listings), and one leaderboard handle is among them. It is the house's seat, it needs no price edge, and its expectancy for a newcomer with no distribution is the $42 average minus gas and the initial buy, i.e. roughly zero.

### 11.7 Verdict on round 3

Directional edge: none survived (scalp, lottery, baskets, arbitrage, copy, dip). The two seats that actually earn on this chain without price prediction are the house's (creator fees, buybacks) and the lender's (funding from crowded longs). The second one is open to a retail account, is measured above with no look-ahead and no survivorship, and is the recommendation of this report: run the carry in section 11.5 as a two-week paper test alongside the section 7 forward test, and treat every directional memecoin idea in this repository as refuted until a hindsight-free test says otherwise.

## 12. Round 4: "filter new coins and scalp", tested on every launch of a day

The question was why the community playbook (new-pair filters: early buyer count, buy/sell ratio, volume, dev holdings, serial deployers, momentum in the first minutes; scalp exits with take-profit and stop) had not been tested. Rounds 1–3 only had the leaderboard's picks, which are survivors. This round rebuilt the full universe for one day.

**Data** (`src/collect/pull_v4_swaps_day.py`, `pull_v4_init.py`, `pull_v2_curve.py`; `src/analysis/launch_replay.py`, `curve_replay.py`): all 5,865,157 Uniswap v4 PoolManager swaps on Robinhood Chain on Sep 3 (three parallel block ranges), the 18,258 v4 pool initialisations of the day (pool id → token, quote, hook), the creation events of all 46,218 launches with token, curve contract and creator address, and 418,595 Pons V2 bonding-curve Buy/Sell events for 12:00–18:00 UTC. Prices are per-trade (sqrtPrice for v4, quote-in ÷ tokens-out for the curve); returns are price ratios so the quote asset does not matter. Costs: 1% pool fee each side, impact of a 0.05 ETH clip (v4) or a 2%-of-curve clip against the depth actually in the pool/curve at entry, the 5-second snipe tax if entering earlier, stops filled 5% worse, and a token that never prints again after entry counted as an exit at half. Fit/holdout split by hour of day; all rules were fixed before running and none were tuned afterwards.

**Base rates (Pons V2, 6,108 launches 12:00–18:00 with ≥30 min of follow-up)**

| | |
|---|---|
| creator's initial buy (only trade in the launch block) | median 7.1% of supply, p90 22.6% |
| launches by creators with ≥10 launches that day | 43% (8,370 of 19,261 V2 launches; top creator 369 in a day) |
| launches with ≥10 trades / ≥100 trades | 59% / 12% |
| ever 2× the first price / ever 5× | 25% / 7% |
| price after the 60-second mark ever 2× / 5× | 3.8% / 0.7% (≥20 buys in the first minute: 10% / 1.5%; serial creator: 1.8% / 0.4%; one-off creator: 6.1% / 1.0%) |
| ended below first price | 92% |
| graduated to a v4 pool the same day | 4.6% (277 collected ≥ 4.2 quote units) |

**Filters and scalps on the V2 curve** (mean net return per trade, bootstrap CI, median, win rate; fit = 12:00–15:00, holdout = 15:00–18:00; full table in `data/derived/curve_replay_0903.txt`)

| Rule (entry → exit) | fit | holdout |
|---|---|---|
| any launch, 10 s → 60 s | −40% [−42, −37], med −30%, win 9% | −46% [−48, −44], win 8% |
| ≥5 buys & 0 sells in 30 s, 30 s → 120 s | −16% [−34, +8], win 13% | −34% [−49, −21], win 17% |
| ≥10 buys in 60 s & price ≥1.5× at 60 s, 60 s → 300 s | −22% [−31, −11], win 25% | −23% [−36, −11], win 27% |
| same with TP 2× / SL 0.7 | −19% [−25, −12] | −22% [−30, −14] |
| ≥20 buys in 60 s, 60 s → 15 min | −26% [−32, −20], win 14% | −28% [−35, −21], win 15% |
| same with TP 1.5× / SL 0.7 | −26% [−29, −23] | −28% [−32, −25] |
| buys ≥ 3× sells & ≥1 quote unit by 5 min, 5 → 30 min | −1% [−31, +36] (n=22) | −21% [−37, −4] |
| near graduation (≥3 quote units by 15 min), 15 → 30 min | −24% [−32, −15] | −23% [−29, −14] |
| post-snipe dip (price at 60 s < 0.7 × first-minute high, ≥8 buys), 60 s → 10 min | −31% [−35, −27] | −36% [−41, −31] |
| one-off creator & ≥10 buys in 60 s, 60 s → 15 min | −26% [−33, −18] | −23% [−29, −15] |
| serial creator (≥10/day) & ≥10 buys in 60 s | −32% [−36, −26] | −38% [−47, −29] |
| creator initial buy ≥3% & ≥10 buys in 60 s | −29% [−34, −25] | −33% [−39, −27] |
| big first buy (≥0.2 quote units), 10 s → 300 s | −18% [−21, −14] | −10% [−15, −5] |
| graduated that day (hindsight), 60 s → 30 min | +50% [+17, +84], med −10% | +120% [+66, +168], med +14% |

**Filters and scalps on the 0x7ed5 pad and LONG (v4 pools from launch; 982 launches with a price path out of 24,864 + 2,093 launched; the rest never got a liquid print)**: any launch 10 s → 60 s: −94% to −100% (most launches have no bid after the first minute); ≥5 buys in 30 s: −26% / −32%; ≥20 buys in 60 s: −40% / −24% (with TP/SL −18% / −11%); ≥10 buys & ≥1.5× at 60 s: −3% / −34%; post-snipe dip: −30% / −12%; one-off creator: −41% / −23%; LONG venue: −78% / −30%. Nothing is positive in both halves. Full table in `data/derived/launch_replay_0903.txt`.

**Graduation, the one predictable thing**: P(graduate | ≥50 buys in 5 min) = 34% fit / 30% holdout; P(graduate | ≥2 quote units and buys ≥ 2× sells by 5 min) = 52% / 33%. It does not pay: buying on that signal at 5–15 minutes is −21% to −24% because the curve price already carries the progress, and buying at the second liquid print after graduation returns +4% (60 s), +7% (5 min), +7% (15 min), +9% (60 min) mean before fees with CIs from −5% to +26%, medians −5% to −30%, 32% reaching 2× and 14% reaching 5× afterwards: a fair lottery, not an edge.

**What the playbook filters actually do here**: "avoid serial deployers" is a real filter (one-off creators' launches double three times as often after the first minute) and "buy the ones with the most early buyers" raises the odds of a graduation from 5% to 30%; neither turns a −30% trade into a positive one, because the snipe tax hands the first five seconds to the creator, the curve's own price rise is what the early buyers are paying for, and the exit liquidity for a scalper is the next buyer in a stream where 92% of launches end below their first print. Dev-holding, bundle and top-holder filters were not computable per launch without holder snapshots, but the creator's initial buy (the on-chain equivalent of "dev holdings") is, and it does not separate winners either.

**Verdict on round 4**: filtering new launches and scalping them has negative expectancy on this chain under every rule tried, on the full universe, on both halves of the day, with realistic costs. That closes the last untested branch of the brief. The measured, positive, retail-executable expectancy in this repository is still only the funding carry of section 11.5, and the structural seats (creator fees, buybacks) remain the house's.

### 12.1 Addendum: the "Viral Coin Sniping" cheat sheet's entry, as written

A four-page PDF sold as a lead magnet for a paid Discord ("Viral Coin Sniping", "we help traders reach 5 figs a month") describes one entry: watch new and migrated coins, wait for a hype signal, then confirm momentum before entering: holders rising fast (5–10 per tick), five-minute volume rising, chart not already crashed. No exit, sizing or stop is given. `src/analysis/vcs_rule_test.py` runs that entry on every Uniswap v4 pool that opened on Sep 3 with candles built from the day's own swaps (17,054 pools with a priced quote side; 8,569 with any swaps; 3,882 with twenty or more): per minute after the pool's first swap, at least five buy swaps in the minute (the holder proxy), the last five minutes' volume above the previous five and at least $10k, the close within 10% of the pool's high so far; first qualifying minute per pool; entry at the next swap; exits at 15, 30 and 60 minutes or +50%/−30% inside the hour; a pool with no later swap exits at half its last price; costs 3% plus a $300 clip's impact against a quarter of the five-minute volume, capped at 10%. Output `data/derived/vcs_rule_0903.txt`.

| cohort | n | 15 min: mean [CI], median, win | 60 min | TP +50% / SL −30% |
|---|---|---|---|---|
| all qualifying pools | 275 | +0.2% [−22, +38], −20%, 28% | −0.1% [−26, +39], −40%, 25% | −8.3% [−13, −4], −31%, 38% |
| graduated Pons V2 ("migrated") | 69 | −11.1% [−25, +4], −21%, 30% | −19.7% [−35, −1], −33%, 29% | −10.0% [−19, −1], −37%, 38% |
| launched on v4 (pads, LONG) ("new") | 206 | +3.9% [−25, +60], −20%, 28% | +6.4% [−29, +59], −41%, 24% | −7.8% [−13, −3], −19%, 38% |
| fit, 00–12 UTC | 122 | +17.7% [−29, +122], −25%, 30% | +31.3% [−29, +114], −53%, 28% | −7.2% [−14, −1], −32%, 42% |
| holdout, 12–24 UTC | 153 | −13.9% [−22, −5], −15%, 27% | −25.2% [−35, −16], −36%, 23% | −9.3% [−15, −4], −29%, 35% |
| ≥ 10 buys in the minute | 220 | +5.1% [−22, +51], −23%, 28% | +2.0% [−31, +54], −44%, 24% | −9.2% [−14, −4], −35%, 37% |

The confirmed-momentum entry buys the top of the first wave: the median trade loses 20–40% within the hour, one trade in four is positive, the take-profit/stop version loses 8–10% with the interval entirely negative, and the only positive means are two or three morning pools that ran, which the confidence intervals cannot separate from zero; the afternoon is negative on every exit. The "migrated" branch is the worst. It is the same result as the rest of section 12, with the sheet's own filters.

## 13. Round 5: the creator's seat, priced exactly and audited

Every filter and scalp in section 12 loses. Someone is on the other side of those trades in the first minute of a launch. Section 11.6 measured the creator seat only as a fee base rate. This round prices it as a strategy on the mechanics of the Pons V2 curve, then audits it against the launchers' own wallets and the identity of their first buyers.

**Mechanics that make it computable.** The creator's initial buy is part of the creation transaction and is the only trade in the launch block (no latency race, no 99%-decaying snipe tax, which hits buys in the next five seconds). All supply sits on a deterministic bonding curve; selling walks the same curve back, so the quote a creator can take out for their tokens at any moment equals what the most recent buyers paid for the top slice of sold supply, minus the 1% fee. `src/analysis/creator_seat.py` replays that for the 6,108 launches of 12:00–18:00 UTC on Sep 3 and detects the creator's sale as the first sell that eats into the launch-block layer (only the holder of that layer can do it); fees are 0.7% of curve volume. `src/collect/pull_quotes.py` reads each launch's quote asset from its creation receipt (ETH 43%, USDG 29%, NVDA 24%, the rest gold, RDDT, SPY, MU and other stock tokens); `pull_first_buyers.py` fetches the senders of the first five buys after the creator's on every launch (21,371 transactions); `bundle_check.py` clusters them.

**Results in stake units (fit = 12:00–15:00, holdout = 15:00–18:00)**

| Creator class | n | fees | sale, as actually timed | fees + sale, fit | fees + sale, holdout | launches ending ≥ 0 | median time to sale |
|---|---|---|---|---|---|---|---|
| serial (≥10 launches/day) | 3,074 | +5.7% of stake | +12% | +10% | +22% | 99% | 13 s (p90 54 s) |
| 2–9 launches/day | 1,147 | +17% | +11% | +32% | +25% | 99% | < 1 min |
| one-off | 1,887 | +51% | +56% | +69% | +137% | 99% | 1 min |

**The audit.** Three checks were run before believing those numbers.

1. *Launchers' wallets.* Net ERC-20 flow over the whole of Sep 3 for the six busiest creators: +$157, −$16, +$146, $0, −$1,514, −$7. Their stakes are recycled hundreds of times (0x7de5b9c8: 122.37 WETH in and 122.37 out, $281,544 USDG in and out, 158 launches in six hours). Whatever they earn does not stay on the launching wallet, and on these wallets it rounds to zero. (Native ETH balances could not be checked: the public RPC has no archive state.)
2. *Who buys first.* Among the first five buyers of serial launchers' tokens, 55% are wallets that recur as early buyers across ≥3 launches of the same creator (bundles), 18% are sniper bots (wallets that are early buyers on ≥10 different creators' launches), 27% other; 77% of serial launches, and 88–97% of the eight busiest launchers' launches, have a bundle wallet among the first buyers. One-off creators have none by construction; their first buyers are 38% sniper bots and 62% others. 185 sniper-bot wallets were identified; the largest bought 953 launches from 254 creators in six hours.
3. *Expectancy by counterparty.* Launches whose first buyers include the creator's own bundle: +13% of stake (fees +5, sale +8), stake ≈ 7.2 units. No bundle but a known sniper bot among the first buyers: +55% (fees +14, sale +40). No bundle and no known bot: +37% (fees +26, sale +11). One-off creator, no bundle: +109% of stake (fees +52, sale +57), median +19%. Nobody else bought: 0%.

**Results in dollars (4,874 launches with a priced quote; six-hour window)**

| Cohort | n | stake / launch | fees / launch | sale / launch | total, 6 h | mean / launch | median | p90 | share ≥ $0 |
|---|---|---|---|---|---|---|---|---|---|
| all creators | 4,874 | $439 | $40 | $76 | $562k | $115 | $12 | $145 | 99% |
| serial ≥10/day | 2,245 | $669 | $38 | $76 | $255k | $114 | $10 | $156 | 99% |
| own bundle among first buyers | 1,761 | $670 | $37 | $66 | $182k | $103 | $12 | $143 | 99% |
| one-off (no bundle) | 1,740 | $238 | $44 | $93 | $238k | $137 | $14 | $162 | 99% |
| 2–9/day | 889 | $252 | $35 | $42 | $69k | $78 | $11 | $105 | 98% |
| nobody else bought | 433 | $237 | $3 | −$2 | $0.4k | $1 | $0 | $2 | 91% |

**Reading.** For serial launchers the seat is mostly a machine: their own wallets buy their launch in the first seconds (the sale is circular), the fake activity pulls in sniper bots and organic buyers, and their income is the 0.7% fee on that volume; their launching wallets net roughly nothing because the money is swept elsewhere and the bundle wallets carry the losses on the other side of the sale, so their true margin is unmeasurable from here and is at most the fee line. For a one-off creator the seat is real and simple: stake $100–240 in the launch block, sell into the first strangers within a minute, keep 0.7% of everything after; mean $137 and median $14 per launch on a $1 launch fee, with a floor of −1% of stake when nobody buys. Across the six hours one-off creators took $238k from bots and organic buyers.

**What it is, honestly.** This is the one mechanism found in this repository that pays a newcomer with no audience, no allocation and no price prediction more than a yield. It is not a trade; it is a launch bot, and it exists because 185 sniper bots auto-buy launches at a loss. Its capacity is their appetite (they bought a few thousand launches in six hours), it is diluted by every additional launcher (28,000 launches a day already), the fomo app and Pons can rate-limit or tax it, gas is sponsored only until early October, one-off wallets in the sample may include operators rotating fresh wallets (which would mean the "one-off" cohort is partly bundled too), and the whole thing ends the day the bots stop. It is also the spam that the chain's 0.077% survival rate describes.

**Forward test (frozen).** First, at zero cost, rerun `creator_seat.py`, `pull_first_buyers.py` and `bundle_check.py` on a fresh day to confirm the one-off cohort still clears +$100 mean and ≥ 95% non-negative. Then a launch bot with a fixed $100 stake in ETH, a sell 10 seconds after launch or when curve proceeds reach 1.5× the stake, 50 launches with names drawn from the day's trending list, a hard stop if the first 20 average below +$20, and the fee share left to accrue.

### 13.2 The fee share on its own (no initial-buy sale)

The creator's income has two parts and they are different things: the sale of the launch-block buy (the dump, sections 13–13.1) and the 0.7% share of every trade on the token, which the launchpad pays whether or not the creator ever sells. Isolating the fee share for one-off creators across the five windows (fees counted only inside each six-hour window; a token that keeps trading after graduation keeps paying, which is not included):

| window | n | mean fee / launch | median | p90 | p99 | launches covering the $1.22 launch fee | > $10 | > $100 | top 5% share of fees |
|---|---|---|---|---|---|---|---|---|---|
| Aug 12 | 331 | $12 | $3.1 | $14 | $268 | 75% | 13% | 3.6% | 65% |
| Aug 20 | 205 | $17 | $2.1 | $35 | $256 | 58% | 21% | 4.4% | 61% |
| Aug 27 | 1,294 | $38 | $6.7 | $76 | $517 | 81% | 43% | 8.0% | 50% |
| Sep 2 | 1,926 | $38 | $7.1 | $99 | $448 | 93% | 44% | 9.9% | 42% |
| Sep 3 | 1,740 | $44 | $10.8 | $115 | $404 | 89% | 51% | 12.2% | 36% |
| pooled | 5,496 | $37.6 | $6.8 | $97 | | 87% | | | |

Launches with a tiny or no initial buy (< $25) still earn $9–22 mean, $0.3–2.8 median per launch: the fee needs no stake, only the $1.22 launch fee. Creators who did not sell inside the window earned more fees ($70–165 mean), partly selection (tokens that ran) and partly because a token whose creator has not dumped keeps trading. On Sep 3, the 280 launches that graduated to a pool earned $203 mean ($151 median) in curve-phase fees against $23 ($8.5) for the rest, and were 29% of all creator fees; their pool-phase fees afterwards are not counted here.

So the fee share alone is a lottery ticket priced at $1.22 with a mean payout of $12–44 depending on the day's flow, a median of $2–11, and 58–93% of tickets paying back the fee, pooled over all initial-buy sizes. It requires no dumping; whether it requires a stake, and what it is worth per wallet rather than per launch, is section 13.3, which cuts these means down considerably. Measured here as a finding; `src/analysis/creator_fee_tracker.py` reads any creator address's launches, curve volume and accrued fee share from the chain, without keys or transactions.

### 13.3 How profitable the fee share is without the dump

Section 13.2 pooled every one-off creator. Splitting them by the size of the initial buy, pricing the no-dump version (the stake is kept and marked at the end of the window at its LIFO exit value), and splitting by how many launches the wallet made that day gives the number that applies to a person who follows the runbook's rules (`src/analysis/creator_fee_profitability.py`, output `data/derived/creator_fee_profitability.txt`). Two facts first: no creation among the 48,048 in the five windows had a zero initial buy (the smallest used is 0.00001 ETH, two cents; whether the contract accepts zero is untested), so the "no-stake" version is the bucket with an initial buy under $5; and the fee counted is the window's curve-phase fee only, as in 13.2.

**(a) Fee share per launch by initial buy, one-off creators, mean (median), USD.**

| window | < $5 | $5–25 | $25–100 | ≥ $100 |
|---|---|---|---|---|
| Aug 12 | $5.3 ($0.03), n = 38 | $13.0 ($1.1), n = 30 | $5.8 ($3.4), n = 193 | $34 ($4.5), n = 69 |
| Aug 20 | $19.0 ($0.05), n = 17 | $18.5 ($0.6), n = 21 | $11.4 ($0.8), n = 101 | $26 ($6.8), n = 65 |
| Aug 27 | $22.6 ($2.3), n = 40 | $21.8 ($2.4), n = 198 | $31.4 ($3.4), n = 556 | $53 ($26), n = 464 |
| Sep 2 | $9.8 ($2.7), n = 149 | $25.8 ($2.9), n = 218 | $30.1 ($4.5), n = 399 | $45 ($13), n = 1,095 |
| Sep 3 | $4.3 ($1.1), n = 133 | $24.7 ($3.4), n = 161 | $47.2 ($5.8), n = 380 | $53 ($29), n = 945 |

The fee rises with the stake because the bots select launches with a real launch-block buy: on the peak day the dust launches earned the least of any window. A 20-launch bootstrap batch of dust launches nets $60–420 mean after launch fees, $30–390 median, with the single best launch 36–61% of the batch's fees.

**(b) No dump: fee share plus the initial buy marked at the end of the window, minus the launch fee, per launch: mean / median / share above zero.**

| window | < $5 | $5–25 | $25–100 | ≥ $100 |
|---|---|---|---|---|
| Aug 12 | +$3.7 / −$1.2 / 34% | −$1.0 / −$13 / 13% | −$55 / −$57 / 2% | −$152 / −$122 / 12% |
| Aug 20 | +$16.5 / −$1.2 / 18% | −$0.5 / −$13 / 24% | −$33 / −$44 / 8% | −$158 / −$145 / 15% |
| Aug 27 | +$20.6 / +$0.7 / 55% | +$4.7 / −$17 / 22% | +$0.8 / −$40 / 13% | −$491 / −$178 / 7% |
| Sep 2 | +$7.5 / +$0.2 / 52% | +$10.7 / −$15 / 20% | −$4.6 / −$38 / 19% | −$248 / −$168 / 6% |
| Sep 3 | +$1.7 / −$1.2 / 38% | +$14.4 / −$11 / 33% | +$25.9 / −$41 / 27% | −$240 / −$157 / 9% |

A kept stake of $25 or more loses more than its fee earns on every day (the stake ends 50–90% down; the fee is 5–50% of it), so the higher fee of the staked cohorts in (a) and 13.2 is bought with capital that is lost unless it is sold into the first buyers, which is the dump of 13–13.1. The $5–25 bucket is a coin flip around zero with a negative median. Only the dust bucket is positive in mean, and its median is the launch fee lost.

**(c) Fee share per launch by the wallet's number of launches that day, initial buy under $25: net of the launch fee, mean (median fee).**

| window | 1 launch (one-off) | 2–9 | 10–49 | ≥ 50 |
|---|---|---|---|---|
| Aug 12 | +$7.5 ($0.34), n = 68 | −$0.3 ($0.05), n = 22 | | |
| Aug 20 | +$17.5 ($0.50), n = 38 | −$1.0 ($0.04), n = 30 | −$1.1 ($0.00), n = 44 | −$1.2 ($0.02), n = 119 |
| Aug 27 | +$20.7 ($2.35), n = 238 | +$3.6 ($1.34), n = 109 | −$0.3 ($0.34), n = 60 | +$0.3 ($0.34), n = 191 |
| Sep 2 | +$18.0 ($2.79), n = 367 | +$3.6 ($1.54), n = 185 | +$2.1 ($0.36), n = 124 | −$0.4 ($0.07), n = 131 |
| Sep 3 | +$14.3 ($2.38), n = 294 | +$5.3 ($1.51), n = 137 | −$0.2 ($0.32), n = 22 | −$0.7 ($0.03), n = 19 |

The second to ninth launches from the same wallet earn a quarter or less of the first, the tenth onward about the launch fee or less, and the ≥ 50 cohort nothing. This is the bots' first-time-creator filter seen from the creator's side (the rule in section 14 filters `prior_launches == 0` for the same reason). So the one-off means apply to one launch per wallet per day; a batch of twenty from one wallet is the 2–9 and 10–49 cohorts, $0–5 net each, and the only way to launch twenty one-offs is twenty fresh wallets, which is the serial-launcher pattern of 13.1 and excluded here.

**Bottom line.** A person with one wallet who launches one token a day with a dust initial buy, follows the no-dump and no-impersonation rules, and claims the fee expects $3–21 a day in mean and $0–2.7 in median, with a third to a half of days earning nothing beyond the $1.22 lost. Launching more from the same wallet adds roughly nothing per extra launch; keeping a real stake turns it negative. The no-dump creator seat is worth a few dollars a day, and the runbook is amended to say so. A live reading of the amended gauge on Sep 5, 12:00–14:00 UTC (1,228 launches), agreed: single launch with a dust buy $3.49 mean / $0.19 median (n = 66, 35% covering the fee); single launch with a stake $59 / $15 (n = 510); second to ninth launch $2.65 / $0.66 (n = 70).

## 14. Round 6: the sniper bots, and the seat that actually wins

Section 12 showed every scalp entered after the snipe window losing, section 13 showed creators collecting from the first minute of every launch, and 185 sniper-bot wallets were identified as the payers. Bots do not run 953 launches a day at a loss for long, so this round reconstructed what each of them actually made.

**Method.** For the fifteen busiest sniper wallets, every ERC-20 transfer in and out during 12:00–19:00 UTC on Sep 3 (`src/collect/pull_bot_transfers.py`), joined by transaction hash to the Pons V2 curve Buy/Sell events (quote in, tokens out) and to the Uniswap v4 swaps for tokens that had graduated (`src/analysis/bot_pnl.py`). Quote legs converted to dollars per launch's quote asset. Unsold tokens marked at zero.

| bot | launches | spent | received | net (unsold = 0) | ROI | win rate | unsold | buy time after launch p10 / median | median hold | $/launch |
|---|---|---|---|---|---|---|---|---|---|---|
| 0xbc46a7f0 | 175 | $107,515 | $138,346 | **+$30,831** | +28.7% | 39% | 0% | 0.3 s / 0.8 s | 7 s | $614 |
| 0x9eed092b | 225 | $54,688 | $61,696 | +$7,008 | +12.8% | 31% | 0% | 1.9 s / 2.8 s | 21 s | $243 |
| 0xbbcea8b6 | 125 | $41,279 | $43,765 | +$2,486 | +6.0% | 26% | 0% | 1.6 s / 2.1 s | 3 s | $330 |
| 0xddf8cbf8 | 220 | $35,140 | $35,586 | +$445 | +1.3% | 20% | 2% | 1.1 s / 1.6 s | 89 s | $160 |
| 0xff335b2c | 137 | $14,214 | $12,034 | −$2,180 | −15% | 18% | 2% | 0.8 s / 1.3 s | 185 s | $104 |
| 0x03c32391 | 352 | $14,396 | $11,686 | −$2,710 | −19% | 5% | 11% | 1.3 s / 2.9 s | 84 min | $41 |
| 0xd91abf0e | 1,962 | $17,706 | $9,931 | −$7,775 | −44% | 1% | 20% | 4.9 s / 171 s | 34 min | $9 |
| 0xd4b453fb | 1,073 | $17,680 | $5,455 | −$12,224 | −69% | 2% | 45% | 4.7 s / 48 s | 41 min | $16 |
| 0x31ee40cd | 12 | $12,692 | $776 | −$11,916 | −94% | 17% | 0% | 1.6 s / 1.7 s | 24 min | $1,058 |

The line between winners and losers is not selection, it is time: buy in the first second, sell within ten. The fastest bot avoids launches with bundle wallets (27% of its picks vs 40% of launches; on those it is −6%, on the rest +31%), prefers first-time creators with small initial buys, and holds seven seconds. On the fitting hours it made +7% and on the holdout hours +31% (per-launch mean +9% [−1, +21] and +24% [+8, +47]).

**The seat, simulated on every launch** (`src/analysis/sniper_sim.py`; 6,108 V2 launches, 12:00–18:00; fit 12–15 h, holdout 15–18 h). Rule, everything computable at launch time: the creator has no prior launch today (a real-time proxy for "no bundle"), the curve is ETH-quoted, buy min(3% of supply, $300) at the price of the first non-creator trade (what the fastest bot pays), sell 7 s later into whoever bought after (exact bonding-curve exits, LIFO on the layers above, 1% fee each way, remainder refunded by the curve at cost).

| rule | half | n | net | on | pooled | per-launch mean [95% CI] | median | win | top 5% of launches | worst |
|---|---|---|---|---|---|---|---|---|---|---|
| all launches with a buyer within 3 s | fit | 1,760 | +$28,689 | $260,818 | +11.0% | +10.5% [+7, +15] | −2% | 42% | $42k | −$303 |
| | holdout | 1,413 | +$29,276 | $217,454 | +13.5% | +15.2% [+10, +20] | −2% | 42% | $36k | −$301 |
| creator's first launch today | fit | 840 | +$24,896 | $120,038 | +20.7% | +19.8% [+14, +27] | −2% | 46% | $20k | −$303 |
| | holdout | 751 | +$34,002 | $111,798 | +30.4% | +31.1% [+24, +40] | −1% | 48% | $20k | −$301 |
| creator has a prior launch today | fit | 920 | +$3,793 | $140,780 | +2.7% | +2.0% [−3, +7] | −5% | 39% | | |
| | holdout | 662 | −$4,726 | $105,655 | −4.5% | −2.8% [−10, +4] | −10% | 36% | | |
| **first launch today & ETH-quoted** | fit | 664 | **+$26,452** | $96,950 | +27.3% | +26.7% [+20, +34] | −2% | 46% | $17k | −$303 |
| | holdout | 647 | **+$31,168** | $98,205 | +31.7% | +32.8% [+24, +41] | −1% | 48% | $17k | −$301 |
| same, hold 3 s | fit / holdout | 664 / 647 | +$26,357 / +$28,496 | | +27.2% / +29.0% | +27.1% / +30.6% | −1% / +1% | 48% / 53% | | |
| same, hold 15 s | fit / holdout | | +$8,847 / +$19,933 | | +9.1% / +20.3% | | | | | |
| same, $100 cap | fit / holdout | | +$17,659 / +$22,474 | $67k / $65k | +26.3% / +34.4% | | | | | −$101 |
| same, creator's initial buy ≥ 5% of supply | fit / holdout | 124 / 159 | +$12,408 / +$9,320 | | +58.9% / +32.5% | +62% / +35% | +7% / +2% | 56% / 51% | | |
| NVDA-quoted | fit / holdout | 81 / 23 | +$98 / +$1,586 | | +0.9% / +52.8% | | | | | |
| USDG-quoted | fit / holdout | 54 / 50 | −$1,138 / +$1,855 | | −17.0% / +29.6% | | | | | |

**Sensitivity: it is a latency race.** Same rule, same launches:

| what changes | fit | holdout |
|---|---|---|
| first in line (baseline) | +27.3% | +31.7% |
| pay 10% more than first-in-line (second in the block) | +17.8% | +22.0% |
| pay 25% more | +6.3% | +10.1% |
| pay 50% more (third in line) | −7.7% | −4.5% |
| land 0.5 s late | −5.0% | −4.2% |
| land 1 s late | −4.7% | −3.1% |
| land 2 s late | −8.7% | −2.5% |
| two equal snipers sharing the exit (6% of supply) | +26.6% combined | +28.4% combined |

Half a second decides the sign. The first block after creation is worth +27–33% a trade; the tenth block is worth nothing. Two wallets can share the first block (the launch caps are per wallet) and still both earn.

**What it is, honestly.** This is the seat the brief was looking for in its economics: measured on 1,311 qualifying launches with a hindsight-free rule, positive in both halves of the day with confidence intervals well above zero, consistent with the realized P&L of the bot that actually holds the seat, turnover of seconds, a hard floor of one stake per launch, and $50–60k of profit per six hours at a $300 cap on Sep 3's flow. It is not available to a person with an app: it needs a bot that sees the creation transaction on the sequencer feed and lands a buy in the next 100-millisecond block ahead of 0xbc46a7f0, then sells seven seconds later. It is adversarial (the profit is the slower bots' and humans' losses), it is capacity-limited (two or three fast wallets can share the block; the fourth is at −5%), it lives on sponsored gas until early October and on a launch flow of ~28,000 a day, and it is the kind of edge that a single faster competitor or a protocol change (a real snipe tax, a longer launch-block lock) removes overnight. The first-block seat on Robinhood Chain is the treasure; the question is only whether you can be first.

### 14.2 Regime test: the same rules on five windows across the fee cycle

The Sep 2 and Sep 3 windows sit in the launchpad's fee-peak week. Three more six-hour windows (12:00–18:00 UTC) were pulled to cover the cycle: Aug 12 (Pons V2's second week), Aug 20 (the fee trough, $0.25M of Pons fees that day), Aug 27 (the ramp). Nothing in the rules was changed. Outputs: `data/derived/sniper_sim_extra.txt`, `data/derived/creator_seat_extra.txt`.

| window | Pons fees that day | first-in-line rule, fit / holdout (pooled) | per-launch CIs | second-in-line (pay 10% more) | one-off creator seat: mean / median $ per launch, share ≥ $0 |
|---|---|---|---|---|---|
| Aug 12 | ≈ $0.5M | **−13.1% / −13.6%** (n = 106 / 123) | [−20, −7] / [−18, −8] | −17% / −18% | $14 / $3, 95% (n = 331) |
| Aug 20 | ≈ $0.25M | +3.9% / +8.0% (n = 72 / 48) | [−6, +15] / [−6, +21] | −1% / +2% | $35 / $1, 96% (n = 205) |
| Aug 27 | ≈ $2.3M | −2.2% / −0.7% (n = 398 / 444) | [−8, +5] / [−5, +7] | −8% / −7% | $78 / $9, 99% (n = 1,294) |
| Sep 2 | ≈ $6.0M | +0.4% / +15.3% (n = 820 / 812) | [−5, +5] / [+8, +21] | −7% / +7% | $100 / $11, 100% (n = 1,926) |
| Sep 3 | $6.4M | **+27.3% / +31.7%** (n = 664 / 647) | [+20, +34] / [+24, +41] | +18% / +22% | $137 / $14, 99% (n = 1,740) |
| Sep 4, live shadow (20 min) | | +12.3% (n = 34) | [−5, +33] | | |

**Correction (section 19).** The simulator valued a hold that ended without a trade *after* the next event instead of at the seven-second mark, which mostly charged the sniper for creator dumps that happened a minute after it had sold. With the exit valued at seven seconds the first-in-line rule reads, fit / holdout: Aug 12 +0.7% / −3.7%, Aug 20 +9.2% / +11.3%, Aug 27 +5.5% / +8.9%, Sep 2 +10.0% / +24.7%, Sep 3 +33.0% / +37.7%; landing 0.5 s late Sep 3 −0.9% / −4.5%. The seat is positive on four of five windows and flat in the launchpad's second week, which strengthens the peak-flow reading below rather than reversing it: the size of the edge is still the day's flow.

**Verdict.** The first-block seat is not a structural edge; it is a peak-flow phenomenon. It is significantly positive only on the two peak days, flat on the ramp, and significantly negative in the launchpad's early weeks. Its sign tracks the day's flow of slower buyers, which tracks the launchpad's fee cycle, which was driven by the gas subsidy and the mania. Second-in-line is positive on exactly one day of five. The incumbent bot's realized P&L (above) was measured on the best of these days.

The creator seat never goes negative in aggregate, because the curve refunds the stake, so it is structurally a floor plus a tail; but the tail is the flow: at the trough the median launch made $1 and the mean $35, at the peak $14 and $137. Both seats are the launchpad's flow seen from two sides, and both shrink to nothing when the flow does. Sections 11–14 stand as measured; the executive-summary claims for these two seats are amended to "peak-flow, regime-dependent", and the repository's recommendation returns to what survived every window: nothing directional on this chain has a measured edge across regimes.

**Out of sample: Sep 2, 12:00–18:00, same rule, nothing changed** (`data/derived/sniper_sim_0902.txt`): 340,393 curve events, 5,580 launches. First-in-line: +0.4% on $120,723 in 12–15 h (per-launch mean +0.4% [−5, +5]) and +15.3% on $118,240 in 15–18 h (+14.1% [+8, +21]); +7.8% over the six hours, net +$18.6k. Paying 10% more: −6.6% / +6.9%; landing 0.5 s late: −11.8% / −9.5%; two snipers sharing the block: +4.4% / +16.6% combined. By hour, both days:

| hour (UTC) | Sep 2 | Sep 3 |
|---|---|---|
| 12 | −9.5% (n=348) | +25.4% (n=180) |
| 13 | +11.1% (247) | +39.9% (263) |
| 14 | +3.8% (225) | +14.3% (221) |
| 15 | +12.8% (210) | +18.5% (273) |
| 16 | +16.2% (389) | +45.4% (246) |
| 17 | +16.2% (213) | +34.1% (128) |

Eleven of twelve hourly buckets are positive for the first-in-line seat; the one negative hour is the low-flow start of Sep 2. Sep 3 was the fee-peak day ($6.4M of Pons fees, section 10); Sep 2 was ordinary. The seat's size is the day's flow of slower buyers; its sign is the block position. Everyone one block behind loses on both days.

**Forward test.** `src/strategy/sniper_shadow.py` watches every new Pons V2 creation live and, 25 seconds later, scores what the rule would have returned from the actual curve events, logging to `data/derived/sniper_shadow.jsonl` without capital; its first eligible launch scored −$1.4 on a $131 stake with the entry at 2.4 s, which is the point: the shadow log measures the rule as if first in line, and the live gap between that and what a real bot lands is the latency you would have to buy.

## 15. Round 7: the second clip ("scalp the highs, tech-stock memes early, trench with a tracker")

The transcript claims three strategies from a trader who "bought a Porsche" and holds "about a hundred thousand dollars worth of tokenized-stock memes". The holding is a mark-to-market bag of the kind section 2 audits. The three strategies were tested on the data already in the repository plus one new pull.

### 15.1 "Scalp the highs of a viral meme": buy at $10M, sell at $15M

`src/analysis/viral_high_scalp.py`, output `data/derived/viral_high_scalp.txt`. Universe: the 737 tokens with GeckoTerminal 15-minute candles and a known supply (676 on Robinhood Chain), Jul–Sep 4; these are the leaderboard's own picks, i.e. survivors, which biases any momentum test upward. Signal at candle i using only candles ≤ i: FDV ≥ T, close is the highest close of the trailing 24 h, and the last hour's volume is at least 3× the trailing-24h hourly average (the "going viral" condition). Entry at the next open; exits take-profit +50% (the clip's $10M → $15M), stop −25% (assumed to fill first when both hit in one candle), time stop; costs 3% round trip. Fit = before Aug 10, holdout = after; CIs token-clustered.

| threshold | signals / tokens | TP +50% / SL −25% / 24 h: mean [CI], median, win | no exits, 4 h | no exits, 24 h | placebo (random candles above T), TP/SL 24 h |
|---|---|---|---|---|---|
| $1M | 1,308 / 200 | −2.8% [−4, −1], −5.4%, 30% | −4.9% [−6, −4] | +0.6% [−2, +4], median −4.2% | −2.3% [−3, −1] |
| $3M | 862 / 127 | −2.9% [−5, −1], −4.3%, 29% | −5.2% [−7, −4] | −1.5% [−4, +1] | −1.3% [−3, 0] |
| $10M | 464 / 62 | −1.5% [−4, +1], −3.6%, 29% | −3.3% [−5, −2] | −1.0% [−3, +2] | −1.0% [−2, +1] |

Fit and holdout halves are both negative for every row; the tighter TP +30% / SL −15% variant is −4% to −5%; dropping the volume condition (any new 24-hour high) is −3.1% to −3.3% on 2,583–3,867 signals. Before costs the hour after a viral high returns −1% to −2%: the new high is where the sellers are, and the signal does no better than random candles of the same tokens. The clip's literal rule, buy the first time a token crosses $10M and sell at $15M or −25% or 24 h, ran on the 58 tokens that ever crossed: +0.1% mean [−9, +10], −28% median, 55% stopped out, 34% hit the target. Zero expectancy on a survivor universe means negative on the real one.

### 15.2 "Catch the tokenized-stock memes early"

Two views. The leaderboard's own LONG stock-paired entries (section 3b) are the only venue bucket with a positive pooled realized return, +45% on 90 positions in 14 tokens, with a confidence interval of [−84%, +54%] and the sign carried by AI, the token the LONG co-founder and the #3 handle rode from the launchpad's first week.

The universe: every LONG launch in the eight-week factory census, 21,598 tokens, valued today on DexScreener (`src/collect/pull_dex_long.py`, `src/analysis/long_census.py`, `data/derived/long_census.txt`, snapshot `long_tokens_dex_2026-09-05.json.gz`). 1,711 (7.9%) have a pair today; 92 are above $100k FDV, 22 above $1M, 5 above $10M, one above $100M (AI, $270M, NVDA-paired, launched the week of Jul 13), none above $500M. By launch week, a $100 ticket on every launch, valued today with dead tokens at zero, at an initial FDV bracketing the Sep 3 replay ($21k p25, $67k median):

| launch week | launches | pair today | ≥ $1M | ≥ $10M | top token's share of the cohort's value | $100 a launch, today (FDV₀ $21k / $67k) |
|---|---|---|---|---|---|---|
| Jul 13 | 380 | 48 | 4 | 1 | 95% (AI) | ×35 / ×11 |
| Jul 20 | 4,365 | 126 | 3 | 1 | 71% (MOO) | ×0.43 / ×0.14 |
| Jul 27 | 1,279 | 36 | 0 | 0 | | ×0.05 / ×0.01 |
| Aug 3 | 252 | 11 | 0 | 0 | | ×0.10 / ×0.03 |
| Aug 10 | 327 | 16 | 1 | 0 | | ×0.81 / ×0.25 |
| Aug 17 | 432 | 22 | 1 | 1 | 98% (BONER) | ×5.1 / ×1.6 |
| Aug 24 | 4,031 | 183 | 6 | 0 | 18% | ×0.23 / ×0.07 |
| Aug 31 | 10,532 | 1,269 | 7 | 2 | 40% (MEME) | ×0.51 / ×0.16 |

Two of eight weekly cohorts pay, each on one token; the other six lose 50–99% of the stake. The first cohort is the launchpad's first week, the same July wave that section 10.2 found was the only period in which following leaders into fresh launches paid. On the one fully replayed day (Sep 3, 168 LONG launches with an initial FDV above $1k), 11% were at 2× or better six hours later and 1% at 10×, the median at ×0.99 of the initialization price, which nobody can buy at; entries at the first tradable price lose −11% to −48% (section 12). The surviving pairs are quoted in AI, AMC, SPCX, NVDA, GME, TSLA and AAPL tokens: the "tech stock" framing is the launchpad's pairing rule, not a selection edge.

### 15.3 "Trench for the 100× with a Twitter tracker"

There is no tweet-time feed in this repository, so the tracker itself is untested; the mechanism it feeds is not. A tracker delivers a contract address seconds after a poster's audience sees it, and the poster is in before both. That seat has been measured three ways: the app's own buy alerts (section 4, +2.5% median at one hour before costs, about zero after); leaders' entries into tokens under a day old with dead tokens at −100% (section 10.2, +326% mean in the July launch wave, −41% to −75% since mid-August, −55% throughout for big-audience posters); a fast follower entering two blocks behind the leader's swap (section 11.1, zero net at $250, −8% at $500); and every launch-time filter on the whole universe of a day (section 12, −10% to −48%). Testing a specific tracker would need paid X API access and would measure the same follower seat with a different latency.

### 15.4 Verdict

The three strategies are the poster's story told as a method. Momentum on a viral high has negative expectancy even on survivors; the tokenized-stock jackpot is one token in 21,598, from the launchpad's first week, held by insiders; tracker trenching is the follower seat, positive only in July. Nothing here changes the recommendation of sections 7, 12 and 14.

## 16. Round 8: the liquidity-provider seat, hedged

The only seat not priced in rounds 1–7 was the pool itself: supply liquidity to the mania token's pool, collect the swap fee, hedge the inventory with the perp short and collect the funding the carry of section 11.5 already measured. `src/analysis/lp_seat.py`, output `data/derived/lp_seat.txt`.

**Which pools.** Pons V1/V2 and LONG pools are Uniswap v4 pools with hooks; their protocol-owned liquidity sits in the locker, the 1% fee is routed to creator and protocol by the hook, and the v4 Swap events show a separate dynamic LP fee (0.31% on CASHCAT/USDG, 0.35% on PONS/USDG) whose recipient and whether outsiders may add liquidity at all were not established here. The clean case is the CASHCAT/WETH 0.3% Uniswap v3 pool (pre-Pons token, plain v3, anyone can LP), the pool section 11.4 used for cross-pool arbitrage.

**The denominator is not the TVL.** The pool's TVL is $3.4M, but liquidity is concentrated, and what a full-range position competes with is the in-range liquidity: read from every Swap event of Sep 3 (2·L·√P), its virtual full-range TVL is $13.3M (p10 $11.8M, p90 $14.2M). Sep 3 volume in the pool was $6.15M, LP fees $18.4k, so a full-range dollar earned 0.14% that day; the TVL proxy would have said 0.54%. Concentrating the position multiplies fee share and price-path loss by the same factor, so the ratio below does not change with the range.

**Fees versus the price path, per day, from 15-minute candles (56 full days, Jul 10 → Sep 4):**

| period | days | pool volume / day | fee yield / day, full-range $ at $13M virtual TVL | LP cost / day if rehedged every 15 min | realised daily vol | CASHCAT funding / day | net / day (fee + half funding − LP cost) |
|---|---|---|---|---|---|---|---|
| July | 22 | $5.8M | 0.13% | −1.10% | 28% | 0.44% | −0.75% |
| Aug 1–19 | 19 | $7.1M | 0.16% | −0.53% | 19% | 0.22% | −0.26% |
| since Aug 20 | 15 | $22.2M | 0.50% | −0.52% | 20% | 0.26% | +0.11% |
| all | 56 | $10.7M | 0.24% | −0.75% | 23% | 0.32% | −0.35% |

The LP cost is the loss versus rebalancing of a position whose delta is reset every 15 minutes (the sum of 2√(1+r)/(2+r) − 1 over 15-minute returns), which is the cost a hedged LP actually pays; the worst days were −3.5%, −2.8%, −2.8%. The funding line is what a short on the CASHCAT perp received, applied to the half of the position that is CASHCAT (the WETH half needs an ETH hedge at roughly zero funding). The fee yield applies today's in-range liquidity to past volume, which flatters the early periods if liquidity was thinner then. Hedge trading costs and the basis swings that gave the carry a −15% equity drawdown are not subtracted.

**Verdict.** The hedged LP seat on the most-traded mania pool is negative over the study and marginally positive only in the last fifteen days of peak volume, before costs it does not include. The launchpads keep the fee income on this chain in their own locked positions and hooks; an outside liquidity provider is paid less than the volatility costs. The seat is closed, with the same caveat as every other one here: it is the day's flow, seen from the pool.

## 17. Round 9: the consistent traders, from the whole app rather than the leaderboard

The instruction was to stop looking at the top handles and find consistent traders, including small ones, and pull their strategies from their trades. The leaderboard cannot do that (it ranks unrealized bags), so this round started from the chain: every wallet that trades through the fomo app is an ERC-4337 smart account whose operations are logged by the EntryPoint with the wallet as an indexed topic. That gives the whole app population without any ranking.

### 17.1 Method

* **Wallet universe.** `src/collect/pull_userops.py`: every UserOperationEvent in Sep 3 12:00–19:00 UTC: 37,142 operations, 11,738 wallets, 37,007 transactions.
* **Trades.** Each transaction joined by hash to the Pons V2 curve Buy/Sell events (section 12's pull), all 5.9M Uniswap v4 swaps of the day (section 12), and a new pull of all 1.85M Uniswap v3 swaps in the window (`pull_v3_swaps.py`), with pool metadata for 603,359 v4 pools since the chain's start (`pull_v4_init_all.py`) and v3 pools resolved by `token0()/token1()`. Quote assets: ETH, WETH, USDG plus 188 currencies that sit on 60 or more pools and have a stable price across them (stock tokens, PONS, AI, …), priced at the median of the day's own swaps; currency-to-currency swaps are ignored as conversions. 24,270 user transactions carry a priced trade; 229 swaps stay unpriced. `src/analysis/user_pnl.py`, output `data/derived/user_pnl_2026-09-03_12-19.txt`.
* **Histories.** For the 251 wallets that looked best in the window (top realized closers, top marked, everyone with five or more closed positions and a profit, the largest spenders), every operation from Jul 13 to Sep 5 (userOps filtered by sender, then the receipts) and the same pricing (`pull_wallet_history.py`, `wallet_history_pnl.py`): FIFO round trips per token, weekly realized P&L, hold times, entry ages (pool or curve age at the first buy), sizes, the unsold remainder marked at the wallet's last price. Proceeds of tokens the wallet did not buy inside the priced history are dropped, not counted.
* **Base rate.** The same for 120 wallets drawn at random from the 11,738.
* **Skill or beta.** `wallet_timing.py`: for every closed trip of the eight most profitable or most consistent wallets with 15-minute candles, the actual return against twenty placebo entries at random times within ±24 h of the real entry with the same hold; entry context (return before entry, position in the trailing-24h range); exit capture (share of the maximum favourable excursion taken).

### 17.2 One afternoon of the whole app

| | |
|---|---|
| wallets that traded | 11,738 (median 1 operation, p90 4, max 171) |
| wallets with a priced buy | 5,431 |
| spent / received | $5.04M / $1.57M |
| net, unsold tokens at zero | **−$3.47M** |
| net, unsold marked at the last price | +$0.17M |
| wallets net positive (marked) | 43% |
| wallets with ≥ 5 positions closed in the window | 145, of which 67 profitable |
| best realized closer | $4,482 (5 positions, 80% wins, $575 median clip) |
| best wallet with ≥ 5 closed and ≥ 60% wins | $471 |

Half of the transactions had neither a curve trade nor a v4 swap: they were v3 swaps (Pons V1 tokens, CASHCAT/WETH), which is why the v3 pull was needed. Seven hours is too short to call anyone consistent, so the window only chose whom to follow back.

### 17.3 Eight weeks: the candidates and the random sample

Realized P&L of the 251 candidates by week (closed round trips, the week a trip closed):

| week of | wallets active | share positive | sum | median | best wallet |
|---|---|---|---|---|---|
| Jul 13 | 33 | 18% | −$80k | −$718 | $7.5k |
| Jul 20 | 37 | 41% | −$117k | −$184 | $9.3k |
| Jul 27 | 35 | 31% | −$22k | −$212 | $12k |
| Aug 3 | 53 | 58% | −$12k | +$16 | $13k |
| Aug 10 | 61 | 41% | +$94k | −$5 | $86k (one wallet, STONKBROKER) |
| Aug 17 | 58 | 34% | −$14k | −$45 | $26k |
| Aug 24 | 140 | 68% | +$268k | +$155 | $71k |
| Aug 31 | 248 | 71% | +$950k | +$230 | $104k |

$1,065,621 realized in total; 89% of it in the week of Aug 31, the fee-peak week of section 10. These wallets were chosen for winning on Sep 3, so the weeks before Aug 24 are out of sample for them, and they lost in five of six. Four of the 251 were active five weeks or more with at most one losing week and $5k or more: 0x9aefc1f639 ($126k), 0xd121958a47 ($27k), 0xd4e2362235 ($21k), 0xcc93ea5fee ($8k). Only the first was consistent before the mania: +$7.3k, +$2.6k, +$2.7k, +$13.3k, −$2.1k in the five weeks to Aug 23, then +$6.6k and +$95k.

The random sample: 75 of the 120 wallets had a priced trade in eight weeks; median realized $0, mean $8, 44% positive, three above $1k, none above $5k. Seventeen were active three weeks or more, three of those were positive in three quarters of their weeks, and the best of them made $2,660. A fomo-app wallet's expected realized profit over the period is zero, and the "consistent" wallets of 17.2 are four in twelve thousand, chosen after the fact.

### 17.4 What the winners do

The eight most profitable or most consistent histories (`wallet_strategy_focus.txt`):

| wallet | realized | round trips | tokens | weeks act./pos. | win | entry age, median | entries < 1 h | hold, median | clip, median | exit return, median | top token's share |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0x9aefc1f639 | $126k | 707 | 55 | 7 / 6 | 64% | 6.2 d | 8% | 2.1 d | $49 | +15% | 34% (NUDES) |
| 0xcfe0b7ecc6 | $121k | 414 | 24 | 2 / 2 | 71% | 38.6 d | 0% | 29 h | $266 | +39% | 105% (PONS) |
| 0x97aea605e5 | $111k | 1,286 | 69 | 5 / 3 | 63% | 47 h | 16% | 27 h | $102 | +13% | 48% (NUDES) |
| 0xb28d1b5abb | $91k | 1,823 | 226 | 8 / 5 | 50% | 18 h | 10% | 6.6 h | $172 | 0% | 128% (STONKBROKER) |
| 0x78a1b7fc59 | $89k | 255 | 41 | 2 / 1 | 77% | 2.9 d | 0% | 28 h | $235 | +24% | 35% (BONER) |
| 0x7ea805d2f7 | $87k | 1,559 | 60 | 4 / 4 | 52% | 43 h | 2% | 34 h | $171 | +1% | 60% (microduck) |
| 0x6ac5e50fc4 | $63k | 2,153 | 72 | 8 / 6 | 47% | 3.0 d | 0% | 12 h | $195 | −2% | 62% (STONKBROKER) |
| 0xd121958a47 | $27k | 91 | 16 | 6 / 5 | 79% | 8.8 h | 4% | 7.3 d | $84 | +75% | 46% (NUDES) |

The profile is the same for all of them. They trade the memes the leaderboard trades (72–96% of their tokens are in `token_metrics.json`): NUDES, MOO, HMM, PONS, BONER, STONKBROKER, microduck, AI, CASHCAT. They are never first: 0% of entries inside ten minutes of a pool's creation and 0–16% inside the first hour; median entry age hours to weeks. They hold hours to days, buy in small clips and sell in many partials (0x9aefc1f639: 14 buys and 55 sells of MOO, 30 and 107 of HMM), and the profit is two or three tokens per wallet: the top token is 34–128% of realized P&L, and for the most consistent wallet the pre-mania weeks were wire and HMM, the mania weeks NUDES and MOO. Nothing in the profile is sniping, launch filtering or copy-trading; it is swing-trading the liquid names of the moment.

### 17.5 Skill or beta

Random timing on the same tokens over the same holds earns what they earned. Pooled over 6,701 candle-covered round trips, the actual return's median is +7.0% and the placebo's +4.5%; the timing alpha's median is −3.5% and only 44% of trips beat their placebo. Per wallet: −0.1%, +6.5%, +1.9%, −3.9%, −5.2%, +16.1%, −16.0%, +0.9%. The one clearly positive number belongs to a two-week wallet (0x78a1b7fc59, 69% of 170 trips above placebo, momentum entries in the mania). Exit capture, the share of the maximum favourable excursion actually taken, is 14–81% by wallet, mostly under 50%. Entry styles differ (four buy strength in the top third of the 24-hour range, one buys weakness in the bottom third) and the outcome does not: the return is the token's return over the hold, and the token was chosen in the two weeks when the liquid memes went up 3–30×.

The dip buyer, 0x6ac5e50fc4, is the one wallet whose behaviour reads as a rule: entries after −8% over 6 h and −10% over 24 h, 24% below the 24-hour high, in the bottom third of the range 64% of the time, hold 12 h median, 41 round trips a day, +0.9% median and +5.6% cost-weighted timing alpha over 1,528 trips, profitable in six of eight weeks before and during the mania. Its ledger says something else: $1.3M bought for $63k realized (4.8% of turnover), median trip −1.7%, and its ten best trips are 117% of its profit, two of them STONKBROKER for $48k. It is a churner who caught one token.

### 17.6 The extracted rule, tested

`dip_rule_backtest.py` puts that behaviour into a rule: pool at least a day old, trailing-24h volume ≥ $200k, close ≥ 20% below the trailing-24h high and in the bottom third of the range, one entry per token per 6 h, 3% costs. On the 676 Robinhood tokens with candles (the leaderboard's memes, survivors): hold 12 h +4.7% mean [+2, +8] on both halves of the period, hold 24 h +7.7%, medians −5% to −9%, win 40%, placebo +1.2%; every take-profit/stop variant negative; liquid names only (≥ $1M) +0.9% [−2, +3]. On a hindsight-free universe, every Uniswap v4 pool of Sep 3 with candles built from the day's own swap stream and no survivor selection (`dip_rule_v4day.py`): −0.5% to −7.7% mean, medians −8% to −20%, win 30–38%, no better than placebo, at $300 and $1,000 clips. This is section 5's result again: the bounce exists in the names that survived and not in the names one could have chosen at the time.

### 17.7 Verdict

Consistent traders exist in the sense that four wallets in about twelve thousand were profitable in nearly every week they traded, and one of them made $24k in five ordinary weeks and $102k in the two mania weeks. Their method is legible from their trades and it is not a secret: be long the liquid memes of the moment, size small, sell in pieces. What it is not is an edge that transfers: random timing on their tokens does as well as they did, their profit sits in two or three tokens each, the rest of the population's expected profit is zero, and the one rule-shaped behaviour fails out of sample. Nobody sampled is making $30–100k a month from a repeatable rule; the wallets that made that much made it in two weeks on the right bags.

## 18. Round 10: the influencer-catalyst scalp, tested as described

Two videos by a trader who says he turned $1,000 into millions describe one method: identify the most influential and trustworthy people in the market, wait for them to do something (a buy, a launch, a listing, a post), enter the second it happens with size, set a tight stop (his example: bought at $900k market cap, stop at $700k, −22%), and sell into the crowd that arrives after you (his average exit about +50%; a second example +38% with a trailing stop), ten to twenty trades a day, only in high-volume regimes. This repository has the two things needed to test it exactly: 276 leaderboard buys matched to their exact pool swaps (section 11.1) and the real-time alert feed of the app he recommends.

### 18.1 Who moves the market

`kol_swap_events2.jsonl`, per poster: the pool's move in the 60 seconds after their own fill (measured 0.2 s behind it), the best price available within that minute, and the crowd that arrives inside ten minutes.

| poster | followers | fills | pool depth, median | 60 s move after the fill, median | best within 60 s | +10% available | follower swaps in 10 min, median | sells inside 10 min |
|---|---|---|---|---|---|---|---|---|
| DumbCrayonEater | 451k | 4 | $476k | +52% | +65% | 75% | 430 | 0% |
| PoorGoat_ | 498k | 4 | $12k | +32% | +40% | 75% | 1,058 | 0% |
| Rowdy | 169k | 6 | $45k | +24% | +27% | 83% | 2,084 | 67% |
| Binkieee | 147k | 20 | $10k | +15% | +25% | 75% | 480 | 5% |
| Salem1299534 | 179k | 3 | $505k | +10% | +15% | 67% | 89 | 33% |
| frankdegods | 219k | 14 | $55k | −0.4% | +10% | 50% | 1,834 | 57% |
| insentos (the author) | 100k | 3 | $10k | −1.3% | +27% | 100% | 3,124 | 67% |
| unipcs | 466k | 3 | $20k | 0% | 0% | 33% | 7 | 0% |

The premise is true: a handful of posters move their pools 15–50% within a minute and draw hundreds to thousands of follower swaps. The author's own fills draw the largest crowd in the table, and he sells inside ten minutes two times in three. That is the mechanism of section 11.1: the poster is in before the move he causes, and sells it to the people the strategy tells to buy.

### 18.2 The exact rule, on swap-level data

`src/analysis/catalyst_scalp.py`, output `data/derived/catalyst_scalp_swaps.txt`. For each of the 276 fills, every swap of the pool from 30 minutes before to 30 minutes after (`rh/catalyst_paths*.jsonl`). Entry at the first swap D seconds after the fill; stop −22%; take-profit +50%; trailing stop 25% below the running high once +30% is reached; exit at 30 minutes otherwise; costs 1% each way plus constant-product impact of the clip against the pool's measured depth, each way (median depth $29.6k). Net return per trade, mean with a poster-clustered 95% interval:

| cohort | n | $500 clip, 3 s | $500, 15 s | $500, 60 s | $2,000, 3 s | $5,000, 3 s |
|---|---|---|---|---|---|---|
| all fills | 276 | −1.6% [−4, +2] | −5.8% [−9, −2] | −11.0% [−14, −8] | −19.3% [−25, −14] | −54.8% [−69, −42] |
| followers ≥ 100k | 123 | −2.4% [−6, +3] | −7.1% [−11, −2] | −12.9% [−18, −8] | −20.7% | −57.5% |
| followers ≥ 300k | 16 | +6.5% [−9, +25] | +0.8% [−7, +12] | −12.5% [−21, −3] | −10.1% | −43.3% |
| pool depth ≥ $100k | 88 | +2.9% [−3, +8] | +1.2% [−4, +7] | −4.9% [−8, −1] | +1.8% [−4, +7] | −0.3% [−7, +6] |
| ≥ 100k & depth ≥ $100k | 33 | −1.9% [−11, +8] | −2.4% | −6.5% | −3.1% | −5.4% |
| walk-forward "influential" (second half of each poster's events, poster chosen on the first half) | 28 | +1.5% [−7, +13] | −4.8% | −16.9% [−22, −9] | −15.9% | −50.5% |
| entering 10–30 min *before* the fill (the poster's seat) | 220 | +11.6% [+7, +17] | +9.2% | +8.7% | −5.8% | −40.0% |

Medians are −6% (3 s), −9% (15 s), −15% (60 s) for all fills; win rates 41%, 34%, 26%. Three seconds behind the fill, which is bot latency, the rule is zero to slightly negative; fifteen seconds, which is a fast person on a desktop, it is −6%; sixty seconds, which is the app's alert-to-tap latency, it is −11%, and −13% for the big-audience cohort the strategy says to follow. Size makes it worse faster than latency: the median pool is $30k deep, so a $2,000 clip pays 13% of impact for the round trip and a $5,000 clip pays a third. The one cohort that is flat at every size is the deep pools, where the poster's fill does not move the price and there is nothing to scalp. The only row that is clearly positive is the one no follower can occupy: entering before the fill.

### 18.3 Cross-checks

* **One-minute candles, all leaderboard buys of $1k or more with candle coverage** (`catalyst_scalp_candles.py`, 418 events, Robinhood only; no Solana fill fell inside the Solana candle coverage): entry 60 s after the fill, same exits, 3% flat costs: −1.3% [−5, +5] mean, −6.0% median, 30% wins; followers ≥ 100k −0.5% [−6, +8]; ≥ 300k −3.5% [−18, −1], 12% wins.
* **Listing catalysts.** Binance Alpha's public token list carries listing times; 13 listings fall in the study window, 4 have GeckoTerminal candles at listing time (`alpha_listing_test.py`). One of four was positive with the scalp's exits (FLORK, which had run +199% in the 24 hours before the listing, i.e. the anticipated catalyst the author warns against); the other three stopped out or bled. Too few to conclude; the list also omits delisted tokens.
* **The author's own wallets.** On Robinhood Chain the fomo handle `insentos` is a CASHCAT position: $2.0M bought from Jul 9 in 100 fills, $1.64M sold in 5, the rest held (section 3: rank 45, unrealized 110% of PnL, last 25 closed trades −$13k). On the scanned Solana wallet, Jan 17 → Aug 31: 74 tokens, 53 completed, $489k bought, $627k sold, net +$137k, 19 of 53 winners (36%), median token −$234, hold 34 minutes median, one token per active day, $4k median size. $125k of the $137k is one token bought Jun 28 and sold over five days; the other 52 net +$12k over seven months. Monthly: −$17k, +$29k, +$9k, +$22k, −$15k, +$125k, −$16k.

### 18.4 Live shadow

`src/strategy/catalyst_shadow.py` listens to the real-time alert feed and, on every buy by a trader with 100k followers or more, prices the token on DexScreener every 20 seconds for an hour and applies the rule from the first price it sees (2 seconds after the alert in practice). It is running and logs to `data/derived/catalyst_shadow.jsonl`. First hour: two alerts completed, one +47% net (OZZY, take-profit in nine minutes, $108k pool), one −25% (a $5k buy on BSC, stopped in the first minutes after a +24% spike). The log will be the hindsight-free sample; two trades are not.

### 18.5 Verdict

The strategy is a true description of a real mechanism and a wrong prescription for who can use it. The posters he names do move their pools 15–50% within a minute and draw thousands of follower swaps; entering before them pays +12% a trade; entering three seconds behind them pays about zero; entering at the speed of a person reading the app pays −6% to −13% before size, and size destroys it in pools this shallow. His own scanned record is one June token and a CASHCAT bag. The seat that works is the one he holds when he posts, which is why his fills draw the largest crowd in the table and why he sells into it inside ten minutes.

## 19. Round 11: the sniper, made executable from a small bankroll

The instruction: no capital, so forget the carry; take the seats that pay, optimise risk and return, and make it executable. The sniper is the one seat where a stake turns over in seven seconds, so a small bankroll can cycle through a day's launches. This round priced it by stake, found and fixed a simulator error, designed the switch and the stops on the five windows, and built the engine.

### 19.1 A correction to section 14

`sniper_sim.py` applied the first curve event after the seven-second mark before valuing the exit. A sniper who has sold at seven seconds is not hit by the creator's dump at sixty; the old code charged it. Fixed in both simulators (`sniper_sim.py`, `sniper_capacity.py`). Corrected first-in-line results, $300 stake, fit / holdout: Aug 12 +0.7% / −3.7%, Aug 20 +9.2% / +11.3%, Aug 27 +5.5% / +8.9%, Sep 2 +10.0% / +24.7%, Sep 3 +33.0% / +37.7%. Paying 10% more than first-in-line on Sep 3 is +24% / +27%, 25% more +13% / +16%; landing 0.5 s late is −0.9% / −4.5% on Sep 3 and −4.2% / +3.6% on Aug 27. The latency penalty is real and smaller than section 14 said; the seat is positive on four windows of five and flat in the launchpad's second week. Section 14.2 carries the correction.

### 19.2 Gas

The fastest bot's receipts: buys 450k gas at an effective 0.45–0.57 gwei, $0.50–0.63; sells 210–425k gas, $0.25–0.58; about $1 a round trip. The 25 gwei in its transactions is a maximum fee, not what it paid. The subsidy ends in early October; on the Sep 1–2 congestion the base fee was thirty times higher. The model below charges $1 (`sniper_capacity_gas1.txt`) and, as a stress, $8 (`sniper_capacity_gas8.txt`).

### 19.3 Capacity by stake, five windows

`src/analysis/sniper_capacity.py`: the rule on every eligible launch (creator's first launch of the day, ETH-quoted), exact LIFO exits at seven seconds, 1% each way, $1 gas. Mean return per trade and net dollars per six-hour window:

| stake | Aug 12 | Aug 20 | Aug 27 | Sep 2 | Sep 3 |
|---|---|---|---|---|---|
| $20 | −23% | −5% | −12% | −4% | +25% |
| $50 | −19% / −$2.2k | −1% | +6% / +$2.6k | +15% / +$12.7k | +35% / +$23.3k |
| $100 | −16% | +3% | +7% / +$5.7k | +16% / +$27.1k | +36% / +$47.1k |
| $300 | −14% / −$4.4k | +4% / +$0.8k | +7% / +$7.3k | +17% / +$40.6k | +35% / +$66.9k |
| $1,000 | −14% | +4% | +7% / +$3.0k | +17% / +$36.7k | +35% / +$56.7k |

Gas makes stakes under $50 unprofitable on all but the peak day; returns are flat from $100 to $300; above $500 the exit impact on a $30k curve costs more than the size earns. Overlap, the share of eligible launches arriving while a seven-second hold is still open, is 22–47%: one position at a time captures roughly 60% of a flow day.

With the creator-stake filter (launch-block buy ≥ 5% of supply): Sep 2 +24% per trade, $11.7k on 302 launches; Sep 3 +48%, $22.7k on 283; Aug 27 −0.3% on 98. It trades a quarter of the launches at a higher mean and lower drawdown, and it is the variant that survives a bad first hour.

### 19.4 The switch, the stop, and the compounding path

**Switch.** Score every eligible launch 25 s after creation from the curve's own events (the rule's outcome is known by then); trade live only while the mean of the last 30 scores is ≥ +5% of stake. $300 stakes, base filter, always-on versus switched: Aug 12 −$747 → $0 (never on); Aug 20 +$1,593 → +$543; Aug 27 +$7,255 → +$4,878 with the drawdown cut from −$1,427 to −$511; Sep 2 +$40,632 → +$34,042; Sep 3 +$66,876 → +$60,260. Live 0%, 48%, 56%, 74%, 90% of the time. No window negative. One position at a time under the switch: $0, +$600, +$4,253, +$19,894, +$41,271. At $8 gas the switched results are $0, +$184, +$630, +$23,286, +$51,396.

**Stop.** Stop for the UTC day at −30% of the day's starting bankroll. On Sep 2 the base filter's first hour is the one negative hour of the two peak days (section 14) and 20% sizing from $300 or $500 rode it to ruin without the stop; with it, the day ends at −30% and the bankroll is there for the afternoon.

**Compounding.** Stake = 20% of bankroll clamped to $50–$300, one position at a time, switch on, daily stop, trades in time order, the return at the stake actually used taken from the nearest simulated stake:

| window | filter | from $300 | from $500 | from $1,000 |
|---|---|---|---|---|
| Sep 3 | base | $82,641 (low $219) | $83,603 | $85,012 |
| Sep 3 | creator ≥ 5% | $32,439 | $33,384 | $34,710 |
| Sep 2 | base | stop at $188 | stop at $350 | stop at $694 |
| Sep 2 | creator ≥ 5% | $15,563 | $16,754 | $17,959 |
| Aug 27 | base | $5,465 | $7,132 | $9,401 |
| Aug 20 | base | $597 | $1,016 | $2,059 |

The stake reaches its $300 cap within the first hour of a flow day; after that the bankroll grows with the count of trades, not geometrically. The realistic floor is $300 and the willingness to lose it on a day like Sep 2's morning.

### 19.5 The engine

`src/strategy/sniper_engine.py` runs the whole loop live: sequencer feed → creation decode (creator, quote, initial buy from the calldata) → curve resolution from the factory event (q0, tk0) → filters → regime switch, daily stop, one-position, latency and gas gates → sizing → the exact unsigned `buy` (curve, `0x59a87bc1`, amountIn / minOut / recipient, value) and, seven seconds later, `approve` and `sell` (`0xd04c6983`) → `submit()`, which in the repository logs the transaction and sends nothing → a score for every eligible launch 25 s after creation. Its dry run from this sandbox (`data/derived/sniper_engine_dryrun.jsonl`): creations decoded within the second, curve resolution 630–1,150 ms (median 753 ms), which the 300 ms gate refused on every launch, as it should from a machine in the wrong place. The bot it competes with lands in 300–800 ms. `docs/SNIPER_RUNBOOK.md` is the A-to-Z: machine placement and the latency test, wallet, configuration, go/no-go, the send step and what to verify on the first $50 trade, tracking, kill criteria.

### 19.6 What is not built and why

The signing and broadcasting step. It is a few lines for whoever holds the key, and it is the line this environment draws; everything up to the byte before the signature is in the repository.

### 19.7 Verdict

With the exit valued correctly, the first-block seat is the best return per dollar in this study on every flow day and about zero on the others, and a switch built from the seat's own live scores separates the two. From $300 it is a machine near the sequencer, a wallet, a send function, and October's expiry.

## 20. Round 12: the audit that changed the answer

Section 19 said the first-block sniper was executable from $300. This round audited that claim with three independent
auditors (infrastructure and region; live-versus-backtest gap and ruin odds; simulator correctness), triple-checked every
flag against the chain, and rebuilt the simulator on the exact bonding curve. The audit found the curve, the fees and
the snipe tax exactly, and then found the thing that matters most: **the seat sections 14 and 19 measured cannot be
taken by an outside wallet.** What is left for an outsider is smaller, later, filtered and peak-day-only, and it is
written up here with the same care as the original claim. Scripts: `src/analysis/sniper_exact.py` (exact replay),
`sniper_compound.py` (switch, compounding, ruin), `sniper_audit.py`, `sniper_capacity.py` (LIFO capacity, kept for
comparison); outputs in `data/derived/sniper_exact.txt`, `sniper_compound.txt`, `sniper_bundle_filter.txt`,
`sniper_audit.txt`; engine v2 in `src/strategy/sniper_engine.py`; runbook v2 in `docs/SNIPER_RUNBOOK.md`.

### 20.1 The curve, exactly

Pons V2 curves are constant-product with virtual reserves **X0 = 1.68 ETH and Y0 = 1e9 tokens**. Fitted on the creator's
launch-block buy of 1,896 Sep 3 curves the median is 1.6800 ETH (p10 1.6800); the curve contract's own getter
(selector `0xc57eadfc`) returns 1.68e18. With that state every later buy is predicted to 1e-15 at the 1% and 1.19% fee
tiers and to 6e-4 at 7.18%, and every sell's gross is predicted exactly; the sell event's `quoteOut` is net of fee. The
creation event's `(q0, tk0)` are the creator's launch-block buy, not the reserves (section 19 read them correctly as the
first layer). Two things the LIFO simulator did not know:

- **Every token has its own creator-set trading fee**, 1% to 5% of the quote on both sides, exposed by the curve getter
  `0x24a9d853` in basis points (100 = 1%) and readable from the launch-block Buy event's fee before anyone else trades.
  On the eligible launches: Sep 3 46% at 1%, 24% at 2%, the rest 2.5–5%; Aug 12 66% at 1%. The flat 1% of sections 14
  and 19 under-charged 40–60% of launches on both legs.
- **The snipe tax is keyed to whole timestamp seconds, not to milliseconds.** The factory reports `snipeTaxStartBps =
  9900` and `snipeTaxSeconds = 3` (the public docs say 99% decaying over five seconds, which is out of date). Measured
  on 45 early buys with their real block timestamps: a buy in the **same second as the creation pays 93–98%**, in the
  next second **+6.18%** on top of the token's fee, in the second after that **+0.19%**, then nothing. Within a second
  the block does not matter (buys 3 to 18 blocks after creation all paid exactly 6.18% when stamped one second later).

### 20.2 Who pays no snipe tax, and why that closes the seat

Among 400 outside buys in the first 20 blocks after creation on Sep 3, 225 paid **no** surcharge at any delay,
including inside the creation second, and 175 paid the schedule. It is not the token (392 curves have both kinds), not
the path (both classes call the curve directly), not the size. It is the address: of 62 senders seen on two or more
curves, 62 are always taxed or always untaxed. The public v2 documentation says the creator "can name further
addresses at creation for a team bundling its opening buys", fixed at creation. **All 8 sampled untaxed first-second
buyers appear, address for address, in their launch's creation calldata**, whose length varies with the size of that
list (39–40 words without one, 44–57 with one). The untaxed wallets buy launches of 27 different creators and 44 of the
188 are themselves creators of other tokens in our windows: launch operators rotating creator and bundle wallets.

So the "first-in-line" buyer of sections 14 and 19, whose price the rule assumed it could take, is the launch team's own
bundle. An outside wallet that lands in the creation second pays 93–98% and is wiped out; the earliest legal outside
seat is the first block of the next second, at +6.18%, behind every bundle wallet. The fastest bot of section 14
(+28.7% a trade) is such a bundle: 12 of its early buys carried the 7.18% fee, i.e. the +6.18% surcharge on a 1% token,
and it still won because it was first *among the outsiders* on peak days. The seats are therefore:

| seat | who | when | surcharge |
|---|---|---|---|
| E0 | creator's named wallets only | creation second | none |
| E1 | fastest outsider | first block of the next second | +6.18% |
| E2 | slower outsider | first block of the second after | +0.19% |

### 20.3 What the auditors flagged, and what survived a triple check

| flag | verdict | effect |
|---|---|---|
| exit valued after the next event | confirmed, fixed (19.1) | large |
| compounding credited ROI-on-cost to the whole stake | confirmed, fixed | table inflated 1.4–2.3× |
| launches with no follower within 3 s were skipped (post-entry selection) | confirmed; every eligible launch is now traded | Sep 3 +34.6 → +26 % on the LIFO model |
| 3% cap binds on 97% of launches: return on stake is half the return on cost | confirmed; tables now show net $ and cost | reporting |
| engine sold `min_out` instead of the balance (34% left unsold) | confirmed; engine v2 sells the receipt's tokens | large |
| engine scorer used wall clock and log order | confirmed, fixed | small |
| LIFO exit is an artefact: exact replay ranges +5.7% to +65.7% | confirmed; the exact replay replaces LIFO | the E0 seat on the exact curve is +36.5% (Sep 3), close to LIFO by coincidence |
| block-time interpolation ±20% | confirmed; ±2 pp; engine (block count) and simulator (interpolated) agree to 0.1 pp on the mean | small |
| entry fee double-charged, layers gross | confirmed; −0.1 to −0.4 pp | small |
| switch used the previous launch's outcome before it was known | confirmed; scores now available 20 s after exit | ≤11% of net |
| 630–1,150 ms resolution from the sandbox puts the engine in the loss bucket | confirmed from here; the machine must sit in Ohio (20.8) | decisive |
| "quoteIn is post-tax, tx value ≫ quoteIn" | refuted: one splitter contract emits 2–3 Buy events per transaction whose sum equals the value | none |
| "99% tax makes 300 ms the wrong goal" | partly right for the wrong reason: the tax is per second and the barrier is the exemption (20.2) | decisive |
| Maestro / GMGN on Robinhood Chain at 1% | confirmed (Maestro announced Pons V2 support; 1% flat) | fallback only |
| region: sequencer in AWS us-east-2 (Ohio), FCFS, 100 ms blocks | as reported | plan |
| Robinhood Chain terms of use, automated-trading clause | ambiguous; flagged, not resolved | operator's call |

### 20.4 The seats on the exact curve, five windows

Exact replay, $300 stake, hold 7 s, gas $1, every eligible launch (creator's first launch of the day, ETH-quoted),
per-token fee on both legs, the seat's surcharge, later buyers spend the same ETH on the modified curve and revert
beyond a 10% shortfall, dropped buyers cannot sell, the sniper's sell lands 0.3 s late. Mean ROI on cost per launch;
`data/derived/sniper_exact.txt` has the confidence intervals, net dollars and every variant.

| seat, 3% of supply | Aug 12 | Aug 20 | Aug 27 | Sep 2 | Sep 3 |
|---|---|---|---|---|---|
| E0 (named wallets only) | +0.6 | +4.0 | +9.4 | +26.1 | +38.2 |
| E0, 0.3 s behind the first bundle buy | +0.2 | −1.7 | +3.1 | +5.0 | +7.6 |
| **E1, first outsider (+6.18%)** | **−5.0** | **−7.0** | **−0.2** | **+1.6** | **+3.2** |
| E1, 0.3 s behind the first outsider | −6.0 | −8.1 | −2.9 | −2.9 | −1.4 |
| E2, first of the next second (+0.19%) | +0.7 | −1.6 | +4.2 | +3.8 | +3.8 |
| E2, 0.3 s behind | −2.7 | −3.1 | +0.2 | −1.1 | −0.7 |

The E0 row reproduces section 19's headline (it is what the LIFO model measured, corrected for the fee tiers); it is the
launch team's return on its own launches. The outsider's seats are within a few points of zero on every window, and
negative 0.3 s behind. Five percent of supply is worse on every outsider row (impact); eight percent is negative
everywhere.

### 20.5 The one filter the outsider can see in time: bundled launches

The E1 decision is taken at the second boundary, after the creation second's blocks are on the feed. Those blocks show
how many wallets the creator's bundle bought with. Launches where **three or more named wallets bought inside the
creation second** (6–20% of eligible launches on the five windows; the bundle's median outlay 0.33–0.79 ETH) are the
ones the follow-on flow chases (`sniper_bundle_filter.txt`):

| bundle ≥ 3, 3% of supply | Aug 12 | Aug 20 (n=17) | Aug 27 (n=85) | Sep 2 (n=303) | Sep 3 (n=400) |
|---|---|---|---|---|---|
| E1, front | none | −4.5 | +2.4 | +9.1 [+4,+15] | +14.8 [+10,+21] |
| **E1, 0.3 s behind** | none | −6.2 | −1.9 | **+5.1 [0,+11]** | **+10.4 [+6,+15]** |
| E1, 0.75 s behind | none | −4.7 | −4.3 | +2.1 | +5.9 |
| E2, front | none | +2.9 | +2.3 | +8.9 | +11.4 |
| E2, 0.3 s behind | none | −0.4 | +0.2 | +6.2 | +8.0 |

Thresholds 2, 4 and 6 give the same picture. Between the E1 seat and its exit on those launches (Sep 3), 284 ETH of
buying carries no surcharge (the bundle's own later buys inside 3 s, and anyone after 3 s) against 19 ETH from
surcharged outsiders: the outsider is riding the bundle's pump for seven seconds and selling into it. Two cautions:
the filter was chosen on these five windows (it is a natural hypothesis, and it is monotone in the threshold, but it
is in-sample), and it only pays on the two peak-flow days.

### 20.6 Switch, compounding and ruin, on the exact trades

`sniper_compound.py` replays the exact-curve trades in time order with the regime switch (mean of the last 30 scores
≥ +5%, each score available 20 s after its launch's exit), one position at a time, stake = 20% of bankroll clamped
$50–$300, deployed = min(stake, simulated cost), a −30% daily stop.

| E1 on bundled launches, 0.3 s behind, 3% | Aug 20 | Aug 27 | Sep 2 | Sep 3 |
|---|---|---|---|---|
| always-on, $300 stakes, 6 h | −$180 | +$122 | +$4,811 | +$11,691 |
| switched, one at a time | $0 (never on) | −$242 | +$265 | +$8,015 |
| from $300, 20% sizing | $300 | $236 | $193 (stop) | $6,136 |
| from $1,000, 20% sizing | $1,000 | $774 | $654 | $8,714 |
| from $50, all-in: chance of reaching $300 before $25 | 0% | 5% | 23% | 33% |

For comparison the E0 seat (the launch team's) compounds $300 into $63k on Sep 3 and reaches $300 from $50 96% of the
time; that is the table section 19 printed, and it is not available to the reader.

### 20.7 The engine, version 2

`src/strategy/sniper_engine.py` now: sizes on the exact curve (virtual reserves, per-token fee assumed at the worst
common tier, the seat's surcharge); takes the seat (E0 refuses to start unless `EXEMPT=1`; E1 waits for the first feed
message stamped in the next whole second, counts the creation second's direct curve buys on the feed and trades only if
they number at least `BUNDLE_MIN`); builds the buy with `minOut` at the sized tokens less `SLIP`, so a landing in the
wrong second reverts for gas instead of paying 95%; live, reads the tokens received from the buy's own event, approves
the curve immediately so the exit is one 81k-gas transaction, and sells that balance HOLD seconds after the buy
landed; scores every eligible launch 25 s after creation with the simulator's replay (mean agrees to 0.1 pp on Aug 27
and Sep 3) so the switch is fed the same way in the backtest, the dry run and live; in dry run the bankroll follows
those scores. Still not built: signing and sending (`submit()` returns None), and a local sequencer-following node.

### 20.8 Infrastructure

The sequencer (`sequencer.mainnet.chain.robinhood.com`) is in AWS us-east-2 (Ohio), first-come-first-served, no
priority fee, 100 ms blocks, and publishes `wss://feed.mainnet.chain.robinhood.com`. From this sandbox the engine
resolves a creation in 550–1,150 ms, which is the losing bucket on every row above; the seat requires an EC2 instance
in us-east-2, the feed for detection, a nearby RPC (a provider endpoint in Ohio, or better a Nitro node following the
feed on the same machine, which makes the curve resolution a local call) and direct submission to the sequencer. Gas
is ≈ $1 a round trip at 0.5 gwei (buy ~450k, approve ~46k, sell ~81k gas); Robinhood's gas subsidy applies to its own
wallet's swaps, not to bots. Telegram bots (Maestro announced Pons V2 on Robinhood Chain at a flat 1%; GMGN lists the
chain) trade from a phone with no seat control and no second-gating: usable to place a manual test buy, not to run this
rule. The chain's terms of use have an automated-trading clause whose scope is ambiguous; it is flagged, not resolved.

### 20.9 Verdict

- The treasure of sections 14 and 19 is real and it is the launch team's: the creator's named wallets buy tax-free in
  the creation second and sell into the outsiders seven seconds later. That is the creator's seat of section 13 seen
  from its bundle wallets, and it is the launch-and-dump this project declined to automate.
- The best outside seat is the first block of the next second, on launches whose bundle bought with three or more
  wallets, from a machine in Ohio. On the exact curve it earns +5% to +10% a trade on the two peak-flow days (a few
  thousand dollars on $300 stakes over six hours), about zero on the ramp, and nothing off-peak; the switch keeps the
  off-peak days near zero. The filter is in-sample. Starting from $50 all-in it reaches $300 one time in three at best.
- Backtest = paper = live is now true in the sense the brief demanded: the engine and the simulator share the curve
  model, the fee model, the seat, the filter, the sizing and the scoring, and the dry run measures the one thing the
  backtest cannot, resolution latency. The remaining gap is the race for the first block of second one, which only a
  live wallet in Ohio can measure.

## 21. Round 13: more days, the machine, and the chain question

Three questions from the reader after section 20: what speed can a retail box actually get and with what, which
chain, and why only five windows. This round pulled nine more six-hour windows (three in flight as this is written),
rebuilt the engine's critical path so that it needs no RPC call before the buy, and priced the Solana alternative.
Scripts: `src/analysis/sniper_oos.py` (out-of-sample seats), engine v2.1 in `src/strategy/sniper_engine.py`; outputs in
`data/derived/sniper_oos.txt`.

### 21.1 Out of sample: the bundle filter holds, at about half the peak-day size

The bundle filter of section 20.5 was chosen on Aug 12 to Sep 3. Sep 4 and Sep 5 were never looked at before this
round. Exact curve, $300 stakes, 3% of supply, sell 0.3 s late; "behind" means 0.3 s behind the first outsider.

| window (12–18 UTC) | eligible | bundled (≥3) | E1 front | E1 behind | E2 front | E2 behind | switched net, 1 at a time (E2 behind) |
|---|---|---|---|---|---|---|---|
| Sep 2 (in-sample) | 2,199 | 14% | +9.1% | +5.1% | +8.9% | +6.2% | $1.8k |
| Sep 3 (in-sample) | 1,962 | 20% | +14.8% | +10.4% | +11.4% | +8.0% | $6.3k |
| **Sep 4 (new)** | 799 | 19% | +11.9% [+4,+18] | +8.5% [+1,+15] | +13.2% [+6,+20] | +9.6% [+4,+16] | **$2.7k** |
| **Sep 5 (new)** | 1,730 | 24% | +4.7% [0,+9] | +0.6% [−4,+6] | +5.0% [+1,+9] | +4.2% [0,+9] | **$4.3k** |
| **Aug 30 (new)** | 1,344 | 18% | −1.1% [−6,+3] | −1.9% [−6,+2] | +2.8% [−3,+8] | +0.4% [−5,+5] | **−$0.5k** |
| **Sep 6 (new)** | 1,695 | 21% | +9.4% [+4,+14] | +2.5% [−2,+7] | +5.8% [+1,+11] | +0.9% [−4,+6] | **$2.9k** |
| **Aug 31 (new)** | 1,502 | 21% | +2.2% [−2,+7] | +1.1% [−4,+6] | +6.2% [+2,+12] | +2.6% [−2,+8] | **$0.5k** |
| **Sep 1 (new)** | 1,912 | 18% | −2.1% [−8,+3] | −6.0% [−10,−1] | −2.3% [−6,+2] | −4.7% [−9,0] | **−$0.7k** |
| **Sep 3, 00–06 UTC (night)** | 1,909 | 13% | +2.4% [−3,+9] | −0.9% [−6,+5] | +4.2% [−1,+10] | +0.4% [−5,+6] | **−$0.3k** |
| **Sep 3, 18–24 UTC (evening)** | 2,674 | 22% | +11.5% [+7,+16] | +7.4% [+3,+12] | +10.1% [+6,+14] | +5.9% [+2,+10] | **$2.5k** |
| **Sep 5, 00–06 UTC (night)** | 842 | 28% | +6.1% [+2,+11] | +2.6% [−1,+7] | +8.0% [+3,+13] | +6.2% [+1,+11] | **$2.2k** |

Nine windows were never used to choose anything (the six new days and the three off-hours windows). At the E2 seat
0.3 s behind the front, on bundled launches, seven of the nine are positive, two are flat (Aug 30, the Sep 3 night)
and one loses (Sep 1); the switched, one-position-at-a-time nets sum to about +$13.4k over those 54 hours, with the
worst window at −$677.

The off-hours windows say the launchpad does not sleep: 1,909 launches between midnight and 06:00 UTC on Sep 3 and
2,674 between 18:00 and 24:00, the busiest window of the thirteen. At night the bundled seat is about zero (the
switch holds the window to −$311 at E2 behind) and the unfiltered seats lose 5–6% a trade; in the evening every
outsider cell pays (+5.9% to +11.5%), with $2.5k to $11.6k switched. What the new days add. The filter survives out of sample on four of six new windows (Sep 6, the day this was
written, is +9.4% at the front and +2.5% behind on 364 bundled launches, $2.9k to $6.6k switched; Aug 31 is small
but positive on every outsider cell, $0.5k to $3.7k switched; Sep 1 loses on every outsider cell, −$0.6k to −$0.9k
switched): every bundled-launch cell is
positive on Sep 4 and Sep 5 while the unfiltered outsider seat is within a point or two of zero (Sep 4 E1 +1.1%, Sep 5
E1 +1.6%, negative 0.3 s behind). Aug 30, a busy day (1,344 launches, 18% bundled), is the counter-example: the launch
teams' own seat made +31.5% but the outsider's bundled seat was flat (E2 +2.8% front, +0.4% behind, confidence
intervals straddling zero), and the switch held the day to a loss of $79 to $736. So the bundled seat is not "busy day
= profit"; it is "busy day with follow-on buyers behind the bundle = profit", and the switch is what tells the two
apart, thirty launches at a time. Second, **the E2 seat (the second whole second after creation, +0.19% surcharge) is at least
as good as E1 behind the front**, and it is the cheaper, less contested slot: the fastest outsider bots fight for the
first block of second one, and the E2 buyer sits behind them paying six points less tax. The runbook now runs E2 by
default. Rows for Sep 6, Aug 30, Aug 31, Sep 1 and the off-hours windows are appended to `sniper_oos.txt` as their
pulls finish.

The launch-time signal can be read even earlier than the bundle's buys. The creation transaction's calldata carries
the list of wallets the creator exempted; on 600 Sep 3 launches the count of those wallets predicts both the bundle and
the outsider's return (0 named: −5.1% at E1 behind; 6 or more named, 27% of launches: 71% of them bundle three or more
and the seat returns +13.5%). A filter of "three or more named wallets" earns +9.7% against +12.9% for "three or more
observed bundle buys"; the engine logs both.

**The E2 seat on every launch, and what latency does to each seat.** `data/derived/sniper_e2front.txt` runs the
second-two seat on all eleven windows (66 hours), at the front of the T+2 flip block, one block (0.1 s) behind it,
and three blocks behind, with and without the bundle filter. Switched, one position at a time:

| E2 seat, 3% of supply | front | +1 block | +3 blocks |
|---|---|---|---|
| every eligible launch, sum of 11 windows | $38.0k (9 of 11 positive; +2.4% to +6.2% a trade from Aug 27 on) | $14.7k | $8.7k |
| bundled launches only | $23.7k | $19.5k | (section 21.1: about zero on Aug 30 and Sep 1, positive elsewhere) |

The unfiltered front seat is the largest and the most consistent per trade, and it evaporates one block behind; the
bundled seat is smaller and survives a block of delay. That is the whole latency question in one table: the filter
buys tolerance for being late, the front seat buys size for being first. The engine runs the bundled seat by default
and can run the unfiltered one (`BUNDLE_MIN=0`) once the `landing` events show it is first in the flip block.

### 21.2 What speed a retail box can have, and what to run

- **Where the time goes.** The sequencer orders, executes, then broadcasts; the feed message arrives after the block
  exists, and RPC nodes show the block only after re-executing it. So nobody outside the sequencer sees a creation
  before the feed does, and anyone who then asks an RPC "which curve did that create" pays the re-execution and the
  network twice. From this sandbox that resolution took 550–1,150 ms; from a box next to the sequencer it is a few
  tens of milliseconds with a provider node, and a few milliseconds with a local node.
- **The engine no longer asks.** The creator's exempted wallets buy the new curve inside the creation second, and their
  addresses are in the creation calldata. Engine v2.1 recovers the sender of every buy on the feed (about 70 µs each),
  matches it against the creation's named list, and takes the address they bought as the curve: no RPC call before the
  buy, and an exact match rather than a guess. In the dry run the match is validated against the factory event 25 s
  later; the first version with a freshness heuristic mismatched 2 of 16 (simultaneous creations in a feed burst),
  which is why the match is now by sender. The creator's token count is derived from the calldata's initial buy on the
  exact curve (within 4% at the worst fee tier). The only remaining waits are the seat's second boundary, which every
  outsider shares, and the submit round trip.
- **What to rent.** An EC2 instance in us-east-2 (Ohio), the smallest general-purpose size is enough for the engine
  (the feed is ~70 transactions a second; decoding is microseconds). Connect to `wss://feed.mainnet.chain.robinhood.com`
  directly, or through Offchain Labs' Nitro relay (23 MB, 1.6% of a core) if more than one process needs the feed, since
  Robinhood rate-limits per client. Submit to `sequencer.mainnet.chain.robinhood.com`. For nonces, receipts and the
  25-second scorer use a provider endpoint (Alchemy, QuickNode and Chainstack list the chain; QuickNode and Chainstack
  let you pick a US-East region or a dedicated node) rather than the public RPC, which returned 429s to three engines
  from one address here. A full Nitro node (64 GB RAM, several TB of NVMe, an Ethereum L1 RPC and beacon endpoint) is
  not needed for this path and costs more than the strategy's quiet weeks.
- **What to measure on day one.** `resolve_ms` (feed to curve known: should be the wait to the second boundary and
  nothing else), `sent_ms` (feed to submit), and the surcharge on the first receipts (the token's tier + 0.19% at E2,
  + 6.18% at E1; 93–98% means the wrong second). Section 20.7 and the runbook say what each number must be.

### 21.3 Which chain

The seat was found, measured and audited on Robinhood Chain, and only there. It exists because of three things that
are specific to this chain and this launchpad: first-come-first-served ordering with no priority fee, so a box in Ohio
can be first among outsiders without paying for it; a snipe tax keyed to whole seconds, which fixes the seat at a known
boundary; and a bonding curve that is exact and cheap to replay, which is what lets a $150 trade be priced to the
cent. Solana was checked in rounds 1 and 3 for the leaderboard traders, not for this seat. On pump.fun the equivalent
seat is bought, not raced: token creation and the team's buys land in one Jito bundle, the first outside slot goes to
the highest tip (0.001–0.05 SOL under competition), and the competitive bots run sub-50 ms end-to-end on bare metal
co-located in Frankfurt and Ashburn with shred-level visibility; a 200 ms pipeline lands in slot two or three, which is
where the trade stops paying. That is a different business, with a data pull the remaining Helius budget cannot cover
at trade level, and it is not what was tested. If the reader wants the Solana seat priced the same way, that is a new
round with its own data.

### 21.4 Why five windows, and what changed

Each six-hour window is 200–420 thousand curve events pulled through a rate-limited public RPC (ten to twenty minutes
a window when it behaves); the first five were chosen to span the fee cycle rather than to be many. This round adds
Sep 4, Sep 5, Sep 6, Aug 30, Aug 31, Sep 1, and three off-hours windows (Sep 3 00–06, Sep 3 18–24, Sep 5 00–06) so
that the seat is seen on ordinary days and at night. The rows land in `sniper_oos.txt`; the table above is updated in
place as they arrive, and the verdict of section 20.9 stands: an outside seat that pays on busy days, about zero
otherwise, now confirmed on two days it had never seen.

### 21.5 The latency, researched and made operational

**Ordering.** Robinhood's documentation states first-come-first-served ordering by arrival at the sequencer, with no
fee-based bypass; Timeboost (the Arbitrum express-lane auction) is not enabled on the chain. So the seat is a pure
arrival race, which is the one kind of race a $30 box next to the sequencer can win.

**Where the first outsiders actually land.** Sampling 70 bundled launches on Sep 6 and fetching the real block
timestamps around each: the first block stamped with the next second (the E1 boundary) comes 1 to 9 blocks after the
creation (median 4, i.e. the boundary falls anywhere inside the creation second). The first surcharged outsider buy is
**in that flip block itself on 33% of launches and within two blocks on 63%**; the rest arrive up to nine blocks
later. The first outsider block holds a median of one and at most two outsider buys. Two conclusions: the fastest
outsiders *predict* the boundary (a reactive sender, one that waits to see the new second on the feed, can only land
one or two blocks after it, 100–200 ms late), and once in that block there is almost nobody to share it with. The E2
seat is more relaxed: the first +0.19% buyer lands in the T+2 flip block 12 times, one block later 18 times, two later
14 times: mostly reactive, which is why E2 behind the front holds up as well as it does in 21.1.

**Measuring the boundary without sending.** The feed's L2 messages (header kind 3; kind 11 batch-posting reports carry
Ethereum's clock and must be ignored) arrive one per block at ~93 ms median cadence here, and the block timestamp flips
once a second. Because flips are only visible at block granularity, the sequencer's true boundary is the *low edge* of
the wall-clock phases at which flips are observed, not their median. `src/strategy/latency_probe.py` measures that
edge, its spread, the feed's delivery delay and the round trips to the sequencer and the RPC; on connect the feed
replays a backlog of several seconds in a burst, so the first five seconds are discarded (the engine now discards them
too, and never trades a creation from the replay). From this sandbox, through a proxy: boundary edge stable to a few
ms across runs, flip spread 0.34 s (block cadence plus proxy jitter), sequencer round trip 27–37 ms, RPC 37–42 ms.
From Ohio the round trip should be 1–3 ms and the spread close to one block.

**The engine's send modes.** `SEND_MODE=react` sends when the feed shows the seat's second (lands one to two blocks
after the boundary: the E2 seat's typical position). `SEND_MODE=predict` keeps the last 600 observed flips, estimates
the boundary edge, and sends at the seat's boundary plus `MARGIN_MS` (default 25 ms); if the feed shows the seat's
second before that moment it sends immediately and logs `predict-late`. Live, every buy receipt is checked against the
block timestamps: a revert stamped before the seat's second means "too early" (the minOut guard turned a 95% tax into a
gas fee) and the margin grows by 20 ms; a landing in the seat's second but not its first block shrinks it by 5 ms; a
first-block landing keeps it. The margin therefore converges on the smallest value that never lands early, which is
the definition of being first among the outsiders on that machine.

**The machine, as a script.** `deploy/ohio_setup.sh` installs chrony (the boundary is the sequencer's clock; the box
must be on NTP), a Python environment, the engine as a systemd service in dry run with the runbook's configuration,
and the probe as a one-shot service. What day one must show: `boundary` events with a stable phase, `trade_decision`
events with `send_mode: predict` and `sent_ms` equal to the seat's wait, `feed_resolution_ok` after every bundled
launch, probe round trips in single-digit milliseconds. Then the send step, then the first receipts' `landing`
events, which are the only measurement of the race itself.

### 21.6 Why the losing windows lose, and the rule that came out of it

`src/analysis/sniper_failure.py` builds a feature table for all 20,728 eligible launches in fourteen windows (3,704
bundled) and scores each at the E2 seat, 0.3 s behind, 3% of supply, 7 s hold (`data/derived/sniper_features.json`,
`sniper_failure.txt`).

**The timing budget.** The third named-wallet buy lands inside the creation second by definition; the E2 send goes at
the boundary two seconds later (median 2.30 s after creation, p10 1.76 s). In between, the engine decodes and matches
a few dozen transactions (microseconds each), sizes on the exact curve, signs and sends (a few milliseconds from Ohio).
The seat sets the pace, not the machine; what the machine must not do is miss the boundary.

**What a losing trade looks like.** Of trades losing more than 30% (792 of 3,704), 100% had a sell of at least 1% of
supply during the hold, with a median 45.7% of supply dumped, against 0.3% for trades winning more than 20%. The
first sell comes at 2.0 s after entry for losers, 2.6 s for winners; losers see 0.31 ETH of buying during the hold,
winners 0.79 ETH. It is the team unloading into the crowd it attracted, seven seconds after we joined it.

**Can the exit dodge the dump?** No. The dump lands 86% in its first sell and 94% within 0.3 s (median of 2,012 dumped
launches), so a reactive sell that reaches the chain 0.3 s after seeing the first big sell exits at the same price a
7 s hold would (+3.4% versus +3.3% mean over twelve windows; a first version of the replay that stopped applying the
cascade at the trigger showed +14% and was wrong). A 5 s hold is slightly better on money and equal on return; 10 s is
much worse. 82% of dumped supply goes through direct curve calls, visible on the feed by selector, so the engine can
see dumps; it just cannot outrun them. The reactive exit is implemented (`STOP_SELL_FRAC`) and off by default.

**What is visible before the send, and what it says.** Feature splits on bundled launches (mean return at E2, 0.3 s
behind):

| feature, known before the send | worst bucket | best bucket |
|---|---|---|
| outsiders (non-named buyers) in second one | ≥1: −2.9% to −4.1% (1,459) | none: +7.9% (2,245) |
| creator's own launch buy | <1% of supply: −4.5% (308) | ≥6%: +12.1% (686) |
| bundle's ETH in the creation second | <0.3: −1.9% (603) | 0.3–0.6: +7.7% (713) |
| team buys continuing in seconds 1–3 | none: −0.5% (1,493) | ≥0.5 ETH: +25.0% (183) |
| creator seen launching on earlier days | ≥2 days: −12.6% (13) | never: +3.6% (3,663) |

The first line is the one that matters and it is counterintuitive: outsiders piling in at second one are not a sign
of demand, they are the fast bots that will sell at 3–7 s, exactly during our hold. Walk-forward, fitting nothing:

| pre-entry rule (bundle ≥3 plus …) | first 7 windows | last 7 windows | windows > 0 | worst window |
|---|---|---|---|---|
| nothing | +0.9% | +5.4% | 11 of 13 | −4.7% (Sep 1) |
| no outsider in second one | +4.1% | +11.3% | 10 of 12 | −1.8% |
| no outsider + creator buy ≥1% | +5.4% | +12.2% | 12 of 12 | +1.3% (Sep 1) |
| **no outsider + creator ≥1% + bundle ≥0.3 ETH** | **+6.4%** | **+12.6%** | **11 of 11** | **+2.5% (Sep 1)** |

The full rule keeps 1,843 of the 3,704 bundled launches and turns Sep 1, the losing day, into +2.5%. Per window,
E2 0.3 s behind, 7 s hold, $300 stakes (`data/derived/rule_plan.txt`):

| window | n | mean ROI | always-on | switched, 1 at a time | from $300 at 20% |
|---|---|---|---|---|---|
| Aug 30 | 164 | +4.4% | $2,041 | $292 | $313 |
| Aug 31 | 261 | +4.0% | $2,917 | $2,365 | $1,093 |
| Sep 1 | 188 | +2.5% | $1,277 | −$889 | $190 (stop) |
| Sep 2 | 184 | +12.8% | $6,756 | $4,898 | $3,258 |
| Sep 3 night | 68 | +14.0% | $2,824 | $1,509 | $725 |
| Sep 3 day | 211 | +13.4% | $8,296 | $6,606 | $4,830 |
| Sep 3 evening | 339 | +11.5% | $11,599 | $7,458 | $6,076 |
| Sep 4 | 70 | +18.9% | $3,947 | $1,851 | $884 |
| Sep 5 night | 48 | +9.7% | $1,400 | −$150 | $273 |
| Sep 5 | 124 | +20.7% | $7,511 | $6,662 | $5,075 |
| Sep 6 | 177 | +6.1% | $3,217 | $409 | $205 (stop) |
| sum | 1,843 | | $51,910 | $31,010 | |

Every window is positive per trade. The switched column is lower because the rule leaves 50–340 launches a window
and the 30-launch warm-up eats a third to a half of them; two windows end slightly negative for that reason. The
compounding column shows the other side of risk control: with a $300 bankroll a single dumped trade is a 12% hit, so
the −30% daily stop fires after two or three bad trades in a row and twice stops a day that ends positive (Sep 1,
Sep 6). Section 21.7 sweeps the stop and the switch.

**The engine.** All three gates are now in the engine and in its scorer (`OUT1_MAX=0`: no non-named buyer of the
curve stamped in second one; `MIN_CREATOR_SUPPLY=0.01` from the calldata's initial buy; `BUNDLE_MIN_ETH=0.3` from
the named wallets' transaction values on the feed), so the switch scores the same universe the engine trades. The
sell selector and the fast bots' router are watched during the hold so that `trade_done` records whether a dump landed
and when, which is the live measurement of this section's mechanism.

### 21.7 The switch and the stop, re-tuned under the rule

`data/derived/stop_sweep.txt`: compounding from $300 at 20% sizing (stakes clamped $50–$300), one position at a time,
on the eleven windows with enough rule-passing launches, end bankroll summed as gains over the start:

| setting | sum of gains from $300 | windows ending below start | from $1,000 |
|---|---|---|---|
| switch 30 launches / +5%, stop −30% (section 19's) | $19,623 | 3 | $29,015 |
| switch 15 / 0%, stop −50% | $20,430 | 0 | $32,071 |
| no switch, stop −30% | $30,011 | 1 | $39,896 |
| **no switch, stop −50%** | **$30,343** | **0** | **$44,071** |
| no switch, no stop | $30,343 | 0 | $44,071 |

Two conclusions. The regime switch was doing the filter's job badly: once the rule removes the launches where the
fast bots sit, the switch's warm-up only skips good trades, and every switched setting loses to none. The −30% daily
stop is too tight for a $300 bankroll where one dumped trade is a 12% hit: it fired on Aug 31 and Sep 1 in windows
that ended positive; at −50% it never fired. The engine's defaults are now a safety-net switch that only stops
trading when the last 15 scores average below −10% (it never triggers on these windows), and a −50% daily stop. Both
exist for the day the seat stops working, not for ordinary variance.

### 21.8 What this round changes in the plan

1. Enter only bundled launches with no outside buyer in second one, a creator launch buy of at least 1% of supply
   and a bundle of at least 0.3 ETH: positive on every window measured, worst +2.5%.
2. Hold 7 s, no reactive exit: the dump cannot be outrun, only avoided by the gate above.
3. No regime switch in normal operation; a −50% daily stop; a −10% safety switch.
4. From $300 the rule compounded to $625 to $9,379 per six-hour window on the eleven windows (median about $1,500),
   from $1,000 to $1,880 to $11,524, with every window ending above its start. The chance of running $50 into $300
   before losing half of it is 16–68% by window (`rule_plan.txt`): still a lottery ticket below $300.
5. Everything above is the backtest side; the engine now trades this exact universe in its dry run, so the first days
   in Ohio will show whether the live scores match these tables before any money moves.

### 21.9 "Do we always get filled?"

On a bonding curve a buy that lands executes; there is no counterparty to disappear. "Filled" therefore means landing
in the seat's second with a `minOut` the price at that moment satisfies. Three things decide that, and one of them was
wrong in the engine until this section.

- **The sizing bug.** The engine sized the buy on the curve's state right after the creator's launch buy. By the time
  it sends, two seconds later, the bundle (0.3–0.8 ETH into reserves of about 1.7 ETH) and the team's follow-up buys
  have moved the price 30–60% higher; the sized ETH would have bought far fewer tokens than intended and `minOut`
  would have reverted most trades. The engine now rebuilds the curve's reserves from the feed at send time (creator
  buy from the calldata, every buy of the curve with its ETH value, every direct sell with its token amount) and
  sizes 3% of supply on that state, logging `price_vs_creator` on every decision. This is also what the simulator does.
- **The minOut refusal.** The simulator now refuses a trade the way the live engine would: if the price it meets 0.3 s
  behind the seat's start is more than `SLIP` above the price at the seat's start, the buy reverts for half a round
  trip of gas. At the engine's 25% tolerance that refuses 0.8–5.7% of rule-passing trades per window and changes the
  window's return by −1.1 to +0.7 points (Sep 1 +2.5 → +2.2%, Sep 3 evening +11.5 → +12.2%, Sep 6 +6.1 → +5.0%); at
  a 10% tolerance it would refuse 2–16%. Twenty-five percent stays.
- **The wrong second.** A buy stamped in the creation second reverts on `minOut` (the tax would take 95%), costing
  gas only; a buy stamped in second one pays +6.18% and lands. Neither is in the backtest, which assumes we land where
  we aim; the receipt-tuned margin exists to keep both rare, and `landing` events count them.

The sell side always fills: `minOut` is zero, the approve is sent right after the buy confirms, and a dump landing
just before our sell is priced into the 0.3 s exit slip. The operational exception is a box or endpoint failure during
the seven seconds, which is why the runbook asks for the sell to be signed at buy time and sent through a second
endpoint if the first fails.

## 22. Round 14: two independent audits, the same brief, and what changed

Two auditors (one Fable 5.1, one Opus 5) received the identical brief (`scratchpad/audit_prompt.md`): audit the
strategy from A to Z for a retail operator with a laptop, $300 and one Ohio instance, verify against the chain, and
say whether live results would match the backtest. Their scratch work is in `audit_fable/` and `audit_opus/` in the
data root. Every finding was re-checked here before acting on it. Outputs of this round: `data/derived/sniper_plan.txt`
(`src/analysis/sniper_plan.py`, which now reproduces every table of sections 21.6–21.8 and this one),
`sniper_oos_v2.txt`, engine v3, `deploy/ohio_setup.sh` v2.

### 22.1 What both auditors found, verified here, and what was done

| finding (both auditors unless noted) | verification | action |
|---|---|---|
| **The engine decoded only type-2 transactions and counted a buy only when the call went straight to the curve**, so it saw about 40–44% of the second-one outsiders whose absence is the rule's main gate (Fable: 32 of 80 sampled; Opus: 66 of 150), 85% of bundle buys and 35% of second-two buyers; 7% of creations use a second selector | Live feed, 60 s: 213 type-2 buys, 19 legacy, 1 type-1, plus router calls carrying value. Confirmed. | Engine v3 decodes legacy, type-1 and type-2 envelopes, recognises router buys as any value-carrying transaction whose calldata names the curve, handles both creation selectors, and at score time logs `gate_check`: the feed's bundle count, bundle ETH and outsider count against the chain's. First dry run: bundle and ETH match exactly, outsiders match on five of six checks (one router buy missed). |
| **The rule is in-sample**: the three gates were picked from splits pooled over all fourteen windows; the "walk-forward" halves both contain days used to choose them; "11 of 11 positive" omitted three windows with under ten qualifying launches | Correct as stated. Both auditors also found the rule is not knife-edge: Opus swept seven threshold perturbations, all 11 of 11 positive at +8.3% to +9.9%; Fable's leave-one-window-out rules score +6.8% to +22.7% on held-out busy windows; Fable's shuffle test attributes a third to a half of the +6.1 pp lift to selection. | Disclosed. The honest pooled expectation before live effects is put at +7–8% per trade, with the un-gated bundled seat (+3.6%) as the floor; the forward test is the only cure. |
| **Compounding paths are one ordering each** ("every window ends above start") | Correct. | `sniper_plan.py` now resamples the trade order 1,000 times per window: from $300, the chance of hitting the −50% stop is 15% (Aug 30), 18% (Aug 31), 34% (Sep 1), 10% (Sep 6) and 0–6% on the seven busy windows, with p10 ends of $135–$149 on the four weak ones. |
| **Displacement tolerance is an unverified assumption** (Opus): at a 5% slippage limit for the follow-on buyers the pooled return halves (+9.65% → +4.5%, 9 of 11 windows) | Fable checked the direct later buyers on chain: 46 of 54 set `minOut = 0`, the rest above 20%, so 10% is conservative for them; router buyers unknown. | Disclosed as the largest unquantified modeling risk; 10% kept. |
| **`GAS_MAX_SHARE` had been swallowed by a comment** (Opus) after an earlier edit, exactly as `MAX_CREATOR_BUY_ETH` had been the day before; the gas gate silently returned "ok" | Confirmed by AST. | Restored; a module-level scan for unassigned constants is now part of the check. |
| **The bundle-ETH gate read 0.000 on most launches** (Opus) | Those were launches with no visible named-wallet buys (decoder blindness above). | Fixed by the decoder; the `gate_check` log proves the reading. |
| **Operational fragility** (both): nonce and gas fetched synchronously with a silent fallback to zero; receipt timeout abandoned a landed buy; two threads could pass the gates together; react mode sent after a stale 3.5 s wait; `seed` ran inside the first launch after midnight and failed on 429; no state persistence across the restarts the service enables; the position lived only in a thread | Confirmed in code. | Engine v3: nonce/gas/ETH price refreshed by a background thread, a stale reading is a gate, never a zero; receipt timeout still approves and sells; gates and `busy_until` under one lock; the seat's second not seen means no send; seed in a background thread with retries; bankroll, day, scores, margin and the open position persisted to a state file and an open position is closed on restart. |
| **The decoder got slower every hour** (Opus): the router-sell scan looped over every curve ever seen; the decision log rebuilt the curve state twice; deques were copied per decision; signature recovery without `coincurve` costs milliseconds; scoring polls the RPC per launch | Confirmed. | Per-curve indexes, pruning after 15 minutes, router-sell scan limited to the open position's curve, state computed once; `coincurve` installed by the setup script. Scoring still costs one log query per launch (a provider endpoint is required). |
| **Predict mode anchored the boundary to the local clock**, not to the creation's second (Opus); an E2 buy that lands one second early pays +6.18% rather than reverting (Fable) | Correct. | Predict mode now derives the target from the local time the feed first showed the creation's next second, snapped to the estimated boundary edge; react mode is the default and the recommended mode at E2 (it cannot land early). |
| **The Buy event's `fee` field is the 1% protocol fee, not the token's tax** (Opus: implied net-into-curve is 1–2% below the event's quote net of fee; Fable: the quote-less windows dropped every ≥3%-tax launch) | Confirmed: the runbook's receipt check would have failed and the nine newer windows were missing 26–45% of launches | Native-curve check rewritten to try the token tax tiers; universes are now comparable (Sep 4: 799 → 1,131 eligible; Sep 5: 1,730 → 2,408); curves whose launch buy does not fit the curve are dropped instead of clamped; the runbook now checks tokens received against the engine's target. |
| **Wording**: at $300 stakes the stake binds on three trades in four, so "$150 a trade" was wrong at that stake (Opus); gas is $0.25 a round trip at current prices, not $1 (Fable) | Confirmed. | Runbook wording fixed; $1 gas kept as the conservative charge. |
| **Setup gaps** (both): public RPC as the default endpoint, world-readable env file that will hold the key, chrony not on Amazon Time Sync, probe unit killed by the 90 s default timeout, no log rotation, the monitoring cron described but not installed, no `coincurve` | Confirmed. | All fixed in `deploy/ohio_setup.sh`; the provider endpoint is a placeholder that must be filled. |
| **Capacity is about one bot** (Fable): one competitor at the same seat takes Sep 4 from +18.9% to +9.8% and Sep 1 to −5.6%; 40% of rule-passing launches already have a buyer at second two | Plausible and consistent with section 21.2's latency table. | Disclosed. The repository itself is the disclosure; a second operator running this rule roughly halves it for both. |

### 22.2 What neither auditor could verify, and neither can this report

Where a wallet from Ohio actually lands in the seat's second (no transaction has been sent); the real slippage limit
of the router buyers behind us; the terms of use (the chain's documentation returned an error to one auditor);
whether the provider endpoints serve the chain from Ohio at the claimed latency and whether the sequencer accepts
direct submissions from anyone; how the seat behaves once a second operator sits in it.

### 22.3 The numbers after the corrections (`sniper_plan.txt`)

Corrected universe, E2 seat 0.3 s behind, 3% of supply, 7 s hold, minOut refusals included, under the final rule:

| window | eligible | rule | mean ROI | median trade | always-on | one at a time |
|---|---|---|---|---|---|---|
| Aug 30 | 1,756 | 175 | +3.7% | +6.6% | $1,861 | $1,433 |
| Aug 31 | 2,086 | 276 | +4.1% | +10.5% | $3,165 | $3,041 |
| Sep 1 | 2,416 | 197 | +1.8% | +12.5% | $971 | $1,264 |
| Sep 2 | 2,173 | 184 | +12.8% | +23.9% | $6,615 | $5,742 |
| Sep 3 night | 1,314 | 68 | +14.0% | +13.9% | $2,824 | $2,685 |
| Sep 3 day | 1,902 | 211 | +14.1% | +17.7% | $8,357 | $8,299 |
| Sep 3 evening | 2,153 | 339 | +12.2% | +19.7% | $11,843 | $11,291 |
| Sep 4 | 1,131 | 87 | +13.8% | +7.5% | $3,424 | $3,136 |
| Sep 5 night | 1,217 | 51 | +9.9% | +2.7% | $1,487 | $1,487 |
| Sep 5 | 2,408 | 136 | +18.6% | +13.6% | $7,381 | $7,491 |
| Sep 6 | 2,394 | 192 | +5.4% | −1.7% | $2,929 | $1,919 |

Compounding from $300 with the engine's defaults (safety switch, −50% stop, 20% sizing): every window ends above
$300 on its own ordering (median $1,754), but the resampled orderings put the four weak windows at a 10–34% chance of
the daily stop. From $100, three of eleven windows end below start; from $200, one; the $300 floor stands.

### 22.4 Verdict, restated after the audits

The mechanism is real, both auditors reproduced the headline tables from the raw data, and the engine now reads the
feed the way the backtest reads the chain and proves it on every scored launch. What the audits changed is the level
of the expectation and the honesty of the risk: the per-trade return an operator should plan on is +5% to +8% on a
busy window, not the fitted +10% to +14%, with the un-gated +3.6% as the floor; a flat day has a one-in-three chance
of ending at the daily stop; profit does not scale past a $300 stake and roughly halves if one other bot takes the
same seat. Nothing has been sent live. The two auditors' own expectations for a $300 start were +$100 to +$800 per
busy six-hour window and −$150 to +$100 per quiet one, and those are the numbers this report now carries forward.

## 23. Round 15: losing less, and landing where the tables assume

Two questions, each put to two independent researchers with the same brief (one Fable 5.1, one Opus 5): how does the
strategy lose less without giving up its return, and how does a retail box in Ohio land where the backtest assumes.
Both risk researchers and one speed engineer delivered in full; the other speed engineer was cut off by an API limit
and re-run. Everything they claimed was re-derived here before it changed anything: the verification harness is
`src/analysis/risk_harness.py` (outputs in `data/derived/risk_harness.txt`), the rival analysis
`src/analysis/risk_blocks.py` (`data/derived/risk_blocks.txt`), and the four deliverables are kept verbatim under
`data/derived/audit_risk_*.md` and `audit_speed_*.md`.

### 23.1 The harness, corrected before anything else

The first thing the reconciliation found was a bug in this project's own verification harness, not in the auditors'
work. Its resampled stop probability shuffled only the trades its own compounding path had taken; when that path hit
the stop early (Sep 6 at a 5 s hold), the pool it shuffled was the losing subset, and it reported a 74% chance of the
−50% stop where the plan script's method (shuffle every rule-passing trade) gives 9%. The harness now uses the plan
script's resampler and reproduces `sniper_plan.txt` window for window (Sep 6: 11% against the plan's 10%); its local
replay is equal to `sniper_exact.replay` on 504 checks, and its take-profit is a single pass over the event grid. The
earlier "shorter holds raise the stop risk on Sep 6" conclusion from the old harness was the artefact and is withdrawn.

### 23.2 What the risk researchers found, and what a triple check made of it

| finding | who | checked here | outcome |
|---|---|---|---|
| The loss is a fat left tail, not a run of small losses: 18–23% of trades end below −40% with p5 near −70%, and the blow-ups do not cluster in time (longest run 2.6 vs 2.7 in shuffles) | both | reproduced (tail 23.1% fit, 18.5% test) | consecutive-loss caps, cooldowns and per-hour caps cannot help; confirmed by both and here |
| Hold 7 s → 5 s | both | fit +5.4% → +8.3%, stop odds 18% → 2%; test +12.3% → +12.0%, 2.8% → 1.7%; leave-one-window-out picks 5 s in 11 of 11 folds (Opus) | adopted. Hold 4 s (Opus's in-sample pick) is fragile out of sample: worst window +1.5%, stop odds up to 17% |
| Take-profit at +50% over the entry price, computed from the feed | Fable (+50%), Opus (+35/+50%) | at hold 5: fit +8.3% → +9.0%, test +12.0% → +12.7%, tail 14.1% → 11.3%; at hold 7 test +14.1% | adopted; it needs the engine to price the curve live, which v4 does by folding every feed buy and sell (router buys over-count, so a wrong trigger exits earlier, never later) |
| Sizing 15% of bankroll with a $25 floor instead of 20% / $50 | Fable | stop odds 2.1% → 0.2% fit, 1.7% → 0.5% test at hold 5; compounding −28% (own-path gains $10.5k → $7.5k fit, $24.4k → $21.2k test) | adopted as the default for a small bankroll; 20% / $50 stays a documented option |
| "Seat-clear gate": skip the launch if any surcharge-paying buy is stamped before 2.0 s after the creation | Opus | see below | adopted in its executable form |
| Daily stop −30%, tighter switch, E1 seat, 10 s hold, price stop-loss, reactive dump exit, hour-of-day, creator ≥ 8% or tier gates | both (rejected) | reproduced where re-run: −30% stop raises stop-outs to 37% fit; switch variants cost gains and buy nothing; E1 worse on both axes; feature gates keep 15–40% of trades | rejected |

The seat-clear gate needed the most work, because its threshold is not what it looks like. The replay's clock is
interpolated between block-timestamp anchors that are a median 36 s apart, so "2.0 s after the creation" is not a
chain-time boundary; and of the 357 surcharged buys the gate keys on (four sample windows), 352 are in the +0.19% band,
that is outsiders who already sit in second two, our own seat. Counting blocks instead of seconds
(`risk_blocks.txt`) shows the gate is the same as "an outsider bought within 20 blocks of the creation" (100% of those
launches skipped, 3% of the rest), and that the creation's own position inside its second does nothing on its own
(gating on it alone leaves fit stop odds at 32%). What the gate finds is a rival ahead of us:

| first outsider in second two | fit n | fit ROI (7 s) | test n | test ROI (7 s) |
|---|---|---|---|---|
| none | 652 | +10.2% | 486 | +19.6% |
| within 12–16 blocks of the creation | 39 | −12.3% | 121 | +1.5% |
| 16–20 blocks | 61 | −8.4% | 191 | +2.1% |
| 20–24 blocks | 57 | −15.0% | 177 | +8.8% |
| 24–30 blocks | 20 | +1.6% | 60 | +25.2% |

Only what is seen before our own transaction leaves the box can gate it. The executable form is to send a fixed
0.3 s into second two and only if no outsider has bought by then; that is already the replay's entry for launches
nobody else took (2.0 s plus the 0.3 s latency it charges), so the kept launches are modelled exactly, and a launch
whose first outsider lands later than 0.3 s is still modelled with us behind that outsider, which is pessimistic.
Waiting longer keeps helping in the tables (0.5 s: fit +11.2%) but every extra tenth is time for the launch team's
dump, so 0.3 s, the replay's own assumption, is the rule:

| rule (all at 20% / $50 unless stated) | fit ROI | fit stop odds (max) | test ROI | test stop odds (max) | one at a time fit / test |
|---|---|---|---|---|---|
| current: hold 7 | +5.4% | 18.1% (32) | +12.3% | 2.8% (11) | $11,481 / $36,308 |
| hold 5 | +8.3% | 2.1% (2) | +12.0% | 1.7% (9) | $17,955 / $35,671 |
| wait 0.3 s for a rival, hold 7 | +7.3% | 9.6% (21) | +15.6% | 0.9% (3) | $15,006 / $35,179 |
| wait 0.3 s, hold 5 | +10.4% | 0.7% (1) | +15.6% | 0.2% (1) | $21,152 / $34,962 |
| wait 0.3 s, hold 5, take-profit +50% | +10.7% | 0.4% (1) | +16.4% | 0.0% (0) | $21,998 / $37,405 |
| the same at 15% / $25 | +10.7% | 0.0% (0) | +16.4% | 0.0% (0) | $21,998 / $37,405 |
| wait 0.3 s, hold 4 | +11.7% | 0.1% (0) | +13.7% | 0.1% (0) | $23,979 / $31,095 |
| skip any launch an outsider ever takes (look-ahead, not executable) | +12.9% | 0.1% | +18.9% | 0.1% | $22,554 / $25,993 |

### 23.3 The rule after this round

Bundled launch (three or more named wallets buying at least 0.3 ETH in the creation second), creator's launch buy at
least 1% of supply, no outsider in second one; **0.3 s into second two, send only if no outsider has bought the curve
yet**; 3% of supply capped by the stake; sell after 5 s, or as soon as the curve price is 50% above our entry; one
position at a time; 15% of the bankroll per trade, stakes $25–$300; daily stop −50%; safety switch off when the last
15 scores average below −10%. Engine v4 implements every piece (`OUT2_MAX=0`, `SEAT_WAIT_MS=300`, `HOLD_S=5`,
`TAKE_PROFIT=0.5`, `FRAC=0.15`, `STAKE_MIN=25`).

| window | rule-passing | mean ROI | trades below −40% | one at a time, $300 stakes | from $300, engine defaults | stop odds (resampled) |
|---|---|---|---|---|---|---|
| Aug 30 | 155 | +8.9% | 13% | $3,800 | $1,497 | 0% |
| Aug 31 | 251 | +9.7% | 14% | $6,146 | $3,717 | 0% |
| Sep 1 | 184 | +8.7% | 16% | $4,376 | $1,805 | 0% |
| Sep 2 | 169 | +16.1% | 15% | $7,677 | $5,693 | 0% |
| Sep 3 night | 51 | +16.6% | 8% | $2,418 | $894 | 0% |
| Sep 3 day | 171 | +20.9% | 9% | $10,022 | $7,658 | 0% |
| Sep 3 evening | 284 | +18.0% | 11% | $14,293 | $12,367 | 0% |
| Sep 4 | 66 | +9.5% | 0% | $1,779 | $632 | 0% |
| Sep 5 night | 43 | +16.0% | 5% | $2,077 | $728 | 0% |
| Sep 5 | 105 | +16.3% | 6% | $5,085 | $2,722 | 0% |
| Sep 6 | 89 | +7.6% | 7% | $1,730 | $571 | 0% |

Fit half (Aug 30–Sep 2): 759 trades, +10.7% per trade, worst window +8.7%. Test half (Sep 3–6): 809 trades, +16.4%,
worst +7.6%. Against the section 22 rule the one-at-a-time net rises from $11.5k to $22.0k on the fit half and from
$36.3k to $37.4k on the test half, the compounding paths from $300 go from $5.6k / $24.0k to $11.5k / $23.5k at the
safer sizing ($15.0k / $27.2k at 20% / $50), and the resampled chance of the −50% stop is zero in every window at
either sizing (at most 1% at 20% / $50). The trade count falls by 9% fit and 25% test: those are the launches a rival
had already entered.

Smaller starts, same rule, 1,000 resampled orderings per window: from $50 the stop is hit 19% of the time on the fit
windows and 6% on the test windows (25% on the worst), because a $25 floor is half the bankroll; from $100 it is 4.2%
fit and 0.7% test (7% on the worst window), with own-path gains of $5.3k over the four fit windows and $16.3k over the
seven test windows; from $150 it is 0.9% and 0.0%; from $200 and above 0.1% or less. $100 is the floor, $150–$300 is
comfortable.

What is in-sample here: the 5 s hold and the +50% take-profit were chosen on the earlier half (Fable's grid, Opus's
hold sweep) and only confirmed on the later one; the 0.3 s wait was not tuned (it is the replay's existing entry); the
data is still eleven six-hour windows over 26 days of one launchpad. What the replay cannot know: its clock is
interpolated, so the seat's timing carries about ±0.2 s of noise; rivals may adapt to a wallet that stands down; and
the take-profit relies on the engine's live price, which router buys over-state. What is pessimistic: every launch
whose first outsider arrives after our send is scored as if we were 0.3 s behind that outsider.

### 23.4 Speed: what the engineers found, and what was verified

| claim | verified here | done in engine v4 |
|---|---|---|
| The buy as built cannot be signed: `eth_account` rejects a lowercase `to` address | reproduced (`TypeError: Transaction had invalid fields`); a checksummed `to` with the same hex fields signs | every address in a built transaction is checksummed; the docstring says so for the operator's signer |
| Sender recovery costs 5.5 ms without coincurve, 0.41 ms with it, 0.11 ms straight from coincurve; 89% of recoveries are router transactions whose sender is never used | reproduced on the same 300 transactions | direct coincurve recovery with a start-up self-test against `eth_account` (falls back if it fails); router senders recovered lazily, only when the transaction names a curve being traded; `REQUIRE_COINCURVE=1` refuses to run slow |
| The feed loop as written is busy 17% of the time without coincurve and delays its own arrival stamps (median 11.1 ms per frame, p99 79 ms) | reproduced; v4 on the same 7-minute capture without coincurve: median 0.26 ms per frame, busy 3.5% | as above, plus the flip is published after the message's transactions are indexed, so a wake never reads a half-indexed block |
| The curve state is rebuilt twice after the boundary by scanning 4,000 calldatas (2.2–2.6 ms) | reproduced (1.1 ms per scan, 2.8 ms on this box) | reserves and gate counters are folded incrementally as each buy and sell arrives; the send path reads two floats (0.5 µs measured) |
| Polling with `sleep(0.001–0.002)` wakes 0.85–1.2 ms late at the median and up to 16–20 ms late | reproduced by the engineer's benchmark | one `Condition` notified per feed message; predicted boundaries sleep to 4 ms before and spin the rest |
| Cold TLS costs 87–133 ms here (4–10 ms in Ohio, inferred); connections lived in per-thread locals and every launch ran in a new thread | reproduced | `SENDER` keeps warm keep-alive sockets to the sequencer and the provider, pings them every 5 s and logs their round trips (`sender_rtt`) |
| The boundary estimator used only the upper side of each second's bracket; a two-sided midpoint is inside the bracket 75% of the time against 66%, early 14% against 32%, and needs a 15–20 ms margin instead of 40 | reproduced on the capture (the 75% ceiling is this sandbox's proxy jitter) | two-sided bracket estimator, cached, with its width logged (`boundary` events) |
| `tune_margin` only ever went up (a first-block landing changed nothing) | confirmed in the code | one-sided quantile controller targeting 1% early landings, floor 8 ms, cap 45 ms, run off the trade thread; landings log the transaction index |
| A log write and a thread start sat between the boundary and the send; `max_queue` let stale frames carry fresh stamps; a dead feed took up to 40 s to notice; wall-clock stamps move with chrony steps | confirmed | log writes on a queue, scorer thread started after the send, `max_queue=4`, no compression, a 2 s watchdog, monotonic clock on the critical path, the collector off while anything is in flight |
| The two-sided midpoint estimator (the first engineer's proposal, adopted in v4) is a tail statistic: on the second engineer's captures it swings 75–146 ms at 30 flips and 21–116 ms at 60 and sits 12–59 ms late, so it would land in the first block only 45–58% of the time at zero margin; an interval vote (each bracket votes for the milliseconds it covers) is stable to 6–25 ms at 30 flips and 1.5–24 ms at 60 with 86–92% first-block landings | reproduced: the auditor's script re-run on both captures, then the engine's own implementation replayed on them (sd 25.3 / 23.3 ms and 6.5 / 1.4 ms at 30 / 60 flips, first block 88–93%) | v4.1 uses the interval vote on reference-relative brackets, needs 30 brackets, logs its confidence (peak votes over brackets) and falls back to react below 0.5 |
| The v4 margin controller (+12 early, −12/99 first block, −6 later block) has its equilibrium at 6–8% early landings, not 1%, because a later-block landing happens 10–15% of the time on the sequencer's own timer even at a perfect margin | confirmed by the arithmetic | +15 ms on an early landing; every 20 landings without one, −2 ms if fewer than 80% were first-block; floor 5 ms, cap 60, start 15 |
| Every creation the feed cannot resolve (88–95% of them, no bundle) polled the RPC for 3 s at 20 ms, which is where the public endpoint's 429s came from; and the feed resolution waited for the whole creation second when the bundle is visible after a few blocks | confirmed in the logs (v15: 158 of 167 creations resolved by RPC) | a launch the calldata already rules out is not resolved at all; a bundled one is resolved the moment `BUNDLE_MIN` named wallets have bought one curve |
| The 5 s warm-up timer after a connect discards live seconds and would accept a slow replay; brackets were kept across reconnects although the route (and theta) may change; a reconnect waited 2 s; every reconnect rebuilt a TLS context (21–25 ms) | confirmed | replay detected per message from its timestamp, brackets and the estimate cleared on reconnect, 0.2 s reconnect, one shared TLS context |
| The feed message's `sequenceNumber` is the L2 block number (checked against the RPC, offset 0) | taken from the auditor's check; not re-run here | `landing` logs `blocks_after_flip` from the feed's own numbering, no RPC needed to place the transaction |

Where the two engineers disagreed, the data decided: the first proposed the midpoint estimator and measured it best on
one long capture; the second measured it at the sample sizes an engine actually has after a reconnect and found it the
worst of the bracket-based estimators; the second's protocol (estimate on 30 or 60 flips, judge on the next 60) is the
one that matches how the estimator is used, and its verdict was reproduced with the engine's own code, so the vote is
what v4.1 runs. The second engineer's other claim, that predicting the boundary would put this operator in the first
block of second two on 80–90% of launches, is an inference from the captures and stays untested; with the rule of 23.3
it is not needed.

The rule change of 23.3 reorders the priorities. The send now happens 300 ms into second two, so predicting the
boundary and shaving milliseconds off it is no longer the point; what matters is that an outsider's buy in the first
three blocks of the second is decoded and indexed before the send (v4: about 0.3 ms per frame), and that the send
itself is one warm round trip. The expected landing is the fourth or fifth block of second two, 350–450 ms after the
boundary, which is the replay's 2.3 s entry. The proof is in the first live receipts: `trade_decision` logs
`seat_flip_to_send_ms` (should read about 300) and `blocks_to_seat`, and `landing` logs the block, its timestamp
against the seat's second and the transaction index. Predict mode, the margin controller and the estimator stay for
E1 or for an operator who wants to be first in the block.

### 23.5 Verdict

The strategy loses less by not trading when someone faster is already in the seat, by holding five seconds instead of
seven, and by taking a +50% gift when the curve hands it over; each of those was found by two researchers
independently, re-derived here, and holds on the half of the data it was not chosen on. Per trade the planning number
is +9% to +12% (fit +10.7%, test +16.4%, none of the eleven windows under +7.6%); from $300 the windows end between
$571 and $12,367 on their own orderings (median about $1,800), with no window below the start and a resampled chance
of the daily stop of zero; from $100 the same rule ends between $148 and $10,083 with the stop hit at most 7% of the
time. Nothing has been sent live; engine v4 is running as a dry run, and the runbook says which log lines have to match
these tables before the first real transaction.

### 23.6 September 7–10: ten windows that were never seen

Everything above was chosen on Aug 30–Sep 2 and confirmed on Sep 3–6. After the rule was fixed, ten more six-hour
windows were pulled (Sep 7 night, day and evening; Sep 8 night, day and evening; Sep 9 night, day and evening; Sep 10
night: `src/collect/pull_v2_curve.py`, block anchors from `pull_anchors.py`) and scored with the same harness and no
further choice (`data/derived/risk_harness_sep.txt`, `risk_seats.txt`).

| window | rule-passing | kept (no rival) | mean ROI | trades below −40% | one at a time, $300 | end bankroll from $300, 15% / $25 | stop odds |
|---|---|---|---|---|---|---|---|
| Sep 7 night | 193 | 136 | +9.3% | 11% | $3,589 | $906 | 0% |
| Sep 7 day | 128 | 74 | −0.6% | 7% | −$92 | $321 | 0% |
| Sep 7 evening | 276 | 200 | +5.8% | 8% | $3,614 | $1,426 | 0% |
| Sep 8 night | 81 | 61 | +12.5% | 8% | $2,128 | $726 | 0% |
| Sep 8 day | 103 | 75 | +3.2% | 5% | $713 | $395 | 0% |
| Sep 8 evening | 188 | 145 | +5.0% | 11% | $1,831 | $516 | 0% |
| Sep 9 night | 94 | 72 | +6.3% | 3% | $1,363 | $466 | 0% |
| Sep 9 day | 67 | 43 | +7.4% | 5% | $912 | $438 | 0% |
| Sep 9 evening | 35 | 21 | +1.5% | 10% | $110 | $301 | 0% |
| Sep 10 night | 48 | 28 | +15.1% | 0% | $1,178 | $527 | 0% |

Ten windows, 855 kept launches of which 840 executed (15 minOut refusals, charged gas in the dollar columns), +6.2% per
executed trade, nine of ten windows positive, worst −0.6%, tail 7.7%, one-at-a-time $15.3k (a number that needs $300
available on every launch; from a $300 bankroll the same windows compound to $3.0k of gains in total, median window
about +$190, best +$1,126, worst +$1), resampled stop odds 0.1%. Section 23.8 narrows the per-trade figure to a range. At 20% / $50 sizing the gains are $5.3k with stop odds of at most 6%. From $100 the $25 floor meets
$1 of gas per round trip on windows that pay 2–3%, and the stop odds reach 98% on Sep 7 day: a $100 start is no longer
advised while the flow is this thin. The section 22 rule (hold 7, no gate) on the same windows: +6.1% per trade,
$7.3k of gains at its bigger sizing, stop odds up to 18%. The rule held out of sample; what changed is the level.

**Why the level fell.** The launch teams did not change; the other bots did. Of the bundled launches, the share with an
outsider already buying in second one (which the rule excludes) went from 14% on Aug 31 to 67% on Sep 9, and the share
of the rest with a rival in second two within 0.3 s from 7–11% (Aug 30–Sep 2) to 23–42% on the ten new windows (54% on
Sep 6), about a third overall. The rule therefore
keeps 21–200 launches per window instead of 87–339, and the launches it keeps have fewer follow-on buyers (4–8 buys
inside the hold against 7–10 before). Per window, the three classes of bundled launch and the E1 seat:

| window | E2 rule (kept) | E2, second-one outsider present | E2, seat rival | E1 front, all bundled | E1 0.3 s behind, all |
|---|---|---|---|---|---|
| Aug 31 | 248, +10.1% | 45, −1.5% | 25, −9.2% | 322, +5.7% | 317, +4.0% |
| Sep 3 day | 165, +20.5% | 125, +0.4% | 37, +6.5% | 341, +17.1% | 328, +13.1% |
| Sep 5 day | 104, +23.5% | 237, −2.9% | 31, +9.5% | 374, +3.3% | 355, −1.1% |
| Sep 7 day | 73, +2.2% | 152, +15.2% | 50, −0.5% | 284, +16.4% | 257, +6.0% |
| Sep 7 evening | 199, +6.2% | 280, +18.7% | 76, −5.6% | 559, +13.8% | 510, +4.5% |
| Sep 8 day | 75, +1.9% | 188, +1.8% | 28, −3.1% | 291, +3.1% | 273, −3.2% |
| Sep 8 evening | 139, +7.3% | 210, −0.4% | 43, +6.2% | 408, +8.8% | 370, −0.5% |
| Sep 9 day | 43, +8.9% | 146, +4.8% | 24, +7.7% | 213, +12.5% | 173, −1.3% |
| Sep 9 evening | 21, +4.0% | 180, −2.9% | 14, −10.8% | 219, +5.9% | 182, −4.8% |

Two things were tested on this and rejected. Trading the launches with a second-one outsider (the class the rule
excludes) looked attractive on Sep 7 (+15% to +19%) and is nothing on Sep 8–10 (−6% to +5%); over all twenty windows
it is −6.6% on the fit half, 0.0% on the test half and +5.6% on the new one, with stop odds of 35–52%. A per-class
switch that trades a class only while its own last 20 scores average above +3% captures Sep 7 and gives it back on
Sep 8 (19 trades at −28%); its total over twenty windows ($36–42k) is within noise of the static rule ($38.5k) and its
risk is worse. Tighter safety switches (+3% or +5% over 30 scores) cost gains on every half and save nothing, because
the new windows are thin, not negative.

**Where the flow went.** The E1 seat, first in second one and paying +6.18%, on every bundled launch. At the exit the
engine runs (hold 5 s, take-profit +50%) the front of that seat pays +8.7% per trade on the ten new windows (2,970
launches, ten of ten positive, median trade +4.8%); at a 7 s hold with no take-profit it shows +13.1%, but that mean is
carried by a thin right tail (median trade +0.8%, 17% of trades below −40%) and is not the engine's exit. It is a
knife edge: one block behind the first outsider it pays +3.8% with stop odds of 24%, 0.3 s behind −0.1% with stop odds
of 64%. The replay's "front" means ahead of every other outsider in that second; on chain the first outsider of second
one sits in its very first block on a third of launches (section 21.5), so a sender that lands in the first block is in
front on the other two thirds and in a coin flip on the rest. The auditor's expected value under stated landing mixes
(section 23.8): +7.0% per attempt at 85% first-block landings, +6.5% at 80% with 7% early, +4.8% at a coin flip on the
boundary, so +5% to +7%, provided an early landing (the creation second, 93–98% tax) is refused by the minOut: verified
on a live curve by simulation (23.8). That cannot be proven in a dry run; it needs live receipts. It is the next test,
at $5 to $10 stakes over thirty launches (about $2 each in gas and surcharge), before any capital goes to E1.

**Verdict, restated.** The clean-seat rule is real and still positive, but in the September regime it is a +6% trade
on 20–200 launches per six hours: from $300, about +$200 per busy window and about zero on a thin one, gas included,
with the daily stop a 1-in-1,000 event. It is not the +$1,500 per window of Sep 3–6, and it will not be while two
thirds of the bundled launches carry a bot in second one. The engine's own scores are the gauge: rule-passing launches
per six hours and the mean score of the last 60 (runbook section 6).

### 23.7 What could kill it, and what was done about each

Nine ways this stops paying, ranked by likelihood, each measured and answered (`data/derived/risk_killers.txt`;
`src/collect/chain_checks.py`, `src/analysis/risk_killers_harness.py`, `risk_killers_harness2.py`). An independent
auditor re-derived section 23.6 and the E1 analysis from the raw files in parallel (`data/derived/audit_sep_opus.md`).

| # | killer | what was measured | what is in place now |
|---|---|---|---|
| 1 | **Competition in the seat** (in progress: second-one bots on 14% → 67% of bundled launches) | The seat the bots moved to, first in second one, at a 7 s hold with no take-profit pays +13.5% at the front on the ten September windows, +7.0% one block behind, +4.9% two behind, +3.3% at 0.3 s; under landing mixes of 90/8/2/0, 70/20/7/3, 50/30/15/5 and 30/40/20/10 (front / block 2 / block 3 / later, an early landing refused for gas) +12.8%, +11.3%, +9.7%, +8.1% on September, +9.7% to +7.6% on the test half, +4.4% to +3.0% on the fit half, where E2 was the better seat. At the engine's own exit (hold 5, take-profit) the front pays +8.7% and the auditor's landing-mix value is +5% to +7% per attempt (23.8). A seat chosen by the regime (E1 when the previous window's second-one occupancy was above 45%, else the E2 rule) makes $69k over the twenty windows against $38k for E2 alone, $45k if every E1 landing is one block late, with stop odds up to 22% on one window | The engine already runs `SEAT=E1 SEND_MODE=predict` with the vote estimator; at E1 an early landing is the creation second, refused by minOut for gas only, so the margin controller now steps +5 ms there instead of +15. The landing position cannot be proven in a dry run: runbook section 9 gives the thirty-launch live test at $5–10 stakes that decides it |
| 2 | **Teams adapt** (dump earlier, or plant a cheap second-one buy to trip the gate) | Two seconds faster dumps (a 3 s hold) leave +3.6% on September, +10.1% / +12.5% on the two earlier halves. A hold re-chosen every window from the previous one earns $39.7k against $38.0k fixed: no gain, the teams' timing has been stable. A planted second-one buy under 0.01 ETH predicts +6.0% (fit and test) and +4.7% (September) against +13.3% / +7.2% clean and −5.5% / +18.5% for buys above 0.05 ETH | The scorer now logs the median first sell after entry and the supply dumped inside the hold (`flow` events); `OUT1_MIN_ETH` lets the gate ignore dust if planting starts (default 0: every buy counts) |
| 3 | **The venue changes the rules** (tax schedule, exemption, ordering) | The sequencer accepts raw transactions from an unknown sender: an unfunded key's transaction is refused for insufficient funds, after signature recovery, at both endpoints. The factory (4,416 bytes) carries `transferOwnership` and no pause or blacklist selector; the curves (10,229 bytes) and tokens (3,248 bytes) carry none of 28 candidate blacklist, pause, trading-switch or upgrade selectors | A schedule alarm: every scored launch's surcharges must fall in the three known bands; when half of the last twenty do not, trading stops and `alarm` is logged. A factory-silence alarm after 30 minutes without a creation on a live feed. The chain's terms of use could not be fetched from here (503); this stays the operator's call |
| 4 | **The flow dries up** | Bundled launches per window are stable (218–387); the second launchpad on the chain (factory 0x7ed5…) logs 30–36k events a day against 14–19k for Pons V2 and was never tested for the same mechanism | The `flow` event every five minutes: rule-passing launches in the last hour and six hours, mean score of the last 60, creations seen; runbook section 6 turns it into a stop rule |
| 5 | **Gas** | Measured from Sep 9 receipts: a direct buy uses 97,676 gas, a direct sell 78,243, at 0.18 gwei; the round trip with an approve is **$0.10**, not the $1 the tables assumed (router transactions use 4× more). At the measured gas a $100 start has stop odds of 1.4% / 0.2% / 2.4% (max 14%) on the three halves and $50 of 11% / 3% / 14%; at a planning gas of $0.25, $100 gives 1.7% / 0.3% / 3.3% (max 20% on one September window) | The engine prices the round trip with the measured units; `eth_gasPrice` on this chain equals the base fee, and a transaction sent at exactly that price was refused when the fee ticked up (`max fee per gas less than block base fee`), which would have lost the first live buy: `GAS_HEADROOM=2` now sends at twice the quote (about $0.05 extra per trade) |
| 6 | **Live execution not matching the replay** | The operator's send step, exactly as the runbook shows it, signs the engine's own transaction dict, fires through the warm sockets to the sequencer and the provider, and returns their answers; with a throwaway key the only refusal is insufficient funds. In react mode with the 300 ms wait an early (second one) landing is impossible by construction; the sensitivity if it happened on every trade is +8.3% / +12.9% / +1.0% | Runbook section 5's checklist plus `landing` events with the block, its timestamp against the seat's second, the transaction index and blocks after the flip |
| 7 | **One-off operational failures** | The lowercase-address landmine (round 15) and the fee-headroom landmine (this round) were both found by trying to sign and send the engine's real output | Both fixed; the reference send step is tested; the runbook's monitoring cron, restart-with-open-position recovery and state file cover the rest |
| 8 | **Rules and blacklists** | No blacklist or pause code in the token, curve or factory (above); the terms of use unresolved | The operator's call, as before |
| 9 | **Statistics** | Bootstrap over the ten September windows: mean per trade +6.2%, 90% interval +4.4% to +7.9%, probability of a negative mean 0.000; the thin windows' own intervals include zero (Sep 7 day −5.3% to +4.3%, Sep 8 day −1.5% to +7.6%, Sep 9 evening −8.9% to +11.8%) | Small sizing, the stop, and the go-live checkpoints; nothing else can be done about sample size but waiting |

The one killer already in motion is the first. The answer to it is not a parameter but a different seat, and that seat is
a first-block race whose outcome only live receipts can show. Everything else on the list is either measured harmless
today (gas, blacklists, the sequencer), or wired to an alarm the operator reads in the log before it costs a trade.

### 23.8 The audit of 23.6, and what it changed

An independent auditor re-derived section 23.6 from the raw event files with its own loader and replay
(`data/derived/audit_sep_opus.md`). The per-window table reproduced to the digit (one launch of 855 differs), the
flow shift reproduced (14.3% → 68.5%), the exit modelling was found conservative (selling later than the modelled
0.3 s helps; the sell tax matches the tier to four decimals over 360k sells), no double count, no survivorship loss
(the native-quote fallback drops zero rule-passing launches), and the second-one gate has no material look-ahead (two
launches in 1,756 vetoed by a band buy after our send). Six points needed an answer; each was tested here
(`data/derived/risk_audit_checks.txt`; `src/analysis/risk_audit_checks.py`, `src/collect/chain_checks_slippage.py`).

**1. The later buyers' slippage tolerance is an unpinned constant, and at 5% the result halves.** True, and the tables'
10% never binds (10%, 25% and "no reverts" give identical numbers), so the tables were the optimistic edge. The real
tolerances were read from 79 direct buyers' calldata on Sep 9: 59% send no minimum at all, and of the rest 28% sit at
or below 5%, 41% at or below 10%, 69% at or below 25%. Replayed with that mix (each later buyer drawn from it; router
buyers, whose minimum is not decoded, treated like direct ones): fit +7.2%, test +13.0%, September +3.9%; with every
router buyer at 5%: +5.1%, +10.0%, +2.9%. A buyer who reverts may resend, which the replay does not allow, so the truth
sits between the mix and the tables. **The planning number for September is +4% to +6% per trade, not +6%.**

**2. The gate's 0.3 s threshold is on a clock the data cannot resolve** (the creation's position inside its second is
interpolated, and the derived lag falls outside its feasible range on 35–44% of launches). True. Read on the entry's
own clock instead (skip when the first second-two outsider is stamped before 2.3 s), the ten windows give +8.4% on 523
launches and $12.4k one-at-a-time against +6.2% on 855 and $15.3k; the look-ahead bound (skip any launch a rival ever
takes) +8.3% on 473; widening the second-two surcharge band changes nothing; off-grid fee tiers are 5 launches in
2,430. So the gate's existence is robust (every reading beats no gate by 2.6–4.8 points) and its calibration is not:
**per trade +6.2% to +8.4%, one-at-a-time $11.3k to $15.3k, compounding gains $2.1k to $4.3k over the ten windows.**
Live, the rule is exact (no outsider seen before the send at 300 ms into the second) and the dry run's
`seat_flip_to_send_ms` and `out2` counts are the calibration the backtest lacks.

**3. The tuned exit lost on the newest windows.** True for September alone: hold 7 with no take-profit makes +8.6% and
$20.2k there against +6.2% and $15.3k, at a tail of 11.6% against 7.7%. Over all twenty-one windows the picture is flat:
compounding gains from $300 sum to $38.0k for hold 5 with the take-profit, $39.4k for hold 6, $38.0k for hold 7, and
$32.5k for hold 7 without it (with 4% stop odds on the fit half). The hold is a plateau between 5 and 7 s once the
take-profit is on; the default stays at 5 s because it has the smallest tail, and the runbook says what the longer
hold would have earned.

**4. The E1 seat was priced at an exit the engine does not run, and its early-landing branch was unmodelled.** Both true;
23.6 now carries the engine's-exit figure (+8.7%) and the auditor's landing-mix value (+5% to +7%). The branch was
closed by simulation: a buy sent to a live curve with an impossible minimum reverts with the curve's slippage error
(`0x71c4efed`, carrying the tokens it would have given), and with a zero minimum returns the tokens; an early landing
in the creation second delivers about a twentieth of the sized tokens against a minimum of three quarters, so it is
refused for gas. The margin controller at E1 therefore steps +5 ms on an early landing, not +15.

**5. "Three or more named wallets" is three or more tax-free buys.** True: the event data has no sender, and the tables
count buys. The live engine now logs both (`bundle` buys and `bundle_wallets` distinct senders) on every decision and
gates on buys, as the tables do; the dry run shows how often the two differ.

**6. Two confirmation windows (Sep 5 and Sep 6) had four or five block anchors in six hours.** True; dense anchors (one
per 300 blocks, 16,574 in all from Aug 30 to Sep 10) were pulled for every earlier window and the tables re-run on them
(`data/derived/risk_harness_dense.txt`). The final rule reads fit +10.3% and test +15.4% per trade (against +10.7% and
+16.4% on the sparse anchors), one-at-a-time $20.0k and $33.3k (against $22.0k and $37.4k), stop odds still zero on
every window; single windows move by up to four points (Sep 4 day +6.1% from +9.5%, Sep 5 day +18.9% from +16.3%,
Sep 6 +5.3% from +7.6%). The confirmation half survives; the earlier tables were one point too high.

The auditor's ranked weakest point is the one this section cannot remove: one launchpad, one chain, 21 windows over
29 days, and a regime that deteriorated inside the sample. Nothing in the data says the deterioration stops where the
data stops.

### 23.9 The box, re-verified

The choice of an EC2 instance in us-east-2 rests on the sequencer's location, which was re-checked on Sep 10 rather than
carried forward: `sequencer.mainnet.chain.robinhood.com` resolves to three addresses, all inside Amazon's published
us-east-2 EC2 ranges, one per availability zone, behind an Envoy front; the feed and the public RPC resolve to
Cloudflare, the sequencer host refuses WebSocket upgrades and the Nitro feed ports are closed, so the feed has no
Cloudflare-free path. A cloud-hosted sequencer has no colocation; an instance in its region is the best any operator
can do, and the only refinement left is the zone, which the engine now measures itself (it pings each address, pins
the fastest socket and logs the three round trips every twenty minutes: from this sandbox 34.9, 38.1 and 41.3 ms, a
spread that on an Ohio box separates the sequencer's own zone from the other two). Runbook section 3 has the zone test.

### 23.10 The terms of use, read

The Robinhood Chain Terms of Service (docs.robinhood.com/chain/terms-of-service, last updated August 24, 2026, provider
RHDA, LLC) were fetched and read in full on Sep 10. What they govern, in their own words (section 1): "your access to
and use of Robinhood Chain Sequencer, Robinhood Chain Public RPC, Full Node Snapshot, and the Robinhood Chain Testnet
... and any other content, tools, documentation, SDKs, features, and functionality made available on or through
https://docs.robinhood.com/chain (collectively, the 'Services')". The sequencer feed is listed on the documentation's
connecting page next to the sequencer and the public RPC ("The following public endpoints are available but are
rate-limited and not recommended for production use"), so it is a Service. What they do not govern (section 2.1):
"Robinhood Chain itself, including its protocol smart contracts and any associated bridging contracts ... is not part
of the Services", and "Robinhood does not control what third parties build on Robinhood Chain, the activity of such
parties, any user transacting on Robinhood Chain".

The clause the earlier rounds flagged is section 2.3, Network Abuse or Security Violations, a Prohibited Use: "Any
activity that interferes with, disrupts, degrades, or attempts to circumvent the intended operation, security, or
integrity of the Services, or any underlying blockchain or infrastructure, including unauthorized access attempts,
use of automated tools (such as bots, scrapers, or spiders), denial-of-service activity, or bypassing technical or
usage restrictions." There is no clause on MEV, front-running, sniping or trading strategy. Two further covenants
matter: section 2.4, "you will use the Services solely for lawful testing, experimentation, evaluation, and
development purposes", and section 2.2, no VPN or proxy "to mask or misrepresent your identity, location, or IP
address" (an EC2 instance is neither). The Onchain Integrations Terms (July 1, 2026) bind users of the Robinhood
mobile app's wallet and its protocol integrations, prohibit "wash trading, spoofing, layering, or other forms of
market manipulation" (7.1.4), and do not apply to a self-generated wallet used through a third-party node. The
launchpad's interface is operated by Pons Labs, LLC and is unavailable in the UK and EU according to third-party
summaries; its site refuses connections from this sandbox, so its interface terms could not be read, and the engine
never uses the interface, only the contracts.

**What this means, in plain terms.** The engine as configured uses two Services: it reads the sequencer feed and it
posts transactions to the sequencer. Both are automated. Read one way, section 2.3 prohibits automation only when it
"interferes with, disrupts, degrades, or attempts to circumvent" the Services, and one WebSocket client plus one
transaction per launch does none of that; read the other way, "use of automated tools (such as bots ...)" is listed
as a prohibited use in itself, and section 2.4 limits the Services to testing and development. The second reading is
the one a lawyer for Robinhood would give. Nothing in either reading touches the trade itself: the chain and its
contracts are outside the terms, and every wallet on the chain transacts through some sequencer.

**The posture that removes the question.** Use no Robinhood Service at all: a third-party node (the documentation
itself recommends Alchemy, QuickNode, Blockdaemon, dRPC and Validation Cloud, and Alchemy publishes a Robinhood Chain
WebSocket) for detection and for sending. The engine now supports it (`FEED_SOURCE=provider`, `PROVIDER_WS=...`):
the node's `newHeads` gives the chain's second, its Buy and Sell logs carry the curve and the buyer in their topics
(verified: the buyer topic equals the transaction's sender) and the amounts in their data, the factory's log marks a
creation and one call fetches its calldata for the named wallets. Everything downstream is unchanged. The cost is the
node's own delay: on the replay a detection 150 ms later than the sequencer feed keeps the same return per trade and
takes 10% fewer trades (September: 770 against 855, $2.5k against $3.0k from $300); 300 ms later, 20% fewer. The E1
seat is not reachable this way. The path was exercised against a synthetic node in the sandbox (a creation, three
named buys, the seat's second, a decision at 300 ms); a real provider WebSocket must be watched for a day in dry run
before it is trusted.

That is the whole answer available from here: the terms are ambiguous on automation, silent on the trade, and
avoidable by using a provider's endpoints at a cost of about a tenth of the trades. The recommendation is posture A
with B armed: the terms' only remedy against a client is to refuse it access (the sequencer "cannot modify, reverse,
or cancel transactions" and holds no funds), the engine sends through the provider as well as the sequencer already,
and it now switches detection to the provider by itself after five refused feed connections. So A costs nothing
extra if the door closes, and B is what remains.

### 23.11 Why the edge thinned, measured, and what still pays

The September windows pay +6% a trade against +11% to +16% before. The question was whether that is the day, the
competition, the buyers or the sells, and what, if anything, restores it. Every number below is from the exact-curve
replay of the twenty-one windows in the harness cache (`src/analysis/edge_anatomy.py`, `edge_gauge.py`, `edge_fix.py`,
`edge_stops.py`, `edge_seat.py`, `edge_seat2.py`; outputs in `data/derived/edge_*.txt`).

**The return, taken apart.** For each kept launch (bundled, creator ≥ 1%, no outsider in second one, nobody in the seat
before our send 0.3 s into second two) the return at the engine's exit (hold 5 s, +50% take-profit, $300) is split into
three parts on the exact curve: *base*, the token's fee, the seat's +0.19% and our own impact in and out (the return if
nothing happened while we held); *buys*, what the buyers who came after us add; *sells*, what the sells inside the hold
take. Per half of the data (fit Aug 30–Sep 2, test Sep 3–6, September Sep 7–10):

| half | windows | kept per window | ROI a trade | = base | + buys | + sells | later buys per hold | later ETH per hold | bots in second one | seat rivals |
|---|---|---|---|---|---|---|---|---|---|---|
| fit | 4 | 124 | +10.7% | −2.5% | +26.4% | −10.5% | 7.2 | 0.36 | 24% | 10% |
| test | 7 | 108 | +14.2% | −2.8% | +24.5% | −9.7% | 6.3 | 0.35 | 50% | 27% |
| September | 10 | 84 | +6.9% | −3.0% | +18.1% | −10.9% | 6.2 | 0.26 | 62% | 32% |

The fees did not move and the sells did not move: the teams dump the same share of supply (5–7%) at the same time.
The whole drop is in the buys: the people who buy after us bring 28% less ETH per hold (0.36 → 0.26 ETH), a little
fewer of them and smaller. Across the twenty-one windows the kept launches' return correlates +0.88 with the later ETH
per hold, +0.59 with the creator's own buy, and only −0.15 with the share of bundled launches carrying a bot in second
one and −0.38 with the share of seat rivals; the later buyers per hold do not correlate with the bots (−0.08). The
chain-wide bonding-curve volume in the window (every curve, every buy: 30k–350k ETH a window) predicts nothing
(−0.08). So on the launches we keep, the competition does not cost return; it costs *trades*: the clean share of
bundled launches fell from 67% (fit) to 38% (test) to 29% (September), 124 → 108 → 84 kept per window, while bundled
launches per window stayed at 250–300. Of the drop in gains per window from the first four windows to September, 45% is
fewer trades (crowding) and 55% is less return per trade (demand); from the strongest seven windows, 22% and 78%.

**It depends on the day, and on the hour.** Window by window the kept launches pay −0.3% (Sep 7 12–18) to +21.7%
(Sep 3 12–18); the follow-on ETH per hold runs 0.17 to 0.47 and the two move together. By hour of day, September's
loss is concentrated in the US day:

| UTC hours | test half, n / ROI | September, n / ROI | bots in second one |
|---|---|---|---|
| 0–6 (US evening) | 96 / +15.1% | 290 / +10.1% | 55–68% |
| 12–18 (US morning) | 400 / +15.5% | 191 / +3.0% | 35–49% |
| 18–24 (US afternoon) | 262 / +16.4% | 359 / +5.6% | 38–61% |

The night hours have the most bots in second one and the best returns, which says the same thing as the correlations:
demand sets the return of a kept launch, the bots set how many there are. Three nights of evidence is a lean, not a
law; the engine runs around the clock and the readout below tells the operator which regime the hour is in.

**Five things tried against it, three rejected.**

1. *Read the demand live and size to it.* The engine scores every bundled launch 25 s after it, so the ETH later
   buyers brought inside the hold is known then. The rolling mean over the previous twenty scored launches, taken
   before the next send, sorts the next return by bin over all windows (below 0.25 ETH +3.6% a trade, 0.25–0.35
   +8.4%, 0.35–0.5 +11.3%, above +13.2%), but launch by launch it is noise (r = +0.05): a bad hour and a good hour
   are told apart, two consecutive launches are not. Sizing to it (off below 0.15, half to 0.25, full to 0.35,
   1.5× above) earns the same return per trade as the flat rule, and its gains ($13.3k / $25.5k / $6.2k on the three
   halves against $10.6k / $20.8k / $3.3k at 15%) are what a flat 20% earns ($13.7k / $24.2k / $5.5k) with *higher*
   stop odds (September 1.2%, 9% on one window, against 0.5% and 2.2% for flat 20%), because the 1.5× tier fires on
   Sep 7 12–18, where the demand gauge read 0.36 ETH and the window paid −0.3%. Thresholds re-fitted on the fit half
   alone do worse. Rejected as a rule; kept as a readout: the `flow` event now carries `follow_eth_last_20` and
   `follow_eth_last_60`, and under 0.2 ETH the operator should expect +3% to +4% a trade.
2. *React to the dump.* Sell as soon as a sell of 0.5% to 5% of supply lands inside the hold (we land 0.3 s after
   seeing it). Worse everywhere it was not fitted: September +3.7% to +5.3% instead of +6.1%, test +13.5% to +14.2%
   instead of +15.6%. The sells we would react to are followed by buys; leaving on them sells the dip. Rejected.
3. *Change the exit.* Hold 7 s with no take-profit pays +8.8% on September but +8.2% on the fit half against +10.4%,
   at a 17% tail; hold 4 and a +30% take-profit are better on the fit half and worse on September. The plateau of
   section 23.8 stands: hold 5 with +50% stays.
4. *Size up.* Stop odds by resample (each window's kept trades shuffled a thousand times, $300 start, −50% stop),
   averaged over the windows of each half, with the worst window:

   | sizing | fit P(stop) / worst | test | September | September median gain per window |
   |---|---|---|---|---|
   | 15% (the rule) | 0.1% / 0.2% | 0.0% / 0.0% | 0.1% / 0.3% | $326 |
   | 17.5% | 0.1% / 0.4% | 0.0% / 0.0% | 0.2% / 1.0% | $423 |
   | 20% | 0.3% / 0.6% | 0.0% / 0.1% | 0.5% / 2.2% | $542 |
   | 22.5% | 0.5% / 1.2% | 0.1% / 0.5% | 1.1% / 5.6% | $648 |
   | 25% | 1.0% / 1.7% | 0.1% / 0.5% | 1.8% / 10.1% | $753 |

   20% is the most the September windows allow at stop odds under 1% on every window; 15% stays for the first $300
   and the first live windows. That is the only lever on the E2 rule itself, and it buys two thirds more gain.
5. *Take the seat the crowd moved to.* The bots in second one are not competitors of a kept E2 trade; they are the
   buyers an E1 trade sells to. On every bundled launch (no gate on outsiders is possible at E1, because landing
   first in second one *is* the seat), at the engine's own exit, front landing:

   | E1 front, hold 5 + 50%, 15% | ROI a trade | tail < −40% | own path from $300 | windows positive | P(stop) mean / worst window |
   |---|---|---|---|---|---|
   | fit (Aug 30–Sep 2) | +5.5% | 13.3% | $8.4k (E2: $10.6k) | 4 of 5 | 20% / 99% (Aug 30: −1.0% a trade) |
   | test (Sep 3–6) | +7.8% | 11.8% | $26.5k (E2: $20.8k) | 6 of 7 | 6.6% / 43% (Sep 5 12–18: +1.5%) |
   | September (Sep 7–10) | +8.7% | 10.1% | $39.5k (E2: $3.3k) | 8 of 10 | 1.3% / 10.6% (Sep 8 12–18: +2.5%) |

   Three times the trades (2,365 against 814 on September) at a higher return each, twelve times the September
   gain, at September stop odds that match E2 at 22.5%; and on the August windows, where second one was empty, it
   loses to E2 and stops on Aug 30. One block behind the front it is +3.8% a trade on September with 22% stop odds;
   hold 7 without take-profit lifts the front to +13.1% at a 17% tail. Choosing the seat from the share of the
   previous sixty bundled launches that carried a bot in second one (known at send time; the engine now prints it
   as `out1_share_last_60`): above 45%, $10.4k / $18.8k / $28.1k with two stopped windows; above 55%, $10.6k /
   $19.7k / $19.8k with one; above 65%, $10.6k / $21.2k / $7.4k with none. None of this exists unless the box lands
   first in second one, which no dry run can show (section 23.8, point 4).

**What this means, in one place.** The September edge is thinner for two measured reasons, one of which is ours to
act on. Demand (the ETH other people put in after us) fell by a quarter and moves with the hour and the day; it can be
read live but not predicted launch by launch, so nothing sizes to it, and the operator reads it as a regime. Crowding
(bots taking second one on two thirds of launches) took half the trades; the E2 rule survives it by skipping them,
and the E1 seat converts it into the best return in the data, conditional on the race. So: run E2 at 15% as
configured (+6% a trade on the ten unseen windows, +$200 a busy window from $300); read `follow_eth_last_60` and
`out1_share_last_60` each evening; move to 20% once the live scores match the tables; run the thirty-launch E1 test
of runbook section 9 at $5–10 stakes, and if the receipts show the first block of second one on most attempts, run
E1 at 10% while `out1_share_last_60` is above 55% and E2 otherwise. Nothing in this section changes what the engine
sends; it adds the two readouts, and `src/analysis/live_check.py` (runbook section 5), which pulls the receipts of every
live trade and puts the live return next to the engine's score of the same launch, so the first thirty live trades
settle whether the box lands where the tables assume.

## 24. Round 16: six live trades, four blind days, and the rule re-fitted on what is left

The engine went live on Sep 11 with $109 and was stopped that night after six losing trades (−$50). It then ran in
paper mode for four days that produced nothing, because the node's monthly quota ran out on Sep 12 at 01:07 and the
engine kept running blind: it saw launches and scored none. The watchdog only checked that the log grew, and it grew,
full of errors. `deploy/sniper-check.sh` now alerts when launches keep arriving and nothing is scored for two hours, and
`src/analysis/paper_report.py` refuses to be read as valid when scoring stopped before the log ends.

**The four days were recoverable from the chain, and they change the conclusion.** Sep 12 to 16 pulled and replayed
(`src/analysis/oos_test.py`, `data/derived/oos_sep12_16.txt`): 484 clean seats, **+6.8% a trade, 95% interval +4.7% to
+9.0%**, on days nothing was fitted to. The engine as it then stood would have made **+$718 from $62** over those four
days. The strategy was switched off while it was working.

**What actually happened on Sep 11.** Not a sudden death: the share of team launches with a bot ahead of our seat rose
from 24% on Sep 2 to 88% on Sep 11 and fell back to 67-77% afterwards, and Sep 11 was the worst day in the whole record
(1.7 clean seats an hour, 23% win rate). Five clean trades all losing has probability 27% on such a day, against 0.5%
under the old distribution. The machine was right; the day was bad and my sample to judge it was worse.

**The rule re-fitted, and tested in all three periods** (`src/analysis/audit_combo.py`, `data/derived/audit_combo.txt`).
A change was only kept if it helped on the days the rule was built on, the days in between, and the four new days:

| rule | to Sep 8 | Sep 9-11 | Sep 12-16 |
|---|---|---|---|
| as it ran | +12.5% | +7.7% | +6.8% |
| at least 5 team wallets | +13.3% | +8.5% | +8.1% |
| team ETH capped at 1.2 | +12.8% | +9.9% | +8.5% |
| creator holds 3% of supply | +14.0% | +11.7% | +9.4% |
| all three | **+15.4%** | **+15.4%** | **+14.7%** |

The team-ETH cap is new (`BUNDLE_MAX_ETH`, engine 4.97): a team that puts in more than 1.2 ETH has already taken the
move, and those launches paid −0.7% on the new days. The creator-supply floor went from 1% to 3% and the wallet count
from 3 to 5. On the four new days the filtered rule takes 152 trades instead of 461, pays +14.6% instead of +6.5%, and
its worst drawdown is 6% instead of 14%; from $62 at $25 a trade the chance of running the wallet down goes from 1.9% to
0.0% over those days. Eight synthetic launches test every threshold (`tests/test_gates.py`).

**Hours need no change.** The afternoon block was the weak one on the new days (+2.7%, interval spanning zero) but the
filtered rule repairs it (+6.5%, interval +2.3% to +11.1%); evening +20.0% and night +17.3%. 06:00-12:00 UTC still has no
measured launches at all and stays blocked. Hold, take-profit, seat wait and the supply fraction were all swept out of
sample and none beat the current setting by enough to touch (`data/derived/audit_params_oos.txt`); a 7-second hold pays
more per trade but doubles the drawdown in combination, so it stays at 5.

**The E1 front seat is dead.** Scored on every team launch of every day, it is negative on all of them, −4.8% to −13.7%.
No Ohio machine, no race test. The seat that pays is the one the engine already sits in.

**The code audit, and why the go-live was held back a day.** An adversarial read of the whole engine (an independent
pass, every finding then verified line by line against the file) found five defects that could each have ended with a
token bought and never sold, the wallet stuck holding it, and the `position open` gate blocking every later trade with
no alarm:

1. the launch thread was started bare; any exception after the buy killed it silently, before the sell;
2. a position saved while it was being sold kept an in-flight `closing` flag, and the restart recovery path returned
   immediately on it, so the recovered position was never sold;
3. a lost or slow reply from one endpoint was read as a refusal, and the buy was abandoned without approving or selling
   (`already known` and `nonce too low` mean the opposite of refused);
4. the exit's retries took a new nonce each time, so the doubling fee cap never replaced the stuck transaction, every
   attempt eventually landed, and the cap could climb to a fee worth multiples of the position;
5. a nonce reserved for a buy that was rejected or reverted was never given back, leaving a gap that strands every later
   transaction in the pool.

Four more could stop trading with no alarm: the readout block in `chain_loop` sat outside every `try` and iterated
deques that other threads append to, so one `RuntimeError` ended the nonce refresh for good; the daily stop measured
against `BANKROLL_USD` instead of the wallet and could latch on the first launch; our own approve names the curve in its
calldata and was folded as a sell, which would fire the dump exit instantly; and a "learned reverter" could never be
un-learned, so the crowding gates decayed the longer the engine ran. Sells and watched curves were also never pruned,
with the garbage collector off. All are fixed in engine 4.98 and covered by fourteen tests in `tests/test_safety.py`,
alongside the five exit-path tests and the eight gate tests.

### 24.7 The second audit of Sep 16, and engine 5.0

The user asked for every change made on Sep 16 to be audited a second time before the first $10 trade landed. The whole
day's engine diff (394 lines, 4.9 → 4.99) was re-read line by line, the analysis scripts and the preflight were re-run,
and the fixes below were made, each with a test. The one that mattered for the bill: engine 4.95 had added the provider's
Buy events as a second source of rivals by subscribing to **every Buy on the chain plus every block head** (measured
from the sandbox: 323 Buys and 291 heads in 30 s, 1.0 MB, i.e. 1.7 million messages and 2.9 GB a day), which is what
ran the free Alchemy plan dry on Sep 12 and what the user saw as "usage very high" on the paid one. Nothing was stuck:
the subscription was doing exactly what it was written to do.

| # | what was wrong (4.99) | 5.0 | test |
|---|---|---|---|
| 1 | one Buy-log subscription for the whole chain, plus block heads | one subscription per **watched curve** (`address` filter), opened when the watch starts and dropped when it ends; no head subscription: a Buy's second comes from the feed's own bookkeeping (`flip_block`, and `sequenceNumber` = the L2 block number, checked at 40 second boundaries) | `tests/test_rivals.py` (11 checks against a scripted socket; the real socket showed the subscribe and unsubscribe round trips) |
| 2 | a Buy whose block time was not known yet was assigned to the **current** feed second | it waits up to 2 s for the feed to pass its block, then is dropped, never guessed | same |
| 3 | `rejected()` treated a transport error string ("timeout", "connection reset") like a node refusal, so a buy the sequencer had taken could be marked rejected and its nonce released | only a JSON-RPC error **dict** from every endpoint is a refusal; a transport failure is "unknown", and the receipt decides | `tests/test_safety.py` (two new checks) |
| 4 | `SELL_FEE_MAX_USD` defaulted to $0.50, below the first cap (~$0.70), so the doubling never happened | default $2.00 | existing fee-cap test |
| 5 | the exit's token address fell back to the **curve** when the RPC lookup failed, and an approve on the curve reverts for ever | `learn_token`'s address is used first; the curve stays only as a marker, and `close_position` re-resolves it on every retry with an alarm | — (path exercised by the close-position tests) |
| 6 | `fire()` waited without limit for an endpoint's lock, held by the keep-alive ping | 0.1 s, then that endpoint is skipped for this send | `tests/test_fire.py` |
| 7 | `resolve_rpc` asked the node for the head every 20 ms (fifty calls a launch) | the head is cached 150 ms, the loop runs ten times a second, `toBlock: latest` so the cache hides nothing (83–95 ms to resolve, unchanged) | probe on live creations |
| 8 | the wallet balance was read every 3 s | every 30 s (it changes only on trades) | — |

The rest of the day's diff held: the seat wait, the gates, the E1 paper score, the token matching, the crash wrapper,
the state file, the daily stop and the demand floor were read again and left as they were. `test_safety` (18),
`test_gates` (8), `test_close_position` (5), `test_rivals` (11) and `test_fire` (live endpoints) all pass on 5.0, and a
60 s dry-run start on the real feed and the real Alchemy socket came up clean.

### 24.8 The analysis re-derived, independently of the harness

The user asked whether the day's *analysis* had been checked, not only the code: the chain replay of the four blind
days, the E1/E2 check, the re-fitted filter. It had not — the scripts were run once, when written. Three checks
follow, none of which reuses `risk_harness.replay`.

**1. The rows are the chain.** Three launches from the blind days (Sep 13 12:32, Sep 14 00:01, Sep 15 13:09) were
compared event by event with Alchemy's logs: every buy and sell amount, every token count and every event count is
identical (26/16, 111/140, 54/54 buys/sells).

**2. An independent simulator agrees with the harness on the same rows.** `src/analysis/indep_replay.py` is ~80 lines
written from the curve's arithmetic (x·y = k from (1.68 ETH, 1e9), tier plus the seat's surcharge on the buy, tier on
the sell, 3% of supply capped at the stake, 0.3 s into the seat's second, hold 5 s or +50%, later buyers' 10% minOut,
our own 25% minOut quoted at send time) and classifies the seconds by the surcharge alone. It agrees with the harness
on which launches are clean (100%) and on the numbers (`data/derived/indep_replay.txt`):

| Sep 12–16, E2, $25 | harness (24.3) | independent |
|---|---|---|
| every clean seat | n 484, +6.8% [+4.7, +9.0] | n 490, +7.5% [+5.5, +9.6]; anchored like the harness +6.9% |
| crowded seats | negative | n 1863, −6.1% [−7.5, −4.9] |
| clean + re-fitted filter | +14.7% | n 171, +15.9% [+12.1, +19.9]; hours 12–05 only +15.3% |
| from $62 at $25, filter, hours | +$554, dd 6% | 156 trades, +$599, dd 6% |

Every hour bucket is positive on the whole data set (00–05 +19.8%, 05–12 +13.5% on 28, 12–18 +16.4%, 18–24 +18.2%),
the crowding rise reproduces (28% Aug 30 → 88% Sep 11 → 67–77% Sep 12–15), and Sep 11 is the one negative day.

**3. The clock, and a real correction.** The cache's row times are interpolated between block anchors; the spot check
found a buy the chain places 2 s after creation sitting at 1.34 s in the cache. So for 150 random "clean" launches
of Sep 12–15 every block from the creation to +8 s was read (12,000 timestamps) and the rows rebuilt on the exact
clock (`src/analysis/exact_clock_check.py`, `data/derived/exact_clock_check.txt`). The return per taken trade is
unchanged: +6.6% exact vs +8.2% interpolated on all 150; on the 100 the engine would actually take, +5.9%
[+1.5%, +10.3%] vs +6.7%; on the 40 of those that pass the filter, +10.3%. But **only 67% (±8) of the launches the
harness calls clean are clean on the true clock**: on the other third the first outsider of second two landed inside
the 0.3 s wait (the interpolated clock had it 0.36–1.07 s in; the chain has it at 0.0–0.3 s), and the engine, which
watches the real feed, does not send. The harness therefore overstates the trade count by about a third; every
dollar figure from the replay (the +$554 / +$599 over four days, the days-to-$300 estimate in 24.4) should be read
at two thirds. The per-trade edge, the filter, the hours, the stop and the sizing are unaffected, and the engine
itself never was: it has never used the interpolated clock. Two launches also show why the exact clock matters per
trade — one that the cache scores −2.6% is −60% on the chain (a dump the interpolated clock put outside the hold),
another the cache scores +69% is a no-send on the chain (rival at 0.3 s) — but they cancel in the mean.

**4. E1, worded precisely.** The line "the E1 front seat is dead, −4.8% to −13.7%" is the harness's E1 seat landing
0.3 s after the first second-one buyer — the executable seat, not the front. The theoretical front of second one
(ahead of every buyer, no wait) pays +1% to +3% in the harness's model and +11% to +17% in the independent one
(which also goes ahead of the team's own second-one buys, which is not achievable); the executable E1 is not: on
Sep 12–16 the harness has it at −4.8% to −13.7% and the independent simulator at −1.6% to +1.1% (−9.1% on Sep 16's
49 launches). E1 stays off, and the race data (23.11) is why the front cannot be had.

**5. Housekeeping.** `data/derived/oos_sep12_16.txt` had been committed empty; regenerated, and it reproduces
(n 484, +6.8% [+4.7%, +9.0%]). The "reshuffle" at the end of `oos_test.py` uses a flat stake, so its 5th/50th/95th
percentiles are the same number by construction; only its ruin count (2.0% unfiltered at $25 from $62) says anything.

### 24.9 The first live afternoon reconciled with the chain, launch by launch

Engine 5.0/5.01 ran live at $10 from 12:00 UTC on Sep 16 and took nothing. The same hours (12:00–17:14) were pulled from
the chain and replayed with the current rule (`src/analysis/replay_live_hours.py`, `data/derived/replay_live_hours_0916.txt`):
37 bundled launches, **35 with a bot in second one (95%)**, two clean. One of the two fails the 3% creator floor. The other,
13:19:00 (8 wallets, 0.537 ETH, creator 3.4%), the replay trades at +14.7% — and the engine's log shows why it did not:
the feed resolved it in 111 ms, counted the bundle exactly as the chain did, and then saw a 0.005 ETH outsider buy land
**0.16 s into second two**, before the 0.3 s send; the chain confirmed the buy (block 64538690). The replay's interpolated
clock had placed that buy at 0.54 s, after the send — the very error 24.8 measured on 150 launches. On the true clock the
afternoon had zero tradeable seats, and the engine took zero. Live and backtest agree once the backtest is read on the
chain's clock.

Three more launches the replay lists with bundles of 7–8 wallets (16:11, 16:18, 16:31) reached the engine as `bundle 0`:
their wallets bought through a helper contract whose calldata names neither the curve nor the token, so the feed cannot
attribute the buys and the launch is refused. All three were crowded on the chain (1–3 bots in second one), so nothing
was lost today, but it is a blind spot that costs opportunities: about one bundled launch in ten today. The fix is to read
the creation block's Buy events from the provider at resolution time (one call, ~150 ms) and count the bundle from the
chain, as the tables do — queued for the next engine version, not changed on a live day.

The rest of the engine's afternoon: 653 creations in two hours, 50 reaching the decision, every refusal accounted for
by a gate the chain confirms, no alarms, no socket errors, one process, the wallet untouched.

### 24.10 "Why does it only lose when we go live?" — answered launch by launch, and two corrections

The user's challenge on the morning of Sep 17 was the right one, and answering it properly required matching what the
engine saw and did against the chain replay **on the same launches** rather than comparing day averages. The engine's
131 logged paper scores (Sep 10 15:58 to Sep 16 23:17) and its six real trades were matched by curve address to the
replay (`src/analysis/match_engine_replay.py`, input `data/derived/engine_scores_0910_0916.txt`; Sep 11 06–12 UTC was
pulled from the chain for the one trade outside the windows). Two things came out that earlier sections had wrong.

**Correction 1 — the Sep 11 loss was the code, not the day.** Section 24 said five of the six live trades were clean seats
lost to a bad day. On the chain, four of the six had a rival the engine of that day could not see:

| trade (UTC) | replay, same launch | on the chain | today's engine |
|---|---|---|---|
| 07:25 | −71.8% | second-two rival at 0.0 s; bundle 1.38 ETH; creator 2.6% | refused three ways (rival, cap, creator floor) |
| 14:30 | −7.3% | outsider in second one | refused |
| 14:45 | −3.4% | clean | traded, small loss (fees, no demand) |
| 14:49 | −52.5% | outsider in second one | refused |
| 14:54 | −3.4% | clean | traded, small loss |
| 21:47 | −68.1% | router bot buying by token (the 4.95 fix) | refused |

About $51 of the $53 lost came from the four seats the old feed decoder misread as clean; the two genuinely clean seats
lost $1.70 between them. Every one of the four is refused by engine 4.95+ (token matching, chain-side rivals, the
second-two rival gate, the 1.2 ETH cap, the 3% creator floor). The day was also bad — 97% crowded in the morning, 88–90%
after — but that is not what lost the money.

**Correction 2 — the engine's own paper scores were 4–10 points too low.** `exact_score` deducted a flat **$1.00** of gas
from every score; four Sep 11 receipts show a round trip (buy, approve, sell) costs $0.06–0.14 at 0.1–0.2 gwei. At $25
that is 4 points off every score, at $10 it is 10 points, and the bias fed the switch (rolling 15 below −10%: at $10, a
seat that truly returned zero was scored −10%) and every readout the user was shown (`mean_score_last_60 −10%`). Engine
5.02 prices the real gas (`gas_usd()`, 230,000 gas at the chain's base fee, clamped $0.05–1.00). Section 24.9's line
"9 rule-passing seats scored today, mean −1.8%" was this bias: with the real gas those 14 seats of Sep 16 average about
+1.6% — flat, on a day with 8 clean seats in total.

**What the match shows once the gas is right.** 93 of the 131 scores fall inside the replay's windows: engine as logged
+1.4%, engine with the real gas **+4.8%**, harness +5.5%, independent simulator +4.9%; per launch the engine and the
harness differ by a median of 0.04 points and are within one point on 87% of launches (the rest are launches where a
dump lands on one side of the 5 s hold on one clock and the other side on the other). Sep 10 evening: engine +11.4% vs
harness +12.4%; Sep 11: −3.0% vs −2.8%; the Sep 16 seat: +20.9% vs +21.0%. The engine, live on the real feed, sees the
same seats and the same returns as the replay. The replay's profitable days are not an artefact of the replay.

**So why did the two live days show nothing?** Sep 11: the loss was the decoder's blind spots, fixed since, on the
second-worst day for clean seats in the record (31 of 414). Sep 16: 8 clean seats in the whole day (of 86 bundled
launches, a fifth of the usual count, 88–100% crowded), the engine took none because every one had a rival inside the
0.3 s wait or failed the filter, and their paper return was flat. Two draws that were the two worst days of eighteen
is a 1-in-150 coincidence; the honest reading is a mix of bad luck and a trend the report has flagged since 23.11 —
crowding rising, and now the supply of bundled launches thinning. The engine's account of it is now verified against
the chain to within a point; what it cannot do is create seats that are not there.

### 24.11 The six real trades, rebuilt from their receipts

Asked to make sure the two Sep 17 fixes were the whole problem, the last thing left to test was execution itself: not
the engine's model of a trade against the replay's model, but the chain's record of what the six real trades cost and
returned against what the replay predicts for those launches (`src/analysis/real_vs_replay.py`,
`data/derived/real_vs_replay_0911.txt`). From the buy and sell receipts: ETH in (the transaction's value), ETH out (the
curve's Sell event), gas, the landing block relative to the creation block, and the hold.

| trade | in ETH | out ETH | gas | **real** | replay | landed | held | the seat on the chain |
|---|---|---|---|---|---|---|---|---|
| 07:25 | 0.01012 | 0.00292 | $0.06 | **−71.4%** | −71.8% | 2.0 s | 5.1 s | rival in second two at 0.0 s |
| 14:30 | 0.00954 | 0.00896 | $0.09 | **−6.5%** | −7.3% | 1.9 s | 5.1 s | rival at 0.12 s |
| 14:45 | 0.00959 | 0.00938 | $0.05 | **−2.4%** | −3.4% | 2.0 s | 5.1 s | clean |
| 14:49 | 0.00959 | 0.00463 | $0.05 | **−51.9%** | −52.5% | 1.7 s | 5.1 s | rival at 0.11 s |
| 14:54 | 0.00961 | 0.00940 | $0.05 | **−2.4%** | −3.4% | 1.8 s | 3.7 s | clean (dump exit fired) |
| 21:47 | 0.00986 | 0.00321 | $0.05 | **−67.7%** | −68.1% | 1.6 s | 5.1 s | bot in second one + rival at −0.26 s |

Real mean −33.7%, replay −34.4%, independent simulator −34.0%; per trade the chain is 0.4–1.0 points *better* than the
replay (the replay's $0.10 gas and 0.3 s slip are slightly conservative). Real money: −$50.56. Every buy landed 1.6–2.0 s
after the creation block (the seat's second, as designed), every exit closed in 5.1 s, and the one early exit (3.7 s) is
the dump stop doing its job. The four large losses are four seats a rival reached first — 0.0, 0.11, 0.12 and −0.26 s
into the seat's second — which the engine of that day could not see and today's engine refuses.

That closes the audit. The chain, the replay, the independent simulator and the engine's own scorer now agree with each
other and with real money to within a point. What is left is not a fault: the replay counts a third more seats than the
true clock allows (24.8), the feed cannot attribute helper-contract bundles (24.9), the second-two rival gate may be
stricter than it needs to be (24.9), and the tape since Sep 16 has offered few seats. None of those can lose money;
they decide how often it trades.

### 24.12 The day table, audited

The day table given to the user on Sep 17 (bundled launches, clean seats and clean-seat return per day) was audited on
request. Three faults, none changing the conclusion, all corrected in `data/derived/day_table_audit.txt`:

1. **Unequal coverage.** The replay's windows cover 6 to 22 hours per day (Sep 12 is 12 h, Sep 16 is 14.2 h, most days
   18 h, Sep 11 22 h), so the day totals were not comparable. The audited table is per hour.
2. **Sep 11 was stale.** Its row predated the 06–12 UTC pull; with it the day is 23.9 bundled launches an hour and 1.5
   clean, not 18.8 and 1.4.
3. **"Clean" was on the interpolated clock.** The column the engine can act on is filter-passing clean seats × 0.67 (24.8).

The pulls themselves are complete: four 10-minute block ranges (Sep 11, 14, 16 morning, 16 afternoon) hold exactly the
Buy logs Alchemy returns for them today.

| day | h | chain events/h | bundled/h | clean/h | filter-passing clean/h | true-clock/h | return per filter-passing seat |
|---|---|---|---|---|---|---|---|
| Sep 2 | 6 | 56,700 | 40.5 | 28.3 | 21.7 | 14.5 | +22.1% |
| Sep 3 | 18 | 61,400 | 55.2 | 27.4 | 16.9 | 11.4 | +22.9% |
| Sep 5 | 12 | 74,500 | 49.2 | 11.8 | 5.0 | 3.4 | +19.3% |
| Sep 7 | 18 | 63,600 | 63.6 | 22.8 | 7.9 | 5.3 | +11.0% |
| Sep 8 | 18 | 61,100 | 53.1 | 15.6 | 5.5 | 3.7 | +18.3% |
| Sep 9 | 18 | 46,900 | 37.6 | 7.6 | 2.4 | 1.6 | +16.1% |
| Sep 10 | 18 | 44,600 | 37.6 | 5.8 | 2.8 | 1.9 | +17.8% |
| **Sep 11 (live)** | 22 | 46,800 | 23.9 | 1.5 | 0.5 | 0.3 | −4.3% |
| Sep 12 | 12 | 54,100 | 53.2 | 7.3 | 2.2 | 1.5 | +22.4% |
| Sep 13 | 18 | 50,600 | 45.0 | 7.8 | 2.9 | 1.9 | +19.3% |
| Sep 14 | 18 | 50,900 | 35.3 | 9.7 | 2.3 | 1.6 | +10.9% |
| Sep 15 | 18 | 41,000 | 21.8 | 4.4 | 2.7 | 1.8 | +13.9% |
| **Sep 16 (live)** | 14.2 | 17,300 | 6.0 | 0.6 | 0.3 | 0.2 | +7.0% (n 4) |

Read per hour, the history is a staircase, not a cliff: 11–15 tradeable seats an hour on Sep 2–3 (the days the rule
was found on), 3–5 on Sep 5–8, 1.5–2 from Sep 9 to Sep 15 with Sep 11 at 0.3, and 0.2 on Sep 16 — whose whole-chain
activity (17,000 curve events an hour against 41,000–89,000 on every other day) was a quarter of normal. The return
per seat has not moved: +11% to +22% on every day but Sep 11 since the filter was fitted. What the user remembers as
"a lot of trades" was the Sep 2–3 level, gone by Sep 9; Sep 12–15 was 25–30 trades a trading day on the true clock,
worth about +$100–150 a day at $25; Sep 16 offered three.

### 24.13 The seat that still pays, and the assumption that hid it

The user's challenge — "the seat cannot close only when I go live; there is a mistake in your logic" — was right in a
way the day-table audit did not reach. The engine has refused the creation second since round 11 on the belief that
"anyone else pays 93–98% in the creation second" (its own start-up guard). The chain says otherwise, on every day of
the record: an outsider buying in the creation second *after* the creation block pays the second-one surcharge,
**6.18%**, on 94–98% of such buys from Sep 2 to Sep 17 (`src/analysis/e0_seat.py`); the 96–98% cases are contract
callers, routers and 0.001 ETH dust probes (`e0_seat2.py`), which a direct buy with a minOut never joins — it reverts
instead, for the gas. So the fastest bots' seat was open to us all along, at a cost we already pay in second one.

**What it pays.** Entering the creation second 0.3 s after the creation block, 6.18% surcharge, 3% of supply capped at
the stake, hold 2 s or +50%, on *every* bundled launch (no clean requirement — this seat is ahead of the team's second
round and of every bot, so crowding is what it sells into):

| period | launches | at 0.2 s | at 0.3 s | at 0.4 s | at 0.5 s | at 0.7 s |
|---|---|---|---|---|---|---|
| Sep 7–10 | 3,452 | +34.8% | +25.1% | — | +14.3% | +7.0% |
| Sep 11 (the day we lost) | 525 | +32.9% | +22.6% | +14.4% | +8.6% | +2.7% |
| Sep 12–15 | 2,477 | +27.3% | +15.3% | +10.4% | +7.2% | +1.8% |
| **Sep 16–17 (the new regime)** | 175 | **+14.0%** | **+6.5%** | +3.7% | +2.9% | −3.5% |

Positive in every period including the two live days; it decays 3–5 points per 100 ms of delay, because the profit is
being ahead of the team's own exempt second-one buys (34–44% of launches, median 200–233 ms into second one, 0.26–0.39
ETH) and of the bot wave (first outsider at a median 300–400 ms into second one): entering right *after* the team's buys
pays −4 to −5% (`front_seat.py`). Win rate 45–74% by period, median +8%, p5 −14%, p1 −48%, worst −69%; 60 trades from
$60 at $10 reshuffled 3,000 times never hit the −50% daily stop (median end $147). Money per day at $25, one position
at a time: Sep 12–15 +$1,500–2,800 a day at 0.3 s (+$1,000–2,100 at 0.4 s); Sep 16 +$258; Sep 17's first six hours +$31.
The bundle filter neither helps nor hurts it (Sep 12–15: +15.3% all, +14.7% filter-passing).

**Why this is the same game the bots play, and why we can play it:** ordering is first come, first served at the
sequencer; the fastest bots land 0.2–0.3 s after the creation block; our box is 20 ms from the sequencer and the feed
resolves a bundled launch from the creation message itself in 59–150 ms on the fast path. The seat is worth taking
at 0.3–0.4 s in every regime measured; at 0.7 s it is not. What decides it is our own seeing-to-landing time, which a
dry run measures directly (`resolve_ms`, `seat_flip_to_send_ms` on each decision).

**Engine 5.1** adds the seat for a non-exempt wallet behind an explicit opt-in (`SEAT=E0 E0_OUTSIDER=1`, with
`HOLD_S=2`, `MAX_RESOLVE_MS=300`, `MIN_FOLLOW_ETH_60=0`, `BUNDLE_MIN=3`, `MIN_CREATOR_SUPPLY=0.01`): the surcharge is
6.18%, there is no seat wait, the send goes out the moment the curve is resolved, and the buy's minOut (25%) is what
refuses the 96–98% tokens. The old guard stays for anyone who does not opt in.

**Checked on the exact clock.** Because this seat lives inside the first half-second, the 150 launches of 24.8 whose
every block time was fetched were re-scored with the creation-second seat on exact times (`src/analysis/exact_clock_e0.py`,
`data/derived/exact_clock_e0.txt`): +25.4% at 0.2 s, +9.1% at 0.3 s, +9.1% at 0.4 s, +7.2% at 0.5 s, +4.0% at 0.7 s,
against +23.0 / +10.0 / +6.1 / +2.2 / −2.0% on the interpolated clock for the same launches. The seat is not a clock
artefact; if anything the true clock is kinder to a slightly late landing.

### 24.14 The creation-second seat optimised: what loses, what wins, filters, exits, sizing, risk

Fitted on Sep 7–10, judged on Sep 11, Sep 12–15 and Sep 16–17 untouched; every candidate reported
(`src/analysis/e0_optimize.py`, `e0_optimize2.py`; `data/derived/e0_optimize*.txt`). Entry 0.3 s, $25.

**What loses.** Trades worse than −30% are 0.8% of the fit period and look exactly like the winners before the send
(same tier, bundle, wallet count, creator share): they are the launches the team or a bot dumps inside the hold, and
nothing observable before the send tells them apart. Winners (34%) leave by the take-profit; the middle (65%) leave by
the hold with a few percent either way. So the tail is managed by the *exit*, not by a filter.

**Exits.** Hold 1.5 s with no take-profit is the best mix: +26.5 / +24.7 / +18.5 / +10.5% across the four periods, 5th
percentile −8.5 to −12.3%, trades below −30% at 0.6–1.1%, against 0.8–3.4% at hold 2 s. Hold 1.0 s cuts the tail
further (0.3–0.6% below −30%, worst −39% in the new regime) at a cost of 1–2 points. The +50% take-profit costs 2–3
points and protects nothing the hold does not. A stop-loss or a dump stop does nothing: by the time the sell lands
(0.3 s) the dump is over.

**Pre-entry filters (better in all four periods).** Tokens with a 2–3% tax: +34 / +43 / +36 / +27% (a higher tax
punishes the flippers behind us, not us); team share under 25% of supply: +42 / +39 / +24 / +13%; largest bundle wallet
under 5%: +32 / +32 / +16 / +10%; 3–4 wallet bundles: +35 / +32 / +25 / +19%. The worst class is a 1%-tax token whose
team holds 35% or more; dropping only that keeps 63–82% of launches at +32 / +30 / +21 / +13.5% and 76–105% of the money.
Hard filters raise the return per trade but cut the trade count more, so total money falls on good days (tier 2–3%:
a third of the launches, 30–50% of the money) and holds or rises on thin days. A sizing tilt (full stake on 2–3% tax or
team under 25%, half on the rest) keeps every trade, 78–98% of the money, and halves the drawdown.

**Sizing.** At the $150 cap, 2% of supply per trade is as good as 3% (+$18 vs +$21 a trade on Sep 12–17); 1% halves it.

**Speed, again.** With the chosen exit: +38.9 / +36.5 / +33.4 / +18.8% at 0.2 s, +26.5 / +24.7 / +18.5 / +10.5% at
0.3 s, +20.7 / +15.9 / +12.2 / +7.0% at 0.4 s, +14.8 / +9.3 / +8.4 / +4.7% at 0.5 s.

**Money and risk at the cap.** At $150 a trade, no filter, hold 1.5 s, no take-profit, one position at a time: Sep 12–15
+$62,756 (2,382 trades), Sep 11 +$18,004, the thin Sep 16–17 +$2,621 (171 trades); maximum drawdown −$98 to −$348,
longest losing streak 7–12 trades, no losing day in the record. These are the model's numbers at a size no real trade
has yet tested; the impact model is the same one that matched six real trades within a point at $25, but at 400 trades
a day the market would see us, and nothing here models the bots adapting. Read the new-regime rows as the base case.

**What the engine can and cannot read before the send.** The team's share of supply it has (from the bundle it folds);
the token's tax tier it does not on the fast path (it assumes 1% until the chain's first Buy event is read), unless the
tier is a parameter in the creation calldata — checked next.

**The tier is in the calldata.** Word 13 of the creation call (selector `f85f8e41`) is the token's own tax in basis
points on top of the 1% protocol fee — 0 for the 1% tier, 100 for 2%, 200 for 3%, 300 for 4% — and matched the chain's
tier on 117 of 120 launches. Engine 5.2 reads it before the send at zero latency: `TIER_MIN_BPS` / `TIER_MAX_BPS` gate on
it (100–200 = the 2–3% tokens), `SKIP_TIER1_TEAM_SHARE=0.35` drops the worst class, both fail closed on an unknown
layout, the watch folds buys with the token's real tax instead of a flat 1%, and every decision logs `tax_bps` and
`team_share`. Recommended live settings for the seat: `HOLD_S=1.5 TAKE_PROFIT=0 TIER_MIN_BPS=100 TIER_MAX_BPS=200`.

**Audit of the optimisation on periods it never used.** The filter and exit above were chosen on Sep 7–10 and judged
on Sep 11, 12–15 and 16–17. Two more periods sit in the record that no analysis today touched, Sep 2–3 and Sep 5–6.
On both the chosen set beats the unfiltered seat, and the bootstrap intervals of the two rows do not overlap:

| period | no filter (95% interval) | 2–3% tokens (95% interval) | 1% tokens |
|---|---|---|---|
| Sep 2–3 (untouched) | +28.1% [+24.7, +32.0], n 2,110 | +97.7% [+85.4, +112.4], n 447 | +6.0% |
| Sep 5–6 (untouched) | +25.1% [+22.2, +28.7], n 910 | +37.3% [+29.4, +45.7], n 183 | +20.9% |
| Sep 7–10 (fit) | +26.5% [+24.8, +28.1], n 3,452 | +34.3% [+30.6, +38.4], n 795 | +22.4% |
| Sep 11 | +24.7% [+20.8, +28.6], n 525 | +43.0% [+34.4, +51.9], n 158 | +16.1% |
| Sep 12–15 | +18.5% [+16.6, +20.7], n 2,477 | +36.4% [+30.8, +43.4], n 657 | +11.8% |
| Sep 16–17 | +10.5% [+6.2, +16.7], n 175 | +26.6% [+14.3, +41.1], n 64 | +1.2% |

Entry 0.3 s, hold 1.5 s, no take-profit, $25. The exit choice holds on the untouched periods as well: hold 1.5 s with
no take-profit against the first version (hold 2 s, take-profit +50%) gives the same or better mean (+28.1 vs +26.9%,
+25.1 vs +23.3%), the same p5, and a quarter to a seventh of the trades below −30% (0.2 vs 0.7%, 0.3 vs 2.1%). Six
periods out of six, on two independent simulators' mechanics, is as far as the record can take the filter; the
one thing still unmeasured is our own landing time on the droplet, which the E0 dry run is collecting now.

**The public snipers, checked.** Two products advertise sniping Pons launches; neither is ours and neither has code
we can read. `github.com/Trustdev-eth/pons-sniper-bot-v1-v2` is a README and nothing else (two commits, both Sep 8,
one star, no fork, no release, no source file in its history) by a freelancer who sells custom bots and lists 125
repositories, among them a `fomo-copy-trading-bot` and a `Robinhood-Bundler`, also README-only. The README is a
specification for sale: a V2 entry that polls the address-specific opening tax and buys only when the effective tax is
at or under a configured cap, 1% in its example, with a 100 ms poll. That is a description of the crowd we measured at
second two: a bot that waits for the surcharge to reach zero and then races. Its default never takes the creation
second at 6.18%, so the seat we run is not the one this design targets, though any buyer can raise the cap. The
second product is the browser-based sniper at ponssniperbot.com announced on Sep 16, the day the second-two crowd
doubled; its press release says it "fires the moment there is something to trade", which is the same second-two
race. Nothing in either mentions the tax tier in the creation calldata, the team's share, or the creation-second
surcharge schedule.

### 24.15 The creation-second seat, corrected: no entry ahead of the bundle (engine 5.3)

**What the dry run showed.** Engine 5.2 in E0 paper mode, Sep 17 11:15–11:29 UTC: 60 creations (245 an hour, most of
them one-wallet launches), 46 skipped on the calldata (fewer than three named wallets), 7 passed the calldata check,
and all 7 were refused at the gates with `bundle 0 < 3, 0.000 ETH < 0.3`. The E0 path of 5.1–5.2 read the gates the
moment the curve was resolved, before a single bundle buy had arrived on the feed; the E1/E2 paths never had this
problem because their wait for the seat's second let the bundle arrive first. Zero trade decisions in a day of E0 paper
was this, not the market.

**What the replay had assumed.** The E0 tables of 24.13–24.14 entered at a fixed 0.3 s on every launch the hindsight
filter called bundled. On the tables' clock the bundle (three named-wallet buys, 0.3 ETH) is complete by 0.1 s on
15–30% of launches, by 0.2 s on 58–67%, by 0.3 s on 73–80%, and after 0.3 s on a fifth to a quarter. On that last
group a fixed 0.3 s entry sat ahead of the team's own bundle, which then bought into our position: Sep 12–15, bundle
complete by 0.2 s, 509 launches, +14.9% a trade; bundle complete after 0.2 s, 148 launches, +110%. Sep 7–10: +15.5% on
519 against +69.7% on 276. Sep 16–17: +14.4% on 47 against +60.2% on 17. The tables' +27–36% mean was those launches.
Nobody can take that entry: at 0.3 s the calldata says the wallets exist, not that they will buy.

**The seat that can be taken.** Enter once the bundle is visible on the feed (complete plus 0.15 s of delivery and
processing), only if it completed within 0.3 s of the creation, 2–3% tokens, hold 1.5 s, no take-profit, $25:

| period | n | share of bundled launches | mean | median | win | p5 | below −30% | worst | trades/day | $/day at $10 | at $25 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Sep 2–3 | 153 | 34% | +13.0% | +1.7% | 52% | −12.0% | 0.0% | −13% | | | |
| Sep 5–6 | 136 | 74% | +5.7% | −2.9% | 40% | −12.2% | 0.7% | −52% | | | |
| Sep 7–10 | 633 | 80% | +13.1% | −1.9% | 47% | −12.3% | 0.3% | −58% | 211 | +$276 | +$690 |
| Sep 11 | 129 | 82% | +19.1% | +8.5% | 67% | −10.9% | 0.0% | −12% | 141 | +$269 | +$671 |
| Sep 12–15 | 558 | 85% | +14.6% | +7.1% | 62% | −12.3% | 0.9% | −59% | 203 | +$297 | +$743 |
| Sep 16–17 | 53 | 83% | +15.9% | +1.9% | 57% | −11.6% | 0.0% | −12% | 45 | +$72 | +$181 |

Positive in six periods of six, about half the earlier claim, with a low median: the mean is carried by the launches
where the team's second round and the bots follow. Waiting for bundles that complete later than 0.3 s adds trades and
subtracts return (T = 1.0 s: +9.9 / +15.7 / +13.0 / +11.2%), and a bundle completing at 0.5 s or later loses money
(−6% and −12% in the two judged periods), so the wait is capped. The tier filter still earns its place on the honest
entry: all tiers +15.1 / +11.8 / +9.8 / +5.5%, 1%-tier tokens +16.0 / +9.2 / +9.0 / −0.6%, the 2–3% tokens above.

**Engine 5.3.** The E0 path waits for the bundle on the feed up to `E0_BUNDLE_WAIT_S` (0.45 s) after the creation:
the named wallets' buys name the curve, so the curve is resolved from the feed with no RPC call, the watch is seeded
from those buys and the gates read a real bundle; a launch whose bundle is not visible in time is skipped with the
reason and the wait, again with no RPC call. The decision records `bundle_wait_ms`; the resolve limit on this path is
the wait plus 150 ms, so a stale `MAX_RESOLVE_MS=300` cannot refuse every launch silently. `tests/test_e0_wait.py`
drives the path on a scripted feed state: bundle at 120 ms traded from the feed with the gates filled, no bundle
skipped at the deadline with no send and no RPC, a bundle under the ETH floor skipped, a 1%-tier token refused by the
tier gate, a bundle at 350 ms still inside the limit, stale buys of the same wallets on an earlier curve not taken.

**The entry not taken.** Sending at the resolve on the calldata's named-wallet count alone would sit ahead of the
bundle on purpose. Its value is p × (the fixed-entry return) − (1 − p) × (the 6.18% surcharge and fees when nothing
follows, about −12%), where p is the share of launches naming three wallets whose bundle then arrives; break-even is
near p = 0.3 at a 0.3 s entry, and p is unmeasured. The 5.3 dry run measures it for free (the readout prints "calldata
pre-check passed / bundle visible in time"); the decision waits for that number. Until then the seat is the visible
bundle, and the daily expectation in `data/derived/e0_expectation.txt` is corrected to it.

### 24.16 The bundle the engine could not see (engine 5.4)

**The 5.3 dry run.** Sep 17 12:00–12:30 UTC: 169 creations, 36 passed the calldata check, and on all 36 the engine saw
"0 named buys" inside its 450 ms wait. Not a timing tail: a blind spot. The chain for the same half hour
(`src/analysis/bundle_probe.py`): of 28 launches naming three or more wallets, 15 never saw those wallets buy at all, 9 saw
them buy 1.1–1.7 s after the creation (blocks 11–17, ten wallets, under 0.3 ETH together: the team's second-one round,
not a bundle), and 3 had a real bundle, every one bought through a helper contract inside the creation block. The
engine counted direct calls to the curve only; a named wallet calling a helper contract that buys for it is a
value-carrying transaction to another address, which the feed loop stores but the bundle count never read.

**Two hours, scored in the cache's format** (`src/analysis/today_probe.py`, 10:38–12:37 UTC,
`data/derived/today_probe_0917.txt`): 575 creations, 10 bundled launches by the tables' definition (5 an hour, the cache's
Sep 16–17 rate), all 10 through helper contracts in the creation block or the next one, and on 9 of 10 every bundle buy's
sender is a wallet named in the creation calldata. So the calldata check is right, the count behind it was blind. Seven
of the ten are one template: three wallets, 0.800 ETH, 1%-tier token, and each pays the seat −8.5 to −9.2% at 0.3 s
(nothing follows; the surcharge and fees are the loss). The three 2–3%-tier launches pay +28.8, +60.7 and −3.8%. The tier
filter of 24.14 is not a refinement in this regime, it is the difference between a losing and a paying seat.

**The cache's clock, verified against the chain** on ten Sep 16–17 launches: a row at 0.0 s is the creation block, 0.1 s
the next block, 0.3 s the third. Helper-contract bundles were already common then. The honest table of 24.15 stands.

**Engine 5.4.** The bundle is the named wallets' transactions in the creation block and the next nine, whatever contract
they call: direct curve buys as before, plus value-carrying calls to any other address, with the sender recovered on
demand and cached. On the creation-second path the chain resolve of the curve starts in the first millisecond and runs
while the bundle is awaited; a direct bundle names the curve and needs no chain read; otherwise the send waits for the
resolve. After the watch is built the helper calls are folded into it as the team's buys (a helper that named the curve
in its calldata was already seeded and is not counted twice), so the price our size and minimum output are computed
on includes the bundle; without that fold a 0.8 ETH bundle would have moved the curve twofold under a 25% slip and
the buy would have reverted. This fold applies to every seat, so the E2 and E1 readouts of bundles are corrected as well.
Every decision records `bundle_helper`, the count folded this way. `tests/test_e0_wait.py` adds the helper-bundle cases: a
helper bundle in the creation block traded with the bundle and its ETH read and the curve from the chain; a helper that
names the curve counted once; helper calls from wallets not named in the calldata not counted.

**What this regime pays.** Five bundled launches an hour, a third of them 2–3% tier: about 35 seats a day at the honest
entry. On the cache's Sep 16–17 rows with the bundle complete at 0.0–0.1 s the seat paid +15% at 0.3 s; today's three
paid +28.6% on average with n = 3. At $10 that is $30–60 a day. It is a small, positive, verifiable edge, and the first
thing 5.4 has to prove is that it takes the seat at all.

**Does the blind spot revive E2?** No. The E2 verdict of 24.7–24.13 came from the chain replay, which classified bundles by
their exemption from the surcharge and never depended on the engine's count, so helper bundles were always in it. Scored
with the independent simulator of 24.8 (second two on the wall clock, 0.3 s after its boundary, hold 5 s, take-profit
+50%), today's ten bundled launches give E2 −4.9% a trade; two of ten had no bot in second one and those two paid −2.6%
(nothing followed). The two 2–3%-tier launches that paid the creation-second seat +28.8% and +60.7% had 11 and 21 bots in
second one: the crowd is heaviest exactly where the token is good. On the cache, E2 on the clean launches was +6.3% on
Sep 12–15 (26% clean), −4.3% on Sep 16 (15% clean), and +10.2% with a −2.4% median on the six clean launches of Sep 17
0–6. The engine's refusals of helper-bundle launches under E2 were wrong for the wrong reason and right in effect: those
seats were crowded.

**The first seat taken (engine 5.4, Sep 17 12:50:10 UTC).** Creation at block 65379790, 0.90 into its second, a 2% token,
three named wallets. Block 1: a bot through a helper contract at the 6.18% surcharge. Block 4: the team's three wallets,
0.37 ETH, exempt. Block 5: fifteen bots, 0.9 ETH, at 8.18% all-in. Block 7: 0.43 ETH sold, the team flipping into the
crowd. Block 9: four more bots, 0.8 ETH. The engine saw the bundle 390 ms after the creation and sent 2 ms later from
the feed's own resolution, 4 blocks after the creation. In the replay the seat pays +245% at a 0.3–0.4 s entry, +103% at
0.5 s and +6% at 0.6 s: the block-5 flood is the whole trade, and a 100 ms later landing is the difference between a
tripling and nothing. The scorer refused to grade it, "outside the rule on the chain's reading": the tables end a bundle at
the first taxed buy, the bot at block 1, and the engine's gate does not, because a helper call that does not name the
curve is invisible to the feed. On today's two-hour universe no launch of this shape exists at all (0 of 289 with an ETH
quote and a creator above 1%; the ten bundled launches all had the bundle first), so the class is rare and the tables'
figures stand. Engine 5.41 grades the creation-second seat on its own window, the named wallets' transactions inside
nine blocks whatever bought first, so the paper result of every seat taken is recorded, and counts the bots-before-bundle
launches in the state for the record.

**First paper session on the seat (engine 5.41, Sep 17 13:00–15:25 UTC, 2.4 h).** 1,129 creations (467 an hour), 207 passed
the calldata check, 31 bundles visible in time (15%), 19 of them the 1%-tier template refused by the tier gate, 7 seats
taken. Speed: bundles inside the creation block were visible at 6–10 ms, the chain resolve took 58–177 ms, and the send
went out 7–12 ms after the later of the two; four of seven sends left 67–184 ms after the creation was seen. Paper on the
seven: mean −0.9%, median +0.1%, −$0.63 at $10. The four bundles visible at 6–95 ms paid +0.6, +1.1, +0.1 and +14.4%; the
three visible at 282–378 ms paid −12.4, −6.8 and −3.2%, the late bundles the honest table (complete by 0.3 s) had left
out and the 450 ms cap let in. Engine 5.42 adds `E0_BUNDLE_MAX_BLOCKS` (3 = the table's 0.3 s on the cache's clock) so
paper and backtest gate on the same rule. Seven seats decide nothing; the day does. Live waits for a positive paper mean
over at least twenty seats under the same rule.

**Engine 5.43: the resolve by receipt.** On the seats that matter, bundles inside the creation block, the 5.41 run spent
58–177 ms in the chain resolve, a log scan over the factory's recent blocks; the bundle itself was visible at 6–10 ms.
5.43 resolves the curve from the creation transaction's own receipt, a direct lookup by hash computed from the feed's
raw transaction, polled every 15 ms until the provider has indexed the block, with the log scan as the fallback. Every
decision records which path answered (`resolve_src` receipt, rpc or feed). On the replay's sensitivity, 2–3 points a
trade on the honest seat and far more on a flood launch (24.16: +245% at 0.4 s, +103% at 0.5 s).

**Engine 5.44: the paper score at our own landing, with the revert check.** The scorer graded every seat at the tables'
assumption, 0.3 s behind the first buyer of the seat, whatever the engine had done. 5.44 grades each seat a second time at
our estimated landing: the feed had shown `blocks_to_seat` blocks after the creation when the send left, the feed trails
the sequencer by about a block and the sequencer includes us in the block after the one it is building, so two blocks
past the last one seen. That score uses the transaction the engine actually built, its amount and its minimum output;
if the curve had moved past the 25% tolerance by the landing block, the buy reverts and the score is the gas. The paper
bankroll and the safety switch follow the landing score; the table score stays on the record as `roi_table` for
comparison with the replay. Each score also records whether a taxed outsider landed ahead of the bundle. The readout
prints the landing mean, the revert count, the bot-first count and the table mean on the same seats, so tomorrow's
decision reads paper the way live would have paid it.

### 24.17 The feed outage, the fallback that never came back, and the helper-created launches

**What happened at 19:44 UTC.** The sequencer feed went silent for 2 s at 19:29, the engine reconnected, and at 19:44 the
feed refused five connections in a row (the endpoint answered HTTP 520 from outside as well: an origin failure, not a
block on our address). The engine did what it was built to do and switched detection to the provider's WebSocket, and
then did what it should not: it stayed there. The fallback was written as a one-way door. The four seats of 19:57–20:00
were taken on the provider path, whose block stream trails the sequencer by an amount the boundary estimator put at
about 1.3 s; their paper landing was scored as if taken on the feed and is not comparable. Engine 5.45 makes the door
swing both ways: the provider path runs for `PROVIDER_FALLBACK_S` (120 s) and the feed is tried again, indefinitely;
every decision records the detection path; and on the creation-second seat the provider path is a gate, not a seat,
because a send a second late is second one at 6.18% with the crowd, not the seat the tables priced. The readout names
the detection path, the seats taken on the provider path, and excludes them from the decision count.

**The paper session so far (Sep 17 15:42–20:11 UTC, 4.5 h).** 2,244 creations, 554 past the calldata check, 125 bundles
visible in time, 31 of them the 1%-tier template refused, 6 seats taken, 2 on the sequencer feed (+8.4%, −1.5%) and 4 on
the provider path (−10.5, −0.7, +23.1, +20.7%, not comparable). No revert on any, no bot ahead of any bundle, sends 8–11 ms
behind the bundle, the receipt resolve answering on the one seat that needed a chain read.

**The helper-created launches.** 181 creations of the session carried no readable tax layout and 69 came from selectors
the engine does not know: since this evening a fifth of creations (197 of 1,046 in two hours) go through launch-helper
contracts (`0x6319141d…` with three selectors, six others) that create the token and buy in the same transaction. The
chain says they are not the seat's business: 139 of 197 hold a single buy inside the creation transaction, median 0.062
ETH, and the helper's own buy pays the contract caller's 90–99% surcharge, so neither the tier nor the bundle can be
read the way the rule reads them. By the tables' rule 22 of 197 are bundled and the seat pays −33.6% on them (n 22; +13.4%
mean, −4.4% median on the four 2–3%-tier ones), against +19.1% mean and +11.0% median on the 14 direct 2–3%-tier bundled
launches of the same two hours. The engine ignoring them is the right default; they are recorded here so a change in
their share or their behaviour is noticed.

**Engine 5.47: the provider path made lean.** The fallback path subscribed to every Buy and Sell on the chain and to every
block header, the firehose of Sep 16 again (millions of messages a day on a chain doing 500 creations an hour); the
sequencer feed never needed it because it carries raw transactions. 5.47 subscribes to the factory's events only. A
creation's factory event already names the token, the curve and the creator's buy, so nothing is resolved; the calldata
comes from one transaction read, the block's timestamp from one block read, and the bundle from one log read on the
curve, polled every 80 ms until it is complete or the wait runs out. There are no raw transactions on this path, so the
bundle is the tables' definition, exempt buys inside the block window, the same one the scorer applies, and the chain's
outsider buys are folded into the price our size is computed on. The E1 and E2 seats, which need the block clock, do not
run on this path. Usage: a few hundred calls an hour instead of tens of thousands of messages. The seat runs on the
provider path only behind `E0_ALLOW_PROVIDER=1` with `PROVIDER_LAG_MS` set from `deploy/provider_lag_probe.py`
(`deploy/provider_enable.sh` measures and applies it, under 300 ms only); the measured lag is added to those seats'
paper landing.

**The outage was a protocol change (engine 5.48).** A raw WebSocket upgrade to the feed at 21:40 UTC answered
`400 Bad Request` with the body "Compression is required: offer permessage-deflate (or Arbitrum-permessage-deflate)",
and `/feed` answered `403 Blocked for 1 hour after sustained feed connection rejections`. Since about 19:30 UTC
Robinhood's feed refuses a connection that does not offer compression; the engine had connected with compression off
since 4.x to spare the one-core box, so every reconnect since then was refused and read as an outage, and the
two-minute retry loop was walking the address toward their hour-long block. 5.48 offers permessage-deflate on the feed
(`FEED_COMPRESSION`, default deflate; a compressed connection from the sandbox delivered 61 messages in 6 s), and on a
403 stays on the provider path for the hour their edge names instead of feeding the block. The provider path remains the
fallback, lean since 5.47, with the seat allowed there in paper at an assumed 300 ms, pessimistic by about 100 ms against
the probe's delivery estimate (215 ms after the first block of each second on an NTP-synced clock, blocks produced up to
100 ms into their second).

### 24.18 The single-transaction bundle (engine 5.49), and the first night of paper

**The night's paper.** Sep 17 21:20 to Sep 18 07:25 UTC, 10 h on the sequencer feed under the block cap: 7 seats, mean
−1.4% at our landing, median −12%, two wins (+20, +30%) and five launches where nobody followed. Sends 76–296 ms after
the creation, median 205 ms; no revert; no bot ahead of any bundle.

**The chain's version of the same night** (`today_probe14`, 17:29–07:29 UTC, 14 h): 60 qualifying launches (2–3% tier,
bundle complete within three blocks), honest seat +11.1% mean, +1.7% median, 33% with no follow-through, in two-hour
buckets: +24, +19, +8, −2, then a dead patch from 22:00 to 03:00 UTC (55–100% dead), then +56 and +38% from 04:00. The
market half of the night's result is real and time-of-day shaped. The other half is the engine: 31 qualifying launches
since the restart, 7 taken.

**Why the engine took a fifth.** The bundles it missed are one transaction each: a wallet sends the whole bundle's ETH
(0.36 to 2.5 ETH) to a helper contract, `0x14b9a544…` selector `6f49227e`, whose calldata lists the buyer wallets, every
one of them in the creation's named list, and the helper buys for all of them in one call; the transaction's value
equals the bundle's ETH to the wei; on two of ten the sender is a bundler-service wallet outside the named list. The
feed sees one value-carrying transaction from one wallet, and 5.4–5.48 counted named transactions: "1 named
transactions, 1.500 ETH", refused on the three-transaction floor, thirteen times in the night on thirteen-wallet
bundles. The seven seats it took were the launches whose wallets still bought separately, a biased fifth.

**Engine 5.49.** The bundle is counted in buyers, not transactions: a value-carrying call in the block window whose
calldata names wallets from the creation's list is a bundle transaction whoever sent it, its named recipients are the
buyers, its value the ETH. The same rule seeds the watch for every seat (`fold_buy` takes the buyers of a helper call),
so the gates, the price and the E1/E2 readouts all see the bundle the chain sees. Three tests: one helper transaction
from a named sender with two more buyers in its calldata, traded with bundle 3; the same from an unnamed bundler wallet,
traded with bundle 3; one named wallet alone with 1.5 ETH, skipped as one buyer. The count of comparable paper seats
starts again from this build, and the readout's near-miss list now reads "named buyers".

### 24.19 The live trade, and the second the seat sits in (engine 5.51)

**What happened.** The first live trade went out on Sep 18 at 09:43:52 UTC on curve `0x1372f539…`: $10 (0.004 ETH),
minOut 810,889 tokens, sent the moment the bundle was visible. It landed three blocks after the creation, at index 1 of
its block, 66126814, and reverted: status 0, 53,160 gas, cost about $0.02. The curve's state just before it (2.35 ETH /
715.6M tokens after a 0.66 ETH bundle, tier 2.44%) would have given 1.11M tokens at the 6.18% surcharge, 137% of the
minOut, so the revert was not slippage. Replaying the exact call with `eth_call` returned the contract's own error,
`0x71c4efed(12,191 tokens offered, 810,889 minimum)`: the curve offered **1.1% of the fair amount**, the 98% snipe tax,
and the minOut refused it. The same call reverts at every state through block +5 and passes from block +6, for any
amount and from any address; blocks +0 to +5 carry the creation block's timestamp, block +6 the next second's.

**The rule, with real timestamps.** Round 12 had it right (section 20: the tax is keyed to whole seconds, 93–98% in
the creation second) and 24.13 overturned it wrongly: `e0_seat.py` measured time as 0.1 s a block from the creation
block and read next-second buys at small block offsets as creation-second buys. On Sep 18 00:24–10:24 UTC, 1,872
surcharged buys landed within nine blocks of a creation on 747 launches: all 1,547 at the 6.2% surcharge sat in a
later second than their creation block; every same-second outsider buy (53) paid 98%; 63 more paid 98% in a later
second (contract callers and the like). The creation block is followed by a median of 6 blocks (4 two days ago) that
still share its second, so a send 0.3 s after the creation lands inside it 70–96% of the time. The creation-second seat
for an outsider is therefore a 98% tax with a minOut revert in front of it, and the +13–19% of 24.15 was the honest
replay of a seat that does not exist: it priced every entry at 6.18%. Engine 5.51 refuses `SEAT=E0` without `EXEMPT=1`
again; `E0_OUTSIDER` no longer opts in.

**The next-second seat, honestly.** `src/analysis/e1_honest.py` scores the first legal outside seat with real second
boundaries: fold every buy and sell that carries the creation's timestamp, enter in the first block of the next second
either first or after that block's other buys, 6.18% surcharge plus the tier, 3% of supply cap, hold 15 blocks (1.5 s),
sell at the tier fee with our own impact. Launches with >= 3 named wallets, a bundle >= 0.3 ETH in the creation second
and a 2–3% tier (the engine's band), `data/derived/e1_honest_0918.txt`:

| window | launches | position | mean | median | win | dead | $/trade at $250 | $/day at $250 |
|---|---|---|---|---|---|---|---|---|
| Sep 17 20:38 – Sep 18 10:36 | 50 (86/day) | first in the block | +8.0% | +1.3% | 54% | 0% | +$21 | +$1,804 |
| same | same | after the block's other buys | −4.6% | −10.0% | 20% | 6% | −$11 | −$907 |
| Sep 15 20:47 – Sep 16 10:45 | 43 (74/day) | first in the block | +19.7% | +14.2% | 63% | 0% | +$50 | +$3,679 |
| same | same | after the block's other buys | +5.2% | −0.9% | 44% | 5% | +$14 | +$1,031 |

The next second's first block carries 2.7–3.4 other buys on average, 0.18 ETH ahead of a last-placed entry; 12 of 50
launches today and 4 of 43 two days ago had none. On the 1–2% tier band the seat is +2.6% first and −1.3% to −2.0% last
on both windows. On the live launch itself the seat pays +25.7% first and +0.6% behind the three bots that took
indices 1, 2 and 4 of block +6 through helper contracts. The position in that block is the whole edge, it is decided by
who reaches the sequencer first at the second boundary, and paper cannot measure it: the engine's E1 mode times its send
to the estimated boundary (sections 21.5, 23.4), and only real sends show where it lands. The round-12 verdict stands:
the first legal outside seat is a few points a trade at best, positive on some days and negative on others, and it
belongs to whoever is first in the block.

**What the $10 bought.** The revert cost the gas and answered the question the paper could not: the seat the engine
was built around since 24.13 is inside the creation second, and the creation second is closed. Nothing else was lost;
the wallet holds what it held. The engine stays capped and refuses the seat.

### 24.20 Five days on the true clock, the crowd, and the burst (engine 5.6)

`src/analysis/e1_multi.py` scores both legal outside seats on five full days (Sep 13 11:23 – Sep 18 11:17 UTC, 38,000
creations, 740 qualifying launches: >= 3 named wallets, bundle >= 0.3 ETH inside the creation's clock second, tier 2–3%,
ETH quote) with real block timestamps, from the public RPC: fold everything stamped with the creation's second, enter in
the first block of the next second first or behind that block's other buys, or one block late, 6.18% plus the tier, 3% of
supply cap, sell 15 blocks later at the tier fee with our own impact; the second-two seat the same way at +0.19%.
`data/derived/e1_five_days_0918.txt`.

| day (UTC) | n | first in the block | behind the block's buys | one block late | E2 first | E2 behind |
|---|---|---|---|---|---|---|
| Sep 13 | 225 | +17.3% (med +7.2%, 61% win) | +8.2% | +5.3% | +3.0% | −2.6% |
| Sep 14 | 189 | +18.5% (+1.6%, 51%) | +5.3% | +3.0% | +1.8% | −2.3% |
| Sep 15 | 124 | +15.2% (+3.5%, 58%) | +1.2% | −2.3% | −1.8% | −3.7% |
| Sep 16 | 74 | +16.4% (−1.9%, 49%) | +2.7% | −2.6% | +0.0% | −1.7% |
| Sep 17 | 128 | +10.8% (+1.5%, 54%) | −3.6% | −5.3% | −2.4% | −3.4% |
| pooled | 740 (148/day) | **+16.1% (+3.7%, 56%, 1% dead)** | +3.7% | +0.8% | +0.6% | −2.7% |

At $250 capped at 3% of supply (36% of launches cap below it, mean stake $241) first in the block is $39 a trade and about
$5,900 a day; the $10 stake scores +15.4%, so the seat is not capacity-bound at this size. Hold 15 and 30 blocks score
alike (+16.1%, +16.2%); 60 blocks +14.6% and a +50% take-profit +12.6% score worse.

**The value is the crowd.** Alone in the next second's first block (231 of 740 launches, 31%) the seat loses 3.2% (21%
win). First ahead of one other buy +5.2%; ahead of two +23%; three +19%; four +23%; five +31%; six or more +49% (124
launches, median +33%). Behind the whole crowd it still pays +6.8% on contested launches (−1.3% on Sep 17, +12.6% on
Sep 13). The bots that buy in that block are the demand we sell into 1.5 s later; the eight most frequent occupants are
each present on 8–15% of launches and the three most frequent together on 25%, a rotating cast rather than one shop.
Bundles of 0.3–0.5 ETH draw a crowd on 62% of launches and pay +8.7% first, nothing behind; 0.5 ETH and above draw one on
70–78% and pay +17% to +27% first. Tokens at the 2.0–2.25% tier pay +11.8% first, the rest +18–21%. The 1% tier class (tax under 100 bps), scored the
same way on Sep 16–18 (257 launches), is dead: −0.0% first in the block, −1.2% behind, 33% win, median −7%, and the bots
leave half of them alone (0.9 other buys a block against 2.6); the tier gate stays. 04:00–08:00 UTC pays
best (+38% first on 30 launches) and 02:00–04:00 worst (−2% on 18); no hour filter is warranted on these counts.

**Position, not tolerance.** A tight minOut as a "fill only if first" rule is wrong for this seat: behind the crowd, a 3%
tolerance fills 26% of the time and turns +6.8% into +0.4%, because the launches where a big crowd is ahead are the ones
that pump. The tolerance's only job is to reject a second fill of our own inside a burst: at $250 a second identical shot
gets about 8% fewer tokens, so 7%; at $100 about 3.4%, so 3%.

**The burst (engine 5.6).** The sequencer takes transactions in arrival order and there is no priority fee, so the seat
belongs to whoever arrives first after the tick. A single send needs a safety margin for its clock error or it lands in
the creation second at 98%. The burst removes the margin: `BURST_N` shots at consecutive nonces, `BURST_STEP_MS` apart, the
first `BURST_LEAD_MS` before the predicted boundary, each on its own warm socket to the sequencer, all signed before the
first leaves. Shots before the tick revert on their minOut for about $0.008 each; the first past the tick fills; the later
ones revert on the same minOut once our own fill has moved the price. Against a single-shot sender it arrives one step
after the tick instead of a margin after it; against a bursting sender in the same zone it is a coin flip. Twelve tests
on the scripted feed (`tests/test_burst.py`): four shots 4 ms apart at nonces 5–8 with the state nonce advanced by six,
the first planned 8 ms before the boundary less the signing budget, identical value and calldata, the filled shot's receipt
becoming the position with the sell at the nonce after the last shot, a burst with no fill logged as reverted with no
position, and the dry run's four unsigned shots. The expected value by the share of contested blocks we win, alone
always ours: 0% → +3.7% a trade (the "behind" column), 50% → +9.9%, 100% → +16.1%. The share is measured by the landing
test of runbook 5e on the Ohio box, ten launches at $100, position read from every included shot's receipt.

### 24.21 Calibrating the burst: New York, then Ohio (engines 5.61–5.62)

**Five live bursts from New York.** The first three (13:50–13:57 UTC, five shots at $10, 1% tier tokens) all landed in
the second block of the new second with every shot in the same block: the saved state had restored a 25 ms margin, 26 ms
passed between the boundary wake and the first shot (gates, sizing, build and signing after the wait on one core), and the
estimate is in feed-arrival time. `deploy/feed_lag_probe.py` put the feed's delivery lag at 67–73 ms on that box (p5–p10
of flip arrival minus its second, NTP within 50 µs). Engine 5.61 builds and signs the shots before the boundary and
fires them on the estimate (`predict-prebuilt`); 5.62 refuses to fire a burst without a confident estimate (the first
send of the 5.61 run had fallen back to react mode: twelve shots 429 ms into the second, all reverted on the guard, six
cents). Two twelve-shot bursts 120 to 10 ms before the estimate then put their first shots in the **first block** of the
new second at index 19 and index 6, five to seven shots in that block and the rest in the next: on the New York box the
tick sits about 150 ms before the estimate, and 5 and 18 transactions were ahead of the first shot.

**Ohio.** A c6i.large in us-east-2 (`docs/STEP_BY_STEP.md` Part 1b): 1.4 ms round trip to the sequencer against 21 ms
from New York; the feed's lag there is 81–93 ms (through Cloudflare's edge, a little more than New York, and irrelevant
to the send). The first live burst from Ohio, twelve shots 200 to 90 ms before the estimate at $5:

| shot | ms before the estimate | landed | index | status |
|---|---|---|---|---|
| 1–3 | 200, 190, 180 | last block of the creation second | 5, 23, 25 | reverted (98%, the guard) |
| **4** | **170** | **first block of the next second** | **2** | **filled** |
| 5–12 | 160 … 90 | first block of the next second | 23–35 | reverted (the guard, after the crowd) |

Between shot 4 at index 2 and shot 5 ten milliseconds later at index 23, about twenty other transactions landed: the
bots' wave arrives within 10 ms of the tick, and from Ohio the first shot past the tick was ahead of all of it. The tick
sits 170–180 ms before the estimate on that box. The production shape from there: nine shots 3 ms apart from 184 ms
before the estimate, `BURST_SLIP=0.03` so that the shots behind the crowd revert, on the 2–3% tier with bundles of 0.5
ETH and more, $20 stakes, five sends, the index read on every one. One launch is not a verdict; it is the position the
five-day table pays +25% for, and the test that follows counts how often it repeats.

Money: the wallet went from 0.02458 ETH at the start of the day to 0.02695 after twelve real trades, about +$6, on
launches of the wrong class and mostly in the wrong position; the number says the machinery works, nothing about the edge.

### 24.22 What the sequencer's clock actually does, and the ramp model (engines 5.7–5.91)

Two burst attempts on real launches (tax 200, bundles 0.56 and 0.72 ETH) fired 184 to 160 ms before the vote's estimate
and both landed a full block early, all shots reverted on the 98% price for three cents; a wider 21-shot window did the
same twice more. The estimate itself was the problem, so the clock was probed rather than the lead re-guessed.

- `deploy/feed_lag_probe.py`: the feed delivers a second's first block 81–93 ms after that second at best on the Ohio box
  (67–73 in New York), with a spread of 140 ms behind it.
- `deploy/grid_probe.py` (90 s): 882 blocks, a period of 101.58 ms, and the first block of each second walking forward
  16 ms a second in a clean sawtooth that wraps by 86: ten blocks a second, sometimes nine.
- `deploy/timer_probe.py` (180 s): consecutive block numbers, seconds holding 10 blocks 155 times, 9 blocks 20 times, 8
  twice, 6 once; **no period fits all the flips** (the admissible origin is empty at every candidate), and a least-squares
  line leaves a 386 ms residual against the 30 ms a strict timer would leave. The block clock is regular for a few
  seconds and wanders over ten.

Three estimators were built and scored on the feed alone (`slot_shadow`, every 30 flips, no send): the vote (5.4x) sits
+55 ms late with a 20 to 130 ms spread; a phase model folding every arrival on the period (5.7) is no better, because
the delivery jitter it averages is also what it must predict; a strict-timer model on flip block numbers (5.8) finds no
fit at all. The **ramp model** (5.9) fits a line through the last thirty block arrivals and predicts the next second's
first block ten blocks after the last one: median error −10 ms, tails ±70 ms that are mostly the flip's own delivery
jitter, and it names the block nine times in ten, the tenth being the 9-block catch-up 86 ms early. That is the target,
and the burst is sized to it: 50 shots 3 ms apart from 100 ms before the predicted block window to 47 ms after, about
18 cents of reverts a launch, `SLOT_SEND=1 SLOT_LEAD_MS=100 FEED_LAG_MS=85`. Every landing logs the flip's arrival against
the first shot and the first fill, the constants that narrow the window once they repeat.

### 24.23 First landings at the front of the block on the launches that pay (Sep 18, 16:5x–17:1x UTC)

Four ramp-aimed bursts from Ohio (50 shots 3 ms apart, 100 ms before the ramp's predicted block window to 47 ms after,
$15 stakes, 3% guard) on 2–3% tier launches with bundles of 0.5 ETH and more:

| launch | shots before the seat block opened | our first shot in the seat second's first block | outcome |
|---|---|---|---|
| 0x511f1f88 | 17 | index 2, filled | sold 1.5 s later, about +7% |
| 0x482b6bcd | 27 | **index 1, filled** | sold, about +7% |
| 0xddd5df06 | 30 | index 2, one bot ahead, the 3% guard refused | gas |
| 0xa92fdeb8 | 30 | index 4, three bots ahead, the guard refused | gas |

Every burst straddled the block's opening (the fill or the first seat-block shot fell between shots 18 and 31 of 50),
so the timing is solved to the width of the window, about 18 cents of reverts a launch. The race then reads first, first,
second, fourth: three of four at the front or one behind it. Between our first seat-block shot and the next one 3 ms
later, 20 to 50 other transactions landed every time: the crowd arrives within milliseconds of the opening, and the first
shot past it is the seat. The wallet went from 0.02677 to 0.02755 ETH on the two fills, about +$2 on $30 of stakes. Every
shot the sequencer was asked to take, it took (all fifty answers carried the hash); one burst's last twelve shots were
mined after the ten-second receipt wait, harmless. At test stakes the 3% guard refuses a fill behind one bot, which the
five-day table says is still worth taking; at production stakes the guard is 7% and our own fill is what protects the
burst, so that fill goes through.

### 24.24 The night of Sep 18: the burst filled five and six times, and the fix is the wallet (engine 5.93)

Engine 5.92 ran on Ohio from 19:54 UTC with the production burst (35 shots 3 ms apart, ramp-aimed, 3% guard, $15 stakes,
cap ten sends, bundles of 0.5 ETH and more, 2–3% tier). `src/analysis/night_readout.py` reads every receipt of every
hash the engine sent since its start and reconciles them against the wallet; the night, from its output:

| time (UTC) | shots landed | where our shots sat | fills | ETH in | ETH out | net |
|---|---|---|---|---|---|---|
| 20:12 | 35 of 35 | 17 in the creation second, 18 in the seat block from index 1 | 1 (index 1) | 0.00571 | 0.00538 | −0.00046 (−8.0%) |
| 21:10 | 35 | 19 creation second, 16 seat block from index 2 | none | | | gas 0.00012 |
| 21:11 | 22 | 13 and 9, from index 12 and 19 | none | | | gas 0.00008 |
| 21:19 | 35 | 2 and 33, from index 23 and 1 | none | | | gas 0.00012 |
| 21:35 | 35 | 29 and 6, from index 5 and 4 | none | | | gas 0.00012 |
| 21:47 | 35 | 7 and 28, from index 31 and 7 | none | | | gas 0.00013 |
| 21:52 | **6 of 35** | one block, fills at index 4, 32, 38, 39, 40, 41 | **6** | 0.03426 | 0.03018 | −0.00413 (−12%) |
| 21:57 | **26 of 35** | 21 creation second; seat block from index 1, fills at 1, 21, 28, 29, 30 | **5** | 0.02856 | 0.01277 | −0.01590 (−55.7%) |

Receipts explain −0.02106 ETH; the wallet moved from 0.03573 to 0.01512 ETH (−0.02061, about −$54); the difference is a
rounding of the starting figure. No position is open, no sell reverted, no alarm other than the two double fills.

**What happened.** The burst's shots are independent transactions at consecutive nonces. The design relied on the 3%
guard to refuse every shot after the first fill: our own buy moves the price, and the next shot's minOut is then out of
reach. That holds at $150 and above (own impact 5–8%) and fails at $15, where a fill moves the price by well under 1%;
24.23 had noted a four-fill at $15 as noise. It is not noise: every shot after the fill also fills, and the run stops only
when the wallet can no longer fund a shot: the sequencer drops the rest for insufficient funds (the "6 of 35" and
"26 of 35" landed). The stake was therefore never $15; it was the whole wallet on every launch that filled, and one
launch at −56% took the night. The first fill of the 21:57 launch sat at index 1 of the seat block, exactly the seat the
tables price at +16% a trade on average: the loss is the launch's, the size is the bug's.

**The fix (engine 5.93, `WALLET_STAKE=1`, on by default live).** The sequencer's insufficient-funds drop is made the cap
on purpose: every buy is sized to the wallet less a gas reserve (`GAS_RESERVE_USD`, $2.50 or the burst's reverts plus the
approve, the exit's $2 fee ceiling and the upfront gas of the filling shot, whichever is more), so after the first fill
what is left cannot fund a second shot, whatever the guard sees. `STAKE_MAX` becomes the most the wallet may hold: above
it the engine refuses to trade and says to withdraw the excess or raise the cap; below `STAKE_MIN` it says to top up; a
balance older than a minute refuses (the wallet is read every 10 s when idle and right after every landing and exit);
and a launch on which the 3% supply cap would shrink the buy to less than half of the wallet is not taken, because the
remainder could fund a second fill. `tests/test_wallet_stake.py` runs the six cases on the scripted feed. The rule for
the operator is one line: what sits in the wallet is what one launch can lose, plus $3 of gas.

**Two more things the receipts showed.** The sells landed 31–36 blocks after the buy while the tables hold 15: the hold
clock started after the receipt reader's 0.6 s settle and a wait of up to 0.5 s for the flip message, not at the fill.
5.93 stamps the fill's time in the receipt poller and starts the hold there (`fill_seen_ms` on the decision), and stops
the other 34 pollers once the burst is resolved (a dropped shot was polled for the full ten seconds, about 200 RPC calls
each). With the clock on the fill, `HOLD_S=1.3` lands the sell about 15 blocks after the buy. And the five bursts that
did not fill: the readout now labels each block creation-second, seat or later and lists the buys on the curve ahead of
our first shot with their ETH, so a refusal behind the crowd (the guard working) is told from a burst that missed the
seat block; those five are to be read that way on the next run of the readout.

**The guard was refusing the seat.** The readout, re-run with the curve's own Buy events: seven of the eight bursts
reached the seat block (one landed all 35 shots in the creation second, a block early), and in four of them our first
seat-block shot had no buy on the curve ahead of it (index 1, 2, 4 and 7, the transactions before us were not buys) and
still did not fill. The 3% guard is measured against the feed's reserves at build time, 35 ms before the first shot and
about 130 ms before the seat block; the bundle's own tax-free buys in the last blocks of the creation second move the
price past 3% before the seat block opens, and every shot then reverts on its minOut. The tables never refuse a first
fill, and their own minOut test says a 3% tolerance behind the crowd turns +6.8% into +0.4% while 25% keeps +5.6%.
The guard existed to stop the burst's own second fill, and the wallet now does that. `BURST_SLIP=0.25` from here, the
engine's ordinary slip. The tables also score hold 15 and hold 30 blocks the same (+16.1% and +16.2%), so the late
sells did not cause the night's losses.

**The tally so far.** Nine fills on real launches from Ohio at $15 to the wallet: +24%, −3%, +7.5%, −15% (four fills),
+49% (four fills), +22%, and the night's three read on the first fill alone −8.0%, −10.9% and −54.9% (the later fills of
the two multi-fills bought higher and are excluded). Four wins in nine, mean about +1%. Against the tables'
+16% mean and 56% win share this is too few trades to judge either way (the per-trade spread is about 30 points, so nine
trades resolve the mean to ±10), and the size bug means the dollar result of the night says nothing about the seat.

### 24.25 The BuyOnce relay: the stake is a setting again (engine 5.94)

The wallet rule of 24.24 ties the bet to the wallet, because a plain transaction cannot say "only if I have not bought
yet". A contract can. `contracts/BuyOnce.sol` (Solidity 0.8.26, 1,810 bytes of runtime code, no dependencies) is a
relay owned by the wallet with one job: `buy(curve, amountIn, minOut)`, payable, refuses any caller but the owner,
refuses a curve it has already bought (`bought[curve]`), otherwise forwards the value to the curve's own `buy` with the
wallet as the recipient and bubbles the curve's error unchanged. A shot that reaches the curve inside the tax second
reverts inside the curve, the whole call reverts, and the flag stays clear for the next shot; the first shot past the
opening buys and sets the flag; every later shot reverts on the flag and pays only gas. The tokens land in the wallet, so
the approve and the sell are untouched. The owner can sweep back any ETH or token that ends up in the relay.

Two facts were checked on the chain before writing it. The curve's code never reads `tx.origin` (the usual ban on
contract buyers); it uses code-size checks nine times, so a buy was simulated from a contract address and from the
wallet on a live curve: identical tokens out. Then the relay's compiled code was placed on a live curve's chain state
with `eth_call` state overrides and exercised: the owner buys (the curve's Buy event fires with the relay as sender and
the wallet as recipient), a stranger gets `NotOwner`, a curve with the flag set gets `AlreadyBought(curve)`, and an
impossible minOut returns the curve's own `0x71c4efed(offered, minOut)`.

Engine 5.94 takes `RELAY=<address>`: every shot goes to the relay with (curve, amountIn, minOut) and the stake as value,
the fill is read from the curve's Buy event in the shot's receipt as before, `WALLET_STAKE` turns off by default and
`STAKE_MIN`/`STAKE_MAX` are the bet again, a double fill is reported as a relay failure, and the engine refuses to start
if the relay has no code or is not owned by the wallet. `deploy/relay_deploy.py` deploys it from the machine's wallet
(a few cents of gas), compares the runtime code byte for byte with the compiled artifact, reads `owner()` back and
simulates one buy through it. `tests/test_relay.py` covers the calldata, the value, the gas, the fill, the alarm and the
dry run. The Buy event's first topic is the sender and the second the recipient (checked on live events), so
`live_check.py` and `night_readout.py`, which match the recipient, still recognise our fills.

**Two exit facts from the first relay trades (Sep 19, engine 5.95).** The per-trade timeline showed the approve sent
right after the buy never landing (`approve_not_seen` at +1.1 s, `approve_missing` at +2.4 s, then a fresh approve and
the sell): it was sent at the burst's first nonce plus one, the second shot's nonce, so the sequencer refused it on every
burst since 5.6, and every exit waited a second for a receipt that could not come before re-approving. 5.95 sends it at
the last shot's nonce plus one (`tests/test_relay.py` checks the nonce); the sells should now land about 15 blocks after
the buy instead of 27–36. And the wallet's change was 0.00029 ETH short of what the receipts said: the curve's Sell event
carries four words (tokens in, ETH out, two fees) and the wallet receives the ETH out net of both fees, about 3% here;
the readout nets them now, so the live returns it prints are about three points lower than before, and match the wallet.

**The first two relay trades, read with the send timing (Sep 19, engines 5.95–5.96).** 06:44: aimed on time, every
shot fired within 0.0 ms of plan, and the sequencer answered up to 1.26 s later; the seat's first block reached the feed
1.1 s after we fired, and every shot was included in the second after the seat (index 13, one buy ahead, −19.3% net of
fees). The sequencer stalled for about a second and our transactions, already sent, landed after it. 07:14: fired on
time, first in the seat block with nothing ahead and two small buys behind, −2.1% net: a launch with no crowd, which the
tables price at −3.2% on average. Two lessons became code. A sent transaction cannot be recalled, but the relay reads the
same block clock the curve keys its tax to, so `BuyOnce.buy` now takes a `deadline` (the seat's clock second) and reverts
with `TooLate(blockTime, deadline)` in any later block, for a cent, instead of buying the dead seat behind a stall
(exercised on a live curve's state before deployment: past deadline refused, future and none accepted, the old
three-argument call gets a plain revert, which is how engine 5.96 tells an old relay from the new one at start and
refuses to run on the old). And the readout nets the two sell fees the curve keeps, so its returns match the wallet.

**Sep 19 08:01 and 08:53 (engine 5.97).** The first was the seat exactly: first in the seat block, nothing ahead,
one buy of 0.1 ETH behind, sold 15 blocks later with the sell taking 0.2 s, +2.9%. The second lost 29 of its 35 shots:
the first six reached the chain (index 72 of the seat block, three buys of 0.47 ETH ahead, −12.7%), the rest never did,
and because the engine assumed every shot had landed, the approve went out at a nonce 29 ahead of the chain's and failed
as before. Two changes: a shot whose socket fails on the write or the read is re-fired once on a fresh socket with the
same hash (`refired_after` on its `send_answers`), and the position's nonce is the last shot the chain actually took,
with a `burst_dropped` event naming the lost shots and the sequencer's answers, and the next launch waiting for a fresh
nonce from the chain. The readout prints the lost shots and the answers, so the cause is read from the log rather than
guessed. And the fee correction of the morning was wrong: recent sellers' balance changes match the Sell event's ETH
out exactly (the two fee words are informational, already taken out), so the readout is back to the gross figure; the
0.0003 ETH gap of the first two relay trades stays unexplained, about eighty cents.

### 24.26 Shooters: one wallet per shot, the stake in the relay (engine 6.0, third relay)

The burst's shots were one wallet's consecutive nonces on 35 sockets 3 ms apart. The sequencer takes requests from
different sockets in parallel, and under load it processed shot 6 before shot 5 and refused shots 6 to 34 as "nonce too
high" (Sep 19 08:53; the sequencer's own answers, read back from the log). The failure is structural, and it strikes on
crowded launches, the ones the tables pay for. The third relay removes the dependency: every shot comes from its own
shooter wallet, which holds gas only, and the relay holds the stake and buys with its own ETH on any registered shooter's
order (`shooters`, set by the owner), once per curve, at or before the deadline, tokens to the owner wallet. No shot
depends on another; a refused or lost shot costs its shooter nothing but the chance. Exercised on a live curve's state:
a shooter buys from the relay's ETH, the owner too, a stranger gets `NotShooter`, a relay below the stake gets
`Insufficient(balance, needed)`, a past deadline `TooLate`, a curve already bought `AlreadyBought`, and value sent
with the call is refused (not payable).

Engine 6.0 takes `SHOOTER_KEYS` (created by `deploy/relay_ops.py shooters-create 35`, registered on the relay by
`shooters-register`, given gas by `shooters-fund`, all from the machine's wallet; `deposit` puts the stake into the
relay). Each shot is built at its shooter's nonce with no value and 250k gas and the send step signs it with that
shooter's key (`keys=`; the engine refuses an older send step). The wallet's nonce is reserved for the approve and the
sell only, so the exit no longer depends on how many shots landed. The shooters' nonces and gas are read from the chain
at start, after every burst and every five minutes; a shooter below 0.00004 ETH is refilled to 0.0001 from the wallet;
the relay is refilled to 1.2 stakes after every exit; a relay below one stake, or fewer than half the shooters ready,
gates the launch. `tests/test_shooters.py` (16 checks) and `tests/test_send_step_keys.py` (3) cover it.

**6.03 (Sep 19, 12:xx).** The start-up checks added with the relays (the relay's code and owner, the deadline, the shooters'
registration) sat before the line that loads the send step, so in live mode `SEND` was still `None` and none of them
ran; the engine logged no `shooters` report and would have started on a wrong relay. 6.03 runs them right after the send
step is loaded. Nothing was lost to it: the relay and the shooters were verified by the deploy and operations scripts,
and the trades of the morning went through them correctly.

**A wrong column, and the switch on it (Sep 19 13:xx, engine 6.05).** The engine's `score` event carries two paper results
for every qualifying launch: `roi`, the seat 0.3 s behind the first buyer of the seat's second (the tables' "behind"
position), and `roi_e1`, the seat at the front of that second, ahead of every buyer. The burst takes the front (index 1-2
on every clean trade), but the safety switch, the readouts and the first diagnosis of the day read `roi`: 145 launches at
−8.5% mean and 9% winners, which I reported as the market having changed. The live results of six flat launches matched
either column (no crowd, the same price from either seat); the one crowded launch made +38.4% live and scored −2% from
0.3 s behind, the crowd's buys already in the price. 6.05 scores, switches and reads out the front seat when the burst
is on, and `live_check` reads a relay-paid buy from the curve's Buy event. The unchanged five-day script, run on Sep 18-19
from the chain, is the independent check of whether the front seat still pays (`data/derived/e1_sep1819/`).

**6.06: the engine's scorer on the real clock.** The engine's replay measured time as blocks after the creation at 9.9 a
second, the error 24.19 had found in the analysis and corrected in the tables (real second boundaries) but not in the
engine: its simulated seat's second began up to 0.9 s after the real one and its front seat entered behind buyers our
burst is ahead of. On Sep 19 it read the front seat at −3.9% over 24 hours while the tables' script read +5.6% on the
same launches. 6.06 builds a clock from the feed's flips (every second's first block is known to the engine) so the
seat's second's first block sits at exactly 1.0 s, the tables' definition; the score event says `clock: seconds` or
`offset` (the fallback within a minute of a restart). `tests/test_clock.py` checks the clock and the three seats' order.

### 24.27 The last 24 hours by the tables' own script (Sep 18 13:27 to Sep 19 13:10 UTC)

`src/analysis/e1_multi.py`, unchanged from the five-day run, on the chain, real second boundaries, the same filters
(tier 2-3%, three named wallets, bundle 0.3 ETH and more), hold 15 blocks:

| window (UTC) | qualifying | E1 first mean | median | win | E1 behind | E1 one block late |
|---|---|---|---|---|---|---|
| Sep 18 13:27 to 01:25 | 105 (211 a day) | **+10.5%** | +1.1% | 51% | −7.3% | −8.2% |
| Sep 19 01:12 to 13:10 | 36 (72 a day) | **+5.6%** | −0.1% | 50% | −1.7% | −3.1% |
| pooled | 141 | **+9.3%** | +1.0% | 51% | −5.9% | −6.9% |

By hour, the evening pays and the small hours do not: 16h +20% (13), 18h +22% (13), 19h +18% (16), 20h +12% (11),
22h +14% (10); 12h −11% (4), 14h −9% (2), 21h −5% (14), 23h −4% (8). Against the five days (+16.1%, 56% win, 148 a
day) the seat pays about 60% of what it did and half as many launches qualify, and it pays in the same place: first in
the block, with the crowd behind (behind the crowd is −5.9% now, against +3.7% then). The engine's own scorer had read
the same day at −8.5% (the "behind" column) and then −3.9% (the front on the block-offset clock); both were the engine's
errors, corrected in 6.05 and 6.06. The seven live trades of the day, −0.8% on average, fell in the morning hours where
the script reads +5.6%, and seven trades resolve a mean only to about ±10 points.

At $15 a launch the day's expectation is about $1.40 a launch, of the order of $150 to $200 a day at the day's rate if
the seat keeps paying what it paid; at $250 it would have been $5,400 for the evening half alone by the script's
figure, with the position risk that stake carries. The daily check is the script on the last 24 hours (`e1_multi.py 12 0`
and `12 12`, then `e1_agg.py`), which the runbook now carries; the engine's own score line is the same measure from
the feed and should agree with it from 6.06 on.

### 24.28 The seat we get against the seat the tables price (Sep 23: every fill reconciled on the chain)

Three days after the engine was stopped, the question was put the other way round: not "what did the engine do wrong"
but "what would the tables have said for the launches we really traded, at our stake, at the position we really got".
`src/analysis/live_vs_table.py` pulls every Buy and Sell event whose counterparty is the wallet or the relay (135
events, 43 curves, Sep 17 to 20), rebuilds each launch's tape from the chain, removes our own events from it, and runs
`e1_multi.py`'s `score()` for the same launch four ways: first in the seat block (the tables' column), behind every buy
of the block, at the position we really landed with a 15-block hold, and at that position sold in the block our sell
really landed in. `data/derived/live_vs_table/sep17_20_fills.txt` has every line.

**The engine is exact.** On all 34 single-fill trades the last of those four equals the wallet's realised return to
the decimal (`execution/fees/model +0.0%` on every line): every fill landed in the seat second and paid tier + 6.18%,
every sell returned what the curve model says. The multi-fill, approve-nonce, nonce-too-high, bankroll, start-check
and clock bugs of 24.24-24.26 were real and are fixed, and none of them was the reason live pays less than the tables.

**Where the tables' +9.3% goes:**

| fills, Sep 17-20 | n | first in the block | at our position, 15 blocks | actual |
|---|---|---|---|---|
| nobody ahead of us | 22 | −1.5% | −1.5% | −3.9% (27% win) |
| somebody ahead of us | 12 | **+17.7%** | +5.8% | +7.4% (67% win) |
| all | 34 | +5.2% | +1.0% | +0.1% |

The −3.9% against −1.5% is the hold: the first trades held 24-31 blocks (the approve at the spent nonce, 24.24). Gas is
not in the tables: a 35-shot burst is 34 reverts at 27k gas plus the fill, the approve and the sell, $0.32-0.38 at
0.054 gwei, **2.3% of a $15 stake** on every burst, filled or not. As executed: +0.1% − 2.3% ≈ −2% a trade. The nine
multi-fill launches of Sep 18 (24.24) are a further −$24 and are structurally impossible since the relay.

**Why.** The race readout (`src/analysis/race_readout.py`, the engine's own timing on all 53 bursts,
`data/derived/live_vs_table/race_readout_sep18_20.txt`): on 32 of 37 fills the burst straddled the second's tick
(shot k filled with shots 1..k−1 reverted in the tax second, so the tick fell inside the 3 ms before shot k), and
when nobody faster wanted the launch we took tx index 1, the block's first user slot, 20 times of 26. On the launches
that pay, one wallet, `0x6c56103c…`, sits at index 1: ahead of us on 7 of the 12 crowd fills although we had
straddled the tick (it wins inside our 3 ms step), and first on 10 of the 13 no-fill bursts whose crowd moved the price
past the 25% guard before any shot of ours was processed (those 13 launches model +15%, +20%, +127%, +36%, +24%, +24%,
+13%, +13%, +9%, +9%, −49%, +6%, +6% for the first seat). On the other 5 crowd fills the whole burst left after the tick
(the first shot filled, at index 6 to 72): the seat blocks that matter are the congested ones, and congestion is what
makes the aim late. The sequencer is in the box's own region (3.141.111.43, warm RTT 1.3 ms); this is not a distance
problem.

The bot selects. On the tables' 141 launches it is in the seat block 18 times (13%); the first seat on its launches is
**+19.4% with 92% winners**, on the launches it skips +12% with a crowd and −8.5% without. Its launches look like the
others in the calldata (tier 2.7% vs 2.6%, bundle 0.77 vs 0.74 ETH, four named wallets vs nine, no repeat creator,
never itself a named wallet); the only thing that separates them is the crowd that arrives with it (0.40 ETH in the
seat block vs 0.17), which is the outcome, not a signal. Following it one block later, once its buy is visible, is
−10% to −15% on its launches by the tables (`E1_late1`), and the second-second seat (E2) −9% to −10%. Being second
behind it in the same block is +7% before gas, and a race for second place.

**What the tables' number is.** +9.3% is the mean over 141 launches of a seat that one bot takes when it is worth
+19% and leaves when it is worth −1.5%. We get the seat it leaves. That is the winner's curse of a latency race, and
it is not a code fix: a finer grid (1 ms, 105 shots) triples the gas to about 7% at $15, and the bot can go finer.

**What the process got wrong.** Each live shortfall was met with a mechanism bug, real, fixed, redeployed, and the
next batch expected to show the tables' number; the fill-by-fill reconciliation, which shows in one run that the
mechanism was exact by Sep 18 and the gap is who gets the seat, was never done until now. Seven trades were called
noise while 34 were on the chain. The tables assumed we are first on every launch and carried no gas; both were
assumptions of this report, not of the chain.

**The engine's own record of the last run agrees.** `night_readout.py --from "2026-09-19 14:00" --to "2026-09-20 12:00"`
on the box (604 receipts; `data/derived/live_vs_table/night_readout_last_run.txt`): 15 bursts, 15 fills, ETH in
0.08515, out 0.08272 (the chain reconciliation's −0.00243 ETH to the wei), gas from receipts 0.001773 ETH ($4.56),
net −$10.80; capital −$12.33 from the shooters' baseline, of which transfers' gas $0.18 and $1.34 unexplained (the
relay and shooter top-ups' own gas outside the window's labels is the likely remainder). Every burst straddled the
tick (the seat's block opened at shot 5 to 16 of 35; shots fired late by at most 1.1 ms); 11 of 15 fills took index 1
with nobody ahead and returned −3.7% before gas; the 4 with somebody ahead returned −0.4% where the first seat was
+12.3%. The 37-block hold of 17:14 was 1.57 s of wall clock: the block rate spiked on the hot launch (16 buys behind
us), so a hold in seconds is a longer hold in blocks exactly on the launches that pay (+51% at 15 blocks, +27% at 37);
a hold counted in blocks would have kept about $3 of that one trade. After 20:44 the engine ran 14 more hours without
a burst: the tier gate refused every eligible launch at "token tax 0 bps".

### 24.29 Verdict: three audits, two more tests, and what the seat is worth today (Sep 23)

Three independent audits ran on the public chain with no access to the engine's assumptions; their write-ups are in
`data/derived/audits_sep23/`. Two further tests followed from them.

**The seat's ground truth (`seat_ground_truth.md`).** From Buy and Sell events only: the real first buyer of the seat
block is the first curve event of that block on all 233 launches of two windows, paid tier + 6.18% on 231 (the two
others are named wallets, which pay no surcharge), and every one of 443 tracked sells returned exactly (1 − tier) of
the curve price, so the model's entry and exit arithmetic is exact. What the first buyers realised: last 30 hours
(Sep 22 01:17 to Sep 23 07:14, 175 qualifying launches), **−11.9% mean, 27% winners** when they sold within 100
blocks, −2.7% counting held lots at the mark; Sep 18-19, +6.1% and 57%. The wallet that takes index 1 ahead of us,
`0x6c56103c…`, held 20 first seats in the last 30 hours with 2.97 ETH and made **+0.0025 ETH (+0.08%)**, holding 14.5
blocks; on Sep 18-19, 16 seats, 2.40 ETH, **+2.0%**, where the tables said +24.7% for the first seat on its launches
(it held 48 blocks there). Fewer than half the first buyers sell within 100 blocks; the small ones hold into dumps.
The model's own mean on the unchanged script: **+9.3% on Sep 18-19, +1.5% on Sep 22-23** (37% winners).

**The tier gate (`tier_gate_and_calldata.md`).** Pons changed nothing: the creation selector, the calldata layout
(word 0 = 224, the launch struct at word 7, the tax at word 13), the factory and the event are the same on Sep 19,
20 and 23; the Buy event's own tax word equals word 13 on 630 of 630 launches. The 11 refusals of Sep 20 13:30-15:00
were real 1%-tier launches: 44 of the 53 bundled launches of 13:00-16:00 that day were tier 0, from about six
operators recycling wallets; 2-3% launches that qualify came back to 6-7 an hour on Sep 21-22 (170 in the last 24
hours). Two leads for the engine: the feed logged 398 creations in a window where the chain has 491 (19% missed if the
window is exact), and 7-10% of creations are wrapped in router calls the engine never sees (they rarely qualify).

**The mechanism (`mechanism_vs_scorer.md`).** The curve model reproduces all 23 fills of Sep 19 to 0.01%. From the
+9.27% claim to live, in points: regime −6.8 (the scorer on the hours we traded reads +1.85%; the evening read −2% to
+5%), position −3.6 (six fills with 1-2 buys ahead, −4.8 to −24 each; four of them from bursts that straddled the tick
well), exit −0.9, gas −2.3. Live minus the scorer on the same launches: −4.5 points (standard error 1.6). Two
defects: the engine's `gas_usd()` assumes 230k gas a round trip against a real 1.94M (12 shots before the tick at
88.6k, the fill at 137.7k, 21 relay reverts at 27k, approve 46k, sell 78.5k), so its own cost model is 8.4× low; the
sell's minOut is encoded as 0 (`tx_sell`), so a delayed sell absorbs whatever came before it. 24% of the scorer's
launches cannot be fired at because the bundle crosses 0.3 ETH too late for the burst.

**The crowd before the tick (`crowd_signal.py`).** Bots that want a launch fire at it during the creation second and
revert; those blocks reach the feed before the seat's tick. Distinct wallets already firing at the curve by block 5:

| attackers by block 5 | Sep 18-19: n, first seat, win | Sep 22-23: n, first seat, win |
|---|---|---|
| 0 | 77, +1.3%, 35% | 83, −6.4%, 17% |
| 1 | 30, +9.2%, 50% | 32, −0.2%, 44% |
| 2-3 | 13, +29.1%, 92% | 24, +7.3%, 58% |
| 4-6 | 11, +24.0%, 91% | 21, +19.1%, 67% |
| 7+ | 10, +29.0%, 80% | 15, +15.3%, 53% |

The 26 fills we took with nobody ahead were launches with no attackers; the gate would have refused them. There is
no express lane on the chain (no Timeboost auction events, no timeboost RPC): the index-1 bot bursts too, a dozen or
more shots in the last creation-second block on every one of its launches, and wins on jitter inside our 3 ms step.

**The gated seat by position (`gated_seat.py`, the tape re-pulled, our stake, hold 15 blocks, before gas):**

| gate: 2+ attackers | Sep 18-19 (34 launches) | Sep 22-23 (60 launches) |
|---|---|---|
| first in the block | +26.4%, 88% win | +12.9%, 60% win, median +5% |
| behind one buy | +18.0%, 79% | **+4.9%, 46% win, median −2.9%** |
| behind two | +14.0%, 71% | +0.1%, 38% |
| behind everybody | −0.6%, 29% | −9.8%, 22% |
| per burst landing second, 25% guard, gas $0.33: $15 / $100 | +$2.25 / +$17.1 (34 a day) | +$0.38 / +$4.55 (60 a day) |

Second place is what we can plan on (the bot takes first on the launches it wants); live we landed behind one buy on
8 of 12 crowd fills, behind two or three on the rest, and behind the whole crowd, refused by the guard, on 13 of 25
crowd bursts. Weighting those, the gated seat today is about +3% a fill before gas with a fill on perhaps half the
bursts: of the order of **+$1.3 a burst at $100, $80 a day at 60 bursts**, with a daily swing of the same size, on
an edge that went from +18% to +4.9% in four days. At $15 it is $0.20 a burst. The bots that hold first place earn
nothing on it because their stakes (0.08-0.5 ETH) move the curve; a $100 stake (0.04 ETH) is small enough for the
curve's edge to survive, and that is the only structural reason a small player could earn where they do not.

**Verdict.** The engine is exact, and the seat as built cannot pay: the launches we win are worth −1.5% first and −2%
after gas, and the launches worth having belong to a bot that is already at breakeven on them. The gated version is
real but small, decaying and high-variance, needs $100 stakes and about $400 of capital on a box holding $22, and
would have to be re-priced every day against the chain. It does not meet the brief of a very profitable, sustainable,
proven edge. If it is run at all, it is as a capped experiment: the pre-tick gate, a hold counted in blocks, a real
gas model and a sell minOut in the engine; a paper day with the model's expected return logged per burst; live only if
paper reads above +3% a fill in the current regime, with a kill line in dollars set beforehand.

### 24.30 The profitable trades, taken apart (Sep 23)

`src/analysis/pnl_timeline.py` rebuilds the P&L burst by burst from the chain and the race readout
(`data/derived/live_vs_table/pnl_timeline.txt`). It peaked at **+$24.10 on Sep 18 at 18:44 UTC**, went to −$31.65 at
21:57 (two multi-fill launches, −$10.48 and −$40.57, on launches with nobody behind us), and drifted to −$47 over the 25
relay-era trades of Sep 19. `winners_anatomy.py` then took every filled launch apart: the creation calldata, the
wallets already firing at the curve in the creation second, the buyers behind us in the seat block, the buys in the
next 15 blocks, and the curve price at +15, +60, +150, +600 blocks against our entry.

**What the 12 winners (over +5%) had that the 31 others did not:**

| | winners | the rest |
|---|---|---|
| buys behind us in the seat block | 5.2 (0.34 ETH) | 1.5 (0.06 ETH) |
| buys in the next 15 blocks | 6.7, 0.23 ETH, **5.5 wallets** | 2.2, 0.05 ETH, 2.0 wallets |
| curve price +60 blocks vs our entry | +32% | +2% |
| curve price +600 blocks vs our entry | +32% | **+21%** |

Named wallets, recurring wallets, tier and bundle size do not separate them. The edge is the crowd that arrives after
the seat, not the seat. The three trades that made the peak were multi-fills: Sep 18 18:36 (+48%, ×4, +$28.40; 1.02 ETH
behind us in the block, then 19 buys from 13 wallets, +118% at 15 blocks and +256% a minute later), 14:29 (+19%, ×5,
+$9.43, held 30 blocks) and 14:59 (+13%, ×12, +$7.93; nothing in 15 blocks, +24% at 60: the 30-block hold caught it).
At one $15 fill the same launches were worth +$13.50, +$2.85 and +$1.95. Size made the peak and size made the −$51;
over the nine multi-fill launches size was −$24. The last line of the table is the one that was not expected: the
tokens we sold were, a minute later, 20-30% above our entry, losers included. A 15-block hold sells into the crowd's
entry.

**The fleets.** In one creation-second block of Sep 18 14:17, 42 transactions from 30 wallets were aimed at the curve:
all to three relay contracts (`0x8532fee5…` 28, `0xf300b2c0…` 9, `0xa02060b9…` 5), all reverting at 48k gas — three
sniper operations with shooter fleets, the same architecture as ours, bursting at the tick; 27 more of their shots in
the seat block for two fills. The "attackers" count of 24.29 counts fleet wallets, and our own shooters on the 53
launches we fired at on Sep 18-19 (fixed in `crowd_signal.py`: shots to our relay are excluded; the Sep 22-23 numbers
were clean, the engine was stopped). We are one of four or five fleets splitting the retail that follows.

**The hold, on the population (`hold_grid.py`, 316 launches, the tape to +620 blocks, $15, before gas):**

| | first, h15 | first, h300 | behind one, h15 | behind one, h150 | behind one, h300 | behind one, h600 |
|---|---|---|---|---|---|---|
| Sep 18 (104) | +9.9% | +9.4% | +4.8% | +2.2% | +4.2% | +2.5% |
| Sep 19 (37) | +5.3% | −0.1% | +2.5% | −0.3% | −2.9% | −3.5% |
| Sep 22 (161) | +1.2% | **+11.7%** | −3.2% | +3.8% | **+6.7%** | +3.8% |
| all (316) | +4.5% | +10.1% | −0.0% | +2.6% | +4.8% | +2.8% |

A take-profit at +50% is negative everywhere (the runners go +100-300%); a −20% stop reads +13.8% first / +7.2% behind
one over 600 blocks, but the model sells at the trade that crosses the line and live the sell lands two or three
blocks after the dump, so that is an upper bound. On Sep 18 the crowd came within 1.5 s and 15 blocks was right; on
Sep 22 it comes over 30 s.

**Gate × hold, the current regime (Sep 22-23, 60 gated launches of 175, behind one, $15, before gas):**

| hold | mean | median | win | dead (< −40%) | SE |
|---|---|---|---|---|---|
| 15 blocks | +4.3% | −2.9% | 45% | 3% | 3.8 |
| 60 | +9.8% | +1.2% | 53% | 3% | 4.6 |
| 150 | +20.0% | +7.1% | 67% | 7% | 6.7 |
| **300** | **+25.1%** | **+15.4%** | **63%** | 10% | 8.0 |
| 600 | +28.6% | +17.1% | 63% | 13% | 9.6 |

Per burst after gas at $15: +$0.32 at 15 blocks, **+$3.43 at 300** (sd $9.25; 60 bursts a day, about $200 a day, daily
sd $72 if independent); at $100, +$24.72 a burst. The 115 launches the gate skips are negative at every hold. On
Sep 18-19's gated launches the long hold was not better (+17.2% at 15 blocks, +13.2% at 300), so the hold is
regime-dependent and a rule fitted to Sep 22 is not yet a rule. Everything here is in sample on one 30-hour window.
The out-of-sample run is Sep 20 12:00 to Sep 22 00:30 (three 12-hour windows of the tables' script, then the crowd
signal and the hold grid: `data/derived/e1_sep2021/`, `launches_oos_sep2021.json`); if the gated long hold survives it,
the engine change is the pre-tick gate at burst-build time, a hold of 150-300 blocks with a sell minOut, the real gas
model, and a paper day before any stake.

### 24.31 Out of sample: Sep 20-21, and the rule as it will be run (Sep 23)

The tables' script on three 12-hour windows nothing above was fitted on (`data/derived/e1_sep2021/`: Sep 20 13:26 to Sep 22
01:02 UTC, 189 qualifying launches), then the crowd signal and the position-by-hold model on them
(`crowd_signal_oos_sep2021.json`, `position_hold_oos_sep2021.txt`).

**The gate holds out of sample.** Distinct wallets already firing at the curve by creation-second block 5 (our own shooters
excluded; the engine was stopped for most of this window anyway):

| attackers | launches | first seat | win |
|---|---|---|---|
| 0 | 90 | −1.0% | 29% |
| 1 | 34 | +9.0% | 47% |
| 2-3 | 27 | **+30.2%** | 67% |
| 4-6 | 18 | +13.9% | 89% |
| 7+ | 20 | +8.2% | 50% |

**The hold, by position, on the 65 gated launches ($15, before gas):**

| position | 15 blocks | 150 | 300 | 600 |
|---|---|---|---|---|
| first | +18.1% / 66% | +16.2% | +16.8% / 58% | +8.0% |
| behind one | +11.2% / 53% | +9.7% | **+10.9% / 54%** | +2.9% |
| behind two | +6.0% | +5.6% | +6.5% | −0.5% |
| behind three | +2.2% | +1.3% | +1.9% | −4.4% |
| last | −4.4% | −4.9% | −3.7% | −10.6% |
| second second (E2), first | −7.5% | −5.5% | −5.2% | −11.3% |

**Across the three windows, second place:** at 15 blocks +18.0% (Sep 18-19), +11.2% (Sep 20-21), +4.9% (Sep 22-23); at
300 blocks **+13.7%, +10.9%, +26.9%**. The 300-block hold is the one whose worst window stays above +10%; 600 blocks
loses out of sample. Third and fourth place: +11.3% / +16.5% (Sep 18-19), +6.5% / +1.9% (Sep 20-21), +21.0% / +19.5%
(Sep 22-23) at 300 blocks: weaker and less stable, so the burst stays dense (the 3 ms grid is what puts us second
rather than fourth). Last in the block is negative on every window: the 25% guard stays. The second-second seat and
E1+3 are negative on two windows of three: no shortcut around the seat block.

**The rule, as it will be run:** the existing seat (E1, the burst of 35 at 3 ms, the relay, the shooters, the 25%
guard), plus engine 6.1's `ATTACK_MIN=2` (fire only when two or more relays or direct senders are already firing at the
curve when the burst is built), `HOLD_BLOCKS=300`, the measured gas model in the engine's own cost gate, and
`KILL_USD=15` on the $22.50 the box holds ($13.40 in the relay as the stake, $7 of shooter gas for about 25 bursts, $2 in
the wallet). Expected at $13 from the three windows, with our real landing mix (behind one two thirds of the time, behind
two or three otherwise) and a fill on about half the bursts: roughly +9% (Sep 20-21) to +24% (Sep 22-23) a fill before
gas, $0.30 to $1.20 a burst after it, of the order of $10-40 a day at 25-65 bursts; positive on every window, small at
this stake, and the stake is the setting.

**What the paper day tests** is the one assumption the chain cannot: that the engine sees two attackers on the feed by
the time the burst is built (the chain counts by block 5 of the creation second, about 0.4 s before the tick; the burst
leaves about 130 ms before the seat's predicted arrival). `paper_day.py` scores every launch the engine would have
fired at from the chain, at the positions we can get, held 300 blocks, after gas, and every launch the gate refused.
Go: second place at or above +10% over at least 40 gated launches with the refused set negative. Then live at $13 with
the kill line, the fills reconciled daily with `live_vs_table.py` (which must keep reading 0.0% in its model column).

**The same window priced a second way** (`hold_grid.py` on all 189, joined with the gate: `gate_hold_eval_oos_sep2021.txt`):
at $13 a burst after $0.33 of gas, second place on the 65 gated launches is **+$0.87 a burst at 15 blocks (SE $0.40, none
dead) and +$0.84 at 300 blocks (SE $0.68, 6% dead)**; on the 124 the gate skips, −$0.63 and −$0.30. Across the three
windows at 300 blocks the burst is worth +$1.65, +$0.84, +$3.43; at 15 blocks +$2.25, +$0.87, +$0.32. The long hold's
worst window is the better one and its mean is higher, at the price of a fatter tail (6-10% of fills below −40%
against 0-3%). The gate is worth about $1.20 a burst on every window; the hold is worth the difference between a
regime where the crowd comes in 1.5 s and one where it comes in 30 s, and the last two windows say 30 s.

**The first gated launch of the paper day (Sep 23 11:55 UTC, curve 0xac4d55df…)** was refused with 0 attackers at the
build (build lead 37 ms). On the chain: nothing fired at the curve until creation-second block +5 (one fleet, relay
0xa95fe1ca…), a second sender only in the seat block; the seat at second place would have returned −7.2%. The engine
builds about 130 ms before the tick, so its count runs about two blocks behind the tables' block-5 count. Re-running the
gate at block 3, what the engine can see, on the three windows (second place, 300 blocks, $13 after gas): 2+ attackers
by block 3 fires 23 / 41 / 44 launches a window at **+19.4% / +13.3% / +30.4%** ($2.19 / $1.40 / $3.63 a burst), against
+13.2% / +9.0% / +25.1% for the block-5 gate; the launches it skips are −1.0% / +0.5% / −1.2%. The fleets that fire
early are the stronger signal; the engine's lag makes the gate stricter and better. ATTACK_MIN=2 stands.

### 24.32 The paper day: the signal was there, the engine looked too early (Sep 23)

Engine 6.1 ran in dry run from 10:50 UTC with ATTACK_MIN=2, HOLD_BLOCKS=300, KILL_USD=15. By 20:10, 16 launches had
reached the gate and all were refused: the engine saw 0 attackers on 12 and 1 on 4. Scored from the chain at second place
over 300 blocks, all 16 would have lost (−3% to −72%, mean −15%): every refusal was right. On seven of the eight checked
block by block the engine's count equalled the chain's at the moment it counted (one over-count by one, cause pending
the address logging). But the chain, scored the way the three windows were (`e1_multi.py` on the day, then the crowd
signal: 58 qualifying launches 10:22-20:20), says the signal was present:

| attackers by block 5 | launches | first seat, 15 blocks |
|---|---|---|
| 0 | 27 | −8.6% |
| 1 | 6 | −0.1% |
| 2-3 | 12 | +12.9% |
| 4-6 | 6 | +12.9% |
| 7+ | 7 | +36.5% |

The fleets that day fired late in the creation second (blocks 4-6) and in the seat block itself, with dense bursts (60-82
shots from `0x460b1f81…` and `0x5b8e11e3…` in one block). The engine counts when it builds the burst, about 300 ms before
the tick; the feed has delivered blocks produced about 500 ms before that moment, so it sees roughly block k−5 of a
k-block creation second. By that view the gate passes 3% of launches on every window (2 of 58 that day, 4-7 a window
before); by block k−2, the view at the shot scheduled for the tick, it passes 24% at the same return:

| count taken at | today (58) | Sep 22-23 (175) | Sep 20-21 (189) | Sep 18-19 (141) |
|---|---|---|---|---|
| block 5 (the tables) | 25 fire, +19.5% first | 60, +13.4% | 65, +18.9% | 34, +27.4% |
| k−2 | 14, +18.0% | 21, +23.0% | 29, +23.9% | 14, +35.3% |
| k−3 | 7, +17.4% | 14, +26.2% | 19, +25.3% | 11, +40.3% |
| k−5 (engine 6.1) | 2, +29.2% | 7, +20.3% | 5, +76.0% | 4, +21.5% |

Second place, 300 blocks, at the k−2 view, $13 after gas: **+23.0% (Sep 18-19, 14 fires, $37 a day), +18.0% (Sep 20-21,
29 fires, $39 a day), +30.0% (Sep 22-23, 21 fires, $60 a day)**; at 15 blocks +23.1% / +13.7% / +9.2%.

**Engine 6.2 moves the gate into the burst.** The shots before the tick land in the tax second and revert; only the first
shot after the tick fills. So the gate need not be decided at the build: the sender asks it before every shot and sends
a shot only once ATTACK_MIN snipers are visible; if the gate is still shut at the shot scheduled for the predicted tick
(plus GATE_LATE_MS, default 0) no later shot is sent, so a burst that never opens leaves nothing on the chain and pays no
gas. Skipped shots are (None, None) in the sender's result, never counted against a shooter's nonce
(`restore_shooter_nonces`), and logged as `gated` with the shot the gate opened at; the decision carries
`attackers_at_build`, `attackers_at_open`, `gated_shots` and the attackers' addresses. The dry run simulates the same
rule, so the paper day measures what the live sender would do. The deployed send step must be the 6.2 copy
(`deploy/send_step.py`); the engine refuses to start with ATTACK_MIN on an older one. `tests/test_gated_burst.py`.

**The other leak.** The tables' population that day was 58 launches; 16 reached the attackers gate. The engine's own
filters (the bundle visible on the feed in time, creator repeats, the resolve limit, the slot model's confidence) removed
42, and that loss has never been priced against the tables. It is the next thing to measure from the engine's skip log.

**The review panel (night of Sep 23, `data/derived/audits_sep23/engine_62_panel.md`).** Five reviewers with distinct
lenses over the 6.1+6.2 change, three refuters per finding: 19 confirmed. The one that mattered: in dry run with shooters
configured the shooters' nonce map is never filled (only the live path reads it), so with 6.2 every eligible launch
crashed at the burst's build before the gate was simulated; 6.1 had never reached that line because its gate refused
first. Fixed (`.get(a, 0)`, a regression test that greps for it). Also fixed from the panel: `attackers()` no longer
counts the launch's own token when the approve came before the token was learned; a burst with the gate on needs
shooters (a wallet-nonce burst would gap) and the engine refuses to start otherwise; `burst_dropped` counts only shots
that were sent; a live burst whose sent shots all came back without a hash opens no position; `paper_day.py` reads
the 6.2 fields, defaults its window to the first start of the day rather than the last, prints the window, and takes a
bare date; the runbook's env check uses sudo.

### 24.33 Is the engine doing what the tables priced? Two mismatches, measured (Sep 24)

The night's one fire lost 20% and the question was whether engine 6.2 fires on the launches the tables priced. Checked
on the chain, launch by launch, then on every shot aimed at the 563 launches of the four windows, pulled raw
(`src/analysis/crowd_raw.py`, `data/derived/live_vs_table/crowd_raw_*.json.gz`: per creation-second block, every
transaction to the curve or naming it, with sender, target, and the named-wallet flags) so that every counting rule is
scored on one pull with the same returns (`hold_grid`: second place, 300 blocks, the $15 model). `crowd_rules.py`
prints the tables below (`crowd_rules.txt`).

**The night's three decisions against the chain.** Fleets (the engine's unit, see below) cumulative by block of the
creation second, the tables' rule, the engine:

| launch | blocks in the second | fleets by block | tables' rule (2+ by block k−2) | engine 6.2 |
|---|---|---|---|---|
| Sep 23 23:23 `0x7f4588cb` | 7 | 0 0 0 0 0 3 4 (seat block 6) | 0 by block 4: refuse | fired: 0 at the build, opened at shot 4 with 3 |
| Sep 23 23:47 `0x1a03dc87` | 4 | 0 0 1 1 (seat 3) | 0: refuse | refused: 1 at the tick's shot |
| Sep 24 04:52 `0xb88cdecd` | 5 | 0 0 0 0 0 (seat 2) | 0: refuse | refused: 0 |

The fire is a launch the tables' rule refuses: the crowd arrived in block 5 of 7, one block after the index the tables
priced, and the engine saw that block before the shot at the tick. Two of eight refusals of the Sep 23 day (6.1, the
count at the build) also disagree with the tables' count: `0xacbc7874` (14:19), engine 1, tables 51; `0xf5737a75`,
engine 1, tables 0.

**Mismatch 1: the unit.** The tables (`crowd_signal.py`) count distinct shooter *wallets* aimed at the curve. The engine
(`note_attack`) counts *fleets*: distinct relay targets plus direct senders, so a fleet behind one relay counts once.
`0xacbc7874`: one relay, `0x5b8e11e3…`, fired 73, 82, 76 and 87 shots from 51 wallets in blocks 3-6 of the creation
second: 51 for the tables, 1 for the engine. (`0xf5737a75`: the engine's 1 was the token's approve target, recorded
before the token was learned, fixed at `6f89765`.) The tables' "2+ attackers" is nearly "any fleet with two shooters";
the engine's "2+" is two separate snipers. Different rules, priced as one.

**Mismatch 2: the view.** The tables' "block k−2" is a block index. The engine sees time: the blocks the feed has
delivered (about 200 ms behind) by the shot that fills. Blocks on this chain are produced on demand, so the fleets'
own shots create blocks late in the second: on `0x1332d47c` (10 blocks) the engine's build had seen at most block 2;
on `0xacbc7874` (7 blocks) block 3 or 4. A block index is not a time, and the engine's view cannot be reconstructed from
block numbers; it can only be measured, which 6.3 now does: every decision logs `blk0`, `feed_block_at_build`,
`feed_block_at_open` (the feed's block when the gate first opened) and `feed_block_after_burst`, plus both counts
(`fleets_at_open`, `wallets_at_open`); `paper_day.py` prints them against the chain's k.

**The engine's rule priced at every view it could have.** Fleets ≥ 2 at the gate's opening, the view modelled as the
blocks minted before a fraction of the creation second with the blocks evenly spaced (0.76 = the shot at the tick with a
200 ms lag; 1.0 = the whole second). Second place, 300 blocks; $/burst and $/day at $13 after $0.33 gas:

| view | Sep 18-19 (23 h) | Sep 20-21 (35 h) | Sep 22-23 (29 h) | Sep 23 day (9 h) | pooled |
|---|---|---|---|---|---|
| 0.60 | 14, +21.8%, $36/d | 32, +23.8%, $61/d | 27, +8.3%, $16/d | 9, +22.2%, $63/d | 82, +18.2%, 57% win, $2.03, $42/d |
| 0.71 | 17, +20.2%, $41/d | 37, +21.9%, $64/d | 31, +10.4%, $26/d | 11, +15.9%, $52/d | 96, +17.2%, 57%, $1.91, $46/d |
| 0.76 | 21, +15.3%, $36/d | 46, +18.7%, $67/d | 42, +12.2%, $43/d | 14, +6.4%, $19/d | 123, +14.5%, 57%, $1.56, $48/d |
| 0.86 | 34, +4.7%, $10/d | 66, +15.3%, $76/d | 62, +10.8%, $54/d | 20, +4.9%, $17/d | 182, +10.6%, 55%, $1.05, $48/d |
| 1.0 | 64, +2.4%, −$1/d | 113, +6.5%, $40/d | 105, +12.1%, $107/d | 31, +5.8%, $36/d | 313, +7.5%, 49%, $0.64, $50/d |
| tables as priced (wallets ≥ 2 by block k−2) | 12, +27.8%, $41/d | 27, +15.8%, $32/d | 21, +30.0%, $61/d | 14, +5.5%, $15/d | 74, +19.8%, 57%, $2.25, $42/d |

By exact block: fleets ≥ 2 by block k−3 +17.9% (84 fires), k−2 +14.6% (114), k−1 +8.8% (215), k−0 +7.5% (313).
By the block where the second fleet first showed: k−3 to k−5 +21% to +28%; k−2 +6%; k−1 and k−0 +2% to +5%. The night's
fire was a k−1 arrival. The later the crowd is seen, the thinner the fire: the dollars a day hold up (more fires at a
lower return), the win rate and the return per fire fall, and at the latest views Sep 18-19 is negative after gas.

**Alternatives on the same pull, not adopted.** Wallets ≥ 2 at the opening (the tables' unit at the engine's time):
+15.0% pooled, but +6.7% on Sep 20-21 and −$8/d on the day. Fleets ≥ 2 at the opening and ≥ 1 at the build: +16.3%,
positive on all four windows, but the build's view is the least measurable of all. Wallets ≥ 2 and fleets ≥ 2: +20.2%
pooled, +8.1% on Sep 20-21. Higher wallet thresholds (5, 10) lose the day window. The settings stay `ATTACK_UNIT=fleets`,
`ATTACK_MIN=2`, `ATTACK_BUILD_MIN=0` (6.3 makes the others settable); they are re-scored at the *measured* view after a
paper day of 6.3, not at a modelled one.

**What this changes.** The expectation for the paper day and for live is the engine's rule at the tick's shot: about
**+11% to +15% a fire, 55-58% wins, $1.0-1.6 a burst, about $48 a day at $13** (views 0.76-0.86), not the +23% to
+30% of 24.32, which priced a block index the engine does not see. The go line of runbook 5l (behind one at or above
+10% mean over the gated launches with the refused set negative) stands; the measured view (`paper_day.py`'s "feed at
the open block j; k=…") is read alongside it.

**Addendum, the first measured view and the third mismatch (Sep 24 10:23).** The first 6.3 decision: `0xfa1eea51`, 8 blocks
in the creation second, the feed had shown block 4 at the build (the model's 0.71 view says block 4), one fleet of 51
wallets by the tick's shot: the fleets gate refused (1 < 2), the wallets unit would have fired, second place lost 20%.
The pre-gate histogram of the same day answered the leak of 24.32: 10 of the 12 launches that passed the tables' filters
were refused by the **safety switch** ("rolling −0.13 over 15 < −0.10"), which scores every eligible launch, fired or
refused, at the first seat and the HOLD_S hold: the ungated old rule, whose population the crowd gate exists to refuse. The
tables never had a switch. Replayed on the four windows with the tables' own first-seat scores, the switch is on 93-97% of
the time there, yet the fires it blocks are the best ones: 12 of 123 blocked, averaging +50% (h300 metric; h15: 1 of 123,
+47%). It is set off (`SWITCH=-9`, runbook 5n); KILL_USD and DAILY_STOP remain the capital protection. Three mismatches,
then: the unit, the view, the switch; the engine now runs the priced rule and nothing else in front of it.

**Addendum 2, the seam audit (Sep 24 12:00).** Three checks on "is the number the engine gates on the number the tables
priced, at the same moment": a mechanical replay, and two independent readers, one on the moment and the fill, one on the
filters in front of the gate.

*The replay* (`tests/test_seam_replay.py`): every transaction of the raw pull fed through the engine's own `note_attack`,
block by block, against the tables' count. 4 of 563 launches differed, all Sep 18-19, all our own wallet firing through two
retired relay addresses (the tables skip our sender, the engine only knew its current relay): 6.4 skips its own sender behind
any relay; 0 differences.

*The moment reader found the largest error in the tables, not the engine.* `crowd_raw.py` looked the launch's token up with
the Buy event's topic instead of the factory's address, so the token was unknown on all 563 launches and the exclusion of the
token's approvals never fired: the bundle wallets' `approve(curve)` calls (1,178 rows in the creation seconds) name the curve
in their calldata and were counted as a fleet. The engine excludes the token (`note_attack`, `attack_fleets`). The replay
missed it because both sides read the same wrong field. Tokens refilled from the factory log; the engine's rule re-priced:

| fleets ≥ 2 at | fires (96 h) | mean | win | $/burst at $13 | $/day | SE | dead |
|---|---|---|---|---|---|---|---|
| the tick's shot (0.76 view) | 83 | +22.1% | 63% | $2.54 | $53 | 5.9% | 7% |
| block k−1 | 147 | +19.5% | 60% | $2.20 | $81 | 5.8% | 12% |
| block k−2 | 73 | +26.7% | 67% | $3.14 | $57 | 6.9% | 8% |
| block k−3 | 52 | +30.1% | 65% | $3.59 | $47 | | |
| the whole second | 251 | +13.3% | 53% | $1.39 | $87 | | |

Every row is positive on all four windows (Sep 23 day +12.5% to +24.8%); the 40 fires the token alone had added averaged
−1.2%. The tables of 24.33 above (+14.5% at the tick's shot) carried the token; the engine's own number is +19% to +30% a
fire, 3.4 to 3.9 standard errors above zero pooled, median +11% to +21%.

*The moment reader's other findings, in order of effect:*
1. **The gate's deadline is the predicted tick, the fill depends on the actual one.** With the 80 ms lead the gate may open
   until t_first + 80 ms; the race readout puts the actual tick at about t_first + 36 ms (fills at shots 1-18, median 12).
   A gate that opens in that 45 ms window fills on its opening shot, behind the crowd's wave, not at the priced second
   place. 6.4 adds GATE_CLOSE_MS (the deadline as ms after the first shot); 36 aligns it with the median actual tick, at the
   cost of the fires whose second fleet shows between +36 and +80 ms (the late arrivals, +5% in the tables). Live, the check
   is `gate_opened_at_shot` against the landing's shot index.
2. **The burst's minOut guard is not in the price.** minOut is set at the build from the feed's curve state; the bundle's
   remaining creation-second buys can move the price past 25% (9 of 123 priced fires, 7 of the 83 token-free ones, among
   them +254%, +48%, +28%); scoring those at zero takes +22.1% to +19.3%. `paper_day.py` now applies the guard from the
   decision's `min_out_tokens` and prints "GUARD: no fill, gas only".
3. **The engine is blind until the curve is registered.** `note_attack` counts only watched curves; the watch starts after
   the bundle wait and the resolve (up to 1.5 s); shots before it are never replayed. Blind to blocks 0-2 costs 4 of 83
   fires, blind to 0-3 costs 46. 6.4 logs the feed's position at registration (`seq_watch`), `paper_day` prints it.
4. **"At the open" was read after the burst.** The 6.3 counts labelled at the open were taken when the burst ended; 6.4
   snapshots block, chain block and both counts at every ask of the gate: the opening's snapshot decides a fire, the last
   ask's a refusal, both logged (`seq_at_open`, `fleets_at_open`, `gate_opened`), plus the after-burst values apart.
5. **k is not the second's length.** `k` counts the blocks after the creation block; the creation lands anywhere inside its
   second, so the fraction view is a label, not a clock. The exact-block rows are the reference; `feed_seq` (the L2 block
   number) is now logged at the build, the open and after the burst, so offsets are the chain's.
6. The feed counter skips non-L2 messages and counts backlog replays (±1 block, rare): `feed_seq` supersedes it. Live
   signing of 35 shots (about 50 ms) competes with the feed thread: the paper view is slightly fresher than live. `paper_day`
   joins the live `sent_burst` for the opening shot and names the launches it cannot score.

Verified identical: the gate loop in the sender and the dry run; the decision as a single-view rule (the count only rises);
the exclusions (named sender, creator, helper, direct rule); `paper_day`'s positions and hold against `hold_grid`; the 6.3
fields' fallbacks; `blk0`'s zero against the chain's b0.

**Addendum 3, the population reader (Sep 24 12:30).** Thirty-three conditions stand between a creation and the burst's gate;
the tables' population (`e1_multi.one()`: selector f85f8e41, native quote, three named wallets, 100-200 bps, first buy at b0,
0.3 ETH of exempt bundle over the creation second, both seat seconds within 24 blocks) applies six of them. Engine-only and
binding in the paper configuration, with the fires they take from the 123 of the tick's-shot view (token-included pricing):
GAS_MAX_SHARE at 5% of $13 (all-or-nothing on the base fee: up to 28% of launches at Sep 18-19 fee levels, 0-3% since);
MIN_CREATOR_SUPPLY 1% (15 fires, +3.5%); TRADE_HOURS 12-05 (12 fires, +17.7%); the bundle's visibility on the feed and the
aim's readiness (8 fires, +10.6%, unscored, plus every launch for 30 s after a feed reconnect); the creator-repeat skip (5
fires, −36%); one position at a time (2 fires); the bundle fold closing on a stranger's early direct shot (up to 19 fires,
−5%); the nonce nulled for 3 s after a released reservation (1-4% of fires); the demand floor's arming after a stale restart
(an hour or two of refusals). Together the priced filters cut 36 of 123 fires averaging +3.9% and leave 87 at +18.9%: the
dollars a day are unchanged, the return per fire higher. The reverse seam: with the tier gates at 0 the engine fires on
1%-tier and 4%+ launches never priced; with the ohio template's BUNDLE_MAX_ETH=1.2 it would drop 30 fires averaging +26%.
SWITCH=−9 is a real off (roi ≥ −1.38 by construction). Runbook 5o sets every one of these explicitly. Live: KILL_USD=15 on
$15.40 of capital stops after the first loss over $0.40.

**Addendum 4, the first day of engine 6.4 against the prediction (Sep 24 12:55-21:45 UTC).** The prediction was committed
before the box was read (`prediction_sep24_paper.txt`: 51 qualifying launches; the rule at k−1 17 fires +19.4%, at the
tick's shot 11 fires +8.0%, at k−2 9 fires +1.8%; the 34 refused −2.8%). The engine's reading: 37 of the 51 reached the
gate, 8 fired, 29 refused; 14 never reached it (the pre-gate filters; among them three k−1 fires at +102%, +44%, +4%,
and three losers).

*Is the engine on the rule?* Every one of the 8 fires is in the predicted k−1 set, and every refusal agrees with the count the
engine logged at the gate's close, with one exception: `0xc63ab843` (17:58), 2 fleets by block 3 on the chain, the engine
saw 1 at its close (block 5): it registered the curve at block 2 and the fleet that fired only in block 2 was never counted
(the blind window of audit item 3, measured for the first time; a loser, −8.6%). Registration was at block 1 on 30 of the
37 launches, so the window is usually blocks 0-1.

*The measured view.* At the gate's opening or close the feed's last fully indexed block was k−2 on most launches, with the
next block partly indexed (`0xf61ae3fa`: block 5 recorded, 2 fleets counted, the chain's block 5 has 1 and block 6 has 6;
the count runs ahead of the block number while a message is being indexed). So the engine's view is k−2 fully, k−1 in
part: the rows it can reach are the tick's-shot and k−2 rows of the tables (+22.1% / +26.7% over the four windows), not
the k−1 row; a later close would fill behind the wave.

*The day's numbers.* Fired: 8, behind one +13.7% mean, median −1.4%, 38% wins, $1.46 a burst, about +$12 in nine hours;
before the minOut guard the same eight average +7.1% (the guard, real in live, turned −41% and −17% into gas only, and
refused a further two at the later positions). Refused: 29, mean +5.3%, median −12.7%, 28% wins: the day's largest
winners had 0 or 1 fleet before the tick (+191% with 1 at k−2 and 3 at k−1, +120% with 0, +51%, +45%, +41%, +39%, +36%),
the opposite of the four windows' 0-1 fleet mean of −1% to −9%. At the engine's real view the prediction for the day was
+1.8% to +8.0%; the engine's +13.7% sits above it because of the guard.

*Against the go line* (5l: behind one ≥ +10% over 15+ fired launches, the refused set ≤ 0): not met (8 fires; the refused
mean is positive on this day), not failed (the fired set is positive). The paper run continues; 15 fires need about two
days at this rate. The 14 launches that never reached the gate are the next reading (`skip`/`gates` reasons on the box).

*The 14 that never reached the gate* (from the box's `skip` events): 6 "no confident boundary estimate to aim at" (five of
them creations landing in the last one or two blocks of their second, k ≤ 2, where the bundle wait leaves no time to aim;
the k−2 row of the tables already excludes those by construction, since block k−2 is the creation block or earlier; the
sixth, `0xcff204f6` +44%, k=6, an aim gap of the estimator), 7 "creator buy < 1% of supply" (MIN_CREATOR_SUPPLY, kept on
purpose: five losers, one flat, one +102%, mean +5%, −11% without the winner), 1 "bundle 0 < 3" (the feed's fold saw no
bundle where the chain had one: the fold's early close, audit row 11; +4%). Nothing broken; the aim skip is a property of
the burst, the creator filter a choice, the fold race a known one-in-fifty.

**Addendum 5, the night of Sep 24-25 against its prediction (21:45-05:21 UTC).** Prediction (`prediction_sep25night.txt`,
committed first): 8 qualifying launches; at the engine's view one fire, `0x9f834b70` 00:33, +169%; at k−1 three; the five
refused +27% with two 0-fleet winners (+80%, +134%). The reading: one fire, `0x9f834b70`, opened at shot 0 with 2 fleets, the
feed's block 2 of k=4 (the chain's count at block 2 is 2: exact), behind one +169.1%, +$21.66; three refused (0, 0 and 0
fleets at the close; the third, `0x2c296eee`, had 2 fleets by block 4 = k−1, the engine's close was block 3: consistent with
the k−2 view); four never reached the gate (one un-aimable k=1 creation, the +134% one, and the pre-gate filters).
Prediction and reading agree launch by launch.

Running tally of engine 6.4 with the aligned settings (18 h, Sep 24 12:55 to Sep 25 05:21): 9 fires, behind one +31.0% mean,
44% wins, about +$33 at $13; 32 refused, +7.5% mean, median about −12%. The refused set's mean is positive because the five
largest winners of the period (+191%, +134%, +120%, +85%, +80%) had 0 or 1 fleet before the tick, two of them 0 at every
view; on the four windows the 0-1 fleet launches averaged −1% to −9%. Recorded as a fact against the rule, not acted on:
the go line (15+ fires, refused ≤ 0) is not met and not failed; the day stretch of Sep 25 decides it.

**Addendum 6, the morning of Sep 25 against its prediction (05:30-12:11 UTC).** Prediction: 4 qualifying launches, 0-1 fires
(the 11:43 one, borderline at block 2 of 3), the rest refused near −12%. Reading: one fire, `0x03e861dc` 09:23, opened at
shot 5 with 2 fleets at the feed's block 6 of 8; the chain has 1 fleet by block 6 and 2 by block 7, so the count was block
7's while block 6 was still the last fully indexed one (the partial-index effect of addendum 4, now seen twice): the fire
was in the predicted k−1 set (−20.7%, −$3.02). The 11:43 launch was refused with 1 fleet at block 1 of 3 (block 2 partly
in), +4.3% missed; two 0-fleet refusals (−12%, −64%; the second landed after the prediction's cut). One never reached the
gate. Prediction and reading agree. The engine's effective view is "inside block k−1": fully k−2, partly k−1, on every
launch measured so far.

Running tally (Sep 24 12:55 to Sep 25 12:11, 23 h): 10 fires, 4 wins, about +$30 at $13; 35 refused, mean about +5%,
median about −12%.

**Addendum 7, the afternoon of Sep 25 against its prediction (12:15-18:34 UTC).** Prediction: 22 qualifying launches, one
sure fire at the engine's view (`0xd43ed726` 16:24, 2 fleets from block 2, +9.2%), three k−1 borderlines (+12.6%, +50.0%,
−0.5%), 18 refused at +4.3%. Reading: 0 fires, 10 refused, 12 never reached the gate, the sure fire among them. The three
borderlines were refused with the count of block k−2 (1, 0, 1 at the close; the chain's 2, 2, 3 sit in block k−1), so
the engine's view this afternoon was k−2 with no partial k−1 on any of them. Every decision agrees with the rule; the
refused set: +6.9% mean, +6.0% median, 5 of 10 up (+50%, +24%, +17%, +13%, +50%).

Running tally (Sep 24 12:55 to Sep 25 18:34, 30 h): 10 fires, +31% mean, 4 wins, about +$30 at $13; 45 refused, mean about
+5%, median about −8%; 8 fires a day against the k−2 row's 18 before the pre-gate filters. The 15-fire line is not reached
and the refused set is not at or below zero: the go conditions of runbook 5l are not met after 30 hours. The 12 launches
that never reached the gate today (of 22) are the next reading.

**Addendum 8, the 12 that never reached the gate on Sep 25 afternoon.** 6 "no confident boundary estimate" (five creations
in the last one or two blocks of their second, un-aimable by construction; one, `0x48a89f86` k=5 +5.6%, an estimator gap);
3 "creator buy < 1% of supply" (+110%, −6%, −6%; the filter kept its net: it also dropped −58% yesterday, but the +110% is
its cost); 1 creator repeat (−58%); and **2 "bundle 0 < 3"** where the chain has a full bundle: `0xd43ed726` (the sure
fire, +9.2%) and `0xba059c17`. Cause found: `curve_buys` returned the feed's direct buys before its helper calls, so at
registration a stranger's reverting shot at block 2 was folded before the helper's named buys at block 1 and closed the
bundle at zero. That is the population audit's row 11, and it hits exactly the launches with the earliest crowd, the ones
the tables pay most for. Engine 6.5 folds the replay in (block, arrival) order; `tests/test_bundle_order.py` pins it.
Three launches in two days carried it (`0x56e76663` on Sep 24 too).

**Addendum 9, the evening of Sep 25 against its prediction (19:30-22:22 UTC).** Prediction: 14 qualifying launches (plus
`0xf45fa520` 20:07, +67.9%, present in the first run of the window and silently dropped by the launch builder's second
run); one sure fire (`0xe41e16e1` 20:47, −10.5%), three k−1 borderlines (−11.9%, −1.1%, +67.9%), 11 refused at −12.7%.
Reading: two fires, the sure one (−10%) and the 20:05 borderline (3 fleets at block 2 of 3, the engine's open at block 2:
−12%); eight refusals, all with 0-1 fleets at the close (the 21:31 borderline's four fleets sat in block k−1), mean −25.6%
with three dead; five never reached the gate, among them the two winners of the window (+81% with 0 fleets, +68% with 2
in block k−1). Prediction and reading agree; the refused set is negative for the first window, as the tables say.

Running tally (Sep 24 12:55 to Sep 25 22:22, 33.5 h): 13 fires, 4 wins, about +$24 at $13; 54 refused, mean about 0,
median about −10%. The go line: 13 of 15 fires, the refused mean at zero; one more busy stretch decides it.

### 24.34 Can the rule be improved? Three independent searches, one protocol (Sep 25-26)

The question, asked after five days of predictions against readings: is any change to the rule more profitable, robustly,
on everything measured? Three searchers ran the identical brief (`data/derived/improve_search/BRIEF.md`) independently:
two Opus agents (A, B) and the session itself (C); each wrote its own scripts (`data/derived/improve_search/{A,B,C}/`),
and each other's scripts were re-run as the cross-check. The protocol: fit on the four backtest windows (96 h, 563
launches), validate on the five paper windows (34 h, 99 launches, truly out of sample since the rule was fixed on Sep 24
before them); executable views only (block k−2 exact; k−1 reported as a borderline, never a headline); a candidate passes
only if it beats the baseline's $/day on the fit set, is positive on each fit window, beats or matches the baseline on the
validation set, keeps the win and dead rates within 10 and 5 points, and fires at least 30 times on the fit set.

**All three reproduce the same baseline to the cent** (fleets ≥ 2 at k−2, second place, 300 blocks, $13 after $0.33 gas):
fit 73 fires, +26.7%, 67% wins, 8% dead, $3.14 a burst, $57.3 a day; validation 12 fires, +15.3%, $19.92 total. A's fleet
counts match `crowd_rules.py` on all 563 launches; A's and B's tape pulls reproduce `hold_grid`'s returns exactly.

**Verdict, unanimous: nothing is proven; keep the rule as it is.** Variants tried: C 47, A 383 (plus 4,800 random-feature
variants as a null test), B 3,420. Every variant that clears the five criteria as written fails the brief's own caveat:
- A's 5 and B's 9 "passes" are all OR-branches on 1-fleet launches split by bundle size, k, or the fleet's arrival block, and
  every one rests on a single launch: `0x39501200` (+619%, Sep 22-23) on the fit set, `0x057d2437` (+191%) or `0x93d7d429`
  (+51%) on validation. Remove it and the pass flips. Both tails of the same feature (bundle < 0.45 ETH and bundle ≥ 1.0
  ETH) "pass", and the middle loses. A's null test: random features pass at 3.3%, the real ones at 2.7%. B's paired
  t-statistics of the per-launch gain over the baseline never exceed +1.06.
- C's two "passes" are not rule changes: the $100 stake column (size; and `hold_grid` folds later buyers by tokens, so it
  overstates large stakes: 24.29), and the k−1 view (147 fires, +19.5%, $81 a day fit; validation 30 fires, +22.5%, $78),
  which the feed cannot show in time: a later gate fills behind the crowd (24.33 addendum 2).

**By dimension, all three agree:** thresholds: fleets ≥ 1 $53/day (52% wins, 16% dead), ≥ 3 $21, ≥ 4 $2; wallets ≥ 2 $44;
fleets ≥ 2 at k−2 and ≥ 1 at k−3 $58 on fit but +6% on validation. Holds on the baseline gate: h15 $33, h60 $33, h150 $45,
h300 $57, h600 $41; tp50 $33; stop20 $51 (51% wins, 1% dead); tp50+stop20 $38. Hours: every exclusion lowers $/day (the old
12-05 window $56). Creator supply: ≥ 1% (the engine's setting) $56, ≥ 2% $37. No pre-tick feature separates the 0-1 fleet
winners of Sep 24-25: the twelve of them span the whole range of every feature (k 1-9, bundle 0.32-1.55 ETH, named 3-31,
both tiers, hours 2-22), two are un-aimable creations.

**One trade-off, not an improvement:** a −20% stop with a 600-block hold takes the dead fraction from 8% to 1% at the cost
of $/day ($51 against $57) and win rate (51%: many small stops); the stop is modelled as an instant exit at the crossing
trade, which the engine's single sell is not. Recorded for the owner's risk preference, not adopted.

**Found on the way and fixed:** `hold_grid.py`'s combined take-profit/stop column took the take-profit even when the stop
had hit first (48 of 563 fit launches, 9 baseline fires): now whichever hit first. The column is not used by the rule.

**Not testable with this data:** the real minOut guard per launch (needs the engine's `min_out_tokens`), the partial k−1 view
and the blind window (need more 6.4+ logs), exits outside the nine columns and other seat positions (need re-pulled tapes),
stakes above $13 (need the fixed-ETH model on every launch), creator supply as a branch (tapes for all 663 launches).

**Addendum 10, the night of Sep 25-26 against its prediction (22:25-08:02 UTC, engine 6.5).** Prediction: 17 qualifying
launches, one sure fire (`0x0a6c1259` 22:27, +25.8%), two k−1 borderlines (−10.0%, +18.4%), 14 refused at −0.1%. Reading: the
one fire, +25.8% (+$3.02), opened at shot 0 with 3 fleets; seven refusals, all with 0-1 fleets at the close (both
borderlines refused: their second fleet sat in block k−1), mean −31%, four dead; nine never reached the gate (three
creations in the last blocks of their second, the rest the pre-gate filters; among them the +96% one-fleet launch the
gate would have refused anyway). Prediction and reading agree; the engine reports 6.5.

Running tally (Sep 24 12:55 to Sep 26 08:02, 43 h): 14 fires, 5 wins, +21.5% mean, about +$27 at $13; 61 refused, mean
about −4%, median about −10%. The go line: 14 of 15 fires; the refused set below zero; the fired mean above +10%.

**Live, Sep 26 09:15 UTC.** After 43 hours of paper on the aligned settings (14 fires, +21.5% mean, about +$27 at $13, the
refused set below zero), the owner switched the engine to live at $13 with KILL_USD=10 on 0.008753 ETH ($23.48) of
capital ($13.98 in the relay, $7.34 of shooters' gas). The daily order stays: the prediction from the chain first, then the
reading, then every real fill against the model (runbook 5q).

