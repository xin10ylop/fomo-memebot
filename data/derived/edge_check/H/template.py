"""template.py (edge_check/H): the causal named-wallet template flag for every launch, and the templates it finds.
    python3 data/derived/edge_check/H/template.py > data/derived/edge_check/H/template.txt
Online, in T0 order over all 759 launches of both periods (fires and refused alike): a template is a group of earlier launches
merged whenever a launch's named-wallet set shares >= MINSH wallets with the group's wallet union. A launch is FLAGGED when its
named set shares >= MINSH wallets with a group that already holds >= MINN launches BEFORE it (only earlier launches count); it then
joins (and merges) every group it matched. Writes H/template_flags.json {cv: {"flag", "size_before", "tid"}} for MINSH=3, MINN=5
(the brief's filter) and the sensitivity grid MINSH in {2,3,5}, MINN in {3,5,8}."""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
def flags(P, minsh=3, minn=5):
    groups = {}; nxt = 0; out = {}
    for x in P:
        S = set(x["named"]); hit = [gid for gid, g in groups.items() if len(S & g["w"]) >= minsh]
        size = max((len(groups[g]["l"]) for g in hit), default=0)
        if hit:
            gid = min(hit, key=lambda g: groups[g]["t"])
            for o in hit:
                if o != gid: groups[gid]["w"] |= groups[o]["w"]; groups[gid]["l"] += groups[o]["l"]; del groups[o]
        else: gid = nxt; nxt += 1; groups[gid] = {"w": set(), "l": [], "t": x["T0"]}
        groups[gid]["w"] |= S; groups[gid]["l"].append(x["cv"])
        out[x["cv"]] = {"flag": size >= minn, "size_before": size, "tid": gid}
    final = {}
    for gid, g in groups.items():
        for cv in g["l"]: final[cv] = gid
    for cv in out: out[cv]["final_tid"] = final[cv]
    return out, groups
if __name__ == "__main__":
    P = load(); byc = {x["cv"]: x for x in P}
    grid = {}
    for minsh in (2, 3, 5):
        for minn in (3, 5, 8):
            f, groups = flags(P, minsh, minn); grid[f"{minsh}_{minn}"] = f
            if (minsh, minn) == (3, 5): F35, G35 = f, groups
    json.dump(grid, open(H + "template_flags.json", "w"))
    print("the brief's filter: shares >= 3 named wallets with a template of >= 5 earlier launches")
    for s in ("fit", "rec"):
        S = [x for x in P if x["set"] == s]
        for lab, key in (("tables", "fire_tab"), ("engine", "fire_eng")):
            Fi = [x for x in S if x[key]]; fl = [x for x in Fi if F35[x["cv"]]["flag"]]
            print(f"  {s:3s} {lab:6s}: {len(fl)} of {len(Fi)} fires flagged; all launches flagged {sum(F35[x['cv']]['flag'] for x in S)} of {len(S)}")
    print("\ntemplates (final groups) with >= 5 launches, in order of the first launch:")
    for gid, g in sorted(G35.items(), key=lambda kv: kv[1]["t"]):
        if len(g["l"]) < 5: continue
        L = sorted((byc[cv] for cv in g["l"]), key=lambda x: x["T0"])
        print(f"\n  template {gid}: {len(L)} launches {hms(L[0]['T0'])} - {hms(L[-1]['T0'])}, {len(g['w'])} named wallets in its union")
        for x in L:
            fl = F35[x["cv"]]; r11 = "   n/a" if x["r11"] is None else f"{x['r11']:+6.1%}"
            print(f"    {hms(x['T0'])} {x['win']:12s} {x['cv'][:10]} named {len(x['named']):2d} bundle {x['bundle']:.3f}  tab {x['f_tab']} eng {x['f_eng']}"
                  f"{'  FIRE-eng' if x['fire_eng'] else ('  fire-tab' if x['fire_tab'] else '          ')}  h11 {r11} h15 {x['r15']:+6.1%}  earlier in template {fl['size_before']:2d} {'FLAGGED' if fl['flag'] else ''}")
    for key in sorted(grid):
        f = grid[key]; line = []
        for s in ("fit", "rec"):
            for k2 in ("fire_tab", "fire_eng"):
                Fi = [x for x in P if x["set"] == s and x[k2]]; line.append(f"{s}-{k2[5:]} {sum(f[x['cv']]['flag'] for x in Fi)}/{len(Fi)}")
        print(f"sensitivity shares>={key.split('_')[0]} size>={key.split('_')[1]}: " + ", ".join(line))
