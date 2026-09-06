# First-block sniper runbook (Pons V2, Robinhood Chain)

The one seat in this study that a person with almost no capital can take, because each trade lasts seven seconds and a
single small stake can cycle through the day's launches. Everything below is measured in `REPORT.md` sections 14 and
19 and implemented in `src/strategy/sniper_engine.py`, which runs the whole decision loop and builds the exact
transactions but does not sign or send them. The send step is yours; section 6 says exactly what it must do.

## 0. The trade

A Pons V2 launch is a bonding curve. The creator buys in the launch block; the first outside buyer sets the next
price; within seconds the bots and the app's traders arrive and the curve walks up; within a minute most of them are
gone. The seat: buy at the first outside price, 3% of supply or your stake, whichever is smaller, and sell seven
seconds later into whoever came after you. Measured on every launch of five six-hour windows with exact curve exits,
1% fee each way and $1 of gas per round trip (section 19, corrected exit valuation):

| window | Pons fees that day | launches traded | mean return per trade | net at $300 stakes |
|---|---|---|---|---|
| Aug 12 | ≈ $0.5M | 229 | −3.7% | −$747 |
| Aug 20 | ≈ $0.25M | 120 | +4.3% | +$1,593 |
| Aug 27 | ≈ $2.3M | 842 | +6.6% | +$7,255 |
| Sep 2 | ≈ $6.0M | 1,632 | +16.6% | +$40,632 |
| Sep 3 | $6.4M | 1,311 | +34.6% | +$66,876 |

The median trade loses 2 to 3% (fees on a launch nobody follows); 45% of trades win; the top 5% of launches carry a
third of the profit. It is a flow business: the day's flow of slower buyers is the income, and the switch below is how
you only trade when it exists.

## 1. What decides whether you make money

1. **Latency.** You must be the first outside buyer, or at worst the second paying ≤ 10% more. Half a second late is
   zero to negative on every window. The incumbent bot lands 0.3 to 0.8 s after creation. From a sandbox in the wrong
   region the engine resolves a creation in 630 to 1,150 ms, which the engine's gate refuses. You need a machine in the
   sequencer's region (the feed is `wss://feed.mainnet.chain.robinhood.com`; test from AWS us-east and us-west and
   pick the lower), a direct RPC, and the engine's resolve time under 300 ms p50. Measure before funding anything.
2. **The regime switch.** Every eligible launch is scored 25 s after creation from the curve's own events, whether you
   traded it or not. Trade live only while the mean of the last 30 scores is ≥ +5% of stake. Across the five windows
   this turned Aug 12 from −$747 to $0, Aug 27 from +$7.3k to +$4.9k with a third of the drawdown, and kept 84 to
   90% of the peak days. No window is negative with the switch on.
3. **Stake size.** Gas is ≈ $1 a round trip at today's base fee (0.45 to 0.57 gwei, ~450k gas each way). Under $50 a
   stake, gas eats the edge; from $100 to $300 the return per trade is flat; above $500 the exit impact on a $30k
   curve costs more than the extra size earns. Stake = 20% of bankroll, floored at $50 and capped at $300.
4. **Filters.** Creator's first launch of the day (the bots skip serial launchers, so their flow does too), native-ETH
   quote, creator's launch-block buy ≥ 5% of supply (the bots select launches with a real stake; this filter earned
   +24% on Sep 2 and +48% on Sep 3 per trade against +17% and +35% without it, on a quarter of the launches, and it
   was the only variant that survived Sep 2's bad first hour from a $300 bankroll).
5. **One position at a time** until the bankroll can fund several stakes; on a peak day this captures about 60% of
   what unlimited concurrency would.

## 2. Compounding from a small bankroll (measured paths, section 19)

Stake = 20% of bankroll clamped to $50–$300, one position at a time, switch on, stop for the day at −30%:

| window | filter | start $300 | start $1,000 |
|---|---|---|---|
| Sep 3 | creator buy ≥ 5% | $32,439 | $34,710 |
| Sep 3 | base | $82,641 (low $219) | $85,012 |
| Sep 2 | creator buy ≥ 5% | $15,563 | $17,959 |
| Sep 2 | base | daily stop at $188 | daily stop at $694 |
| Aug 27 | base | $5,465 | $9,401 |
| Aug 20 | base | $597 | $2,059 |

