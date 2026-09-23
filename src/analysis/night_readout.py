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


def read(log_path, t_from=None, t_to=None):
    """all rotated copies of the log too (engine.jsonl, .1, .2.gz, ...); the window is the last start by default, or
    --from/--to (UTC), whose header start is the last one before the window"""
    import glob, gzip
    ev = []
    for f in sorted((f for f in glob.glob(log_path + "*") if not f.endswith(".state.json")), key=os.path.getmtime):
        with (gzip.open if f.endswith(".gz") else open)(f, "rt", errors="replace") as fh:
            for line in fh:
                if not line.startswith("{"):
                    continue
                try:
                    ev.append(json.loads(line))
                except Exception:
                    pass
    ev.sort(key=lambda e: e.get("t", 0))
    starts = [e for e in ev if e.get("ev") == "start"]
    if not starts:
        sys.exit("no start event in the log")
    if t_from is None:
        t0 = starts[-1]["t"]; since = [e for e in ev if e.get("t", 0) >= t0]; return starts[-1], since, ev
    start = next((s for s in reversed(starts) if s["t"] <= t_from), starts[0])
    since = [e for e in ev if t_from <= e.get("t", 0) <= (t_to or 9e18)]
    return start, since, ev


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("log", nargs="?", default="/var/log/sniper/engine.jsonl")
    ap.add_argument("--rpc", default="https://rpc.mainnet.chain.robinhood.com"); ap.add_argument("--start-eth", type=float, default=None)
    ap.add_argument("--eth-usd", type=float, default=None)
    ap.add_argument("--from", dest="t_from", default=None, help="UTC 'YYYY-MM-DD HH:MM': account this window instead of the last start")
    ap.add_argument("--to", dest="t_to", default=None); a = ap.parse_args()
    utc = lambda x: datetime.datetime.strptime(x, "%Y-%m-%d %H:%M").replace(tzinfo=datetime.timezone.utc).timestamp() if x else None
    start, since, ev_all = read(a.log, utc(a.t_from), utc(a.t_to)); px = a.eth_usd or (start.get("eth_usd") or 0)
    if not px:
        px = next((e["eth_usd"] for e in reversed(since) if e.get("eth_usd")), 0) or 0
    if not px:
        try:
            import urllib.request
            px = float(json.load(urllib.request.urlopen("https://api.coinbase.com/v2/prices/ETH-USD/spot", timeout=10))["data"]["amount"])
        except Exception:
            px = 0
    usd = (lambda e: f" (${e * px:+,.2f})") if px else (lambda e: "")
    if a.t_from: print(f"window {a.t_from} to {a.t_to or 'now'} UTC; the start before it:")
    print(f"since the engine started at {t_str(start['t'])} UTC on {datetime.datetime.fromtimestamp(start['t'], datetime.timezone.utc).date()} (engine {start.get('version')}, stake ${start.get('stake', '?')})")
    L = collections.OrderedDict()                                       # curve -> launch record
    def rec(curve):
        return L.setdefault(curve, dict(t=None, shots=[], landing=None, dones=[], approve=[], sells=[], alarms=[], events=[], answers=[], sent=None))
    last_curve = None; by_hash = {}; pending_sent = None; transfers = [e for e in since if e.get("ev") == "sent_tx" and e.get("label") in ("relay_float", "shooter_gas") and e.get("hash")]
    for e in since:
        c = e.get("curve"); k = e.get("ev")
        if k == "resend" and last_curve:
            rec(last_curve)["events"].append(e); continue
        if k == "sent_burst":
            pending_sent = e; continue
        if k == "send_answers" and e.get("hash") in by_hash:
            rec(by_hash[e["hash"]])["answers"].append(e); continue
        if not c:
            continue
        if k == "trade_decision":
            last_curve = c
            if pending_sent is not None and abs(pending_sent["t"] - e["t"]) < 3:
                rec(c)["sent"] = pending_sent; pending_sent = None
        r = rec(c)
        if k == "trade_decision":
            r["t"] = e["t"]; r["decision"] = e
        elif k == "burst_shots":
            r["shots"] = e["hashes"]; r["t"] = r["t"] or e["t"]
            for hh in e["hashes"]:
                by_hash[hh] = c
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
        elif k in ("buy_reverted", "buy_rejected", "receipt_timeout", "token_resolved_at_exit", "landing", "score", "approve_not_seen", "approve_missing", "sell_reverted"):
            r["events"].append(e)
    hashes = []
    for r in L.values():
        hashes += r["shots"] + list(dict.fromkeys(r["approve"])) + list(dict.fromkeys(r["sells"]))
    hashes = list(dict.fromkeys(h for h in hashes if h)) + [e["hash"] for e in transfers]
    rpc = Rpc(a.rpc)
    print(f"fetching {len(hashes)} receipts from {a.rpc} ...", flush=True)
    recs = dict(zip(hashes, rpc.batch([("eth_getTransactionReceipt", [h]) for h in hashes])))
    landed = [h for h in hashes if recs.get(h)]
    txs = dict(zip(landed, rpc.batch([("eth_getTransactionByHash", [h]) for h in landed])))
    wallet = (start.get("wallet") or "").lower() or None
    ours_blocks = {int(recs[h]["blockNumber"], 16) for r in L.values() for h in r["shots"] if recs.get(h)}
    blocks_needed = sorted(ours_blocks | {b - 1 for b in ours_blocks})
    blocks = dict(zip(blocks_needed, rpc.batch([("eth_getBlockByNumber", [hex(b), False]) for b in blocks_needed])))
    spans = {c: (min(int(recs[h]["blockNumber"], 16) for h in r["shots"] if recs.get(h)), max(int(recs[h]["blockNumber"], 16) for h in r["shots"] if recs.get(h)))
             for c, r in L.items() if any(recs.get(h) for h in r["shots"])}
    buys = dict(zip(spans, rpc.batch([("eth_getLogs", [{"address": c, "fromBlock": hex(lo - 60), "toBlock": hex(hi), "topics": [BUY_EV]}]) for c, (lo, hi) in spans.items()])))
    cblocks = {c: min(int(l["blockNumber"], 16) for l in (buys.get(c) or [])) for c in spans if buys.get(c)}          # the creation block carries the bundle's first buys
    cts = dict(zip(cblocks, [int(b["timestamp"], 16) if b else None for b in rpc.batch([("eth_getBlockByNumber", [hex(b), False]) for b in cblocks.values()])]))
    tot = collections.Counter(); n_fill_launch = 0; n_bursts = 0; nets = []; firsts = []
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
                v = int(txs[h]["value"], 16) / 1e18
                bl_ = [words(l["data"]) for l in rc.get("logs", []) if l["topics"][0] == BUY_EV and l["address"].lower() == c.lower()]
                tk = sum(w_[1] for w_ in bl_) / 1e18
                if v == 0 and bl_:                                            # a shooter's shot: the relay paid; the curve's Buy event carries the ETH it took
                    v = sum(w_[0] for w_ in bl_) / 1e18
                eth_in += v; fills.append((b, ix, v, tk))
        sold_hashes = list(dict.fromkeys(r["sells"])); sell_ok = None; sell_block = None; tokens_sold = 0.0
        for h in list(dict.fromkeys(r["approve"])) + sold_hashes:
            rc = recs.get(h)
            if not rc:
                continue
            gas += int(rc["gasUsed"], 16) * int(rc.get("effectiveGasPrice", "0x0"), 16) / 1e18
            if h in sold_hashes:
                sell_ok = rc.get("status") == "0x1" if sell_ok is not True else sell_ok
                for l in rc.get("logs", []):
                    if l["topics"][0] == SELL_EV and l["address"].lower() == c.lower():
                        w_ = words(l["data"]); eth_out += w_[1] / 1e18; tokens_sold += w_[0] / 1e18; sell_block = int(rc["blockNumber"], 16)   # word 2 is what the wallet receives; words 3-4 are the fees already taken out (checked against sellers' balance changes, Sep 19)
        net = eth_out - eth_in - gas; nets.append(net) if fills else None
        tot["eth_in"] += eth_in; tot["eth_out"] += eth_out; tot["gas"] += gas; tot["net"] += net; n_fill_launch += bool(fills)
        when = t_str(r["t"]) if r["t"] else "?"
        seat_ts = (r.get("decision") or {}).get("seat_ts") or (r["dones"][-1].get("seat_ts") if r["dones"] else None)
        c_ts = cts.get(c); feed_note = ""
        if c_ts is not None and seat_ts is not None and c_ts + 1 != seat_ts:
            feed_note = f"  [the engine's clock read the creation as second {seat_ts - 1}, the chain says {c_ts}: {seat_ts - 1 - c_ts:+d} s]"
        parts = []
        for b, v in sorted(by_block.items()):
            blk = blocks.get(b) or {}; ts = int(blk["timestamp"], 16) if blk else None; first = min(i for i, _ in v)
            if ts is None or c_ts is None:
                sec = "?"
            else:
                d_ = ts - c_ts; sec = "creation-second" if d_ == 0 else ("SEAT" if d_ == 1 else (f"seat+{d_ - 1}s" if d_ > 1 else f"before creation ({d_} s)"))
                if d_ == 1 and b > cblocks.get(c, b) and blocks.get(b - 1) and int(blocks[b - 1]["timestamp"], 16) == ts:
                    sec = "SEAT (not its first block)"
            ours = {i for i, _ in v}
            bl = [l for l in (buys.get(c) or []) if int(l["blockNumber"], 16) == b and int(l["transactionIndex"], 16) not in ours and (wallet is None or l["topics"][2][-40:] != wallet[-40:])]
            ahead = [l for l in bl if int(l["transactionIndex"], 16) < first]; after = [l for l in bl if int(l["transactionIndex"], 16) > first]
            ahead_eth = sum(words(l["data"])[0] for l in ahead) / 1e18; after_eth = sum(words(l["data"])[0] for l in after) / 1e18
            parts.append(f"{sec}: {len(v)} shots from idx {first}, " + (f"{len(ahead)} buy{'s' if len(ahead) != 1 else ''} ahead ({ahead_eth:.3f} ETH)" if ahead else "no buy ahead")
                         + (f", {len(after)} behind ({after_eth:.3f} ETH)" if after else ", nobody behind") + (f", FILL@{','.join(str(i) for i, ok in sorted(v) if ok)}" if any(ok for _, ok in v) else ""))
        print(f"{when} launch {c}  shots landed {n_landed}/{len(r['shots'])}  " + " | ".join(parts) + feed_note if parts else f"{when} launch {c}  no shot landed")
        lost = [h for h in r["shots"] if not recs.get(h)]
        if lost:
            ans = collections.Counter()
            for ans_ev in r["answers"]:
                if ans_ev.get("hash") in lost:
                    for _, txt in ans_ev.get("answers") or []:
                        ans[txt.split("'message': ")[-1][:70] if "'message': " in txt else txt[:70]] += 1
            idx = [r["shots"].index(h) for h in lost]
            print(f"           LOST {len(lost)} shots (never on the chain): shots {min(idx)}-{max(idx)}; the sequencer answered: " + ("; ".join(f"{n}x {t}" for t, n in ans.most_common(4)) if ans else "no answer recorded"))
        dc_ = r.get("decision") or {}; sb = r.get("sent") or {}; ld_ = r.get("landing") or {}
        if r["shots"] and (dc_ or sb or ld_):
            def nums(x):
                return [x] if isinstance(x, (int, float)) else [v for y in x for v in nums(y)] if isinstance(x, (list, tuple)) else []
            replies = [v for a in r["answers"] for v in nums(a.get("reply_ms"))]
            fk = next((i for i, h in enumerate(r["shots"]) if recs.get(h) and recs[h].get("status") == "0x1"), None)
            seat_first = min((i for i, h in enumerate(r["shots"]) if recs.get(h) and c_ts is not None and blocks.get(int(recs[h]["blockNumber"], 16)) and int(blocks[int(recs[h]["blockNumber"], 16)]["timestamp"], 16) > c_ts), default=None)
            print(f"           window: the seat's block opened at shot {seat_first if seat_first is not None else 'none (all before it)'} of {len(r['shots'])}" + (f", the fill was shot {fk}" if fk is not None else ""))
            print(f"           send: aimed {dc_.get('burst_at_ms')} ms after the creation was seen ({dc_.get('target_model')}, built {dc_.get('build_lead_ms')} ms before), shots fired late by up to {max(sb.get('late_ms') or [0]):.1f} ms"
                  + (f", sequencer replies up to {max(replies):.0f} ms" if replies else "") + (f"; flip minus first shot {ld_.get('flip_minus_first_shot_ms')} ms, flip minus first fill {ld_.get('flip_minus_first_fill_ms')} ms" if ld_ else ""))
        if fills:
            ret = (eth_out - gas) / eth_in - 1 if eth_in else 0
            state = "sold" if eth_out else ("SELL REVERTED, tokens still held" if sell_ok is False else ("NOT SOLD, tokens still held" if not sold_hashes else "sell sent, no receipt"))
            print(f"           fills {len(fills)} (${eth_in * px:.2f} in)  ETH in {eth_in:.5f}  out {eth_out:.5f}  gas {gas:.6f}  net {net:+.5f} ETH{usd(net)}  return {100 * ret:+.1f}%  {state}"
                  + (f"  held {sell_block - fills[0][0]} blocks" if sell_block else "") + (f" ({r['dones'][-1].get('held_s')} s)" if r["dones"] and r["dones"][-1].get("held_s") is not None else "") + (f"  exit: {r['dones'][-1].get('exit')}" if r["dones"] else ""))
            dn = r["dones"][-1] if r["dones"] else None; dc = r.get("decision"); ld = r.get("landing")
            if dn and dc and dn.get("held_s") is not None:
                t_buy = dn["t"] - dn["held_s"]
                print(f"           timeline: decision->buy clock {1000 * (t_buy - dc['t']):.0f} ms" + (f", buy clock->landing logged {1000 * (ld['t'] - t_buy):.0f} ms" if ld else "")
                      + f", held {dn['held_s']} s of which the sell took {dn.get('sell_confirm_s', '?')} s" + (f"  (note: {dn['note']})" if dn.get("note") else ""))
                exit_ev = [e for e in r["events"] if e["ev"] in ("approve_not_seen", "approve_missing", "resend", "sell_reverted", "receipt_timeout", "token_resolved_at_exit")]
                if exit_ev:
                    print("           exit events: " + "; ".join(f"{e['ev']} at +{e['t'] - t_buy:.2f} s" + (f" (attempt {e.get('attempt')}, {e.get('label')})" if e["ev"] == "resend" else "") for e in exit_ev))
            if len(fills) > 1 and eth_out and tokens_sold:
                b0, i0, v0, tk0 = fills[0]; own = (tk0 / tokens_sold * eth_out) / v0 - 1 if v0 else 0.0; firsts.append(own)
                print(f"           the first fill alone (${v0 * px:.2f} at idx {i0}): {100 * own:+.1f}% on its own tokens; the other {len(fills) - 1} fills bought higher and are what a one-stake wallet would not have bought")
            elif fills:
                firsts.append(ret)
        else:
            print(f"           no fill  gas {gas:.6f} ETH{usd(-gas)}" + (f"  ({r['events'][-1]['ev']}: {r['events'][-1].get('note', '')})" if r["events"] and r["events"][-1]["ev"] in ("buy_reverted", "buy_rejected") else ""))
        for al in r["alarms"]:
            print(f"           ALARM {t_str(al['t'])}: {al['what']}")
    print()
    print(f"totals: bursts {n_bursts}, launches filled {n_fill_launch}, ETH in {tot['eth_in']:.5f}, ETH out {tot['eth_out']:.5f}, gas {tot['gas']:.6f} ETH{usd(-tot['gas'])}, net {tot['net']:+.5f} ETH{usd(tot['net'])}")
    if nets:
        print(f"per filled launch: " + ", ".join(f"{n:+.5f}" for n in nets) + f" ETH; mean {sum(nets) / len(nets):+.5f}, worst {min(nets):+.5f}")
        print(f"first-fill returns (what one stake per launch would have made): " + ", ".join(f"{100 * x:+.1f}%" for x in firsts) + f"; mean {100 * sum(firsts) / len(firsts):+.1f}%")
    moved = 0.0
    for e in transfers:
        rc = recs.get(e["hash"])
        if rc:
            v = int((txs.get(e["hash"]) or {}).get("value", "0x0"), 16) / 1e18; g = int(rc["gasUsed"], 16) * int(rc.get("effectiveGasPrice", "0x0"), 16) / 1e18
            moved += v + g; tot[e["label"]] += v
    if transfers:
        print(f"moved out of the wallet by the engine: {tot['relay_float']:.5f} ETH to the relay (its stake), {tot['shooter_gas']:.5f} ETH to shooters (gas); still yours, not a loss")
    if a.start_eth is not None and wallet and start.get("shooters"):        # the stake sits in the relay and the shots' gas in the shooters: reconcile the whole capital
        relay_ = start.get("relay"); sh_ev = [e for e in ev_all if e.get("ev") == "shooters"]
        addrs = (sh_ev[-1].get("addresses") or []) if sh_ev else []     # the engine logs them at start (6.02); before that, derive from the env when eth_account is at hand
        if not addrs:
            try:
                env_ = dict(l.split("=", 1) for l in open("/etc/sniper/engine.env").read().splitlines() if "=" in l and not l.startswith("#"))
                from eth_account import Account
                addrs = [Account.from_key(k.strip()).address for k in env_.get("SHOOTER_KEYS", "").split(",") if k.strip()]
            except Exception:
                pass
        bals = rpc.batch([("eth_getBalance", [x, "latest"]) for x in [wallet, relay_] + addrs])
        wnow = int(bals[0], 16) / 1e18; rnow = int(bals[1], 16) / 1e18; snow = sum(int(b, 16) for b in bals[2:]) / 1e18; now = wnow + rnow + snow
        xfer_gas = moved - tot["relay_float"] - tot["shooter_gas"]
        print(f"capital (wallet {wnow:.5f} + relay {rnow:.5f} + {len(addrs)} shooters {snow:.5f}): {a.start_eth:.5f} ETH at the start, {now:.5f} ETH now, change {now - a.start_eth:+.5f} ETH{usd(now - a.start_eth)}; trades explain {tot['net']:+.5f} ETH, transfer gas {-xfer_gas:+.6f}, unexplained {now - a.start_eth - tot['net'] + xfer_gas:+.5f} ETH")
    elif a.start_eth is not None and wallet:
        bal = rpc.batch([("eth_getBalance", [wallet, "latest"])])[0]; now = int(bal, 16) / 1e18
        print(f"wallet: {a.start_eth:.5f} ETH at the start, {now:.5f} ETH now, change {now - a.start_eth:+.5f} ETH{usd(now - a.start_eth)}; trades explain {tot['net']:+.5f} ETH, transfers {-moved:+.5f}, unexplained {now - a.start_eth - tot['net'] + moved:+.5f} ETH")
    shots_ev = [e for e in since if e.get("ev") == "burst_shots" and e.get("nonces")]
    if shots_ev and wallet and not start.get("shooters"):
        last = shots_ev[-1]; landed_n = [n for h, n in zip(last["hashes"], last["nonces"]) if recs.get(h)]
        expected = (max(landed_n) + 1 if landed_n else min(last["nonces"])) + (2 if any(e.get("ev") == "trade_done" and e.get("curve") == last["curve"] for e in since) else 0)
        n_chain = int(rpc.batch([("eth_getTransactionCount", [wallet, "latest"])])[0], 16)
        print(f"nonce: the chain says {n_chain} transactions from the wallet, the log accounts for {expected}" + ("" if n_chain == expected else f": {n_chain - expected} transaction(s) the log does not list"))
    relay = start.get("relay")
    if relay:
        rb = int(rpc.batch([("eth_getBalance", [relay, "latest"])])[0], 16) / 1e18
        print(f"relay {relay} holds {rb:.6f} ETH{usd(rb)}" + (" (the stake it buys with)" if start.get("shooters") else ("" if rb == 0 else " (withdraw it: deploy/relay_ops.py withdraw all)")))
    sh = [e for e in ev_all if e.get("ev") in ("shooters", "shooter_topup")]
    if start.get("shooters"):
        last_sh = [e for e in ev_all if e.get("ev") == "shooters"]
        if last_sh:
            print(f"shooters: {last_sh[-1]['n']}, {last_sh[-1]['low']} low on gas at the last check; refills since the start: {sum(1 for e in since if e.get('ev') == 'shooter_topup')}")
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
