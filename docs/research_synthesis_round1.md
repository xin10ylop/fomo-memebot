# The Big Treasure — Synthesis of Six Research Threads (as of 2026-09-03)

## 0. Corrections to the premise (read first)

1. **Pons is now V2, not V1.** The "no bonding curve, Uniswap V3 pool from launch, 2-block protection" description only covers Pons V1 tokens launched Jul 13 – ~Aug 3. On-chain reads (Sep 4): V1 factory `0xA5aAb3F0…351feB` has `launchEnabled()=false`; V2 factory `0x7eD598Bc…1EC7e` is live with a constant-product curve (phantom quote 1.68 ETH, graduation 4.2 ETH, 1% curve fee), graduating into a locked full-range Uniswap **v4** pool with 0 LP fee + 1% hook fee (`hook 0xE5e70264…`). Launch protection is a time-based **snipe tax** (99% decaying to 0 over 3 s on-chain / 5 s in docs), with creator + up to 32 whitelisted wallets exempt. Aug 31 fees: V2 $4.89M vs V1 $508K. Sources: docs.ponsfamily.com/v2, github.com/ponsdotdev/ponsfamily, thedefiant.io (Sep 1). Any backtest must branch on V1 (V3 pool, 1% fee) vs V2 (curve phase, then v4 hook pool).
2. **The "dominant relayer 0xcaf681a6…5cb2" in Bitquery's report is Uniswap SwapRouter02** (address confirmed on developers.uniswap.org for chain 4663). It is not a fomo relayer; the social-signal thread's speculation that it identifies fomo flow is wrong. fomo flow must be tagged via resolved real wallets (fomoapi `/v2/users/{handle}`, fomoscan) or via fomo's ERC-4337 paymaster/bundler, which remains unidentified.
3. **fomo "copy trading" is manual push-alerts**, not auto-mirroring (fomo.family/answers/how-does-copy-trading-work). docs.onfomo.com (auto-copy, 0.5x-5x, TP/SL) is a different product (Hyperliquid perps). Follower flow arrives spread over seconds-to-minutes after the leader's fill.
4. **"36% of Robinhood Chain volume is fomo" is likely wrong.** Dune terminal data (Sep 2) puts fomo at $268M on a ~$1.6-1.9B day (~15%), with GMGN at $480M. fomo is the majority of small-ticket wallets (~64K DAA, ~$1.5K/address/day) but a minority of dollars; GMGN carries pro/bot flow (~$63K/address/day).

---

## 1. Ten most decision-relevant facts

