# Edge check, round 2 (Sep 27 2026): the strategy from its discovery to today, re-examined whole

You are an independent reviewer with the full history. Read-only on the code; write under
`data/derived/edge_check/<your letter>/` (letters C and D this round). Do not modify `src/`, `deploy/` or `docs/`; do
not commit. Public RPC `https://rpc.mainnet.chain.robinhood.com` only (no historical state; pace calls, 4 threads at
most, back off on 429). Round 1's reports (`A/REPORT.md`, `B/REPORT.md`) exist: read them, reuse their scripts and
tape caches if useful (`B/tapes/` may be absent; `A/tapes.json.gz` is committed), but check what you rely on.

## The story, in the order it happened (docs/REPORT.md, section 24)

1. **The old strategy, live Sep 17-20**: a first-block sniper (seat E1: the second after the creation second) with a
   bundle rule, 35-shot bursts through a relay, 15-block hold. 43 launches, 34 single fills reconciled to the decimal
   (`24.28`, `data/derived/live_vs_table/sep17_20_fills.txt`, `sep17_20_fills.json`). Net about −$47 by Sep 19.
2. **The discovery (`24.30`, `winners_anatomy.json`)**: the 12 winners (over +5%) against the 31 others differed in ONE
   thing: the crowd that arrived after the seat (5.2 buys behind us in the seat block vs 1.5; 6.7 buys from 5.5 wallets in
   the next 15 blocks vs 2.2 from 2.0; curve +32% at +60 blocks vs +2%; +32% vs +21% at +600). Named wallets, tier, bundle
   size did not separate them. "The edge is the crowd that arrives after the seat, not the seat." Fills with somebody
   ahead of us in the block: +17.7% first-in-block model, +7.4% real (12 fills, 67% win); nobody ahead: −3.9% (22).
3. **The rule built on it (`24.31`-`24.32`)**: fire only when a crowd is ALREADY visible before the tick: distinct
   fleets (relay targets + direct senders, named and creator excluded) shooting at the curve by block k-2 of the creation
   second, >= 2. Out of sample on Sep 20-21 it held. The hold was moved to 300 blocks from the tables (the fills' own
   +600-block column and the position-by-hold model), not from executed trades.
4. **Engine = tables (`24.33`)**: three mismatches found and closed (unit wallets vs fleets, the view k-1 vs k-2, a safety
   switch), a seam test that replays 563 launches through the engine's counter, five days of predictions matching the
   engine launch by launch. The fit: 4 windows Sep 18-23, 563 launches, 73 fires, +26.3% at $13, $56/day
   (`stake_table.txt`, `reach_table.txt`).
5. **Improvement search (`24.34`)**: three independent searches (views, units, holds, stops, features, null tests) on the
   fit + 5 paper windows: nothing proven; keep the rule. Null test: random features pass 3.3%, real 2.7%.
6. **Live Sep 26-27 (`24.33` addenda, runbook 5q-5r)**: two bursts, one fill (−2.6%, model −2.6%), −$0.68. Plumbing
   faults found and fixed (relay float, RPC quota, log rotation), none of them the edge.
7. **The edge check (`24.35`, `A/`, `B/`)**: since Sep 24 the rule's fires (18, the engine's own population) average
   +3.5%, 39% win, the last five all lost. Both reviewers: real, not an artefact (p 0.01-0.05; same code, same chain, same
   fees). The entry still works at 15 blocks (+12.8% vs the fit's +16.2%); the selection at 300 blocks is gone (lift over
   refused +27 -> −1 points); outsiders' buying after the seat fell to a sixth; bundles dump during the hold (28% of fires
   vs 10%); one operator's template is a third of recent fires at −13.6%; the launch supply halved (5.9 -> 2.7 qualifying
   launches an hour); the fit's best k-2 fleet (22 fires +52%) has 3 recent fires at −5%; our own visibility is not the
   cause (our bursts were on the chain from Sep 19 inside the fit).

