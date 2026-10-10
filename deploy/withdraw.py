"""withdraw.py: send ETH from an engine's wallet to another address (your Phantom address on Robinhood Chain).

    sudo /opt/sniper-venv/bin/python3 deploy/withdraw.py --to 0xYourPhantomAddress --amount 0.02
    sudo /opt/sniper-venv/bin/python3 deploy/withdraw.py --to 0xYourPhantomAddress --amount all
    sudo SNIPER_ENV=/etc/sniper/runner.env /opt/sniper-venv/bin/python3 deploy/withdraw.py ...      # the runner's wallet
    sudo /opt/sniper-venv/bin/python3 deploy/withdraw.py --record 0xHASH                             # record a send the script could not confirm

Reads PRIVATE_KEY, WALLET and RPC_URL from the env file (SNIPER_ENV, default /etc/sniper/engine.env) and refuses while the engine
that sends from that wallet runs (sniper-engine, or runner-engine for runner.env): the two would race for the same nonce. 'all'
leaves a little for the transfer's own gas. Prints the balance, asks for a yes, prints the transaction's hash BEFORE sending, sends,
waits up to two minutes for the receipt, and records a landed withdrawal so the P&L line counts it as kept (the sniper's in
TG_PNL_WITHDRAWN in /etc/sniper/telegram.env, a second instance's in PNL_WITHDRAWN in its own env file). Each hash is recorded once
(a ledger next to the env file). Exit 0 only when the withdrawal landed and was recorded."""
import argparse, json, os, subprocess, sys, time, urllib.request
from eth_account import Account

ENV = os.environ.get("SNIPER_ENV", "/etc/sniper/engine.env")                # 6.25: a second instance (the runner) passes its own env file
POSTING_HEADROOM = 30_000                                                   # gas over the estimate for the chain's posting cost (Oct 9, see main)
RECEIPT_WAIT_S = 120.0
REFUSED_BEFORE_ACCEPT = ("insufficient funds", "intrinsic gas too low", "gas price", "fee cap", "nonce too low", "nonce too high", "invalid sender", "exceeds block gas limit", "max fee per gas")   # 6.27: every other error (already known, a forwarding timeout) is polled


def engine_unit():
    """6.26: the engine that sends from this env file's wallet"""
    return "runner-engine" if os.path.basename(ENV) == "runner.env" else "sniper-engine"


def engine_active():
    try:
        return subprocess.run(["systemctl", "is-active", "--quiet", engine_unit()]).returncode == 0
    except FileNotFoundError:
        return False


def ledger_path():
    return os.path.join(os.path.dirname(ENV) or ".", "withdrawals_" + os.path.basename(ENV).replace(".env", "") + ".log")


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


