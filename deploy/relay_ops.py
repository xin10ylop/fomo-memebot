"""relay_ops.py: the relay's money and the shooter wallets (engine 6.0), from the machine's wallet.

    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_ops.py status
    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_ops.py shooters-create 35      # 35 new keys into engine.env (SHOOTER_KEYS)
    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_ops.py shooters-register       # tell the relay who may shoot (one transaction)
    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_ops.py shooters-fund           # gas to every shooter below the minimum
    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_ops.py deposit 0.009           # ETH into the relay (the stake it buys with)
    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_ops.py withdraw all            # the relay's ETH back to the wallet
    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_ops.py shooters-sweep          # every shooter's gas back to the wallet

Stop the engine before anything that sends (it and this script would race for the wallet's nonce); status is read-only.
Reads PRIVATE_KEY, WALLET, RPC_URL, RELAY and SHOOTER_KEYS from /etc/sniper/engine.env; shooters-create writes SHOOTER_KEYS
there (it refuses to overwrite an existing set unless --replace: sweep the old ones first)."""
import argparse, json, os, subprocess, sys, time, urllib.request
from eth_account import Account
from eth_utils import to_checksum_address

ENV = "/etc/sniper/engine.env"
SHOOTER_TARGET_ETH = 0.0001; SHOOTER_MIN_ETH = 0.00004


def env():
    d = {}
    for line in open(ENV):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1); d[k.strip()] = v.split(" #", 1)[0].strip()
    return d


def set_env(key, value):
    lines = [l for l in open(ENV).read().splitlines() if not l.startswith(key + "=")] + [f"{key}={value}"]
    tmp = ENV + ".tmp"; open(tmp, "w").write("\n".join(lines) + "\n"); os.chmod(tmp, 0o600); os.replace(tmp, ENV)


