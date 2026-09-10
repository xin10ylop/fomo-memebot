# Sniper runbook, version 2 (after the round-12 audit)

Read report section 20 first. Version 1 of this runbook described a seat that an outside wallet cannot take. This version
describes what an outside wallet can do, what it earns on the exact curve, and what must be true before a single
dollar is sent.

## 0. What changed

**v3 (round 15, report section 23).** Four researchers, two per question, then a triple check of everything:

- **The rule loses less by not trading behind a rival.** Launches nobody else enters in second two earn +10% (fit half)
  and +20% (test half) a trade; launches where an outsider is already in the seat lose. So the engine now sends a fixed
  0.3 s into second two and only if no outsider has bought the curve yet (`SEAT_WAIT_MS=300`, `OUT2_MAX=0`). That is
  exactly the entry the tables always assumed for launches nobody took; the gate keys only on what the feed shows
  before your transaction leaves the box.
- **Hold 5 s instead of 7, sell earlier at +50%.** Both researchers found the exposure, not the entry, is the risk:
  hold 5 s (fit +5.4% → +8.3% at the old rule), and a take-profit when the curve price is 50% above your entry
  (`TAKE_PROFIT=0.5`, priced live from the feed).
- **Sizing 15% of the bankroll, stakes $25–$300** (`FRAC=0.15`, `STAKE_MIN=25`): with the new rule the resampled
  chance of the −50% day is zero in every window at this sizing (at most 1% at the old 20% / $50).
- **Engine v4** (speed track): every built address is checksummed (the old build could not be signed by `eth_account`),
  sender recovery straight from coincurve and only when needed, no RPC call at all for launches the calldata rules out,
  the curve resolved the moment the bundle is visible, one wake per feed message, the curve's reserves folded as the
  feed arrives (nothing rebuilt after the boundary), warm keep-alive sockets to the sequencer and the provider, an
  interval-vote boundary estimator, a margin controller that can come down, a feed watchdog, monotonic clock. Section 3b.
- **Expect**, on the ten September windows the rule never saw (section 23.6, runbook 2d): +4% to +6% per trade after
  the audit of 23.8, nine windows of ten positive, from $300 about +$200 per busy six-hour window and about zero on a
  thin one, stop odds 0.1%. The
  Aug 30–Sep 6 windows paid +11% to +16% a trade and +$1,500 a window; the difference is other bots now sitting in
  second one on two thirds of bundled launches. At the measured gas ($0.10 a round trip, section 23.7) a $100 start is
  back on the table; section 9 lists the nine ways this dies and the alarm for each.

**v2 (rounds 12–14).**

- The curve is exactly constant-product (1.68 ETH / 1e9 virtual reserves). Every token has its own 1–5% fee on both
  legs, implied by the launch-block Buy event (the tokens it delivers against the exact curve; the event's `fee`
  field is only the 1% protocol fee) or read from the curve getter `0x24a9d853` (basis points).
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

## 0b. From nothing to a running dry run (the complete list)

Accounts and tools, all standard, no colocation and no custom node:

1. **AWS account** and one EC2 instance in **us-east-2 (Ohio)**, Ubuntu 24.04. t3.small (about $15–20 a month) is
   enough for the dry run; for live, c6i.large or c7i.large (about $60–70 a month) gives two dedicated cores with no
   CPU credits to run out of, and `PIN_CPU=1` keeps the engine off the core that takes the network interrupts. Open no
   inbound ports; connect by SSH key only.
2. **A provider RPC key** with Robinhood Chain (Alchemy, QuickNode or Chainstack; free tiers cover the nonce, receipt
   and scoring calls). The public RPC rate-limits and is a fallback, not the plan.
3. **A fresh wallet** generated on the box (any standard Ethereum key tool), used for nothing else. Keep the key in
   `/etc/sniper/engine.env` with permissions 600, never in the repository, never on a phone.
