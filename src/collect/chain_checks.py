"""killer checks that need the chain: (a) real gas per buy / sell / approve from receipts, (b) does the sequencer accept a raw
transaction from an unknown sender (unfunded throwaway key: expect an 'insufficient funds' style error, never an execution),
(c) do the curve and the factory carry blacklist-like selectors"""
import json, urllib.request, time, random, sys, collections
RPC = "https://rpc.mainnet.chain.robinhood.com"; SEQ = "https://sequencer.mainnet.chain.robinhood.com"
H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) curl/8"}
def call(url, payload, tries=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=H); return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:
            err = e; time.sleep(2 * (i + 1))
    return {"error": str(err)[:200]}
BUY = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"; SELL = "0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"
# (a) gas: sample buys and sells from Sep 9 12-18
buys, sells = [], []
random.seed(5)
for line in open("rh/v2curve_2026-09-09_12-18.jsonl"):
    b, li, tx, addr, t0, data = json.loads(line)
    (buys if t0 == BUY[:10] else sells).append(tx)
sample = random.sample(buys, 40) + random.sample(sells, 40)
gp_now = int(call(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_gasPrice", "params": []})["result"], 16)
eth = 2445.0
rows = []
for i in range(0, len(sample), 20):
    chunk = sample[i:i + 20]
    r = call(RPC, [{"jsonrpc": "2.0", "id": j, "method": "eth_getTransactionReceipt", "params": [h]} for j, h in enumerate(chunk)])
    if isinstance(r, list):
        for x in r:
            rc = x.get("result")
            if rc:
                kind = "buy" if any(l["topics"][0] == BUY for l in rc["logs"]) else "sell"
                direct = rc["to"] and rc["to"].lower() == next((l["address"].lower() for l in rc["logs"] if l["topics"][0] in (BUY, SELL)), "")
                rows.append((kind, direct, int(rc["gasUsed"], 16), int(rc.get("effectiveGasPrice", "0x0"), 16), int(rc["blockNumber"], 16)))
    time.sleep(0.3)
by = collections.defaultdict(list)
for kind, direct, gu, gpx, blk in rows:
    by[(kind, "direct" if direct else "router")].append((gu, gpx))
print("gas price now: %.4f gwei" % (gp_now / 1e9))
for k, v in sorted(by.items()):
    gus = sorted(g for g, p in v); gps = sorted(p for g, p in v)
    print(f"{k[0]:4s} {k[1]:6s} n={len(v):2d} gasUsed median {gus[len(gus)//2]:,} (p90 {gus[int(0.9*len(gus))-1]:,})  price median {gps[len(gps)//2]/1e9:.4f} gwei  -> ${gus[len(gus)//2]*gps[len(gps)//2]/1e18*eth:.4f} per tx at ETH ${eth:.0f}")
# an approve: 46k-50k gas is the ERC-20 norm; price the round trip at the observed price
med_price = sorted(p for v in by.values() for g, p in v)[len(rows)//2]
buy_g = sorted(g for g, p in by[("buy", "direct")])[len(by[("buy", "direct")])//2] if by[("buy", "direct")] else 0
sell_g = sorted(g for g, p in by[("sell", "direct")])[len(by[("sell", "direct")])//2] if by[("sell", "direct")] else 0
rt = (buy_g + sell_g + 50000) * med_price / 1e18 * eth
print(f"round trip buy+approve+sell at the observed price: {buy_g:,}+50,000+{sell_g:,} gas x {med_price/1e9:.4f} gwei = ${rt:.4f}; the tables assume $1.00 -> gas gate GAS_MAX_SHARE 5% of a $25 stake = $1.25")
# (b) sequencer acceptance with an unfunded throwaway key
from eth_account import Account
from eth_utils import to_checksum_address
a = Account.create()
tx = {"to": to_checksum_address("0x" + "11" * 20), "value": 0, "data": b"", "gas": 21000, "gasPrice": gp_now, "nonce": 0, "chainId": 4663}
raw = "0x" + bytes(a.sign_transaction(tx).raw_transaction).hex()
for name, url in (("sequencer", SEQ), ("public rpc", RPC)):
    r = call(url, {"jsonrpc": "2.0", "id": 1, "method": "eth_sendRawTransaction", "params": [raw]})
    print(f"{name}: unfunded raw tx from a fresh key ->", json.dumps(r.get("error", r.get("result")))[:160])
# (c) blacklist-like selectors in the curve and the factory bytecode
import hashlib
def sel(sig):
    from eth_utils import keccak
    return keccak(text=sig)[:4].hex()
cands = ["blacklist(address)", "blacklist(address,bool)", "setBlacklist(address,bool)", "addBlacklist(address)", "isBlacklisted(address)", "blocked(address)", "setBlocked(address,bool)", "ban(address)",
         "banned(address)", "setBanned(address,bool)", "denylist(address)", "isDenylisted(address)", "pause()", "setPaused(bool)", "paused()", "setTradingEnabled(bool)", "setMaxTx(uint256)", "setMaxWallet(uint256)",
         "setSnipeTax(uint256)", "setSniperTax(uint256)", "setTax(uint256)", "setFee(uint256)", "setExempt(address,bool)", "setWhitelist(address,bool)", "transferOwnership(address)", "upgradeTo(address)", "upgradeToAndCall(address,bytes)"]
factory = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"
curve = next(json.loads(l)[3] for l in open("rh/v2curve_2026-09-09_12-18.jsonl"))
for name, addr in (("factory", factory), ("curve " + curve[:10], curve)):
    code = call(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_getCode", "params": [addr, "latest"]}).get("result", "0x")
    found = [c for c in cands if sel(c) in code[2:]]
    proxy = "363d3d373d3d3d363d73" in code[2:] or sel("implementation()") in code[2:]
    print(f"{name}: code {len(code)//2-1:,} bytes, proxy-like {proxy}, selectors present: {found}")
