#!/usr/bin/env python3
"""Every fomo-app wallet that transacted in a window: UserOperationEvent logs from the ERC-4337 EntryPoint (report section 17).

fomo-app trades are ERC-4337 user operations relayed by a bundler, so the transaction sender is the bundler and the real
wallet is the userOp sender, which the EntryPoint logs as an indexed topic. This pulls every UserOperationEvent in
[T0, T1) and writes rh/userops_{DAY}.jsonl lines: [block, txHash, sender, success]. Read-only public RPC.

usage: python3 pull_userops.py DAY H0 H1   (hours UTC; run from the data root with rh/blocks/)
"""
import json, urllib.request, time, bisect, glob, datetime, sys

RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fomo-memebot/userops"}
EP = "0x0000000071727de22e5e9d8baf0edac6f37da032"; UOP = "0x49628fd1471006c1482da88028e9ce4dbb080b815c9b0344d39e5a8e6ec1419f"
DAY = sys.argv[1]; H0 = int(sys.argv[2]); H1 = int(sys.argv[3])


def call(p):
    for i in range(8):
        try:
            req = urllib.request.Request(RPC, data=json.dumps(p).encode(), headers=H); d = json.load(urllib.request.urlopen(req, timeout=120))
            if "error" in d:
                raise RuntimeError(d["error"])
            return d["result"]
        except Exception as e:
            time.sleep(3 * (i + 1))
    raise RuntimeError("rpc failed")


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
out = open(f"rh/userops_{DAY}_{H0}-{H1}.jsonl", "w"); n = 0; b = b0; step = 5000; t_start = time.time()
while b < b1:
    e = min(b1, b + step)
    try:
        logs = call({"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs", "params": [{"fromBlock": hex(b), "toBlock": hex(e - 1), "address": EP, "topics": [UOP]}]})
    except RuntimeError:
        step = max(500, step // 2); continue
    for l in logs:
        d = l["data"][2:]; success = int(d[64:128], 16) if len(d) >= 128 else 1
        out.write(json.dumps([int(l["blockNumber"], 16), l["transactionHash"], "0x" + l["topics"][2][-40:], success]) + "\n"); n += 1
    b = e
    if len(logs) < 2000:
        step = min(20000, step * 2)
    print(f"{b - b0}/{b1 - b0} blocks, {n} userOps, {time.time() - t_start:.0f}s", file=sys.stderr, flush=True)
    time.sleep(0.2)
out.close(); print(f"done: {n} userOps in blocks {b0}-{b1}", file=sys.stderr)
