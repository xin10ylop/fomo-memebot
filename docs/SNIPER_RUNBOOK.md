# Sniper runbook, version 2 (after the round-12 audit)

Read report section 20 first. Version 1 of this runbook described a seat that an outside wallet cannot take. This version
describes what an outside wallet can do, what it earns on the exact curve, and what must be true before a single
dollar is sent.

## 0. What changed

- The curve is exactly constant-product (1.68 ETH / 1e9 virtual reserves). Every token has its own 1–5% fee on both
  legs, readable from the launch-block Buy event (fee ÷ quoteIn) or the curve getter `0x24a9d853` (basis points).
- The snipe tax is per whole timestamp second since creation: 93–98% in the creation second, +6.18% in the next,
  +0.19% in the one after, then nothing. Wallets the creator names at creation are exempt. Nobody else is.
- So the creation-second seat (E0) belongs to the launch team. Your earliest seat is the first block of the next
  second (E1), paying the token's fee plus 6.18%.
- On the exact curve, E1 on every launch is −5% to +3% a trade depending on the day. E1 on **bundled launches** (three
  or more named wallets bought in the creation second) is +9% and +15% at the front on the two peak days, +5% and
  +10% from 0.3 s behind, about zero on Aug 27, and there are too few such launches off-peak to trade. That is the
  trade this runbook runs.

## 1. The trade

1. A Pons V2 creation appears on the sequencer feed (factory `0xe33e…`, selector `0xf85f8e41`); the engine recovers the
   creator and the quote asset from the calldata and resolves the curve from the factory's event.
2. Filters: creator's first launch of the UTC day, ETH quote, a usable launch-block buy.
3. The engine waits for the first feed message stamped in the next whole second, counts the direct curve buys stamped in
   the creation second (the bundle), and trades only if there are at least `BUNDLE_MIN` (3).
4. Buy 3% of supply or the stake, whichever is smaller, sized on the exact curve with the fee assumed at 5% + 6.18%;
   `minOut` = sized tokens × (1 − `SLIP`), so a landing in the wrong second reverts for gas rather than paying 95%.
5. Read the tokens received from the buy's Buy event; approve the curve at once; sell that balance 7 s after the buy
   landed, in one transaction.
6. Every eligible bundled launch is scored 25 s after creation with the simulator's replay; the engine trades only
   while the mean of the last 30 scores is ≥ +5%. Daily stop at −30% of the day's starting bankroll. One position at a
   time. Stake = 20% of bankroll, clamped $50–$300.

## 2. What to expect (exact curve, $300 stakes, 3% of supply, sell 0.3 s late)

| | Aug 20 | Aug 27 | Sep 2 | Sep 3 |
|---|---|---|---|---|
| bundled launches in 6 h | 17 | 85 | 303 | 400 |
| mean ROI per trade, front of second one | −4.5% | +2.4% | +9.1% | +14.8% |
| mean ROI, 0.3 s behind | −6.2% | −1.9% | +5.1% | +10.4% |
| switched, one at a time, 0.3 s behind | $0 | −$242 | +$265 | +$8,015 |
| from $300 at 20% sizing | $300 | $236 | $193 (stop) | $6,136 |

Sep 2 and Sep 3 were the two busiest days of the fee cycle. Aug 12 had no bundled launches at all. The filter was
found on these windows: treat the numbers as the upper end until a forward test reproduces them.

## 3. The machine

- EC2 in **us-east-2 (Ohio)**, where the sequencer lives. From anywhere else the resolution latency alone puts every
  row above in the loss bucket (this sandbox: 550–1,150 ms; the gate is 300 ms).
- Detection from `wss://feed.mainnet.chain.robinhood.com`. Reads from an RPC in the same region; best is a Nitro node
  following the feed on the same instance so that resolving the curve is a local call. Submission straight to
  `sequencer.mainnet.chain.robinhood.com` (first come, first served, no priority fee).
