"""block-time anchors, batched eth_getBlockByNumber with three workers.
usage: pull_anchors.py skeleton STEP            (from the last known anchor to the head)
       pull_anchors.py range B0 B1 STEP         (dense anchors inside a block range)"""
import json, urllib.request, time, glob, sys, os, threading
RPC = "https://rpc.mainnet.chain.robinhood.com"; H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) curl/8"}
OUT = "rh/blocks/blocks_sep7_10.json"; lock = threading.Lock()
def call(payload, tries=8):
    for i in range(tries):
        try:
            req = urllib.request.Request(RPC, data=json.dumps(payload).encode(), headers=H); return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception:
            time.sleep(3 * (i + 1))
    return None
new = json.load(open(OUT)) if os.path.exists(OUT) else {}
if sys.argv[1] == "skeleton":
    blocks = {}
    for f in glob.glob("rh/blocks/blocks*.json"):
        blocks.update(json.load(open(f)))
    last = max(int(k, 16) for k in blocks); head = int(call({"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []})["result"], 16); step = int(sys.argv[2])
    need = [b for b in range(last + step, head, step)] + [head]
else:
    b0, b1, step = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]); need = list(range(b0, b1, step))
need = [b for b in need if hex(b) not in new]
print(sys.argv[1], "anchors needed", len(need), file=sys.stderr, flush=True)
chunks = [need[i:i + 50] for i in range(0, len(need), 50)]; done = [0]
def worker(k):
    for ci in range(k, len(chunks), 3):
        chunk = chunks[ci]
        r = call([{"jsonrpc": "2.0", "id": j, "method": "eth_getBlockByNumber", "params": [hex(b), False]} for j, b in enumerate(chunk)])
        got = {}
        if isinstance(r, list):
            for x in r:
                if x.get("result"):
                    got[hex(chunk[x["id"]])] = int(x["result"]["timestamp"], 16)
        else:
            for b in chunk:
                x = call({"jsonrpc": "2.0", "id": 1, "method": "eth_getBlockByNumber", "params": [hex(b), False]})
                if x and x.get("result"):
                    got[hex(b)] = int(x["result"]["timestamp"], 16)
                time.sleep(0.1)
        with lock:
            new.update(got); done[0] += 1
            if done[0] % 10 == 0:
                json.dump(new, open(OUT + ".tmp", "w")); os.replace(OUT + ".tmp", OUT); print("anchors", len(new), "chunks", done[0], "/", len(chunks), file=sys.stderr, flush=True)
        time.sleep(0.2)
ths = [threading.Thread(target=worker, args=(k,)) for k in range(3)]
for t in ths: t.start()
for t in ths: t.join()
json.dump(new, open(OUT + ".tmp", "w")); os.replace(OUT + ".tmp", OUT)
ts = sorted(new.values()); print("DONE", len(new), "anchors, span", time.strftime("%m-%d %H:%M", time.gmtime(ts[0])), "->", time.strftime("%m-%d %H:%M", time.gmtime(ts[-1])), file=sys.stderr, flush=True)
