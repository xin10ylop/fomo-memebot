"""code_check.py (reviewer B): the runtime code of the Pons V2 factory and of curves created in the fit windows and since Sep 24
(hash and length; the public node serves the latest code only, so a curve's code is its code today, the same code it was
created with unless it is a proxy). python3 data/derived/edge_check/B/code_check.py"""
import sys, os, json, hashlib, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common as c
import live_vs_table as lv
F = json.load(open(c.B + "features.json"))
fit = sorted([f for f in F if f["fire"] and f["grp"] == "fit"], key=lambda f: f["T0"]); rec = sorted([f for f in F if f["fire"] and f["grp"] == "recent"], key=lambda f: f["T0"])
ref = None
for lab, a in [("factory", lv.V2F)] + [(f"fit {c.hhmm(f['T0'])}", f["cv"]) for f in (fit[0], fit[-1])] + [(f"recent {c.hhmm(f['T0'])}", f["cv"]) for f in (rec[0], rec[-1])]:
    code = lv.call("eth_getCode", [a, "latest"]); time.sleep(0.15)
    body = bytes.fromhex(code[2:])
    if lab != "factory" and ref is None: ref = body
    diff = sum(x != y for x, y in zip(body, ref)) if (ref is not None and lab != "factory" and len(body) == len(ref)) else None
    runs = sorted({i // 32 for i, (x, y) in enumerate(zip(body, ref)) if x != y}) if diff else []
    print(f"   bytes differing from the first fit curve: {diff} in {len(runs)} 32-byte words") if diff is not None else None
    print(f"{lab:22s} {a[:12]} {len(body):6d} bytes  sha256 {hashlib.sha256(body).hexdigest()[:16]}" + (f"  (EIP-1167 proxy to 0x{body[10:30].hex()})" if len(body) == 45 else ""))
