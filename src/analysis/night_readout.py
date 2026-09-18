"""night_readout.py: where did the wallet's ETH go since the engine last started?

    sudo python3 src/analysis/night_readout.py [/var/log/sniper/engine.jsonl] [--start-eth 0.03573] [--eth-usd 2630]

Reads every event since the last `start`, collects every hash the engine sent (burst shots, approves, sells, retries),
pulls the receipts and the transactions from the chain (batched, public RPC by default) and prints, launch by launch:
the shots that landed and where, the fills, the ETH that left the wallet (buy values), the ETH that came back (the
curve's Sell event), the gas of every transaction, the net, the exit reason and whether the position is still open.
Then the totals, the alarms and errors with their times, the open position from the state file, and the sum against
the wallet's measured change when --start-eth is given. Nothing is estimated: every number is a receipt."""
import sys, json, ssl, http.client, urllib.parse, argparse, datetime, collections, os, time

BUY_EV = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"
SELL_EV = "0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"
UA = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}


class Rpc:
    def __init__(self, url):
        u = urllib.parse.urlparse(url); self.host = u.netloc; self.path = u.path or "/"; self.c = None; self.ctx = ssl.create_default_context()

    def batch(self, calls):
        """calls: list of (method, params); returns results in order (None where the node answered with an error).
        The public RPC allows about five requests a second: small batches, a pause between them, and a backoff on 429."""
        out = []
        for i in range(0, len(calls), 5):
            chunk = calls[i:i + 5]
            body = json.dumps([{"jsonrpc": "2.0", "id": k, "method": m, "params": p} for k, (m, p) in enumerate(chunk)])
            for attempt in range(8):
                try:
                    if self.c is None:
                        self.c = http.client.HTTPSConnection(self.host, timeout=20, context=self.ctx)
                    self.c.request("POST", self.path, body=body, headers=UA)
                    resp = self.c.getresponse(); raw = resp.read()
                    if resp.status == 429:
                        raise RuntimeError("429")
                    d = json.loads(raw)
                    if isinstance(d, dict):
                        raise RuntimeError(d.get("error", d))
                    byid = {x["id"]: x.get("result") for x in d}; out.extend(byid.get(k) for k in range(len(chunk))); break
                except Exception as e:
                    self.c = None
                    if attempt == 7:
                        raise RuntimeError(f"rpc failed: {e}")
                    time.sleep(1.5 * (attempt + 1) if "429" in str(e) else 0.5)
            time.sleep(0.3)
        return out


def words(data):
    d = data[2:]; return [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]


def t_str(t):
    return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%H:%M:%S")


