**Verdict (provisional, being written): see the sections below; the final line replaces this one.**

# Edge check round 2, reviewer D (Sep 27 2026)

Work in progress. Every number has its command beside it; all scripts are in `data/derived/edge_check/D/` and run from the
repository root. Yardstick everywhere: `stake_scale.model_eff`, $13 at ETH $2,570, second place in the seat block E1, gas $0.33
a fire, the surcharge by second, the 3% cap. Fit = the four windows Sep 18-23 (563 launches, 73 fires, 96 h); recent = the 11
windows Sep 24-27 (160 launches, 18 fires, 60 h).

## 0. What I rely on, checked
`python3 data/derived/edge_check/D/check_tapes.py` -> `check_tapes.txt`: B's cached tapes equal A's independent pull on all 91
fires (0 differing event lists, max price difference 0.0000 at 15 and 300 blocks); the yardstick gives fit 73 fires +26.3%
$56.4/day, recent 18 fires +3.5% $0.9/day (reach_table.txt). The 85 fit launches round 1 had no tape for were pulled here
(`pull_tapes.py`, 85 ok), so every one of the 723 launches is priced. `features.py` prices every launch after every block
0..600 in one pass and equals `model_eff` to 0.000000 at 15 and 300 blocks (`features.txt`).
