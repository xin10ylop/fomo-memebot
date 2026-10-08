"""withdraw.py: send ETH from the machine's wallet to another address (your Phantom address on Robinhood Chain).

    /opt/sniper-venv/bin/python3 /root/fomo-memebot/deploy/withdraw.py --to 0xYourPhantomAddress --amount 0.02
    /opt/sniper-venv/bin/python3 /root/fomo-memebot/deploy/withdraw.py --to 0xYourPhantomAddress --amount all

Stop the engine first (systemctl stop sniper-engine): it and this script would otherwise race for the same nonce.
Reads PRIVATE_KEY, WALLET and RPC_URL from /etc/sniper/engine.env. 'all' leaves a little for the transfer's own gas.
Prints the balance, asks for a yes, sends, and waits for the receipt."""
import argparse, json, os, sys, time, urllib.request
from eth_account import Account

ENV = "/etc/sniper/engine.env"


def env():
    d = {}
    for line in open(ENV):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1); d[k.strip()] = v.split(" #", 1)[0].strip()
    return d


def rpc(url, method, params):
    req = urllib.request.Request(url, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(), headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    d = json.load(urllib.request.urlopen(req, timeout=20))
    if "error" in d:
        raise RuntimeError(d["error"])
    return d["result"]


def record_withdrawal(eth, path="/etc/sniper/telegram.env"):
    """Oct 8: adds a landed withdrawal to TG_PNL_WITHDRAWN, so the P&L line (relay_ops.py status) counts it as kept, not lost"""
    try:
        lines = open(path).read().splitlines() if os.path.exists(path) else []
        prev = 0.0; out = []
        for line in lines:
            if line.startswith("TG_PNL_WITHDRAWN="):
                prev = float(line.split("=", 1)[1].strip() or 0)
            else:
                out.append(line)
        out.append(f"TG_PNL_WITHDRAWN={prev + eth:.6f}")
        open(path, "w").write("\n".join(out) + "\n"); os.chmod(path, 0o600)
        print(f"recorded: {prev + eth:.6f} ETH withdrawn in all (the P&L line counts it as kept)")
    except Exception as e:
        print(f"could not record the withdrawal in {path} ({e}): add TG_PNL_WITHDRAWN by hand")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--to", required=True); ap.add_argument("--amount", required=True, help="ETH, or 'all'"); ap.add_argument("--yes", action="store_true")
    a = ap.parse_args(); e = env(); url = e.get("RPC_URL") or "https://rpc.mainnet.chain.robinhood.com"
    key = Account.from_key(e["PRIVATE_KEY"]); wallet = key.address
    if e.get("WALLET", "").lower() != wallet.lower():
        sys.exit(f"the key in {ENV} is for {wallet}, WALLET says {e.get('WALLET')}: not sending")
    to = a.to
    if not (to.startswith("0x") and len(to) == 42):
        sys.exit("the destination must be a 0x address of 42 characters")
    from eth_utils import is_checksum_address, to_checksum_address
    if to != to.lower() and not is_checksum_address(to):
        sys.exit("the destination's capital letters do not match its checksum: a character is probably wrong; check the address")
    to = to_checksum_address(to.lower())
    bal = int(rpc(url, "eth_getBalance", [wallet, "latest"]), 16); gp = int(int(rpc(url, "eth_gasPrice", []), 16) * 2); gas = 21000; reserve = gp * gas * 3
    amount = bal - reserve if a.amount == "all" else int(float(a.amount) * 1e18)
    if amount <= 0 or amount + gp * gas > bal:
        sys.exit(f"balance {bal/1e18:.6f} ETH cannot cover {amount/1e18:.6f} ETH plus gas")
    print(f"from {wallet}\nto   {to}\nbalance {bal/1e18:.6f} ETH, sending {amount/1e18:.6f} ETH (gas about {gp*gas/1e18:.7f} ETH)")
    if not a.yes and input("type yes to send: ").strip().lower() != "yes":
        sys.exit("not sent")
    nonce = int(rpc(url, "eth_getTransactionCount", [wallet, "pending"]), 16)
    tx = {"to": to, "value": amount, "gas": gas, "gasPrice": gp, "nonce": nonce, "chainId": 4663}
    signed = key.sign_transaction(tx); h = rpc(url, "eth_sendRawTransaction", ["0x" + bytes(signed.raw_transaction).hex()])
    print("sent", h)
    for _ in range(60):
        time.sleep(0.5); r = rpc(url, "eth_getTransactionReceipt", [h])
        if r:
            ok = r.get("status") == "0x1"; print("landed in block", int(r["blockNumber"], 16), "status", "ok" if ok else "FAILED")
            if ok:
                record_withdrawal(amount / 1e18)
            return
    print("no receipt after 30 s: check the hash on the explorer before sending again")


if __name__ == "__main__":
    main()
