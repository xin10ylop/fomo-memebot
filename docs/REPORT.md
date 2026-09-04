# The Big Treasure — fomo leaderboard research report

Session: 2026-09-03 20:45 UTC → 2026-09-04 (Robinhood Chain / Solana memecoins as traded on fomo).
Everything below was computed from data collected in this session; scripts are in `src/`, derived data in `data/derived/`, raw pulls in `data/raw/` (large raw files stayed in the session scratch area and are described in `docs/DATA_SOURCES.md`).

## 0. Executive summary

1. **The fomo leaderboards do not rank traders, they rank bags.** `pnlUsd` is mark-to-market on current holdings (24h PnL ÷ modelled holdings move: median ratio 0.97, p25–p75 0.84–1.09 across 90 traders). No price impact, no realized/unrealized split. Median top-100 trader has 78% of their portfolio in one token; the constant-product liquidation haircut on their top holdings is 29% at the median and 60% for the #1 trader.
2. **Realized trading by the "top traders" is mostly negative.** In the last-25 closed trades fomo exposes, the median win rate is 32% and 63% of the 147 traders have a negative realized sum. On-chain (Robinhood Chain ERC-20 transfers, 45,865 real fills after stripping 114k airdrop-spam transfers; Solana via Helius, 238k signatures) the picture is the same: the money is a handful of early, never-sold bags (PONS, AI, CASHCAT, BONER, MARSCOIN), often acquired before the token was tradable on fomo, plus founder/allocation supply (LONG co-founder Natan_benish: $5.2M "PnL" on $12.6K fomo volume).
3. **Following the leaderboard is not an edge.** After a leader's buy (276 precisely matched on-chain fills, exact pool-swap prices), price rises a median +2.7% within 60 s versus 0.0% in placebo windows — real, but the leader's own fill already moved price +3.4% and a $500 follower pays ~2% fees plus impact in ~$30k pools: net −4.6% median. Buying on the app's buy alert 1–3 min later: +2.5% median at 1 h before costs, ~0 after, and ~0 at 4 h. Multi-trader "consensus" entries: no edge. The feed only prints profitable sells (281/281 sells with a realized figure were gains), so the app's social proof is one-sided.
4. **What does show a repeatable, retail-executable edge in this market is the opposite of copy-trading: buying sharp dips in liquid tokens that the leaderboard crowd is actively trading.** 15-minute drops ≥15% in pools with ≥$100k liquidity, where ≥2 leaderboard wallets traded the token in the prior 24 h (knowable in real time) and the dip is not the end of a blow-off (prior 1 h return ≤ 0), show median forward returns of +7.8% (1 h, 74% positive), +7.2% (4 h), +27.7% (24 h, 67% positive) versus −0.3%/−0.4%/+0.3% for random entries on the same tokens. Net of 2% fees + impact for a $500 clip: +4.8% median at 1 h (62% positive); a +15% take-profit / −30% stop / 4 h time-stop rule hits 83% of the time with a +6.5% mean. 137 events verified on exact swap prices. Sample: 65 core events, 15 tokens, July-heavy; two tokens contribute a third of events. This is gold with a strong mechanism (thin liquidity + impatient flow → overreaction), not yet proven treasure: n is small, the regime (a chain in blow-off) is unusual, and the 24 h figures carry residual survivorship. Section 5 gives the full spec, the audit, and the paper-trading plan already running.
5. **Where the "big edge" actually sits on Robinhood Chain is structural, not a trade**: Pons creators receive 70% of a 1% fee on every trade forever (creators were paid ~$20.9M in 47 days); insiders/whitelisted wallets own the first seconds of every launch; audiences of 100k–500k followers move thin pools 60–140% in seconds. None of these is available to a retail trader with no special access, and the report says so rather than dressing them up as a strategy.

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

## 5. Candidate strategy: dip-reversion in liquid, socially active memecoins

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

Do not copy the leaderboard. Run the dip-reversion rule as a paper trade for at least two weeks across the September 29 gas-subsidy change, logging every signal with the fill price actually obtainable, and only then trade it live at $500 clips. Keep the "process" lessons from the few disciplined traders (no launch-window buys, survivors only, fixed-clip scaling in and out, moon bag), and treat KOL buys as exit liquidity for positions already held rather than as entries.

## 8. Adversarial audit verdict

(pending)