def record_withdrawal(eth, path=None, tx_hash=None):
    """Oct 8: adds a landed withdrawal to TG_PNL_WITHDRAWN, so the P&L line (relay_ops.py status) counts it as kept, not lost.
    6.25: a second instance's withdrawals go to PNL_WITHDRAWN in its own env file (SNIPER_ENV). 6.26 (5bk): the file is rewritten
    atomically (a temporary file, fsync, rename: an interrupted write can no longer empty runner.env, which holds the runner's only
    key copy), and a hash is recorded once (the ledger). Returns True when recorded."""
    key = "TG_PNL_WITHDRAWN=" if ENV == "/etc/sniper/engine.env" else "PNL_WITHDRAWN="
    path = path or ("/etc/sniper/telegram.env" if key.startswith("TG_") else ENV)
    led = ledger_path()
    try:
        if tx_hash and os.path.exists(led) and any(l.split()[0].lower() == tx_hash.lower() for l in open(led) if l.strip()):
            print(f"{tx_hash} is already recorded ({led}): not counting it twice"); return True
        lines = open(path).read().splitlines() if os.path.exists(path) else []
        prev = 0.0; out = []
        for line in lines:
            if line.startswith(key):
                prev = float(line.split("=", 1)[1].strip() or 0)
            else:
                out.append(line)
        out.append(f"{key}{prev + eth:.6f}")
        tmp = path + ".tmp"; fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write("\n".join(out) + "\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
        if tx_hash:
            with open(led, "a") as f:
                f.write(f"{tx_hash} {eth:.6f} {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}\n")
        print(f"recorded: {prev + eth:.6f} ETH withdrawn in all (the P&L line counts it as kept)"); return True
    except Exception as e:
        print(f"could not record the withdrawal in {path} ({e}): run withdraw.py --record {tx_hash or '<hash>'} once the cause is fixed"); return False


def record_hash(url, wallet, h):
    """6.26: record a withdrawal the script could not confirm: the transaction must be from this wallet, landed, a plain transfer"""
    tx = rpc(url, "eth_getTransactionByHash", [h]); rc = rpc(url, "eth_getTransactionReceipt", [h])
    if not tx or not rc:
        sys.exit(f"{h}: not found or not landed yet")
    if tx["from"].lower() != wallet.lower():
        sys.exit(f"{h} was sent from {tx['from']}, not from this wallet {wallet}: not recording")
    if rc.get("status") != "0x1":
        sys.exit(f"{h} FAILED on the chain: nothing left the wallet but gas; not recording")
    if tx.get("input") not in ("0x", "", None):
        sys.exit(f"{h} carries data (not a plain transfer): not recording")
    eth = int(tx["value"], 16) / 1e18; print(f"{h}: {eth:.6f} ETH to {tx['to']}, landed in block {int(rc['blockNumber'], 16)}")
    sys.exit(0 if record_withdrawal(eth, tx_hash=h) else 1)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--to"); ap.add_argument("--amount", help="ETH, or 'all'"); ap.add_argument("--yes", action="store_true")
    ap.add_argument("--record", metavar="HASH", help="record a landed withdrawal from this wallet that the script could not confirm")
    a = ap.parse_args(); e = env(); url = e.get("RPC_URL") or "https://rpc.mainnet.chain.robinhood.com"
    key = Account.from_key(e["PRIVATE_KEY"]); wallet = key.address
    if e.get("WALLET", "").lower() != wallet.lower():
        sys.exit(f"the key in {ENV} is for {wallet}, WALLET says {e.get('WALLET')}: not sending")
    if a.record:
        record_hash(url, wallet, a.record)
    if not a.to or not a.amount:
        sys.exit("--to and --amount are required (or --record HASH)")
    if engine_active():
        sys.exit(f"{engine_unit()} is running: sudo systemctl stop {engine_unit()} first (it sends from this wallet: same nonce)")
    to = a.to
    if not (to.startswith("0x") and len(to) == 42):
        sys.exit("the destination must be a 0x address of 42 characters")
    from eth_utils import is_checksum_address, to_checksum_address
    if to != to.lower() and not is_checksum_address(to):
        sys.exit("the destination's capital letters do not match its checksum: a character is probably wrong; check the address")
    to = to_checksum_address(to.lower())
    bal = int(rpc(url, "eth_getBalance", [wallet, "latest"]), 16); gp = int(int(rpc(url, "eth_gasPrice", []), 16) * 2)
    # Oct 9: the chain charges the parent-chain posting cost as extra gas, non-zero in about half the blocks (up to ~5,000 gas
    # sampled over 12 h): a transfer capped at exactly 21,000 is refused with "intrinsic gas too low" whenever it is. The limit
    # is the node's estimate plus POSTING_HEADROOM; only the gas used is charged, the rest is refunded.
    try:
        est = int(rpc(url, "eth_estimateGas", [{"from": wallet, "to": to, "value": hex(max(0, bal // 2))}]), 16)
    except Exception:
        est = 21000
    gas = max(est, 21000) + POSTING_HEADROOM; reserve = gp * gas * 3
    amount = bal - reserve if a.amount == "all" else int(float(a.amount) * 1e18)
    if amount <= 0 or amount + gp * gas > bal:
        sys.exit(f"balance {bal/1e18:.6f} ETH cannot cover {amount/1e18:.6f} ETH plus gas")
    print(f"from {wallet}\nto   {to}\nbalance {bal/1e18:.6f} ETH, sending {amount/1e18:.6f} ETH (gas limit {gas}, at most {gp*gas/1e18:.7f} ETH; only the gas used is charged)")
    if not a.yes and input("type yes to send: ").strip().lower() != "yes":
        sys.exit("not sent")
    nonce = int(rpc(url, "eth_getTransactionCount", [wallet, "pending"]), 16)
    tx = {"to": to, "value": amount, "gas": gas, "gasPrice": gp, "nonce": nonce, "chainId": 4663}
    signed = key.sign_transaction(tx); hx = bytes(signed.hash).hex(); h = hx if hx.startswith("0x") else "0x" + hx
    print(f"transaction {h} (if this script stops before 'recorded', check it on the explorer and run: withdraw.py --record {h})")
    try:
        sent = rpc(url, "eth_sendRawTransaction", ["0x" + bytes(signed.raw_transaction).hex()])
        if isinstance(sent, str) and sent.lower() != h.lower():
            print(f"the node answered a different hash {sent}: polling ours")
        print("sent", h)
    except RuntimeError as ex:                                           # the node's own JSON-RPC error
        if any(k in str(ex).lower() for k in REFUSED_BEFORE_ACCEPT):     # refused before acceptance: nothing was sent
            sys.exit(f"refused by the node, nothing sent: {ex}")
        print(f"the node answered an error after the send ({str(ex)[:80]}): it may have accepted the transaction (6.27); polling its hash, never sending again blind")
    except Exception as ex:                                              # a timeout or a dropped connection: the node may have taken it; never send again blind
        print(f"the node did not answer ({str(ex)[:80]}): the transfer may have been accepted; polling its hash")
    t0 = time.time(); last_err = None
    while time.time() - t0 < RECEIPT_WAIT_S:
        time.sleep(0.5)
        try:
            r = rpc(url, "eth_getTransactionReceipt", [h])
        except Exception as ex:
            last_err = ex; continue
        if r:
            ok = r.get("status") == "0x1"; print("landed in block", int(r["blockNumber"], 16), "status", "ok" if ok else "FAILED")
            if ok and record_withdrawal(amount / 1e18, tx_hash=h):
                return
            sys.exit(1)
    sys.exit(f"no receipt after {RECEIPT_WAIT_S:.0f} s{' (last error: ' + str(last_err)[:60] + ')' if last_err else ''}: check {h} on the explorer; "
             f"if it landed run withdraw.py --record {h}; do NOT send again before checking")


if __name__ == "__main__":
    main()
