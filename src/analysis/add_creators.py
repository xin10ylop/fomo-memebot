"""add_creators.py: give e1_multi's launches their creator and named wallets (for crowd_signal.py). python3 add_creators.py in.json [in2.json ...] out.json"""
import json, sys
sys.path.insert(0, "src/analysis"); from live_vs_table import call, V2F, pad
out = []
for f in sys.argv[1:-1]:
    for l in json.load(open(f))["launches"]:
        cl = [x for x in call("eth_getLogs", [{"fromBlock": hex(l["b0"]), "toBlock": hex(l["b0"]), "address": V2F, "topics": [None, None, pad(l["cv"])]}]) if len(x["topics"]) > 3]
        l["creator"] = ("0x" + cl[0]["topics"][3][-40:]).lower() if cl else None
        if cl:
            tx = call("eth_getTransactionByHash", [cl[0]["transactionHash"]]); data = bytes.fromhex(tx["input"][2:]); words = [data[4 + 32 * i: 4 + 32 * (i + 1)] for i in range((len(data) - 4) // 32)]
            l["named"] = sorted({"0x" + w[12:].hex() for w in words if w[:12] == b"\0" * 12 and int.from_bytes(w[12:], "big") > 2 ** 100} - {l["creator"]})
        out.append(l)
json.dump(out, open(sys.argv[-1], "w")); print(len(out), "launches ->", sys.argv[-1])
