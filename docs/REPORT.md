# The Big Treasure — fomo leaderboard research (working report)

Status: DRAFT, being filled in as backtests complete. Session date: 2026-09-03/04.

## 1. What the fomo leaderboards actually measure

* `pnlUsd` on the 24h/7d/30d/all boards is **mark-to-market on current holdings**. For every top trader checked, the 24h figure equals the day's change in the value of their bags (ratio 0.9–1.1). Unrealized gains on illiquid tokens count at the last print with zero price impact.
* `all` ≈ `30d` for almost everyone: the boards are a ranking of who holds the most of what pumped in the Robinhood Chain memecoin wave (Pons launchpad, since July 2026).
* PnL / cumulative fomo volume is 5×–400× for several top-10 names (Natan_benish, frogmanhaha, DumbCrayonEater, ogle, unipcs): the money is unrealized appreciation on early bags, often acquired outside fomo.
* The live feed shows a sell only with a **positive** realized figure ("+$3K realized"); of 423 sell alerts collected, all 281 with a number were gains. Losing sells print without a number. The app's social proof is one-sided by design.
* The web app (fomo.family) has no public leaderboard route; boards require login and live in the mobile app. fomoapi.io mirrors them live ("source: fomo-live"), which is what was analysed.

## 2. Data actually used

See `docs/DATA_SOURCES.md` and `docs/ANALYSIS_GUIDE.md`. Headline counts (2026-09-04 03:00 UTC):
147 unique leaderboard handles; 147 trade/holding pulls; 128 Robinhood Chain wallets with full ERC-20 transfer history (~174k txs, ~48k real fills after removing ~114k airdrop-spam transfers); 117 Solana wallets with full Helius history (238k signatures); live feed ~1,900 alerts; GeckoTerminal 15-minute candles for the traded tokens (in progress) and 1-minute candles for feed tokens.

## 3. Trader-by-trader findings

(to be filled from the dossier workflow and on-chain ledgers)

## 4. Hypotheses tested

| # | Hypothesis | Test | Result |
|---|---|---|---|
| H1 | Front-run the follower wave after a leader's buy (public sequencer feed ~0.1–1 s vs app feed ~15 s) | 276 precisely matched leader buys on Robinhood Chain, exact pool swap prices, placebo windows | Real but small: +2–3% median at 60 s vs 0% placebo; leader's own impact +3.4%; net of 2% fees + impact in ~$30k pools: −4.6% median. Not an edge for a follower. |
| H2 | Fade/exit on leader sells | same data, sells | no negative drift found at minute scale |
| H3 | 48h survivor entries | 22 events so far | inconclusive (positive, tiny n) |
| H5 | Multi-trader consensus entries | 1,568 entries | no edge; more buyers → worse |
| H-alert | Buy on app feed buy alert (+1–3 min) | ~600 alerts, 1m candles | +2.5% median at 1h on Robinhood before costs, ~0 after; 4h ~0 |
| H-dip | Buy sharp dips (≥15% in 15 min / 5 min) in liquid pools | 1,018 events (15m), 285 (1m), 137 swap-verified | positive drift; details in section 5 |

## 5. Candidate strategy

(to be filled)

## 6. Audit log

(to be filled)
