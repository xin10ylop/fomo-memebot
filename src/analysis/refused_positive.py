"""refused_positive.py: are we refusing positive trades? Every qualifying launch of every prediction piece, the engine's own
decision for it (engine_vs_chain: the reason in the log), and what the seat would have paid (the hold grid's behind-one return
at hold 11, $13 stake). Run on the box (the engine log is there):

    sudo python3 src/analysis/refused_positive.py [--min 15] [--days 7]

Prints the return of every decision class, then the refused launches that would have paid over --min percent."""
import glob, json, os, re, subprocess, sys, time, calendar
args = sys.argv[1:]
def arg(k, d):
    return args[args.index(k) + 1] if k in args else d
MIN = float(arg("--min", "15")); DAYS = float(arg("--days", "30")); D = "data/derived/live_vs_table"; HOLD = arg("--hold", "11")
LINE = re.compile(r"^(\w{3} \d+ \d\d:\d\d:\d\d) (0x[0-9a-f]{8}) .*?fleets@k-2 (\d+) \| (FIRE|FILL|GATE|PRE|GUARD|SKIP)\s*(.*)$")
def reason_key(cls, text):
    t = text.lower()
    if cls in ("FIRE", "FILL", "GUARD"): return "fired"
    if "attackers" in t: return "gate: attackers < 2"
    if "relay holds" in t: return "relay under the stake (Sep 29-30 fault)"
    if "creator buy" in t and "supply" in t: return "creator supply < 1%"
    if "bundle" in t and "> 3" in t: return "bundle cap (> 3 ETH)"
    if "boundary" in t: return "seat second already open (late creation)"
    if "not fresh" in t: return "nonce/gas not fresh"
    if "shooters" in t: return "shooters not ready"
    if "supply cap" in t: return "supply cap"
    return cls.lower() + ": " + re.sub(r"[\d.]+", "#", t)[:38]
def span_of(n):
    for f in glob.glob(f"data/derived/*/e1m_{n}.json"):
        d = json.load(open(f)); return d["t_lo"], d["t_hi"]
now = time.time(); rows = []; pieces = 0
for pf in sorted(glob.glob(f"{D}/prediction_*.txt")):
    n = os.path.basename(pf)[11:-4]; sp = span_of(n); cf = f"{D}/crowd_raw_{n}.json.gz"; hg = f"{D}/hold_grid_week_{n}.json"; lf = f"{D}/launches_{n}.json"
    if not (sp and os.path.exists(cf) and os.path.exists(hg) and os.path.exists(lf)) or sp[1] < now - DAYS * 86400: continue
    fmt = lambda t: time.strftime("%Y-%m-%d %H:%M", time.gmtime(t))
    out = subprocess.run([sys.executable, "src/analysis/engine_vs_chain.py", lf, "--crowd", cf, "--from", fmt(sp[0]), "--to", fmt(sp[1] + 60)], capture_output=True, text=True).stdout
    grid = {g["cv"][:10]: g for g in json.load(open(hg))}
    fl = {}
    for line in open(pf):
        m = re.match(r"(\w{3} \d+ \d\d:\d\d)\s+(0x[0-9a-f]{8})\s+(\d+)\s+(\[[^\]]*\])\s+(\d+)\s+(\d+)\s+(\d+)", line)
        if m: fl[m.group(2)] = (int(m.group(3)), int(m.group(5)))
    got = 0
    for line in out.splitlines():
        m = LINE.match(line)
        if not m: continue
        cv = m.group(2); g = grid.get(cv)
        if g is None or f"behind1_13_h{HOLD}" not in g: continue
        rows.append({"piece": n, "when": m.group(1), "cv": cv, "k": fl.get(cv, (None, None))[0], "k1": fl.get(cv, (None, None))[1], "cls": m.group(4), "reason": reason_key(m.group(4), m.group(5)),
                     "text": m.group(5)[:70], "r": 100 * g[f"behind1_13_h{HOLD}"], "bundle": g.get("bundle_eth"), "tier": g.get("tier")}); got += 1
    pieces += 1; print(f"  {n}: {got} decisions joined", file=sys.stderr)
def summ(v):
    if not v: return "n   0"
    s = sorted(v); return f"n {len(v):3d}  pos {sum(1 for x in v if x > 0):3d} ({100 * sum(1 for x in v if x > 0) / len(v):3.0f}%)  mean {sum(v) / len(v):+6.1f}%  median {s[len(s) // 2]:+6.1f}%  sum@$13 ${13 * sum(v) / 100:+7.2f}  @$25 ${25 * sum(v) / 100:+7.2f}"
print(f"{len(rows)} qualifying launches with an engine decision, {pieces} pieces, {min(r['when'] for r in rows)} - {max(r['when'] for r in rows)} UTC; return = the seat behind one, hold {HOLD}, $13, before gas")
print(f"{'decision':44s} {summ([r['r'] for r in rows if r['reason'] == 'fired'])}".replace("decision", "fired (any fill or guard revert)"))
ref = [r for r in rows if r["reason"] != "fired"]
print(f"{'refused, all':44s} {summ([r['r'] for r in ref])}")
for k in sorted(set(r["reason"] for r in ref), key=lambda k: -len([r for r in ref if r["reason"] == k])):
    print(f"  {k:42s} {summ([r['r'] for r in ref if r['reason'] == k])}")
print("refused by the attackers gate, by fleets at k-1 (the chain's count):")
for n_ in (0, 1, 2, 3):
    v = [r["r"] for r in ref if r["reason"].startswith("gate") and r["k1"] == n_]
    if v: print(f"  fleets {n_} on the chain, engine saw < 2      {summ(v)}")
print(f"\nrefused launches that would have paid over +{MIN:.0f}%:")
for r in sorted(ref, key=lambda r: -r["r"]):
    if r["r"] > MIN: print(f"  {r['when']} {r['cv']} k {r['k']} fleets(k-1) {r['k1']} bundle {r['bundle']:.2f} tier {r['tier']}  {r['r']:+6.1f}%  {r['reason']}")