def read(log_path):
    ev = []
    for line in open(log_path):
        if not line.startswith("{"):
            continue
        try:
            ev.append(json.loads(line))
        except Exception:
            pass
    starts = [e for e in ev if e.get("ev") == "start"]
    if not starts:
        sys.exit("no start event in the log")
    t0 = starts[-1]["t"]; since = [e for e in ev if e.get("t", 0) >= t0]
    return starts[-1], since


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("log", nargs="?", default="/var/log/sniper/engine.jsonl")
    ap.add_argument("--rpc", default="https://rpc.mainnet.chain.robinhood.com"); ap.add_argument("--start-eth", type=float, default=None)
    ap.add_argument("--eth-usd", type=float, default=None); a = ap.parse_args()
    start, since = read(a.log); px = a.eth_usd or (start.get("eth_usd") or 0)
    if not px:
        px = next((e["eth_usd"] for e in reversed(since) if e.get("eth_usd")), 0) or 0
    usd = (lambda e: f" (${e * px:+,.2f})") if px else (lambda e: "")
    print(f"since the engine started at {t_str(start['t'])} UTC on {datetime.datetime.fromtimestamp(start['t'], datetime.timezone.utc).date()} (engine {start.get('version')}, stake ${start.get('stake', '?')})")
    L = collections.OrderedDict()                                       # curve -> launch record
    def rec(curve):
        return L.setdefault(curve, dict(t=None, shots=[], landing=None, dones=[], approve=[], sells=[], alarms=[], events=[]))
    for e in since:
        c = e.get("curve"); k = e.get("ev")
        if not c:
            continue
        r = rec(c)
        if k == "trade_decision":
            r["t"] = e["t"]; r["decision"] = e
        elif k == "burst_shots":
            r["shots"] = e["hashes"]; r["t"] = r["t"] or e["t"]
        elif k == "burst_landing":
            r["landing"] = e
        elif k == "trade_done":
            r["dones"].append(e)
            if e.get("approve_hash"): r["approve"].append(e["approve_hash"])
            if e.get("sell_hash"): r["sells"].append(e["sell_hash"])
        elif k == "sell_reverted" and e.get("hash"):
            r["sells"].append(e["hash"])
        elif k == "alarm":
            r["alarms"].append(e)
            if e.get("sell_hash"): r["sells"].append(e["sell_hash"])
        elif k in ("buy_reverted", "buy_rejected", "receipt_timeout", "token_resolved_at_exit", "landing", "score"):
            r["events"].append(e)
    hashes = []
    for r in L.values():
        hashes += r["shots"] + list(dict.fromkeys(r["approve"])) + list(dict.fromkeys(r["sells"]))
    hashes = list(dict.fromkeys(h for h in hashes if h))
    rpc = Rpc(a.rpc)
    print(f"fetching {len(hashes)} receipts from {a.rpc} ...", flush=True)
    recs = dict(zip(hashes, rpc.batch([("eth_getTransactionReceipt", [h]) for h in hashes])))
    landed = [h for h in hashes if recs.get(h)]
    txs = dict(zip(landed, rpc.batch([("eth_getTransactionByHash", [h]) for h in landed])))
    wallet = None
    tot = collections.Counter(); n_fill_launch = 0; n_bursts = 0; nets = []
    print()
    for c, r in L.items():
        if not r["shots"] and not r["dones"]:
            continue
        n_bursts += 1 if r["shots"] else 0
        eth_in = eth_out = gas = 0.0; fills = []; by_block = collections.defaultdict(list); n_landed = 0
        for h in r["shots"]:
            rc = recs.get(h)
            if not rc:
                continue
            n_landed += 1; g = int(rc["gasUsed"], 16) * int(rc.get("effectiveGasPrice", "0x0"), 16) / 1e18; gas += g
            b = int(rc["blockNumber"], 16); ix = int(rc["transactionIndex"], 16); ok = rc.get("status") == "0x1"
            by_block[b].append((ix, ok)); wallet = wallet or rc["from"].lower()
            if ok:
                v = int(txs[h]["value"], 16) / 1e18; eth_in += v; fills.append((b, ix, v))
        sold_hashes = list(dict.fromkeys(r["sells"])); sell_ok = None; sell_block = None
        for h in list(dict.fromkeys(r["approve"])) + sold_hashes:
            rc = recs.get(h)
            if not rc:
                continue
            gas += int(rc["gasUsed"], 16) * int(rc.get("effectiveGasPrice", "0x0"), 16) / 1e18
            if h in sold_hashes:
                sell_ok = rc.get("status") == "0x1" if sell_ok is not True else sell_ok
                for l in rc.get("logs", []):
                    if l["topics"][0] == SELL_EV and l["address"].lower() == c.lower():
                        eth_out += words(l["data"])[1] / 1e18; sell_block = int(rc["blockNumber"], 16)
        net = eth_out - eth_in - gas; nets.append(net) if fills else None
        tot["eth_in"] += eth_in; tot["eth_out"] += eth_out; tot["gas"] += gas; tot["net"] += net; n_fill_launch += bool(fills)
        when = t_str(r["t"]) if r["t"] else "?"
        blocks = " ".join(f"b{b - min(by_block)}:{len(v)}sh,idx{min(i for i, _ in v)}" + ("" if not any(ok for _, ok in v) else f",FILL@{','.join(str(i) for i, ok in sorted(v) if ok)}") for b, v in sorted(by_block.items())) if by_block else "none landed"
        print(f"{when} launch {c[:10]}  shots landed {n_landed}/{len(r['shots'])}  [{blocks}]")
        if fills:
            ret = (eth_out - gas) / eth_in - 1 if eth_in else 0
            state = "sold" if eth_out else ("SELL REVERTED, tokens still held" if sell_ok is False else ("NOT SOLD, tokens still held" if not sold_hashes else "sell sent, no receipt"))
            print(f"           fills {len(fills)} (${eth_in * px:.2f} in)  ETH in {eth_in:.5f}  out {eth_out:.5f}  gas {gas:.6f}  net {net:+.5f} ETH{usd(net)}  return {100 * ret:+.1f}%  {state}"
                  + (f"  held {sell_block - fills[0][0]} blocks" if sell_block else "") + (f"  exit: {r['dones'][-1].get('exit')}" if r["dones"] else ""))
        else:
            print(f"           no fill  gas {gas:.6f} ETH{usd(-gas)}" + (f"  ({r['events'][-1]['ev']}: {r['events'][-1].get('note', '')})" if r["events"] and r["events"][-1]["ev"] in ("buy_reverted", "buy_rejected") else ""))
        for al in r["alarms"]:
            print(f"           ALARM {t_str(al['t'])}: {al['what']}")
    print()
    print(f"totals: bursts {n_bursts}, launches filled {n_fill_launch}, ETH in {tot['eth_in']:.5f}, ETH out {tot['eth_out']:.5f}, gas {tot['gas']:.6f} ETH{usd(-tot['gas'])}, net {tot['net']:+.5f} ETH{usd(tot['net'])}")
    if nets:
        print(f"per filled launch: " + ", ".join(f"{n:+.5f}" for n in nets) + f" ETH; mean {sum(nets) / len(nets):+.5f}, worst {min(nets):+.5f}")
    if a.start_eth is not None and wallet:
        bal = rpc.batch([("eth_getBalance", [wallet, "latest"])])[0]; now = int(bal, 16) / 1e18
        print(f"wallet: {a.start_eth:.5f} ETH at the start, {now:.5f} ETH now, change {now - a.start_eth:+.5f} ETH{usd(now - a.start_eth)}; receipts explain {tot['net']:+.5f} ETH, unexplained {now - a.start_eth - tot['net']:+.5f} ETH")
    others = [e for e in since if e.get("ev") in ("alarm", "error", "feed_stall", "feed_error") and not e.get("curve")]
    if others:
        print("\nother alarms and errors:")
        for e in others:
            print(f"  {t_str(e['t'])} {e['ev']}: {e.get('what') or e.get('err') or e.get('note') or ''}"[:220])
    sp = a.log + ".state.json"
    if os.path.exists(sp):
        try:
            st = json.load(open(sp)); op = st.get("open")
            print("\nopen position in the state file: " + (f"curve {op['curve']} tokens {op.get('tokens')} buy {op.get('buy_hash')} sell {op.get('sell_hash')}" if op else "none"))
        except Exception as e:
            print(f"\nstate file unreadable: {e}")


if __name__ == "__main__":
    main()
