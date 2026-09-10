"""live_check.py: did the live trades do what the engine said they would?

    python3 src/analysis/live_check.py engine.jsonl [--rpc https://...] [--slip 0.25]

Reads the engine's log, takes every trade_done that carries a buy hash and a sell hash (the operator's send step returns
them), pulls the receipts from the chain, and for each trade computes what actually happened: ETH in and tokens out from
the buy's own Buy event, tokens in and ETH out from the sell's Sell event, gas from both receipts (and the approve's),
the live return, where the buy landed (block timestamp against the seat's second, transaction index), and the tokens
received against the engine's target. Then it puts the live return next to the engine's exact-curve score of the same
launch (the score event, computed the same way as the tables) and reports the gap with a bootstrap interval.

Runbook section 5's go/no-go, in numbers:
  - every buy landed in the seat's second (where = first block / later block, never early or next second);
  - tokens received within SLIP of tokens_target on every trade;
  - the sell moved the whole balance;
  - the mean live return over the first thirty trades inside the interval of the engine's scores for the same launches.
A gap between live and engine on the SAME launches is the box or the seat, not the market."""
import sys, json, ssl, http.client, urllib.parse, statistics as st, random, argparse, collections

BUY_EV = "0xec36bf571f136799e8dc0b0b8bea4b04d8bd3d43de838aab0d5fc21d4cbfc455"
SELL_EV = "0x8113d738abdcb6b38357e9d53a54a7157861a09031b453651f0fe7fe151f59df"
UA = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}


class Rpc:
    def __init__(self, url):
        u = urllib.parse.urlparse(url); self.host = u.netloc; self.path = u.path or "/"; self.c = None; self.ctx = ssl.create_default_context()

    def call(self, method, params):
        for i in range(3):
            try:
                if self.c is None:
                    self.c = http.client.HTTPSConnection(self.host, timeout=15, context=self.ctx)
                self.c.request("POST", self.path, body=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}), headers=UA)
                d = json.loads(self.c.getresponse().read())
                if "error" in d:
                    raise RuntimeError(d["error"])
                return d["result"]
            except Exception:
                self.c = None
                if i == 2:
                    raise


def words(data):
    d = data[2:]; return [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]


def receipt_cost(rpc, rec):
    gp = int(rec.get("effectiveGasPrice", "0x0"), 16); return int(rec["gasUsed"], 16) * gp / 1e18


