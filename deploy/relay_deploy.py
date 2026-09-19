"""relay_deploy.py: put the BuyOnce relay (contracts/BuyOnce.sol) on Robinhood Chain from the machine's wallet.

    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_deploy.py

Stop the engine first (sudo systemctl stop sniper-engine): it and this script would otherwise race for the same nonce; the
script refuses to run while the service is active. Reads PRIVATE_KEY, WALLET and RPC_URL from /etc/sniper/engine.env,
checks that contracts/BuyOnce.json was compiled from the contracts/BuyOnce.sol next to it, estimates the gas, shows the
cost, asks for a yes, deploys, waits for the receipt, reads owner() back from the chain and compares it with the wallet,
runs one simulated buy through the new relay on a live curve, and prints the RELAY= line for the env file."""
import argparse, hashlib, json, os, subprocess, sys, time, urllib.request
from eth_account import Account

ENV = "/etc/sniper/engine.env"; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTORY = "0xe33e9e479df8802cb0866d5d05258bec4cf62948"


def env():
    d = {}
    for line in open(ENV):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1); d[k.strip()] = v.split(" #", 1)[0].strip()
    return d


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
            time.sleep(2 * (i + 1))
        raise RuntimeError(f"{method}: {last}")


def word(x):
    return ("%064x" % x) if isinstance(x, int) else x[2:].lower().zfill(64)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--yes", action="store_true", help="do not ask")
    ap.add_argument("--write-env", action="store_true", help="after a verified deployment, put RELAY=<address> into /etc/sniper/engine.env (replacing any RELAY line)"); a = ap.parse_args()
    if subprocess.run(["systemctl", "is-active", "--quiet", "sniper-engine"]).returncode == 0:
        sys.exit("the engine is running: sudo systemctl stop sniper-engine first (same wallet, same nonce)")
    e = env(); key = e.get("PRIVATE_KEY"); wallet = e.get("WALLET", "").lower(); url = e.get("RPC_URL") or "https://rpc.mainnet.chain.robinhood.com"
    if not key or not wallet:
        sys.exit(f"PRIVATE_KEY or WALLET missing in {ENV}")
    acct = Account.from_key(key)
    if acct.address.lower() != wallet:
        sys.exit(f"the key in {ENV} is for {acct.address}, WALLET says {wallet}")
    art = json.load(open(os.path.join(ROOT, "contracts", "BuyOnce.json"))); src = open(os.path.join(ROOT, "contracts", "BuyOnce.sol")).read()
    if hashlib.sha256(src.encode()).hexdigest() != art["source_sha256"]:
        sys.exit("contracts/BuyOnce.json was not compiled from contracts/BuyOnce.sol (source hash differs): recompile before deploying")
    rpc = Rpc(url)
    bal = int(rpc.call("eth_getBalance", [wallet, "latest"]), 16); gp = int(rpc.call("eth_gasPrice", []), 16); nonce = int(rpc.call("eth_getTransactionCount", [wallet, "pending"]), 16)
    gas = int(rpc.call("eth_estimateGas", [{"from": wallet, "data": art["bytecode"]}]), 16); gas_lim = int(gas * 1.3)
    cost = gas_lim * gp * 2 / 1e18
    print(f"wallet {wallet}: {bal / 1e18:.5f} ETH; deploy needs about {gas} gas at {gp / 1e9:.4f} gwei: at most {cost:.6f} ETH (a few cents)")
    if bal < gas_lim * gp * 2:
        sys.exit("not enough ETH for the deployment")
    if not a.yes and input("deploy the BuyOnce relay now? (yes/no) ").strip().lower() != "yes":
        sys.exit("not deployed")
    tx = {"data": art["bytecode"], "value": 0, "gas": gas_lim, "gasPrice": gp * 2, "nonce": nonce, "chainId": 4663}
    signed = acct.sign_transaction(tx); h = rpc.call("eth_sendRawTransaction", ["0x" + bytes(signed.raw_transaction).hex()])
    print("sent", h); rec = None; t0 = time.time()
    while time.time() - t0 < 120 and rec is None:
        time.sleep(1.5); rec = rpc.call("eth_getTransactionReceipt", [h])
    if rec is None:
        sys.exit("no receipt after two minutes: check the hash on the explorer before trying again")
    if rec.get("status") != "0x1":
        sys.exit(f"the deployment reverted (block {int(rec['blockNumber'], 16)}); nothing to use")
    relay = rec["contractAddress"].lower(); print(f"deployed at {relay} in block {int(rec['blockNumber'], 16)}, gas used {int(rec['gasUsed'], 16)}")
    code = rpc.call("eth_getCode", [relay, "latest"]); owner = rpc.call("eth_call", [{"to": relay, "data": "0x8da5cb5b"}, "latest"])
    expected = bytearray.fromhex(art["deployedBytecode"][2:])           # the runtime code with the owner immutable filled in must match byte for byte
    for refs in art["immutableReferences"].values():
        for r in refs:
            expected[r["start"]:r["start"] + r["length"]] = bytes(12) + bytes.fromhex(wallet[2:])
    ok_code = code[2:].lower() == expected.hex()
    print(f"code on the chain: {len(code) // 2 - 1} bytes {'ok' if ok_code else 'UNEXPECTED'}; owner() = 0x{owner[-40:]} {'== wallet ok' if ('0x' + owner[-40:]).lower() == wallet else '!= WALLET: DO NOT USE'}")
    if ("0x" + owner[-40:]).lower() != wallet:
        sys.exit(1)
    head = int(rpc.call("eth_blockNumber", []), 16)
    logs = rpc.call("eth_getLogs", [{"fromBlock": hex(head - 30000), "toBlock": "latest", "address": FACTORY}])
    curves = ["0x" + l["topics"][2][-40:] for l in logs if len(l["topics"]) > 3]
    if curves:
        curve = curves[-1]; amt = 10 ** 14
        try:
            rpc.call("eth_call", [{"from": wallet, "to": relay, "value": hex(amt), "data": "0x1622dbe4" + word(curve) + word(amt) + word(0) + word(0)}, "latest"], tries=2)
            print(f"simulated buy through the relay on the latest curve {curve}: ok")
            try:
                rpc.call("eth_call", [{"from": wallet, "to": relay, "value": hex(amt), "data": "0x1622dbe4" + word(curve) + word(amt) + word(0) + word(1)}, "latest"], tries=2)
                print("a buy with a deadline in the past WENT THROUGH: the relay does not enforce the deadline; do not use it"); sys.exit(1)
            except SystemExit:
                raise
            except Exception as ex:
                print("a buy with a deadline in the past is refused (TooLate): ok" if "388b0173" in str(ex) else f"unexpected answer to a past deadline: {str(ex)[:120]}")
        except Exception as ex:
            print(f"simulated buy through the relay on {curve} did not go through ({str(ex)[:120]}); the curve may be graduated or in its tax second, try the engine's dry run")
    if a.write_env:
        lines = [l for l in open(ENV).read().splitlines() if not l.startswith("RELAY=")] + [f"RELAY={relay}"]
        tmp = ENV + ".tmp"; open(tmp, "w").write("\n".join(lines) + "\n"); os.chmod(tmp, 0o600); os.replace(tmp, ENV)
        print(f"\nRELAY={relay} written to {ENV}; set STAKE_MIN/STAKE_MAX to the bet you want and restart the engine")
    else:
        print("\nadd this line to /etc/sniper/engine.env (and STAKE_MIN/STAKE_MAX to the bet you want), then restart the engine:")
        print(f"RELAY={relay}")


if __name__ == "__main__":
    main()