| # | Fact | Why it matters | Sources |
|---|------|----------------|---------|
| 1 | **Leaderboard PnL is mark-to-market on illiquid bags.** Several top-10 handles have PnL/cumulative-volume ratios of 5x-400x (Natan_benish $5.24M PnL on $12.6K volume; frogmanhaha $3.68M on $21.9K; DumbCrayonEater $9.35M on $1.0M, 91% in one token). Critic MidCurveMortal: unipcs' impact-adjusted PnL ~25% of displayed. | Rank is not skill; re-score on realized, impact-adjusted PnL from resolved wallets. | local `data/raw/fomoapi/leaderboards/*.json`; kucoin.com/news/insight/FOMO/6a951dc6dd2c0d0007d5a0db; fomo ToS §9 |
| 2 | **Only ~6.16% of ~292K fomo wallets were realized-profitable over 90 days; 25 wallets >$10K** (DWF Ventures, Aug 28). Attributed to execution asymmetry and exit-liquidity loops. | Base rate for naive following is ~94% losers; strategy must be structurally different from "buy after the alert". | yellow.com; alexablockchain.com; cointribune.com (sample definition differs slightly; original DWF post not retrieved) |
| 3 | **App feed/push lags chain by ~15 s (vendor claim, >20 s sometimes); on-chain stream sees trades ~1-2 s after block.** Sequencer feed `wss://feed.mainnet.chain.robinhood.com` is public and leads RPC by 50-130 ms. | The only structural latency edge available to retail is entering before the ~15 s app wave, sourced from the free sequencer feed, not from the $499 fomoapi stream. | fomoapi.io/blog/onchain-stream-15-seconds-faster-than-fomo-feed; github.com/chainstacklabs/robinhood-chain-sequencer-feed |
| 4 | **Robinhood Chain ordering is strict FCFS at a single sequencer (AWS us-east-2), no priority fees, no mempool, no Timeboost.** Ohio 3 ms vs Sydney 200 ms (~2 blocks). Sandwich MEV is structurally impossible; Bitquery found negligible arb extraction (~$599K/13 days). | Latency to Ohio is the whole ordering game; a $20 VPS in us-east-2 beats every phone app and Telegram bot; "anti-MEV" is irrelevant. | docs.robinhood.com/chain; cryptotimes.io (Glassnode probes); bitquery.io/investigations/robinhood-chain-tokenized-stocks |
| 5 | **Round-trip fee floor on a Pons token: 1.99% direct RPC, 2.98% via fomo, 3.96% via GMGN/Maestro (1%/leg).** Plus own impact: $500 into $50K displayed liquidity ≈ 7-8% round trip; $5K into $50K ≈ 43%. Creator tax up to 10%/leg exists but ~0 in 10 of 11 sampled curves. Gas normally <$0.25 but spiked to ~$64/tx in the Sep 1-2 congestion. | Gross edge must exceed ~3-8% per round trip; sub-$100K pools are uninvestable above ~$1K clips; read `creatorTaxBps()` before every trade. | on-chain reads (hookFeeBps=100, curveFeeBps=100); datawallet.com; bitrue.com (gas spike) |
| 6 | **Graduation base rate ~1-1.7%; 84% of launches never trade after day one; median token has 13 trades and 4 wallets; 73% of pump.fun graduates fall >60% within 20 min of migration.** | Curve-phase entries are lottery tickets; the tradeable universe is the ~150-300 graduates/day and the survivors at 48 h. | own eth_getLogs (636 launches/11 grads in 35 min); bitquery.io; arxiv 2602.13480 (MemeTrans); arxiv 2602.14860 |
| 7 | **Insiders own the first seconds.** Pons V2 whitelists up to 32 tax-exempt wallets; bundler tools exist (smithii Pons Bundler, pons-sniper); PIPEDOG ~50% held by one entity via ~80 fresh wallets, ARROW 80% in ~200 wallets; pump.fun deployer-funded same-block snipes were 87% profitable with 85% exiting in <5 min. | Do not compete for block 0; instead detect bundled supply and avoid/fade it. | docs.ponsfamily.com/v2; blog.bubblemaps.io; Pine Analytics via bitget.com; github.com/slightlyuseless/pons-sniper |
| 8 | **The biggest realized wins on Robinhood Chain were catalyst/venue plays, not sniping:** PONS ~181x on fee-buyback reflexivity (ogle $5K→$5.7M), CASHCAT +100-120% on Robinhood brokerage listing with pre-listing fresh-wallet accumulation flagged, AI (NVDA-paired via LONG) +70%/24h on Aster perp listing. | A catalyst-anticipation book on liquid graduates (top-20 by liquidity) is retail-executable and repeatable; the July "chain launch" regime is not. | finbold.com; news.bitcoin.com; blog.bubblemaps.io; theblock.co (Aug 31) |
| 9 | **Bot pollution of activity signals:** one address submitted 25% of all trades, top-5 70%; bot wallets 1.7% of addresses but 51% of volume; coordinated cohorts inflate first-30-min buyer counts (+16%) with zero measurable inflow lift. | Use net quote-asset inflow from uniquely-funded wallets, never trade counts or buyer counts. | bitquery.io; arxiv 2607.02795 |
| 10 | **Regime risk is imminent:** Robinhood Wallet gas subsidy ends ~Sep 29; Visa/Chase/NY AG reviewing MCC-5815 card-funded memecoin buys (Crossmint ~7% of fomo inflows); fee revenue went $56K→$4.45M/day in 10 days (blow-off); fomo had ~10 outage incidents in August. | Every backtest on Jul-Sep data is in-sample to a blow-off; require robustness to a 3-5x activity drop and never depend on card-funded flow. | kucoin.com (subsidy); theblock.co (Sep 1 card story); cryptonomist.ch; trustpilot |