- Gas ≈ $1 a round trip at 0.5 gwei. The engine halts if a round trip exceeds 3% of the stake.
- Telegram bots (Maestro has Pons V2 support at a flat 1%; GMGN lists the chain) cannot take a seat or wait for a second
  boundary: use one to place a manual test buy if you want to see the fee tier and the tax with your own wallet, not to
  run the rule.

## 4. Configure

```
SEAT=E1 BUNDLE_MIN=3 SUPPLY_FRAC=0.03 SLIP=0.25 HOLD_S=7 BANKROLL_USD=300 FRAC=0.2 STAKE_MIN=50 STAKE_MAX=300 \
SWITCH_N=30 SWITCH=0.05 DAILY_STOP=0.30 MAX_RESOLVE_MS=300 GAS_MAX_SHARE=0.03 TIER_ASSUMED=0.05 \
WALLET=0x… RPC_URL=https://… FEED_URL=wss://feed.mainnet.chain.robinhood.com LOG_PATH=engine.jsonl \
python3 src/strategy/sniper_engine.py
```

`SEAT=E0` refuses to start without `EXEMPT=1`, and `EXEMPT=1` is only true for a wallet the creator named. Do not set it.

## 5. Dry run first, then the send step

Run the engine for a full day in dry run on the Ohio machine. It logs `creation`, `skip`, `eligible_not_traded` (with
the gate that stopped it, including `bundle N < 3` and `resolved in N ms`), `trade_decision` (seat, sent_ms, size,
tokens, minOut), `unsigned_tx` (buy, approve, sell) and `score` (the exact-curve outcome of every bundled launch, the
rolling mean, the switch state, and the dry-run bankroll). Go/no-go from that log:

- median `resolve_ms` under 150 and `sent_ms` (feed to send) under 1,100 for E1 (the second boundary is at most a
  second away), otherwise the machine is in the wrong place;
- rolling mean of the scores positive over at least one full peak day, and the dry-run bankroll path matching the
  compounding table within its confidence interval;
- the switch turning on and off as the flow changes rather than sitting on.

The send step is yours: replace `submit()` with a function that signs with your key and calls
`eth_sendRawTransaction`, returning the hash. On the first live trade verify, from the receipt: the Buy event's fee ÷
quoteIn equals the token's tier + 6.18% (if it is 93–98% you landed in the creation second: stop and fix the
second-boundary wait); tokens received within `SLIP` of the sized tokens; the approve landed before the hold ended; the
sell moved exactly the balance. Then compare the first 30 live scores with the first 30 engine scores of the same
launches: they are computed the same way, and a gap is a latency or a seat problem, not a market problem.

## 6. Kill criteria

Stop for the day at −30%. Stop the strategy if the rolling mean of live outcomes over 30 trades is below zero while
the engine's scores for the same launches are above +5% (you are not getting the seat), if the measured surcharge is
ever above 6.18% on a next-second landing, or if the bundled-launch count falls under ten a day (the flow that pays
is gone).

## 7. Starting with $50

Gas is $1 a round trip, so a $50 stake pays 2% before anything else, and the trade's median outcome is a small loss with
a fat right tail. On the exact-curve trades, all-in from $50 reaches $300 before dropping under $25 33% of the time on
Sep 3, 23% on Sep 2, 5% on Aug 27 and never on Aug 20. Start at $300 or save to it; below that the bankroll is a lottery
ticket on the day's flow.

## 8. What this is not

It is not the +30% a trade of sections 14 and 19; that is the launch team's seat. It is not proven out of sample: the
bundle filter was chosen on the five windows. It is not available from a phone or a Telegram bot. It is a peak-day,
Ohio-latency, seven-second ride on other people's pumps, sized at $150 a trade, with a switch that keeps quiet days
near zero and a stop that caps a bad one. The chain's terms of use have an automated-trading clause whose scope is
unclear; that is the operator's call.
