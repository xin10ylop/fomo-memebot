"""status.py: real trades, wallet balance and P&L in one line each.

    /opt/sniper-venv/bin/python3 src/analysis/status.py [log] [--rpc URL] [--wallet 0x...] [--env /etc/sniper/engine.env]

Reads the engine's log (default /var/log/sniper/engine.jsonl), counts the live trades (trade_done with dry_run false),
prices each one from its own receipts (ETH in from the buy's Buy event, ETH out from the sell's Sell event, gas from all
receipts), reads the wallet's balance from the chain and the ETH price from Coinbase, and prints: the trades since going
live and since 12:00 UTC today, their P&L in dollars, and the wallet now. RPC_URL and WALLET come from the engine's env
file when it is readable, so on the machine no argument is needed."""
import sys, os, json, time, argparse, urllib.request, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import live_check as LC


def env_file(path):
    out = {}
    try:
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1); out[k.strip()] = v.split(" #", 1)[0].strip()
    except OSError:
        pass
    return out


def eth_price(fallback):
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request("https://api.coinbase.com/v2/prices/ETH-USD/spot", headers={"User-Agent": "Mozilla/5.0"}), timeout=10))
        px = float(d["data"]["amount"])
        if 100 < px < 100000:
            return px
    except Exception:
        pass
    return fallback


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("log", nargs="?", default="/var/log/sniper/engine.jsonl"); ap.add_argument("--rpc"); ap.add_argument("--wallet"); ap.add_argument("--env", default="/etc/sniper/engine.env")
    a = ap.parse_args(); env = env_file(a.env)
    rpc_url = a.rpc or env.get("RPC_URL") or "https://rpc.mainnet.chain.robinhood.com"
    wallet = a.wallet or env.get("WALLET"); dones = []; flows = []; live_since = None; px_log = None
    for line in open(a.log):
        try:
            e = json.loads(line)
        except Exception:
            continue
        ev = e.get("ev")
        if ev == "start":
            wallet = wallet or e.get("wallet")
            if e.get("dry_run") is False and live_since is None:
                live_since = e["t"]
        elif ev == "trade_done" and e.get("dry_run") is False:
            dones.append(e)
        elif ev == "flow":
            flows.append(e)
            if e.get("bankroll_usd") and e.get("wallet_eth"):
                px_log = e["bankroll_usd"] / e["wallet_eth"]
    rpc = LC.Rpc(rpc_url); px = eth_price(px_log or 2445.0)
    bal = int(rpc.call("eth_getBalance", [wallet, "latest"]), 16) / 1e18 if wallet else None
    now = time.time(); day0 = now - (now % 86400) + 12 * 3600
    if day0 > now:
        day0 -= 86400
    print(f"wallet {wallet}: {bal:.5f} ETH = ${bal * px:,.2f}  (ETH ${px:,.0f})" if bal is not None else "wallet unknown: pass --wallet")
    if live_since:
        fw = [f for f in flows if f.get('wallet_eth')]
        print(f"live since {datetime.datetime.fromtimestamp(live_since, datetime.timezone.utc).strftime('%b %d %H:%M')} UTC; first balance seen {fw[0]['wallet_eth']:.5f} ETH" if fw else f"live since {datetime.datetime.fromtimestamp(live_since, datetime.timezone.utc).strftime('%b %d %H:%M')} UTC")
    print(f"real trades: {len(dones)} in total, {sum(1 for d in dones if d['t'] >= day0)} since 12:00 UTC today\n")
    if flows:
        f = flows[-1]; print("market, last readout: " + ", ".join(f"{k} {f.get(k)}" for k in ("rule_passing_last_1h", "out1_share_last_60", "follow_eth_last_60", "follow_eth_all_60", "mean_score_last_60", "mean_score_e1_last_60", "race_first_rival_ms_median", "race_first_block_share") if k in f)
              + "\n  (clean launches an hour; share of team launches with a bot in second one; ETH buyers bring after a clean seat / after any team launch; mean paper score of the last 60 for our E2 seat and for the E1 front; how many ms after second one opens the first bot lands, and the share landing in its first block)\n")
    if not dones:
        return
    print(f"{'time UTC':9s} {'ETH in':>8s} {'ETH out':>8s} {'gas':>8s} {'P&L $':>8s} {'return':>7s}  exit")
    tot = 0.0; tot_day = 0.0; gas_tot = 0.0
    for d in dones:
        t = datetime.datetime.fromtimestamp(d["t"], datetime.timezone.utc).strftime("%d %H:%M")
        if not (d.get("buy_hash") and d.get("sell_hash")):
            print(f"{t:9s} no hashes in the log ({d.get('note') or d.get('exit')})"); continue
        rb = rpc.call("eth_getTransactionReceipt", [d["buy_hash"]]); rs = rpc.call("eth_getTransactionReceipt", [d["sell_hash"]])
        ra = rpc.call("eth_getTransactionReceipt", [d["approve_hash"]]) if d.get("approve_hash") else None
        if rb is None or rs is None:
            print(f"{t:9s} receipt missing ({'buy' if rb is None else 'sell'} {d['buy_hash' if rb is None else 'sell_hash'][:12]})"); continue
        w = rb["from"].lower(); eth_in = eth_out = None
        for l in rb.get("logs", []):
            if l["topics"][0] == LC.BUY_EV and l["address"].lower() == d["curve"].lower() and l["topics"][2][-40:] == w[-40:]:
                eth_in = LC.words(l["data"])[0] / 1e18
        for l in rs.get("logs", []):
            if l["topics"][0] == LC.SELL_EV and l["address"].lower() == d["curve"].lower():
                eth_out = LC.words(l["data"])[1] / 1e18
        gas = LC.receipt_cost(rpc, rb) + LC.receipt_cost(rpc, rs) + (LC.receipt_cost(rpc, ra) if ra else 0.0); gas_tot += gas
        if eth_in is None:
            print(f"{t:9s} buy reverted or no Buy event (status {rb.get('status')}), gas ${gas * px:.2f}"); tot -= gas * px; continue
        eth_out = eth_out or 0.0; pnl = (eth_out - eth_in - gas) * px; tot += pnl
        if d["t"] >= day0:
            tot_day += pnl
        print(f"{t:9s} {eth_in:8.5f} {eth_out:8.5f} {gas:8.5f} {pnl:+8.2f} {100 * (eth_out - eth_in - gas) / eth_in:+6.1f}%  {d.get('exit')}{'' if rs.get('status') == '0x1' else '  SELL REVERTED'}")
    print(f"\nP&L of the real trades: {tot:+,.2f} $ in total, {tot_day:+,.2f} $ since 12:00 UTC today; gas paid {gas_tot * px:.2f} $")
    fw = [f for f in flows if f.get('wallet_eth')]
    if fw and bal is not None:
        print(f"wallet change since the first live balance ({fw[0]['wallet_eth']:.5f} ETH): {(bal - fw[0]['wallet_eth']) * px:+,.2f} $ (differs from the trades' P&L if you added or withdrew money)")


if __name__ == "__main__":
    main()
