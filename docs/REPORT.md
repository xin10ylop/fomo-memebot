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
