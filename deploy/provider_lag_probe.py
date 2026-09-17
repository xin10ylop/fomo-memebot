"""How far behind the sequencer is the provider's WebSocket? Subscribes to newHeads on PROVIDER_WS and polls the sequencer's
HTTP eth_blockNumber every 20 ms; for every block seen by both, the lag is the provider's push time minus the sequencer's
first report. Run on the trading box for 60 s:  sudo python3 deploy/provider_lag_probe.py [seconds]
Reads PROVIDER_WS and SEQ_URL from /etc/sniper/engine.env when not in the environment."""
import asyncio, json, os, sys, time, threading, statistics as st, urllib.request
def env(k, default=None):
    if os.environ.get(k): return os.environ[k]
    try:
        for line in open("/etc/sniper/engine.env"):
            if line.startswith(k + "="): return line.split("=", 1)[1].strip()
    except Exception: pass
    return default
PROVIDER_WS = env("PROVIDER_WS"); ALCH_HTTP = env("RPC_URL")
REF = env("PUBLIC_RPC", "https://rpc.mainnet.chain.robinhood.com")      # Robinhood's own node as the reference clock (the sequencer endpoint serves transactions only)
SECONDS = float(sys.argv[1]) if len(sys.argv) > 1 else 60
if not PROVIDER_WS: raise SystemExit("PROVIDER_WS not set")
mono = time.monotonic; seq_seen = {}; ws_seen = {}; http_seen = {}; stop = mono() + SECONDS
H = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fomo-memebot/probe"}
def poll(url, store):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []}).encode()
    while mono() < stop:
        try:
            req = urllib.request.Request(url, data=body, headers=H); n = int(json.load(urllib.request.urlopen(req, timeout=2))["result"], 16); t = mono()
            store.setdefault(n, t)
        except Exception:
            pass
        time.sleep(0.02)
async def ws():
    import websockets
    async with websockets.connect(PROVIDER_WS, open_timeout=10, ping_interval=10, ping_timeout=5, compression=None) as w:
        await w.send(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_subscribe", "params": ["newHeads"]})); await w.recv()
        while mono() < stop:
            try:
                d = json.loads(await asyncio.wait_for(w.recv(), timeout=2.0))
            except asyncio.TimeoutError:
                continue
            if d.get("method") == "eth_subscription":
                ws_seen.setdefault(int(d["params"]["result"]["number"], 16), mono())
threads = [threading.Thread(target=poll, args=(REF, seq_seen), daemon=True)]
if ALCH_HTTP: threads.append(threading.Thread(target=poll, args=(ALCH_HTTP, http_seen), daemon=True))
for t in threads: t.start()
try:
    asyncio.run(ws())
except Exception as e:
    print("provider websocket failed:", str(e)[:160])
for t in threads: t.join(timeout=5)
def report(name, store):
    lags = sorted(1000 * (store[n] - seq_seen[n]) for n in store if n in seq_seen)
    if not lags: print(f"{name}: no common blocks"); return
    q = lambda p: lags[min(len(lags) - 1, int(p * len(lags)))]
    print(f"{name}: n {len(lags)} blocks | lag behind Robinhood's node: median {st.median(lags):+.0f} ms, p10 {q(0.1):+.0f}, p90 {q(0.9):+.0f}, max {lags[-1]:+.0f} ms")
print(f"blocks seen: Robinhood RPC {len(seq_seen)}, provider WS {len(ws_seen)}, provider HTTP {len(http_seen)} over {SECONDS:.0f} s")
report("provider WebSocket newHeads", ws_seen)
if http_seen: report("provider HTTP polling", http_seen)
print("reading: Robinhood's node is itself a few tens of ms behind the sequencer, and the poll adds up to 20 ms; a provider WebSocket lag under ~300 ms keeps the seat inside the replay's paying range; a negative lag means the provider is ahead of Robinhood's public node")
