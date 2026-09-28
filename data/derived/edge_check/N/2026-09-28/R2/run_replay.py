"""run_replay.py: runs src/analysis/engine_replay.py unchanged except that the engine's log goes to the scratchpad (not /tmp),
so nothing outside the R2 folder is written. Usage: python3 run_replay.py <engine_replay args>"""
import sys, os
SCR = os.environ.get("R2_SCRATCH", "/tmp/claude-0/-home-user-fomo-memebot/a7a59693-7c2d-5b6c-b7df-e43fdbe7d612/scratchpad")
ROOT = "/home/user/fomo-memebot"; SRC = os.path.join(ROOT, "src/analysis/engine_replay.py")
code = open(SRC).read().replace('"LOG_PATH": "/tmp/engine_replay.jsonl"', '"LOG_PATH": "%s/engine_replay.jsonl"' % SCR)
assert SCR in code
sys.argv = [SRC] + sys.argv[1:]
exec(compile(code, SRC, "exec"), {"__file__": SRC, "__name__": "__main__"})
