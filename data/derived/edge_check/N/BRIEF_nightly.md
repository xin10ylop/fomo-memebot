# Nightly review brief (from Sep 28, 2026; reused every night with the day's facts appended)

You are one of two independent reviewers of today's live trading of the E1 sniper. The owner asks one question every night:
after today's trades, is there any improvement left to make, with a tested number, that survives out of sample? Work only from
the files named here (no network: every number is on disk). Write your report to the folder named in your prompt, with the
scripts you ran beside it. Do not modify any file outside that folder. Do not commit. Under 1,200 words. Be adversarial toward
the current settings and toward your own ideas: the owner has been burned by backtests that did not survive live trading, so
fewer, tested, out-of-sample-checked proposals beat many ideas. If the honest answer is "nothing tonight", say so and why.

## Standing facts (do not re-derive)
- The strategy, the data on disk, the pricing conventions and the earlier findings: `data/derived/edge_check/K/BRIEF.md` (read it
  first), report sections 24.33-24.42 in `docs/REPORT.md` (grep "### 24.4"), runbook sections 5q-5y in `docs/SNIPER_RUNBOOK.md`.
- Already tested and NOT adopted on Sep 28 by four independent analyses (K0-K3, `data/derived/edge_check/K*/PROPOSALS.md`): every
  exit rule against the fixed 11-block exit, E2 and second seats, gate thresholds other than 2 fleets, nine extra gate signals,
  the pre-gate filters (the cap earns its keep; the others too small), size (linear to $200, no raise before the sequential test).
  Do not re-propose these unless today's data changes the picture, and say what changed.
- Adopted on Sep 28 and live since 12:27 UTC: engine 6.7 (sender cache, no lock-spin in the burst, pooled warm RPC connections,
  feed_stats), BURST_SLIP 0.20 (was 0.07), BURST_STEP_MS 2 and BURST_LEAD_MS 46 (were 3 and 80), direct coincurve signing,
  the c7a.large box (two real cores, unpinned). The engine's decision chain on the chain: `src/analysis/engine_replay.py`
  (--view k-2|k-1|k, --reg, --slip, --dump, --list, --from/--to). Today's windows: pieces `sep28am`, `sep28pm`, `sep28eve`,
  `sep28night2` (launches_*, crowd_raw_*.json.gz, hold_grid_week_*.json, prediction_*.txt under data/derived/live_vs_table/).
- The engine's live gate view sits between block k-2 and block k (24.41): floor / usual / ceiling. The replay lands every burst
  at second place; the live landing index is on the reading's `landed` line (the day's facts below).

## Questions for tonight (answer each; add your own)
1. Reconcile today's live bursts with the model and with today's changes: did the tighter step land us earlier (before today 2 of
   5 fills landed first; today 4 of 5)? What is the evidence, and how many fills would settle it?
2. The guard-admitted class (fills 7-20% under the sizing): today's tally, and the running rule (back to 0.15 / 0.07 if...).
3. The two new skip reasons today: "bundle 0 < 3" on a launch the chain shows with a 0.71 ETH exempt bundle (12:52
   `0x98f4e88b`), and "nonce/gas not fresh (RPC)" (19:44:59 `0x057d1ffe`). Read the engine for the cause (fold_buy, named_txs,
   the bookkeeping poll, CHAIN_POLL_S, the 30 s freshness gate around line 1942) and say whether each is fixable and worth it.
4. The winners the rule cannot take: crowds that appear only in the tick's own block (17:39 `0x5ca0bb0d` +75%) or not at all
   (20:24 +75%, 18:42 +59%). Is there any signal before the tick that predicts a block-k crowd, tested on the whole week at the
   k view with fit/read halves? If not, say so.
5. Anything else today's data suggests, with out-of-sample numbers on the week.
6. Your verdict: the single change (if any) to make tomorrow, its expected $ a day at $13 on today's supply, its count, and how
   to verify it live; or "nothing tonight".

## Today's facts, Sep 28 (from the readings, reconciled launch by launch; the engine's log is on the box, not on disk)
- 12:27 the new settings went live. From then to 21:00: seven bursts, five fills, P&L +$0.03 -> +$11.76 since the switch.
- Bursts: 14:55 `0x95129ff1` (the sequencer held the burst 3.9 s behind 429 rival shots, no fill); 15:30 `0xffb0d66a` (landed
  FIRST, index 1, ten buys behind worth 1.3 ETH, two of them the fixed-size first buyers 0.149 and 0.585 ETH; sold at E1+12;
  +98.4% real, +$12.36, against +73.7% modelled because our sell landed before a 27.5M-token dump in the exit block);
  15:33 `0xbb14a5da` (landed last behind four fleets, 23% under the sizing, reverted by the 20% guard); 15:36 `0x0c5816d3`
  (index 4, two buys ahead worth 0.159 ETH, the first guard-admitted fill: -7.1% real = model); 16:33 `0x65f237db` (index 2,
  one 0.010 ETH buy ahead, +2.9% = model); 18:52 `0xe7e91780` (index 1, +1.3% = model); 19:15 `0x22d509a8` (index 1, 0.0% = model).
- Signing 3.8-3.9 ms for 35 shots on every burst (23 ms before), all 35 signed directly; the latest shot of any burst 0.13 ms
  behind schedule except one 2.49 ms on a burst that never opened (20:20). feed_stats on the new box: 599 frames a minute,
  median 0.2 ms, p90 0.7 ms, max 3 ms, busy 0.3%.
- Skips: 12:52 `0x98f4e88b` "bundle 0 < 3" (chain: 0.711 ETH exempt bundle, 22 named, tier 2%, -1.9% modelled behind one);
  19:44:59 `0x057d1ffe` "nonce/gas not fresh (RPC)" (the replay's verdict: guard revert, nothing lost); aim skips at 13:26, 14:20,
  16:23, 19:51 on zero-fleet launches; creator-supply skips 10:52, 20:40; the tier gate refused 37 tokens outside the population.
- Gate refusals all as predicted (12 in the afternoon, 14 in the evening); 0 holes both ways; 1 engine-only launch (14:16, a
  0.338 ETH bundle by the engine's count, absent from the population, refused at the gate anyway).
- Ten fills since the switch: realized mean +10.5%, the model at their landed exits +8.1%, +$13.18 net on the fills; landing
  index of the ten: [second, second, first(E1+2), second, first, first, fourth, second, first, first]. The chain-scored
  sequential test on sixteen fires: mean +10.9%, LLR +0.03 (bounds +-2.94), undecided.
