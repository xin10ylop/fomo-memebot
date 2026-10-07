#!/bin/bash
# The chain-side prediction for a reading, with the CURRENT live settings in one place (runbook 5ah). Run before the box's reading:
#     bash src/analysis/score_window.sh NAME "YYYY-MM-DD HH:MM"        # from that UTC time to now
# Tiers 2-4% (creator tax 100-300 bps, the gate since Sep 30 10:40), the attackers gate at 3 fleets (since Sep 30 20:30, 5ak), hold 11,
# the burst guard at 0.20, the three engine views; fills attacked by a boosted helper (6.13, $50) are marked BOOST and tallied.
set -e; export REPLAY_ATTACK_MIN=3 REPLAY_NAMED_MAX=0 REPLAY_ATTACK_GROUP_PATH=data/derived/sprayers.json REPLAY_BUILD_MIN=0   # 6.21 (5bc): the live gate since Oct 7 (no build floor: the skeptics);   # NAMED_MAX is off live (5al): the replay must not refuse team bundles the engine fires on
 N=$1; FROM=$2; D=data/derived/live_vs_table; E=data/derived/e1_sep24
[ -n "$N" ] && [ -n "$FROM" ] || { echo "usage: score_window.sh NAME \"YYYY-MM-DD HH:MM\""; exit 1; }
H=$(python3 -c "import time,calendar; t0=calendar.timegm(time.strptime('$FROM','%Y-%m-%d %H:%M')); print(round((time.time()-t0)/3600+0.02,2))")
TO=$(date -u +'%Y-%m-%d %H:%M'); echo "== $N: $FROM -> $TO UTC ($H h), tiers 2-4%, block reads on $([ -n "$ALCHEMY_READ_URL" ] && echo "the second endpoint (5av)" || echo "the public node")"
python3 src/analysis/e1_multi.py $H 0 $E/e1m_$N.json 0.02 0.04 2>&1 | tail -1
python3 src/analysis/add_creators.py $E/e1m_$N.json $D/launches_$N.json
[ "$(python3 -c "import json;print(len(json.load(open('$D/launches_$N.json'))))")" = "0" ] && { echo "== no qualifying launch in the window: nothing to score"; exit 0; }
python3 src/analysis/crowd_raw.py $D/launches_$N.json $D/crowd_raw_$N.json 2>&1 | tail -1 && gzip -kf $D/crowd_raw_$N.json
HOLD_OUT=$D/hold_grid_week_$N.json python3 src/analysis/hold_grid.py $D/launches_$N.json 2>&1 | tail -1
HOLD=11 python3 src/analysis/predict_window.py $D/crowd_raw_$N.json.gz $D/hold_grid_week_$N.json $D/launches_$N.json > $D/prediction_$N.txt; cat $D/prediction_$N.txt
for v in "--view k-2" "--view k-1 --reg" "--view k --reg"; do echo "-- $v"; python3 src/analysis/engine_replay.py $v --slip 0.20 --from "$FROM" --to "$TO" --hold 11 --list 2>&1 | grep "^week\|^dispositions\|^boosted\|FILL\|GUARD" | grep -v "^dispositions.*FILL [0-9]* *$" ; done
python3 src/analysis/smart_helpers.py | sed -n 1p
echo "== the box's reading is in runbook 5ah (git pull first)"