class Rpc:
    def __init__(self, url):
        self.url = url

    def call(self, method, params, tries=6):
        last = None
        for i in range(tries):
            try:
                req = urllib.request.Request(self.url, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(), headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
                d = json.load(urllib.request.urlopen(req, timeout=30))
                if "result" in d:
                    return d["result"]
                last = d.get("error")
                if isinstance(last, dict) and last.get("code") != 429:
                    raise RuntimeError(last)
            except RuntimeError:
                raise
            except Exception as e:
                last = str(e)
            time.sleep(1.5 * (i + 1))
        raise RuntimeError(f"{method}: {last}")


def word(x):
    return ("%064x" % x) if isinstance(x, int) else x[2:].lower().zfill(64)


def engine_running():
    return subprocess.run(["systemctl", "is-active", "--quiet", "sniper-engine"]).returncode == 0


def send(rpc, acct, tx, label, wait=True):
    signed = acct.sign_transaction(tx); h = rpc.call("eth_sendRawTransaction", ["0x" + bytes(signed.raw_transaction).hex()])
    rec = None; t0 = time.time()
    while wait and rec is None and time.time() - t0 < 60:
        time.sleep(1.0); rec = rpc.call("eth_getTransactionReceipt", [h])
    if wait:
        print(f"  {label}: {h} {'landed' if rec and rec.get('status') == '0x1' else ('REVERTED' if rec else 'no receipt in 60 s')}")
    return h, rec


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["status", "shooters-create", "shooters-register", "shooters-fund", "shooters-sweep", "deposit", "withdraw"])
    ap.add_argument("arg", nargs="?"); ap.add_argument("--replace", action="store_true"); ap.add_argument("--yes", action="store_true"); a = ap.parse_args()
    e = env(); key = e.get("PRIVATE_KEY"); wallet = e.get("WALLET", "").lower(); url = e.get("RPC_URL") or "https://rpc.mainnet.chain.robinhood.com"; relay = e.get("RELAY", "").lower()
    if not key or not wallet:
        sys.exit(f"PRIVATE_KEY or WALLET missing in {ENV}")
    acct = Account.from_key(key); rpc = Rpc(url); px = None
    try:
        px = float(json.load(urllib.request.urlopen("https://api.coinbase.com/v2/prices/ETH-USD/spot", timeout=10))["data"]["amount"])
    except Exception:
        pass
    usd = (lambda x: f" (${x * px:.2f})") if px else (lambda x: "")
    keys = [k for k in e.get("SHOOTER_KEYS", "").split(",") if k.strip()]; shooters = [Account.from_key(k).address for k in keys]
    gp = int(rpc.call("eth_gasPrice", []), 16)

    if a.cmd == "status":
        wb = int(rpc.call("eth_getBalance", [wallet, "latest"]), 16) / 1e18; print(f"wallet {wallet}: {wb:.6f} ETH{usd(wb)}")
        if relay:
            rb = int(rpc.call("eth_getBalance", [relay, "latest"]), 16) / 1e18; print(f"relay  {relay}: {rb:.6f} ETH{usd(rb)} (the stake it buys with)")
        print(f"shooters: {len(shooters)}")
        low = 0; unreg = 0
        for s_ in shooters:
            time.sleep(0.25); b = int(rpc.call("eth_getBalance", [s_, "latest"]), 16) / 1e18
            reg = int(rpc.call("eth_call", [{"to": relay, "data": "0x5c7b6bcb" + word(s_)}, "latest"]) or "0x0", 16) if relay else 0
            low += b < SHOOTER_MIN_ETH; unreg += not reg
            print(f"  {s_} {b:.6f} ETH {'registered' if reg else 'NOT registered'}{' LOW' if b < SHOOTER_MIN_ETH else ''}")
        print(f"{low} low on gas, {unreg} not registered"); return

    if engine_running():
        sys.exit("the engine is running: sudo systemctl stop sniper-engine first (same wallet, same nonce)")

    if a.cmd == "shooters-create":
        n = int(a.arg or 35)
        if keys and not a.replace:
            sys.exit(f"{len(keys)} shooter keys already in {ENV}: sweep them (shooters-sweep) and pass --replace to make a new set")
        new = [Account.create() for _ in range(n)]
        set_env("SHOOTER_KEYS", ",".join("0x" + bytes(x.key).hex() for x in new))
        print(f"{n} shooter keys written to {ENV} (SHOOTER_KEYS); addresses:"); [print("  " + x.address) for x in new]
        print("next: shooters-register, then shooters-fund"); return

    if not shooters and a.cmd.startswith("shooters-"):
        sys.exit("no SHOOTER_KEYS in the env: shooters-create first")
    nonce = int(rpc.call("eth_getTransactionCount", [wallet, "pending"]), 16)

    if a.cmd == "shooters-register":
        if not relay:
            sys.exit("no RELAY in the env: deploy it first (deploy/relay_deploy.py --write-env)")
        data = "0x4ee0e011" + word(64) + word(1) + word(len(shooters)) + "".join(word(s_) for s_ in shooters)
        gas = int(rpc.call("eth_estimateGas", [{"from": wallet, "to": relay, "data": data}]), 16)
        print(f"registering {len(shooters)} shooters on {relay}: about {gas} gas{usd(gas * gp / 1e18)}")
        send(rpc, acct, {"to": to_checksum_address(relay), "value": 0, "data": data, "gas": int(gas * 1.3), "gasPrice": gp * 2, "nonce": nonce, "chainId": 4663}, "setShooters")
        time.sleep(1); ok = sum(int(rpc.call("eth_call", [{"to": relay, "data": "0x5c7b6bcb" + word(s_)}, "latest"]) or "0x0", 16) for s_ in shooters)
        print(f"{ok} of {len(shooters)} registered"); return

    if a.cmd == "shooters-fund":
        target = float(a.arg) if a.arg else SHOOTER_TARGET_ETH; plan = []
        for s_ in shooters:
            time.sleep(0.25); b = int(rpc.call("eth_getBalance", [s_, "latest"]), 16) / 1e18
            if b < SHOOTER_MIN_ETH:
                plan.append((s_, target - b))
        total = sum(x for _, x in plan); wb = int(rpc.call("eth_getBalance", [wallet, "latest"]), 16) / 1e18
        print(f"{len(plan)} shooters to fund, {total:.6f} ETH{usd(total)} in total; the wallet holds {wb:.6f} ETH")
        if not plan:
            return
        if wb < total + 0.001:
            sys.exit("the wallet cannot cover it: top up the wallet first")
        if not a.yes and input("send? (yes/no) ").strip().lower() != "yes":
            sys.exit("not sent")
        hashes = []
        for i, (s_, amt) in enumerate(plan):
            h, _ = send(rpc, acct, {"to": to_checksum_address(s_), "value": int(amt * 1e18), "data": b"", "gas": 30_000, "gasPrice": gp * 2, "nonce": nonce + i, "chainId": 4663}, f"gas to {s_[:10]}", wait=False); hashes.append(h)
        time.sleep(3); landed = sum(1 for h in hashes if (rpc.call("eth_getTransactionReceipt", [h]) or {}).get("status") == "0x1")
        print(f"{landed} of {len(hashes)} transfers landed"); return

    if a.cmd == "shooters-sweep":
        got = 0.0
        for k, s_ in zip(keys, shooters):
            time.sleep(0.25); b = int(rpc.call("eth_getBalance", [s_, "latest"]), 16); fee = 21_000 * gp * 2
            if b <= fee * 2:
                continue
            n_ = int(rpc.call("eth_getTransactionCount", [s_, "pending"]), 16)
            send(rpc, acct=Account.from_key(k), tx={"to": to_checksum_address(wallet), "value": b - fee, "data": b"", "gas": 21_000, "gasPrice": gp * 2, "nonce": n_, "chainId": 4663}, label=f"sweep {s_[:10]}", wait=False); got += (b - fee) / 1e18
        print(f"about {got:.6f} ETH on its way back to the wallet"); return

    if a.cmd == "deposit":
        amt = float(a.arg or 0)
        if not relay or amt <= 0:
            sys.exit("deposit <eth>: the relay address from the env, an amount in ETH")
        print(f"sending {amt:.6f} ETH{usd(amt)} to the relay {relay}")
        send(rpc, acct, {"to": to_checksum_address(relay), "value": int(amt * 1e18), "data": b"", "gas": 50_000, "gasPrice": gp * 2, "nonce": nonce, "chainId": 4663}, "deposit")
        rb = int(rpc.call("eth_getBalance", [relay, "latest"]), 16) / 1e18; print(f"relay holds {rb:.6f} ETH{usd(rb)}"); return

    if a.cmd == "withdraw":
        amt = 0 if (a.arg or "all") == "all" else int(float(a.arg) * 1e18)
        send(rpc, acct, {"to": to_checksum_address(relay), "value": 0, "data": "0x2e1a7d4d" + word(amt), "gas": 80_000, "gasPrice": gp * 2, "nonce": nonce, "chainId": 4663}, "withdraw")
        rb = int(rpc.call("eth_getBalance", [relay, "latest"]), 16) / 1e18; print(f"relay holds {rb:.6f} ETH{usd(rb)}"); return


if __name__ == "__main__":
    main()