---

## 2. Ranked strategy hypotheses

Ranking criteria: expected edge after ~3-5% round-trip cost, persistence, retail-executability (single VPS, $500-$5K clips, public data), and testability with our data.

### H1. Front-run the follower wave (sequencer-feed KOL detector, exit into the app-lag crowd) — rank 1
- **Mechanism.** Resolve real wallets of high-follower fomo traders (200K-500K followers: unipcs, PoorGoat_, change, ether_monk, 0xAvast, DumbCrayonEater, frankdegods). Decode their buys from the public sequencer feed (block N); submit our buy at N+1/N+2 from us-east-2; sell into the manual-copier wave that arrives ~15-90 s later once the push fires. Target the crowd's own heuristic band (Odaily: skip if already +10-20%), i.e. exit at +8-15% or on time-stop.
- **Why it persists.** Structural: FCFS ordering + fomo's server-side feed lag + manual human copying. The lag cannot be arbitraged away by app users; fomo has no incentive to make the feed faster than its own indexer. Referral/Trader Rewards programs pay KOLs to broadcast, sustaining the wave.
- **Test.** Event study on chain 4663 logs: for each leader buy (resolved wallet, Jul 15-Sep 3), measure pool price path and net quote inflow at 0-2 s, 2-15 s, 15-60 s, 1-5 min, 5-30 min; bucket by follower count, usdValue, pool quote-side reserve, whether a `LARGE_BUY`/push appeared in `/v2/notifications`. Simulate entry at N+2 with our size and 1%+impact, exit rules at +X% or T seconds. Cross-check timing with fomoapi `/ws/alerts` `seenAt` vs `blockTs`. Solana analogue via Helius on the "Fomo Co-signer" `AgmLJBM…zN51`.
- **Falsified if.** Median post-buy excess return at 60 s < round-trip cost for every bucket; leader sells arrive within the same window >50% of the time (we become exit liquidity for the KOL); wave is only detectable for leaders whose buys already dwarf pool depth (no room for us).
- **Confidence.** Medium: mechanism is asserted by DWF, fomoscan, the fomo co-founder, but no public quantification exists.

### H2. KOL-sell detector as a hard exit / short-horizon fade — rank 2
- **Mechanism.** Same feed, opposite side: when a resolved KOL sells (visible on-chain ~15 s before followers see it), exit any position in that token immediately; optionally fade tokens whose price is >20% above the KOL's entry when the KOL's first sell prints.
- **Why it persists.** Followers cannot see the sell for ~15 s; KOL disclaimers ("can sell at any time") and documented dump patterns (CATE 29 wallets, PIPEDOG) make sells informative.
- **Test.** Conditional returns 15 s-10 min after first KOL sell, by size relative to their position and pool depth. Compare to unconditional drift.
- **Falsified if.** Post-sell drift is not significantly negative or is fully priced within 2 blocks (bots already do this).

### H3. Survivor selection at 48 h ("Wood rule") with narrative/holder-quality filters — rank 3
- **Mechanism.** Ignore launches; buy graduated tokens still trading at 48 h with rising unique-funded-wallet inflow, top-10 holder share < ~35%, no deployer-funded early cluster, low creator tax, and a one-sentence narrative; sell incrementally into strength, keep a moon bag.
- **Why it persists.** Survival is a hard filter that prunes >95% of tokens; the evidence (Marino et al., MemeTrans) shows holder concentration and non-bot share are predictive; retail attention on fomo lags survivorship, so survivors keep receiving flow.
- **Test.** Universe = all Pons V1/V2 graduates Jul 13-Sep 3 (PoolGraduated logs). Compute 48 h survival, holder concentration, funding-source clustering, inflow velocity; forward returns at 1 d/3 d/7 d with 3% costs and depth-aware sizing. Notanicecat69's own trade history (fomoapi) as a sanity check of the rule.
- **Falsified if.** Survivor forward returns are not better than a 3-5% cost hurdle after dropping the top 5 outliers (CASHCAT, PONS, AI, BONER, PIPEDOG).

