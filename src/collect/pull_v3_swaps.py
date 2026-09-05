#!/usr/bin/env python3
"""Every Uniswap v3 Swap event on Robinhood Chain in a window (all pools), for pricing fomo-app wallets' trades on
v3 pools (Pons V1 launches, CASHCAT/WETH, ...). Writes rh/v3swaps_{DAY}_{H0}-{H1}.jsonl lines
[block, logIndex, txHash, pool, amount0, amount1, sqrtPriceX96, liquidity, tick]. Read-only public RPC.
usage: python3 pull_v3_swaps.py DAY H0 H1   (run from the data root with rh/blocks/)
"""
import json, urllib.request, time, bisect, glob, datetime, sys, os

RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fomo-memebot/v3swaps"}
SWAP = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
DAY = sys.argv[1]; H0 = int(sys.argv[2]); H1 = int(sys.argv[3])


def call(p):
    for i in range(8):
        try:
            req = urllib.request.Request(RPC, data=json.dumps(p).encode(), headers=H); d = json.load(urllib.request.urlopen(req, timeout=180))
            if "error" in d:
                raise RuntimeError(d["error"])
            return d["result"]
        except Exception:
            time.sleep(3 * (i + 1))
    raise RuntimeError("rpc failed")


def s256(x):
    return x - 2 ** 256 if x >= 2 ** 255 else x


blocks = {}
for f in glob.glob("rh/blocks/blocks*.json"):
    try:
        blocks.update(json.load(open(f)))
    except Exception:
        pass
pts = sorted((int(k, 16), v) for k, v in blocks.items()); xs = [p[0] for p in pts]; ys = [p[1] for p in pts]


def blk(ts):
    i = bisect.bisect_left(ys, ts)
    if i >= len(ys):
        return int(xs[-1] + (ts - ys[-1]) * 9.9)
    if i <= 0:
        return int(xs[0] - (ys[0] - ts) * 9.9)
    x0, y0, x1, y1 = xs[i - 1], ys[i - 1], xs[i], ys[i]; return int(x0 + (x1 - x0) * (ts - y0) / (y1 - y0))


t0 = datetime.datetime.fromisoformat(DAY + "T00:00:00+00:00").timestamp(); b0, b1 = blk(t0 + H0 * 3600), blk(t0 + H1 * 3600)
out_path = f"rh/v3swaps_{DAY}_{H0}-{H1}.jsonl"; prog = out_path + ".progress"
b = int(open(prog).read()) if os.path.exists(prog) else b0
out = open(out_path, "a"); n = 0; step = 2000; t_start = time.time()
while b < b1:
    e = min(b1, b + step)
    try:
        logs = call({"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs", "params": [{"fromBlock": hex(b), "toBlock": hex(e - 1), "topics": [SWAP]}]})
    except RuntimeError:
        step = max(200, step // 2); continue
    for l in logs:
        d = l["data"][2:]; w = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]
        if len(w) < 5:
            continue
        out.write(json.dumps([int(l["blockNumber"], 16), int(l["logIndex"], 16), l["transactionHash"], l["address"].lower(), s256(w[0]), s256(w[1]), w[2], w[3], s256(w[4]) if w[4] < 2 ** 255 else w[4] - 2 ** 256]) + "\n"); n += 1
    b = e; open(prog, "w").write(str(b))
    if len(logs) < 3000:
        step = min(10000, int(step * 1.5))
    elif len(logs) > 8000:
        step = max(200, step // 2)
    print(f"{b - b0}/{b1 - b0} blocks, {n} swaps, {time.time() - t_start:.0f}s", file=sys.stderr, flush=True)
    time.sleep(0.15)
out.close(); print(f"done: {n} v3 swaps", file=sys.stderr)
