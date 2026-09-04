#!/bin/bash
cd /tmp/claude-0/-home-user-fomo-memebot/a7a59693-7c2d-5b6c-b7df-e43fdbe7d612/scratchpad
python3 pull_gt.py >> pull_gt.log 2>&1
python3 pull_gt_1m.py >> pull_gt_1m.log 2>&1