### H4. Catalyst anticipation on liquid graduates (listings, perps, brokerage) — rank 4
- **Mechanism.** Watch the top-20 tokens by locked liquidity for pre-catalyst fresh-wallet accumulation (Bubblemaps-style), CEX/perp listing rumors, Robinhood brokerage listing patterns (CASHCAT precedent). Enter with depth-aware size; exit into the listing pump.
- **Why it persists.** Robinhood is economically aligned with chain-native tokens (sequencer fees), has listed one, and listings leak through wallet behavior; catalysts recur (Gate, Binance Alpha, Hyperliquid/Aster perps).
- **Test.** Collect all known catalysts (Jul-Sep: PONS Gate/Binance Alpha, CASHCAT RH listing, AI Aster, HOODRAT Furie) and measure T-72 h to T+24 h price and fresh-wallet inflow; check if a generic "fresh-wallet accumulation in top-20 token" trigger has positive expectancy. GeckoTerminal OHLCV suffices.
- **Falsified if.** Fewer than ~10 events, or the pre-catalyst signal has no precision without hindsight knowledge of the catalyst.

### H5. Bundle/insider-overhang filter as a universal overlay — rank 5 (modifier, not standalone)
- **Mechanism.** On every candidate, compute share of supply held by tax-exempt/whitelisted wallets and by wallets funded from a common source in the first 60 s; avoid tokens above a threshold or size down.
- **Why it persists.** V2's 32-wallet exemption list is on-chain and fixed at creation; bundling is a persistent behavior.
- **Test.** For all graduates, regress 24 h/7 d drawdown-from-peak on bundle share; also test if PIPEDOG-style bundled runners have higher peak but faster collapse.
- **Falsified if.** No relationship between bundle share and forward returns (bundled runners run just as far).

### H6. Low-follower "quiet skill" copy (cosby, CardinalSaint2, pointfarmcap, Salem1299534) — rank 6
- **Mechanism.** Copy on-chain (not via app) traders with high realized PnL, few holdings, modest volume, and <25K followers, so their buys are not self-fulfilling and copying does not front-run a crowd.
- **Why it might persist.** These accounts cannot be exit-liquidity operators (too small an audience); if their edge is real it is information/selection.
- **Test.** Pull full trade histories (`/v2/users/{handle}/trades`, realized vs unrealized), compute realized win rate, hold time, PnL concentration (Herfindahl across tokens), out-of-sample stability (split Jul/Aug/Sep). Simulate copy at N+2 with 2-3% cost.
- **Falsified if.** PnL is one bag, or realized edge disappears out of sample or after the copier's 1%+impact penalty (arxiv 2601.08641's ~3%/trade ceiling).

### H7. Venue-token thesis (buy the dominant launchpad's fee-burn token early) — rank 7, low frequency
- **Mechanism.** PONS' 181x was driven by 80%-of-protocol-fees buyback/burn on record fees; the same reflexive structure could recur with the next dominant venue (e.g., a Pons V2 successor, LONG if it ever tokenizes, o1, NOXA re-launch).
- **Test.** Backtest PONS vs daily Pons fee revenue (DefiLlama) to confirm the fee→price link; define an entry rule (venue >30% of launch share for 5 days, buyback live) and check it would have fired on PONS at <$10M FDV.
- **Falsified if.** Fee→price relation is coincidental (buyback share is "not yet immutable") or no second instance appears for months.

### H8. Pools.trade / low-fee venue arbitrage of attention — rank 8
- **Mechanism.** 0.25% LP fee vs 1% on Pons: a fee-sensitive scalp strategy on Pools.trade graduates. Likely fails on attention/liquidity thinness ($38.6K fees on Aug 31).
- **Falsified if.** Daily volume per token too low for $500 clips.

### Rejected / low-confidence
- **Launch sniping (block 0 / first 3 s).** 99% snipe tax, whitelisted insiders, ~1% graduation, negative-sum for non-insiders (Gigabots, Pine). Reject.
- **Naive leaderboard copying via app.** 94% loser base rate, 15 s lag, ~3% cost. Reject.
- **Stock-paired (LONG) pairs as a generic strategy.** Distinct microstructure (HIMS 4.6x premium, NYSE-hour mint gaps); park until modeled separately.

