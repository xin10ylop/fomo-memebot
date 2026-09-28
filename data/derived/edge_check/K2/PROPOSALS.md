# Brief K, reviewer K2: proposals (Sep 28)

**Basis.** `build_table.py` + `sim.py` rebuild engine_replay's week launch by launch and reproduce 24.41 exactly (floor 45/27/18
$45.17, usual 129/61/68 $97.92, ceiling 219/118/101 $80.65). Every setting below is changed one at a time in that chain. Fit =
Sep 21-23 (62.1 h, 79 fires at the usual view), read = Sep 24-28 09:40 (105.7 h, 50 fires). `price_tapes.py` re-prices the 535
launches that have a B/D tape at any place, block and stake (equal to `hold_grid.model_path` to 0.0; to G's r2 with the ETH fold).
Tapes cover 103 of the 129 fires (71 fit, 32 read). Every sample under about 30 is flagged. $ at $13, $0.33 a burst.

## The one recommendation (Q8): BURST_SLIP 0.07 -> 0.15

The 7% guard trips on the buy ahead in E1, not on the drift of the creation second (taped trips: 44 of 48 from the buy ahead,
2 from drift). A big buy ahead marks the crowd that pays (Q4), so the guard removes good fills. Its original job, stopping a
second fill of our own, is now done by the BuyOnce relay (`contracts/BuyOnce.sol`, `AlreadyBought`).

| basis (0.07 -> 0.15) | fit $/day | read $/day |
|---|---|---|
| replay convention: every burst lands second (all 129 fires) | 31.93 -> 52.58 (**+20.65**) | 3.47 -> 13.08 (**+9.61**) |
| live landing mix: first 3/8, second 3/8, last 1/8, first in E1+2 1/8 (the 8 live bursts that landed) | +7.22 | **+4.39** |
| deeper mix: 1/4 each first/second/third, 1/8 last, 1/8 E1+5 | +12.64 | +4.79 |
| worst case: 1/2 last, 1/4 E1+2, 1/4 E1+5 | -2.45 | +0.76 |

In the live-mix and worst-case rows the guard is checked at the place the burst lands, so deep and late fills the looser guard
admits are charged. The incremental fills at second place: read **15, mean +21.7% (95% +6.4..+38.7), median +11.5%, win 80%**,
+$31.6 without the largest. Fit: 29, mean +14.2% (95% +2.5..+27.1), median +1.5%. The gain is positive on every day that has
a changed burst (Sep 21-25 and 27). Out of sample: chosen on fit, the best slip is 0.30, which reads +$49.8 on read; chosen on
read it is 0.20, which reads +$58.4 on fit. I take **0.15, not 0.20-0.30**. On the fit, if every burst lands last or late, 0.20+
costs $6-10 a day against 0.15, because held bursts landing at E1+2..E1+8 get through (`q1c_late.txt`). 0.15 is also the choice
the fit makes under the deeper mix.

**Expected effect at $13 on the Sep 24-28 supply: +$4 (live landing mix) to +$10 (replay convention) a day at the replay's 11.4
fires a day.** Live fired about 5 a day on Sep 26-28, so plan on **+$2-5 a day**. Worst case -$2.5 to +$0.8 a day.

**Against it.** The replay sizes the guard's build on the chain's k-2 view, and the engine's build view differs. Of the 4 live
reverts, 3 are templates the replay rates q = 1.0 (all capped now). The fourth, 17:06 `0x4fed869a`, landed last at q 0.884. At
0.15 it would have filled at -2.5%. The held 22:09 burst filled live although the replay trips it. So the live trip rate is
unknown, and the gain depends on how often live landings sit at q 0.85-0.93.

**Verify live.** Log q = tokens received / tokens sized at the build on every fill. Run the SPRT (H0 +2.5%, H1 +19%, sd 0.34,
±2.94) on the fills with q in [0.85, 0.93): about 19 fills if the read mean holds, 25 at H1, 16 to reject at -2.5%. That is
1-2 weeks at 1.5-3 such fills a day. The main SPRT scores fires at second place and is unchanged. A free pre-check: score each
past revert at its real landing index.

## Q1. The guard
- At 0.07 the replay reverts 61 of 129 bursts: gas $20. At second place those reverts would have paid **+15.7% mean ($125)**:
  fit +13.7% on 42, **read +20.2% on 19 (win 79%)**, against the fills' +22.6% and +7.9%. The guard does not select.
- The slip sweep in read $/day: 0.05 1.74, 0.07 3.47, 0.10 7.86, 0.15 13.08, 0.20 15.08, 0.30+ 14.79. Fit: 28.2 ... 60.9, same order.
- Smarter guards (bypass at fleets ≥3 or 4, bundle ≤1.5, tier 3%, k ≥5, drift-only): none beats plain 0.15 in both periods.
  For example, bypassing at fleets ≥3 gives fit $147.9 vs $136.1 but read $48.1 vs $57.6.
- By landing place (taped, $ change 0.07 -> 0.15, fit/read): first 0/0, second +48/+30, third +76/+25, last -4/0, E1+2
  -6/+10, E1+5 -9/-1, E1+8 -11/-10.

## Q2. The filters (switched off one at a time; added fires at the usual view)

| filter | added fires fit/read | at second place | $ if off, fit / read | verdict |
|---|---|---|---|---|
| creator supply < 1% | 12 / 8 | -9.8% / +6.3% | -12.0 / +6.1 | keep: the sign flips, and 8 is too few |
| bundle cap 3.0 ETH | 7 / 8 | -11.0% / -10.6% | -10.9 / -13.7 | keep: earns it in both |
| creator repeat | 3 / 0 | +11.3% / - | +1.5 / 0 | too small to judge |
| bundle count < 3 | 1 / 0 | +5.5% | +0.4 / 0 | too small |
| creator buy > 2 ETH, tier 100-200, floor 0.3 ETH | 0 / 0 | - | - | untestable: every file on disk is tier 2-3% and ≥ 0.3 ETH |

The creator-supply threshold swept 0-3% gives no setting that beats 1% in both periods.

## Q3. The gate
At the usual view, ≥2 fleets is the best threshold in both periods at both slips.

| k-1+reg | ≥1 | ≥2 | ≥3 |
|---|---|---|---|
| slip 0.07 | fit 44.7 / read 3.7 | 82.6 / 15.3 | 50.1 / 9.1 |
| slip 0.15 | 72.9 / 42.1 | **136.1 / 57.6** | 91.3 / 33.0 |

- The tick's block (k) adds 62 fit and 28 read fires. At second place they average +4.9% and +4.3%; at last place, -6.4% and
  -2.2%. The k view earns less than k-1 in all four cells, so do not widen the gate's close.
- The fires that k-1+reg adds over k-2 pay +7.8% and +9.5%, so keep them.
- Wallets ≥5/10/20, growth from k-2 to k-1, bundle bands, tier, k, named ≥5, creator supply ≥2%, hour: none adds $ in both
  periods. The closest is tier 3%: read +$20.9 vs +$15.3 but fit $43.6 vs $82.6.

## Q4. Position (taped usual-view fires, guard ignored, h11)

| | first | second | third | last | first in E1+1 |
|---|---|---|---|---|---|
| fit (71) | +29.8% | +18.8% | +12.7% | -0.4% | -0.5% |
| read (32) | +24.1% | +15.4% | +10.9% | +4.1% | +3.6% |

Landing behind a big buy pays. Second place behind a first buy of 0.15 ETH or more: +24.5% (fit, 21) and +14.0% (read, 9);
behind 0.05-0.15 ETH: +17.4% (20) and +27.1% (7); behind less than 0.005 ETH: +2.7% (4). When E1 held 0.3 ETH or more in all,
second place pays +43% (32) and +30% (9). The E1 block is the signal, and only a loose guard lets the engine buy into it.

## Q5. Exit
Every rule's sell lands 2-4 blocks after its read, which is priced. Nothing beats the fixed E1+11 in both periods (103 fires):
- **Take-profit** at +10 to +50%: -1.1 to -4.1 points in both periods.
- **Stops** at -5 or -10%: -3.3 to -4.5 points in read.
- **Selling on the seat buyers' first sell**: 0 to -0.6 points.
- **Early reads** at E1+2, 3 or 5: -2 to -4 points in read.
- **A 20% trail**: +1.8 points fit, -1.9 read.
- **Other fixed holds**: 9 gives -2.8/-0.7, 13 gives -1.5/-0.9, 15 gives -5.4/-1.7.

Keep the hold at 9, which lands at 11.

## Q6. Size (second place h11; later buys folded by their ETH, the conservative fold)

| stake | $13 | $50 | $100 | $200 | $300 | $500 |
|---|---|---|---|---|---|---|
| fit, mean / $ per fire | +18.6% / 2.09 | +18.3% / 8.83 | +17.9% / 17.58 | +17.1% / 33.94 | +16.5% / 45.71 | +16.0% / 59.84 |
| read | +15.3% / 1.66 | +15.0% / 7.18 | +14.7% / 14.35 | +14.0% / 27.70 | +13.5% / 39.03 | +13.0% / 50.13 |

The return loses about 0.7 points per $100. The 3% cap binds from $218 on the most concentrated launches, and at $500 the median
effective stake is $323-332. Bundles over 1 ETH pay more in both periods (+36.0% vs +13.6% fit, +22.4% vs +12.9% read), but only
8 read fires, too few for a size rule. The crowd effect does not repeat (fleets ≥3: +26.3% vs +11.6% fit, +15.0% vs +15.6% read).
Scaling is not the constraint; the unproven edge is. Hold $13 until the SPRT decides.

## Q7. More fills
- **E2 is negative everywhere.** On the fires: -5.4% fit, -6.9% read at h11, and negative at every hold from 3 to 30.
  After a guard revert: -9.5% / -9.2%. On gate-refused launches whose E1 block showed a crowd (E1 ETH ≥ 0.3): -11.7% (26) fit
  against +5.3% (8) read, so it fails. As a second seat on every launch: -6%. The launch files' own E2 column agrees (-12.4%
  on 24, -4.2% on 151). The 6-point surcharge saving is smaller than the move already made by E2.
- **A second seat in E1** is a doubled stake, since the relay buys once per curve. The Q6 scaling covers it; it is not a new edge.
- **A smaller burst step** cannot be tested on disk. It only pays if it turns second place into first (+11 points fit, +9 read),
  which is a question for a landing test.
- **Tier-1% launches and bundles under 0.3 ETH** are not on disk.

## Not proposed
Every other variant above failed its out-of-sample read or rests on fewer than about 10 fires.

Scripts and outputs are in this folder: `build_table.py`, `sim.py`, `price_tapes.py`, `q1_guard`, `q1b_position`,
`q1c_late`, `q2_filters`, `q3_gate`, `q5_exit`, `q6_size`, `q7_e2`, `q8_slip` (`.py` and `.txt`). One side effect to note:
importing `sniper_engine` (engine 6.7), needed for the engine's own fleet count, opens warm-connection probes to the sequencer and
the RPC at import. That happened twice, fetched no data, and every number here comes from disk.
