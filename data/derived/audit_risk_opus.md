# Risk audit of the Pons V2 first-block sniper — how to lose less

Independent scratch re-implementation under `audit_risk_opus/` (build.py, ev.py, run*.py, final2.py).
No repository file was modified. Everything below comes from the exact constant-product replay
(`src/analysis/sniper_exact.py`) re-run out of the data root on all 14 windows.

**Baseline = today's plan**: bundle >=3 named wallets buying >=0.3 ETH in the creation second, creator's launch buy
>=1% of supply, no outsider in second one; E2 seat 0.3 s behind the first buyer of second two; 3% of supply capped by
the stake; hold 7 s; sell lands 0.3 s late; later buyers revert beyond 10% shortfall; minOut refusal at +25%;
20% sizing, stakes $50-$300, one position at a time, daily stop -50%, safety switch 15/-10%; gas $1/round trip, ETH $2,445.

**Harness check.** My cache reproduces `data/derived/sniper_plan.txt` launch-for-launch: same rule counts per window
(175/276/197/184/68/211/339/87/51/136/192), same always-on and one-at-a-time dollars (sum $50,857 / $47,789).
Mean ROI differs by <=0.6 pp per window only because I count minOut-refused launches as 0% instead of dropping them,
and my resampled stop probabilities run 1-3 pp above the repo's because I price fills on a finer stake grid
(25/35/50/75/100/150/200/250/300). Both differences are conservative.

**Splits.** In-sample (IS) = the seven earliest windows, Aug 12 - Sep 2; only four of them carry >=10 rule-passing
launches (Aug 12 has 0, Aug 20 has 1, Aug 27 has 9), so IS is really 08-30, 08-31, 09-01, 09-02 — 832 trades.
Out-of-sample (OOS) = Sep 3 0-6 through Sep 6, seven scored windows, 1,084 trades. **Every parameter below was chosen
on the IS half only**; the OOS column is a held-out read.

---

## 1. Where the loss actually comes from

Per-trade ROI on cost, $300 stake rows (run6.py section 1):

| set | n | mean | median | p1 | p5 | p25 | p75 | p95 | share <-40% | share <0 |
|---|---|---|---|---|---|---|---|---|---|---|
| IS baseline | 842 | +5.3% | +11.9% | -74% | -68% | -12% | +32% | +67% | 22.6% | 36.2% |
| OOS baseline | 1084 | +11.9% | +8.6% | -75% | -71% | -6% | +46% | +83% | 17.9% | 42.3% |

- **It is a fat left tail, not many small losses.** The median trade is a winner in both halves; 18-23% of trades lose
  more than 40% and they are near-total: p5 is -68% to -71%, and there is no mass between -20% and -40%
  (share <-20% is 24.1% IS / 19.6% OOS, barely above the share <-40%). A trade either survives the hold or the team
  dumps 46% of supply into it and it comes back at -70%.
- **The window P&L is a difference of two big numbers.** Per window (run6.py section 2, flat $300):
  09-01 nets +$971 out of -$7,734 from the 48 blow-ups and +$4,301 from the 27 big winners; 08-31 nets +$3,165 out of
  -$10,969 / +$8,085. The weak windows are not windows with a lower win rate, they are windows where the blow-up rate
  is 21-24% instead of 3-16%. Blow-up rate by window tracks mean ROI almost one-for-one.
- **The blow-ups do not cluster in time** (run7.py): the longest observed run of <-40% trades per window averages 2.64
  vs 2.71 in 1,000 shuffles of the same window; adjacent loss pairs 93 observed vs 78 shuffled. So the drawdown is
  order-luck on an i.i.d.-looking fat tail — which is exactly why the resampled stop probability is the right metric,
  and why consecutive-loss caps cannot work (confirmed below).
- **Hour of day is not a usable axis.** IS worst hour is 15h (+0%), OOS best hour is 16h (+22%); the IS ranking does
  not survive into OOS (run6.py section 3). No hour gate proposed.
- **One pre-entry feature separates the tail in both halves**: whether another *surcharge-paying* buyer has already
  landed before our send. IS: 731 clean launches +7.7% (21% blow-ups) vs 111 contested -10.8% (34% blow-ups).
  OOS: 735 clean +16.8% (14%) vs 349 contested +1.7% (27%). Every other feature either fails to replicate
  (px_ratio, lpm, bundle_max_eth, team1_eth) or costs 60-80% of the trades (creator buy >=8% of supply).

