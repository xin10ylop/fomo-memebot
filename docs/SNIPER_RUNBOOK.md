# Sniper runbook, version 2 (after the round-12 audit)

Read report section 20 first. Version 1 of this runbook described a seat that an outside wallet cannot take. This version
describes what an outside wallet can do, what it earns on the exact curve, and what must be true before a single
dollar is sent.

## 0. What changed

**v3.1 (report section 23.11): why September pays less, and the two readouts.** The return of a kept launch, taken
apart on the exact curve, is the same fees and the same dumps as before with 28% less ETH from the buyers who come
after you; that is the whole drop in return per trade, and it moves with the hour (September's US-morning hours +3%,
its nights +10%) and the day. The bots in second one do not lower a kept launch's return; they take the launches
(clean launches 67% → 29% of bundled ones). Sizing to a live demand gauge, reacting to dumps and changing the exit
were tried and rejected. What is left: 20% sizing once live scores match the tables (September stop odds 0.5%), and
the E1 seat when second one is crowded (section 9). The `flow` event now prints the demand (`follow_eth_last_20`,
`follow_eth_last_60`: ETH later buyers brought while a scored launch was held) and the crowding (`out1_share_last_60`:
share of the last sixty bundled launches with an outsider in second one). Nothing the engine sends has changed. `src/analysis/live_check.py` compares the live receipts with the engine's
scores of the same launches (section 5); the send step is now a file the engine loads (`SEND_MODULE`, `deploy/send_step.py`)
instead of an edit, and live the bankroll is the wallet's balance. `docs/STEP_BY_STEP.md` is the operator's checklist.

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
6b. **Posture.** Decide which endpoints you use (section 23.10). A: Robinhood's sequencer feed for detection and the
   sequencer for sending, the defaults: the fastest path and the only one that can take the E1 seat, and it uses
   Robinhood's "Services", whose terms list automated tools under prohibited network abuse and limit the Services to
   testing and development. B: your provider's WebSocket and RPC only (`FEED_SOURCE=provider`,
   `PROVIDER_WS=wss://robinhood-mainnet.g.alchemy.com/v2/KEY`, `SEQ_URL=` empty), which touches no Robinhood endpoint;
   on the replay it costs about a tenth of the trades at the same return per trade. Under B, dry-run a full day first:
   the provider path was tested only against a synthetic node. **Recommended: A with B as the fallback.** Set
   `PROVIDER_WS` even under A: if Robinhood's feed ever refuses the box (five HTTP refusals in a row) the engine
   switches detection to the provider by itself and logs an `alarm`; the send already goes to both the sequencer and
   the provider, so a refused sequencer costs nothing. The worst the terms can do to A is exactly that refusal.
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
better half by +5.7 points); the 0.3 s wait was not tuned. Re-run on dense block anchors after the audit (section 23.8)
the two halves read +10.3% and +15.4% per trade, one-at-a-time $20.0k and $33.3k, stop odds unchanged at zero; single
windows move by up to four points (Sep 4 +6.1%, Sep 5 +18.9%, Sep 6 +5.3%). Plan on +9% to +12% per trade. From $300: +$270 to
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

**Where the sequencer is, verified on Sep 10.** `sequencer.mainnet.chain.robinhood.com` resolves to three addresses
(3.136.74.196, 3.141.111.43, 3.142.9.34); all three are inside Amazon's published `us-east-2` EC2 ranges
(`ip-ranges.amazonaws.com`), one per availability zone, behind an Envoy front (`server: istio-envoy`). The feed and the
public RPC resolve to Cloudflare (104.20.46.209, 172.66.147.70); the sequencer host refuses WebSocket upgrades and the
Nitro feed ports (9642, 8547) are closed on all three addresses, so there is no feed path that bypasses Cloudflare.
Ordering is first-come-first-served with no priority fee. That fixes the machine:

- **Region: us-east-2 (Ohio), and nothing else.** The sequencer is a cloud service, not a colocation venue: an
  instance in its own region reaches it over Amazon's backbone in about a millisecond, and no bare-metal, other-cloud
  or other-region option can beat that; anything outside the region adds 10–80 ms, which section 20.8 showed puts the
  engine in the losing bucket. The one improvement left is the **zone**: cross-zone round trips are 0.5–1 ms, same-zone
  0.1–0.3 ms. The engine measures the three sequencer addresses at start and every 20 minutes (`sender_addresses`),
  pins its socket to the fastest and logs which; a box in the sequencer's own zone will see one address well under the
  other two. To choose the zone, run the probe or the dry run for ten minutes on a t3.micro in each of us-east-2a, 2b
  and 2c and keep the zone whose best address reads lowest (a $1 experiment); if all three read alike, the zone does
  not matter and any is fine.
- **Instance:** c6i.large or c7i.large (two dedicated cores, no CPU credits, enhanced networking) for live; t3.small is
  fine for the dry run. `PIN_CPU=1` keeps the engine off the core that takes the network interrupts.
- **Network:** IPv4, the default VPC, no NAT instance in the path (a NAT gateway adds a hop), the sequencer reached by
  address with TCP_NODELAY and a warm TLS session (done by the engine), `tcp_slow_start_after_idle` off (the setup script
  sets it). The feed goes through the Cloudflare edge nearest the box (Columbus for an Ohio instance); nothing you do
  changes that path.
- **Clock:** chrony on Amazon Time Sync (`169.254.169.123`), stepping only at boot, slewing after; the engine times
  everything on the monotonic clock, so a step during a trade cannot move a send.
- **Provider RPC:** a key from Alchemy, QuickNode or Chainstack for the nonce, receipts and scoring; it is not on the
  buy path (the curve is resolved from the feed) and its own latency only matters as the second send endpoint.

With the round-15 rule the send is a fixed 300 ms after the seat's second opens, so the last millisecond does not
decide the E2 trade; it decides the E1 test (section 9), and that is where the zone choice and the pinned address earn
their keep.

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

`FEED_SOURCE=provider` with `PROVIDER_WS=wss://…` replaces the sequencer feed by a third-party node's subscriptions
(posture B above). `SEAT=E2` waits two seconds past the creation's timestamp (+0.19%); `SEAT=E1` waits one (+6.18%, in front of the
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
- the switch turning on and off as the flow changes rather than sitting on;
- the `flow` event every five minutes: `follow_eth_last_60` between 0.2 and 0.5 ETH on a normal day (under 0.2 means
  +3% to +4% a trade, section 23.11) and `out1_share_last_60` about 0.6 in September (above 0.55 is the crowded regime
  where the E1 seat pays, section 9).

**The live check, one command.** Once the send step returns hashes, every `trade_done` carries the buy, approve and
sell hashes, and `python3 src/analysis/live_check.py engine.jsonl` pulls the receipts and prints, per trade, where the
buy landed (first block / later block of the seat's second, or EARLY / LATE), its index in the block, ETH in and tokens
out from the buy's own event, tokens against the engine's target, the share the sell moved, ETH out, gas, the live
return, and the engine's exact-curve score of the same launch next to it; then the mean gap over all trades with a
bootstrap interval and a verdict. It was exercised on real receipts from the chain (a stranger's buy and sell on one
curve: +4.6% live, gas 0.00004 ETH, sell moved 100%). Ten compared trades are the minimum for the verdict; thirty is the
plan. A gap whose interval excludes zero is the box or the seat (latency, landing, slippage), never the market, because
both numbers are computed on the same launches. Send the log and the checker's output when you want them read.

The send step is yours, and it is one file: `deploy/send_step.py` (the tested code of section 9). Copy it to
`/etc/sniper/send_step.py`, set `SEND_MODULE=/etc/sniper/send_step.py` and the wallet's private key in `engine.env`,
restart. The engine loads it at start (`send_step_loaded` in the log, `"dry_run": false` in the start line), refuses to
start if the key does not match `WALLET`, and from then on sizes from the wallet's real ETH balance (`flow`:
`wallet_eth`, `bankroll_usd`), so every profit is staked again and the daily stop reads real money. Without the file
the engine is the dry run it always was; nothing in the repository signs or sends. `docs/STEP_BY_STEP.md` walks the
whole thing. The engine signs the sell as soon as the buy's receipt is in (it builds it
with the next nonce) and keep a second endpoint to send it through if the first fails: a token held past the dump is
the one loss the tables do not contain. On the first live trade verify, from the receipt: the block's timestamp is the seat's second and `tx_index` puts you
in the fourth or fifth block of it (the engine's `landing` event says early / first block / later block; "early" at E2 means you paid the +6.18% of second one, and a revert
means the creation second); tokens received within `SLIP` of the engine's `tokens_target` (the event's `fee` field is
only the 1% protocol fee, the token's own 1–5% tax is a separate deduction, so compare tokens, not fees); the approve
landed before the hold ended; the sell moved exactly the balance. Then compare the first 30 live scores with the first 30 engine scores of the same
launches: they are computed the same way, and a gap is a latency or a seat problem, not a market problem.

## 5b. Before every live start

Run `sudo sh deploy/preflight.sh` on the machine. It prints one line per check and a verdict: the settings as they will
be used, whether the key matches `WALLET`, the file modes, whether the feed is delivering, the round trip to each node,
the wallet's balance, the clock offset, disk, the watchdog, and the signature backend. Do not set `SEND_MODULE` until it
says PREFLIGHT PASSED. The launch filter it should show (round 16): `BUNDLE_MIN=5`, `BUNDLE_MIN_ETH=0.3`,
`BUNDLE_MAX_ETH=1.2`, `MIN_CREATOR_SUPPLY=0.03`, `TRADE_HOURS=12-05`, `STAKE_MAX=25` until five receipts check out.

## 5c. What the engine asks the provider, and what it costs

Engine 5.0 keeps the provider traffic small: the sequencer feed (Robinhood's, free) carries every block; the provider
socket carries only the Buy events of the curves being watched (one subscription per curve, a few at a time, dropped
after 180 s), and the HTTP side does the nonce, the balance every 30 s, the receipts, and the factory lookup for a
launch the feed could not resolve. That is thousands of requests a day, not millions. If a provider's dashboard shows
millions, something is subscribed to the whole chain again (engine 4.95–4.99 did this: every Buy and every head,
1.7 million messages a day) — check the version on the start line, and that exactly one engine runs:

    grep '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); print("version", d["version"], "chain_rivals", d["chain_rivals"])'
    pgrep -af sniper_engine.py | grep -v pgrep          # exactly one line
    ss -tnp state established | grep -c python           # its sockets: feed, sequencer, RPCs — under ten

`PROVIDER_WS=` (empty) switches the chain rivals off altogether; the feed decoder's token matching still covers the
router blind spot that made trade 6.

## 5d. The creation-second seat is closed to outsiders (engine 5.51, report 24.19)

The seat of engines 5.3–5.5 (0.2–0.4 s after the creation block at "6.18%") does not exist for a wallet that is not on
the creation's named list. The snipe tax is keyed to the block's clock second, not to the block offset: a buy in any block
that carries the creation block's timestamp pays ~98%, and the 6.18% surcharge starts with the first block of the next
second. Report 24.13 measured time in block offsets (0.1 s a block) and mistook next-second buys at small offsets for
creation-second buys. The first live trade (Sep 18 09:43 UTC, $10) landed three blocks after the creation at index 1,
was offered 1.1% of the fair tokens, and reverted on its minOut: cost, the gas. With real timestamps every one of the
1,547 outsider buys at 6.2% on Sep 18 sat in a later second, and every same-second outsider buy paid 98%.

The engine refuses `SEAT=E0` without `EXEMPT=1` (the round-12 guard, back); `E0_OUTSIDER` no longer opts in.

The next-second seat, scored honestly (E1, real second boundaries, >= 3 named wallets, bundle >= 0.3 ETH in the creation
second, tier 2–3%, hold 1.5 s; `data/derived/e1_honest_0918.txt`, `src/analysis/e1_honest.py`): +8% a trade (median +1%,
54% win, no dead) if our buy is the FIRST in the next second's first block, −4.6% (median −10%, 20% win) if it lands after
the two or three bots that queue for that block; two days earlier +20% first, +5% last. The landing position is the whole
edge, and paper cannot measure it: only a real send can. Paper E1 (the engine's original boundary-timed seat) runs with

    SEAT=E1 SEND_MODE=predict MARGIN_MS=15 HOLD_S=1.5 TAKE_PROFIT=0 TIER_MIN_BPS=100 TIER_MAX_BPS=200 BUNDLE_MIN=3
    BUNDLE_MIN_ETH=0.3 BUNDLE_MAX_ETH=0 MIN_CREATOR_SUPPLY=0.01 MIN_FOLLOW_ETH_60=0 MAX_RESOLVE_MS=600 SEND_MODULE=
    E0_BUNDLE_WAIT_S=0.9 E0_BUNDLE_MAX_BLOCKS=9

(engine 5.52: the E1 and E2 seats resolve the curve and count the bundle exactly as the creation-second path does, from the
creation receipt and the helper calls' calldata, so a single-transaction bundle is seen before the boundary; before 5.52
the next-second path waited for direct named buys and only resolved the curve when the next second opened on the feed, too
late for a predict-mode send. The bundle window is the whole creation second: `E0_BUNDLE_WAIT_S=0.9`, nine blocks.)

and records the boundary estimate and the send timing. On a paper box add `CHAIN_POLL_S=10 RECEIPT_POLL_MS=40` (engine
5.53): the bookkeeping poll and the receipt poll are the engine's steady provider usage. A landing test is a decision, not a default: section 9's E1 test
(`MAX_LIVE_TRADES=3` at $10 with the send step), then `src/analysis/live_check.py` and the receipt's index against the
other buys of its block. First every time, the seat pays +8–20%; behind the bots, it pays nothing and the strategy stops.

## 5e. Five days on the true clock, the burst send, and the landing test (engine 5.6, report 24.20)

Five days with real second boundaries (Sep 13–18, 740 launches, `data/derived/e1_five_days_0918.txt`): the next-second seat
pays **+16.1% a trade first in its block** (+3.7% median, 56% win, 1% dead, 148 launches a day, about $5,900 a day at $250
stakes), +3.7% behind the block's other buys, +0.8% one block late; the second-two seat is dead (+0.6% first, −2.7%
behind). The value is the crowd: alone in the block −3.2%, first ahead of one bot +5%, ahead of two or more +19% to +49%,
and behind a big crowd still +6.8%. Bundles under 0.5 ETH draw fewer bots and pay +8.7% first, nothing behind. Hold 1.5 s
and 3 s score alike; 6 s and a +50% take-profit score worse. 02:00–04:00 UTC is the one negative stretch (small sample).
The 1% tier class (tax under 100 bps), scored the same way on Sep 16–18 (257 launches), is dead: −0.0% first, −1.2% behind,
33% win, bots leave half of them alone; `TIER_MIN_BPS=100` stays. On Sep 18 13:00–14:00 UTC nearly every bundle seen in
time was one of these, so a slow hour on the 2–3% band is the gate working, not a fault.

**The burst.** `BURST_N` shots at consecutive nonces, `BURST_STEP_MS` apart, the first `BURST_LEAD_MS` before the predicted
boundary (predict mode only; the sender keeps one warm socket per shot to the sequencer; the send step signs all shots
first). A shot that reaches the sequencer before the tick lands in the creation second and reverts on its minOut for the
gas, about $0.008; the first past the tick fills; the later ones must revert on the same minOut once our own fill has moved
the price. So `BURST_SLIP` sits just below our own impact and no lower: at $250 (3% of supply) a second identical shot
gets about 8% fewer tokens, so 7%; at $100 about 3.4%, so 3%. Any looser and a second shot fills; any tighter and a fill
behind a crowd that still pays is thrown away (5% throws away two thirds of the +6.8%). The engine notes on the decision
when the stake is too small for the guard. Needs the burst-capable send step: `sudo cp deploy/send_step.py
/etc/sniper/send_step.py`.

**The landing test**, on the Ohio box (`deploy/ohio_setup.sh`, section 3; the New York droplet is 14 ms away one way, the
losing bucket of section 20.8), after an hour of paper there to fill the boundary estimator:

    SEAT=E1 SEND_MODE=predict MARGIN_MS=0 BURST_N=5 BURST_STEP_MS=3 BURST_LEAD_MS=8 BURST_SLIP=0.03
    STAKE_MIN=100 STAKE_MAX=100 MAX_LIVE_TRADES=10 HOLD_S=1.5 TAKE_PROFIT=0 TIER_MIN_BPS=100 TIER_MAX_BPS=200
    BUNDLE_MIN=3 BUNDLE_MIN_ETH=0.5 BUNDLE_MAX_ETH=0 MIN_CREATOR_SUPPLY=0.01 E0_BUNDLE_WAIT_S=0.9 E0_BUNDLE_MAX_BLOCKS=9
    SEND_MODULE=/etc/sniper/send_step.py

**Calibrating the lead (engine 5.61).** The first three live bursts from New York (Sep 18 13:50–13:57 UTC, $10, 1% tier
tokens, five shots each) all landed in the SECOND block of the new second, every shot in the same block: the margin came
back as 25 ms from the saved state, 26 ms passed between the boundary wake and the first shot (gates, sizing, build and
signing ran after the wait on a one-core box), and the boundary estimate is in feed-arrival time while the feed trails
the sequencer's tick by 50–150 ms. 5.61 builds and signs the shots before the boundary and fires them on the estimate
(`send_mode predict-prebuilt`, `prebuilt_ms` on the decision), keeps the env's `MARGIN_MS` in burst mode (the lead is the
knob, the margin is not tuned), and adds `deploy/feed_lag_probe.py` (run with the engine's interpreter, two minutes: the
p5–p10 of flip arrival minus its second is the feed's lag on the box). The calibration burst, three launches at $5:

    BURST_N=12 BURST_STEP_MS=10 BURST_LEAD_MS=120 MARGIN_MS=0 STAKE_MIN=5 STAKE_MAX=5 MAX_LIVE_TRADES=3 TIER_MIN_BPS=0

spans 120 to 10 ms before the estimate; the first filled shot's index gives the true lead for the box (shot k filled first:
lead = 120 − 10k ms puts the first shot on the tick), and the next run narrows to five shots 4 ms apart around it.
Measured (report 24.21): the tick sits about 150 ms before the estimate on the New York droplet (feed lag 67–73 ms, 10 ms
to the sequencer) and 170–180 ms on the Ohio c6i.large (feed lag 81–93 ms, 1 ms to the sequencer). The production shape
on Ohio, from the first calibration burst there (index 2 of the first block, about twenty transactions behind within 10 ms):

    BURST_N=9 BURST_STEP_MS=3 BURST_LEAD_MS=184 BURST_SLIP=0.03 MARGIN_MS=0 STAKE_MIN=20 STAKE_MAX=20 MAX_LIVE_TRADES=5
    TIER_MIN_BPS=100 BUNDLE_MIN_ETH=0.5

Re-run the calibration burst whenever the box, the region or the feed route changes: the lead is a property of the box.

**The slot model (engine 5.7).** `deploy/grid_probe.py` showed the sequencer creates a block every ~101.6 ms on a steady timer:
the first block of each second walks forward 16 ms a second in a clean sawtooth, and what jitters is the feed's delivery,
about 30 ms a block. The flip vote averages one noisy point a second; the slot model folds every block's wall-clock arrival
on the slot grid (period searched 101.2–102.0 ms, phase as the circular mean of 900 arrivals) and predicts the arrival of a
second's first block as the first slot whose creation (arrival minus `FEED_LAG_MS`, the probe's p5–p10) is at or after
the second. It scores itself on every flip without a send: `slot_shadow` every 30 flips, the slot model's and the vote's
error on the flip's arrival (`abs_median` is the number; the slot model should read a few ms, the vote tens). Once that
holds, `SLOT_SEND=1` aims the burst at the prediction minus `SLOT_LEAD_MS` (the feed's lag plus the block's window; the
first calibration burst under the slot model is 13 shots 10 ms apart from `SLOT_LEAD_MS=200`, `BURST_LEAD_MS=0`), and
every landing then logs `flip_minus_first_fill_ms`, the constant that sets `SLOT_LEAD_MS` for a narrow burst.

Ten launches; then `ALCHEMY_KEY=... python3 src/analysis/landing_check.py --log /var/log/sniper/engine.jsonl`: every
included shot with its block, second, index and the other buys before and after it. The number that decides: the share of
contested launches whose filled shot is first in the next second's first block. Above three in four, production at $250 with
`BURST_SLIP=0.07`, `STAKE_MAX=250`, `MAX_LIVE_TRADES` off, `BUNDLE_MIN_ETH=0.5` (add the 0.3–0.5 ETH bundles only if the
landing share stays high: they pay +8.7% first and nothing behind). Around half, the seat pays about +8% a trade and is
worth running with the same care. Below one in four, it pays nothing and the strategy stops there.

### 5f. One fill per launch: the wallet is the stake (engine 5.93)

The night of Sep 18 (report 24.24): at $15 the 3% guard cannot see our own fill, so every shot of the burst after the
first one also filled, until the wallet could not fund one more; the bet was the whole wallet on every launch that filled,
and one launch at −56% took $42. Engine 5.93 makes the sequencer's insufficient-funds drop the cap: live, every buy is
the wallet less a gas reserve (`WALLET_STAKE=1`, the default; `GAS_RESERVE_USD=2.5` or the burst's reverts plus the exit's
fee ceiling, whichever is more), so a second shot can never be funded, whatever the guard sees.

The operating rule: **what sits in the wallet is what one launch can lose, plus about $3 of gas.** `STAKE_MAX` is the most
the wallet may hold; above it the engine refuses every launch and logs "withdraw the excess or raise STAKE_MAX"; below
`STAKE_MIN` it logs "top up". Profits accumulate in the wallet, so a run of wins walks the stake up until the ceiling
stops it: withdraw down to the stake (Phantom) or raise the ceiling. A balance older than a minute refuses (read every
10 s when idle and after every landing and exit). A launch on which the 3% supply cap would make the buy less than half
the wallet is skipped: the remainder could fund a second fill. The hold clock now starts at the fill (`fill_seen_ms`),
so `HOLD_S=1.3` lands the sell about 15 blocks after the buy, the tables' exit; the 5.92 sells landed at 31–36 blocks.

    WALLET_STAKE=1 STAKE_MIN=8 STAKE_MAX=60 HOLD_S=1.3 BURST_SLIP=0.25   # the wallet holds $8-60: every launch bets what is there

`BURST_SLIP` goes back to the engine's ordinary 25%: the 3% guard existed to stop the burst's own second fill, which the
wallet now does, and it was refusing the seat itself (four of the night's bursts sat first on the curve in the seat block
and reverted on the minOut: the bundle's tax-free buys in the creation second's last blocks move the quote past 3%
between the build and the block). The tables' minOut test: 3% keeps +0.4% of the +6.8% behind the crowd, 25% keeps +5.6%.

