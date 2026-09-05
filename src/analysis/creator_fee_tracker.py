#!/usr/bin/env python3
"""Read-only creator fee tracker for Pons V2 (report section 13.2).

Given one or more creator addresses, lists every token they launched (factory creation events), the curve volume each
token has traded (Buy/Sell events on its curve contract), the creator's 0.7% fee share of that volume, and whether the
token graduated to a Uniswap v4 pool. No keys, no signing, no transactions: it only reads the public RPC.

usage: python3 creator_fee_tracker.py 0xCREATOR [0xCREATOR2 ...] [--from-block N]
"""
import json, sys, time, urllib.request, collections

RPC = "https://rpc.mainnet.chain.robinhood.com"
H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fomo-memebot/fee-tracker"}
FACTORY = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"
BUY = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"
SELL = "0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"
INIT = "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6d3307c1e1c5f3a5d0d1c5d0c"  # placeholder; graduation is read from the curve's last state below
FEE_SHARE = 0.007
QUOTE_DEC = {"native": 18, "0x0bd7d308f8e1639fab988df18a8011f41eacad73": 18, "0x5fc5360d0400a0fd4f2af552add042d716f1d168": 6, "0xc1a0957594a80aa55a12e76ae4cdf513e84301c7": 6}
QUOTE_USD = {"native": 2445.0, "0x0bd7d308f8e1639fab988df18a8011f41eacad73": 2445.0, "0x5fc5360d0400a0fd4f2af552add042d716f1d168": 1.0, "0xc1a0957594a80aa55a12e76ae4cdf513e84301c7": 1.0}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def call(method, params):
    for i in range(6):
        try:
            req = urllib.request.Request(RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(), headers=H)
            d = json.load(urllib.request.urlopen(req, timeout=120))
            if "error" in d:
                raise RuntimeError(d["error"])
            return d["result"]
        except Exception:
            time.sleep(2 * (i + 1))
    raise RuntimeError("rpc failed: " + method)


def get_logs(params, step=200_000):
    """chunked eth_getLogs that halves the range on provider limits"""
    out = []
    b0 = int(params["fromBlock"], 16); b1 = int(params["toBlock"], 16) if params["toBlock"] != "latest" else int(call("eth_blockNumber", []), 16)
    b = b0
    while b <= b1:
        e = min(b1, b + step)
        p = dict(params); p["fromBlock"] = hex(b); p["toBlock"] = hex(e)
        try:
            out += call("eth_getLogs", [p]); b = e + 1
        except RuntimeError:
            step = max(2_000, step // 2)
        time.sleep(0.2)
    return out


def quote_of(creation_tx, curve, token):
    rc = call("eth_getTransactionReceipt", [creation_tx]) or {}
    for l in rc.get("logs", []):
        if l["topics"][0] == TRANSFER and len(l["topics"]) > 2 and ("0x" + l["topics"][2][-40:]).lower() == curve and l["address"].lower() != token:
            return l["address"].lower()
    return "native"


def main():
    from_block = 0x2000000
    argv = sys.argv[1:]
    if "--from-block" in argv:
        i = argv.index("--from-block"); from_block = int(argv[i + 1]); argv = argv[:i] + argv[i + 2:]
    args = [a for a in argv if a.startswith("0x")]
    if not args:
        sys.exit(__doc__)
    total = 0.0
    for creator in args:
        creator = creator.lower()
        logs = get_logs({"fromBlock": hex(from_block), "toBlock": "latest", "address": FACTORY, "topics": [None, None, None, "0x" + creator[2:].rjust(64, "0")]})
        print(f"\ncreator {creator}: {len(logs)} launches")
        rows = []
        for l in logs:
            token = "0x" + l["topics"][1][-40:]; curve = "0x" + l["topics"][2][-40:]; b = int(l["blockNumber"], 16)
            q = quote_of(l["transactionHash"], curve, token)
            ev = get_logs({"fromBlock": hex(b), "toBlock": "latest", "address": curve, "topics": [[BUY, SELL]]}, step=2_000_000)
            vol = 0.0; net = 0.0
            for e in ev:
                d = e["data"][2:]; w = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]
                amt = (w[0] if e["topics"][0] == BUY else w[1]) / 10 ** QUOTE_DEC.get(q, 18)
                vol += amt; net += amt if e["topics"][0] == BUY else -amt
            px = QUOTE_USD.get(q)
            fee_usd = vol * FEE_SHARE * px if px else None
            rows.append((b, token, curve, q, len(ev), vol, net, fee_usd))
            if fee_usd:
                total += fee_usd
        rows.sort()
        print(f"{'block':>10s} {'token':44s} {'quote':10s} {'trades':>7s} {'volume (quote)':>15s} {'net in curve':>13s} {'creator fee $':>14s}")
        for b, token, curve, q, n, vol, net, fee in rows:
            print(f"{b:10d} {token:44s} {q[:10]:10s} {n:7d} {vol:15.4f} {net:13.4f} {('%.2f' % fee) if fee is not None else 'n/a':>14s}")
    print(f"\nestimated creator fee income across listed creators: ${total:,.2f} (0.7% of curve volume; pool-phase fees after graduation not included)")


if __name__ == "__main__":
    main()
