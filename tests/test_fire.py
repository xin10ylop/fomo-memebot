"""fire() against the real endpoints with an unfunded throwaway key: the call must return the local hash right after the
socket writes, the replies must arrive in the background, and rejected() must turn True when every endpoint refuses"""
import os, sys, json, time
for line in open(sys.argv[1]):
    if "=" in line and not line.startswith("#"):
        k, v = line.strip().split("=", 1); os.environ.setdefault(k, v)
os.environ["LOG_PATH"] = "/tmp/claude-0/-home-user-fomo-memebot/a7a59693-7c2d-5b6c-b7df-e43fdbe7d612/scratchpad/test_fire.jsonl"; os.environ["SEND_MODULE"] = ""; os.environ["PRIVATE_KEY"] = ""
sys.path.insert(0, "/home/user/fomo-memebot/src/strategy"); import sniper_engine as E
from eth_account import Account
time.sleep(8)                                                     # let the keepalive open and measure the sockets
acct = Account.create()
tx = {"to": E.to_checksum_address("0x22464c128df67bea04830aefdea074671b7f0eb9"), "value": hex(10**15), "data": "0x", "gas": hex(60000), "gasPrice": hex(10**10), "nonce": "0x0", "chainId": 4663}
signed = acct.sign_transaction(tx); body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_sendRawTransaction", "params": ["0x" + bytes(signed.raw_transaction).hex()]}).encode()
for i in range(3):
    t0 = E.mono(); h, out = E.SENDER.fire(body); dt = 1000 * (E.mono() - t0)
    ok = h == "0x" + signed.hash.hex().replace("0x", "")
    early = len(out); ans = E.SENDER.answers(out, 3.0); dt2 = 1000 * (E.mono() - t0)
    print(f"fire returned in {dt:.2f} ms, hash matches signed hash: {ok}, answers at return: {early}, after wait: {len(ans)} in {dt2:.0f} ms, rejected: {E.SENDER.rejected(ans)}; " + "; ".join(f"{hh[:12]} {str(d.get('error', d))[:60]}" for hh, d in ans))
    time.sleep(1)
os._exit(0)