---

## 3. Traps and pitfalls to audit

1. **Look-ahead via PnL fields.** fomoapi passes fomo's mark-to-market PnL; `unrealizedPnlUsd` at snapshot time embeds future prices. Recompute from trade prints and pool state at the time of each decision.
2. **Wallet-resolution look-ahead.** fomoapi `verified: db|relay|code` with retractions means handle→wallet mapping is probabilistic and may only be known after the fact. Backtest with the resolution state available at that timestamp.
3. **Survivorship in the leaderboard.** Top-100 is conditioned on winning; traders like Aurelius0121 fell out of 7d/30d. Use the full historical roster (peer.family polls every 5 min; our snapshots) not the current one.
4. **Regime in-sample.** Jul 1-Sep 3 is a launch + blow-off regime (volume 3x in the last week of August). Require the edge to survive July-only and August-only splits, and stress with 3-5x lower activity.
5. **Fee model.** Per-token `creatorTaxBps()`/`feeBps()` reads; V1 (1% V3 pool) vs V2 curve (1% on input) vs V2 v4 pool (1% hook on "unspecified currency" — verify whether exact-input buys pay in tokens); fomo $0.95 min on Solana; gas spikes to $60+/tx under congestion (Sep 1-2) and FCFS congestion shows up as failed/delayed inclusion, not a fee.
6. **Impact model.** Size to quote-side reserve, not market cap (liquidity/mcap of 2-5% is typical). Use constant-product for V2 v4 pools (full range) and tick-range math for V1 V3 pools. Our own buy marks up the bag by (1+T/Q)^2 — do not count that as PnL.
7. **Bot-polluted activity.** Exclude the top-5 relayer/bot addresses; dedupe by funding source; use net inflow, not counts.
8. **Ticker spoofing.** 361 contracts claimed "GME"; key everything by contract address.
9. **Signal spoofing.** Fake "fomo trader" txs and bait buys exist (Potion, Bloom); require the resolved wallet AND a matching feed item before acting, or size down on `code`-verified events.
10. **Latency assumptions.** All "~15 s" and "3 ms" figures are vendor/third-party; measure our own feed-to-inclusion latency from us-east-2 before trusting any timing-dependent PnL.
11. **Data-vendor conflicts.** fomo volume share (15% Dune vs 36% Chaincatcher vs $27M DefiLlama); Pons graduation stats (1.10%/1.27%) unattributed; DWF sample definition (fomo vs all Solana wallets). Prefer our own on-chain counts.
12. **Operational risk.** fomo app freezes during LP pulls, bridge-partner outage Aug 30, chain uptime ~98% in August with multi-hour state-update gaps. Execute on-chain with an exported key/separate hot wallet; keep positions small enough to survive a 2-3 h chain stall.

---

## 4. Top traders: skill vs luck vs insider (external evidence)

