#!/bin/sh
# R1: the engine's chain through today at the live guard, three views, dumped for the q*.py scripts (run from the repo root)
R1=data/derived/edge_check/N/2026-09-28/R1
python3 src/analysis/engine_replay.py --from "2026-09-21 09:40" --to "2026-09-28 21:00" --view k-2      --slip 0.20 --dump $R1/rows_k2.json    > $R1/replay_k2.txt
python3 src/analysis/engine_replay.py --from "2026-09-21 09:40" --to "2026-09-28 21:00" --view k-1 --reg --slip 0.20 --dump $R1/rows_k1reg.json > $R1/replay_k1reg.txt
python3 src/analysis/engine_replay.py --from "2026-09-21 09:40" --to "2026-09-28 21:00" --view k --reg   --slip 0.20 --dump $R1/rows_kreg.json  > $R1/replay_kreg.txt
# then: python3 q0_today.py; q1_landing.py; q2_admitted.py; q3_bundle.py (imports engine67.py = git show 34265b9:src/strategy/sniper_engine.py); q3_nonce.py; q4_tickcrowd.py; q5_*.py
