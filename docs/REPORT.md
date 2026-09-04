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
