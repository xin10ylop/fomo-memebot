#!/bin/sh
# Searcher B: re-run every number. Read-only on the repo; outputs land next to this script (*.out, search_results*.json).
# tapes.py pulls ~143 launch tapes from the public RPC (~10-15 s each on a cold cache, cached in ./tapes/); everything else is offline.
set -e
export PYTHONDONTWRITEBYTECODE=1
B=/tmp/claude-0/-home-user-fomo-memebot/a7a59693-7c2d-5b6c-b7df-e43fdbe7d612/scratchpad/improve/B
cd /home/user/fomo-memebot
python3 $B/baseline.py   > $B/baseline.out
python3 $B/explore.py    > $B/explore.out
python3 $B/search.py --show 40 > $B/search.out
RAW=1 python3 $B/search.py --show 40 > $B/search_raw.out
python3 $B/dims.py       > $B/dims.out
python3 $B/scrutiny.py   > $B/scrutiny.out
python3 $B/robust.py     > $B/robust.out
python3 $B/extra.py      > $B/extra.out
python3 $B/winners01.py  > $B/winners01.out
python3 $B/tables.py     > $B/tables.out
python3 $B/tapes.py      > $B/tapes.log 2>&1
python3 $B/guard.py      > $B/guard.out
echo "done: outputs in $B/*.out"
