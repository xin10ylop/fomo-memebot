#!/usr/bin/env python3
"""Live gauge for the creator fee share (report section 13.2). Read-only: no keys, no transactions.

Looks at the Pons V2 launches of the last HOURS hours and reports what the 0.7% fee share on curve volume has earned per
launch so far, for three cohorts that the report (section 13.3) showed earn very different amounts: single-launch
creators with an initial buy under $5 (the no-stake version), single-launch creators with a larger initial buy (whose fee
comes with a stake that is usually lost), and creators with 2-9 launches in the span (the bots filter them and their fee
collapses). Each line: n, mean, median, p90, share of launches covering the $1.22 launch fee, share nobody else traded.
Run it before launching anything: the first line is the number that applies to one launch from a fresh wallet.

usage: python3 creator_fee_gauge.py [--hours 2] [--eth-usd 2445]
"""
import json, sys, time, urllib.request, collections, statistics as st

RPC = "https://rpc.mainnet.chain.robinhood.com"
H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fomo-memebot/fee-gauge"}
FACTORY = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"
BUY = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"
SELL = "0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
FEE_SHARE = 0.007; LAUNCH_FEE_ETH = 0.0005; BLOCKS_PER_S = 9.9
QUOTE_DEC = {"native": 18, "0x0bd7d308f8e1639fab988df18a8011f41eacad73": 18, "0x5fc5360d0400a0fd4f2af552add042d716f1d168": 6, "0xc1a0957594a80aa55a12e76ae4cdf513e84301c7": 6}


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


def get_logs(p, step):
    out = []; b = int(p["fromBlock"], 16); b1 = int(p["toBlock"], 16)
    while b <= b1:
        e = min(b1, b + step); pp = dict(p); pp["fromBlock"] = hex(b); pp["toBlock"] = hex(e)
        try:
            out += call("eth_getLogs", [pp]); b = e + 1
        except RuntimeError:
            step = max(1_000, step // 2)
        time.sleep(0.15)
    return out


def main():
    hours = float(sys.argv[sys.argv.index("--hours") + 1]) if "--hours" in sys.argv else 2.0
    eth_usd = float(sys.argv[sys.argv.index("--eth-usd") + 1]) if "--eth-usd" in sys.argv else 2445.0
    usd = {"native": eth_usd, "0x0bd7d308f8e1639fab988df18a8011f41eacad73": eth_usd, "0x5fc5360d0400a0fd4f2af552add042d716f1d168": 1.0, "0xc1a0957594a80aa55a12e76ae4cdf513e84301c7": 1.0}
    head = int(call("eth_blockNumber", []), 16); b0 = head - int(hours * 3600 * BLOCKS_PER_S)
    creations = get_logs({"fromBlock": hex(b0), "toBlock": hex(head), "address": FACTORY}, 20_000)
    creations = [l for l in creations if len(l["topics"]) > 3]
    creators = collections.Counter("0x" + l["topics"][3][-40:] for l in creations)
    print(f"last {hours:g} h: {len(creations)} Pons V2 launches, {len(creators)} creators, {sum(1 for c, n in creators.items() if n == 1)} single-launch creators")
    cohorts = {k: {"fees": [], "no_stranger": 0} for k in ("single launch, initial buy < $5", "single launch, initial buy >= $5", "2-9 launches, initial buy < $25")}
    fees_eth_quoted = []
    for l in creations:
        creator = "0x" + l["topics"][3][-40:]
        if creators[creator] >= 10:
            continue
        token = "0x" + l["topics"][1][-40:]; curve = "0x" + l["topics"][2][-40:]; b = int(l["blockNumber"], 16)
        d0 = l["data"][2:]; q0_raw = int(d0[64:128], 16) if len(d0) >= 128 else 0
        rc = call("eth_getTransactionReceipt", [l["transactionHash"]]) or {}
        quote = "native"
        for lg in rc.get("logs", []):
            if lg["topics"][0] == TRANSFER and len(lg["topics"]) > 2 and ("0x" + lg["topics"][2][-40:]).lower() == curve and lg["address"].lower() != token:
                quote = lg["address"].lower(); break
        px = usd.get(quote)
        if px is None:
            continue
        stake = q0_raw / 10 ** QUOTE_DEC.get(quote, 18) * px
        if creators[creator] == 1:
            key = "single launch, initial buy < $5" if stake < 5 else "single launch, initial buy >= $5"
        elif stake < 25:
            key = "2-9 launches, initial buy < $25"
        else:
            continue
        ev = call("eth_getLogs", [{"fromBlock": hex(b), "toBlock": hex(head), "address": curve, "topics": [[BUY, SELL]]}])
        vol = 0.0
        for e in ev:
            d = e["data"][2:]; w = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]
            vol += (w[0] if e["topics"][0] == BUY else w[1]) / 10 ** QUOTE_DEC.get(quote, 18)
        f = vol * FEE_SHARE * px; c = cohorts[key]; c["fees"].append(f)
        if quote == "native" and creators[creator] == 1:
            fees_eth_quoted.append(f)
        if len(ev) <= 1:
            c["no_stranger"] += 1
        time.sleep(0.1)
    fee_usd = LAUNCH_FEE_ETH * eth_usd
    print(f"fee share earned so far per launch, USD (launch fee ${fee_usd:.2f}):")
    for key, c in cohorts.items():
        fees = sorted(c["fees"]); n = len(fees)
        if not n:
            print(f"  {key:36s} n=0"); continue
        print(f"  {key:36s} n={n:4d} mean ${st.mean(fees):7.2f} median ${fees[n // 2]:6.2f} p90 ${fees[9 * n // 10]:7.2f} max ${fees[-1]:6.0f} | covering the launch fee {100 * sum(1 for x in fees if x > fee_usd) / n:3.0f}% | nobody else traded {100 * c['no_stranger'] / n:3.0f}%")
    if fees_eth_quoted:
        print(f"  single-launch, ETH-quoted only: n={len(fees_eth_quoted)} mean ${st.mean(fees_eth_quoted):.2f} median ${st.median(fees_eth_quoted):.2f}")
    print("reference (six-hour windows, section 13.3): single launch < $5 initial buy: mean $4-23, median $0-2.7; 2-9 launches: mean $0.2-6.6, median $0-1.5")


if __name__ == "__main__":
    main()
