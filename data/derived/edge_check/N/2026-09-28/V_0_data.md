# V_0 (data lens): verifying R1's "deploy engine 6.8's bundle fix" (Sep 28)

Scripts and outputs are in `V_0_data/`: `v_bundle.py` (my own 6.7 vs 6.8 fold on all 685 launches), `v_money.py`, `v_side.py` and `v_confirmed.py`.
Everything was read from disk. I did not commit anything. (Side note: importing either engine module writes a `sender_addresses` RTT probe
to the sequencer into its LOG_PATH at import. R1's `engine67_log.jsonl` has the same line. Nothing is sent.)

## 1. Reproduction: R1's numbers hold as stated
- `engine_replay.py` re-run for all three views at `--slip 0.20`: 685 rows each, **0 differing rows** from R1's dumps.
- R1's `engine67.py` is byte-identical to `git show 34265b9:src/strategy/sniper_engine.py`. 6.8 (working tree) never sets
  `bundle_closed` anywhere: 0 closes on 685 launches.
- My own fold uses each engine's `watch_curve`, both modules, and three feed horizons: blocks < k-1, blocks < k, and all captured blocks. It gives the same 20 usual-view fires. Fit: 14 fires, +$17.39. Read: 6 fires, +$2.66. Floor: +$3.36 / +$4.94. 12:52 gives bundle 0 under 6.7 and 22 under 6.8.
- Small corrections, none decisive:
  - The "36 affected gate-reaching launches" overcounts. R1's 8 "closed by a direct buy" include launches that 6.8 also counts under 3, and R1 never ran 6.8. The corrected figure is 32 at R1's horizon and 26 at what the feed has shown by the gate.
  - Ceiling read: R1 reports 9 fires, +$0.12. I get 7 fires, +$0.78 at the gate-time horizon, and 8 fires, +$0.45 at R1's horizon. R1's 9th fire is a launch that 6.8 does not change.
- No side effect at the ETH gates. Five launches were partly counted by 6.7 (bundle of 3 or more, closed early). Under a pro-rata estimate, none crosses 0.3 or 3.0 ETH (`v_side.txt`).

## 2. The mechanism is real, but only for one bot
- In 17 of the 20 usual-view fires, the first outsider call is the same one: `0x8191c327` → `0xbd7c6f67` (`cce7ec13`), in block 1 or 2, before the
  team's buys. That call closed the bundle live twice: Sep 25 16:24 `0xd43ed726` and today's 12:52, both "bundle 0 < 3". So it carries value, and those 17 skips are real.
- The report blamed Sep 25 on a pre-6.5 ordering bug. That is not the cause: on `0xd43ed726` the bot sits at block 2 ix 27, before the team at ix 30, in chain order.
- Two more fires close on a stranger's direct buy (a skip whatever its value). Those two are -$8.99.
- **The other two fires are an assumption, not a measurement.** 0x39501200 (+$10.90) and 0x50dd5611 (+$1.11) are closed by calls through `0x5b8e11e3` (`d7311a37`, `33bfe246`). That relay has never been seen closing a bundle live. The crowd rows carry no value, and if those calls carry none, 6.7 counts bundles of 4 and 14 and fires on both anyway.
  - 0x39501200 is also marginal on its own: its bundle is 0.368 ETH in 4-5 direct buys (blocks 3, 4, 6, 7), so by the k-1 read the count is 4 and the ETH is near the 0.3 floor.

## 3. The tests the owner asked for (guard 0.20, $13, gas $0.33)
| view | fit | fit without its largest | read | read without its largest |
|---|---|---|---|---|
| floor (k-2) | 3, +$3.36 | +$1.32 | 3, +$4.94 | **-$0.28** |
| usual (k-1 reg) | 14, +$17.39 | +$6.49 | 6, +$2.66 | **-$2.56** (5 fires, 2 wins, median -$0.32) |
| ceiling (k reg) | 14, +$17.39 | +$6.49 | 7, +$0.78 | **-$4.43** |

- **The whole out-of-sample gain is one fill.** 0xd43ed726 (Sep 25, +$5.21) carries the read half. Without it the read half is negative at every view.
- **63% of the fit half is one fill**, 0x39501200 (+$10.90), and it is one of the two unconfirmed closers above.
- **On the confirmed set only** (the bot plus the direct buys), usual view:
  - fit: 12 fires, +$5.39; -$0.35 without its largest
  - read: 6 fires, +$2.66; -$2.56 without its largest
  - week: 18 fires, +$8.04; +$2.30 without the largest, **-$2.91 without the two largest**
- **Too few fires to tell from zero**:
  - Read half: t = +0.43 at the usual view and +0.12 at the ceiling.
  - Bootstrap probability that the read total is at or below $0: 0.34 at the usual view, 0.48 at the ceiling. The 90% interval for the usual view's read total is -$5.38 to +$13.05.
  - The floor has 3 read fires.
  - The week at the usual view: 20 fires, t = +1.21, probability at or below $0 is 0.10.

## Verdict
**Refuted as a gain. The correctness fix is not refuted.**
- The claimed +$0.5 a day does not survive removing one fill in the read half at the floor, usual or ceiling view.
- It rests on 6 read fires, which cannot be told from zero.
- The fit half's size comes mostly from a launch whose 6.7 skip is not established.

**Recommendation:**
- Deploy 6.8 only as a correctness fix with an expected value of $0, not an edge. The mechanism is real and the week shows no downside: the side-effect check at the ETH gates is clean.
- Verify it with the log condition, not with P&L: no "bundle N < 3" on a launch whose chain bundle has 3 or more exempt buyers.
- Book nothing until about 20 of these fires are scored live.
