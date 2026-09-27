"""q2b.py (reviewer D): would the 15-block rule have survived round 1's two mechanisms?
 (1) bundle dumps: for every fire, the bundle's (creation-second buyers, creator, named) sold share by E1+15 and by E1+300, the
     block of its first sell; the fires with a dump (>= 10% sold, B's definition) at each horizon, and their returns at 15 and 300
 (2) the thinner follow-on demand: outsiders' ETH bought in E1+1..15 (inside a 15-block hold) against E1+16..60 (after it)
 (3) the operator template B found (launches linked by a shared named wallet or creator; the one holding the Sep 26 23:53 and
     Sep 27 00:10 fires): its fires at 15 and 300 blocks
 (4) every recent fire, in time order, at 15 / 60 / 150 / 300 blocks
    python3 data/derived/edge_check/D/q2b.py > data/derived/edge_check/D/q2b.txt"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c, kit as K
ALL = sorted(K.FIT + K.REC, key=lambda f: f["T0"])
def sold_by(f, h): return max([s for d, s in f["bsell"] if d <= h], default=0.0)
print("(1) BUNDLE DUMPS among the fires (bundle sold >= 10% of its tokens by the horizon)")
for g, S in (("fit", K.FIT), ("recent", K.REC)):
    fi = [f for f in S if f["fire"]]
    for h in (15, 300):
        d = [f for f in fi if sold_by(f, h) >= 0.10]; nd = [f for f in fi if sold_by(f, h) < 0.10]
        print(f"  {g:6s} dump by E1+{h:<3d}: {len(d):2d}/{len(fi)} fires  -> their h15 {c.mean([f['path'][15] for f in d]):+6.1%} h300 {c.mean([f['path'][300] for f in d]):+6.1%}"
              f" | the others h15 {c.mean([f['path'][15] for f in nd]):+6.1%} h300 {c.mean([f['path'][300] for f in nd]):+6.1%}")
    firsts = sorted(min([d for d, s in f["bsell"]], default=999) for f in fi); print(f"  {g:6s} first bundle sell after E1 (blocks, fires with any): {[x for x in firsts if x < 999]}")
print("\n(2) FOLLOW-ON DEMAND: outsiders' ETH (not the bundle) bought after the seat block, mean / median per fire")
for g, S in (("fit", K.FIT), ("recent", K.REC)):
    fi = [f for f in S if f["fire"]]
    def oeth(f, lo, hi):
        L = c.tape(f["cv"]); e1 = c.seat_block(L, L["b0"]); T0 = L["T0"]; ts = L["ts"]
        bundle = {x["who"] for x in L["rows"] if ts.get(x["bn"], 9e18) == T0 and x["k"] == "B"} | {f["creator"]} | set(f["named"])
        return sum(x["eth"] for x in L["rows"] if x["k"] == "B" and e1 + lo <= x["bn"] <= e1 + hi and x["who"] not in bundle and x["who"] not in c.lv.OURS)
    a = [oeth(f, 1, 15) for f in fi]; b = [oeth(f, 16, 60) for f in fi]
    import statistics as st
    print(f"  {g:6s} E1+1..15: {c.mean(a):.3f} / {st.median(a):.3f} ETH    E1+16..60: {c.mean(b):.3f} / {st.median(b):.3f} ETH")
print("\n(3) THE OPERATOR TEMPLATE (shared named wallet or creator, all launches in time order)")
par = {}
def root(x):
    while par.get(x, x) != x: x = par[x]
    return x
for f in ALL:
    ids = ["c:" + f["creator"]] + ["n:" + w for w in f["named"]]
    for x in ids: par.setdefault(x, x)
    for x in ids[1:]:
        a, b = root(ids[0]), root(x)
        if a != b: par[b] = a
tmpl = collections.defaultdict(list)
for f in ALL: tmpl[root("c:" + f["creator"])].append(f)
target = next(f for f in ALL if f["cv"].startswith("0x") and f["fire"] and c.hhmm(f["T0"]) == "Sep 27 00:10")
T = tmpl[root("c:" + target["creator"])]
print(f"  template of the Sep 27 00:10 fire: {len(T)} launches, {sum(f['fire'] for f in T)} fires")
for g in ("fit", "recent"):
    fi = [f for f in T if f["fire"] and f["grp"] == g]
    print(f"   {g:6s} fires {len(fi)}: h15 {c.mean([f['path'][15] for f in fi]):+6.1%}  h300 {c.mean([f['path'][300] for f in fi]):+6.1%}   -> " + " ".join(f"{c.hhmm(f['T0'])[4:]} {f['path'][15]:+.0%}/{f['path'][300]:+.0%}" for f in fi))
for g, S in (("fit", K.FIT), ("recent", K.REC)):
    fi = [f for f in S if f["fire"] and f not in T]
    print(f"   {g:6s} fires outside this template {len(fi)}: h15 {c.mean([f['path'][15] for f in fi]):+6.1%}  h300 {c.mean([f['path'][300] for f in fi]):+6.1%}")
print("\n(4) EVERY RECENT FIRE (h0 / h15 / h60 / h150 / h300; bundle sold by 15 / 300; outsider wallets in 15 blocks)")
for f in [f for f in K.REC if f["fire"]]:
    p = f["path"]; print(f"  {c.hhmm(f['T0'])} {f['cv'][:10]} fleets@k-2 {f['k2']['f']}  {p[0]:+6.1%} {p[15]:+6.1%} {p[60]:+6.1%} {p[150]:+6.1%} {p[300]:+6.1%}   bundle sold {sold_by(f,15):4.0%} / {sold_by(f,300):4.0%}   ow15 {f['ow15']}")
