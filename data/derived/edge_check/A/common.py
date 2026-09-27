"""common.py (edge_check/A): loaders shared by the reviewer-A scripts. Independent fleet counter (written from the brief's
definition, not from crowd_rules.cums) plus the window lists. Run everything from the repo root."""
import json, gzip, os, time
D = "data/derived/live_vs_table/"; A = "data/derived/edge_check/A/"
FIT = ["sep1819", "sep2021", "sep2223", "sep23day"]
REC = ["sep24paper", "sep25night", "sep25am", "sep25pm", "sep25eve", "sep25eve2", "sep26night", "sep26am", "sep26pm", "sep26restart", "sep27night"]
HG = {"sep1819": "hold_grid.json", "sep2021": "hold_grid_oos_sep2021.json", "sep2223": "hold_grid.json", "sep23day": "hold_grid_today_sep23.json",
      "sep24paper": "hold_grid_sep24paper.json"}
for w in REC[1:]: HG[w] = f"hold_grid_{w}.json"
WALLET = "0xe0686dc72b04c12ceefeea75e286e4ef7c056f01"; RELAY = "0xe8e98c3514d5bd83fdd01360896f2382b861a720"; US = {WALLET, RELAY}
def load_raw(w):
    return json.load(gzip.open(D + f"crowd_raw_{w}.json.gz", "rt"))
def fleets_by_block(r, unit="fleets"):
    """cumulative distinct shooters by block offset 0..k (independent re-implementation): a relay shot counts its relay (to),
    a direct shot its sender; our own wallet/relay, approvals on the token, named senders (incl. the creator) and calls that
    carry a named address in the calldata (the bundle helper) are not shooters. unit='wallets' counts senders instead."""
    seen = set(); out = []
    for rows in r["blocks"][: r["k"] + 1]:
        for t in rows:
            if t["to_token"] or t["to"] in US or t["fr"] in US: continue
            if t["direct"]:
                if t["named_fr"]: continue
                seen.add(t["fr"])
            else:
                if t["named_data"]: continue
                if unit == "fleets": seen.add(t["to"])
                elif not t["named_fr"]: seen.add(t["fr"])
        out.append(len(seen))
    return out
def at(c, j): return c[j] if 0 <= j < len(c) else 0
def all_launches(windows):
    """every launch of the windows, deduplicated by curve (sep25eve2 repeats 5 of sep25eve; sep26restart repeats 1 of sep26pm)"""
    seen = {}; out = []
    for w in windows:
        for r in load_raw(w):
            if r["cv"] in seen: continue
            seen[r["cv"]] = w; r["win"] = w; out.append(r)
    return out
def is_fire(r): return at(fleets_by_block(r), r["k"] - 2) >= 2
def hms(t): return time.strftime("%b %d %H:%M", time.gmtime(t))
