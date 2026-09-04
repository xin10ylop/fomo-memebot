# fomo-memebot — "The Big Treasure" research

Research repository: is there a big, sustainable, retail-executable edge behind the fomo (fomo.family) memecoin leaderboards?

**Read `docs/REPORT.md` first.** Short version: the leaderboards rank unrealized bags, following the leaders has no edge after costs, and the one candidate that looked like an edge (buying sharp dips in liquid, leaderboard-active tokens) was refuted by an adversarial audit (look-ahead liquidity filter, survivor universe, candle artifacts, understated costs). What survives is a small, capacity-limited 15-minute overreaction bounce that still has to be proven on a hindsight-free forward test. No big, sustainable, retail-executable edge was found; the report says so and documents why. Round 2 (report section 10) tested the viral "95% lose, buy the revenue protocols" thesis: following leaders into fresh launches only paid in the July launch wave, and PONS, the one real fee-earning token, is priced like pump.fun's PUMP on what it actually burns. Round 3 (section 11) quantified every money-making mechanism with its tail and costs; the only one open to a retail account with positive, measured expectancy is a delta-neutral funding carry on the mania tokens' Hyperliquid perps (CASHCAT: +16% on capital in 55 days, every two-week window positive). Round 4 (section 12) replayed every launch of Sep 3 from 5.9M v4 swaps and 419k bonding-curve trades and tested the "filter new coins and scalp" playbook on the whole universe: every filter and exit loses on both fit and holdout hours.

## Layout

| Path | What |
|---|---|
| `docs/REPORT.md` | full findings, trader-by-trader summary, hypotheses, candidate strategy, audit |
| `docs/TRADERS.md` | 147 leaderboard traders classified from fomo + on-chain data |
| `docs/TRADER_POSITIONS.md`, `docs/MEMES.md` | every captured position / entry per trader; every meme the leaderboard trades, ranked by number of leaderboard traders |
| `docs/TOKEN_METRICS.md` | memecoin fundamentals per meme and per trader: entry market cap (FDV), token age at entry, launchpad, deployer / dev, fomo holder counts and tracked top holders, and whether any of it predicted the leaders' realized results |
| `docs/trader_dossiers_agents.json` | deep dives on the top 10 handles |
| `docs/research_round1.json`, `docs/research_synthesis_round1.md` | external research with sources |
| `docs/DATA_SOURCES.md`, `docs/ANALYSIS_GUIDE.md` | data access, file formats, conventions |
| `src/collect/` | collectors: fomoapi leaderboards/trades/balances/feed (`pull_fapi.py`, `ws_collect.py`, `snapshot_loop.py`), Helius (`pull_sigs.py`, `pull_helius_parsed*.py`), Robinhood Chain logs/blocks/deployers (`pull_rh_logs.py`, `pull_rh_blocks_all.py`, `pull_creators.py`), whole-day swap and launch replays (`pull_v4_swaps_day.py`, `pull_v4_init.py`, `pull_v2_curve.py`), fomoapi holders and theses (`pull_holders.py`, `pull_theses.py`), GeckoTerminal candles (`gt_common.py`, `pull_gt.py`, `pull_gt_1m.py`), DexScreener metadata (`pull_dex.py`) |
| `src/analysis/` | ledgers (`rh_ledger_v2.py`, `sol_ledger.py`), dossiers (`dossier.py`, `classify_traders.py`), positions and token fundamentals (`positions_all.py`, `token_metrics.py`, `entry_outcomes.py`, `holders_series.py`, `token_docs.py`), round 2 (`lottery_bound.py`, `house_token_fees.py`, `pons_burns.py`, `pons_swaps.py`), round 3 (`behavior.py`, `hl_carry.py`, `pool_swaps2.py`, `pull_factory_logs.py`), round 4 (`launch_replay.py`, `curve_replay.py`), event studies and backtests (`kol_swap_study2.py`, `kol_event_study.py`, `flow_backtest.py`, `momentum_1m.py`, `crash_reversion_15m.py`, `crash_swaps.py`, `survivor_test.py`, `pick_quality.py`) |
| `src/strategy/dip_reversion_paper_trader.py` | the candidate strategy as a live paper trader (DexScreener polling, fomo feed universe) |
| `data/raw/fomoapi/` | leaderboards, feed (`ws_alerts.jsonl`), 30-minute board snapshots |
| `data/raw/hyperliquid/` | perp meta, funding history (CASHCAT, PONS, PUMP; 60-day scan of all liquid perps), hourly perp candles |
| `data/raw/defillama/` | daily fees/revenue for Pons, The Index, pump.fun, letsbonk, Robinhood Chain; PUMP and BONK prices |
| `data/derived/` | classification table, on-chain fills per trader (`rh_fills/`), every position per trader (`positions/`, `positions_all.csv.gz` with entry FDV / age / launchpad / dev columns), `memes_traded.json`, `token_metrics.json`, `trader_entry_metrics.json`, `entry_outcomes.json`, event-study outputs, paper-trade log |

## Reproducing

All scripts expect to run from a data root containing the raw pulls (`fapi/`, `rh/`, `helius/`, `gt/`, `dex/`, `prices/`); see `docs/ANALYSIS_GUIDE.md`. Keys (fomoapi `fapi_…`, Helius) are read from the scripts' constants; replace them with your own. Rate limits that matter: fomoapi free key 10k requests/month and 25 handle resolutions/month (never call `/v2/users/{handle}` in a loop), GeckoTerminal ~30 requests/minute, Robinhood Chain public RPC batches of ≤100 with a browser user agent.

Order: `pull_fapi.py` → `pull_sigs.py` + `pull_helius_parsed.py` → `pull_rh_logs.py` + `pull_rh_blocks_all.py` → `pull_dex.py` → `pull_gt.py` → `rh_ledger_v2.py`, `sol_ledger.py` → `dossier.py`, `classify_traders.py` → backtests.
