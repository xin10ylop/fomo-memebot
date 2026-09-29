#!/usr/bin/env python3
"""Same-nonce race between the sequencer's addresses: does one path deliver a shot to the sequencer before the others?

The sequencer's name resolves to one address per availability zone. Each round signs ONE harmless transaction (the wallet
sending 0 ETH to itself, 21,000 gas) and posts the identical bytes to every address at the same instant from pre-warmed
TLS sockets. Only one copy can be sequenced: its reply carries the hash, the others get a nonce error at no cost. The
share of rounds each address wins is the path's arrival-order advantage, which is what decides first place in a block
under strict arrival ordering. The engine pins the address with the lowest ping; this probe tells whether the lowest ping
is also the earliest arrival, and whether a fan-out of every shot over two paths would gain anything.

    sudo systemctl stop sniper-engine
    sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/ingress_race.py [rounds, default 30]
    sudo systemctl start sniper-engine

Refuses to run while the engine is active (same wallet, same nonce). Costs about 21,000 gas a round (a few cents in all).
Reads PRIVATE_KEY, WALLET and RPC_URL from /etc/sniper/engine.env; prints no key.
"""
import http.client, json, os, socket, ssl, statistics as st, subprocess, sys, threading, time, urllib.request
from eth_account import Account
from eth_utils import to_checksum_address

ENV = "/etc/sniper/engine.env"; HOST = "sequencer.mainnet.chain.robinhood.com"; ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
CTX = ssl.create_default_context(); UA = {"Content-Type": "application/json", "User-Agent": "ingress-race/1"}


def env():
    out = {}
    for line in open(ENV):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1); out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def rpc(url, method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(url, body, UA), timeout=15))
    if "error" in r:
        raise RuntimeError(str(r["error"])[:160])
    return r["result"]


def connect(ip):
    raw = socket.create_connection((ip, 443), timeout=5); raw.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    c = http.client.HTTPSConnection(HOST, timeout=10, context=CTX); c.sock = CTX.wrap_socket(raw, server_hostname=HOST)
    c.request("POST", "/", body=b'{"jsonrpc":"2.0","id":0,"method":"eth_chainId","params":[]}', headers=UA); c.getresponse().read()   # warm the socket
    return c


def main():
    if subprocess.run(["systemctl", "is-active", "--quiet", "sniper-engine"]).returncode == 0:
        sys.exit("the engine is running: sudo systemctl stop sniper-engine first (same wallet, same nonce)")
    e = env(); key = e.get("PRIVATE_KEY"); wallet = e.get("WALLET"); url = e.get("RPC_URL") or "https://rpc.mainnet.chain.robinhood.com"
    if not key or not wallet:
        sys.exit("PRIVATE_KEY / WALLET missing from the env")
    acct = Account.from_key(key); wallet = to_checksum_address(wallet)
    ips = sorted({ai[4][0] for ai in socket.getaddrinfo(HOST, 443, socket.AF_INET)})
    if len(ips) < 2:
        sys.exit(f"{HOST} resolves to {ips}: nothing to race")
    conns = {ip: connect(ip) for ip in ips}
    print(f"{len(ips)} addresses for {HOST}: {ips}; {ROUNDS} rounds")
    wins = {ip: 0 for ip in ips}; none = 0; ties = 0; reply_ms = {ip: [] for ip in ips}; win_ms = []; spread_ms = []
    for r in range(ROUNDS):
        nonce = int(rpc(url, "eth_getTransactionCount", [wallet, "pending"]), 16); gp = int(rpc(url, "eth_gasPrice", []), 16) * 2
        tx = {"to": wallet, "value": 0, "gas": 21000, "gasPrice": gp, "nonce": nonce, "chainId": 4663, "data": b""}
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_sendRawTransaction", "params": ["0x" + bytes(acct.sign_transaction(tx).raw_transaction).hex()]}).encode()
        order = ips[r % len(ips):] + ips[:r % len(ips)]                   # rotate the thread order every round
        bar = threading.Barrier(len(ips)); out = {}

        def shoot(ip):
            c = conns[ip]
            try:
                bar.wait(timeout=5); t0 = time.perf_counter(); c.request("POST", "/", body=body, headers=UA); resp = json.loads(c.getresponse().read()); t1 = time.perf_counter()
                out[ip] = (t0, t1, "result" in resp, str(resp.get("result") or resp.get("error", {}).get("message", resp))[:60])
            except Exception as ex:
                out[ip] = (time.perf_counter(), time.perf_counter(), False, "EXC " + str(ex)[:60])
                try:
                    conns[ip] = connect(ip)
                except Exception:
                    pass
        ths = [threading.Thread(target=shoot, args=(ip,)) for ip in order]
        for t in ths: t.start()
        for t in ths: t.join()
        winners = [ip for ip in ips if out.get(ip, (0, 0, False))[2]]
        t0s = [out[ip][0] for ip in ips if ip in out]; spread_ms.append(1000 * (max(t0s) - min(t0s)) if len(t0s) > 1 else 0.0)
        for ip in ips:
            if ip in out: reply_ms[ip].append(1000 * (out[ip][1] - out[ip][0]))
        if len(winners) == 1:
            wins[winners[0]] += 1; win_ms.append(1000 * (out[winners[0]][1] - out[winners[0]][0]))
        elif not winners:
            none += 1
        else:
            ties += 1
        print(f"round {r + 1:2d} nonce {nonce}: " + "  ".join(f"{ip} {'WIN ' if out.get(ip, (0, 0, False))[2] else 'lost'} {1000 * (out[ip][1] - out[ip][0]):6.1f} ms {out[ip][3][:28]}" for ip in ips if ip in out) + f"  (send spread {spread_ms[-1]:.2f} ms)")
        # wait for the winner's receipt so the next nonce is clean
        h = next((out[ip][3] for ip in winners if out[ip][3].startswith("0x")), None); t_end = time.time() + 15
        while h and time.time() < t_end:
            try:
                if rpc(url, "eth_getTransactionReceipt", [h]): break
            except Exception:
                pass
            time.sleep(0.5)
        time.sleep(0.5)
    print()
    for ip in ips:
        print(f"{ip}: won {wins[ip]} of {ROUNDS} ({100 * wins[ip] / ROUNDS:.0f}%), reply median {st.median(reply_ms[ip]):.1f} ms" if reply_ms[ip] else f"{ip}: no replies")
    print(f"no winner {none}, more than one 'winner' {ties}; the local send spread between the threads was {st.median(spread_ms):.2f} ms median, {max(spread_ms):.2f} max; the winning reply took {st.median(win_ms):.1f} ms median" if win_ms else "no rounds decided")


main()
