# R1 nightly review, Sep 28 2026

**Basis.** `run_replay.sh`: engine_replay through Sep 28 21:00 at the live guard (0.20), three views, dumped; 685 launches. Usual
view (k-1 + registration): 139 fires, 128 fills, +$225.69 at second place. Fit = Sep 21-23 (2.59 days), read = Sep 24-28 21:00
(4.85 days). $13, gas $0.33. **The repo moved during this review**: engine 6.8 (`aa0f85a`, runbook 5z) was committed at 21:07.
Q3 therefore replays the *live* 6.7 (`engine67.py` = `git show 34265b9:src/strategy/sniper_engine.py`).

## Today on the replay (`q0_today.txt`)
Since 12:27 at 0.20: floor 4 fires +$15.99, usual 10 fires +$18.21, ceiling 18 fires +$20.40. Live: 7 bursts, 5 fills, +$11.73.
15:30 is +$16.9 of the usual view's +$18.21.

## Q1. Did the 2 ms / 46 ms step land us earlier? (`q1_landing.py`, from crowd_raw's chain order)

| | bursts in E1 | our first shot at position 0 | head-to-head vs every rival in the same E1 | our shots in the creation second |
|---|---|---|---|---|
| before 12:27 (Sep 26-28) | 8 | 3 | 24/34 (71%) | 45% |
| after 12:27 | 6 | 3 | 26/38 (68%) | 28% |
| on-time gates only (drop the two late-gate bursts, 00:10 and 15:33) | 7 / 5 | 3 / 3 | 24/32 (75%) / 26/29 (90%) | |

- Correction to the brief: since 12:27 the fills landed at index 1, 4, 2, 1, 1. That is 3 of 5 first. "4 of 5" only works if the
  08:43 fill (old settings, index 1) is counted.
- Fisher p = 1.00 on first place and 0.19 on the on-time head-to-head. The pairs cluster by burst, so 0.19 flatters it.
- What did change is the share of our shots landing in the creation second: 45% before, 28% after. No burst so far has put every
  shot there, so the rollback trigger has not fired.
- 40% vs 70% first place at 80% power needs about **42 bursts a side**; the "before" side is frozen at 8, so only the box's
  sent_burst lateness can settle it.
- If real: first beats second by 9-11 points, so +20 points of P(first) at 5 fills a day is about $1.3 a day. Keep the step.

## Q2. The guard-admitted class (`q2_admitted.txt`)
- **Live today: one admitted fill.** 15:36 landed at index 4, not last, at -7.1%, the same as the model. That puts the class's own
  test at LLR -0.25 (bounds ±2.94).
- 15:33 came in 23% under the sizing and was still reverted. Rollback trigger: 1 of 10, not met.
- The replay's admitted set at second place (14:55, 15:30, 15:33, 19:15) landed held, first, last, first live. **The landing
  decides the class, not the replay's label.**
- The guard change moved exactly one outcome today: 15:36, which cost $0.92. 15:30 (+$12.36) and 19:15 landed first and would have
  filled at 7% too. **Today's P&L is not evidence for 0.20.**
- On the week, the admitted class at second place: fit n=34, +13.2%, +$47.20; read n=22, +25.3%, +$65.20. The fixed-size first
  buyer `0x6c56103c` is back today (in E1 on 15:30, 15:33 and 15:36; `q5_rivals.txt`).

## Q3. The two new skips
**12:52 `0x98f4e88b` "bundle 0 < 3": found and fixable** (`q3_bundle.py`).
- In block 2 a stranger's call (`0x8191c327` → `0xbd7c6f67`) sits ahead of the team's 21 helper calls.
- The live 6.7 `watch_curve` folds in chain order, and `fold_buy` sets `bundle_closed` at that call. Result: **bundle 0**.
  Replayed with that call carrying no value, the bundle is 22.
- On the week, 36 gate-reaching launches carry the pattern. At the usual view that is **20 fires, +$20.05**: fit 14, +$17.39
  (+$6.72/day); read 6, +$2.66 (**+$0.55/day**). Floor: +$1.30 / +$1.02 a day. Ceiling: +$6.34 / +$0.02.
- Two of the 20 were closed by a stranger's direct buy (-$8.99, fit).
- Upper bound: it assumes every stranger's call naming the curve carries value.
- Engine 6.8 removes the close; my numbers agree with its commit. No side effect at the gate: it reads before the tick.

**19:44:59 `0x057d1ffe` "nonce/gas not fresh (RPC)": not worth fixing further** (`q3_nonce.py`).
- `release_reservation()` (6.7 line 1664) sets nonce to None after every burst that ends without a fill.
- 19:44:51 `0x2c38692a`, a live gate refusal, released 6-7.5 s earlier. That is more than the 3 s poll, so a failed or slow pass
  (the every-100th pass runs `refresh_shooters` and a 10 s price fetch) also had to happen. Only the box's log can tell.
- 6.8's 30 → 60 s change does nothing on this path (the nonce is None, not stale). Its 2 s retry after a failure helps.
- On the week: 4 gate-reaching launches came within 12 s of a release, 2 of them fires worth -$1.92. The expected loss under the
  normal poll is $0.00. Rolling the reservation back (nonce -= 2 when no shot left) would be hygiene, not money.

## Q4. Crowds only in the tick's block, or none (`q4_tickcrowd.txt`)
- Refused at the usual view: fit 200 launches, -3.7%; read 141, -1.5%.
- 31% (fit) and 26% (read) of them get their crowd in block k: +4.9% and +3.8% at second place.
- **Even a perfect oracle for that crowd loses at the live guard**: fit 62 fires, -$20.72 (-$8.01/day); read 37, -$9.28
  (-$1.92/day). Only guard off pays (+$19.38 / +$5.90), and that is unsafe.
- 11 pre-tick signals (fleets, wallets and shots at k-1, fleets at k-2, k, bundle ETH, named, tier, creator supply, the last 10
  launches' crowd rate, minutes since the last launch), each chosen on one half: **none gains in both directions**.
- The no-crowd winners (20:24, 18:42) sit in a class paying -7.6% / -3.4%. **No.**

## Q5. Other things today suggests (tested, dropped)
- **The team's forward-sender helper counted as a rival fleet** (`note_attack` adds its target, and `--reg` counts its block).
  Only 9 of 139 usual-view fires depend on it: fit 4, +$4.34; read 5, +$4.23. Dropping it loses money in both halves; the count
  stands.
- **Slip 0.25 with today's data** (`q5_slip_today.txt`), usual view against 0.20: fit +$7.15 on 3 more fills, read +$0.97 on 2.
  One or two launches, more deep-landing risk. Keep 0.20.

## Q6. Verdict
Nothing new beyond what is already committed. **Deploy engine 6.8 as in runbook 5z.**
- Its bundle half is the only change with a positive number in both halves: +$6.72 fit and +$0.55 read a day at the usual view,
  on 20 fires.
- On today's supply it is **-$0.67 a day**: its one case, 12:52, is -1.9%.
- Realistically expect about **+$0.5 a day**. It is a correctness fix, not an edge.
- **Verify live**: in the morning reading's `engine_vs_chain`, no "bundle N < 3" on a launch whose chain bundle has 3 or more
  exempt buyers; about 1.2 such fires a day, scored on the main sequential test.
- Change nothing else until the counts exist: the guard (1 of 10 admitted fills) and the step (6 of about 42 bursts). The edge
  question stays with the sequential test (16 fires, LLR +0.03).