After any run, the accounting of every hash the engine sent since its start, reconciled against the wallet:

    sudo python3 src/analysis/night_readout.py --start-eth <wallet ETH at the start>

It prints, per launch, the shots by block (creation second, seat, later), the buys on the curve ahead of our first shot,
the fills, ETH in and out, gas, net, the exit and the blocks held; for a multi-fill, the first fill's own return; totals;
alarms; the open position; and the part of the wallet's change the receipts do not explain (it should be cents).

### 5g. The BuyOnce relay: any bet with any wallet (engine 5.94)

`contracts/BuyOnce.sol` is a relay owned by the wallet that buys at most once per curve and sends the tokens to the
wallet; with it the burst's extra shots revert on the relay's flag instead of buying, whatever the wallet holds
(report 24.25). Deploy it once from the machine, with the engine stopped:

    sudo systemctl stop sniper-engine
    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_deploy.py

The script checks the artifact against the source, shows the cost (a few cents), asks for a yes, deploys, verifies the
code on the chain byte for byte and `owner()` against the wallet, simulates one buy through the relay, and prints the
`RELAY=0x...` line. Put that line in `/etc/sniper/engine.env`, set `STAKE_MIN`/`STAKE_MAX` to the bet, and restart. The
engine refuses to start on a relay that has no code or is not owned by the wallet. `WALLET_STAKE` turns off by itself
when `RELAY` is set (the wallet may then hold many stakes); `BURST_SLIP` stays at 25%.

    RELAY=0x... STAKE_MIN=15 STAKE_MAX=15 HOLD_S=1.3 BURST_SLIP=0.25   # $15 a launch, the wallet holds whatever you like

If the readout ever shows two fills on one launch with the relay in place, stop the engine: the alarm says "THROUGH THE
RELAY" and the contract, not the stake, is what to look at. `sweep(address)` on the relay (token, or 0 for ETH) returns
anything that ended up in it to the wallet.

Engine 5.95 fixed the approve's nonce (it was the second shot's, refused since the burst; the exit re-approved a second
later), and the readout nets the curve's two sell fees from the Sell event's ETH out, which is gross.

Engine 5.96 and the second relay: `buy` takes the seat's clock second as a deadline and reverts (`TooLate`) in any later
block, so a burst the sequencer includes late (a one-second stall on Sep 19) costs gas instead of a dead seat. The engine
refuses to start on the first relay (no deadline): redeploy with the same command (engine stopped, `--write-env`), a few
cents; the old relay stays on the chain unused. `RELAY_DEADLINE=0` sends no deadline (a test setting only).
Engine 5.97: a shot whose socket the sequencer closed is re-fired once; the approve and the sell follow the last shot the
chain took (`burst_dropped` in the log names the lost ones and the sequencer's answers); the readout shows the Sell
event's ETH out as the wallet receives it (gross; the fee words are already taken out).

### 5h. Shooters: one wallet per shot (engine 6.0, third relay)

Why: one wallet's consecutive nonces fired on parallel sockets are refused as "nonce too high" when the sequencer is
under load (report 24.26). Every shot now comes from its own shooter wallet (gas only) and the relay buys with the
stake it holds. Set up once, engine stopped, on the machine (each command prints what it did):

    sudo systemctl stop sniper-engine
    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_deploy.py --write-env      # the third relay
    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_ops.py shooters-create 35   # 35 keys into engine.env
    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_ops.py shooters-register    # one transaction
    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_ops.py shooters-fund --yes  # 0.0001 ETH of gas each
    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_ops.py deposit 0.007        # the stake, 1.2 x $15 at $2,600
    sudo cp ~/fomo-memebot/deploy/send_step.py /etc/sniper/send_step.py                       # signs each shot with its shooter
    sudo systemctl restart sniper-engine

`relay_ops.py status` (read-only, engine running or not) lists the wallet, the relay's ETH, every shooter's gas and
registration. The engine refills shooters below 0.00004 ETH and the relay to 1.2 stakes after each exit, from the
wallet; it logs an alarm when the wallet cannot. `withdraw all` brings the relay's ETH back, `shooters-sweep` the
shooters' gas. The start refuses to run with an older relay, an unregistered shooter, `BURST_N` above the number of
shooters, or the old send step.

Aim (Sep 19, five bursts under the shooters): the seat's block opened at shot 28-33 of 35, once after shot 35 (no fill), so
the window sat 85 ms early; `SLOT_LEAD_MS=50` (from 100) centres it. The readout's `window:` line shows the shot the
block opened at; keep it near the middle of the burst.

### 5i. The daily check: the tables' script on the last 24 hours

The engine's score line and the tables' script must agree; the script is the reference (real second boundaries, the
chain). Once a day, on any machine with the public RPC (about 15 minutes for 24 hours):

    mkdir -p data/derived/e1_today && python3 src/analysis/e1_multi.py 12 0 data/derived/e1_today/e1m_a.json 0.02 0.03 && python3 src/analysis/e1_multi.py 12 12 data/derived/e1_today/e1m_b.json 0.02 0.03 && python3 src/analysis/e1_agg.py data/derived/e1_today | head -8

Read `E1 first` (mean, win) and `E1 last`. Sep 18-19: +9.3% and 51% over 141 launches (report 24.27). Trade while the
front seat's mean over a day is above about +3% (the fees and the misses eat the rest); stop when a day reads below zero
and the next day confirms it. Delete the folder before the next day's run (the script skips a file that exists).

## 6. Kill criteria

Stop for the day at −50%. Stop the strategy if the rolling mean of live outcomes over 30 trades is below zero while
the engine's scores for the same launches are above +5% (you are not getting the seat), if the measured surcharge is
ever above 6.18% on a next-second landing, or if the flow that pays is gone: the engine scores every rule-passing
launch (`score` events), so read two numbers each evening from the log: rule-passing launches in the last six hours
(under 40 means a thin window; September ran 21–200) and the mean score of the last 60 (under +3% does not cover gas
at $25 stakes; do not trade the next day until it is back above +5%). The `flow` event's `follow_eth_last_60` is the
reason behind the second number: it is the ETH later buyers put in while a scored launch was held, 0.36 on the days
that paid +11% to +16%, 0.26 on the September days that paid +6%, 0.17 on the one window that paid nothing. It is a
regime readout, not a per-trade signal (section 23.11): do not size to it.

## 7. Starting small

The tables charged $1 of gas per round trip; the receipts say $0.10 (section 23.7), and that changes the small start. At a
planning gas of $0.25: from **$100** the stop odds are 1.7% / 0.3% / 3.3% on the three halves of the data (20% on the
single thinnest September window), gains of $1.8k over the ten September windows; from **$300** 0% everywhere; from **$50**
12% / 3% / 16% (66% on the thinnest window): not advised. So $100 is the floor again, $300 is comfortable, and the
`GAS_MAX_SHARE=0.05` gate stops the small stakes by itself if gas ever climbs toward the old assumption.

One correction to every trade count quoted from the replay (section 24.8): the replay's clock is interpolated, and on
the exact clock only about two thirds of its "clean" launches are clean — the engine, which watches the real feed, sends
on fewer launches than the replay counts. Read the replay's trades per day and dollars per day at two thirds; the return
per trade, the filter and the hours are unchanged.

## 8. What this is not

It is not the +30% a trade of sections 14 and 19; that is the launch team's seat. It is not proven out of sample: the
bundle filter was chosen on the five windows. It is not available from a phone or a Telegram bot. It is a peak-day,
Ohio-latency, five-second ride on other people's pumps, taken only when no faster bot is already in the seat, sized at
$25–$300 a trade, with a switch that keeps quiet days near zero and a stop that caps a bad one. The chain's terms of use have an automated-trading clause whose scope is
unclear; that is the operator's call.

## 9. What could kill it, and what you watch (section 23.7)

| killer | the sign in the log | what happens by itself | what you do |
|---|---|---|---|
| bots take the seat (already in motion) | `flow`: `out1_share_last_60` above 0.55, `rule_passing_last_6h` under 40, or `eligible_not_traded` mostly gated by `outsider buys in the seat's second` | the rule skips those launches (September: two thirds of bundled launches) | run the E1 test below; if it lands the first block on most attempts, run `SEAT=E1` at `FRAC=0.10` while `out1_share_last_60` is above 0.55 and E2 otherwise: at the front E1 pays +8.7% a trade on every bundled launch of the ten September windows ($39.5k from $300 against $3.3k at E2, stop odds 1.3%), loses to E2 on the August windows, and is +3.8% with 22% stop odds one block late (section 23.11) |
| the buyers after you bring less | `flow`: `follow_eth_last_60` under 0.25 ETH for a day | nothing; the switch reacts only when scores go negative | expect +3% to +4% a trade instead of +6%; the hour matters (September nights +10%, US mornings +3%); do not size to the gauge (tested, rejected) and do not react to dumps (tested, worse) |
| the exit is wrong for the regime | `flow`: `median_first_sell_s` well past 7 s while the take-profit rarely fires (`trade_done` with `exit: hold`) | nothing | `HOLD_S=7` earned +8.6% instead of +6.2% on Sep 7–10 at a tail of 11.6% instead of 7.7%; over all 21 windows holds of 5, 6 and 7 with the take-profit are within a point of each other |
| the other buyers tighten their slippage | not visible in the log (their minimum is in their calldata) | nothing | the replay says −2 to −3 points per trade if they do (section 23.8); re-read the sample with `src/collect/chain_checks_slippage.py` monthly |
| teams dump earlier | `flow`: `median_first_sell_s` falling toward the hold, `share_dumped_inside_hold` rising | nothing | shorten `HOLD_S` to 3 (+3.6% on September instead of +6%) or stop |
| teams plant a dust buy in second one to trip the gate | many `outsider buys in second one` gates with tiny `bundle_eth`-sized buys in the scored launches | nothing | set `OUT1_MIN_ETH=0.01` (dust below it no longer counts) |
| the tax schedule or the exemption changes | `alarm: tax schedule changed` (half of the last 20 scored launches show surcharges outside the three bands) | trading stops until restart | read the curve's getters (`0x24a9d853` tax, `0xc57eadfc` reserves); the rule is dead until the new schedule is measured |
| the launchpad moves or stops | `alarm: no creation seen from the factory for 30 minutes` on a live feed | nothing to trade | find the new factory address (a new creation selector or contract), or stop |
| ordering changes (a priority lane, a different sequencer) | `landing` events with `where: early` or `later block` on every trade while `seat_flip_to_send_ms` reads 300 | the margin controller moves, the stop caps the loss | stop; the seat depends on first-come ordering |
| gas | `eligible_not_traded` with `gas $… per round trip > 5% of stake` | the small stakes stop trading by themselves | wait, or raise the bankroll (gas is $0.10 today, the gate allows $1.25 on a $25 stake) |
| your send step | `sent_tx` answers that are errors, `buy_reverted`, `receipt_timeout` | an open position is closed on restart | the reference below is tested; do not improvise on it at the boundary |
| the sell does not land (a token you cannot get out of) | `resend`, `approve_missing`, `sell_reverted`, then `alarm: sell not confirmed` | engine 4.2 confirms the approve first (its receipt, else the allowance, else a fresh approve: the curve's sell reverts without an allowance, checked on the chain), sells the wallet's real balance, waits for the sell's receipt and re-sends with a doubled cap every 1.5 s until it is in, diagnoses a reverted sell (allowance, balance) and retries, and if nothing is confirmed after 20 s keeps the position open (no new trade), retries every 5 s and alarms. The approve and the sell carry an 8× fee cap (`SELL_GAS_HEADROOM`): receipts show the chain charges only the base fee (a 0.54 gwei cap paid 0.18), so the cap is free and a fee spike cannot refuse the exit. Tested against a simulated chain: lost sell, missing approve, reverted sell, refused endpoints | read the alarm's `sell_hash` on the explorer; if the sequencer and the provider are both down, the retry keeps going until one answers; the only exit the engine cannot force is a chain that is halted |
| the terms of use | nothing in the log | nothing | read in full (section 23.10): Robinhood's chain terms cover the sequencer, the public RPC and the feed, not the chain or your trade; they list "use of automated tools (such as bots ...)" under network abuse and limit those Services to "testing, experimentation, evaluation, and development". Two postures: A, the sequencer feed and the sequencer endpoint (fastest, uses the Services); B, a provider's WebSocket and RPC only (`FEED_SOURCE=provider PROVIDER_WS=...`, no Robinhood endpoint, about a tenth fewer trades, no E1). Your choice |

**The send step, tested.** This is the whole of `deploy/send_step.py`, the file `SEND_MODULE` loads (section 5); it was
run against the engine's own transaction with a throwaway key through both warm sockets, and the sequencer's and the
provider's only complaint was that the key had no funds:

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
for this box and `SEAT=E1 FRAC=0.10` is the plan while `flow` shows `out1_share_last_60` above 0.55, E2 otherwise
(section 23.11: hold 5 with the take-profit as the engine runs it, or `HOLD_S=7 TAKE_PROFIT=0` for +13.1% a trade at a
17% tail); if fewer than twenty do, stay at E2. The cost of the test is about $2 a launch in gas and surcharge, $60 in all.

## 5j. The reconciliation and the race readout (Sep 23)

Before any restart, and after any run, two readouts say whether the seat pays as executed, not as modelled:

    python3 src/analysis/live_vs_table.py            # every real fill against the tables' model for the same launch (chain only, public RPC)
    sudo python3 src/analysis/race_readout.py        # on the box: per burst, which shot filled, our tx index, who was ahead (all rotated logs)

`live_vs_table` must show `execution/fees/model +0.0%` on every line (the engine is exact); the money is in the `seat`
column. `race_readout`: fill shot k > 1 means the burst straddled the tick; k = 1 means the whole burst was late. Section
24.28 of the report: the seat we get is the one the fast bot leaves, worth −1.5% first and −2% after gas at $15.

## 5k. Do not restart the seat as built (Sep 23)

Report 24.29: the seat as built is −2% a trade after gas (the launches we win have no crowd; the ones with a crowd belong
to a faster bot that itself earns about 0%). A restart needs, in this order: the pre-tick crowd gate (crowd_signal.py's
rule inside the engine: fire only when two or more wallets are already firing at the curve by the last visible creation-
second block), a hold counted in blocks, gas_usd() at the real 1.94M gas a round trip, a sell minOut; a paper day with
the expected return logged per burst; then $100 stakes with a dollar kill line, re-priced daily with gated_seat.py on the
last 24 hours. At $15 the gated seat is $0.20 a burst: not worth the gas.

Addendum (24.30): the candidate that survives the winners' anatomy is the pre-tick gate plus a 150-300-block hold at second
place (+20-25% a fill on Sep 22-23, in sample). Not before the out-of-sample run on Sep 20-21 and a paper day.

## 5l. Engine 6.1: the gated seat with a long hold, paper first (Sep 23)

Settings (in /etc/sniper/engine.env), all off by default:

    ATTACK_MIN=2        # fire only when two or more other snipers (relays or direct senders) are already firing at the curve when the burst is built
    HOLD_BLOCKS=300     # hold 300 feed blocks (about 30 s) after the fill instead of HOLD_S seconds
    KILL_USD=15         # below this capital (wallet + relay) no launch is taken; one alarm

The paper day: unset SEND_MODULE (the engine logs unsigned transactions and sends nothing), set the three above, restart, run a
day, then on the box:

    sudo python3 src/analysis/paper_day.py --stake 13 --hold 300

It scores every launch the engine would have fired at from the chain at the positions we can get (behind one, behind two,
behind everybody) held 300 blocks, after gas, and the launches the gate refused. Go: behind one at or above +10% mean over at
least 40 gated launches with the refused set negative. No-go: anything else; then the seat is closed and this stops.

Live after a go: SEND_MODULE back, STAKE_MIN=STAKE_MAX=13, MAX_LIVE_TRADES=30, KILL_USD=15; every day
`python3 src/analysis/live_vs_table.py` (the fills against the model) and `sudo python3 src/analysis/paper_day.py --from "<yesterday> 00:00"`
(the rule against the chain). The burst may be cut to BURST_N=10 with BURST_STEP_MS=10 once section 24.30's position table
confirms that third place pays the same as second at 300 blocks (it does on Sep 22-23: +19.5% against +26.9%).

### 5l, the commands (on the box)

Paper day (nothing is sent; the engine logs what it would have done):

    sudo sed -i 's|^SEND_MODULE=.*|SEND_MODULE=|' /etc/sniper/engine.env
    sudo grep -q '^ATTACK_MIN=' /etc/sniper/engine.env || printf 'ATTACK_MIN=2\nHOLD_BLOCKS=300\nKILL_USD=15\n' | sudo tee -a /etc/sniper/engine.env >/dev/null
    cd ~/fomo-memebot && git pull && sudo systemctl daemon-reload && sudo systemctl restart sniper-engine && sleep 5 && sudo tail -2 /var/log/sniper/engine.jsonl | cut -c1-400

(the service runs the repo's own src/strategy/sniper_engine.py: the pull is the deploy). After a day:

    sudo python3 src/analysis/paper_day.py --stake 13 --hold 300

Live after a go:

    sudo sed -i 's|^SEND_MODULE=.*|SEND_MODULE=/etc/sniper/send_step.py|; s|^STAKE_MIN=.*|STAKE_MIN=13|; s|^STAKE_MAX=.*|STAKE_MAX=13|' /etc/sniper/engine.env
    sudo systemctl restart sniper-engine

Daily: `python3 src/analysis/live_vs_table.py` and `sudo python3 src/analysis/paper_day.py --from "<yesterday> 00:00"`.

## 5m. Engine 6.2: the gate inside the burst (Sep 23)

The gate is decided shot by shot while the burst runs (report 24.32). Nothing to set beyond 5l; GATE_LATE_MS (default 0)
lets the gate open this many ms after the predicted tick's shot. The deployed send step must be the 6.2 copy:

    cd ~/fomo-memebot && git pull && sudo cp deploy/send_step.py /etc/sniper/send_step.py && sudo systemctl restart sniper-engine && sleep 5 && sudo grep '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"version": [0-9.]*\|"dry_run": [a-z]*\|"attack_min": [0-9]*\|"gate_late_ms": [0-9.]*'

The paper day's events now carry attackers_at_build, attackers_at_open, gated_shots and gate_opened_at_shot; a launch whose
gate never opened is an eligible_not_traded with "the gate never opened" and paper_day.py counts it as refused.

## 5n. Engine 6.3: the view measured, both units logged (Sep 24)

Report 24.33: the tables counted shooter wallets and priced a block index; the engine counts fleets and sees time. Nothing
to set (ATTACK_UNIT=fleets, ATTACK_MIN=2, ATTACK_BUILD_MIN=0 are the defaults and the rule of 6.2); every decision now
carries blk0, feed_block_at_build, feed_block_at_open, feed_block_after_burst, fleets_at_open and wallets_at_open. The
send step is unchanged. Deploy (the paper day keeps running, dry run):

    cd ~/fomo-memebot && git pull && sudo systemctl restart sniper-engine && sleep 5 && sudo grep '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"version": [0-9.]*\|"dry_run": [a-z]*\|"attack_min": [0-9]*\|"attack_unit": "[a-z]*"'

The reading (the day's window from its first start, or `--from "YYYY-MM-DD HH:MM"`):

    cd ~/fomo-memebot && git pull && sudo python3 src/analysis/paper_day.py --stake 13 --hold 300 2>&1 | tail -30

Each fired or refused launch prints "k=<blocks in the creation second minus one>, feed at the build block <j>, at the open
block <j>; fleets/wallets at the open a/b": the engine's view, measured. The expectation for the fired set is the
engine's rule at the tick's shot (24.33): behind one +11% to +15% mean, 55-58% wins; the go line of 5l stands (behind one
at or above +10% over the gated launches, the refused set negative). Once a day of 6.3 is in, `crowd_rules.py` is re-run
with the measured view in place of the modelled one before any setting changes.

### 5n, the safety switch must be off for the gated rule (Sep 24)

The first 6.3 day showed the leak in front of the gate: 10 of the 12 launches that passed the tables' filters were refused
by the safety switch (`safety switch off (rolling -0.13 over 15 < -0.10)`), not by the crowd gate. The switch scores every
eligible launch, fired or refused, at the first seat and the HOLD_S hold (`score_launch` calls `exact_score` without
`hold=`), so it measures the ungated old rule, whose population the crowd gate exists to refuse; in this regime that
rolling mean sits below −10% most of the time and the gate never gets the launch. The tables never had a switch: on the
four windows the same switch would have blocked 12 of 123 gated fires, and those 12 averaged +50% (report 24.33). Capital
protection stays with KILL_USD and DAILY_STOP. Set it off and restart:

    sudo grep -q '^SWITCH=' /etc/sniper/engine.env && sudo sed -i 's|^SWITCH=.*|SWITCH=-9|' /etc/sniper/engine.env || echo 'SWITCH=-9' | sudo tee -a /etc/sniper/engine.env >/dev/null
    sudo systemctl restart sniper-engine && sleep 5 && sudo grep '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"version": [0-9.]*\|"dry_run": [a-z]*\|"switch": \[[^]]*\]'

Expected: version 6.3, dry_run true, switch [15, -9.0]. With the switch off the gate sees every qualifying launch and the
fire rate should approach the tables' 22-38 a day (about 31 pooled) instead of the 6-10 the switch was leaving.

## 5o. Engine 6.4: the seam closed, the settings aligned with the tables (Sep 24)

Report 24.33 addenda 2-3: two independent readers and a mechanical replay compared what the engine gates on with what the
tables priced. The tables had counted the token's own approvals as a fleet (fixed in the pull; the engine's rule re-priced at
+19% to +30% a fire); the engine's gate could open after the actual tick and fill behind the wave (GATE_CLOSE_MS); and a
list of engine-only filters stood in front of the gate that the tables never had (TRADE_HOURS 12-05, the demand floor's
arming after a restart, GAS_MAX_SHARE at 5% of a $13 stake, the safety switch) or that the tables had and the engine might
not (the 100-200 bps tier band, no bundle cap). One command sets every one of them explicitly; the send step is unchanged:

    set_kv() { sudo grep -q "^$1=" /etc/sniper/engine.env && sudo sed -i "s|^$1=.*|$1=$2|" /etc/sniper/engine.env || echo "$1=$2" | sudo tee -a /etc/sniper/engine.env >/dev/null; }
    set_kv ATTACK_MIN 2; set_kv HOLD_BLOCKS 300; set_kv SWITCH -9; set_kv GATE_CLOSE_MS 36; set_kv TRADE_HOURS ""; set_kv MIN_FOLLOW_ETH_60 0; set_kv GAS_MAX_SHARE 0.10
    set_kv TIER_MIN_BPS 100; set_kv TIER_MAX_BPS 200; set_kv BUNDLE_MIN 3; set_kv BUNDLE_MIN_ETH 0.3; set_kv BUNDLE_MAX_ETH 0; set_kv MIN_CREATOR_SUPPLY 0.01
    cd ~/fomo-memebot && git pull && sudo systemctl restart sniper-engine && sleep 5 && sudo grep '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"version": [0-9.]*\|"dry_run": [a-z]*\|"gate_close_ms": [0-9.-]*\|"trade_hours": "[^"]*"\|"tier_min_bps": [0-9]*\|"tier_max_bps": [0-9]*\|"bundle_max_eth": [0-9.]*\|"min_creator_supply": [0-9.]*\|"min_follow_eth_60": [0-9.]*\|"switch": \[[^]]*\]'

Expected: version 6.4, dry_run true, gate_close_ms 36.0, trade_hours "", tier 100/200, bundle_max_eth 0.0, min_creator_supply
0.01, min_follow_eth_60 0.0, switch [15, -9.0]. What each does:

- `GATE_CLOSE_MS=36`: the gate may open until 36 ms after the burst's first shot, where the actual tick lands on median
  (fills at shots 1-18, median 12); a gate opening later would fill on its own shot behind the crowd's wave, not at the
  priced second place. Costs the fires whose second fleet shows between +36 and +80 ms (the late arrivals, +5% in the tables).
- `TRADE_HOURS=""`: all hours. The old rule's 12-05 window dropped 12 of 123 fires averaging +17.7%.
- `MIN_FOLLOW_ETH_60=0`: the demand floor never binds on the four windows at its level, but it arms only after 10 scored
  launches following any restart with a state file older than an hour: an hour or two of refusals after every such restart.
- `GAS_MAX_SHARE=0.10`: the 5% cap is $0.65 on $13 and the burst costs $0.43 at today's 0.043 gwei and $0.65 at 0.066 gwei
  (Sep 18-19 median 0.063): at those fees it refused up to 28% of launches on the base fee alone. 10% = $1.30 still refuses a
  burst that would eat the edge.
- `TIER_MIN_BPS=100, TIER_MAX_BPS=200, BUNDLE_MIN=3, BUNDLE_MIN_ETH=0.3, BUNDLE_MAX_ETH=0`: the tables' population (the 2-3%
  tiers, three named wallets and 0.3 ETH, no cap). With the tier gates at 0 the engine fires on 1%-tier and 4%+ launches
  never priced; with BUNDLE_MAX_ETH=1.2 (the ohio template) it drops 30 of 123 fires averaging +26%.
- `MIN_CREATOR_SUPPLY=0.01` stays: the tables never had it, it drops 15 fires averaging +3.5% and lifts the mean.
- Kept and unpriced, in the engine's favour: the creator-repeat skip (5 fires at −36% dropped), one position at a time (2
  fires), the bundle fold's early close on a stranger's direct shot (up to 19 fires at −5%).

Live note: capital is about $15.40 (wallet plus relay) and KILL_USD=15 stops trading after the first loss over $0.40. The
rule's mean shows over 15+ fires with 7-12% of them dead; a live test needs either KILL_USD=10 or more capital, and that is the
owner's call, not a setting to change quietly.

The reading (unchanged): `cd ~/fomo-memebot && git pull && sudo python3 src/analysis/paper_day.py --stake 13 --hold 300 2>&1 | tail -40`.
Each launch prints, from 6.4, the chain-numbered feed blocks at the watch, the build, the open (or the close of a refusal) and
after the burst, both counts at the open and after, the opening in ms, and "GUARD: no fill" where the burst's minOut would
have refused the priced fill. The expectation for the fired set is the engine's own rule: behind one +19% to +30% mean, 60-67%
wins; the go line stands (behind one at or above +10% over 15+ fired launches, the refused set at or below zero).

## 5p. Engine 6.5: the watch's replay in chronological order (Sep 25)

Report 24.33 addendum 8. When a curve is registered, the buys the feed had already shown are replayed into its state; the
replay folded direct buys first and helper calls after, so a stranger's reverting shot at block 2 closed the bundle before
the helper's named buys at block 1 were counted, and the launch was refused with "bundle 0 < 3" (3 launches in two days,
one of them the afternoon's only sure fire). 6.5 folds them in (block, arrival) order. No setting; deploy:

    cd ~/fomo-memebot && git pull && sudo systemctl restart sniper-engine && sleep 5 && sudo grep '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"version": [0-9.]*\|"dry_run": [a-z]*'

The aim's skip ("no confident boundary estimate") logs `boundary` [theta ms, confidence, brackets] and `since_creation_ms`;
a skip with a large since_creation_ms is a creation in the last blocks of its second (un-aimable), one with few brackets
or low confidence is the estimator after a reconnect. To read them: `sudo grep -h '"no confident boundary' /var/log/sniper/engine.jsonl | grep -o '"curve": "0x[0-9a-f]\{8\}\|"boundary": [^}]*\|"since_creation_ms": [0-9]*' | paste - - -`.

## 5q. Live, Sep 26 09:15 UTC: the daily commands

Switched on with SEND_MODULE=/etc/sniper/send_step.py, STAKE_MIN=STAKE_MAX=13, KILL_USD=10, MAX_LIVE_TRADES=30, engine 6.5,
the pre-gate settings of 5o. Base capital 0.008753 ETH ($23.48): wallet 0.000804, relay 0.005212 (the stake), shooters'
gas 0.002737 (35 shooters, 0 low, 0 unregistered). The relay is refilled from the wallet to 1.2 x the stake after every
exit (RELAY_FLOAT_USD); shooters below SHOOTER_MIN_ETH are refilled from the wallet; both log an alarm when the wallet
cannot. The stake stays $13 until a week of real fills reconciles against the model; then $25, then $50, one step per
reconciled week (the return per fire falls with size: stake_table.txt).

Every evening after 22:00 UTC, in this order (the prediction is built here first, from the chain, before the log is read):

    # 1. the balance and the P&L since the base, every gas and fee included (read-only)
    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_ops.py status 0.008753
    # 2. the rule against the chain: fires and refusals, scored as on the paper days (--from = the previous reading's end)
    cd ~/fomo-memebot && git pull && sudo python3 src/analysis/paper_day.py --from "<previous end>" --stake 13 --hold 300 2>&1 | tee /tmp/reading.txt
    # 3. every real fill against the model for the same launch (the seat we got, the hold, the rest)
    cd ~/fomo-memebot && python3 src/analysis/live_vs_table.py 2>&1 | tail -40
    # 4. alarms (a relay or shooter the wallet could not refill, a crashed launch thread, the kill line)
    sudo grep -h '"ev": "alarm"' /var/log/sniper/engine.jsonl | tail -5 | cut -c1-220

Stop at any time: `sudo systemctl stop sniper-engine` (positions already open are sold by the engine only while it runs:
stop between trades, i.e. when `sudo grep -c '"ev": "trade_done"' ...` equals the trade_decision count).

### 5q, the intake readout (Sep 26)

The sequencer's transaction intake holds a burst about a second on the biggest crowds and about one burst in twenty at
random (report: live, the first fire). Every evening, with the four commands of 5q:

    sudo python3 src/analysis/intake_readout.py /var/log/sniper/engine.jsonl.1 /var/log/sniper/engine.jsonl | tail -8

    # 6. every launch the prediction listed against the engine's disposition of it (FIRE / GATE / PRE-gate filter / hole)
    sudo python3 src/analysis/engine_vs_chain.py data/derived/live_vs_table/launches_<window>.json

A `NO EVENT` or `CREATION ONLY` line is a hole: the engine never decided on a launch the chain qualifies, and the
errors within 90 s are printed beside it. The log rotates at 00:00 UTC (logrotate, copytruncate): yesterday's events are in `engine.jsonl.1`, older days in
`.2.gz` and on. `paper_day.py` reads them all by itself; `intake_readout.py` and any ad-hoc `grep` or python over the
log must name `.1` too when the window crosses midnight (Sep 27: the night's first 76 minutes seemed empty until
`.1` was read).

One line per burst: the sequencer's reply time (median / max ms), filled or not, the fill shot (1 = the whole burst was
late: filled behind everybody), the blocks the shots spread over, the crowd's rival shots. A reply median over 500 ms is a
held burst. `deploy/seq_probe.py 35 3` (engine stopped, about $0.10 of gas) measures the intake on demand.