4. **Funding, $300 plus about $20 of gas and bridge fees.** Buy ETH on any exchange you already use, withdraw it to
   **Arbitrum One or Base** (cheap withdrawals), then bridge to Robinhood Chain with a fast bridge that lists the chain
   (Relay, Across or LiFi: minutes, a few dollars) or with the canonical Arbitrum portal from Ethereum (about ten
   minutes, Ethereum gas). Bridge ETH, not only tokens: ETH is the gas token and the trade currency. Withdrawing from
   the chain back to Ethereum through the canonical bridge takes seven days; fast bridges are quicker.
5. **Clone the repository and run** `sudo bash deploy/ohio_setup.sh`. It installs chrony (the second boundary is the
   sequencer's clock), a Python environment, the engine as a systemd service in dry run, and the probe. Fill in
   `/etc/sniper/engine.env` (wallet address, RPC URL).
6. **Monitoring.** Two cron lines: one that alerts you (email or a Telegram bot message) if `engine.jsonl` has not
   grown in ten minutes, one that alerts if `chronyc tracking` reports an offset above 20 ms. systemd restarts the
   engine on any crash; the feed reconnect is handled in the engine and replayed backlogs are ignored.
7. **The send step**, after the dry-run days pass the checks in section 5: a function that signs the engine's
   transactions with the key and calls `eth_sendRawTransaction` on the provider endpoint with the sequencer as a second
   endpoint, returning the hash. About twenty lines with any standard Ethereum library.

Running cost: about $20–40 a month for the instance and nothing for the feed, the RPC free tier or chrony. Gas: about
$1 per trade, $0.50 per refused trade.

## 1. The trade

1. A Pons V2 creation appears on the sequencer feed (factory `0xe33e…`, selector `0xf85f8e41`); the engine recovers the
   creator and the quote asset from the calldata and resolves the curve from the factory's event.
2. Filters: creator's first launch of the UTC day, ETH quote, a usable launch-block buy.
3. The engine reads the creator's exempted wallets from the creation calldata, watches the feed for their buys inside the
   creation second (that address is the curve; at least `BUNDLE_MIN` = 3 of them must have bought, for at least
   `BUNDLE_MIN_ETH` = 0.3 ETH), requires the creator's own launch buy to be at least 1% of supply, and, at the second
   boundary, requires that **no wallet outside the named list bought the curve during second one** (`OUT1_MAX=0`;
   section 21.6: those are the bots that sell during our hold). Then it sends for the seat's second (`SEAT=E2`: two
   seconds after the creation's timestamp).
4. Buy 3% of supply or the stake, whichever is smaller (with a $300 stake the stake binds on three trades in four, so
   the trade is usually the whole stake, 1.5–2% of supply; with the $60 stakes of a $300 bankroll it is always the
   stake), sized on the curve **as the feed shows it at send time** (the
   creator's buy, the bundle and every later buy and sell applied to the exact curve), with the fee assumed at 5% +
   the seat's surcharge; `minOut` = sized tokens × (1 − `SLIP`, 25%), so a landing in the wrong second reverts for gas
   rather than paying 95%, and a price that ran more than 25% in the 0.3 s before we land refuses the trade (0.8–5.7%
   of trades, section 21.9).
5. Read the tokens received from the buy's Buy event; approve the curve at once; sell that balance 7 s after the buy
   landed, in one transaction.
6. Every rule-passing launch is scored 25 s after creation with the simulator's replay. The engine keeps trading unless
   the mean of the last 15 scores falls below −10% (a safety net: under the rule no switch was the best setting on every
   window, section 21.7). Daily stop at −50% of the day's starting bankroll (−30% fired on days that ended positive).
   One position at a time. Stake = 20% of bankroll, clamped $50–$300.

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

Off hours (bundled seat): Sep 3 00–06 UTC, 1,909 launches, about zero (−$311 switched at E2 0.3 s behind); Sep 3
18–24 UTC, 2,674 launches, +5.9% to +11.5% a trade, $2.5k to $11.6k switched; Sep 5 00–06 UTC, 842 launches, +2.6%
to +8.0%, $0.6k to $3.2k switched. The launchpad is busy around the clock; the switch, not the clock, decides when to
trade. Over the nine windows never used to choose anything, E2 0.3 s behind on bundled launches is positive on seven,
flat on two, negative on one (Sep 1, −$677), about +$13.4k switched in total over 54 hours.

Sum over the eleven windows (66 hours), switched and one position at a time: bundled seat $23.7k at the front and
$19.5k one block behind; every launch without the filter $38.0k at the front but $14.7k one block behind and $8.7k
three blocks behind (`data/derived/sniper_e2front.txt`).

Sep 2 and Sep 3 were the two busiest days of the fee cycle; Aug 30, Aug 31, Sep 1, Sep 4, Sep 5 and Sep 6 were never
used to choose anything: four of the six pay, Aug 30 and Sep 1 lose with the switch holding each to under $1,200. Aug 12 had no
bundled launches at all. More windows are appended to `data/derived/sniper_oos.txt` as they are pulled.

### 2b. With the section 21.6 rule, after the two audits (section 22)

E2 seat 0.3 s behind, 3% of supply, 7 s hold, minOut refusals included, corrected universe (`data/derived/sniper_plan.txt`):

| window | Aug 30 | Aug 31 | Sep 1 | Sep 2 | Sep 3 night | Sep 3 day | Sep 3 eve | Sep 4 | Sep 5 night | Sep 5 | Sep 6 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| launches kept in 6 h | 175 | 276 | 197 | 184 | 68 | 211 | 339 | 87 | 51 | 136 | 192 |
| mean ROI per trade | +3.7% | +4.1% | +1.8% | +12.8% | +14.0% | +14.1% | +12.2% | +13.8% | +9.9% | +18.6% | +5.4% |
| one at a time, $300 stakes | $1,433 | $3,041 | $1,264 | $5,742 | $2,685 | $8,299 | $11,291 | $3,136 | $1,487 | $7,491 | $1,919 |
| from $300, engine defaults | $559 | $1,853 | $344 | $4,053 | $1,221 | $6,456 | $9,430 | $1,754 | $633 | $5,962 | $609 |
| chance of the −50% stop (resampled) | 15% | 18% | 34% | 2% | 0% | 2% | 6% | 0% | 0% | 0% | 10% |

What to plan on, after two independent audits (section 22): the rule was chosen on these windows, so take +5% to +8%
per trade on a busy window as the planning number rather than the fitted +10% to +14%; the un-gated bundled seat is
+3.6% and is the floor; one other bot in the same seat roughly halves both. In money, from $300 at the engine's
sizing: +$100 to +$800 per busy six-hour window as the median outcome with a right tail to several thousand, −$150 to
+$100 per quiet window, and on flat days about one chance in three of ending at the −50% daily stop. Nothing has been
sent live; the first month's real fills are the information.

### 2c. With the round-15 rule (section 23): wait 0.3 s for a rival, hold 5 s, take-profit +50%, 15% sizing

E2 seat, send 0.3 s into second two only if no outsider has bought, 3% of supply, sell after 5 s or at +50%, minOut
refusals included (`data/derived/risk_harness.txt`):

| window | Aug 30 | Aug 31 | Sep 1 | Sep 2 | Sep 3 night | Sep 3 day | Sep 3 eve | Sep 4 | Sep 5 night | Sep 5 | Sep 6 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| launches kept in 6 h | 155 | 251 | 184 | 169 | 51 | 171 | 284 | 66 | 43 | 105 | 89 |
| mean ROI per trade | +8.9% | +9.7% | +8.7% | +16.1% | +16.6% | +20.9% | +18.0% | +9.5% | +16.0% | +16.3% | +7.6% |
| trades ending below −40% | 13% | 14% | 16% | 15% | 8% | 9% | 11% | 0% | 5% | 6% | 7% |
| one at a time, $300 stakes | $3,800 | $6,146 | $4,376 | $7,677 | $2,418 | $10,022 | $14,293 | $1,779 | $2,077 | $5,085 | $1,730 |
| from $300, engine defaults (15% / $25) | $1,497 | $3,717 | $1,805 | $5,693 | $894 | $7,658 | $12,367 | $632 | $728 | $2,722 | $571 |
| from $100, engine defaults | $395 | $1,301 | $505 | $3,520 | $340 | $5,279 | $9,983 | $216 | $258 | $901 | $148 |
| chance of the −50% stop from $300 (resampled) | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| chance of the −50% stop from $100 | 6% | 3% | 7% | 2% | 0% | 0% | 2% | 0% | 0% | 0% | 2% |

The hold and the take-profit were chosen on the first four windows and confirmed on the last seven (which are the
better half by +5.7 points); the 0.3 s wait was not tuned. Plan on +9% to +12% per trade. From $300: +$270 to
+$12,000 per six-hour window on the window's own ordering, median about +$1,500, no window below start, and a
resampled chance of the daily stop of zero. From $100: +$50 to +$10,000, median about +$400, stop odds at most 7%.
From $50 the $25 floor is half the bankroll and the stop is hit one time in five on the weaker windows: do not.

### 2d. September 7–10, ten windows the rule never saw (section 23.6)

Same rule, no change (`data/derived/risk_harness_sep.txt`):

| window | Sep 7 night | Sep 7 day | Sep 7 eve | Sep 8 night | Sep 8 day | Sep 8 eve | Sep 9 night | Sep 9 day | Sep 9 eve | Sep 10 night |
|---|---|---|---|---|---|---|---|---|---|---|
| launches kept in 6 h | 136 | 74 | 200 | 61 | 75 | 145 | 72 | 43 | 21 | 28 |
| mean ROI per trade | +9.3% | −0.6% | +5.8% | +12.5% | +3.2% | +5.0% | +6.3% | +7.4% | +1.5% | +15.1% |
| one at a time, $300 stakes | $3,589 | −$92 | $3,614 | $2,128 | $713 | $1,831 | $1,363 | $912 | $110 | $1,178 |
| from $300, engine defaults | $906 | $321 | $1,426 | $726 | $395 | $516 | $466 | $438 | $301 | $527 |
| chance of the −50% stop from $300 | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| chance of the stop from $100 | 5% | 98% | 8% | 1% | 7% | 22% | 2% | 0% | 0% | 0% |

Plan on +4% to +6% per trade and 20–200 trades per six hours: from $300, +$0 to +$1,100 per window, median about
+$200, gas included (the "from $300" row above is the end bankroll). The audit of these numbers (section 23.8) moved
the per-trade figure down: the other buyers' real slippage settings (59% none, the rest often tight) take 2 points
off the tables, and the gate's backtest calibration spans +6% to +8%. The flow is thinner because bots now buy in
second one on two thirds of bundled launches (the rule skips those) and a rival is in second two within 0.3 s on a
third of the rest. The seat they moved to, first in second one (E1 at the front), pays +8.7% a trade at this engine's
exit on 2,970 launches in these windows, +4% one block late, and +5% to +7% per attempt under realistic landing
mixes; an early landing is refused by the minOut (verified on a live curve). Whether a box in Ohio lands the first
block is a live question, and section 9 gives the test.

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

## 3b. The latency, in numbers (sections 21.5 and 23.4)

- Ordering is first come, first served at the sequencer; no priority fee, no express lane.
- With the round-15 rule the engine does not race for the first block. It waits for the feed to show second two, keeps
  watching the curve for 300 ms, and sends only if no outsider has bought; it lands in the fourth or fifth block of the
  second, 350–450 ms after the boundary, which is the tables' entry. What has to be fast is seeing: an outsider's buy in
  the first three blocks must be decoded and indexed before the send (engine v4: about 0.3 ms per feed frame, measured
  on a seven-minute capture, against 11 ms for v3 without coincurve), and the send itself must be one warm round trip
  (`SENDER` keeps the sockets to the sequencer and the provider open and logs their round trips every 100 s as
  `sender_rtt`; in Ohio expect a few milliseconds).
- The proof is in the log, not in the sandbox: `trade_decision` carries `seat_flip_to_send_ms` (should read about 300)
  and `wake_to_send_ms` (should read under 1), and every live `landing` carries the block's timestamp against the
  seat's second and the transaction's index in the block.
- `SEND_MODE=predict` with `MARGIN_MS` (start 15, floor 5), the interval-vote boundary estimator (`boundary` events log
  its confidence and bracket width; below 0.5 confidence the engine sends in react mode) and the margin controller stay
  for E1 or for an operator who wants to be first in the block; at E2 with the rule they are not needed. Run the probe once anyway (`deploy/ohio_setup.sh` installs it): a sequencer round trip above 10 ms or a
  bracket width far above one block (100 ms) means the box is in the wrong place or its clock is off.
- The engine refuses to start without a working coincurve when `REQUIRE_COINCURVE=1` (the setup sets it): without it
  every signature recovery costs 5 ms and the feed loop falls behind at busy times.

## 4. Configure

```
SEAT=E2 BUNDLE_MIN=3 BUNDLE_MIN_ETH=0.3 OUT1_MAX=0 OUT2_MAX=0 SEAT_WAIT_MS=300 MIN_CREATOR_SUPPLY=0.01 STOP_SELL_FRAC=0 SUPPLY_FRAC=0.03 SLIP=0.25 \
HOLD_S=5 TAKE_PROFIT=0.5 BANKROLL_USD=300 FRAC=0.15 STAKE_MIN=25 STAKE_MAX=300 SWITCH_N=15 SWITCH=-0.10 DAILY_STOP=0.50 MAX_RESOLVE_MS=1500 GAS_MAX_SHARE=0.05 \
TIER_ASSUMED=0.05 SEND_MODE=react MARGIN_MS=25 REQUIRE_COINCURVE=1 PIN_CPU=1 \
WALLET=0x… RPC_URL=https://… SEQ_URL=https://sequencer.mainnet.chain.robinhood.com FEED_URL=wss://feed.mainnet.chain.robinhood.com LOG_PATH=engine.jsonl \
python3 src/strategy/sniper_engine.py
```

`SEAT=E2` waits two seconds past the creation's timestamp (+0.19%); `SEAT=E1` waits one (+6.18%, in front of the
second-one bots, only worth it if your `sent_ms` is consistently first). `SEAT=E0` refuses to start without `EXEMPT=1`,
and `EXEMPT=1` is only true for a wallet the creator named. Do not set it. `SEAT_WAIT_MS=300` with `OUT2_MAX=0` is
the round-15 rule (send 0.3 s into the seat's second unless an outsider has bought); `TAKE_PROFIT=0.5` sells when the
curve price is 50% above the entry, `0` turns it off; `FRAC=0.2 STAKE_MIN=50` is the older, faster-compounding sizing
(stop odds at most 1% under the rule); `PIN_CPU` only on a box with two or more cores.

## 5. Dry run first, then the send step

Run the engine for a full day in dry run on the Ohio machine. It logs `creation`, `skip`, `eligible_not_traded` (with
the gate that stopped it, including `bundle N < 3` and `resolved in N ms`), `trade_decision` (seat, sent_ms, size,
tokens, minOut), `unsigned_tx` (buy, approve, sell) and `score` (the exact-curve outcome of every bundled launch, the
rolling mean, the switch state, and the dry-run bankroll). Go/no-go from that log:

- `resolve_src` is `feed` on bundled launches and `feed_resolution_ok` follows every one of them 25 s later
  (a `feed_resolution_mismatch` means the engine would have bought the wrong curve: stop);
- `seat_flip_to_send_ms` about 300 and `wake_to_send_ms` under 1 on every `trade_decision`, `sender_rtt` a few
  milliseconds to both endpoints, `sender_backend` `coincurve-direct` in the `start` line; otherwise the machine is in
  the wrong place or the environment is incomplete;
- `eligible_not_traded` with `outsider buys in the seat's second before our send` on some launches and not on most: the
  rival gate is reading the feed (about a quarter of bundled launches on the busy days);
- rolling mean of the scores positive over at least one full peak day, and the dry-run bankroll path matching the
  compounding table within its confidence interval;
- the switch turning on and off as the flow changes rather than sitting on.

The send step is yours: replace `submit()` with a function that signs with your key and calls
`eth_sendRawTransaction`, returning the hash. Sign the sell as soon as the buy's receipt is in (the engine builds it
with the next nonce) and keep a second endpoint to send it through if the first fails: a token held past the dump is
the one loss the tables do not contain. On the first live trade verify, from the receipt: the block's timestamp is the seat's second and `tx_index` puts you
in the fourth or fifth block of it (the engine's `landing` event says early / first block / later block; "early" at E2 means you paid the +6.18% of second one, and a revert
means the creation second); tokens received within `SLIP` of the engine's `tokens_target` (the event's `fee` field is
only the 1% protocol fee, the token's own 1–5% tax is a separate deduction, so compare tokens, not fees); the approve
landed before the hold ended; the sell moved exactly the balance. Then compare the first 30 live scores with the first 30 engine scores of the same
launches: they are computed the same way, and a gap is a latency or a seat problem, not a market problem.

## 6. Kill criteria

Stop for the day at −50%. Stop the strategy if the rolling mean of live outcomes over 30 trades is below zero while
the engine's scores for the same launches are above +5% (you are not getting the seat), if the measured surcharge is
ever above 6.18% on a next-second landing, or if the flow that pays is gone: the engine scores every rule-passing
launch (`score` events), so read two numbers each evening from the log: rule-passing launches in the last six hours
(under 40 means a thin window; September ran 21–200) and the mean score of the last 60 (under +3% does not cover gas
at $25 stakes; do not trade the next day until it is back above +5%).

## 7. Starting small

The tables charged $1 of gas per round trip; the receipts say $0.10 (section 23.7), and that changes the small start. At a
planning gas of $0.25: from **$100** the stop odds are 1.7% / 0.3% / 3.3% on the three halves of the data (20% on the
single thinnest September window), gains of $1.8k over the ten September windows; from **$300** 0% everywhere; from **$50**
12% / 3% / 16% (66% on the thinnest window): not advised. So $100 is the floor again, $300 is comfortable, and the
`GAS_MAX_SHARE=0.05` gate stops the small stakes by itself if gas ever climbs toward the old assumption.

## 8. What this is not

It is not the +30% a trade of sections 14 and 19; that is the launch team's seat. It is not proven out of sample: the
bundle filter was chosen on the five windows. It is not available from a phone or a Telegram bot. It is a peak-day,
Ohio-latency, five-second ride on other people's pumps, taken only when no faster bot is already in the seat, sized at
$25–$300 a trade, with a switch that keeps quiet days near zero and a stop that caps a bad one. The chain's terms of use have an automated-trading clause whose scope is
unclear; that is the operator's call.

## 9. What could kill it, and what you watch (section 23.7)

| killer | the sign in the log | what happens by itself | what you do |
|---|---|---|---|
| bots take the seat (already in motion) | `flow`: `rule_passing_last_6h` under 40, or `eligible_not_traded` mostly gated by `outsider buys in the seat's second` | the rule skips those launches | run the E1 test below; if it lands the first block, switch seats |
| the exit is wrong for the regime | `flow`: `median_first_sell_s` well past 7 s while the take-profit rarely fires (`trade_done` with `exit: hold`) | nothing | `HOLD_S=7` earned +8.6% instead of +6.2% on Sep 7–10 at a tail of 11.6% instead of 7.7%; over all 21 windows holds of 5, 6 and 7 with the take-profit are within a point of each other |
| the other buyers tighten their slippage | not visible in the log (their minimum is in their calldata) | nothing | the replay says −2 to −3 points per trade if they do (section 23.8); re-read the sample with `src/collect/chain_checks_slippage.py` monthly |
| teams dump earlier | `flow`: `median_first_sell_s` falling toward the hold, `share_dumped_inside_hold` rising | nothing | shorten `HOLD_S` to 3 (+3.6% on September instead of +6%) or stop |
| teams plant a dust buy in second one to trip the gate | many `outsider buys in second one` gates with tiny `bundle_eth`-sized buys in the scored launches | nothing | set `OUT1_MIN_ETH=0.01` (dust below it no longer counts) |
| the tax schedule or the exemption changes | `alarm: tax schedule changed` (half of the last 20 scored launches show surcharges outside the three bands) | trading stops until restart | read the curve's getters (`0x24a9d853` tax, `0xc57eadfc` reserves); the rule is dead until the new schedule is measured |
| the launchpad moves or stops | `alarm: no creation seen from the factory for 30 minutes` on a live feed | nothing to trade | find the new factory address (a new creation selector or contract), or stop |
| ordering changes (a priority lane, a different sequencer) | `landing` events with `where: early` or `later block` on every trade while `seat_flip_to_send_ms` reads 300 | the margin controller moves, the stop caps the loss | stop; the seat depends on first-come ordering |
| gas | `eligible_not_traded` with `gas $… per round trip > 5% of stake` | the small stakes stop trading by themselves | wait, or raise the bankroll (gas is $0.10 today, the gate allows $1.25 on a $25 stake) |
| your send step | `sent_tx` answers that are errors, `buy_reverted`, `receipt_timeout` | an open position is closed on restart | the reference below is tested; do not improvise on it at the boundary |
| the terms of use | nothing in the log | nothing | your call; it is flagged, not resolved |

**The send step, tested.** This is the whole of what replaces `submit()`; it was run against the engine's own transaction
with a throwaway key, and the sequencer's only complaint was that the key had no funds:

```python
from eth_account import Account
KEY = Account.from_key(os.environ["PRIVATE_KEY"])          # the key lives in /etc/sniper/engine.env, mode 600, nowhere else

def submit(tx, label):
    signed = KEY.sign_transaction(tx)                       # tx is exactly as the engine builds it: checksummed to, hex fields
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_sendRawTransaction",
                       "params": ["0x" + bytes(signed.raw_transaction).hex()]}).encode()
    result, answers = SENDER.fire(body)                     # the warm sockets: sequencer first, provider second, same hash
    log({"ev": "sent_tx", "label": label, "hash": result, "answers": [(h, str(d)[:120]) for h, d in answers]})
    return result
```

Two things this round found by running it: `eth_gasPrice` on this chain is the base fee itself, and a transaction sent at
exactly that price is refused the moment the fee ticks up (`GAS_HEADROOM=2` fixes it, about five cents a trade); and
`eth_account` refuses lowercase addresses (fixed in round 15). Both would have lost the first live buy.

**The E1 test, before any capital goes to that seat.** Set `SEAT=E1 SEND_MODE=predict MARGIN_MS=15 STAKE_MIN=5 STAKE_MAX=10
FRAC=0.02` with $50 in the wallet and the send step live, and let it take thirty bundled launches (a busy window). Read the
`landing` events: `where` (early = the creation second, refused for gas; first block; later block) and `tx_index`. If
twenty-five or more of thirty land in the first block and the live outcomes track the engine's E1 scores, the seat is real
for this box and `SEAT=E1 HOLD_S=7` at normal sizing is the plan when `flow` shows second-one occupancy above 45%; if
fewer than twenty do, stay at E2. The cost of the test is about $2 a launch in gas and surcharge, $60 in all.