Read it honestly: the two peak days turn $300 into tens of thousands, one ordinary day into a few thousand, one
trough day into a few hundred, and one bad day into a −30% stop. The stake caps at $300 within an hour on a flow
day, after which the bankroll grows linearly with the number of trades, not exponentially. The floor is $300 of
bankroll and the ability to lose it.

## 3. Prerequisites

* A Robinhood Chain wallet (chain id 4663) used only for this, funded with the bankroll plus 0.01 ETH of gas.
* A machine near the sequencer with Python 3, `websockets`, `rlp`, `eth_account` (the engine's imports) and your
  signing library.
* The engine: `src/strategy/sniper_engine.py`. Run it first as it is (dry run) for a full day: it logs every
  creation, every skip and its reason, every gate that blocked a trade, every score, and the exact unsigned
  transactions it would have sent.

## 4. Configure

Environment variables, defaults in brackets: `WALLET` (recipient address), `BANKROLL_USD` [300], `FRAC` [0.2],
`STAKE_MIN` [50], `STAKE_MAX` [300], `HOLD_S` [7], `SUPPLY_FRAC` [0.03], `SLIP` [0.25] (the buy's minOut tolerance
and the price you accept relative to the post-creator price), `MIN_CREATOR_SUPPLY` [0.05], `MAX_CREATOR_BUY_ETH`
[2], `SWITCH_N` [30], `SWITCH` [0.05], `DAILY_STOP` [0.30], `MAX_RESOLVE_MS` [300], `GAS_MAX_SHARE` [0.03],
`ETH_USD`, `LOG_PATH`.

## 5. Go / no-go each session

* The engine's `score` events over the last hour: rolling mean ≥ +5% → the switch is on. Under +5%, it will not trade
  and you should not override it.
* `resolve_ms` on `trade_decision` and `eligible_not_traded` events: p50 under 300 ms. Over it, move the machine.
* `eth_gasPrice` implied round-trip cost under 3% of the stake (the engine checks this before every trade).
* Gas subsidy status: the subsidy ends in early October 2026. On Sep 1–2 congestion the base fee made a creation
  cost $20–60; a round trip at those prices costs $3–9, which the $8 stress run in section 19 survives only at
  $200+ stakes on flow days. When the subsidy ends, re-measure before trading.

## 6. The send step (yours)

`submit(tx, label)` in the engine receives a dict with `to`, `value`, `data`, `gas`, `gasPrice`, `nonce`, `chainId`
and returns `None`. Your version signs it with the wallet's key and broadcasts with `eth_sendRawTransaction`,
returning the hash. Three transactions per trade: `buy` (to the curve, payable, selector `0x59a87bc1`, arguments
amountIn / minOut / recipient), then after `HOLD_S` seconds `approve` (to the token, `approve(curve, max)`) and
`sell` (to the curve, selector `0xd04c6983`, arguments tokens / minOut / recipient). Verify on the first live trade,
with a $50 stake: that the buy fills at the expected price (the `price_after_creator` in the log), that the sell
requires the approval (if the curve pulls without it, drop the approve and save a block), and that the sell's minOut
of 0 is acceptable to you (the exit is time-based; a bounded minOut at 50% of entry protects against a creator dump
landing in the same block, at the cost of an occasional unfilled sell that you then sell manually). The fastest bot
routes both legs through `0x65050a9b…` with selector `0x4d819a2a`, which bundles approval and sale; the direct curve
calls do the same job one block slower.

## 7. Tracking and kill criteria

* Every trade: the log's `trade_decision` and the `score` event 25 s later carry the simulated outcome; compare it
  with the realized fill. If realized lags simulated by more than 5 points over 50 trades, you are not first in line:
  fix latency or stop.
* Kill for the day: the daily stop. Kill the strategy: the switch off for three consecutive sessions; the gas subsidy
  ending; Pons changing the curve or the fee; the first-buyer flow disappearing (score events with "no first buyer
  within 3 s" above 60%).

## 8. What this is and is not

It is honest trading in an open market, buying first and selling to whoever comes next, the same trade the best bots
on the chain run. It is not sustainable in the sense of the brief: it lives on a launchpad's mania and a gas subsidy
with an announced end, it needs a machine you do not have yet, and its median trade loses. It is the highest return
per dollar in this repository by a wide margin on flow days and nothing on the others, and the switch is what keeps
those two facts apart.