### 5q, capital for the float (Sep 26)

The relay must hold the stake and the wallet keeps 0.0015 ETH; after every exit the relay is refilled from the wallet
to 1.2 x the stake, as far as the wallet reaches. So wallet + relay must stay above stake + 0.0015 ETH (about $17 at
$13), plus slack for losing exits (about $0.7 each at $13: the loss and the burst's gas). Below that the engine refuses
every launch with `the relay holds ... < the stake: deposit` (no alarm: the refill itself did not fail) and the evening
reading shows 0 fires and 0 gate refusals. Check and fix:

    # what the engine refused on, since 13:47 UTC on Sep 26 (change the epoch for another day)
    sudo grep -h '"ev": "eligible_not_traded"' /var/log/sniper/engine.jsonl | python3 -c "import sys,json; [print(json.loads(l)['gates'][0][:90]) for l in sys.stdin if json.loads(l)['t'] > 1790430420]" | sort | uniq -c | sort -rn | head
    # top up the wallet from Phantom (0.004 ETH), wait for it to land, then move the relay to its float
    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_ops.py deposit 0.0015
    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_ops.py status 0.021190

The engine reads the relay's balance every 6 s while no position is open: no restart. The status line's base moves
by exactly the top-up: on Sep 26 the top-up was $17.90 = 0.006659 ETH, so the base is 0.008753 + 0.006659 = 0.015412 ETH
and the P&L line keeps counting from the switch (−$0.68 at 22:45 UTC, the first fire's gas and the first fill's −2.6%).

The prediction window starts at the engine's start line (`"ev": "start"`, its `t`), not at an assumed time: the first
live fill (13:47:18) fell 42 s before a window that assumed a 13:50 start.

### 5q, the RPC quota (Sep 26 22:29 UTC)

The provider behind RPC_URL answered `429 Monthly capacity limit exceeded` to every call from 22:29: the engine's
bookkeeping loop (nonce, gas, the relay's and the wallet's balances) failed every 3 s, every launch was refused on
`nonce/gas not fresh (RPC)`, and `relay_ops.py` could not deposit. The engine already reads logs from the public node
(LOGS_RPC_URL); it now reads everything from it:

    sudo systemctl stop sniper-engine
    set_kv() { sudo grep -q "^$1=" /etc/sniper/engine.env && sudo sed -i "s|^$1=.*|$1=$2|" /etc/sniper/engine.env || echo "$1=$2" | sudo tee -a /etc/sniper/engine.env >/dev/null; }
    set_kv RPC_URL https://rpc.mainnet.chain.robinhood.com
    sudo systemctl start sniper-engine

Symptom to watch (should print a time before the restart, then nothing new):

    sudo grep -h '"stage": "chain_loop"' /var/log/sniper/engine.jsonl | tail -1 | cut -c1-120

`relay_ops.py deposit` refuses to run while the engine runs (same wallet, same nonce): stop, deposit, start.

*Reversed the next morning (Sep 27).* The public node throttles the seat path: it answers 429 to the burst of reads a
launch triggers (resolve, receipt, the creation block's clock), and the night's log shows one launch "not resolved in
3 s" and one two-fleet launch skipped for "no confident boundary estimate" in the same second as a 429. The seat path
goes back to the paid node; what ran the quota out was the bookkeeping loop at 3 s (nonce, gas, balances: about 50M
compute units a month against a 30M allowance), so CHAIN_POLL_S goes to 10 (the value the paper box used), which
fits the allowance with the shooters' refresh included. Logs stay on the public node (LOGS_RPC_URL). The paid node's
URL is typed into the env file by hand and never pasted anywhere:

    sudo systemctl stop sniper-engine
    set_kv() { sudo grep -q "^$1=" /etc/sniper/engine.env && sudo sed -i "s|^$1=.*|$1=$2|" /etc/sniper/engine.env || echo "$1=$2" | sudo tee -a /etc/sniper/engine.env >/dev/null; }
    set_kv RPC_URL 'https://<the HTTPS URL from the provider dashboard>'
    set_kv CHAIN_POLL_S 10
    sudo systemctl start sniper-engine

## 5r. Back to paper, Sep 27 09:02 UTC

Live from Sep 26 09:15 to Sep 27 09:02 UTC: two bursts, one fill (−2.6%), P&L −$0.68 on a base of 0.015412 ETH (the
$17.90 top-up included); the wallet and relay keep their ETH. Reason: the rule's fires on the chain since Sep 24 (18
fires, the engine's population, 300-block hold) average +3.5%, 39% win, the last five all lost; the backtest's 73 fires
at +26% were fitted on Sep 18-23 and the edge has not shown since. The engine runs with `SEND_MODULE=` empty: it fires
paper shots at the same moments and the evening reading scores them on the chain for free.

Every evening, unchanged: the prediction first, then steps 2 (paper_day, `--from` the previous reading's end), 6
(engine_vs_chain) and 5 (intake readout: nothing to read while paper). Step 1 (balance) once a week.

Re-entry: `SEND_MODULE=/etc/sniper/send_step.py` (runbook 5q), at $13, only when the trailing 20 fires of the rule on the
chain are positive on average with at least 55% wins, and with KILL_USD set to about $10 under the wallet-plus-relay
figure at the switch. Not before, whatever a single good day looks like.

### 5r, live again, Sep 27 09:03 UTC (the owner's decision)

Live at $13 with KILL_USD 24: the engine stops itself when wallet plus relay fall under $24, about $10 under the
$33.66 they held at the switch. Base for the status line unchanged (0.015412 ETH). The week's questions, in order:
do the fires come at the predicted moments, do they fill where the model says, and is the running mean of the live
fires positive after 15 of them. The stake rises only on the third. The daily commands are those of 5q (six steps).

## 5s. The hold: 300 blocks to 15 (Sep 27, report 24.36)

Two reviewers with the whole story, unanimous: keep the gate (fleets >= 2 at k-2) and the $13 stake, sell 15 blocks
after the seat. Both periods positive at 15 (+16.2% fit, +12.7% recent), the failure mechanisms of 24.35 act after
block 15, the September winners were complete by block 15. Switch (the engine reads the env at start):

    sudo systemctl stop sniper-engine
    set_kv() { sudo grep -q "^$1=" /etc/sniper/engine.env && sudo sed -i "s|^$1=.*|$1=$2|" /etc/sniper/engine.env || echo "$1=$2" | sudo tee -a /etc/sniper/engine.env >/dev/null; }
    set_kv HOLD_BLOCKS 15
    sudo systemctl start sniper-engine && sleep 5 && sudo grep -h '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"version": [0-9.]*\|"hold_blocks": [0-9]*\|"kill_usd": [0-9.]*\|"stake": \[[^]]*\]'

The evening reading scores the 15-block hold from here: `paper_day.py ... --hold 15`, and the prediction is built
with `HOLD=15 python3 src/analysis/predict_window.py ...` (the h15 column of the same hold grid). Expectation at $13
and today's supply: $3-10 a day. Stops: KILL_USD stays at about $10 under wallet plus relay; back to paper if fewer
than 3 of the first 10 live bursts fill; the sequential test of 24.36 on the chain-scored fires (break-even +2.5%
against +15.5%, sd 0.33, boundaries ±2.94) stops the strategy at its lower boundary and permits the stake step at its
upper one, about 30-35 fires either way.

Switched at 11:17 UTC on Sep 27: version 6.5, stake 13, hold_blocks 15, kill_usd 24. The 15-block test counts from here.

## 5t. The hold: 15 to 9 (Sep 27, report 24.37)

Three reviewers priced every exit from 1 to 1,200 blocks: the peak is at exit block 10-13 in both periods, the sell
lands 2-4 blocks after the setting, so the setting is 9 (E: 9, F: 8, G: 9; 15 inside every plateau).

    sudo systemctl stop sniper-engine
    set_kv() { sudo grep -q "^$1=" /etc/sniper/engine.env && sudo sed -i "s|^$1=.*|$1=$2|" /etc/sniper/engine.env || echo "$1=$2" | sudo tee -a /etc/sniper/engine.env >/dev/null; }
    set_kv HOLD_BLOCKS 9
    sudo systemctl start sniper-engine && sleep 5 && sudo grep -h '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"version": [0-9.]*\|"hold_blocks": [0-9]*\|"kill_usd": [0-9.]*\|"stake": \[[^]]*\]'

The readings: `paper_day.py ... --hold 9` scores the exit at block 9 (the model's sell at E1+9; the engine lands
2-4 later, both are printed by live_vs_table as `landed@our exit(+N blocks)`); the prediction with `HOLD=15` (the
grid has h15, not h9: a 15-block reading is a conservative proxy until the grid gets h9). **The first thing to check
after every fill:** the landed exit block. Above +13 the sell is inside the seat-block sellers' wave and the setting
must come down or the exit path be looked at (`token_resolved_at_exit` events mean the token was resolved at the
sell, which costs up to a second). The stops of 5s stand: KILL_USD 24, back to paper under 3 fills in the first 10
bursts, the sequential test on the chain-scored fires (H0 +2.5%, H1 about +19%, sd 0.34).

Switched at 11:53 UTC on Sep 27: version 6.5, stake 13, hold_blocks 9, kill_usd 24. No fill since the 11:17 restart at 15, so the 9-block test counts from here.

## 5u. The bundle cap: BUNDLE_MAX_ETH 3.0 (Sep 28, report 24.39)

Two reviewers and two verifiers, unanimous: refuse launches whose creation-second bundle is over 3.0 ETH (one serial
operator's 4.2 ETH template, flat at the fee floor on all 21 such launches). Never worse in any window, chosen on one
period and read on the other, null 0 of 2,000. Switch (the engine reads the env at start; no fill should be open:
`sudo grep -c '"ev": "trade_done"'` equals the trade_decision count):

    sudo systemctl stop sniper-engine
    set_kv() { sudo grep -q "^$1=" /etc/sniper/engine.env && sudo sed -i "s|^$1=.*|$1=$2|" /etc/sniper/engine.env || echo "$1=$2" | sudo tee -a /etc/sniper/engine.env >/dev/null; }
    set_kv BUNDLE_MAX_ETH 3.0
    sudo systemctl start sniper-engine && sleep 5 && sudo grep -h '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"version": [0-9.]*\|"hold_blocks": [0-9]*\|"kill_usd": [0-9.]*\|"stake": \[[^]]*\]\|"bundle_max_eth": [0-9.]*'

The prediction's population still lists these launches (e1_multi has no cap); the engine's refusal reads
`bundle N ETH > 3.0` in engine_vs_chain, a PRE line, as intended.


## 5v. Engine 6.6: the burned bundle (Sep 28, report 24.40)

The 02:51 launch the night reading could not find: its team's bundle went through a helper that bought in its own
name, the curve taxed it 97%, the pipeline saw no bundle, the engine's feed count saw 0.49 ETH. Engine 6.6 names that
helper's selector on a denylist (`TAXED_HELPER_SELS`, default `4d819a2a`; add selectors comma-separated with
`set_kv TAXED_HELPER_SELS 4d819a2a,<next>` when a reading shows another `ENGINE ONLY` launch of the kind) and folds
a taxed creation-second buy as the chain does (one percent of its ETH). Deploy, with no fill open
(`sudo grep -c '"ev": "trade_done"'` equals the trade_decision count):

    cd ~/fomo-memebot && git pull && sudo systemctl restart sniper-engine && sleep 5 && sudo grep -h '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"version": [0-9.]*\|"hold_blocks": [0-9]*\|"kill_usd": [0-9.]*\|"stake": \[[^]]*\]\|"bundle_max_eth": [0-9.]*'

Expected: `"version": 6.6`, the rest unchanged (stake 13, hold_blocks 9, kill_usd 24, bundle_max_eth 3.0).

Step 6 of the reading now takes the window and reports both directions:

    sudo python3 src/analysis/engine_vs_chain.py data/derived/live_vs_table/launches_<window>.json --crowd data/derived/live_vs_table/crowd_raw_<window>.json.gz --from "<start>" --to "<end>"

Every population launch as before (FIRE / GATE / PRE / NO EVENT), then `ENGINE ONLY` lines for launches the engine
judged eligible that the population does not hold, and a summary `N engine-only`. After 6.6 an `ENGINE ONLY` line is
a new kind of launch: read it from the chain before anything else (`e1_multi`'s scan prints the burned bundles it
dropped: `N burned bundles` in its summary line, the list in the JSON's `burned`).

## 5w. Engine 6.7: the review's four fixes (Sep 28, edge_check/J/LANGUAGE.md)

An independent review of the "would Rust or C++ help" question (report 24.41's companion, `data/derived/edge_check/J/LANGUAGE.md`)
found the interpreter's share of the seat path small but not zero, and four things worth fixing in Python:

1. **One sender recovery per transaction.** The feed loop and the gate recovered the same rival shot's sender two or three times
   (0.1 ms each; 4-7 ms on a busy frame just before the tick). Cached now.
2. **The burst no longer spins holding the interpreter lock.** The sender waited for each shot's moment in a busy loop (4 ms a
   shot, the whole burst), which starved the feed loop exactly while the gate needed it. It sleeps to 1.5 ms before the shot
   and yields the lock on every spin turn. Same in the dry-run path.
3. **Warm RPC connections on the seat path.** The resolver ran in a fresh thread per launch, and connections lived per thread,
   so every launch paid a cold TLS handshake (4-10 ms). Connections are pooled across threads and the seat node's are pinged
   every 30 s.
4. **The feed loop's per-frame time is logged**: `feed_stats` once a minute (median, p90, max ms per frame, busy share). Read it
   after a busy hour: `sudo grep -h '"ev": "feed_stats"' /var/log/sniper/engine.jsonl | tail -3`. A p90 over 2 ms before the
   tick is the number the review says would cost the k-1 view.

Not done: signing with coincurve directly (a bigger change in the transaction encoder; the gain is a fresher minOut, whose sign is
unknown), and the review's instance advice (a c7a.large has two real cores; a c6i/c7i.large is one core with two threads).

**PIN_CPU.** With PIN_CPU=1 the feed loop and the sender share one vCPU and shots go late when the decoder is busy (p90 2 ms,
p99 6 ms in the review's measurement). On any box with two vCPUs, unpin: `set_kv PIN_CPU ""`. Deploy, with no fill open
(`sudo grep -c '"ev": "trade_done"'` equals the trade_decision count):

    cd ~/fomo-memebot && git pull && set_kv() { sudo grep -q "^$1=" /etc/sniper/engine.env && sudo sed -i "s|^$1=.*|$1=$2|" /etc/sniper/engine.env || echo "$1=$2" | sudo tee -a /etc/sniper/engine.env >/dev/null; }; set_kv PIN_CPU ""; sudo systemctl restart sniper-engine && sleep 5 && sudo grep -h '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"version": [0-9.]*\|"hold_blocks": [0-9]*\|"kill_usd": [0-9.]*\|"stake": \[[^]]*\]\|"bundle_max_eth": [0-9.]*'

Expected `"version": 6.7`, the rest unchanged. The send step on the box (`/etc/sniper/send_step.py`) is the operator's copy of
`deploy/send_step.py`: copy the new one over it before the restart (`sudo cp ~/fomo-memebot/deploy/send_step.py /etc/sniper/send_step.py`)
or fix 2 applies to the dry-run path only.

## 5x. BURST_SLIP 0.15 (Sep 28, report 24.42: four analyses, one change)

The minOut guard at 7% reverted half the bursts on a buy ahead that marks the crowd that pays; the relay's one-buy rule does the
guard's original job. Switch with 5w's deploy (engine 6.7, the new send step, PIN_CPU unpinned), no fill open:

    sudo grep -c '"ev": "trade_done"' /var/log/sniper/engine.jsonl; sudo grep -c '"ev": "trade_decision"' /var/log/sniper/engine.jsonl
    cd ~/fomo-memebot && git pull && sudo cp deploy/send_step.py /etc/sniper/send_step.py && set_kv() { sudo grep -q "^$1=" /etc/sniper/engine.env && sudo sed -i "s|^$1=.*|$1=$2|" /etc/sniper/engine.env || echo "$1=$2" | sudo tee -a /etc/sniper/engine.env >/dev/null; }; set_kv PIN_CPU ""; set_kv BURST_SLIP 0.15; sudo systemctl restart sniper-engine && sleep 5 && sudo grep -h '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"version": [0-9.]*\|"hold_blocks": [0-9]*\|"kill_usd": [0-9.]*\|"stake": \[[^]]*\]\|"bundle_max_eth": [0-9.]*\|"burst": \[[^]]*\]'

Expected: `"version": 6.7` and `"burst": [35, 4, 8, 0.15]`, the rest unchanged (stake 13, hold 9, kill 24, cap 3.0).

**What to watch.** Fills per burst should rise from about half to most; `buy_reverted` events become rare. On every fill the
reading's `landed` line gives the index and the buy ahead: a fill behind a buy that moved the price 7-15% is the admitted class.
Move to 0.20 once ten admitted fills have landed at index 3 or better; back to 0.07 if most of the first ten land last in the
seat block or in a later block, or when the admitted fills' own sequential test (H0 +2.5%, H1 +19%, sd 0.34, ±2.94, on their
realized 11-block returns) reaches its lower bound. The main test on the chain-scored fires runs as before.

## 5y. The four follow-ups of 5w/5x, done together (Sep 28)

1. **BURST_SLIP 0.20** (24.42's second step, taken at once on the owner's call): the two reviewers who chose 0.20 chose it on the
   Sep 24-28 read; the cost is more deep landings filling (a last-in-block fill loses about what a revert costs in gas). Back to
   0.15 if most of the first ten admitted fills (tokens 7-20% under the build's sizing) land last in the seat block or later.
2. **The burst step as a live landing test: BURST_STEP_MS 2, BURST_LEAD_MS 46** (was 3 and 80). The 35 shots now run from 46 ms
   before the estimated boundary to 22 ms after it instead of 80 before to 22 after: the same coverage on the late side (the
   side that decides whether any shot lands past the tick), twice the shot density at the tick. A first-place landing is worth
   9-11 points over second (24.42), and nothing on disk can price where a finer step lands, so this is measured live: the
   `landed` line's index on each fill. Back to 3 / 80 if the first ten bursts show more all-creation-second bursts (every shot
   reverted, `buy_reverted` with "all in the creation second") or worse landing indices than the ten before.
3. **Direct signing** (`deploy/send_step.py`): each shot is signed straight with coincurve, proved once per key against
   eth_account on a probe transaction (a key that differs is signed through eth_account for good); the `sent_burst` event logs
   `sign_ms` and `signed_direct`. The build's lead (`t_build`, 82.5 ms before the burst) is unchanged; it can be shortened once
   `sign_ms` is read from the log.
4. **The instance: c7a.large** (two physical cores, no simultaneous multithreading; about $73 a month against $62). The AWS
   connector of the assistant's session needs re-authorising, so by hand in the console, when no fill is open:
   - on the box: `sudo systemctl stop sniper-engine`
   - EC2 console, us-east-2, the instance: Instance state -> Stop instance; wait for Stopped
   - Actions -> Instance settings -> Change instance type -> c7a.large -> Apply; then Instance state -> Start
   - the public IP changes unless an Elastic IP is attached: read it in the console and ssh to it; the engine starts on boot
     (Restart=always); check `nproc` prints 2 and `lscpu | grep 'Thread(s) per core'` prints 1, then the start line below.
   PIN_CPU stays empty: the two threads must be free to use both cores.
   Done Sep 28: the instance i-001ea415c64ab3f58 reads c7a.large in us-east-2b; its public address became 18.188.14.68 (no Elastic
   IP, so it changes on every stop and start: read it in the console or CloudShell, `aws ec2 describe-instances --region us-east-2
   --query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name,PublicIpAddress]' --output table`). A CloudShell script
   must never call `exit`: it closes the session. The service was not enabled at boot: after the resize it stayed inactive from
   12:18 to 12:27 UTC until started by hand; `sudo systemctl enable sniper-engine` is now done, so a reboot brings it back.

All three settings and the new send step in one paste (no fill open: the two counts equal):

    sudo grep -c '"ev": "trade_done"' /var/log/sniper/engine.jsonl; sudo grep -c '"ev": "trade_decision"' /var/log/sniper/engine.jsonl
    cd ~/fomo-memebot && git pull && sudo cp deploy/send_step.py /etc/sniper/send_step.py && set_kv() { sudo grep -q "^$1=" /etc/sniper/engine.env && sudo sed -i "s|^$1=.*|$1=$2|" /etc/sniper/engine.env || echo "$1=$2" | sudo tee -a /etc/sniper/engine.env >/dev/null; }; set_kv BURST_SLIP 0.20; set_kv BURST_STEP_MS 2; set_kv BURST_LEAD_MS 46; sudo systemctl restart sniper-engine && sleep 5 && sudo grep -h '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"version": [0-9.]*\|"hold_blocks": [0-9]*\|"kill_usd": [0-9.]*\|"stake": \[[^]]*\]\|"bundle_max_eth": [0-9.]*\|"burst": \[[^]]*\]'

Expected `"burst": [35, 2.0, 46.0, 0.2]`, version 6.7, the rest unchanged. After the first burst: `sudo grep -h '"ev": "sent_burst"'
/var/log/sniper/engine.jsonl | tail -1 | grep -o '"sign_ms": [0-9.]*\|"signed_direct": [0-9]*\|"late_ms": \[[^]]*\]'` shows the
signing time, the shots signed directly (35 expected) and each shot's lateness.

Three timing changes at once (the guard, the step, the cores) cannot be told apart in the readings; the readings judge the
combination by the fills' landing index and the sequential test, and the rollback order if landings worsen is the step first,
then the slip.

## 5z. Engine 6.8: the bundle no longer closes at a stranger's shot; the nonce gate (Sep 28 night, report 24.43)

Sep 28 12:52 `0x98f4e88b` was skipped "bundle 0 < 3" while the chain shows a 0.71 ETH exempt bundle from 22 named wallets: two
strangers' shots sat in the bundle's block ahead of it, and the engine closed its bundle count at the first outsider's buy, a rule
the tables never had (e1_multi counts every exempt named buy in the creation window). On the week the rule cost 21 launches the
engine would otherwise have fired or gated on (18 usual-view fires, +$8.04 together, one fill carrying the read half: worth $0,
a correctness fix; report 24.43). Engine 6.8 drops it. Also: the bookkeeping poll retries 2 s after a failed read instead of waiting the whole
interval. The freshness window stays 30 s (a first draft widened it to 60 s; the review found that the wallet's top-up sends do
not advance the local nonce, so a wider window could admit a stale one). The 19:44:59 skip was the release path (5aa), not this. Deploy with the morning reading, no fill
open. `trade_decision` is logged per burst and `trade_done` per closed fill, so their counts differ by the bursts that never
filled (Sep 29 morning: 9 and 7, the 14:55 hold and the 15:33 revert); the open check is the last landing or close event:

    sudo grep -h '"ev": "burst_landing"\|"ev": "trade_done"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"ev": "[a-z_]*"\|"filled": [0-9]*'

`trade_done` or `burst_landing` with `"filled": 0` means nothing is open; `"filled": 1` means wait for its `trade_done`.
    cd ~/fomo-memebot && git pull && sudo systemctl restart sniper-engine && sleep 5 && sudo grep -h '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"version": [0-9.]*\|"burst": \[[^]]*\]\|"stake": \[[^]]*\]\|"hold_blocks": [0-9]*\|"kill_usd": [0-9.]*\|"bundle_max_eth": [0-9.]*'

Expected `"version": 6.8`, the rest unchanged. The morning reading's `engine_vs_chain` should show no more `PRE bundle 0 < 3` on
population launches; `sudo grep -c 'not fresh' /var/log/sniper/engine.jsonl` counts the nonce gate's refusals of the day.

## 5aa. The nightly routine (from Sep 28, report 24.43)

After the last reading of the day, with the day's launches reconciled both ways (`engine_vs_chain`, `live_vs_table`):

1. Append the day's facts to `data/derived/edge_check/N/BRIEF_nightly.md` (bursts with their landing index and real
   against modelled return, every new skip reason with its launch, the gate refusals against the prediction, the guard
   class tally, the signing and feed numbers, the sequential test). The six questions at the top of the brief stay.
2. Two independent reviewers on the brief in parallel (each in its own folder `N/<date>/R1`, `R2`, with the replay
   dumped at all three views and every number in a script next to its text), then two refuters per proposal, one on
   the data and one on the mechanism, each told to refute by default. A proposal survives only if it pays in both halves
   at the usual view, has a live verification and a rollback, and neither refuter breaks it.
3. The assistant re-computes every number that decides (the reviewers' rows are on disk), writes the report section,
   the runbook entry and the morning paste, and commits. One change a night at most; a correctness fix (live engine
   diverging from the model) counts as the change.
4. The morning reading verifies the change live before anything else is touched.

What tonight settled for the readings: the engine's gate view on the two-core box is the usual view (k−1 with the
registration block), so predictions quote it as the centre with the floor and ceiling as the range. The 19:44:59
"nonce/gas not fresh" skip is the release path (a gate refusal 8 s earlier set the nonce to None; the live poll is
every 10 s), worth $0 on the week; count it each morning with `sudo grep -c 'not fresh' /var/log/sniper/engine.jsonl`.
The step's second rollback tail: three or more of the next ten bursts with no shot before the tick means a longer lead.
"No confident boundary estimate" skips are, so far, always launches created in the last block of their second (k = 1), which
no view ever fires on; check the skip's `boundary` field (confidence above 0.5 means the estimate was fine and the seat's
second had simply opened). Watch items carried into the brief: the creator-supply gate (opposite signs in the two halves,
priced Sep 29), the engine-only class (bundles the engine counts over nine blocks that the tables' creation-second rule does
not: two so far, one refused at the gate, one flat fill), the gate view (k−1 on most bursts on the two-core box).

## 5ab. The box's availability zone and the feed's lag (Sep 29, report 24.44)

Measured Sep 29: the box sits in **use2-az2** (AWS zone id; the name us-east-2b maps to it in this account). An independent
measurement of the public feed from the three Ohio zones (BlockRazor, 13,251 blocks, Sep 10) puts use2-az2's delivery lag at
97 ms median and 953 ms p99 against 27-28 ms median and 86-112 ms p99 in use2-az1 and use2-az3, which matches our own probe
(`FEED_LAG_MS` 85 from `feed_lag_probe.py`). Also measured: a second feed socket from the same box delivers 3.8 ms earlier
than the first on 98% of messages (`feed_dual_probe.py`, 1,186 messages), so the earlier-of-two is a 6.9 engine item.

**The test, before moving anything** (a t3.micro in use2-az1 for ten minutes, cents). CloudShell, never `exit`:

    R=us-east-2; I=i-001ea415c64ab3f58
    read SG KEY AMI < <(aws ec2 describe-instances --region $R --instance-ids $I --query 'Reservations[0].Instances[0].[SecurityGroups[0].GroupId,KeyName,ImageId]' --output text)
    SUB=$(aws ec2 describe-subnets --region $R --filters Name=availability-zone-id,Values=use2-az1 --query 'Subnets[0].SubnetId' --output text)
    echo "sg $SG key $KEY ami $AMI subnet $SUB"
    NEW=$(aws ec2 run-instances --region $R --image-id $AMI --instance-type t3.micro --key-name $KEY --security-group-ids $SG --subnet-id $SUB --associate-public-ip-address --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=feed-probe-az1}]' --query 'Instances[0].InstanceId' --output text)
    aws ec2 wait instance-running --region $R --instance-ids $NEW; sleep 20
    aws ec2 describe-instances --region $R --instance-ids $NEW --query 'Reservations[0].Instances[0].[InstanceId,Placement.AvailabilityZone,PublicIpAddress]' --output text

Then from the laptop, with the printed IP (the probes are fetched from the public branch; the first run installs the
websockets package):

    ssh -o StrictHostKeyChecking=no -i ~/.ssh/sniper-ohio.pem ubuntu@IP 'sudo apt-get update -qq >/dev/null 2>&1; sudo apt-get install -y -qq python3-websockets >/dev/null 2>&1; B=https://raw.githubusercontent.com/xin10ylop/fomo-memebot/claude/memecoin-strategy-research-vcdy6c/deploy; curl -sO $B/feed_lag_probe.py; curl -sO $B/feed_dual_probe.py; python3 feed_lag_probe.py 120; python3 feed_dual_probe.py 60'

and at the same time on the engine box, for a same-minute comparison:

    sudo /opt/sniper-venv/bin/python3 deploy/feed_lag_probe.py 120

Decision: the p5-p10 lag is the feed's delivery lag. If use2-az1 reads 30 ms or more below use2-az2, move the engine: a
c7a.large in use2-az1 (same key and security group, `deploy/ohio_setup.sh` as in 5t, `/etc/sniper/engine.env` copied by hand
from the old box with `sudo cat`, `FEED_LAG_MS` set to the new probe's p5-p10), start it with no fill open, then stop the old
instance. If the difference is under 30 ms, stay. Either way terminate the probe instance:
`aws ec2 terminate-instances --region us-east-2 --instance-ids $NEW`.

What it is for: the gate reads the blocks before the tick from the feed, and the burst is aimed from the feed's flips. 60 ms
less lag means the last pre-tick block is seen 60 ms earlier (a fuller gate view, reliably the usual view) and the boundary
estimate has a fifth of the jitter, which is what sets the 46 ms lead; a shorter lead lands first more often (first beats
second by 9 points on the week).

**Result (Sep 29 ~10:40 UTC, same two minutes):** use2-az1 probe p5 45 / p10 53 / median 97 / p90 136 ms; the engine box in
use2-az2 p5 45 / p10 52 / median 102 / p90 138 ms. No difference: the vendor's zone claim does not hold for the public feed
as we see it, so the box stays where it is. The second-socket result repeated on the probe box (B earlier on 99% of
messages, 5.5 ms median), so the earlier-of-two feed is a real, small gain (4-6 ms) and stays on the 6.9 list. The probe
instance was terminated after the test.

## 5ac. Engine 6.9 and the step to $25 (Sep 29, report 24.44)

Engine 6.9 (`tests/test_feed_dual.py`, 17 checks): (1) two sockets to the feed (`FEED_SOCKETS`, default 2); every block is
indexed once, by sequence number, at whichever socket delivers it first (measured 4-6 ms earlier on 98% of messages); the
second socket logs `feed2_connected`, never drives the provider fallback, and waits ten minutes after an HTTP refusal; (2) a
venue guard: `snipeTaxSeconds` and `snipeTaxStartBps` are read from the V2 factory at start and hourly (`PONS_FACTORY_V2`,
`EXPECT_TAX_SECONDS` 3, `EXPECT_TAX_START_BPS` 9900); the start log carries a `venue` line; a different schedule logs an
alarm and closes the gate ("the launchpad's tax schedule changed"), a failed read keeps the last answer; (3) the shots'
gas-price cap `GAS_HEADROOM` 6 (was 2): only the base fee is charged and the sequencer drops a shot whose cap is under a ramped
base fee; the gas gate prices the round trip at the base fee, and a shooter's required float follows the cap
(`shooter_need_eth`, top-up target three times that).

The $25 step (report 24.44 part C, accepted by the owner Sep 29): `STAKE_MIN` and `STAKE_MAX` 25. The relay must hold the
stake before the first launch (about 0.0095 ETH at $2,650; it held 0.0058), so deposit 0.0045 ETH from the wallet first (the relay then holds about 0.0103 ETH, the stake down to an ETH price of about $2,430); the
wallet keeps its 0.0015 ETH reserve and the shooters' floats. `KILL_USD` stays 24 (a capital floor, not a stake multiple).
The rule: twenty fills at $25 are one window; if the window's realized sum is negative, back to $13 for twenty fills; if the
per-fill split (`live_vs_table`: seat, hold, execution/fees/model) stays within a few tenths of a point of the $13 fills, the
next step is $50 after a positive window. Deploy, no fill open (5z's check), one paste:

    set_kv() { sudo grep -q "^$1=" /etc/sniper/engine.env && sudo sed -i "s|^$1=.*|$1=$2|" /etc/sniper/engine.env || echo "$1=$2" | sudo tee -a /etc/sniper/engine.env >/dev/null; }
    set_kv STAKE_MIN 25; set_kv STAKE_MAX 25; set_kv FEED_SOCKETS 2; set_kv GAS_HEADROOM 6
    cd ~/fomo-memebot && git pull -q && sudo /opt/sniper-venv/bin/python3 deploy/relay_ops.py deposit 0.0045 | tail -2
    sudo systemctl restart sniper-engine && sleep 8 && sudo grep -h '"ev": "start"\|"ev": "venue"\|"ev": "feed2_connected"\|"ev": "feed_connected"' /var/log/sniper/engine.jsonl | tail -4 | grep -o '"ev": "[a-z_0-9]*"\|"version": [0-9.]*\|"stake_min": [0-9.]*\|"stake_max": [0-9.]*\|"snipe_tax_seconds": [0-9]*\|"snipe_tax_start_bps": [0-9]*\|"burst": \[[^]]*\]' | paste -sd' '
    sudo /opt/sniper-venv/bin/python3 deploy/relay_ops.py status 0.021190 | tail -2

Expected: `"version": 6.9`, `stake_min 25 / stake_max 25`, a `venue` line with 3 / 9900, `feed_connected` and `feed2_connected`,
the relay above 0.0095 ETH in the status. If `feed2_connected` is missing after a minute (`sudo grep -c feed2 ...`), the feed
refused the second socket; the engine runs on one as before.

**Deployed Sep 29 ~11:15 UTC:** `relay_ops.py deposit` refuses while the engine runs (same wallet, same nonce), so the order is
stop, deposit, start. After it: version 6.9, venue 3 / 9900, stake 25 / 25, both feed sockets connected, relay 0.010270 ETH
($27.90), capital 0.019923 ETH, P&L +$12.26 (a fill landed during the day, +$0.80). The $25 window starts here: twenty fills.

## 5ad. The ingress race (Sep 29, report 24.44 part B)

`deploy/ingress_race.py`: the sequencer's name resolves to one address per zone; each round signs one 0 ETH self-transfer from
the wallet and posts the identical bytes to every address at the same instant from warm sockets; only one copy is sequenced
(its reply carries the hash, the others a nonce error at no cost). Thirty rounds cost a few cents and one to two minutes of
the engine stopped (same wallet, same nonce), so run it in the quiet hours (00-12 UTC) or accept the minute:

    sudo systemctl stop sniper-engine && sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/ingress_race.py 30 2>&1 | tail -6; sudo systemctl start sniper-engine && sleep 6 && sudo grep -h '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"version": [0-9.]*'

Reading it: the engine pins the address with the lowest ping (`sender_addresses` in the log). If the race-winner is the same
address at 65% or more, nothing changes. If another address wins the race although it pings slower, the pin should follow the
race, not the ping (an engine change: `SEQ_PIN_IP`). If it is near 50/50 with a reply-time gap, a two-path fan-out of every shot
(the loser rejected free) would cut arrival variance, at the cost of 70 warm sockets; that is a separate decision after the
number exists. Nothing is deployed from this probe by itself.

**Result (Sep 29 ~11:30 UTC, 30 rounds, engine stopped for it):** the name resolves to 3.136.74.196, 3.141.111.43 and
3.142.9.34; reply medians 60.3 / 60.3 / 60.0 ms (inclusion latency, identical), local send spread 0.16 ms. Race wins:
**3.141.111.43 25 of 30 (83%)**, 3.136.74.196 5 (17%), 3.142.9.34 0. Ping cannot tell the three apart; the race can. Engine
6.9 now takes `SEQ_PIN_IP` (the race winner is pinned when it answers, the fastest ping otherwise; the `sender_addresses` log
line shows `pin_by`). Check what the engine pins today:

    sudo grep -h '"ev": "sender_addresses"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"rtt_ms_by_address": {[^}]*}\|"pinned": "[^"]*"\|"pin_by": "[^"]*"'

If `pinned` is not 3.141.111.43, with no fill open:

    set_kv() { sudo grep -q "^$1=" /etc/sniper/engine.env && sudo sed -i "s|^$1=.*|$1=$2|" /etc/sniper/engine.env || echo "$1=$2" | sudo tee -a /etc/sniper/engine.env >/dev/null; }
    set_kv SEQ_PIN_IP 3.141.111.43; cd ~/fomo-memebot && git pull -q && sudo systemctl restart sniper-engine && sleep 8 && sudo grep -h '"ev": "sender_addresses"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"pinned": "[^"]*"\|"pin_by": "[^"]*"'

Re-run the race monthly (addresses and routing change); a pin that stops answering falls back to the ping automatically.

**Checked Sep 29 11:35 UTC:** the engine pinned 3.141.111.43 at that moment (pings 0.87 / 0.83 / 2.08 ms), but it re-measures
every 20 minutes and the two front addresses are 0.04 ms apart, so the ping pin can flip to the 17% address at any
re-measurement. Set `SEQ_PIN_IP 3.141.111.43` (the paste above) so the choice is the race's, not the ping's.
**Set Sep 29 ~11:45 UTC:** `SEQ_PIN_IP 3.141.111.43`, the log reads `pinned 3.141.111.43, pin_by race`. Everything of the day is
now live: 6.9, the $25 stake, both feed sockets, the venue guard, the gas cap, the race pin.

## 5ae. Send step: keys proved at load (Sep 29)

The direct signer proves each key against eth_account on its first use, so the first burst after every restart signed in 22 ms
(13:24 today) instead of 4. The send step now proves the wallet's key and every shooter key at load. Deploy with no fill open:

    cd ~/fomo-memebot && git pull -q && sudo cp deploy/send_step.py /etc/sniper/send_step.py && sudo systemctl restart sniper-engine && sleep 6 && sudo grep -h '"ev": "start"' /var/log/sniper/engine.jsonl | tail -1 | grep -o '"version": [0-9.]*'

Check: the next burst's `sign_ms` in the reading's sent_burst line is about 4, not 22.


## 5af. Engine 6.10: the relay refilled from the loop; the shooters' gas float on the typical base fee (Sep 30)

**What happened.** The night of Sep 29-30 was the busiest window in days (51 launches; the usual-view prediction +$21 at $13,
two big fills: 20:49 +61%, 21:34 +118%). The engine fired four times (19:01 guard revert, 19:11 -0.9%, 19:30 -6.3%, 20:08 -0.8%,
every one as predicted) and then refused **32 launches over 7 hours** with `the relay holds 0.00557 ETH ($14.95) < the stake $25`,
the two big ones among them (about $45 not taken at $25). The refill after the 20:08 exit left the relay short of the float and
nothing retried it: `relay_topup` ran only after an exit, and there was no exit because nothing fired. At 23:27:59 a second alarm:
`35 shooters are out of gas and the wallet cannot refill them` — 6.9 sized a shooter's gas float on the 6x price cap at the instant
base fee, so one launch's fee ramp marked all 35 low at once and asked the wallet for 3x the ramped cap.

**6.10.**
- `relay_short()`: the relay under the next stake; the background loop calls `relay_topup("under the stake")` every `RELAY_RETRY_S`
  (60 s) while it is, outside a trade (`busy_until`), in the loop's own thread so the nonce is re-read on the next poll. One refill at
  a time (`_relay_lock`). After a wallet send (relay or shooter top-up) the local nonce follows at once (the 6.8 review's stale window).
- `relay_topup` re-reads the wallet two seconds later when the first read cannot cover the need (the sell's proceeds may not be on
  the endpoint yet). The "wallet cannot refill" alarm at most every 30 minutes.
- Shooters: the float is sized on `SHOOTER_HEADROOM` (2) x the ten-minute median base fee (`base_fee_typical`), never below
  `SHOOTER_MIN_ETH`; each shot's price cap is trimmed to what its shooter's balance covers (`shot_gas_price`); `shooter_ready` needs a
  nonce, the float and a cap over the current base fee. The top-up funds as many shooters as the wallet covers, the emptiest first.
  At today's fees nothing changes (need 0.00004, target 0.00012); a ramp no longer empties the fleet.
- `deploy/englog.py HOURS`: the log in time order across rotations, for the readings' greps.

Tests: `tests/test_relay_refill.py` (21 checks), `tests/test_feed_dual.py` (18). Deploy (the engine deposits the relay itself
within a minute of the start; no manual deposit):

    cd ~/fomo-memebot && git pull -q && sudo systemctl restart sniper-engine && sleep 30 && sudo python3 deploy/englog.py 1 | grep -h '"ev": "start"\|relay_topup\|"ev": "alarm"' | tail -3 | cut -c1-170 && sudo /opt/sniper-venv/bin/python3 deploy/relay_ops.py status 0.021190 | tail -2

Check: `"version": 6.10`, a `relay_topup` line with `"why": "under the stake"` and `"landed": true`, the relay at about 0.0111 ETH in
the status. The reading's log block from now on:

    sudo python3 deploy/englog.py 12 > /tmp/eng.jsonl; grep -c 'not fresh' /tmp/eng.jsonl; grep -c 'bundle not visible' /tmp/eng.jsonl; grep -c 'feed2_error' /tmp/eng.jsonl; grep -h '"ev": "alarm"\|"ev": "relay_topup"\|"ev": "shooter_topup"' /tmp/eng.jsonl | tail -4 | cut -c1-200
    python3 -c "import json,datetime as d;[print(d.datetime.fromtimestamp(e['t'],d.timezone.utc).strftime('%H:%M:%S'),'gated',e.get('gated'),'late_max_ms',max(e.get('late_ms') or [0])) for e in map(json.loads,open('/tmp/eng.jsonl')) if e.get('ev')=='sent_burst']" | tail -8

**Deployed Sep 30 05:40 UTC.** The start line shows `"version": 6.1` (the number is a float; `"release": "6.10"` is added for the
next restart). The loop's refill sent 0.006705 ETH within 30 s of the start (`"why": "under the stake"`, landed): relay 0.01227 ETH
($32.8, sized on the env's default ETH price before the first price poll; harmless), wallet 0.00393. The night's refill history
(englog.py 14) settled the cause: after 19:11 and 19:30 the refill was whole (0.01015 and 0.00927 ETH, short 0); after 20:08 it
sent 0.003731 with `short_of_float 0.00559` — the wallet read at that moment was 0.0054 ETH under what it held minutes later —
and nothing retried. The 23:27:59 alarm asked the wallet for 0.0472 ETH (35 shooters at 3x a 12x-ramped cap); at 23:44 for
0.0251. Under 6.10 neither would fire: the float follows the ten-minute median and a shooter at 0.00008 ETH still carries a
0.31 gwei cap.

**Sep 30 08:45 reading check.** `no confident boundary estimate` skips are creations in the last 1-2 blocks of their second (the
seat second opens before the build; report 24.48 addendum): 2 of 51 would-fires since Sep 28, both losers. Not a fault; no change.


## 5ag. Proposed: the tier gate widened to 300 bps (creator tax up to 3%, tier 4%) (Sep 30)

Report 24.49 addendum: over Sep 27-30 the launches with a 201-300 bps creator tax paid +26.7% a fire under the live rule (11
would-fires, +$38 at $13, +$73 at $25), against +7.2% in our 100-200 bps band; the 0-99 bps band stays dead. One setting
changes; the engine reads the tax from the creation calldata and models the seat with the live tax, so nothing else moves
(sizing assumes TIER_ASSUMED for the stake's gross, a 1-point difference inside the 20% burst guard). Deploy with no fill open:

    set_kv() { sudo grep -q "^$1=" /etc/sniper/engine.env && sudo sed -i "s|^$1=.*|$1=$2|" /etc/sniper/engine.env || echo "$1=$2" | sudo tee -a /etc/sniper/engine.env >/dev/null; }
    set_kv TIER_MAX_BPS 300; cd ~/fomo-memebot && git pull -q && sudo systemctl restart sniper-engine && sleep 12 && sudo python3 deploy/englog.py 1 | grep -h '"ev": "start"' | tail -1 | grep -o '"release": "[0-9.]*"\|"tier_max_bps": [0-9]*\|"dry_run": [a-z]*'

Check: `"tier_max_bps": 300`. From then on the readings' scan runs `e1_multi ... 0.02 0.04` and the reconciliation tags each
fill with its tier band; the $25 window and the sequential test count the new band separately for its first 20 fills.

**Audit (Sep 30 10:30 UTC), passed; decision: deploy.** (1) The creator tax charged on the chain in the E1 block matches the
model's tier on all 11 would-fires (2.2-3.0%; platform fee 7.18% = 1% + the 6.18% surcharge). (2) The hold-grid model charges
the tier on the buy and on the sell. (3) The engine: the gate is `tax > TIER_MAX_BPS`, so 300 admits up to 300 bps; sizing
assumes TIER_ASSUMED 5% (conservative for a 4% tier); the sell carries no fee-based minimum; the fold uses the live tax.
(4) The full engine replay (every gate: creator supply, cap, repeat, bundle, registration, the guard at slip 0.20) over
Sep 27 09:15 - Sep 30 08:26 with the gate at 200 and at 300: 35 -> 45 fills, 8 -> 9 guard reverts, +$33.82 -> +$71.60 at $13;
the ten added fills +$38.15 ($73 at $25), 8 of 10 positive, the one -25% launch reverts at the guard; no fill of the current
band lost. (5) Positive on each of the three days; +$20.6 without the +135% launch. (6) Nothing in the earlier work prices the
band against it. Bound: the band's own tally for its first 20 fills in the readings; back to 200 if it is negative then.
`engine_replay.py` now replays the 300 gate by default (`REPLAY_TIER_MAX=200` for the old one); the readings' scan runs
`e1_multi ... 0.02 0.04`.

**Deployed Sep 30 10:40 UTC:** `"tier_max_bps": 300`, release 6.10, live. The readings tally the 201-300 bps band separately from here.


## 5ah. The reading, current version (Sep 30): one place for both sides

Both sides of a reading use the newest code: the chain side through `src/analysis/score_window.sh` (the live settings baked
in: tiers 2-4%, the attackers gate at 3 fleets, hold 11, guard 0.20, the three engine views; since Oct 1 the replay marks the
fills a boosted helper attacked as `BOOST`, the fills the engine stakes $50 on, and tallies them on a `boosted` line), the box
side through the block below, which pulls first (`live_vs_table.py` closes with a `boosted $50` line next to the band lines,
the fills at their real stake). When a live setting changes, this section and the script change with it; older reading
blocks in this runbook are history.

Chain side, before the box is read (the prediction is committed before the paste):

    bash src/analysis/score_window.sh NAME "YYYY-MM-DD HH:MM"

Health, any time (services, the last start line, the flow line, the last 3 hours' events and alarms, an open position, the P&L):

    cd ~/fomo-memebot && git pull -q && sudo bash deploy/health.sh

Box side (the owner pastes the output):

    cd ~/fomo-memebot && git pull -q && sudo /opt/sniper-venv/bin/python3 deploy/relay_ops.py status 0.021190 | tail -2
    sudo python3 src/analysis/paper_day.py --from "YYYY-MM-DD HH:MM" --stake 25 --hold 11 2>&1 | tail -8
    python3 src/analysis/live_vs_table.py 2>&1 | tail -8
    sudo python3 src/analysis/engine_vs_chain.py data/derived/live_vs_table/launches_NAME.json --crowd data/derived/live_vs_table/crowd_raw_NAME.json.gz --from "YYYY-MM-DD HH:MM" --to "$(date -u +'%Y-%m-%d %H:%M')" | tail -12
    sudo python3 deploy/englog.py 12 > /tmp/eng.jsonl; grep -c 'not fresh' /tmp/eng.jsonl; grep -c 'feed2_error' /tmp/eng.jsonl; grep -h '"ev": "alarm"\|"ev": "relay_topup"\|"ev": "shooter_topup"' /tmp/eng.jsonl | tail -4 | cut -c1-200
    python3 -c "import json,datetime as d;[print(d.datetime.fromtimestamp(e['t'],d.timezone.utc).strftime('%H:%M:%S'),'gated',e.get('gated'),'late_max_ms',max(e.get('late_ms') or [0])) for e in map(json.loads,open('/tmp/eng.jsonl')) if e.get('ev')=='sent_burst']" | tail -8

`live_vs_table.py` closes with one line per creator-tax band (100-200 and 201-300 bps): the new band's fills, mean, positives
and net, its own tally for the first 20 fills (5ag). The $25 window rule (5ac) counts every fill; the band line says whether
the new band is carrying or dragging it.


## 5ai. Telegram P&L notifications (Sep 30)

`deploy/tg_notify.py`, service `sniper-notify`: one message, the same line as the box's `pnl`, only when the P&L changes:

    balance 0.018972 ETH ($50.70) | P&L +0.003560 ETH ($9.51) (+23.1%)

A separate process that never touches the engine: it reads the engine's log to learn that a trade closed or a burst landed
(then reads the balances 25 s later, once the refill is in) and reads them every 10 minutes regardless; it sends when the
P&L in ETH moved by 0.00005 ETH or more since the last message (a trade or a burst's gas; the ETH price moving does not
count). It runs 24/7 as a systemd service, restarts on a crash or a reboot, and does not depend on any terminal being open.
Secrets in `/etc/sniper/telegram.env` (root, 0600): `TG_TOKEN`, `TG_CHAT`, `TG_PNL_BASE` (the baseline, 0.015412).

Setup, once:
1. In Telegram, open @BotFather, send `/newbot`, give it a name and a username; it answers with the bot token. Then open the
   new bot's chat and send it any message (that is how the installer learns the chat id).
2. On the box (the token is typed at the prompt, never pasted into the chat with the assistant):

       sudo sh -c 'read -p "bot token: " T; printf "TG_TOKEN=%s\n" "$T" > /etc/sniper/telegram.env; chmod 600 /etc/sniper/telegram.env' && cd ~/fomo-memebot && git pull -q && sudo bash deploy/tg_install.sh

   The first line arrives on the phone right away; the next ones only when the P&L moves.

Check: `sudo systemctl status sniper-notify | head -3`; `sudo python3 deploy/tg_notify.py --test` sends the line once. Off:
`sudo systemctl disable --now sniper-notify`.

**Installed Sep 30 11:35 UTC** on the box (chat id detected from the START press; service active).

**Sep 30 11:55 reading (piece sep30pm, 08:19-11:49).** Usual view 2 fills (-9.7%, -11.9%); the engine fired nothing: 08:28 counted 1 fleet of 71 wallets where the chain view counts 2 (gate closed), 09:59 the bundle was not visible on the feed within 900 ms / 9 blocks (skip). Both saved money this time; both are measurement gaps that would skip winners at the same rate, tallied as classes (24.49). No 3-4% tier launch yet. P&L unchanged, relay 0.01227, no alarm, late_max 0.12 ms.


## 5aj. Engine 6.11: the exit reads the chain from two nodes (Sep 30)

**What happened (16:53 UTC, curve 0xc2f323a4).** The buy filled; the approve and the sell went out 3 s later than usual and
landed at +22 and +40 blocks; then the provider's node, which the engine reads receipts and nonces from, ran about 20 s behind
the chain: no receipt for the sell, the same pending nonce, so `send_confirmed` re-sent the sell thirteen times (the sequencer
answered "nonce too low" each time, meaning the first one had landed), raised `sell not confirmed after 21.3 s`, kept the
position open (a launch at 16:53:19 was refused for it) and closed it 27 s after the buy when the retry saw the token balance
at zero. The 15:30 trade had the same shape with a 4.7 s confirmation. On the chain: no fee ramp, the first attempt landed,
the extra sends cost nothing. The three earlier trades of the day confirmed in 0.13 s. Cost this time: nothing (both tokens
flat); on a winner a sell landing at +40 blocks instead of +11, or a refused launch, would have.

**6.11.**
- `wait_receipt` asks the sequencer's own RPC (`rpc_logs`, rpc.mainnet.chain.robinhood.com) on every second poll (every tenth
  for the burst's 35 hashes); `next_nonce` takes the higher of the two nodes' pending counts.
- `landed_on_chain(nonce, effect)`: a node whose confirmed nonce is past the transaction's, and on which the job is done (the
  tokens gone for a sell, the allowance in place for an approve), proves the landing; a node behind the buy can never count
  (its zero balance predates the buy). `send_confirmed(..., effect=)` uses it after a missed receipt and on "nonce too low",
  returning an inferred receipt (status 0x1, `landed_inferred` in the log) instead of re-sending for 20 s.
- Nothing on the fire path changes. Tests: `tests/test_sell_landing.py` (12 checks).

Deploy (the engine keeps an open position across a restart and resumes its sell):

    cd ~/fomo-memebot && git pull -q && sudo systemctl restart sniper-engine && sleep 12 && sudo python3 deploy/englog.py 1 | grep -h '"ev": "start"' | tail -1 | grep -o '"release": "[0-9.]*"\|"tier_max_bps": [0-9]*\|"dry_run": [a-z]*'

Check: `"release": "6.11"`. In the readings: `sell_confirm_s` back under a second, no `resend` chains, no `landed_inferred`
unless the provider lags again (then one per trade, and the trade closes within a second anyway).

**Deployed Sep 30 17:35 UTC:** release 6.11, tier max 300, live. The two trades before it (17:09 +44.8%, first in the block, +$10.68; 17:12 -0.8%) confirmed in 0.22 s and 0.21 s at +12 blocks: the exit path is fine when the provider keeps up.

**Sep 30 17:40 reading (pieces sep30eve, sep30night).** 11:49-17:22: five fires as the chain view named them (13:56 guard revert, the first 3-4% band fire; 15:13 +1.6%; 15:30 -11.9%; 16:53 -11.9%; 17:09 +44.8% landed first; 17:12 -0.8%), the 14:57 launch skipped for an invisible bundle (-8.8% avoided). P&L +$4.34 -> +$14.99, capital $56.34, the $25 window at 8 fills of 20.


## 5ak. The attackers gate raised to 3 fleets (Sep 30 20:30 UTC)

**Why.** The owner's reading of the ledger was right: more losers than winners and a P&L that drifts. The full engine replay
(every gate, hold 11, guard 0.20, the 300 bps tier gate) over Sep 24 22:00 - Sep 30 20:05, 632 launches, split by the fleets
the usual view counts before the tick:

| gate | fills | positive | mean | $ at $13 / 5.9 days | bursts (gas) |
|---|---|---|---|---|---|
| 2 fleets (live until now) | 78 | 56% | +12.2% | +$94.45 | 89 ($29) |
| 3 fleets | 40 | 72% | +22.2% | +$99.92 | 47 ($16) |
| 4 fleets | 19 | 84% | +29.3% | +$64.38 | 24 |

The 38 fills the 3-fleet gate drops (exactly 2 fleets) pay +1.7% mean, 39% positive, +$8.39 in total - and that total is
Sep 25 alone (+$19.89, one +107% launch); Sep 26-30 they lose on five days of five (-$0.01, +$1.04, -$1.22, -$4.63, -$6.68 at
$13). The fills it keeps (3+ fleets) are positive on every one of the six days. Sep 30 was the extreme: 73% of the fires
were 2-fleet fires, 11 of them, -$12.85 at $25; the 3+ fires +$2.26. The mechanism reads as a regime: as the venue's bot count
grew, two fleets attacking a launch became ordinary noise, three or more still means demand behind us.

**The change.** `ATTACK_MIN` 2 -> 3. Half the fires, the same dollars in expectancy, three losers fewer in every four fires,
half the gas. The stake window (5ac) keeps counting fills; it will take longer to reach 20. Reversible in one line; the
chain-side pieces keep scoring the 2-fleet launches, so the readings will show if they start paying again (then 2 comes back).
`engine_replay.py` replays either gate with `REPLAY_ATTACK_MIN`.

    set_kv() { sudo grep -q "^$1=" /etc/sniper/engine.env && sudo sed -i "s|^$1=.*|$1=$2|" /etc/sniper/engine.env || echo "$1=$2" | sudo tee -a /etc/sniper/engine.env >/dev/null; }; set_kv ATTACK_MIN 3; cd ~/fomo-memebot && git pull -q && sudo systemctl restart sniper-engine && sleep 12 && sudo python3 deploy/englog.py 1 | grep -h '"ev": "start"' | tail -1 | grep -o '"release": "[0-9.]*"\|"attack_min": [0-9]*\|"tier_max_bps": [0-9]*\|"dry_run": [a-z]*'

Check: `"attack_min": 3`.

**Deployed Sep 30 20:40 UTC:** `"attack_min": 3`, release 6.11, tier max 300, live.


## 5al. Engine 6.12: the team-bundle gate, built and off (Sep 30 21:30 UTC)

`NAMED_MAX` (default 0 = off): a creation naming more exempt wallets than this is skipped as a team bundle (report 24.50).
On the week it is a wash in dollars on top of the other gates (10 fewer fires, +$0.6), so it stays off; `REPLAY_NAMED_MAX=12`
replays it. The engine's release string moves to 6.12 with the next restart; no restart is needed for this.


## 5am. Engine 6.13: the boosted stake on the smart helpers (Sep 30 23:30 UTC)

**The finding (report 24.50).** Each bot attacks through its own helper contract, visible in the creation second before our
shots leave. Helpers whose attacked launches paid (4+ launches, mean over +5% behind one at hold 11, trailing 7 days) are
'smart'. Fitted on each day's history and applied to the next day, Sep 26-30, on the 3+ fleet class: $50 when a smart helper
is attacking, $25 otherwise, pays +$470 against +$257 flat on the same 52 fills (31 boosted). As a filter it adds nothing;
as a stake signal it nearly doubles the dollars. On our own 28 live fills: smart helper present +7.0% (18), absent -2.9% (6).

**How it works.** `STAKE_BOOST_USD` (0 = off). At the build, when a smart list is loaded and the relay holds the boosted
stake, the engine sizes a second buy (the same guard rule) and the send step signs both sets - the boosted one only when the
signing cannot delay the first shot. At each shot's time the send step asks `smart_present(w)` (a smart helper among the
curve's `attack_targets`) and sends the boosted shot when it is true. The landing log says which stake filled (`boost`,
`stake_usd`); `sent_burst` counts the boosted shots. The relay float is 1.2 x the boosted stake ($60); the loop refills the
relay to the float (not only to the base stake), so a deposit to the wallet reaches the relay within a minute.

**The list.** `data/derived/smart_helpers.json`, written by `src/analysis/smart_helpers.py` at the end of every
`score_window.sh` run and committed; the box pulls it in the reading and the engine reloads it hourly when the file changed.
Fitted Sep 30 23:20: 14 helpers of 65 seen over 594 launches.

Tests: `tests/test_stake_boost.py` (15 checks: the list, the pick at fire time, the no-time-to-sign fallback, the gate).

**Capital.** The boosted shots need the relay at $60: about $75 on the box. Send about 0.013 ETH to the wallet
(0xe0686dc72b04c12ceefeea75e286e4ef7c056f01); the engine moves it to the relay. Until then the boost is not built and every
fill is $25.

Deploy (the send step changed, so it is copied):

    set_kv() { sudo grep -q "^$1=" /etc/sniper/engine.env && sudo sed -i "s|^$1=.*|$1=$2|" /etc/sniper/engine.env || echo "$1=$2" | sudo tee -a /etc/sniper/engine.env >/dev/null; }; set_kv STAKE_BOOST_USD 50; cd ~/fomo-memebot && git pull -q && sudo cp deploy/send_step.py /etc/sniper/send_step.py && sudo systemctl restart sniper-engine && sleep 12 && sudo python3 deploy/englog.py 1 | grep -h '"ev": "start"\|"ev": "smart_helpers"' | tail -2 | grep -o '"release": "[0-9.]*"\|"stake_boost_usd": [0-9.]*\|"smart_helpers": [0-9]*\|"n": [0-9]*\|"dry_run": [a-z]*'

Check: `"release": "6.13"`, `"stake_boost_usd": 50.0`, `"smart_helpers": 14`. In the readings: `boost` on the landing line,
the $50 fills in their own tally (the stake shows in `live_vs_table`'s stake column).

**Deposit Sep 30 23:55 UTC:** +0.005778 ETH ($17) to the wallet; the engine moved it to the relay (0.0210 ETH, $56): the boost is live. The P&L baseline moves from 0.015412 to **0.021190 ETH** (the deposit added); `pnl`, the notifier (`TG_PNL_BASE`) and the readings use it.


## 5an. Engine 6.14: the two-shot burst, built and off; the audit of 6.13 and 6.14 (Oct 1 00:40 UTC)

**The two-shot burst.** `SHOTS_PER_SHOOTER` (default 1): with 2, every shooter sends a second shot at its next nonce after the
first wave, 70 shots at the same 2 ms spacing, 140 ms of coverage; with `BURST_LEAD_MS 90` and `GATE_CLOSE_MS 80` the burst
spans -90..+48 ms around the aim (today -46..+22, gate closing 10 ms before the aim in both). The second wave's receipts are
polled 0.3 s later at half the cadence, so the provider's load stays that of one wave when the first fills. Nonces: one
provisional +1 per sent shot, one give-back per refused shot; a second-wave shot whose first-wave shot was dropped is refused
by the sequencer and given back the same way; the chain read after the burst corrects any drift.

**Why it stays off at this size (the honest arithmetic, report 24.50 addendum).** 7 of 28 live bursts began after the seal
and paid +0.9% at 43% first place; the 21 straddled ones +5.0% at 52%. Covering those seven is worth about +4 points on a
quarter of the fills, +1 point a fill: at $25 that is +$0.25 a fill, at the boosted $50 +$0.50, about +$1.2 a day at three
fills. The certain cost: about 35 more reverted shots a burst, $0.33, about +$1.7 a day at five bursts. Break-even to
slightly negative at $25-50; positive from $100 a fill, where the same point is worth $1 a fill. Switch on at the $100 step:

    set_kv SHOTS_PER_SHOOTER 2; set_kv BURST_LEAD_MS 90; set_kv GATE_CLOSE_MS 80   (then restart)

**Audit of 6.13, the boosted stake.** Evidence: five walk-forward days, every day's list fitted on the days before; +$470
against +$257 on the same 52 fills; unchanged under a positive-share floor (0.4, 0.5) or a higher minimum count (6): the
boosted fills are the same; on our own live fills +7.0% with a smart helper attacking against -2.9% without. Code, read
adversarially: the two variants share a nonce, so one of them goes per shooter; each variant carries its own minOut from the
same sizing; the boosted set is signed only when it cannot delay the first shot, else the burst is the base one and the skip
is logged; the boost is built only when the relay holds the boosted stake, and one position at a time keeps a stale relay
read from building one the relay cannot pay; the pick is a set intersection under a try (the feed thread grows the set while
the burst reads it - a copy can raise; 6.14 retries once and answers False, the send step never lets the pick break a shot);
the landing log names the stake that filled; the float covers the boosted stake and the loop refills to the float, so a
deposit reaches the relay within a minute. Known and accepted: `paper_day` simulates the guard with the base amount (its
GUARD column is approximate on boosted fills; `live_vs_table` reads the chain's amounts and is exact); the smart list is a
seven-day trailing fit of bot software contracts, refitted in every reading; a bot changing contracts drops out until it
earns its way back. Risk stated plainly: the boosted dollars concentrate on the launches a handful of bots attack; the
readings tally the $50 fills on their own line, and STAKE_BOOST_USD 0 turns it off in one line.

**Audit of 6.14 as deployed with SHOTS_PER_SHOOTER 1:** the burst is byte-for-byte the 6.13 burst (one wave, all pollers
immediate); the only live changes are the hardened pick and the receipt poll cadence parameter at its old value.
Tests: `tests/test_stake_boost.py` 21 checks (the list, the pick, the fallbacks, the gate, the two-wave receipts, the nonce
bookkeeping, the race). Deploy (the send step changed):

    cd ~/fomo-memebot && git pull -q && sudo cp deploy/send_step.py /etc/sniper/send_step.py && sudo systemctl restart sniper-engine && sleep 12 && sudo python3 deploy/englog.py 1 | grep -h '"ev": "start"\|"ev": "smart_helpers"' | tail -2 | grep -o '"release": "[0-9.]*"\|"stake_boost_usd": [0-9.]*\|"shots_per_shooter": [0-9]*\|"n": [0-9]*\|"dry_run": [a-z]*'

**Deployed Oct 1 04:50 UTC:** release 6.14, boost $50 (14 helpers loaded), one shot per shooter, live.


## 5ao. Oct 1 05:15 reading (piece oct01night, Sep 30 20:05 - Oct 1 05:09 UTC)

Chain side first, with the live settings (tiers 2-4%, 3 fleets, hold 11, guard 0.20): 1,584 creations, 22 qualifying.
- Usual view (k-1 with the registration block, the live centre): 2 fills, 21:04 0x1daf553a +42.7% (4 fleets) and 21:26
  0xf78e378c +78.8% (7 fleets); 2 guard reverts, 21:24 0x5c9177c6 and 04:14 0x14479a88 (gas only). Floor (k-2): the same
  two fills, one guard. Ceiling (k): a third fill, 22:38 0x14e238da +6.8%. All four fired launches had a boosted helper
  attacking; at $25/$50 the two fills net +$60 against +$30 flat (they came before the boost went live, so $25 is the
  expectation for them). The 20:08 launch (2 fleets, +39.8%) sits before the 3-fleet gate's deploy at 20:30: a fill if the
  engine fired it, refused by the gate after. 13 launches refused for fewer fleets: mean -7.0%, 15% positive. The smart
  list refit on the window: 15 helpers (was 14); the box pulls it with the reading and the engine reloads it within the hour.

**Box side (05:20 UTC).** Capital $67.16, P&L since the reset +0.003575 ETH (+$9.69, +16.9%): the +$9.9 expected less one burst's gas.
No fill in the window; the $25 window stays at 13 of 20 fills. Engine against the chain, launch by launch:
- 20:08 0x04e4af02 (2 fleets, before the 3-fleet gate's deploy): fired, the 35 shots landed in the seat second's 6th block
  behind 4 buys, all reverted on the guard. Gas only. The chain's +39.8% assumed the seat block; priced where the shots
  landed it was -29% (report 24.51), so the guard was right.
- 21:04 0x1daf553a (4 fleets): fired, the shots landed in the 8th-15th blocks of the seat second behind 8 buys, all reverted.
  Gas only. Chain +42.7% from the seat; -10% where we landed. Same class: the slow-sequencer regime (24.51).
- 21:24 0x5c9177c6 (boosted, 35 shots at $50): 18 shots in the creation second's last block, 17 in the seat block, all
  reverted on the guard, as the chain predicted. Gas only.
- 21:26:18 0xf78e378c (+78.8% on the chain, 4-7 fleets, a boosted helper attacking): refused "nonce/gas not fresh" 3 s after
  the gated burst at 21:26:15 released its reserved wallet nonce by invalidating it. Nothing had left the wallet. A bug: fixed
  in 6.15 (5ap). The same refusal took a +17.6% launch on Sep 28 19:44. Two in seven days, both winners.
- 22:07-03:52: seven launches at 0-2 fleets, the gate never opened, no shot sent; the chain scored the refused set -7% mean.
- 04:14 0x14479a88: the first boosted fire of 6.14 (28 shots at $50, 7 gated): 25 shots in the creation second's last block,
  3 in the seat block, reverted on the guard as the chain predicted. Gas only, the P&L's -$0.33.
Hygiene: 2 "not fresh" and 3 feed2 errors in 12 h; the relay alarm every 30 min was the $60 float against a $56 relay and a
$3.8 wallet (harmless: the boost built and fired at 04:14); `RELAY_FLOAT_USD=55` set and the engine restarted at 05:25.


## 5ap. Engine 6.15: the released nonce is re-read; the landing log shows where the shots landed (Oct 1 06:30 UTC)

- `release_reservation()` (every gated burst, no-fill burst and pre-burst refusal) now reads the wallet's pending nonce from the
  two nodes at once and marks it fresh; both nodes failing leaves the old rule (the next launch waits for the poll). The
  shooters fire the shots, so the wallet's count is whatever the chain says; nothing can be stranded by reading it.
- `burst_landing` carries `land_off` (the first landed shot's block counted from the seat second's first block: -1 the
  creation second's last block, 0 the seat block, +5 five blocks late) and `load_txpb` (the feed's transactions per block over
  the ten blocks before the burst). Report 24.51: the week's 41 bursts placed on the chain by hand; from now on every reading
  has both numbers in the log.
- Tests: `tests/test_release_nonce.py` (15 checks: the two nodes, one down, both down, the poll winning the race, a raising
  read, the offset, the load).

Deploy (the send step is unchanged):

    cd ~/fomo-memebot && git pull -q && sudo systemctl restart sniper-engine && sleep 12 && sudo python3 deploy/englog.py 1 | grep -h '"ev": "start"' | tail -1 | grep -o '"release": "[0-9.]*"\|"stake_boost_usd": [0-9.]*\|"dry_run": [a-z]*'

Check: `"release": "6.15"`. In the readings: `land_off` on every landing line; no "not fresh" refusal within 30 s of a burst.


## 5aq. Engine 6.16: the sequencer-door probe (Oct 1 07:30 UTC)

The week's reply times (24.51): every shot of the seven bursts in the slow regime was acknowledged by the sequencer 0.6-4 s
after it was posted, every other burst in 60-230 ms, and the slow ones landed 5-33 blocks after the seat block. The door is
measurable without a burst: a signed transaction the sequencer always rejects (the wallet's nonce 0, long spent: "nonce too
low", nothing on the chain, no gas), posted every `PROBE_EVERY_S` (10) from its own thread, its reply timed. The latest
probe, its age and the median of the last six ride on every decision (`seq_rtt_ms`, `seq_rtt_age_s`, `seq_rtt_med_ms`) and
on every `burst_landing`; the ten-minute `flow` line carries the median. `SEQ_RTT_SKIP_MS` (0 = off) skips the burst when the
last probe is under thirty seconds old and slower than the limit: built, off until the probe is seen agreeing with the
shots' reply times on a slow burst (a reading's job), then `set_kv SEQ_RTT_SKIP_MS 400`. `tests/test_seq_probe.py` (16 checks).

Deploy (the send step changed: `make_probe`):

    cd ~/fomo-memebot && git pull -q && sudo cp deploy/send_step.py /etc/sniper/send_step.py && sudo systemctl restart sniper-engine && sleep 25 && sudo python3 deploy/englog.py 1 | grep -h '"ev": "start"' | tail -1 | grep -o '"release": "[0-9.]*"\|"probe": \[[^]]*\]\|"dry_run": [a-z]*'; sudo python3 deploy/englog.py 1 | grep -c '"stage": "probe"'

Check: `"release": "6.16"`, `"probe": [true, 10.0, 0.0]`, and a zero count of probe errors. The first `flow` line (ten
minutes in) shows `seq_rtt_med_ms` around 60-100 at rest.


## 5ar. Oct 1 21:30 reading (piece oct01day, Oct 1 05:09 - 20:49 UTC): the best day, launch by launch

Chain side (tiers 2-4%, 3 fleets, hold 11, guard 0.20): 3,322 creations, 95 qualifying. Usual view: 6 fills, 1 guard, +7.0%
mean, 5 of 6 with a listed helper attacking. Box side: P&L +$81.21 since the reset (+142%), capital $138.37, no deposit; Oct 1:
6 fills, 3 up, net +$68.98; the five boosted $50 fills net +$70.76. Engine against the chain:

| time | chain, behind one | engine | note |
|---|---|---|---|
| 07:39 | +78.4% | +80.3%, $50, first in the block | matched |
| 07:46 | -1.1% | no fill: the shots landed 9 blocks late, replies 7.6 ms on the probe, 22 txs a block on the feed | the slow door; nothing lost |
| 09:26 | guard revert | not fired (the engine's view had fewer fleets) | nothing lost |
| 15:36 | -9.8% (22 named wallets: the replay's team-bundle gate refuses it, live NAMED_MAX is off) | -7.4%, $25 | the one the named gate would have saved, $1.86 |
| 17:52 | -2.0% | -2.6%, $50 | matched |
| 18:28 | +17.3% | +30.9%, $50, first in the block | better than the model |
| 18:43 | +8.0% (no listed helper) | no fill: the shots landed 33 blocks late, the probe read 2.0 ms | the slow door, unseen by the probe; $2 lost |
| 20:45 | -58.5% | -58.1%, $50, first in the block | the team dump (below) |
| 20:52 | outside the window | +97.6%, $50 | |

**The -$29 trade (20:45, 0x0e354e61).** Execution was perfect: first in the seat block, sold 11 blocks later in 1.09 s. The
creator's five bundle wallets had bought 0.82 ETH (33% of the supply) in the creation second and sold all of it in one
block, +8, into a crowd of six small buys (0.14 ETH); the curve fell from 2.51 to 1.74 ETH before our sell. The creator and
the five wallets had never launched before. Across the week's 47 fired launches this is the only one where the team sold
inside the hold (the other 46: 0-1% of their tokens); nothing before the tick marks it (an ordinary bundle, 3 fleets, a
listed helper attacking). A stop cannot beat it: the six sells sat in one block, and a sell of ours at +9 would have got the
same price as at +11. It is the "dead" column of the model, 2% of fills, priced in. No change.

**The probe is not a detector.** Both slow-door misses today (07:46, 18:43) read 7.6 and 2.0 ms on the probe while the shots
waited 1-3 s: the sequencer rejects the nonce-0 transaction before the queue the shots stand in. `SEQ_RTT_SKIP_MS` stays off
for good; the probe stays as a cheap record of the RPC front's latency. The shots' own reply times remain the measure.

**The $25 window** stands at 19 fills of 20, net far positive. The next fill closes it, and the step is the base stake to $50 and
the boost to $75 (not $100: a boosted fill would be 72% of today's capital, and the 20:45 dump shows what one fill can cost);
the boost goes to $100 when the capital passes $200. After the next fill:

    set_kv() { sudo grep -q "^$1=" /etc/sniper/engine.env && sudo sed -i "s|^$1=.*|$1=$2|" /etc/sniper/engine.env || echo "$1=$2" | sudo tee -a /etc/sniper/engine.env >/dev/null; }; set_kv STAKE_MIN 50; set_kv STAKE_MAX 50; set_kv STAKE_BOOST_USD 75; set_kv RELAY_FLOAT_USD 90; sudo systemctl restart sniper-engine && sleep 12 && sudo python3 deploy/englog.py 1 | grep -h '"ev": "start"' | tail -1 | grep -o '"release": "[0-9.]*"\|"stake": \[[^]]*\]\|"stake_boost_usd": [0-9.]*\|"dry_run": [a-z]*'

Hygiene: the feed refused five connections at 15:33 (HTTP 429) and the engine ran on the provider path for 120 s, then came
back (the 15:36 fire was on the feed again); one feed stall at 18:27; the relay alarm until the 05:25 float change; nothing
since. Smart list refit: 16 helpers.

**Deployed Oct 1 21:45 UTC:** base stake $50, boost $75, relay float $90, release 6.16, live; one fill before the $25 window's
twentieth. The $50 window starts here: 20 fills, counted in the readings; the base goes to $100 when it closes positive and the
capital allows a $100 fill at under half of it; the boost to $100 when the capital passes $200. The relay refills from the
wallet to the $90 float within a minute of the restart (`relay_topup` in the log); the boost builds once it holds $75.


## 5as. Oct 2 09:30 reading (piece oct02night, Oct 1 20:49 - Oct 2 08:58 UTC)

Chain side first (tiers 2-4%, 3 fleets, hold 11, guard 0.20): 1,689 creations, 46 qualifying, quiet and slightly negative.
- Usual view (the live centre): 2 fills, 23:14 0x74c0183c -3.7% and 00:24 0xfeefb6d7 -4.0%, both with a listed helper
  attacking (so $75 live); 1 guard revert, 20:52 0xdc93b9c0, which the engine in fact filled at +97.6% first in the block
  (the replay's guard prices the seat behind one; first place clears it). Floor: the 00:24 fill only. Ceiling: the same as
  the usual view. Expected on the box for the window after 20:52: two small losers, about -$6 at $75, plus gas.
- 39 launches refused for fewer than 3 fleets: -9.9% mean, 5% positive. 10 refused by the replay's team-bundle gate
  (14-22 named wallets; live NAMED_MAX is off, so the engine may have fired some of them: the box side says).
- Smart list refit: 16 helpers.

**Box side (09:40 UTC).** Capital $137.99, P&L +$79.75 since the reset (+137%); overnight -$2.9. One fire, one fill: 23:14
0x74c0183c, the first $75 fill (a listed helper attacking), landed in the straddle, sold in 1.18 s, -3.7% as the chain
priced it. The 00:24 launch (chain -4.0%) the engine did not fire: its own fleet count stayed under 3 (a measurement-gap
refusal that saved $3 this time). The 20:52 fill (+97.6%, counted on Oct 1) was the night's other fire. Nine launches with
14-22 named wallets, two serial creators' templates (a 2.9% tier with 14-19 wallets, a 4% tier with 15 wallets and 1.1 ETH
bundles), were all refused by the creator-repeat gate or for fewer than 3 fleets: the team-bundle class needs no gate of
its own while those hold. The stake step restarted the engine at 21:25 and the relay refilled to the $90 float at once
(relay 0.0333 ETH). No alarm, no "not fresh", no open position. The public RPC answered a block-number query in 1.1 s from
the box (normally 50 ms) and the trade-reconciliation script timed out at 240 s on its 36 trades: the node was sluggish
this morning, the engine's exits read two nodes and were not affected. The $50 window: 1 fill of 20 (-3.7%).


## 5at. Engine 6.17: the sell goes out with nothing in front of it (Oct 3 00:30 UTC)

**What happened on Oct 2.** Eleven trades, every entry in the right spot (first shot in the straddle or the seat block), and
the day -$22.51. Priced from the chain: the three sells that landed 12-13 blocks after the buy returned +21%, +8%, -7%; the
eight that landed 18-24 blocks after it returned -13%, +20%, -8%, -12%, -18%, -5%, -12%, -4%. The exit sells 11 feed blocks
after the buy; before sending it read the wallet's token balance and the approve's receipt, two or three queries that take
150 ms on a normal day and took one to two seconds on Oct 2, when the public node answered a block-number query in 1.1 s.
A sell at +20 lands in the bots' dump; at +12 it lands before it (the week's holds: +28.5% at 11 blocks, +21.6% at 13).

**6.17.**
- The buy's receipt event gives the exact token amount (`tokens_wei`) and the buy's block (`buy_block`); the first sell uses
  that amount with no balance read. A retry (a sell hash already exists) or a position from before 6.17 reads the balance as
  before; a reverted sell is still diagnosed from the chain.
- The approve is sent at the buy and confirmed by the watcher thread during the hold (`approve_ok`); when it is, the exit
  skips the receipt query. When it is not, `ensure_approved` runs first, as before.
- The receipt poll's alternate node (the public RPC) is a 0.7 s-bounded client, so a slow public node cannot stall the poll
  a second per turn.
- `trade_done` carries `hold_blocks` (the sell's block minus the buy's) and `exit_prep_s` (the time from the hold's end to
  the sell's send). Healthy: 11-13 and under 0.02 s.
- Tests: `tests/test_exit_prep.py` (8 checks), `tests/test_sell_landing.py` updated for the bounded node.

Deploy (no send-step change):

    cd ~/fomo-memebot && git pull -q && sudo systemctl restart sniper-engine && sleep 12 && sudo python3 deploy/englog.py 1 | grep -h '"ev": "start"' | tail -1 | grep -o '"release": "[0-9.]*"\|"stake": \[[^]]*\]\|"stake_boost_usd": [0-9.]*\|"dry_run": [a-z]*'

Check: `"release": "6.17"`. In the readings: `hold_blocks` 11-13 on every trade_done; `exit_prep_s` near zero.

**Deployed Oct 2 23:38 UTC:** release 6.17, base $50, boost $75, live.


## 5au. Oct 3 09:40 reading (piece oct03, Oct 2 23:19 - Oct 3 09:10 UTC)

Chain side first: 859 creations, 7 qualifying, the quietest night yet (46 the night before). The replay in `score_window.sh`
was still refusing team bundles (more than 12 named wallets), a gate that is off live (NAMED_MAX, 5al); fixed in the script
(`REPLAY_NAMED_MAX=0`), and the window re-run with it. Usual view: no fill. One fire, 05:56 0x8cae613b (3-4 fleets, a listed
helper attacking, so $75): the seat behind one buy is past the minOut guard, so a guard revert and gas only, unless the burst
landed first in the block, where the chain scores it far up (behind one +264%). 01:30 0x4a81ceda (4 fleets, -13.8%) refused
by the bundle cap (more than 3 ETH). Five launches refused for fewer than 3 fleets, all -11% to -14%. Expected on the box: P&L
flat to -$0.5 of gas, one burst at 05:56; the open question is whether it landed first.


## 5av. The readings' scan on a second endpoint (Oct 3 10:00 UTC)

The chain side of a reading spends most of its 20-30 minutes waiting on the public node, which throttles past three requests
at once. `src/analysis/rpc_route.py` sends the per-block and per-transaction reads (`eth_getBlockByNumber`,
`eth_getTransactionByHash`, receipts) to `ALCHEMY_READ_URL` when that variable is set, under a shared limit of `ALCHEMY_RPS`
(20 a second; the free plan allows 25), and runs the launches in parallel (8 threads in `e1_multi.py`, 6 in `crowd_raw.py`);
the log searches (`eth_getLogs`) stay on the public node, whose block ranges Alchemy's free plan limits. Unset, every script
behaves exactly as before (tested: the crowd file of piece oct03 reproduced byte for byte; the routed path gives the same
output, 40 s down to 12 s on that piece). Cost: about 60,000 compute units a reading against 30 million free a month.

Setup, once (the owner):
1. Alchemy dashboard: create a new app (free plan) on the same network the engine uses, and copy its HTTPS URL. A separate
   app from the engine's, so the readings never draw on the engine's limits. The engine's network, without its key:
   `sudo grep -o '^RPC_URL=https://[^/]*' /etc/sniper/engine.env`
2. This cloud environment's settings (the environment menu in the session's title bar, then Edit): an environment variable
   `ALCHEMY_READ_URL` with that URL. Never in the chat, never in the repository.
3. A new session picks it up. The scan prints which endpoint it uses on its first line.

**Oct 3 10:30 UTC, in use.** The engine's own Alchemy key serves the readings' block reads from this session (held in a private
local file outside the repository, never printed, never committed), at `ALCHEMY_RPS=8` so a reading cannot crowd the engine's
receipt polls on the same key. Three failures in a row on the second endpoint (a rotated key, a spent quota) switch the rest
of the run to the public node: tested with a dead key, the piece's files come out identical.

**Security finding, Oct 3.** The same key was committed on Sep 11 in `src/analysis/router_blindspot.py`, and the repository is
public. Removed from the code today; it stays in the git history. An RPC key moves no funds, but anyone can spend its quota,
and then the engine's reads are refused mid-trade. The fix is the owner's: a new key in the Alchemy dashboard (and the old one
deleted), the box's settings updated with it, and the repository made private (GitHub, Settings, Danger Zone). On the box,
typed at the prompt, never pasted in the chat:

    sudo sh -c 'read -p "new alchemy key: " K; sed -i -E "s#(alchemy\.com/v2/)[A-Za-z0-9_-]+#\1$K#g" /etc/sniper/engine.env' && sudo systemctl restart sniper-engine && sleep 12 && sudo python3 deploy/englog.py 1 | grep -h '"ev": "start"\|feed_connected\|"ev": "error"' | tail -3 | cut -c1-160
**Oct 3 11:00 UTC:** the repository made private by the owner; pull and push from the session checked after. The key itself
was not rotated (the owner's choice): if the engine's reads start failing with an authorization or quota error, rotating it
with the command above is the fix.
**Oct 3 10:15 UTC:** made public again by the owner (the box pulls anonymously). Nothing secret is in the current tree (checked:
no wallet key, no shooter key, no bot token, no RPC key); the Alchemy key stays in the history of `router_blindspot.py`, so
the rotation above remains the fix if the engine's reads are ever refused.

**Box side (09:40 UTC).** No fill overnight, no burst sent, no alarm; 6.17 running since 23:38; P&L +$53.36, capital $110.19.
The 05:56 launch the chain scored +264% from the seat: the engine did not fire (its own count stayed under 3 fleets); the
replay with the live team-bundle setting calls it a guard revert at the seat behind one, so nothing was lost either way.

**Oct 2 daytime, the model against the engine (piece oct02day, 08:58-23:19, scanned on the Alchemy key).** 3,074 creations,
74 qualifying. Usual view: 13 fires, 9 fills, 4 guard reverts; the fills +4.3% mean, 3 of 9 positive, +$16 at $25/$50. The
engine fired 11 and filled 11: nine are the model's nine fills, launch for launch and sign for sign (12:03, 14:14, 14:55,
16:06, 16:45, 16:53, 17:58, 19:09, 19:55); the other two (14:47 -7.8%, 22:37 -3.9%) the model prices as guard reverts at the
seat behind one and the engine filled by landing first. The 49 launches refused for fewer than 3 fleets ran -9.1%, 4%
positive: the gate was right all day. So the day's launches were the market's (3 winners in 11 on the model too), and the
difference between the model's +$16 and the engine's -$22.51 is the exits: 16:06 sold one block late (+7.7% against +31% a
block earlier), 19:55 (-12.1% against -1.7%), 22:37 (-3.9% against +11.4%), fixed by 6.17. The model's own daily mean on
the fired set fell from +21-62% (Sep 24-30) to +5.5% (Oct 1) and +4.3% (Oct 2): two thin days, watched from here on as the
first line of every reading. The $50 window: 12 fills of 20, net about -$25; a window that closes negative steps the base
back to $25.

**The readings' scan, the honest timing.** At 8 requests a second the Alchemy route is no faster than the public node for a
14-hour window (16,000 requests); raised to 18 a second from the next reading (the engine's steady use of the key is under
2 a second, and since 6.17 the sell does not wait on the key): about 12 minutes for 14 hours.


## 5aw. Oct 4 14:20 reading (pieces oct03day, oct03eve, oct04am: Oct 3 09:28 - Oct 4 13:50 UTC)

The cloud machine restarted at 13:04 and killed the 27-hour scan; it was rerun as three pieces with `score_span.sh`, each
committed as it finished (the machine had also lost the engine's Python packages: reinstalled). Chain side, before the box:
3,216 creations, 74 qualifying. The model's own mean on its fills, the first line from now on: Oct 3 day +79.9% (2 fills),
Oct 3 evening -3.2% (2), Oct 4 morning -6.1% (1).

Usual view (k-1 with the registration block), all with a listed helper attacking, so $75 live:
- Oct 3 13:50 0xcbc4d69d +66.0%; 16:04 0x437717d4 +93.9%; 20:46 0xc03a0c3a -11.9%; 21:28 0x5565b2ce +5.4%; Oct 4 09:04
  0x0e0db022 -6.1%. Guard reverts: 20:18, Oct 4 04:58. Ceiling adds Oct 3 10:05 -9.6% (no listed helper), 16:32 -10.0%,
  16:35 -4.9%, guards 22:55 and 05:02. Floor: 16:04 and 20:46 only.
- Expected at $75 for the five usual fills: about +$110 before gas, nearly all of it 13:50 and 16:04.
- Refused for fewer than 3 fleets: 56 launches, -7% to -11% mean, 0-9% positive.

**Box side (14:05 UTC).** P&L +$63.11 (+$9.75 since the last reading), capital $120.21, no alarm, no open position. Engine
against the chain, the chain pricing each trade from its receipts:

| launch | model (behind one) | engine | position in the seat block | sold at | actual |
|---|---|---|---|---|---|
| Oct 3 13:50 0xcbc4d69d | +66.0% | $75 fill | behind 4 buys | +11 | +40.0%, +$30.07 |
| Oct 3 16:04 0x437717d4 | +93.9% | burst, no fill | 4 buys ahead, 0.47 ETH (one of 0.4) | | guard revert, gas |
| Oct 3 16:35 0x02c64fbd | -4.9% (ceiling) | $75 fill | behind 3 | +26 | -20.0%, -$15.09 (-10.6% at +11) |
| Oct 3 20:18 0x3f681cbb | guard revert | guard revert | | | gas |
| Oct 3 20:46 0xc03a0c3a | -11.9% | not fired (fewer fleets on its own count) | | | saved $9 |
| Oct 3 21:28 0x5565b2ce | +5.4% | $75 fill | behind 2 | +11 | +4.1%, +$3.06 |
| Oct 4 04:58 0x908186e3 | guard revert | 24 blocks late (slow door) | | | gas |
| Oct 4 09:04 0x0e0db022 | -6.1% | $75 fill | behind 3 | +12 | -10.2%, -$7.63 |

Three of four sells landed at +11/+12 (6.17's exit, with the sell sent 19-21 ms after the hold). 16:35's sell landed at +26
with the same 21 ms preparation: the sequencer, not the engine. `hold_blocks` read None on all four: the burst path (the live
one) never set `tokens_wei` or `buy_block`, only the single-shot path did, so the exit still read the balance first (fast on
Alchemy today, 20 ms). Fixed in 6.18, tested by executing the burst block on a receipt (`tests/test_exit_prep.py`, 10 checks).

**The finding: first place is gone.** Every live fill of Oct 1 (6 of 6) was the seat block's first buy. Every live fill since
(15 of 15, Oct 2-4) had 1-5 buys ahead. Three helper contracts, new on the chain, take the seat block's first transaction:
0x23e4ddf1 (first seen Sep 28), 0x6cd02597 (Oct 1) and 0x828f3766 (Oct 2); across all scanned launches they own the seat
block's first transaction on 12 to 18 a day since Oct 1, and on 12 of our 15 fills since Oct 2. The cost on this window:
13:50 sold +40% where the model's behind-one seat gives +66%; 16:04 (+94% from behind one) reverted on the guard behind four
buys. Next: measure the competitors' burst shape and the spread of our seal position, then decide on a denser burst
(6.14's two shots per shooter, built and off, with a shorter step).


## 5ax. Engine 6.19: the two-shot burst audited again, two faults fixed; the density trial (Oct 4 15:00 UTC)

**The double check asked for.** 6.18 verified: on every live trade the log read `hold_blocks: None`, which only the burst path
produces, and the single-shot path alone set the exact amount; the 6.18 block executed on a burst receipt in the test gives
the exact wei, the fill block and the float. Approved and deployed at 14:40. The 14:08 trade, the last on 6.17: +92.7%,
+$69.26, $75, behind three buys (other helpers; the bot 0x23e4ddf1 fired 55 shots on that launch and landed its first
seat-block shot one place behind ours), sold at +26 blocks with the sell sent 18 ms after the hold: the sequencer's door,
twice now in two days on hot launches (16:35 Oct 3 the same), and at +11 it would have been +81.8%, so no harm this time.

**The finding re-checked.** 16 live fills since Oct 2, 16 with buys ahead (1-5); 6 of 6 on Oct 1 first in the block. The
three new helpers hold the seat block's first transaction on 12 of the 16. Our burst shape is unchanged (the first shot 118-300
ms before the flip message, the straddle on every landing), so the field moved, not us.

**The audit of 6.14's two-shot mode, before switching it on: two faults, both fatal to it, both fixed.**
1. The sender's warm-socket pool held BURST_N sockets and the send step addresses socket i for shot i: shot 36 would have raised
   IndexError and aborted the burst mid-way. The pool now holds BURST_N x SHOTS_PER_SHOOTER.
2. The per-shot gas cap was trimmed to the shooter's whole balance, and the shooter's float was sized for one shot; the pool
   admits a sender's pending transactions on their summed cost, so the second wave's shot would have been refused. The cap now
   leaves the balance enough for every wave, and the float is sized per wave (the engine tops the shooters up itself).
   Tests: `tests/test_two_wave_sockets.py` (6 checks); the 6.14 tests mocked the sender and could not see either.

**The trial.** Two shots per shooter at a 1 ms step: 70 shots over the same 70 ms, twice the density around the boundary, so the
first shot after the seal is on average half a millisecond behind it instead of one. Cost about $0.33 a burst more in reverted
shots. Measured in the readings as our transaction index in the seat block and the buys ahead of us, against the 16 fills
above. Deploy and switch on:

    set_kv() { sudo grep -q "^$1=" /etc/sniper/engine.env && sudo sed -i "s|^$1=.*|$1=$2|" /etc/sniper/engine.env || echo "$1=$2" | sudo tee -a /etc/sniper/engine.env >/dev/null; }; cd ~/fomo-memebot && git pull -q && set_kv SHOTS_PER_SHOOTER 2; set_kv BURST_STEP_MS 1; sudo systemctl restart sniper-engine && sleep 12 && sudo python3 deploy/englog.py 1 | grep -h '"ev": "start"' | tail -1 | grep -o '"release": "[0-9.]*"\|"shots_per_shooter": [0-9]*\|"burst": \[[^]]*\]\|"dry_run": [a-z]*'

Check: `"release": "6.19"`, `"shots_per_shooter": 2`, `"burst": [35, 1.0, 46.0, 0.2]`. Back off: `set_kv SHOTS_PER_SHOOTER 1;
set_kv BURST_STEP_MS 2` and a restart.

**Deployed Oct 4 14:21 UTC (the engine's start time):** release 6.19, two shots per shooter at a 1 ms step (`burst [35, 1.0, 46.0, 0.2]`), base $50,
boost $75, live. The trial's first measure is the next fill's position in the seat block.


## 5ay. Oct 5 08:45 reading (pieces oct04pm, oct05am: Oct 4 13:50 - Oct 5 08:20 UTC): the density trial's first day

Chain side first (scored in two pieces while the session stayed on them): 1,893 creations, 38 qualifying. The model's mean
on its fills: Oct 4 afternoon +21.7% (7 fills, usual view), the night none (8 launches, all refused, -13% to -18%).
Usual view, the fires after the trial went live at 15:10 (two shots per shooter, 1 ms step), all $75 but 20:27 ($50):
- 17:08 0x4c9b092e -11.2%; 18:00 0x39aefb20 +21.3%; 18:26 0xab380d87 +36.2%; 18:39 0x13773127 +34.4% (8 fleets);
  20:27 0xd4d86aee -14.3% (no listed helper, $50). Before the trial: 14:08 (live +92.7%, priced last reading), 14:40
  0xfc8dc6f0 -7.0% (a 2.76 ETH bundle). Ceiling adds 15:37 0xbf840cc4 +62.6%, 16:49 +1.6%, 18:53 -9.8%. Floor: 14:40, 18:00,
  20:27.
- Expected at $75 on the five usual fires after 15:10: about +$45 before gas, from the seat behind one buy. The trial's
  question is the position: first in the block lifts all of these (the model's first-place column runs 8-15 points higher).
- Refused for fewer than 3 fleets: 18 launches, -10% to -13% mean.

**Box side (08:35 UTC).** P&L +$126.55 (-$5.91 since 14:08 yesterday), capital $184.31 (the wallet holds $85: the relay float
and the shooters' second-wave gas came out of it), no alarm, no open position, the shooters topped up four times. The trial
was live from 14:21, not 15:10. Its six bursts, placed on the chain:

| launch | model | shots | where they landed | buys ahead of our first seat shot | result |
|---|---|---|---|---|---|
| 14:40 0xfc8dc6f0 | -7.0% | 70 | seat +3 to +5 (the slow door) | none | -9.4%, -$7.09, sold +16 |
| 17:08 0x4c9b092e | -11.2% | 70 | straddled, first seat shot index 3 | 2 (bot B first) | -11.9%, -$8.91, sold +28 |
| 18:00 0x39aefb20 | +21.3% | 70 | straddled, first seat shot index 5 | 2, one of 0.40 ETH | guard revert, gas |
| 18:26 0xab380d87 | +36.2% | 70 | all after the boundary, first seat shot index 53 | 5, one of 0.54 ETH | guard revert, gas |
| 18:39 0x13773127 | +34.4% | 70 | straddled, first seat shot index 4 | 3 | +22.9%, +$17.13, sold +12 |
| 20:27 0xd4d86aee | -14.3% | 70 | straddled, first in the block (no bot there) | 0 | -14.3%, -$7.15, sold +12 |

The seat block's first transaction on the contested launches belongs to bots that spray 50 to 180 transactions across the
boundary (B 0x6cd02597, the listed helper 0x19078e5c, C 0x828f3766, 0x610de2b5): denser than our 70. With the trial our first
seat-block shot sits at index 3-5 where it sat at 2-45 before, still behind them; the two guard reverts (18:00, 18:26) were
the cost, about $43 at $75 from the seat behind one. Two of four sells landed at +16 and +28 with the sell sent 18-20 ms
after the hold: on the hot launches the bots' spray fills the sequencer's intake for seconds and our sell waits in it.

## 5az. The guard at 0.30: rejected; where the edge goes when we sit behind the sprayers (Oct 5)

**The replay said loosen.** `engine_replay.py` on Sep 20 - Oct 5 (guards 0.15 to 0.50, the three views) puts 0.30 above
0.20 by $22-50 over the 15 days, the extra fills (guard ratio 0.70-0.80) winning 14 of 16 on the usual view, in both halves.
Below a ratio of 0.65 the extras lose. But the replay prices every fill behind one buy, and since Oct 2 we are behind 2-3.

**Priced where we land.** `src/analysis/seat_positions.py` re-prices the 232 fired launches (any view) at the seat behind 1, 3
and 5 buys, last in the seat block, and landed 2-33 blocks late, behind the block (`seat_positions_report.py` for the grid).
Usual view (140 fires), the guard at 0.20 and what 0.30 adds:

| position | 0.20 | 0.30 adds |
|---|---|---|
| behind 1 | +$270 | 11 fills, 9 won, +$25 |
| behind 3 | +$58 | 16 fills, 6 won, median -3%, +$10 |
| behind 5 | -$53 | 28 fills, 11 won, +$17 |
| last in the seat block | -$70 | -$5 |
| 5 / 9 / 13 blocks late | -$134 / -$130 / -$75 | -$30 / -$36 / -$37 |

Weighted by the live mix since Oct 2 (about one burst in five first or second, half behind 2-3, one in seven late) 0.30 is
worth about +$2 a week against the late-landing tail: **the guard stays at 0.20.** The two trial reverts (18:00, 18:26) are
the price of that tail.

**The position finding.** Behind 3 the edge is a fifth of what it is behind 1, and behind 5 it is gone. Behind 3, by the
fleets on the usual view: 3 fleets -$13 (58 fills), 4 fleets +$5 (21), 5 or more +$65 (17); launches with no listed helper
-$14 (21). This prices us behind the block's first buys whoever they are; on a thin launch the sprayers may be absent and we
sit first. Next: where the sprayers actually sit by fleet count since Oct 2. If they are on the 3-fleet launches too,
`ATTACK_MIN=4` is the candidate change.

**6.20 (the hold clock counted from the buy block) shelved:** correct, worth $0-5 a week, not a release on its own.

## 5ba. Oct 6 17:10 reading (pieces oct05day, oct05night, oct06day: Oct 5 08:20 - Oct 6 17:05 UTC)

Chain side first (three pieces scored in parallel, the session on them): 3,657 creations, 78 qualifying (35 / 21 / 22), a quiet
span: 64-70 refused for fewer than 3 fleets on every view. All fires carry a listed helper ($75 live). The model prices the
seat behind one buy; behind 2-3 (where we sit since Oct 2, 5az) take about 8-10 points off each fill.
- Usual view (k-1 with the registration block), 8 fires: 15:23 0x4835464b -3.0%; 16:10 0x9e8d4fbf guard (+66.9% behind one);
  16:55 0xdc093b2b +1.4%; 17:49 0x7258454c +23.3%; 20:46 0x1a4d9acb guard (+29.8%); 23:13 0xdd898120 guard (-4.1%);
  Oct 6 12:23 0x9d48eeff -3.5%; 15:39 0x42dfb38f +37.4%. Five fills, mean +11.1%, median +1.4%: about +$42 at $75 before gas.
- Ceiling (k) adds 09:58 -13.8%, 17:58 -9.9%, 19:42 -10.5%, 20:21 -5.1%, Oct 6 15:05 +14.1% and three guards (14:09, 17:01,
  20:15): 10 fills, mean +3.0%. Floor (k-2): 17:49 +23.3% and the 23:13 guard.
- The night (19:20-06:20): 21 launches, nothing the usual view fills. Refused for fewer than 3 fleets: mean -4% to -10%.
- Extension (piece oct06eve, Oct 6 17:05 - 17:26, scored before the box paste for the owner's new trade): 3 launches, no fire on
  the usual view or the floor; the ceiling fires 17:24 0xda48f334 (4 fleets on k) and the guard refuses it (-10.8% behind one).

**Box side (Oct 6 17:30 UTC), recorded only; pricing on the chain and the analysis at the next reading (Oct 7 morning).**
Engine active since Oct 4 14:21 (6.19), notifier since Oct 1 06:02; flow line 17:30: 5,115 creations seen, probe median 4.0 ms,
bankroll $156.06; last 3 h: 502 creations, 1 trade_decision, 12 eligible_not_traded, 13 sent_burst, 1 burst_landing, 1
trade_done, 2 feed_connected; 0 "not fresh" refusals; no open position. Capital 0.060703 ETH ($163.72) = wallet 0.024506 +
relay 0.033386 + shooters' gas 0.002812. P&L since 0.021190 ETH: +0.039513 ETH ($106.57, +186.5%), all gas and fees included.
The engine's bursts since the last reading:

| launch | filled | stake | land_off | load_txpb | exit | hold_blocks | held_s |
|---|---|---|---|---|---|---|---|
| Oct 5 15:23 0x4835464b | 0 (buy_reverted) | | -1 | 4.9 | | | |
| Oct 5 16:10 0x9e8d4fbf | 0 (buy_reverted) | | -1 | 11.9 | | | |
| Oct 5 16:55 0xdc093b2b | 1 | $75 | -1 | 9.6 | hold | 28 | 3.44 |
| Oct 5 17:49 0x7258454c | 0 (buy_reverted) | | +1 | 8.9 | | | |
| Oct 5 17:58 0x0bb5ee0f | 1 | $75 | 0 | 6.8 | hold | 17 | 1.59 |
| Oct 5 20:21 0x91bbe43f | 1 | $75 | +4 | 12.4 | hold | 27 | 3.40 |
| Oct 6 12:23 0x9d48eeff | 1 | $75 | -1 | 5.3 | hold | 25 | 3.19 |
| Oct 6 17:24 0xda48f334 | 1 | $50 | 0 | 8.3 | hold | 14 | 1.43 |

## 5bb. Oct 7 04:30 reading (pieces oct06pm, oct07am: Oct 6 17:26 - Oct 7 04:09 UTC), recorded only (the owner: no analysis)

Chain side first: 1,053 creations, 26 qualifying (25 / 1). The model prices the seat behind one buy.
- Usual view (k-1 with the registration block), 4 fires: 17:45 0x49630455 -11.9% ($75, listed helper); 19:21 0x4416a5ae
  guard; 21:04 0x0af2d4e6 guard; 22:23 0xd7657dce -10.1% (no listed helper, $50). Two fills, mean -11.0%.
- Ceiling (k) adds 18:24 0xe565a53a -10.6%, 21:19 0x14331814 -10.7% and two guards (19:04 0x9b414128, 19:07 0x62084e9d): 4
  fills, mean -10.8%. Floor (k-2): 17:45 -11.9% and 22:23 -10.1%.
- The night after 23:00: one qualifying launch, no fire.

**Box side (Oct 7 04:23 UTC).** Engine active since Oct 4 14:21 (6.19); flow 04:07: 5,997 creations seen, probe median 4.1 ms,
bankroll $141.44; last 3 h: 76 creations, 1 trade_decision, 1 sent_burst, 1 burst_landing, 5 feed_stall, 13 feed_connected; 0
"not fresh" refusals; no open position. Capital 0.056708 ETH ($147.89) = wallet 0.019672 + relay 0.034450 + shooters' gas
0.002585. P&L since 0.021190 ETH: +0.035518 ETH ($92.63, +167.6%), all gas and fees included (-$13.94 since 17:30 the day
before). Bursts since: Oct 6 17:45 0x49630455 no fill, land_off +23, load 18.4 (the slow door); 19:21 0x4416a5ae no fill,
land_off 0, load 8.7 (the guard); 21:19 0x14331814 fill $50, land_off +1, sold +13, held 1.24 s; 22:23 0xd7657dce fill $50,
land_off 0, sold +14, held 1.34 s; Oct 7 04:14 0x47313c63 no fill, land_off -1, load 3.4 (every shot in the creation second;
the chain scan saw no qualifying launch there: scored at the next reading).

The live fills priced on the chain (`live_vs_table.py`, saved as `data/derived/live_vs_table/live_vs_table_oct07.txt`), Oct 5-6:

| fill | landed | buys ahead | model first | landed | actual |
|---|---|---|---|---|---|
| Oct 5 16:55 0xdc093b2b $75 | E1+1, index 1 | 0 (6 in the seat block before it) | +24.0% | +0.2% | +0.2%, +$0.15 (sold +28) |
| Oct 5 17:58 0x0bb5ee0f $75 | E1, index 43 | 3 | +9.4% | +4.0% | +4.7%, +$3.54 |
| Oct 5 20:21 0x91bbe43f $75 | E1+4, index 24 | 0 | +11.4% | -12.7% | -12.7%, -$9.51 |
| Oct 6 12:23 0x9d48eeff $75 | E1, index 4 | 2 | -3.5% | -7.2% | -7.3%, -$5.47 |
| Oct 6 17:24 0xda48f334 $50 | E1, index 49 | 4 | -8.0% | -11.6% | -11.6%, -$5.82 |
| Oct 6 21:19 0x14331814 $50 | E1+1, index 3 | 0 | -5.8% | -9.8% | -9.8%, -$4.89 |
| Oct 6 22:23 0xd7657dce $50 | E1, index 2 | 1 | -8.6% | -11.3% | -10.1%, -$5.04 |

All 43 single fills since Sep 30: actual mean +3.6%, model first +10.4%, landed +3.2%; net +$94.20. By day: Sep 30 +$0.43,
Oct 1 +$69.67, Oct 2 -$22.74, Oct 3 +$18.08, Oct 4 +$55.79, Oct 5 -$5.82, Oct 6 -$21.22.

## 5bc. The Oct 7 review: why the engine fires less and loses since Oct 5; engine 6.21 (the sprayers as one fleet, the hold from the fill block, the first sell with nothing in front of it); one wave again

The owner asked for a deep review of every live trade against the readings and of 6.19/6.20 (6.20 was never deployed: it was
built, tested and shelved in 5az; the box ran 6.19). Five analysts worked independently from the chain, the crowd tables since
Sep 20 (1,618 qualifying launches), the engine log summary (`data/derived/live_vs_table/box_decisions_oct07.txt`: 63 decisions)
and the 43 live fills priced on the chain (`live_vs_table_oct07.txt`); a judge and two skeptics then attacked the findings.
Reports in the session's scratchpad (review/*/report.md); the numbers below are theirs, each re-checked by at least one other.

**Why fewer trades (Q1): the market, not the engine.** Qualifying launches a day: 171 (Sep 28-29), 111 (Oct 1-2), 55 (Oct 3-6).
The share that reaches 3 fleets did not fall (12.8-13.7% of eligible launches on Oct 1-6 against 17% in September), so the fire
count halved with the launches. The attacking field is a third of what it was (129 distinct attackers a day on Sep 21-23, 31-42
on Oct 3-6; the Sep 27-30 whale 0x2124f1fa left after Oct 1). Engine-side refusals in 7 days: 1 relay float, 2 nonce, 1 position
open; feed coverage improved from 71-78% of the chain's eligible launches (Sep 30 - Oct 2) to 82-85% (Oct 4-6). The Oct 3 flood
of 110 "token tax 0 bps" refusals was many small teams choosing the 1% tier for a day; never fireable, never a factor.

**Why losing (Q2): the gate let the sprayers vote.** Since Oct 2 the seven sprayer contracts (0x23e4ddf1, 0x6cd02597, 0xa29d8198,
0x460b1f81, 0x19078e5c, 0x828f3766, 0x610de2b5; 50-180 transactions each across the boundary, at 42% of eligible launches on
Oct 3-6 against 19% before) are counted as fleets like any relay. 63% of the fires since Oct 1 passed the 3-fleet gate only
because sprayers were counted (25% before). On the launches with ONE real sniper and two sprayers: 15 fires over the period, 11
fills, 1 win, mean -5.1% (0 wins of 7 fills Oct 2-6, -$62 behind three buys); with two or more real fleets the launches still earn
(+15-24% behind one, every period). The sprayers do not dump on us: on 26 of 30 post-Oct 2 sprayer launches no sprayer sold
inside the 11-block hold (the big ones, 0x460b1f81 at 0.45 ETH and 0x23e4ddf1, sell at +12..+18; the small ones never within
100 blocks). What separates winners from losers is the follow-through: net ETH into the curve in blocks +1..+11 (corr 0.92 with
the return post-Oct 2); the one-real-sniper launches have none, and a launch with no follow-through returns -(tier + 6.18% +
round trip) = -7..-12%, the mode of the losers. Decomposition of the 27 fills since Oct 2
(+$24 actual): launches worth +$230 first in the seat block; the seat behind the sprayers about -$175; late landings $5-8 (the
skeptics: re-priced at the seat block the four late fills would have made +$5 to +$8 more; the judge's -$38 charged the buys
ahead to the trial); late sells -$39 (Oct 2's public node, fixed by 6.17; ~$0 since); gas -$4.5 (receipts: $0.02-0.15 a burst, the capital line $0.17: the box's
gas estimate assumes every shot lands). The live fills by the model's first-place return since Oct 2: first > +5%: 12 fills,
+$138, 9 wins; first < -5%: 14 fills, -$109, 0 wins. Hold 11 remains the best hold at our real position (h9 +$36, h11 +$49,
h13 +$32 on the 27).

**6.19 (Q4): nothing improved, three faults.** 70 shots at 1 ms (Oct 4 14:21+): our first seat-block shot sat at index 5 (median)
against 4.5 before; only 52% of a two-wave burst's shots reached the straddle blocks (84% of the 35-shot bursts; 10 of 18 bursts
under half); late landings +1..+4 rose from 1 of 38 bursts to 4 of 19 (p 0.04); the fill rate fell from 80% to 58%; two late fills
cost $36. The code faults (none in the 6.19 lines themselves): (F1) a gated first-wave shot leaves its second-wave partner at
nonce+1 behind a nonce the chain never sees, so a gate opening at shot g kills 2g shots and leaves a hole across the tick (Oct 5
20:21: 32 gated, 6 of 38 sent shots alive, landed +4, -$9.51; 16:10: 24 gated, guard revert on a +67% launch); (F2) with LEAD 46
and a 1 ms step the fill IS a second-wave shot, polled by 6.14's late pollers, so the position was built 2-3 blocks later (the
approve landed at +4..+10 against +2/+3 before) and the 9-block hold ran from there (sells at +12..+17 against +11/+12);
(F4) under a sprayer's flood the chained second shot is refused or dropped at the sequencer (36 of 39 pairs on the two flood
bursts). Back to one wave: `SHOTS_PER_SHOOTER 1`, `BURST_STEP_MS 2` (the documented back-off, the 6.18 burst byte for byte).

**The exit (F3).** `exit_prep_s` is measured before `next_nonce()` (two nodes, the public one unbounded) and before
`ensure_approved`'s receipt wait when the watcher has not confirmed: the chain shows the blocks between the approve and the
late sells thin (2-18 transactions), so the 1.2-1.5 s went in the engine, not the sequencer. The +25..+28 sells' `held_s` of
3.2-3.4 s is NOT the wall-clock cap (skeptic B: the cap is 3.9 s and held_s is stamped after the sell's receipt, so a cap hit reads
4.2 s or more): those holds ended on the block count, 11 blocks later than the healthy ones, i.e. the feed was behind the chain at the
hold's end, or the nonce query sat in front of the send. `trade_done` now logs `feed_seq_at_send` (the sell's block minus it is the
feed's lag) and `send_timing` the query: the next reading separates the two.

**Engine 6.21** (tests: `test_attack_group.py` 13, `test_hold_clock.py` 11, `test_sell_nonce.py` 9; the older suites pass):
1. `ATTACK_GROUP`: relay targets that together count as ONE fleet in `attack_fleets()`. Unset, the engine loads
   `data/derived/sprayers.json` (ATTACK_GROUP_PATH): the seven contracts the review tested. `src/analysis/sprayer_list.py` refits
   the candidates each reading into `sprayers_refit.json` (a contract with >= 50 transactions on one launch's blocks on >= 5
   launches in 7 days; our relay excluded: 12 on Oct 7, the seven plus 0x32651dff and 0x7316855a (gone since Oct 1-3),
   0xe665841e (all week, its launches -4.7% behind one), 0xd0fa5138 and 0x982403 (Oct 6)); a candidate enters `sprayers.json`
   only after review, since a listed good sniper would be demoted and the backtest is on the seven. With ATTACK_MIN 3 the gate
   needs two real snipers when a sprayer is attacking. The replay follows the engine (`REPLAY_ATTACK_GROUP`,
   `REPLAY_ATTACK_GROUP_PATH`; score_window/score_span pass the file and `REPLAY_BUILD_MIN=1`).
2. `ATTACK_BUILD_MIN=1` (6.3's setting, now used): no burst when nobody was attacking at the build (the k-2 view): the gate that
   opens only at the seat block fired 6 live bursts since Oct 2, -8.1% behind one, 0 of 6 positive; 8 launches in the replay,
   -$23.7 behind three, 0 wins of 3 fills.
3. `HOLD_FROM_FILL=1` (off by default): the hold counted from the fill's own block (`feed_seq < buy_block + HOLD_BLOCKS + 1`),
   so the receipt pollers' timing no longer moves the clock; the `+1` keeps the old clock's count (it started at the block after
   the fill).
4. `SELL_RESERVED_NONCE=1` (off by default): the first sell at the reserved nonce (`pos.nonce + 2`, the approve's + 1) with no
   node asked and no approve-receipt wait; the sequencer orders the approve before it; a reverted first sell takes the old path
   (allowance read, re-approve, nonce read). Always on: `send_timing` logs the nonce query's time and the time to submit on
   every send, so the next reading measures what these two switches would remove (the judge, below: not supported by the live
   data yet; the 6.19 clock shift is real in blocks, +3.3 (se 0.7), and worth $0 by the actual fills to $13 by the model).

**The backtest (engine_replay, Sep 20 - Oct 7 04:09, $13 behind one; and the fires re-priced at the live stake behind three
buys, gas $0.6 a burst).** Usual view: the current gate 169 fires, 140 fills, mean +19.6%, median +8.4%, win 64%, +$301; the
new gate (sprayers as one fleet, build minimum 1) 133 fires, 115 fills, +23.9%, +11.6%, 71%, +$313. Per day since Oct 2: Oct 2
-$0.16 -> +$6.79, Oct 3 +$17.96 -> +$18.62, Oct 4 +$16.02 -> +$17.73, Oct 5 +$0.83 -> +$1.89, Oct 6 -$0.43 -> -$0.10 (the
pre-Oct 2 days unchanged or better). Ceiling view: 294 -> 184 fires, +$363 -> +$342 (Oct 2-6: -$2.73/+13.46/+21.78/-6.58/-3.35
-> +9.15/+17.04/+25.21/-0.23/-0.31). The gate researcher's table (the seven contracts, behind three, live stake): post-Oct 2
the current gate 41 fires +$46 ($1.12 a fire, se 2.20), the new gate 25 fires +$114 ($4.55, se 3.37); pre-Oct 2 +$530 -> +$569
on 128 -> 108 fires; bootstrap P(post total <= 0) 0.32 -> 0.08. On the live Oct 2-6 fills it keeps 14 (+$113, 8 up) and drops 13
(-$89, 1 up); Oct 2-6 would have been +$113 instead of +$24. The refit 12-contract list gives the same week (+$313, +$344) and
differs on Oct 6 only (3 fewer fires, one the +37% winner of 15:39, net -$1).

**Rejected by the review:** ATTACK_MIN 4 (gives up $440 of the pre-Oct 2 first-place edge, drops the Oct 3-4 winners, post +$60);
ATTACK_MIN 5 (1.7 fires a day); the guard at 0.30 (5az); a shorter or longer hold (h9 does not help with sprayers present, h13
hurts); skipping on `load_txpb` (the slow door is not in the load: costs $14); skipping any burst with gated shots (the gate that
opens DURING the burst marks the best launches: +$98 over the period); firing only without sprayers (they are at 39 of 41
fires); removing the sprayer contracts from the smart list (the boost still pays, +$15 on the Oct 2-6 fills; the fix belongs in
the fleet count). ATTACK_BUILD_MIN 2 saves more since Oct 2 (+$53) but cost $104 on Sep 30 - Oct 1: not taken.

Deploy (no fill open):

    cd ~/fomo-memebot && git pull -q && set_kv() { sudo grep -q "^$1=" /etc/sniper/engine.env && sudo sed -i "s|^$1=.*|$1=$2|" /etc/sniper/engine.env || echo "$1=$2" | sudo tee -a /etc/sniper/engine.env >/dev/null; }; set_kv ATTACK_BUILD_MIN 0; set_kv SHOTS_PER_SHOOTER 1; set_kv BURST_STEP_MS 2; sudo systemctl restart sniper-engine && sleep 12 && sudo python3 deploy/englog.py 1 | grep -h '"ev": "start"' | tail -1 | grep -o '"release": "[0-9.]*"\|"attack_group": [0-9]*\|"attack_build_min": [0-9]*\|"shots_per_shooter": [0-9]*\|"burst": \[[^]]*\]\|"dry_run": [a-z]*'

Expected: `"release": "6.21"`, `"attack_group": 7`, `"attack_build_min": 0`, `"hold_from_fill": false`, `"sell_reserved_nonce": false`,
`"shots_per_shooter": 1`, `"burst": [35, 2.0, 46.0, 0.2]`, `"dry_run": false`. What to watch at the readings: fires about 5-6 a day (5.8 in the replay) instead of 6-8;
`fleets_at_build` on every decision (the build floor is priced on the grouped count at the next readings, not deployed); `land_off` back to -1/0; `hold_blocks` 11-12; `send_timing` query_ms ~0 on the first sell; the `sprayers.json`
refit each reading (`python3 src/analysis/sprayer_list.py` -> `sprayers_refit.json`, diffed against `sprayers.json`; a new contract enters the engine's list only after review).

**The judge's verdict (every analyst's number re-derived from the data; the two skeptics' pass is recorded below when done).**
Diagnosis, in dollars, on the 27 fills since Oct 2 (+$24 actual): the diluted fired set -$89 on 13 fills (1 win; the other 14
fills +$113, 8 wins; 11 of the 13 lose even first in the block; one-real-fleet fires 0 wins of 10 fills behind three over 17
days, P 0.012 at the current win rate); the seat behind the sprayers -$143 of the launches' first-place value (structural, no
setting moves it); late landings under 6.19 -$38 (the post-trial loss); late sells -$39 (Oct 2's node -$33, fixed; -$6 since);
gas -$4.5. Not causes: sprayer dumping, the crowd signal at >= 2 real fleets, the boost, the hold length. Fewer trades: the
market, ~100% (half the launches; the real-sniper supply 8.0 -> 2.8 fires a day with >= 3 real fleets; the engine's own refusals
4 in 7 days). Recommendations: (1) ATTACK_GROUP (the tested seven) + ATTACK_BUILD_MIN 1, ATTACK_MIN 3 unchanged: post-Oct 2
25 fires (4.8 a day), behind three +$114 ($4.55 a fire, se 3.37, win 53%) against +$46 ($1.12, se 2.20, win 36%); pre-Oct 2
+$569 against +$530; the dropped set 0 wins of 8 fills; bootstrap P(post total <= 0) 0.08 against 0.33; live Oct 2-6 +$85 to
+$113 instead of +$24 (the build floor's price in the old regime: Oct 1 20:52, +$48.78, a build-0 fire). (2) One wave again
(SHOTS_PER_SHOOTER 1, BURST_STEP_MS 2): late landings 4 of 19 against 1 of 40 (p 0.033), 60 of 150 sent shots dead on the three
gated two-wave bursts, no position bought. (3) Do NOT deploy the hold clock and the reserved nonce as P&L changes (insufficient
evidence; the mechanism is 6.19's, which (2) removes); keep the `send_timing` log: done as the two switches above, off. (4)
ATTACK_MIN 4 only as a fallback (gives up $440 of pre-Oct 2 first-place edge). (5) Leave the hold, the guard, the exit path, the
smart list; no launch-feature filter (every one that helps post-Oct 2 flips sign before). Caveats the judge keeps: n = 25 post
fires, se of the order of the mean; the kept set's mean is not itself significant, the case rests on the dropped set; the k-2
floor view is negative for every rule post-Oct 2 (n <= 14); Oct 6-type days (no follow-through on 13 of 41 fires) stay negative
under every rule. Watch: 4-5 fires a day, win rate above 50%, no fill with a build-0 gate, the approve back at +2/+3 and healthy
sells at +11/+12, `send_timing` query_ms on the first sell, the refit candidates (0xe665841e, 0x982403) reviewed before listing.

**The skeptics and the final arbiter (Oct 7 09:50 UTC).** Skeptic A (statistics) refuted the build floor and the +$114
headline, not the group: given the group, `ATTACK_BUILD_MIN=1` drops 5 launches post-Oct 2 (1 fill, -$5) and at the ceiling view
costs $186 behind three / $372 behind one of the pre-Oct 2 edge (n = 67); live Oct 1-6 it drops 9 fills worth +$7.68 net (Oct 1
20:52, +$48.78, was a build-0 fire the box saw at 0 because the feed was behind). The kept set's total is top-heavy (G post +$108
behind three, +$10 without its two best launches; the current gate +$46, -$52 without the same two) so the expectation is "the
one-real-fleet leak closed", not a profit figure; the dropped set is uniform (8 fills, all -3% to -13%, 0 wins, in both periods and
at every position). The P = 0.012 used the wrong null (against the one-real-fleet base rate it is 0.14-0.29) but the paired
difference G - A behind three is +$62 [+29, +97] because every dropped fill lost. The list is robust to its own refit
(walk-forward on trailing 7 days: post +$124 vs +$114; fitted on Sep 20 - Oct 1 only: +$124). The density trial's -$36 was
misattributed (above); the revert stands on mechanism and costs nothing. ATTACK_MIN 4 refuted (one launch: +$0 without 0x17d132a9).
Skeptic B (mechanism) did not refute the group: the sprayers are visible by k-1 on 39 of 41 post fires, the grouped count opens the
gate at the same block as the raw count, `attack_fleets()` is pure and the boost, guard and hold are untouched. Corrections: the
list decays within days (by Oct 6 four of the seven were still active while five unlisted contracts sprayed; 2 of Oct 6's 5 grouped
fires passed only through unlisted ones, both losers), so the refit must be reviewed at every reading; the engine's view is k-1..k,
so expect the engine bound (live Oct 2-6 +$74 instead of +$24) rather than the k-1 table's +$113; only Oct 5 20:21 of the four
late fills was the two-wave code's doing; `exit_prep_s` is blind to `next_nonce` only, so the approve wait is excluded on the +26
sells and the candidates are the nonce query and the feed's lag (hence `feed_seq_at_send`). The arbiter's verdict: deploy the
group (the tested seven, loaded from `sprayers.json`), ATTACK_MIN 3, NO build floor; one wave; the two exit switches off; leave the
hold, the guard, the exit path and the smart list; expect 5-6 fires a day and days like Oct 6 to stay negative under any rule;
re-price the build floor on the grouped count once build-0 fires reach n >= 15; review the refit candidates (0xe665841e, 0x98240307,
0xd0fa5138) at the next reading; watch 0x19078e5c (half of the group's effect, last seen Oct 5).

Deployed Oct 7 about 10:05 UTC: the start line read `release 6.21, shots_per_shooter 1, burst [35, 2.0, 46.0, 0.2], attack_build_min 0,
attack_group 7, hold_from_fill false, sell_reserved_nonce false, dry_run false`. (The first attempt failed on the box's pull: an analysis
output `live_vs_table.json` had been committed by mistake and collided with an untracked copy there; removed from the repo, the pull
then went through. During that attempt the engine was restarted once on 6.19 with its old settings; no fill was open.)

## 5bd. The growth review (Oct 7, afternoon): the exit, first place, selection; the burst's partner-shot fix (6.22, send step)

The owner asked for growth, not patches. Three researchers (Opus 5.5), each reviewed here.

**1. The exit: hold 11 stays.** Premise: on the live gate's fills the price touched +50% within a minute on most launches, so a
trailing exit could multiply the per-fill return. Tested on the full price paths of all 133 fired launches (115 fills; a simulator
that reproduces hold_grid's pricing exactly, sells executed two blocks after the decision), 194 rules at $75 and $250, behind 1 and
3 buys, ranked on the pre-Oct 2 fills and held out on Oct 2-7: **no take-profit, trailing stop, early stop or scale-out beats the
fixed 11-block hold** (the best loses 0.5 points, trailing stops lose 6-13). The premise was wrong: the mean mark peaks at block
11 in both periods and every winning group gives back after it, the biggest the most. The one addition with a positive sign is
the reverse: sell the winners at 11, let the LOSERS ride to 300 blocks with a -25% floor (rule G): +3 points pre (se 2.3), +6-8
on the holdout (se 7), +$105 on the live Oct 2-6 fills of which all is Oct 6. Not significant; scored at the readings from now on
(growth/exit/live_check.py prices it at our real landing); on only if the running lift stays positive over ~30 riders.

**2. First place: the mechanism is known, the prize measured, the engine cannot do it yet.** On 25 launches Oct 2-6 where a sprayer's
buy is the seat block's first transaction, dissected from receipts: each sprayer runs N wallets x M consecutive-nonce copies of one
buy (the leader 0x460b1f81: 20 x 15 = 300 copies; 0x6cd02597 10 x 16; 0x19078e5c one wallet x 86), streamed continuously from
about two blocks before the second boundary through the seat block; every copy carries deadline = T0+1, 99-100% revert cheaply
(22-50k gas) in the creation second, the first copy past the boundary succeeds and sits at the top of the block. Ordering is pure
arrival order: effectiveGasPrice == base fee on 21,587 of 21,587 transactions (no priority tip exists), a 137x-base sprayer does not
beat a 4x one, reverting copies occupy slots like successes. Why they beat our timed burst: they start 2-6x earlier (our 46 ms lead
is ~31 ms before the real boundary, which lands 15 ms before our predicted tick), their nonce chains never gap (every copy
included), and they spread 70-300 copies over 200-300 ms (admitted in full) where we force 35-70 into 69 ms on parallel sockets
(dropped ~48% under floods). Prize, measured on the same launches: first place is worth **+$7.43 a fill (se 1.61), +0.094 return
points (median +0.052), +$134 over Oct 2-6**, but 85% of it on the 10 of 18 launches that were already positive; 2 of 18 flip
from loss to win. Cost to replicate with our 35 wallets: $0.2-0.6 a launch in gas (ours is $0.15 today). The current burst cannot
replicate it: it fires one timed cluster, and a gated first-wave shot strands its chained partner (F1).

**6.22 (deploy/send_step.py; `tests/test_partner_shot.py`, 14 checks): in a multi-wave burst a shot sends its key's lowest UNSENT
body, so a shooter whose earlier shot the gate skipped sends that body (its current nonce) instead of a nonce + 1 body the
sequencer refuses; the chain never gaps; `sent_burst` logs `partner_substituted`.** With SHOTS_PER_SHOOTER 1 (live) it changes
nothing; it is the prerequisite for any multi-copy pattern. Next: a one-day config trial after a day of 6.21 baseline, the stream
bent toward the sprayers' pattern with the existing settings (BURST_LEAD_MS ~150-200, SHOTS_PER_SHOOTER 3, BURST_STEP_MS 2: ~105
copies over ~210 ms from about block k-2), measured on our first included seat-block index and the included-shot share on contested
launches, with a stop rule (median first index not below 3 after 10 contested launches, inclusion under 60%, gas over $1 a burst,
or the day's chain-priced P&L at -$15: back to 35 x 1 at 2 ms). If the index moves, build the continuous-stream sender (independent
per-wallet nonce chains topped up from k-2) and spend the copies only on launches worth winning.

**3. Selection:** running (a reputation-weighted crowd score, walk-forward); recorded when done.
