"""The seam test (report 24.33): the number the engine gates on is the number the backtest gated on. Every transaction aimed at
the 563 launches of the four windows (data/derived/live_vs_table/crowd_raw_*.json.gz) is replayed through the engine's own
note_attack / attack_fleets / attack_wallets, block by block, and compared with crowd_rules.cums(), the backtest's count.
Our own wallet's shots through the retired Sep 18-19 relays are excluded on both sides (6.4: the engine skips its own sender).

    python3 tests/test_seam_replay.py
"""
import os, sys, json, gzip
os.environ.setdefault("LOG_PATH", "/tmp/test_seam_replay.jsonl")
for k, v in (("SEND_MODULE", ""), ("PRIVATE_KEY", ""), ("BURST_N", "35"), ("HOLD_BLOCKS", "300"), ("ATTACK_MIN", "2"),
             ("WALLET", "0xe0686dc72b04c12ceefeea75e286e4ef7c056f01"), ("RELAY", "0xe8e98c3514d5bd83fdd01360896f2382b861a720")):
    os.environ[k] = v
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src", "strategy")); import sniper_engine as E
sys.argv = ["x", "0.76", "0.71"]; os.chdir(ROOT)
exec(open("src/analysis/crowd_rules.py").read().split("rules = [")[0])          # cums(), US, data
D = "data/derived/live_vs_table/"; diffs = []; n = 0; nblocks = 0
for rf in ("crowd_raw_sep1819.json", "crowd_raw_sep2021.json", "crowd_raw_sep2223.json", "crowd_raw_sep23day.json"):
    for r in json.load(gzip.open(D + rf + ".gz", "rt")):
        cv = r["cv"]; named = set(r["named"]); creator = r["creator"]
        E.state["watch"].clear(); w = E.watch_curve(cv, 1e7, 1_700_000_000, named, creator, blk0=r["b0"], tax_bps=200)
        w["tb"] = bytes.fromhex(r["token"][2:]) if r["token"] else None
        cw, cf = cums(r); ef, ew = [], []
        for off, rows in enumerate(r["blocks"][: r["k"] + 1]):
            for t in rows:
                E.sender_of = (lambda fr: (lambda tx: fr))(t["fr"])
                data = bytes.fromhex(t["sel"][2:]) if t["direct"] else (bytes.fromhex(t["sel"][2:]) + b"\0" * 12 + bytes.fromhex(cv[2:]) +
                       b"".join(b"\0" * 12 + bytes.fromhex(a[2:]) for a in named if t["named_data"]))
                E.note_attack(w, t["to"], b"", data, cv)
            ef.append(E.attack_fleets(w)); ew.append(E.attack_wallets(w)); nblocks += 1
        n += 1
        if ef != cf or ew != cw: diffs.append((cv[:10], ef, cf, ew, cw))
for d in diffs[:8]: print("DIFF", d)
print(f"{n} launches, {nblocks} creation-second blocks replayed through note_attack: {len(diffs)} differ from the backtest's count")
assert n == 563 and not diffs, "the engine's count and the backtest's count differ"
print("ok   the engine gates on the number the backtest priced (both units, every block, 563 launches)")
