# Edge check, Sep 27 2026: what happened to the rule's edge since Sep 24?

You are an independent reviewer. Work only in this repository (read-only on the code; write your findings under
`data/derived/edge_check/<your letter>/`). Do not modify the engine or any script under `src/`; copy what you need into
your folder. The public RPC `https://rpc.mainnet.chain.robinhood.com` answers JSON-RPC (no historical state, logs and
blocks fine; batches of more than ~20 blocks and bursts get 429: pace your calls, 4 threads at most). No keys exist
here and none are needed. Do not commit; the owner commits your folder.

## The rule and its numbers

The engine fires a 35-shot burst at the second after a Pons V2 launch's creation second ("seat E1") when, by block
k-2 of the creation second (k = blocks after the creation block b0 in that second), at least 2 FLEETS (distinct relay
targets + direct senders, named wallets and the creator excluded) have shot at the curve; it holds 300 blocks and
sells. Population: tier 2-3% tokens (tax 100-200 bps), bundle >= 0.3 ETH of named buys, the engine's own pre-gate
filters aside (creator buy >= 1% of supply, the aim, one hold at a time).

- Fit: four windows Sep 18-23 (96 h), 563 launches, 73 fires, mean +26.3% at $13 after gas, 67% win, 8% dead (< -40%),
  $56/day at $13 (`data/derived/live_vs_table/stake_table.txt`, `reach_table.txt`).
- Since: Sep 24-27 (60 h), 18 fires, mean +3.5%, 39% win, 11% dead, about $1/day; the five fires of Sep 26-27 all lost
  (-41, -3, -11, -51, -38%). Per fire list: `data/derived/live_vs_table/reach_table.txt`.
- Live: Sep 26-27, two bursts, one fill (-2.6%, the model said -2.6% for that seat and hold), P&L -$0.68.

## The question

Is the deterioration real, a measurement artefact, or undetermined, and what is being missed? Answer with evidence
computed from the data here and the chain, not with opinion. Things to test (add your own):

1. Same yardstick? The fit fires and the recent fires must be scored by the same code on the same definitions.
   `src/analysis/reach_table.py` prices both sets with `live_vs_table.model_eff`-style pricing (`stake_scale.py`);
   `src/analysis/hold_grid.py` + `predict_window.py` produce the per-window predictions (`prediction_*.txt`). Check
   the population (`crowd_rules.py`: `cums`, `at`, `view`), the view (k-2 exact), the fee model (tier + the second's
   surcharge 6.18%, the sell's tier fee), the 3% cap, the hold (300 blocks), the ETH price, the tape length (a 300-block
   hold sells past b0+120: fixed Sep 26 in live_vs_table; check every other scorer), gas ($0.33 a burst). `git log`
   shows every change since Sep 23.
2. Statistics. 73 fires at +26% vs 18 at +3.5%: bootstrap and permutation over the fit windows' fires (per-fire returns
   have a standard deviation near 45 points); how often does a random 60-hour stretch of the fit read <= +3.5%? Day by
   day series of the rule's fires from Sep 18 to Sep 27 (the crowd files: `crowd_raw_*.json.gz`, one per window, each
   record has cv, b0, k, T0, creator, named, blocks[i] = the shots at block b0+i with fr/to/direct/named flags).
3. What changed on the chain for the launches the rule fires on: crowd size at k-2 and after, rival shot counts,
   WHICH fleets (relay targets) are shooting (the same ones as in the fit windows? new ones?), who sells in the 300
   blocks after the seat and how early, follow-on demand (ETH bought by outsiders after the seat second), bundle sizes,
   tier mix, hour-of-day mix, serial launchers (creator templates), the dead rate. Fit windows vs Sep 24-27.
4. Alternatives the rule does not see: the 300-block hold vs 15/60 blocks on the recent fires (`hold_grid.py` grids);
   a stop; the tick's-shot view vs k-2; wallets vs fleets. (`docs/REPORT.md` 24.34 records an improvement search on the
   fit + paper windows that found nothing; do not repeat it, but say if the recent windows change its answer.)
5. The world: any change in the Pons V2 contracts or fee schedule (the surcharge by second: 98% in the creation
   second, 6.18% in second +1, 0.19% in second +2), in the sequencer's block cadence (10 blocks a second), in the fleets'
   behaviour after our own live bursts became visible on Sep 26 (35 shots from 35 shooter addresses through relay
   0xe8e98c3514d5bd83fdd01360896f2382b861a720).

## Deliverable

`data/derived/edge_check/<letter>/REPORT.md`: the verdict (artefact / real / undetermined), the evidence for it with
the commands that reproduce every number, what is being missed if anything, and what would settle the question and
by when. Keep scripts you wrote in your folder. No recommendations without a number behind them. Plain prose, no
hedging language; where the data cannot decide, say so and say what data would.

## Files

- `src/analysis/`: crowd_rules.py, crowd_raw.py, predict_window.py, hold_grid.py, stake_scale.py, stake_table.py,
  reach_table.py, live_vs_table.py, e1_multi.py, add_creators.py, paper_day.py, engine_vs_chain.py, intake_readout.py
- `src/strategy/sniper_engine.py` (6.5): the engine; `deploy/send_step.py`: the live send step
- `data/derived/live_vs_table/`: crowd_raw_{sep1819,sep2021,sep2223,sep23day}.json.gz (fit), crowd_raw_{sep24paper,
  sep25night,sep25am,sep25pm,sep25eve,sep25eve2,sep26night,sep26am,sep26pm,sep26restart,sep27night}.json.gz (since),
  launches_*.json, hold_grid_*.json, prediction_*.txt, stake_table.txt, reach_table.txt, crowd_rules.txt
- `data/derived/e1_sep24/e1m_*.json`: the per-launch chain scoring (e1_multi) for the recent windows
- `docs/REPORT.md` 24.33-24.34 and the addenda after them; `docs/SNIPER_RUNBOOK.md` 5n-5r