---

## 2. Ranked ideas — drawdown reduction per unit of expected return given up

`stop%` = resampled probability of hitting the -50% daily stop from $300 (1,000 shuffles of trade order per window,
20% sizing, floor $50), averaged over the scored windows with the worst window in brackets. `dd` = mean resampled max
drawdown. `1at$` = flat-$300 one-position-at-a-time net. All IS numbers are in-sample by construction.

| # | idea | IS mean | IS stop% | IS dd | IS 1at$ | OOS mean | OOS stop% | OOS dd | OOS 1at$ | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| — | **baseline** | +5.3% | 20.2 [35] | 55% | 11,481 | +11.9% | 3.2 [12] | 36% | 36,308 | — |
| 1 | **seat-clear gate** (G4 below), hold 7 | +7.8% | 11.1 [27] | 48% | 15,186 | +16.8% | 0.3 [2] | 24% | 35,263 | free: return *up* in both halves, stop risk down 2-10x |
| 2 | **hold 7 -> 4 s** (timer only) | +9.8% | 0.4 [1] | 30% | 21,626 | +10.5% | 3.1 [20] | 31% | 32,762 | huge IS drawdown cut for -1.4 pp OOS mean |
| 3 | **gate + hold 4 (RECOMMENDED)** | +12.1% | 0.0 [0] | 25% | 23,812 | +14.1% | 0.1 [0] | 20% | 29,800 | best risk-adjusted; costs 18% of OOS 1at$ |
| 3b | gate + hold 5 (leave-one-out pick) | +10.6% | 0.9 [1] | 33% | 20,731 | +16.3% | 0.1 [1] | 21% | 33,882 | almost the same risk, keeps more return OOS |
| 4 | take-profit +35% inside a 7 s hold, with gate | +11.3% | 0.0 [1] | 28% | 22,382 | +15.7% | 0.0 [0] | 17% | 33,450 | as good as #3 but needs live curve pricing |
| 5 | gate + hold 4 + half size when creator buy <4% | +12.1% | 0.0 [0] | 18% | 23,812 | +14.1% | 0.0 [0] | 17% | 29,800 | dd 25->18%; compounded gains $40.3k -> $34.3k |
| 6 | sizing 20% -> 10%, floor $30 (baseline rule) | +5.3% | 4.3 [9] | 37% | 11,481 | +11.9% | 0.3 [2] | 23% | 36,308 | pure dial: stop 20->4%, compounding halves |
| 7 | pause 8 trades after -25% from the window peak | +5.3% | 10.9 [16] | 45% | 11,481 | +11.9% | 2.3 [7] | 34% | 36,308 | works, but resampled median end $1,056 -> $388 |
| 8 | two concurrent seats at half size | +5.3% | 14.8 [26] | 42% | 11,481 | +11.9% | 2.5 [10] | 26% | 36,308 | real diversification, but doubles execution risk |
| 9 | cap 2-3 consecutive losses + cooldown | +5.3% | 18-20 [31-35] | 51-54% | 11,481 | +11.9% | 3 [10-11] | 33-35% | 36,308 | ~no effect — losses do not cluster |
| 10 | tighten safety switch (15/-5%, 15/0%, 30/+5%) | — | — | — | — | — | — | — | — | costs $1-8k of chronological gains, buys nothing |
| 11 | max 6 trades per hour | +5.3% | 20.2 [35] | 55% | 11,481 | +11.9% | 3.2 [12] | 36% | 36,308 | compounded gains $30.3k -> $4.4k, stop unchanged |
| 12 | daily stop -30% instead of -50% | +5.3% | 42 [63] | 49% | 11,481 | +11.9% | 12 [34] | 35% | 36,308 | mechanically *raises* stop-outs |
| 13 | reactive exit on a >=1% supply sell (0.3 s later) | +7.1% | 8 [16] | 47% | 15,419 | +9.9% | 8 [45] | 38% | 29,868 | no help — confirms report 21.6 |
| 14 | -15% price stop-loss inside the hold | +5.6% | 17 [29] | 54% | 12,448 | +11.0% | 3 [11] | 37% | 33,395 | no help; the dump is inside 0.3 s |
| 15 | E1 seat instead of E2 | +3.7% | 34 [50] | 58% | 8,327 | +10.6% | 3 [8] | 38% | 31,261 | worse on both axes |
| 16 | hold 10 s | -2.9% | 81 [100] | 63% | -5,668 | +7.7% | 15 [44] | 49% | 21,946 | direction confirmed: exposure is the risk |
| 17 | creator buy >=8% of supply gate (hold 4) | +17.5% | 0 [0] | 11% | 2,300 | +15.4% | 0 [0] | 19% | 10,744 | best per-trade, but keeps 15% of trades; only 8 scorable windows |
| 18 | fee tier >=1.5% gate (hold 4) | -0.3% | 1 [5] | 18% | -43 | +4.6% | 0 [0] | 14% | 2,644 | destroys the edge |

