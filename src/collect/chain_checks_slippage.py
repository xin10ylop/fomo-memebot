"""two things the auditor could not test: (1) does the curve's buy honour minOut (eth_call on a live curve from a funded address:
a huge minOut must revert, minOut 0 must return tokens); (2) what slippage tolerance do the other buyers actually send (minOut in the
calldata against the tokens they received), which pins the replay's 'later buyers revert beyond a 10% shortfall' assumption"""
import json, urllib.request, time, random, statistics as st, collections
RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) curl/8"}
def call(payload, tries=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(RPC, data=json.dumps(payload).encode(), headers=H); return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:
            err = e; time.sleep(2 * (i + 1))
    return {"error": str(err)[:200]}
BUY = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; BUY_SEL = "59a87bc1"
def word(x): return x.to_bytes(32, "big").hex()
# (2) slippage tolerance of real buyers: direct buys from Sep 9 12-18, their calldata minOut vs the event's tokensOut
rows = []
for line in open("rh/v2curve_2026-09-09_12-18.jsonl"):
    b, li, tx, addr, t0, data = json.loads(line)
    if t0 == BUY[:10]:
        rows.append((tx, addr, int(data[2 + 64:2 + 128], 16)))            # tokensOut is the second word of the Buy event
random.seed(11); sample = random.sample(rows, 240); tol = []; direct = 0; router = 0; latest_curve = None
for i in range(0, len(sample), 20):
    chunk = sample[i:i + 20]
    r = call([{"jsonrpc": "2.0", "id": j, "method": "eth_getTransactionByHash", "params": [tx]} for j, (tx, addr, tk) in enumerate(chunk)])
    if not isinstance(r, list):
        continue
    for x in r:
        t = x.get("result")
        if not t:
            continue
        tx, addr, tk = chunk[x["id"]]; inp = t["input"][2:]
        if t["to"] and t["to"].lower() == addr and inp[:8] == BUY_SEL and len(inp) >= 8 + 192:
            direct += 1; min_out = int(inp[8 + 64:8 + 128], 16)
            tol.append(1 - min_out / tk if tk else None); latest_curve = latest_curve or (addr, t["from"], int(t["value"], 16))
        else:
            router += 1
    time.sleep(0.3)
tol = [x for x in tol if x is not None]; tol.sort()
q = lambda p: tol[min(len(tol) - 1, int(p * len(tol)))]
print(f"direct buys {direct}, router buys {router} (minOut not decoded for routers)")
print(f"direct buyers' slippage tolerance = 1 - minOut/tokensReceived: minOut=0 (no protection) on {100*sum(1 for x in tol if x >= 0.999)/len(tol):.0f}%, "
      f"deciles of the rest: {[round(100*x,1) for x in [sorted(y for y in tol if y < 0.999)[int(k*len([y for y in tol if y<0.999])/10)] for k in range(10)]]} %")
protected = [x for x in tol if x < 0.999]
print(f"of the protected buyers: share with tolerance <= 5%: {100*sum(1 for x in protected if x <= 0.05)/max(1,len(protected)):.0f}%, <= 10%: {100*sum(1 for x in protected if x <= 0.10)/max(1,len(protected)):.0f}%, <= 25%: {100*sum(1 for x in protected if x <= 0.25)/max(1,len(protected)):.0f}%  (n {len(protected)})")
# (1) minOut behaviour: eth_call the newest curve's buy from a funded address with an impossible minOut, then with zero
creates = [json.loads(l) for l in open("rh/creates_v2_2026-09-09.jsonl")]
cv = "0x" + creates[-1][2][2][-40:]; cv = cv.lower()
frm = latest_curve[1] if latest_curve else "0x" + "11" * 20
bal = int(call({"jsonrpc": "2.0", "id": 1, "method": "eth_getBalance", "params": [frm, "latest"]}).get("result", "0x0"), 16)
value = int(0.001e18)
for label, min_out in (("minOut impossible (1e30 tokens)", 10 ** 30), ("minOut 0", 0)):
    data = "0x" + BUY_SEL + word(value) + word(min_out) + frm[2:].rjust(64, "0")
    r = call({"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"from": frm, "to": cv, "value": hex(value), "data": data}, "latest"]})
    print(f"eth_call buy on curve {cv[:10]} from {frm[:10]} (balance {bal/1e18:.3f} ETH), {label}: {json.dumps(r.get('error', {'result': r.get('result', '')[:66]}))[:160]}")
