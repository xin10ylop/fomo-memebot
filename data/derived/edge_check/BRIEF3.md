# Hold sweep (Sep 27 2026): every exit from 1 to 600 blocks, measured, not guessed

Three independent reviewers (letters E, F, G) get this same brief. Read-only on the code; write under
`data/derived/edge_check/<letter>/`; do not modify `src/`, `deploy/` or `docs/`; do not commit; do not read the other
letters' folders of this round (A-D from earlier rounds may be read and reused). Public RPC
`https://rpc.mainnet.chain.robinhood.com` only, paced (4 threads at most, 0.15 s between calls, back off on 429).

## Context (docs/REPORT.md 24.28-24.36)

The rule: at a Pons V2 launch, fire a 35-shot burst for the seat E1 (the second after the creation second) when at
least 2 fleets have shot at the curve by block k-2 of the creation second; the position is sold after a fixed number
of blocks. The hold was 300 blocks from Sep 23 (chosen on the fit windows' tables) and is 15 blocks since Sep 27 11:17
UTC (round 2: both periods positive at 15, the discovery's own horizon, both failure mechanisms act after block 15).
The holds ever priced were 15, 30, 60, 150, 300, 600 and two stop/take-profit variants. Nobody has priced every block.

Yardstick (every number on it): `stake_scale.model_eff` as used by `src/analysis/reach_table.py` and round 2's
scripts: second place in the E1 block (one buy ahead), $13 at 2570 $/ETH, the second's surcharge (6.18% in second +1),
the tier fee on buy and sell, the 3% supply cap, the exit's own impact on the curve, gas $0.33 a burst. The exit sells
at the block E1 + h, folding every buy and sell of the tape up to that block.

Data: the fit windows Sep 18-23 (563 launches, 73 fires) and the recent windows Sep 24-27 (160-172 launches, 18-19
fires); `data/derived/edge_check/A/tapes.json.gz` holds the 91 fires' tapes (Buy/Sell events from b0 to about b0+640
with block stamps); `C/` and `D/` pulled the rest of the population (see their pull scripts; D's `features.json.gz`,
C's `pop.json`); `src/analysis/live_vs_table.py` `launch()` pulls a tape (pass b_last to extend it). Fires and
population as in `reach_table.py` (`crowd_rules.cums/at`, fleets >= 2 at k-2).

## The task

1. Price the rule's fires at EVERY hold h from 1 to 600 blocks (and to 1,200 where the tapes reach), for: the fit set,
   each of the four fit windows separately, the recent set, and day by day Sep 18-27. Report mean, median, win rate,
   dead rate (< −40%), standard deviation, $ a fire after gas, and the fires' lift over the refused launches at that h
   (price the refused too, at least at every 5th block).
2. Choose h on the fit alone and read it on the recent set; choose on the recent alone and read it on the fit; choose
   on Sep 18-21 and read on Sep 22-27. Report each choice's plateau: the range of h whose mean is within one standard
   error of the optimum's, on the choosing set. A spike is not an answer; a plateau is.
3. Robustness: bootstrap the fires (2,000 resamples) and report the distribution of the optimal h and of the mean at
   h = 15 and at your candidate; leave-one-window-out on the fit; the effect of the sell landing 2-4 blocks late (the
   engine's sell lands after the hold, not at it: evaluate every candidate at h+2 and h+4 as well).
4. Two-stage exits only if they pass the same discipline: a take-profit level with a hold, a stop with a hold, a
   partial exit (half at h1, half at h2). Report them against the best fixed hold on both periods; the earlier finding
   is that dumps happen in one block so stops do not help. Do not search widely: at most a handful of levels, and say
   how many variants you tried (the more you try, the less a pass means: apply the null-test discipline of 24.34, e.g.
   permute the per-fire return paths across fires and count how often a variant "wins").
5. $ a day at $13 at the recent supply (0.32 fires an hour at full fill; the live mix fills about half the bursts and
   lands third a third of the time) for h = 15, the fit's optimum, the recent optimum and your recommendation.

## Deliverable

`data/derived/edge_check/<letter>/REPORT.md`, first line the verdict: KEEP 15 / CHANGE to h = N (plateau a-b), with the
mean at that h on BOTH periods and the out-of-sample reading of the choice. Then the curves (a table every 5 blocks
from 1 to 60, every 20 to 300, every 50 to 600, both periods), the choices and their plateaus, the robustness, the
two-stage results, the $ a day, and every number with the command that reproduces it (scripts in your folder).
Plain prose, no hedging. Budget: about 90 minutes.