| Handle | fomo rank / followers | PnL/volume | Classification | Basis |
|---|---|---|---|---|
| unipcs (Bonk Guy) | #1 all windows / 466K | ~5x | **KOL flow-mover; unrealized bag (PONS ~1%, MARSCOIN ~2%)**; impact-adjusted PnL ~25% per critic | tronweekly (Arkham $14.5M portfolio), kucoin MidCurveMortal post, his own "don't blindly copytrade me" |
| DumbCrayonEater | #2 / 451K | ~9x | **Luck/one bag** (91% AI, $21K→$8M unrealized, largest holder) | theblockbeats (Lookonchain), blockscout |
| Salem1299534 | #3 / 179K | ~2.8x | **Unknown** — 11 holdings, anonymous, no footprint | local JSON only |
| Natan_benish | #4 / 77K | ~415x | **Insider** — LONG launchpad co-founder; $12.6K fomo volume | kucoin, mexc learn |
| brrrgrrrz | #5 / 73K | ~1.15x | **Possible predator** — realized churn; "immoral to let a sucker keep his money"; SolBurgerz link inferred (low confidence) | x.com/brrrgrrrz |
| AvgJoesCrypto | #6 / 92K | ~2.2x | **Plausible skill (early-mover)** — DeFi analyst, 810 trades, no dump allegations | substack, X |
| frogmanhaha | #7 / 45K | ~168x | **Luck/one bag** — EVM-only, 227 trades, self-described "0 or $3M" | x.com/frogmanhaha |
| change | #8 all / 337K | 0.12x | **Active KOL, mostly realized**; fomo-native audience 20x his X; referral income | x.com/changefomo |
| notanicecat69 (Wood) | #8-9 / 50K | 0.47x | **Skill, rule-based** (48 h rule, narrative, incremental sells); stats match stated process | fomo.family/blog/learn/notanicecat69-memecoin-trading-strategy |
| ogle | #8-10 / 23K | ~9x | **Thesis-driven single bet** (PONS $5K→$5.7M); low followers so not self-fulfilling; not insider | finbold, coindesk profile |
| econoar | #7-12 / 61K | ~2.1x | **One concentrated bag (BONER/HIMS)**; credible, reflexive LONG-pair dynamics | coinex feed analysis |
| ether_monk | #9-12 / 319K | 0.29x | **Active KOL, diversified, "roundtripper"**; 7d collapse to #50 | x.com/ether_monk |
| frankdegods | #15 / 219K | 0.05x | **Do not trust; flow signal only** — insider allegations, token launcher; FomoTop 65% of picks peak +50% in 48 h (followers do chase him) | theblock, protos, fomotop.money |
| 0xAvast | #14 all / 260K | ~2.1x | **Insider-adjacent early mover who sells into followers** (realized $1M CASHCAT while telling followers to hold) | x.com/0xavast, coingape |
| CardinalSaint2 | #13-14 / 19K | ~1.9x | **Unknown, best "quiet skill" candidate** | local JSON only |
| cosby | #7 24h, #18 all / 19K | ~1.7x | **Unknown, 193 trades — quiet skill or one bag** | local JSON, peer.family |
| Aurelius0121 | #40 all / 272K | 0.14x | **Referral-farming KOL**; faded from 7d/30d | twitterscore, X |
| smol_intern | #56 all / 60K | 0.08x | **Skill (Solana scalper)** — FomoTop #2 pick quality, realized churn | fomotop.money |
| PoorGoat_ | #25 all / 498K | ~1.4x | **Community-takeover KOL (CATE CTO)** — coordinated 29-wallet dump documented | blog.bubblemaps.io, catearmy.com |
| pointfarmcap | #61 24h / 7.6K | — | **Systematic high-turnover unknown** (2,044 trades, 5 holdings) | local JSON |

**Watchlists implied:** flow-mover set for H1/H2 = unipcs, PoorGoat_, change, ether_monk, 0xAvast, frankdegods, DumbCrayonEater; quiet-skill set for H6 = CardinalSaint2, cosby, pointfarmcap, Salem1299534, notanicecat69, smol_intern (Solana); exclude as signal = Natan_benish, frogmanhaha, Aurelius0121.

---

## 5. Highest-priority unresolved questions (blockers for the backtest)

1. Identify fomo's ERC-4337 paymaster/bundler and router path on chain 4663 (needed to tag fomo flow; SwapRouter02 is not it). Inspect a resolved leaderboard wallet's recent tx on Blockscout.
2. Measure the app-feed lag ourselves (block timestamp vs `/ws/alerts` `seenAt`) and our own feed-to-inclusion latency from us-east-2.
3. Run the H1 event study (follower-wave magnitude by follower count and pool depth) — nothing public quantifies it.
4. Pull per-token holdings and realized/unrealized splits for the top 20 (fomoapi) to confirm the one-bag classifications above.
5. Re-measure Pons V2 graduation rate, time-to-graduation, and post-graduation survival/liquidity distributions over several days of logs; read `creatorTaxBps` across thousands of launches.
6. Verify whether the snipe tax window is 3 s or 5 s across curve vintages, and whether Telegram bots can trade V2 curves pre-graduation (affects who is in the follower wave).
7. Plan for the Sep 29 gas-subsidy end and the card-flow regulatory review as regime-change tests.