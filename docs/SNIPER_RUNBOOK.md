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
- On the exact curve, E1 on every launch is −5% to +3% a trade depending on the day. On **bundled launches** (three
  or more named wallets bought in the creation second) the outsider's seats pay: E1 +9% and +15% at the front on the
  two peak days, +5% and +10% from 0.3 s behind; and out of sample on Sep 4 and Sep 5 (section 21.1) +8.5% and +0.6%
  at E1 behind, **+9.6% and +4.2% at E2 behind**. E2, the second whole second after creation, pays +0.19% instead of
  +6.18% and sits behind the fastest bots rather than racing them; it is the seat this runbook runs by default.
- The engine resolves the curve from the feed alone: the wallets the creator exempted are listed in the creation
  calldata, and the address they buy inside the creation second is the curve. No RPC call before the buy.

## 1. The trade

1. A Pons V2 creation appears on the sequencer feed (factory `0xe33e…`, selector `0xf85f8e41`); the engine recovers the
   creator and the quote asset from the calldata and resolves the curve from the factory's event.
2. Filters: creator's first launch of the UTC day, ETH quote, a usable launch-block buy.
3. The engine reads the creator's exempted wallets from the creation calldata, watches the feed for their buys inside the
   creation second (that address is the curve; at least `BUNDLE_MIN` = 3 of them must have bought), and waits for the
   first feed message stamped in the seat's second (`SEAT=E2`: two seconds after the creation's timestamp; `E1`: one).
4. Buy 3% of supply or the stake, whichever is smaller, sized on the exact curve with the fee assumed at 5% + 6.18%;
   `minOut` = sized tokens × (1 − `SLIP`), so a landing in the wrong second reverts for gas rather than paying 95%.
5. Read the tokens received from the buy's Buy event; approve the curve at once; sell that balance 7 s after the buy
   landed, in one transaction.
6. Every eligible bundled launch is scored 25 s after creation with the simulator's replay; the engine trades only
   while the mean of the last 30 scores is ≥ +5%. Daily stop at −30% of the day's starting bankroll. One position at a
   time. Stake = 20% of bankroll, clamped $50–$300.

## 2. What to expect (exact curve, $300 stakes, 3% of supply, sell 0.3 s late)

| | Aug 20 | Aug 27 | Aug 30 (new) | Aug 31 (new) | Sep 1 (new) | Sep 2 | Sep 3 | Sep 4 (new) | Sep 5 (new) | Sep 6 (new) |
|---|---|---|---|---|---|---|---|---|---|---|
| bundled launches in 6 h | 17 | 85 | 246 | 321 | 335 | 303 | 400 | 155 | 416 | 364 |
| E1 front | −4.5% | +2.4% | −1.1% | +2.2% | −2.1% | +9.1% | +14.8% | +11.9% | +4.7% | +9.4% |
| E1, 0.3 s behind | −6.2% | −1.9% | −1.9% | +1.1% | −6.0% | +5.1% | +10.4% | +8.5% | +0.6% | +2.5% |
| E2 front | +2.9% | +2.3% | +2.8% | +6.2% | −2.3% | +8.9% | +11.4% | +13.2% | +5.0% | +5.8% |
| E2, 1 block behind | +1.3% | −0.8% | +1.8% | +3.7% | −3.5% | +7.4% | +9.6% | +12.0% | +4.1% | +3.3% |
| **E2, 0.3 s behind** | −0.4% | +0.2% | +0.4% | +2.6% | −4.7% | +6.2% | +8.0% | **+9.6%** | **+4.2%** | **+0.9%** |
| switched, one at a time, E2 1 block behind | $0 | −$67 | −$706 | +$1,897 | −$1,181 | +$2,439 | +$6,956 | +$3,085 | +$3,561 | +$3,517 |

Off hours, Sep 3 (bundled seat, E2 one block behind): 00–06 UTC 1,909 launches, about zero (−$311 switched at
0.3 s behind); 18–24 UTC 2,674 launches, +5.9% to +10.1% a trade, $2.5k to $10.9k switched. The launchpad is busy
around the clock; the switch, not the clock, decides when to trade.

Sum over the eleven windows (66 hours), switched and one position at a time: bundled seat $23.7k at the front and
$19.5k one block behind; every launch without the filter $38.0k at the front but $14.7k one block behind and $8.7k
three blocks behind (`data/derived/sniper_e2front.txt`).