Ranking logic: #1 gives drawdown reduction at *negative* cost (mean return rises in both halves), so it is first.
#2 buys the largest IS drawdown reduction for the smallest OOS return give-up (-1.4 pp). #3 is their combination and
is the only configuration with a 0% resampled stop probability in *every* window of both halves. #6-#8 are honest but
inferior: they cut drawdown by cutting exposure, at 1-2 points of compounding per point of drawdown. #9-#12 and
#13-#16 are rejected.

**Leave-one-window-out** (run6.py section 6): choose from {gate on/off} x {hold 2,3,4,5,6,7} on 10 windows, score the
11th. The pick is `gate + hold 5` in **11 of 11 folds**; mean held-out ROI +13.4% with 0.4% average stop probability,
against the baseline's +9.8% and 9.4%. The choice is stable — no fold ever prefers the current hold-7 no-gate rule.
The strict IS-only pick is `gate + hold 4` (IS hold sweep under the gate: 2 s +9.3%, 3 s +10.6%, **4 s +12.1%**,
5 s +10.6%, 6 s +9.4%, 7 s +7.8%). I recommend hold 4 because it is the IS-only choice and the IS half is the weak
regime; hold 5 is the leave-one-out choice and is reported alongside it in section 4.

---

## 3. The gates, stated executably

