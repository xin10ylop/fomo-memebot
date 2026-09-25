# The question (identical for all three searchers)

Is there any change to the rule the engine runs that is MORE profitable, robustly, given everything we have measured?
The honest answer may be "no, keep it as it is". Do not invent features; test candidates on the data below and report only
what survives the protocol. Read-only on the repo: write your scripts into your own scratch directory, never edit repo files.

Repo: /home/user/fomo-memebot. Read docs/REPORT.md section 24.33 (and its addenda 1-9, at the end of the file) first: it
holds the rule, the engine's measured view, the pricing tables, the audits and five days of predictions against readings.

## The rule the engine runs (engine 6.5, dry run, on the box)
- Population: the tables' qualifying launches (selector f85f8e41, native quote, >= 3 named wallets, tier 100-200 bps, first
  buy at b0, >= 0.3 ETH exempt bundle over the creation second, both seat seconds within 24 blocks). The engine also skips
  creators holding < 1% of supply, a creator's second launch of the day, launches it cannot aim at (creation in the last
  1-2 blocks of its second), and one position at a time (a 300-block hold, ~30 s).
- Gate: fire only when >= 2 FLEETS (distinct relay targets + direct senders, excluding named wallets, the creator, our own
  addresses and the token's approvals) are visible on the feed firing at the curve before the tick. The engine's measured
  view when the gate closes is block k-2 of the creation second FULLY indexed and block k-1 PARTLY (k = the creation second's
  last block offset; the creation block is offset 0). Treat "count by block k-2 >= threshold" as the sure/executable view;
  "by block k-1" as a borderline the engine sometimes catches. Views later than k-1 are NOT executable (the feed lag is
  ~200 ms; a later gate would fill behind the crowd).
- Fill: second place in the seat block (behind one buy), hold 300 blocks, sell in one transaction. Stake $13, gas $0.33 a
  burst (the burst's minOut guard, 25%, refuses ~8% of fills at the build's quote: score those as -gas).
- Baseline to beat (exact k-2 view, fleets >= 2, behind1 h300): the four backtest windows pooled 73 fires, +26.7% mean,
  67% wins, $3.14 a burst, ~$57/day; the five paper windows (Sep 24-25, out of sample, the rule was fixed before them)
  ~12 fires, ~+15% mean. The engine's actual 33.5 h: 13 fires, +$24 at $13; 54 refused at ~0% mean.

## Data (all under data/derived/live_vs_table/)
- Fleets and everything aimed at each curve, raw, per creation-second block: crowd_raw_<window>.json.gz, records
  {cv, b0, k, T0, token, creator, named[], blocks[[ {fr, to, ix, direct, named_fr, named_data, to_token, sel} ]]}
  (blocks[0..k] = the creation second, blocks[k+1] = the seat block). Count fleets EXACTLY as src/analysis/crowd_rules.py
  cums() does (skip rows with to/fr in US, to_token; direct rows: fleets.add(fr) unless named_fr; relay rows: fleets.add(to)
  unless named_data; wallets similarly). Use crowd_rules.py's cums()/view()/at() by exec-ing the file's text before
  "rules = [" (see src/analysis/predict_window.py for the pattern) or copy the logic verbatim.
- Returns per launch: hold_grid_<window>.json, keys first_15_h{15,30,60,150,300,600}, first_15_tp50_h600,
  first_15_stop20_h600, first_15_tp50_stop20_h600, and the same for behind1_15_*, first_100_*, behind1_100_* ($15 and $100
  stakes; "behind1" = second place). These are the only exits available without re-pulling tapes; the model is
  src/analysis/hold_grid.py model_path (importable; live_vs_table.launch pulls a tape from the public RPC if you need
  other positions/holds: ~1 s a launch, keep it small).
- Pre-tick features per launch (usable by the engine before the shot): launches_<window>.json: bundle_eth, named (count),
  tier, hour (UTC), same_second_blocks (= k), creator; plus anything computable from crowd_raw blocks[0..k] (fleets per
  block, wallets, direct vs relay, the block where the count first reached n, shots per fleet). NOT usable: e1_block_*,
  e2_block_*, anything after the tick.
- Windows. FIT set (the four backtest windows): sep1819 (raw crowd_raw_sep1819, returns hold_grid.json, launches
  launches_141_creators.json), sep2021 (crowd_raw_sep2021, hold_grid_oos_sep2021.json, launches_oos_sep2021.json),
  sep2223 (crowd_raw_sep2223, hold_grid.json, launches_175_sep2223.json), sep23day (crowd_raw_sep23day,
  hold_grid_today_sep23.json, launches_today_sep23.json). Window hours: 23.1, 34.8, 29.3, 8.8.
  VALIDATION set (truly out of sample: the rule and settings were fixed on Sep 24 before these launches): sep24paper (9 h),
  sep25night (9 h), sep25am (6.6 h), sep25pm (6.6 h), sep25eve2 (2.75 h) with the matching hold_grid_/launches_ files
  (crowd_raw_sep25eve is a subset of eve2 plus one launch, 0xf45fa520, the builder dropped from eve2: include it).
  Join by cv; skip launches without a behind1_15_h300 value.

## Candidate dimensions (test these; add others only if they are observable before the shot)
1. The threshold: fleets >= 1, 2, 3, 4 at the k-2 view; wallets instead of fleets; fleets at k-2 AND something at k-3.
2. The hold: 15, 30, 60, 150, 300, 600 blocks; the tp50 / stop20 / tp50+stop20 variants at 600 (behind1_15_*).
3. Any pre-tick feature that separates the 0-1 fleet winners (the refused set held +191%, +134%, +120%, +110%, +85%, +81%,
   +80% launches on Sep 24-25): bundle_eth, named count, tier, hour, k, the fleets' arrival block, direct vs relay shots,
   wallets per fleet. Test as an additional OR-branch ("fire also when ...") and as an AND-filter.
4. The stake: $15 vs $100 columns (return per fire vs dollars; the 3% cap).
5. Hours of the day; the creator-supply filter (approximate with what launches_ files carry, or note it cannot be tested).

## Protocol (strict; this is what makes the answer trustworthy)
- Executable at the engine's view only (k-2 exact; report k-1 as borderline, never as the headline).
- A candidate PASSES only if: (a) it beats the baseline's pooled $/day at $13 after $0.33 gas on the FIT set, (b) it is
  positive on EACH of the four fit windows, (c) it beats or matches the baseline on the VALIDATION set pooled ($ total and
  mean/fire), (d) its win rate is not worse than the baseline's by more than 10 points and its dead fraction (< -40%) not
  higher by more than 5 points, (e) its fire count on the fit set is >= 30 (otherwise the mean is noise).
- You will test dozens of variants: say how many you tried, and treat a pass that barely clears (c) as "not proven".
- Report per window: fires, fires/day, mean, median, win %, dead %, $/burst, $/day; and the pooled numbers for fit and
  validation separately. Show the baseline in the same table.
- Save your scripts in your scratch directory and print the exact commands to re-run them; the other two searchers will
  re-run each other's scripts as the double check.

## Output
1. A ranked list of candidates that pass, with their tables, or the sentence "nothing passes the protocol; keep the rule
   as it is" followed by the three closest misses and why each fails.
2. A short list of what you could not test with this data (and what data it would need).
3. The commands to reproduce every number.
Be concrete, cite files and line numbers, no strategy opinions beyond the numbers.
