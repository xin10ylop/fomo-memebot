# Analysis guide (for humans and for analysis agents)

All paths are relative to the scratch data root `DATA` (the collectors write there; derived
artifacts are copied into `data/derived/` in this repo).

## What fomo shows vs what is real

* Leaderboard `pnlUsd` (24h/7d/30d/all) is **mark-to-market on current holdings**: for every
  trader checked, 24h PnL ≈ Σ holding value × (1 − 1/(1+change24h)). Ratio ≈ 0.9–1.1.
  It counts unrealized gains on illiquid bags at the last price with no price impact.
* `all` ≈ `30d` for almost everyone (Robinhood Chain memecoin wave since July 2026).
* Per-trader `trades` endpoint returns all open positions plus only the **last ~25 closed** trades.
  The closed sample is biased (recent, small losers cut; winners still open).
* Real fills: Robinhood Chain ERC-20 Transfer logs to/from the trader's EVM wallet
  (`rh/logs/<handle>.json` → `rh/logs/<handle>.ledger.json`). fomo settles through the relay
  `0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f` in bundled txs, so fills are priced from
  GeckoTerminal candles at the block time (`px`, `usd`), not from swap events.
  Most inbound transfers are **airdrop spam** to famous wallets (`side: airdrop`) — ignore them.
* Solana fills: Helius enhanced transactions → `helius/parsed/<handle>.ledger.json`
  (average-cost realized PnL, USDC/SOL legs only).

## Files

| File | Content |
|---|---|
| `fapi/lb/{24h,7d,30d,all}.json` | leaderboards, top 100 each (147 unique handles) |
| `fapi/trades/<handle>.json` | open positions + last 25 closed (entry/exit/realized/createdAt/closedAt/thesis) |
| `fapi/balances/<handle>.json` | live holdings across chains with value and 24h change |
| `fapi/ws_alerts.jsonl` | live app feed (buys/sells/theses with usd size; sells carry realized PnL text) |
| `fapi/snapshots/*.json` | leaderboards + token boards every 30 min; `fapi/trades_hist/` every 6h |
| `helius/sigs/<handle>.json` | all Solana signatures for the wallet |
| `rh/logs/<handle>.ledger.json` | Robinhood Chain ledger rows: `side` ∈ buy/sell/airdrop/transfer_in/transfer_out/dust, `usd`, `px`, `ts`, `b` (block), `mint` (token launch block) |
| `gt/ohlcv/<token>.json` | 15-minute OHLCV (base-token pools only) |
| `gt/ohlcv1m/<token>.json` | 1-minute OHLCV for tokens seen in the live feed |
| `dossiers.json` | per-trader merged metrics |
| `docs/research_round1.json` | external research findings with sources |

## Backtest traps found by the adversarial audit (check every one before quoting a number)

1. Never filter or cost on a *current* liquidity snapshot (`gt/pools_v3.json` `liq`, DexScreener liquidity today). Use depth at the event time: on-chain reserves / `sqrtPrice` and `L` at the signal block, or $ per 1% move from the last swaps.
2. Never build the token universe from what today's leaderboard traders traded, or pull candles only for the most-traded tokens; freeze the universe and wallet set as of each event date, and pull prices for every eligible token including the ones that died.
3. Reject candle artifacts: pools where the token is the quote (`base=False`), single-print wicks, |return| implausible for the candle volume vs depth; confirm crashes on swap logs.
4. Fees are 2 × (0.5% app + the pool's actual fee) plus stock-token hops and Pons V2 hook/creator taxes read on-chain; impact is size / measured depth, both legs. GeckoTerminal reserve USD overstates depth 3–10× on concentrated pools.
5. Do not report medians of a take-profit rule (they reproduce under random entries); report the mean and sum of P&L with token-clustered confidence intervals, one observation per token per horizon window.
6. Fill take-profits only on closes or the next observable price, never on candle highs; model stop fills 3–10 points worse than the level.
7. Count missing forward returns (dead token, censoring) as −100% in a conservative variant and report both.
8. Every filter combination examined is a multiple-testing draw; pre-register one rule and hold out the last period.

## Metrics conventions

* Entry price for event studies = **open of the first candle that starts after the event**
  (never the candle containing the event). Report 15m/1h/4h/24h/48h/7d close returns,
  MFE/MAE within 24h and 48h.
* Costs on Robinhood Chain via fomo: 0.5% app fee per side + 1% Pons pool fee per side
  + slippage; gas sponsored by fomo. Direct on-chain: 1% pool fee per side + gas
  (normally < $0.05, but $20–60 during the Sep 1–2 congestion).
* "Dead token" = no GeckoTerminal pool and no DexScreener pair → treat as −100% for strategy
  PnL (conservative) and report separately.
* Launch age = (block − mint block) / 9.9 blocks/s (Robinhood Chain ≈ 100 ms blocks).