## The question

With the whole story in front of you: is the strategy as run today the right reading of the discovery, and what
should it be now? In particular:

1. **The discovery vs the rule.** The discovery was about the crowd AFTER the seat on 15-block holds of real fills; the
   rule fires on the crowd BEFORE the tick and holds 300 blocks. Re-derive from `winners_anatomy.json` and
   `sep17_20_fills.json` what the real winners had, and test on the fit windows AND the recent windows which reading of
   the discovery survives: the crowd-before-the-tick gate (the rule), the crowd-after-the-seat (not tradable before the
   fact, but is a proxy?), the hold (15 / 60 / 150 / 300), the combination. Same yardstick everywhere
   (`stake_scale.model_eff`, second place in E1, $13, gas $0.33, the surcharge by second, the 3% cap).
2. **What the recent windows say about each reading.** The fit favoured 300 blocks (+26% vs +16% at 15); the recent
   windows favour 15 (+12.8% vs +3.5%). Is the 15-block version of the rule an edge that holds in BOTH periods, at what
   $/day at $13 with the recent launch supply (2.7 qualifying launches an hour, fires per hour 0.32), and would it have
   survived round 1's dumps and thinner follow-on demand? Show the day-by-day series Sep 18-27 for both holds.
3. **Is there a version of the discovery that does not depend on a stable population of fleets?** The fit's best fleet
   vanished; half of recent fleets are new. Test rules that do not name fleets: wallet counts, ETH shot, direct vs relay,
   the bundle's own behaviour (its early sells), the creator's history (templates, serial launchers: the operator with 15
   launches). No fitting on the recent windows alone: anything proposed must be fitted on the fit windows and read on
   the recent ones, or the reverse, and the null-test discipline of 24.34 applies (permute the feature, count passes).
4. **The honest expectation** for the next week under each candidate (keep / 15-block / stop), with the launch supply as
   it is now, and the stopping rule that would settle it fastest on chain-scored fires (both round-1 reviewers gave
   sequential tests: use them).
5. **Anything the whole story shows that the pieces did not.** You have every artefact; the earlier reviewers had the
   last four days only.

## Deliverable

`data/derived/edge_check/<letter>/REPORT.md`, verdict first: one of KEEP THE RULE / CHANGE (to what, with the numbers
on both periods) / STOP (until what), then the evidence with the command behind every number, scripts in your folder.
No recommendation without a number on both the fit and the recent windows. Plain prose. Budget: about 2 hours.

## Files

- `docs/REPORT.md` 24.25-24.35 (the story), `docs/SNIPER_RUNBOOK.md` 5n-5r (what runs)
- `data/derived/live_vs_table/`: sep17_20_fills.{txt,json}, winners_anatomy.json, pnl_timeline.txt, crowd_raw_*.json.gz
  (fit: sep1819, sep2021, sep2223, sep23day; recent: sep24paper, sep25night, sep25am, sep25pm, sep25eve, sep25eve2,
  sep26night, sep26am, sep26pm, sep26restart, sep27night), launches_*.json, hold_grid_*.json, prediction_*.txt,
  stake_table.txt, reach_table.txt, crowd_rules.txt, crowd_signal_*.json, position_hold_*.txt
- `data/derived/e1_sep24/e1m_*.json` (per-launch chain scoring), `data/derived/improve_search/` (24.34: BRIEF.md, A/, B/, C/)
- `data/derived/edge_check/`: BRIEF.md, A/, B/ (round 1)
- `src/analysis/`: crowd_rules.py, crowd_raw.py, predict_window.py, hold_grid.py, stake_scale.py, stake_table.py,
  reach_table.py, live_vs_table.py, winners_anatomy.py, pnl_timeline.py, crowd_signal.py, e1_multi.py, add_creators.py,
  engine_vs_chain.py; `src/strategy/sniper_engine.py` (6.5)