Clock convention: `T0` = timestamp of the creation block (the Pons V2 factory Create event); `t` = seconds after that
block, measured on the block stream (~9.9 blocks/s, so `t` is resolvable to ~0.1 s). The launchpad's snipe surcharge
is a function of the *timestamp second*: 93-98% inside second(T0), +6.18% in second(T0)+1, +0.19% in second(T0)+2,
zero afterwards. For every Buy event the engine holds the exact curve state (x*y=k, X0 = 1.68 ETH, Y0 = 1e9 tokens)
and computes the implied total tax `1 - (X*tokensOut/(Y-tokensOut)) / quoteIn`; subtracting the token's own fee tier
(read once from the creator's launch-block Buy) gives that buy's **surcharge**. Classification used everywhere below:
*named/exempt* = surcharge <= 0.08%, *surcharged outsider* = surcharge > 0.1%.

**G1 — bundle (unchanged).** Count buys with surcharge <= 0.08% that land at `t < 1.0 s` **and** before the first
surcharged buy. Require >= 3 distinct wallets and >= 0.3 ETH of quoteIn in total.
*Decided at:* the end of the creation second, i.e. by `t = 1.0 s`. Feed-visible: Buy events.

**G2 — creator size (unchanged).** The creator's own launch-block Buy has `tokensOut >= 1% of 1e9`.
*Decided at:* `t = 0`, from the creation block itself.

**G3 — no second-one outsider (unchanged).** No Buy with surcharge in the +6.18% band (5.0%-7.5% over tier) has
appeared. *Decided at:* continuously, up to our send at `t = 2.0 s`.

**G4 — seat-clear gate (NEW, the recommendation).** *No buy carrying any snipe surcharge (> 0.1% over the fee tier)
has appeared on the feed before our send.* Operationally the engine plans to sit 0.3 s behind the first +0.19%-band
buyer of second(T0)+2; the gate says: **if that first surcharged buy lands at `t < 2.0 s`, stand down and do not
trade this launch; if no surcharged buy has appeared by `t = 2.0 s`, send at 2.0 s (fill modelled at 2.3 s).**
*Decided at:* the instant the rival's Buy is decoded, always at or before `t = 2.0 s` — i.e. strictly before our own
transaction is broadcast. Nothing after our own fill is used.
*What it keys on, empirically* (run3.py, 4 sample windows): of 357 surcharged buys stamped before second two on
rule-passing launches, **352 are +0.19%-band buys** (a rival sniper already in our seat) and 5 are 90-99%-band
creation-second outsiders. Median rival arrival `t = 1.61 s`, median size 0.010 ETH (~$25) — small, fast bots.
*Cost:* removes 13% of IS trades and 32% of OOS trades. Those removed trades averaged -10.8% (IS) and +1.7% (OOS)
with 34%/27% blow-up rates, against +7.7%/+16.8% and 21%/14% for the kept ones.

**Exit (NEW).** Sell 100% on a **4.0 s timer** from our fill (modelled to land 0.3 s late, at `t_in + 4.3 s`).
No price feed, no reaction logic, no take-profit — a pure timer, which is why I prefer it to idea #4 for a retail
operator on one small instance.

Everything else is unchanged: E2 seat 0.3 s behind, 3% of supply capped by the stake, minOut refusal at +25%,
20% sizing with stakes clamped $50-$300, one position at a time, daily stop -50%, safety switch 15/-10%
(the switch is now nearly inert — it costs $246 of $40,572 chronological gains and never saves a window).

---

## 4. Recommended configuration and its per-window table

**RECOMMENDED = current rule + G4 seat-clear gate + 4 s timer exit.** All parameters chosen on the IS half.

`stop%` below is the resampled probability of hitting the -50% daily stop from $300 (1,000 shuffled orderings of that
window's trades, 20% sizing, stakes $50-$300). `rs median` / `rs p10` are that resampling's end bankroll.

| window | n | mean ROI | median | <-40% | flat $300 | 1-at-a-time | compound from $300 | rs median | rs p10 | **stop%** | maxDD |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **in-sample** | | | | | | | | | | | |
| 2026-08-12 12-18 | 0 | — not scored (0 rule-passing launches) | | | | | | | | | |
| 2026-08-20 12-18 | 1 | — not scored | | | | | | | | | |
| 2026-08-27 12-18 | 6 | — not scored | | | | | | | | | |
| 2026-08-30 12-18 | 141 | +9.8% | +14.4% | 9% | $3,929 | $3,770 | $2,786 | $2,855 | $2,761 | **0.0%** | 27% |
| 2026-08-31 12-18 | 238 | +11.8% | +15.9% | 8% | $7,856 | $7,452 | $6,157 | $6,875 | $6,789 | **0.1%** | 22% |
| 2026-09-01 12-18 | 181 | +9.9% | +18.3% | 12% | $4,577 | $4,634 | $3,769 | $3,737 | $3,654 | **0.0%** | 28% |
| 2026-09-02 12-18 | 164 | +17.1% | +22.2% | 11% | $8,185 | $7,956 | $6,995 | $7,088 | $6,980 | **0.0%** | 23% |
| **out-of-sample** | | | | | | | | | | | |
| 2026-09-03 0-6 | 48 | +7.8% | +13.9% | 12% | $1,079 | $1,014 | $579 | $594 | $572 | **0.0%** | 23% |
| 2026-09-03 12-18 | 155 | +20.7% | +18.9% | 8% | $9,444 | $9,374 | $8,177 | $8,335 | $8,249 | **0.0%** | 19% |
| 2026-09-03 18-24 | 270 | +13.8% | +19.3% | 12% | $11,124 | $10,337 | $9,071 | $9,886 | $9,712 | **0.4%** | 30% |
| 2026-09-04 12-18 | 61 | +5.4% | +0.0% | 2% | $982 | $989 | $528 | $536 | $520 | **0.0%** | 14% |
| 2026-09-05 0-6 | 42 | +12.6% | -1.8% | 7% | $1,604 | $1,604 | $752 | $765 | $738 | **0.0%** | 20% |
| 2026-09-05 12-18 | 92 | +20.3% | +0.8% | 4% | $5,534 | $5,545 | $4,323 | $4,400 | $4,326 | **0.0%** | 17% |
| 2026-09-06 12-18 | 67 | +4.8% | -1.8% | 3% | $930 | $937 | $490 | $509 | $487 | **0.0%** | 20% |

Totals — IS: n=724, mean +12.1%, worst window +9.8%, 4/4 windows positive, one-at-a-time $23,812, compounded gains
$18,507, **average stop probability 0.0% (max 0.0%)**, average resampled max drawdown 25%.
OOS: n=735, mean +14.1%, worst window +4.8%, 7/7 positive, one-at-a-time $29,800, compounded gains $21,819,
**average stop probability 0.1% (max 0.4%)**, average max drawdown 20%.

**Baseline for the same table** — IS: mean +5.3%, worst window +1.7%, one-at-a-time $11,481, compounded gains $6,050,
stop 20.2% (max 35.2%: 19.6 / 22.5 / 35.2 / 3.3 by window), max drawdown 55%.
OOS: mean +11.9%, worst +5.2%, one-at-a-time $36,308, compounded gains $24,271, stop 3.2%
(0.1 / 2.6 / 6.7 / 0.0 / 0.3 / 0.5 / 12.5 by window; max 12.5%), max drawdown 36%.

**What the recommendation costs.** OOS it gives up ~18% of the flat one-at-a-time net ($36.3k -> $29.8k) and ~10% of
compounded gains ($24.3k -> $21.8k), because the gate removes a third of OOS trades and the 4 s timer clips winners
(OOS mean under the gate is +16.8% at hold 7 vs +14.1% at hold 4). In exchange the -50% stop, which the current plan
hits 15-35% of the time on the four weak windows, effectively disappears (worst window 0.4%), the average resampled
max drawdown falls from 55%/36% to 25%/20%, and the blow-up rate per trade falls from 22.6%/17.9% to 10.0%/8.4%.
Across all 11 scored windows the recommended config is also simply better in dollars: compounded gains $40,326 vs
$30,321, one-at-a-time $53,612 vs $47,789.

**If you want the return back**, `gate + hold 5` (the leave-one-out pick) keeps OOS mean at +16.3%, one-at-a-time
$33,882 and compounded gains $25,505, at 0.1% average stop probability (max 1.3%) and 21-33% max drawdown — i.e.
nearly all of the risk benefit with none of the OOS return give-up. It is not the IS-only choice, so I report it as
the alternative rather than the recommendation.

**Optional overlay if the operator wants a still-smaller drawdown**: half size when the creator's launch buy is
<4% of supply (a pre-entry, feed-visible quantity, decided at `t = 0`). It leaves per-trade means untouched, drops
average resampled max drawdown from 25%/20% to 18%/17%, and costs $6k of the $40.3k compounded gains.

---

## 5. What I could not test

- **Whether the gate survives contact with reality.** G4 removes launches where a rival bot is already in the seat.
  If that bot is itself the marginal buyer whose absence changes the curve, or if rivals adapt to our standing down,
  the edge changes. The replay assumes every other participant behaves identically whatever we do (apart from the
  10% minOut attrition and the +25% refusal), which is exactly the assumption that gets violated first.
- **Fill timing.** Everything is modelled at a fixed 0.3 s behind the seat's first buyer and a 0.3 s late sell.
  I could not test a distribution of latencies, missed blocks, mempool competition for the same seat, or gas spikes;
  block timestamps here are interpolated at 9.9 blocks/s, so `t` carries ~+/-0.1 s of error and the exact phase of the
  creation block inside its wall-clock second is not recoverable from the data.
- **The 2.0 s send time is the only executable threshold in its family.** "Skip if the seat opened before 2.5 s"
  (ALL mean +15.0%) and "skip if any rival ever takes the seat" (+14.8%) both score better, but both require knowing
  what happens *after* our own send at 2.0-2.3 s. I rejected them as look-ahead and did not carry them forward.
- **Sample size and regime.** Only 11 of 14 windows carry >=10 rule-passing launches; the IS half is effectively four
  windows from four consecutive days (Aug 30 - Sep 2) plus three unusable ones, so "in-sample" here is thinner than
  "seven windows" suggests. All data spans 26 days of one launchpad; nothing tests a different fee regime, a change
  in the surcharge schedule, or a different ETH price (fixed at $2,445 throughout).
- **Multi-day paths.** Every window is treated as an independent day starting at $300, following the existing plan
  scripts. I could not test a true multi-day bankroll path with the daily stop re-arming, nor the operator's real
  withdrawal/top-up behaviour.
- **Idea generation was not blind.** Parameters were chosen on the IS half and the leave-one-out test is honest, but
  the *candidate list* was written after seeing pooled tables from earlier rounds of this project. The OOS column is
  a held-out evaluation of chosen parameters, not a blind test of the search itself.
- **Two-seat diversification and per-hour caps were tested only as position-sizing overlays**, not with real
  nonce/queue mechanics; running two concurrent positions from one wallet on one small instance may not be feasible.
- **Post-window behaviour of the tokens** (anything after the 6-hour capture) and any effect our exit has on later
  buyers are outside the replay entirely.