Sep 2 and Sep 3 were the two busiest days of the fee cycle; Aug 30, Aug 31, Sep 1, Sep 4, Sep 5 and Sep 6 were never
used to choose anything: four of the six pay, Aug 30 and Sep 1 lose with the switch holding each to under $1,200. Aug 12 had no
bundled launches at all. More windows are appended to `data/derived/sniper_oos.txt` as they are pulled.

## 3. The machine

- EC2 in **us-east-2 (Ohio)**, where the sequencer lives; the smallest general-purpose instance is enough (the feed
  is ~70 transactions a second, decoded in microseconds). From anywhere else the round trips alone put every row above
  in the loss bucket. `deploy/ohio_setup.sh` sets the box up in one command (chrony, the engine as a dry-run service,
  the probe).
- Detection from `wss://feed.mainnet.chain.robinhood.com` (directly, or through Offchain Labs' Nitro relay if more than
  one process needs it: Robinhood rate-limits per client). The curve comes from the feed itself (section 21.2), so no
  RPC sits before the buy. Submission straight to `sequencer.mainnet.chain.robinhood.com` (first come, first served,
  no priority fee). Nonce, receipts and the 25-second scorer go to a provider endpoint in the same region (Alchemy,
  QuickNode, Chainstack all list the chain; pick a US-East region or a dedicated node); the public RPC rate-limits.
  A full Nitro node (64 GB RAM, several TB NVMe, an L1 RPC and beacon endpoint) is not needed.
- Gas ≈ $1 a round trip at 0.5 gwei. The engine halts if a round trip exceeds 3% of the stake.
- Telegram bots (Maestro has Pons V2 support at a flat 1%; GMGN lists the chain) cannot take a seat or wait for a second
  boundary: use one to place a manual test buy if you want to see the fee tier and the tax with your own wallet, not to
  run the rule.

## 3b. The latency, in numbers (section 21.5)

- Ordering is first come, first served at the sequencer; no priority fee, no express lane.
- The fastest outsiders land in the very first block of the seat's second on a third of bundled launches and within
  two blocks on two thirds; that block holds one or two outsider buys. They predict the boundary; a sender that reacts
  to seeing the new second on the feed lands one to two blocks (100–200 ms) later.
- `SEND_MODE=predict` with `MARGIN_MS` is how the engine joins that race; `react` is the safe default for the first
  days. Live, the engine tunes the margin from each receipt (`landing` events): early landings revert on minOut and
  cost gas, so the margin only ever creeps toward the boundary from the late side.
- Before anything else run the probe: `deploy/ohio_setup.sh` installs it as a service. A sequencer round trip above
  10 ms or a flip spread far above one block means the box is in the wrong place or its clock is off.

## 4. Configure

```
SEAT=E2 BUNDLE_MIN=3 SUPPLY_FRAC=0.03 SLIP=0.25 HOLD_S=7 BANKROLL_USD=300 FRAC=0.2 STAKE_MIN=50 STAKE_MAX=300 \
SWITCH_N=30 SWITCH=0.05 DAILY_STOP=0.30 MAX_RESOLVE_MS=1500 GAS_MAX_SHARE=0.03 TIER_ASSUMED=0.05 SEND_MODE=react MARGIN_MS=25 \
WALLET=0x… RPC_URL=https://… FEED_URL=wss://feed.mainnet.chain.robinhood.com LOG_PATH=engine.jsonl \
python3 src/strategy/sniper_engine.py
```

`SEAT=E2` waits two seconds past the creation's timestamp (+0.19%); `SEAT=E1` waits one (+6.18%, in front of the
second-one bots, only worth it if your `sent_ms` is consistently first). `SEAT=E0` refuses to start without `EXEMPT=1`,
and `EXEMPT=1` is only true for a wallet the creator named. Do not set it.

## 5. Dry run first, then the send step

Run the engine for a full day in dry run on the Ohio machine. It logs `creation`, `skip`, `eligible_not_traded` (with
the gate that stopped it, including `bundle N < 3` and `resolved in N ms`), `trade_decision` (seat, sent_ms, size,
tokens, minOut), `unsigned_tx` (buy, approve, sell) and `score` (the exact-curve outcome of every bundled launch, the
rolling mean, the switch state, and the dry-run bankroll). Go/no-go from that log:

- `resolve_src` is `feed` on bundled launches and `feed_resolution_ok` follows every one of them 25 s later
  (a `feed_resolution_mismatch` means the engine would have bought the wrong curve: stop);
- `sent_ms` (feed to send) equal to the wait for the seat's second plus a few milliseconds, otherwise the machine is in
  the wrong place;
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
