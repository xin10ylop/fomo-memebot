#!/usr/bin/env python3
"""seq_probe.py: how long the sequencer's transaction intake holds a burst, measured with harmless transactions.

    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/seq_probe.py [burst_n=35] [step_ms=3]

Reads SHOOTER_KEYS, SEQ_URL and RPC_URL from /etc/sniper/engine.env (keys are never printed). Sends first a control of five
zero-value self-transfers 500 ms apart, then a burst of burst_n of them step_ms apart, one warm HTTPS socket per shot to the
sequencer, exactly as the engine's burst does. For every shot: the sequencer's reply time to eth_sendRawTransaction, and the
block it landed in against the head at the send. Cost: 21,000 gas a shot (about $0.01 at 0.1 gwei)."""
import os, sys, json, time, threading, http.client, ssl, urllib.request, statistics as st
from urllib.parse import urlparse
from eth_account import Account
ENV = "/etc/sniper/engine.env"; N = int(sys.argv[1]) if len(sys.argv) > 1 else 35; STEP = (float(sys.argv[2]) if len(sys.argv) > 2 else 3.0) / 1000.0
e = {}
for line in open(ENV):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); e[k.strip()] = v.strip().strip('"').strip("'")
keys = [k for k in e.get("SHOOTER_KEYS", "").split(",") if k.strip()]; SEQ = e.get("SEQ_URL", "https://sequencer.mainnet.chain.robinhood.com"); RPC = e.get("RPC_URL", "https://rpc.mainnet.chain.robinhood.com")
if len(keys) < N + 5: sys.exit(f"need {N + 5} shooter keys, have {len(keys)}: lower burst_n")
def rpc(url, m, p):
    r = urllib.request.urlopen(urllib.request.Request(url, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(), headers={"Content-Type": "application/json"}), timeout=20)
    return json.load(r).get("result")
u = urlparse(SEQ); host = u.hostname; port = u.port or 443; path = u.path or "/"; ctx = ssl.create_default_context()
gp = int(rpc(RPC, "eth_gasPrice", []), 16) * 2; accts = [Account.from_key(k) for k in keys[: N + 5]]
print(f"sequencer {host}, gas price x2 = {gp / 1e9:.3f} gwei, {N + 5} shooters (5 control + {N} burst), step {STEP * 1000:.0f} ms")
bodies = []
for a in accts:
    nonce = int(rpc(RPC, "eth_getTransactionCount", [a.address, "pending"]), 16)
    tx = {"to": a.address, "value": 0, "data": b"", "gas": 21_000, "gasPrice": gp, "nonce": nonce, "chainId": 4663}
    raw = "0x" + bytes(a.sign_transaction(tx).raw_transaction).hex()
    bodies.append(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_sendRawTransaction", "params": [raw]}).encode())
def connect():
    c = http.client.HTTPSConnection(host, port, timeout=20, context=ctx); c.connect(); return c
def fire(c, body, rec):
    t0 = time.monotonic(); c.request("POST", path, body=body, headers={"Content-Type": "application/json", "User-Agent": "seq-probe"}); rec["write_ms"] = round(1000 * (time.monotonic() - t0), 2)
    def read():
        try: d = json.loads(c.getresponse().read())
        except Exception as ex: d = {"error": str(ex)[:100]}
        rec["reply_ms"] = round(1000 * (time.monotonic() - t0), 1); rec["hash"] = d.get("result"); rec["err"] = (d.get("error") or {}).get("message") if isinstance(d.get("error"), dict) else d.get("error")
    threading.Thread(target=read, daemon=True).start()
def landing(recs, head0, label):
    deadline = time.time() + 20
    while time.time() < deadline and any(r.get("hash") and r.get("block") is None for r in recs):
        for r in recs:
            if r.get("hash") and r.get("block") is None:
                rc = rpc(RPC, "eth_getTransactionReceipt", [r["hash"]])
                if rc: r["block"] = int(rc["blockNumber"], 16); r["status"] = rc["status"]
        time.sleep(0.5)
    rep = [r["reply_ms"] for r in recs if r.get("reply_ms") is not None]; blk = [r["block"] - head0 for r in recs if r.get("block") is not None]
    print(f"\n{label}: {len(recs)} shots; sequencer reply ms: median {st.median(rep):.0f}, min {min(rep):.0f}, max {max(rep):.0f}; errors {sum(1 for r in recs if r.get('err'))}"
          f"\n  landed {len(blk)} of {len(recs)}; blocks after the head at the send: median {st.median(blk) if blk else '-'}, min {min(blk) if blk else '-'}, max {max(blk) if blk else '-'}"
          f" (about 10 blocks a second; a shot the intake holds 1.4 s lands 14 blocks late)")
    for r in recs[:5]: print(f"   write {r.get('write_ms')} ms, reply {r.get('reply_ms')} ms, block +{(r.get('block') - head0) if r.get('block') is not None else '-'}, err {r.get('err')}")
# control: five shots 500 ms apart, one socket each
conns = [connect() for _ in range(5)]; recs = [{} for _ in range(5)]; head0 = int(rpc(RPC, "eth_blockNumber", []), 16)
for i in range(5):
    fire(conns[i], bodies[i], recs[i]); time.sleep(0.5)
time.sleep(3); landing(recs, head0, "CONTROL (5 shots, 500 ms apart)")
# the burst: N warm sockets, step ms apart
conns = [connect() for _ in range(N)]; recs = [{} for _ in range(N)]; head0 = int(rpc(RPC, "eth_blockNumber", []), 16); t = time.monotonic()
for i in range(N):
    while time.monotonic() < t + i * STEP: pass
    fire(conns[i], bodies[5 + i], recs[i])
time.sleep(3); landing(recs, head0, f"BURST ({N} shots, {STEP * 1000:.0f} ms apart)")
