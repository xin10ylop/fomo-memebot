#!/bin/bash
# The chain-side scoring of a fixed span, FROM to TO (score_window.sh scores FROM to now). Used to split a long reading into
# pieces that each finish in minutes (runbook 5av): a restarted cloud machine then loses one piece, not the whole scan.
#     bash src/analysis/score_span.sh NAME "YYYY-MM-DD HH:MM" "YYYY-MM-DD HH:MM"
set -e; export REPLAY_ATTACK_MIN=3 REPLAY_NAMED_MAX=0
N=$1; FROM=$2; TO=$3; D=data/derived/live_vs_table; E=data/derived/e1_sep24
[ -n "$N" ] && [ -n "$FROM" ] && [ -n "$TO" ] || { echo "usage: score_span.sh NAME FROM TO"; exit 1; }
set -- $(python3 -c "import time,calendar; f=calendar.timegm(time.strptime('$FROM','%Y-%m-%d %H:%M')); t=calendar.timegm(time.strptime('$TO','%Y-%m-%d %H:%M')); print(round((t-f)/3600+0.02,2), max(0.0, round((time.time()-t)/3600,2)))")
echo "== $N: $FROM -> $TO UTC ($1 h), block reads on $([ -n "$ALCHEMY_READ_URL" ] && echo "the second endpoint (5av)" || echo "the public node")"
python3 src/analysis/e1_multi.py $1 $2 $E/e1m_$N.json 0.02 0.04 2>&1 | tail -1
python3 src/analysis/add_creators.py $E/e1m_$N.json $D/launches_$N.json
[ "$(python3 -c "import json;print(len(json.load(open('$D/launches_$N.json'))))")" = "0" ] && { echo "== no qualifying launch in the span"; exit 0; }
python3 src/analysis/crowd_raw.py $D/launches_$N.json $D/crowd_raw_$N.json 2>&1 | tail -1 && gzip -kf $D/crowd_raw_$N.json
HOLD_OUT=$D/hold_grid_week_$N.json python3 src/analysis/hold_grid.py $D/launches_$N.json 2>&1 | tail -1
HOLD=11 python3 src/analysis/predict_window.py $D/crowd_raw_$N.json.gz $D/hold_grid_week_$N.json $D/launches_$N.json > $D/prediction_$N.txt; cat $D/prediction_$N.txt
for v in "--view k-2" "--view k-1 --reg" "--view k --reg"; do echo "-- $v"; python3 src/analysis/engine_replay.py $v --slip 0.20 --from "$FROM" --to "$TO" --hold 11 --list 2>&1 | grep "^week\|^dispositions\|^boosted\|FILL\|GUARD" | grep -v "^dispositions.*FILL [0-9]* *$" || true; done
echo "== done $N"