def check(log_path, rpc_url, slip):
    rpc = Rpc(rpc_url); decisions = {}; scores = {}; dones = []
    for line in open(log_path):
        try:
            e = json.loads(line)
        except Exception:
            continue
        ev = e.get("ev")
        if ev == "trade_decision":
            decisions[e["curve"]] = e
        elif ev == "score" and "roi" in e:
            scores[e["curve"]] = e
        elif ev == "trade_done" and e.get("buy_hash") and e.get("sell_hash"):
            dones.append(e)
    if not dones:
        print("no trade_done with a buy hash and a sell hash in the log (dry run, or the send step does not return the hash)"); return
    rows = []
    for d in dones:
        curve = d["curve"]; dec = decisions.get(curve, {}); sc = scores.get(curve)
        rb = rpc.call("eth_getTransactionReceipt", [d["buy_hash"]]); rs = rpc.call("eth_getTransactionReceipt", [d["sell_hash"]])
        ra = rpc.call("eth_getTransactionReceipt", [d["approve_hash"]]) if d.get("approve_hash") else None
        if rb is None or rs is None:
            rows.append(dict(curve=curve, note="receipt missing (buy)" if rb is None else "receipt missing (sell)")); continue
        wallet = rb["from"].lower()
        eth_in = tokens_out = tokens_in = eth_out = None
        for l in rb.get("logs", []):
            if l["topics"][0] == BUY_EV and l["address"].lower() == curve.lower() and l["topics"][2][-40:] == wallet[-40:]:
                w = words(l["data"]); eth_in = w[0] / 1e18; tokens_out = w[1] / 1e18
        for l in rs.get("logs", []):
            if l["topics"][0] == SELL_EV and l["address"].lower() == curve.lower():
                w = words(l["data"]); tokens_in = w[0] / 1e18; eth_out = w[1] / 1e18
        gas = receipt_cost(rpc, rb) + receipt_cost(rpc, rs) + (receipt_cost(rpc, ra) if ra else 0.0)
        bb = int(rb["blockNumber"], 16); bs = int(rs["blockNumber"], 16)
        ts = int(rpc.call("eth_getBlockByNumber", [hex(bb), False])["timestamp"], 16); prev = int(rpc.call("eth_getBlockByNumber", [hex(bb - 1), False])["timestamp"], 16)
        seat_ts = d.get("seat_ts") or dec.get("seat_ts")
        if seat_ts is None:
            where = "unknown (no seat_ts)"
        elif ts < seat_ts:
            where = "EARLY (before the seat's second)"
        elif ts > seat_ts:
            where = f"LATE (+{ts - seat_ts} s)"
        else:
            where = "first block" if prev < ts else "later block"
        status_ok = rb.get("status") == "0x1" and rs.get("status") == "0x1"
        live = (eth_out - eth_in - gas) / eth_in if (eth_in and eth_out is not None) else None
        rows.append(dict(curve=curve, wallet=wallet, buy_block=bb, sell_block=bs, held_blocks=bs - bb, where=where, tx_index=int(rb.get("transactionIndex", "0x0"), 16), status_ok=status_ok,
                         eth_in=eth_in, tokens=tokens_out, target=dec.get("tokens_target"), tokens_sold=tokens_in, eth_out=eth_out, gas_eth=gas, live=live,
                         engine=sc["roi"] if sc else None, engine_cost=sc["cost_usd"] if sc else None, exit=d.get("exit"), held_s=d.get("held_s")))
    print(f"{'curve':12s} {'landed':32s} {'idx':>3s} {'blocks':>6s} {'ETH in':>8s} {'tokens':>13s} {'vs target':>9s} {'sold':>7s} {'ETH out':>8s} {'gas':>7s} {'live':>7s} {'engine':>7s} {'gap':>7s} exit")
    live_v = []; eng_v = []; problems = collections.Counter()
    for r in rows:
        if "note" in r:
            print(f"{r['curve'][:12]} {r['note']}"); problems["missing receipt"] += 1; continue
        vt = (r["tokens"] / r["target"] - 1) if (r["target"] and r["tokens"]) else None
        sold = (r["tokens_sold"] / r["tokens"]) if (r["tokens"] and r["tokens_sold"] is not None) else None
        gap = (r["live"] - r["engine"]) if (r["live"] is not None and r["engine"] is not None) else None
        print(f"{r['curve'][:12]} {r['where']:32s} {r['tx_index']:3d} {r['held_blocks']:6d} {r['eth_in'] or 0:8.4f} {r['tokens'] or 0:13,.0f} {('%+.1f%%' % (100*vt)) if vt is not None else '-':>9s} {('%.0f%%' % (100*sold)) if sold is not None else '-':>7s} {r['eth_out'] or 0:8.4f} {r['gas_eth']:7.5f} {('%+.1f%%' % (100*r['live'])) if r['live'] is not None else '-':>7s} {('%+.1f%%' % (100*r['engine'])) if r['engine'] is not None else '-':>7s} {('%+.1f%%' % (100*gap)) if gap is not None else '-':>7s} {r['exit']}")
        if not r["status_ok"]: problems["reverted"] += 1
        if r["where"].startswith(("EARLY", "LATE")): problems["outside the seat's second"] += 1
        if vt is not None and vt < -slip: problems["tokens below target minus slip"] += 1
        if sold is not None and sold < 0.999: problems["sell moved less than the balance"] += 1
        if r["live"] is not None and r["engine"] is not None:
            live_v.append(r["live"]); eng_v.append(r["engine"])
    print()
    if live_v:
        diff = [a - b for a, b in zip(live_v, eng_v)]; random.seed(1); bs_ = []
        for _ in range(2000):
            s = [random.choice(diff) for _ in diff]; bs_.append(st.mean(s))
        bs_.sort(); lo, hi = bs_[int(0.025 * len(bs_))], bs_[int(0.975 * len(bs_))]
        print(f"trades compared {len(live_v)}: live mean {100*st.mean(live_v):+.2f}% a trade, engine mean on the same launches {100*st.mean(eng_v):+.2f}%, gap {100*st.mean(diff):+.2f}% [{100*lo:+.2f}%, {100*hi:+.2f}%] (95% bootstrap)")
        print(f"live: median {100*st.median(live_v):+.2f}%, worst {100*min(live_v):+.1f}%, share below -40% {100*sum(1 for v in live_v if v < -0.4)/len(live_v):.0f}%; sum of live P&L {sum((r['eth_out'] - r['eth_in'] - r['gas_eth']) for r in rows if 'note' not in r and r['eth_out'] is not None):+.4f} ETH, gas {sum(r['gas_eth'] for r in rows if 'note' not in r):.4f} ETH")
        if problems:
            verdict = "STOP and read the problems above: a revert, a landing outside the seat's second, tokens short of the target or a partial sell is the box or the send step, not the market"
        elif len(diff) < 10:
            verdict = f"too few trades to judge the gap ({len(diff)} of the 10 needed); the receipts themselves look right"
        elif hi < 0:
            verdict = "the live return is below the engine's score of the same launches and the interval excludes zero: a latency or seat problem, not the market; check landed / idx / vs target above"
        else:
            verdict = "the live return matches the engine's scores of the same launches: the box and the seat do what the tables assume"
        print("problems: " + (", ".join(f"{k} x{v}" for k, v in problems.items()) if problems else "none")); print("verdict: " + verdict)
    else:
        print("no trade could be compared with an engine score (the score event of each traded launch arrives 25 s after creation)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("log"); ap.add_argument("--rpc", default="https://rpc.mainnet.chain.robinhood.com"); ap.add_argument("--slip", type=float, default=0.25)
    a = ap.parse_args(); check(a.log, a.rpc, a.slip)
