"""crowd_raw.py: every transaction aimed at a launch's curve in the creation second's blocks and the seat block, raw, so that any
counting rule (the tables' distinct senders, the engine's distinct relays plus direct senders) is evaluated offline on the same
pull. Per launch: cv, b0, k, token, creator, named, and per block offset the list of {fr, to, direct, named_fr, named_data,
to_token} where named_data says a named wallet's address is in the calldata (the bundle's helper; the engine skips those).
    python3 src/analysis/crowd_raw.py data/derived/live_vs_table/launches_141_creators.json data/derived/live_vs_table/crowd_raw_sep1819.json"""
import json, urllib.request, time, sys
RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 curl/8"}
V2F = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"                    # the Pons V2 factory (its creation log: topics[1] token, [2] curve, [3] creator)
def call(m, p):
    for i in range(6):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(), headers=H), timeout=60)); time.sleep(0.22)
            if "error" in r: raise RuntimeError(r["error"])
            return r["result"]
        except Exception as e:
            if i == 5: raise
            time.sleep(2 * (i + 1))
L = json.load(open(sys.argv[1])); out = sys.argv[2]; res = []
for n, l in enumerate(L):
    cv = l["cv"].lower(); b0 = l["b0"]; k = l["same_second_blocks"]; creator = (l.get("creator") or "").lower(); named = {w.lower() for w in l.get("named", [])}
    token = None
    for lg in call("eth_getLogs", [{"fromBlock": hex(b0), "toBlock": hex(b0), "address": V2F}]):
        if len(lg["topics"]) > 3 and lg["topics"][2][-40:] == cv[2:]: token = "0x" + lg["topics"][1][-40:]
    if token is None: raise SystemExit(f"no factory log for {cv} at block {b0}")
    blocks = []
    for off in range(0, k + 2):
        blk = call("eth_getBlockByNumber", [hex(b0 + off), True]); rows = []
        for t in blk["transactions"]:
            fr = t["from"].lower(); to = (t.get("to") or "").lower(); data = t.get("input", "")
            if to == cv or cv[2:] in data:
                rows.append({"fr": fr, "to": to, "ix": int(t["transactionIndex"], 16), "direct": to == cv, "named_fr": fr in named or fr == creator, "named_data": any(w[2:] in data for w in named), "to_token": to == token, "sel": data[:10]})
        blocks.append(rows)
    res.append({"cv": cv, "b0": b0, "k": k, "T0": l["T0"], "token": token, "creator": creator, "named": sorted(named), "blocks": blocks})
    if n % 20 == 0: print(n, cv[:10], "blocks", k + 2, [len(b) for b in blocks], flush=True)
json.dump(res, open(out, "w"), indent=0); print("wrote", out, len(res))
