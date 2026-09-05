#!/usr/bin/env python3
"""Latency probe for the first-block seat (report section 14). Read-only: no keys, no signing, no transactions.

Listens to the Robinhood Chain sequencer feed, detects Pons V2 creation transactions (factory 0xe33e..., selector 0xf85f8e41),
recovers the creator, quote asset and initial buy from the calldata, then measures how long it takes to resolve the new curve
address from the block's factory logs over the public RPC. That resolve time plus one block (100 ms) is the entry latency a
live bot would have from this host; the replays say the seat pays only if that lands in the first block or two after creation.
Logs JSON lines to LOG_PATH.
"""
import asyncio, base64, json, os, time, threading, http.client, urllib.parse, collections
import rlp
from eth_account import Account

RPC_URL = os.environ.get("RPC_URL", "https://rpc.mainnet.chain.robinhood.com")
FEED_URL = os.environ.get("FEED_URL", "wss://feed.mainnet.chain.robinhood.com")
LOG_PATH = os.environ.get("LOG_PATH", "sniper_detect_probe.jsonl")
FACTORY = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"
CREATE_SEL = bytes.fromhex("f85f8e41")
UA = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) fomo-memebot/probe"}

def log(ev):
    ev["t"] = time.time()
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(ev) + "\n")

class Rpc:
    def __init__(self, url):
        u = urllib.parse.urlparse(url); self.host = u.netloc; self.path = u.path or "/"; self.local = threading.local()
    def call(self, method, params):
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
        for i in range(3):
            try:
                c = getattr(self.local, "c", None)
                if c is None:
                    c = http.client.HTTPSConnection(self.host, timeout=10); self.local.c = c
                c.request("POST", self.path, body=body, headers=UA); r = c.getresponse(); d = json.loads(r.read())
                if "error" in d: raise RuntimeError(d["error"])
                return d["result"]
            except Exception:
                self.local.c = None
                if i == 2: raise
                time.sleep(0.03)

rpc = Rpc(RPC_URL)
launched_today = collections.Counter()

def resolve_curve(block, creator, seen_at):
    t0 = time.time(); curve = token = None; polls = 0
    while time.time() - t0 < 3.0:
        polls += 1
        try:
            # the feed header's blockNumber is the parent-chain block, not the L2 block: read the factory's newest events instead
            head = int(rpc.call("eth_blockNumber", []), 16)
            logs = rpc.call("eth_getLogs", [{"fromBlock": hex(head - 8), "toBlock": hex(head), "address": FACTORY}])
            for l in logs:
                if len(l["topics"]) > 3 and ("0x" + l["topics"][3][-40:]).lower() == creator:
                    token = "0x" + l["topics"][1][-40:]; curve = "0x" + l["topics"][2][-40:]; break
            if curve: break
        except Exception:
            pass
        time.sleep(0.02)
    now = time.time()
    log({"ev": "resolve", "block": block, "creator": creator, "curve": curve, "token": token, "polls": polls,
         "feed_to_resolve_ms": round((now - seen_at) * 1000), "resolve_ms": round((now - t0) * 1000)})

def decode_batch(l2msg_b64):
    raw = base64.b64decode(l2msg_b64)
    if not raw or raw[0] != 3: return []
    i = 1; out = []
    while i + 8 <= len(raw):
        ln = int.from_bytes(raw[i:i + 8], "big"); seg = raw[i + 8:i + 8 + ln]; i += 8 + ln
        if seg and seg[0] == 4: out.append(seg[1:])
    return out

async def main():
    import websockets
    while True:
        try:
            async with websockets.connect(FEED_URL, open_timeout=15, max_size=None, ping_interval=20) as ws:
                log({"ev": "feed_connected"})
                while True:
                    d = json.loads(await ws.recv()); seen = time.time()
                    for m in d.get("messages", []):
                        hdr = m["message"]["message"]["header"]; blk = hdr.get("blockNumber"); ts = hdr.get("timestamp")
                        for t in decode_batch(m["message"]["message"].get("l2Msg", "")):
                            try:
                                if t[0] != 2: continue
                                body = rlp.decode(t[1:]); to = body[5]; data = body[7]
                                if len(to) != 20 or "0x" + to.hex() != FACTORY or data[:4] != CREATE_SEL: continue
                                creator = Account.recover_transaction(t).lower()
                                quote = "0x" + data[4 + 32 * 2 + 12: 4 + 32 * 3].hex(); init_buy = int.from_bytes(data[4 + 32 * 3: 4 + 32 * 4], "big")
                                launched_today[creator] += 1
                                elig = quote == "0x" + "0" * 40 and launched_today[creator] == 1 and 0.005e18 <= init_buy <= 2e18
                                log({"ev": "creation", "block": blk, "seq_ts": ts, "feed_lag_ms": round((seen - ts) * 1000) if ts else None,
                                     "creator": creator, "quote": quote, "init_buy_eth": init_buy / 1e18, "prior_today": launched_today[creator] - 1, "eligible": elig})
                                if elig: threading.Thread(target=resolve_curve, args=(blk, creator, seen), daemon=True).start()
                            except Exception as e:
                                log({"ev": "error", "stage": "decode", "err": str(e)[:200]})
        except Exception as e:
            log({"ev": "feed_error", "err": str(e)[:200]}); await asyncio.sleep(2)

if __name__ == "__main__":
    print("probe running; log", LOG_PATH)
    asyncio.run(main())
