# R2, nightly review of Sep 28, 2026

Basis: `engine_replay.py` via `run_replay.py`, Sep 21 09:40 - Sep 28 21:00 (685 launches, three views, slip 0.20, `rows_*.json`),
the crowd and launch files, the engine source. Fit Sep 21-23, read Sep 24-28; today (09:40-21:00) no earlier review fitted on.
$13, h11, second place, gas $0.33.

## Q1. Did the 2 ms step land us earlier? Not shown (`q1_landing.*`)
From the chain (our relay's shots per block, their index against rival transactions in E1):

| settings | bursts with shots in E1 | first in E1 | median rival txs ahead | no shot in the creation second |
|---|---|---|---|---|
| old 3 ms / 80 ms (Sep 26 13:47 - Sep 28 08:43) | 8 | 3 | 1 | 1 |
| new 2 ms / 46 ms (15:30-19:15) | 6 | 3 | 0.5 | 1 (15:33) |

Fisher one-sided p = 0.53 on bursts. On fills the brief's own list gives **3 of 5 first today, not 4** (15:30, 18:52, 19:15; 16:33 was
second, 15:36 third of six E1 buyers); before, 1 of 5 first in E1: p = 0.26. The step moves the first post-tick shot about 0.5 ms;
today's order followed which rivals were present (0xfb5b1061 ahead of us at 15:36 and 16:33). To settle: 18 fills per
arm if first place went 40% to 80%, 77 if 40% to 60% (38 landings against a fixed 40% baseline). What it is worth: first minus
second at h11 is +7.7 points on 54 Sep 24-28 fills (median +3.8).

A better live metric is the burst's offset, read from how many shots land in the creation second: new bursts sat 12-32 ms later
than the estimate (median 24; old median 41 against an 80 ms lead). The 46 ms lead leaves about 22 ms of early margin; 15:33
overran it (no shot before the tick, first shot behind 42 rival transactions, last). 5y's rollback watches all-creation-second
bursts (0 of 6); the tail that showed up is the all-late one. Watch it: 3 or more of the next 10 bursts with no creation-second shot
would argue for a longer lead.

## Q2. Guard-admitted class (`q2_guard.*`)
Live today: one admitted fill (15:36, two buys ahead, -7.1% = model), not last; tally 1 of 10, class LLR -0.25. The guard also
refused the one deep landing (15:33, 23% under, last of nine; modelled at last place -21.3%). On the chain four of today's ten
usual-view fires sit in the 0.80-0.93 band (+41% at second place), but live two landed first and one was held, so the class
accrues about one a day: the ten-fill checkpoint is one to two weeks out, its own test needs about 19 fills at +22% or 48 at +15%.

The slip re-read on today alone: usual view 0.07 -$3.11 (4 fills of 10), 0.15 and 0.20 +$18.21 (8), 0.25 +$20.49 (9); floor
-$1.32 vs +$15.99; ceiling +$3.51 vs +$20.07. Out of sample, 0.20 over 0.07 holds. Live it touched only 15:36 (-$0.92): the
two band fires that paid landed first. Keep 0.20; the rule stands (back to 0.15 if most of the first ten land last or later).

## Q3. The two new skips
**12:52 "bundle 0 < 3" is the 6.7 fold, not the poll.** `fold_buy` set `bundle_closed` at the first non-named buy inside the creation
window and ignored every named buy after it. On `0x98f4e88b` a stranger's relay call sat at index 3 of block 2, the team's 22 helper
buys at 14 onward in the same block. Engine 6.8 (committed 21:07) removes the close. Replaying the old rule on the crowd files
(`q3_bundle_close.*`): 28 population launches of 685 skipped (upper bound: every stranger call closes; 3 if only direct calls do;
the live cases 12:52 and Sep 25 `0xd43ed726` fit the upper bound). At the usual view 20 fire and fill: Sep 21-23 14 fills +12.1%
+$17.39; Sep 24-28 5 fills +7.5% +$3.23; today 1 fill -1.9% -$0.57. Fixed; worth about +$0.5 a day now. Its real value: every
projection (24.41, K0-K3, the predictions) already counted these launches as fires.

**19:44:59 "nonce/gas not fresh"**: the gate (line 1946) needs `chain_loop`'s last good poll within 30 s. The loop polls every
CHAIN_POLL_S = 3 s but does blocking work inline: every 100th pass 70 sequential shooter reads, a top-up of low shooters (one
transfer and up to 5 s receipt wait each; all 35 fire once per burst, so they run low together) and a 10 s-timeout price fetch.
6.8 allows 60 s and retries 2 s after a failure. Worth nothing measurable: the replay reverts that launch at the guard (0.751 of
the sizing; last place -29.7%). Check the log for `shooter_topup` or a `chain_loop` error in the minute before; if a top-up was
running, 60 s does not cover 35 of them: move it to its own thread.

## Q4. A signal for a block-k crowd? No (`q4_blockk.*`)
Refused at the usual view: 200 launches fit, 141 read. **Even an oracle for the block-k crowd loses**: those launches fired pay
+4.9% (62) / +3.8% (37) and -$0.33 / -$0.25 a fire after guard reverts and gas. The best predictor of the crowd is one fleet at
k-1 (54% / 53% against 18% / 14%), but firing on it is -$63 / -$18. Ten threshold rules (fleets, wallets, k, bundle, named,
creator supply and buy, 60-minute heat, hour, tier) chosen on one half: none positive on the other both ways (best, wallets >= 2:
+$3.2 read, -$31.7 fit). The crowd-less winners (18:42, 20:24; 14:20 and 17:48 at k = 1) share nothing before the tick.

## Q5. Anything else (`q5_other.*`)
- The engine took 7 of the 8 usual-view fires that reached its crowd gate, three with under two fleets at k-2 (15:36, 16:33,
  18:52), and refused 19:44 `0x2c38692a` (0 at k-2). The two-core box sees about k-1; the Sep 26-28 calibration (k-2 five of ten)
  is stale. Projections should use the usual view.
- No split of the current fires loses in both halves (tier 2% +$13.4 / +$3.3; bundle, fleets 2 vs 3+, k, heat all positive
  both sides): no filter. Hold: h11 best or tied in every window (18.1 / 13.0 / 20.7 vs h13 17.0 / 12.1 / 11.5).

## Q6. Verdict
**Deploy engine 6.8 with the morning reading (runbook 5z), nothing else.** Count: 28 affected launches a week (upper bound), 20
fills at the usual view; expected about +$0.5 a day at $13 on the Sep 24-28 supply, and -$1.2 a day on today's literal supply
(its one case, 12:52, modelled -1.9%): call it $0 plus or minus $1. A correctness fix, not an edge. Verify: the morning `engine_vs_chain` shows no `bundle 0 < 3` on a launch with three or more named buyers on the chain,
and those launches' fires enter the chain-scored test as before. No slip, step, gate, filter, hold or size change survives today's
data; the step question needs 18-77 fills.

Housekeeping: `engine_replay.py --dump` writes relative to the repo root (`run_replay.py` fixes the path). This folder's first
files were swept into commit `aa0f85a` by the orchestrating session, not by this reviewer.
