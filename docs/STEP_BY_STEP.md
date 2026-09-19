# Step by step, click by click: DigitalOcean machine, Phantom wallet, first thirty live trades

Budget about $120: $100 of trading money, about $10 of fees, a $6-a-month machine. The machine is in New York, the
nearest DigitalOcean region to the chain's sequencer in Ohio (about 10–15 ms away, which is fine for the seat this
runs: the engine sends a fixed 0.3 s after the second opens). The faster Ohio machine is only needed later, for the E1
seat test.

Rules that never change: the machine's wallet key stays on the machine and in your password manager, nowhere else.
Never send the key to anyone, including me. The engine sends nothing until step 24.

---

## Part 1. The machine (30 minutes)

**1. Make a DigitalOcean account.** Open `https://cloud.digitalocean.com/registrations/new`. Sign up with email,
confirm the email, add a card. (New accounts often get free credit; if you see one, take it.)

**2. Make an SSH key on your computer.** Open a terminal (Mac: *Terminal*; Windows: *PowerShell*). Paste:
```
ssh-keygen -t ed25519 -f ~/.ssh/sniper -N ""
```
then show the public half:
```
cat ~/.ssh/sniper.pub
```
Copy the whole line that starts with `ssh-ed25519`.

**3. Create the droplet.** In the DigitalOcean console click the green **Create** button (top right) → **Droplets**.
- *Choose Region*: **New York**. Datacenter: **NYC3** (any NYC works).
- *Choose an image*: **Ubuntu**, version **24.04 (LTS) x64**.
- *Choose Size*: **Basic** → CPU options **Regular** → the **$6/mo** box (1 GB / 1 vCPU / 25 GB).
- *Choose Authentication Method*: **SSH Key** → **New SSH Key** → paste the `ssh-ed25519 ...` line, name it `sniper`,
  **Add SSH Key**.
- *Finalize Details*: Hostname `sniper`. Click **Create Droplet**.
After a minute the droplet shows an IP address like `143.198.x.x`. Copy it. Below it is called `YOUR.IP`.

**4. Connect.** In your terminal:
```
ssh -i ~/.ssh/sniper root@YOUR.IP
```
Type `yes` when asked about the fingerprint. You are now on the machine (the prompt says `root@sniper`).

**5. Install everything.** Paste these four lines, one at a time, on the machine:
```
git clone https://github.com/xin10ylop/fomo-memebot.git
cd fomo-memebot
git checkout claude/memecoin-strategy-research-vcdy6c
bash deploy/ohio_setup.sh
```
It runs three to five minutes. The last lines say the engine service is enabled and the probe command. The engine is
now running in **dry run** (watching, logging, sending nothing).

**6. Make the machine's wallet.** On the machine paste:
```
/opt/sniper-venv/bin/python3 -c "from eth_account import Account; a=Account.create(); k=a.key.hex(); print('ADDRESS', a.address); print('KEY', k if k.startswith('0x') else '0x'+k)"
```
It prints two lines. Put both in your password manager now. `ADDRESS` (starts `0x`, 42 characters) is public.
`KEY` (starts `0x`, 66 characters) is the money.

---

## Part 1b. The Ohio machine on AWS (30 minutes; needed for the next-second seat, runbook 5e)

**1. Make an AWS account.** Open `https://aws.amazon.com` → **Create an AWS Account**. Email, password, account name;
then contact details, a card, a phone verification code, and the **Basic support** plan (free). It takes about ten
minutes; the console is at `https://console.aws.amazon.com`.

**2. Pick the region.** In the console, top right, the region menu: choose **US East (Ohio) us-east-2**. Everything
below happens in that region; if the menu shows anything else, the machine is in the wrong place.

**3. Launch the instance.** Search box at the top: type **EC2**, open it. Left menu **Instances** → orange **Launch
instances**.
- *Name*: `sniper-ohio`.
- *Application and OS Images*: **Ubuntu** → **Ubuntu Server 24.04 LTS (HVM)**, architecture **64-bit (x86)**.
- *Instance type*: **c6i.large** (2 vCPU, 4 GiB; about $2 a day). A t3.small is enough for a paper day, not for the race.
- *Key pair (login)*: **Create new key pair** → name `sniper-ohio`, type **ED25519**, format **.pem** → **Create key
  pair**. The browser downloads `sniper-ohio.pem`. Move it into `~/.ssh/` and run `chmod 400 ~/.ssh/sniper-ohio.pem`.
- *Network settings*: leave the default VPC and subnet; **Allow SSH traffic from** → **My IP**.
- *Configure storage*: **20 GiB gp3**.
- **Launch instance**. After a minute, open the instance: its **Public IPv4 address** is `OHIO.IP` below.

**4. Connect** (the user is `ubuntu`, not root):
```
ssh -i ~/.ssh/sniper-ohio.pem ubuntu@OHIO.IP
```

**5. Install** (three to five minutes; the engine starts in dry run):
```
sudo apt-get install -y git && git clone https://github.com/xin10ylop/fomo-memebot.git && cd fomo-memebot && git checkout claude/memecoin-strategy-research-vcdy6c && sudo bash deploy/ohio_setup.sh
```

**6. Move the settings and the key from the droplet**, through your laptop, then delete the copy. On the laptop:
```
scp -i ~/.ssh/sniper root@DROPLET.IP:/etc/sniper/engine.env ~/engine.env && scp -i ~/.ssh/sniper-ohio.pem ~/engine.env ubuntu@OHIO.IP:/tmp/engine.env && rm ~/engine.env
```
On the Ohio machine (paper first: the send step is off until the feed lag is measured and the burst calibrated):
```
sudo install -m 600 /tmp/engine.env /etc/sniper/engine.env && rm /tmp/engine.env && sudo cp ~/fomo-memebot/deploy/send_step.py /etc/sniper/send_step.py
sudo sed -i 's|^SEND_MODULE=.*|SEND_MODULE=|' /etc/sniper/engine.env && sudo systemctl restart sniper-engine
```

**7. Stop the droplet's engine** once its current test is over, so two engines never share the wallet's nonces:
```
sudo systemctl disable --now sniper-engine
```

Then runbook 5e: the feed-lag probe, the calibration burst, the landing test.

## Part 2. The node key (5 minutes)

**7. Alchemy account.** Open `https://www.alchemy.com`, **Sign up** (free). In the dashboard click **Create new app**:
name `sniper`, and under *Networks* tick **Robinhood Chain** (mainnet). Create.

**8. Copy the two addresses.** Open the app → **Network** tab (or the **API key** button). Copy:
- the **HTTPS** URL, looks like `https://robinhood-mainnet.g.alchemy.com/v2/AbC123...`
- the **WebSockets** URL, looks like `wss://robinhood-mainnet.g.alchemy.com/v2/AbC123...`

**9. Put them in the settings file.** On the machine:
```
nano /etc/sniper/engine.env
```
Use the arrow keys. Change these four lines only (replace everything after the `=`):
```
RPC_URL=https://robinhood-mainnet.g.alchemy.com/v2/AbC123...
PROVIDER_WS=wss://robinhood-mainnet.g.alchemy.com/v2/AbC123...
WALLET=0xYourADDRESSfromStep6
BANKROLL_USD=100
```
Save: **Ctrl-O**, **Enter**. Exit: **Ctrl-X**. Then restart the engine:
```
systemctl restart sniper-engine
```

**10. See it live.** On the machine:
```
tail -f /var/log/sniper/engine.jsonl
```
Within a minute: a line with `"ev": "start"`, then `"ev": "feed_connected"`, then within a few minutes lines with
`"ev": "creation"`. Press **Ctrl-C** to stop watching; the engine keeps running.

**11. The ten-minute latency probe** (once):
```
systemctl start sniper-probe && sleep 620 && cat /var/log/sniper/latency_probe.json
```

---

## Part 3. The dry-run day

**12. Wait 24 hours.** Do nothing. The engine logs every launch and scores each one exactly as the tables do.

**13. Send me the log.** On your computer (not the machine):
```
scp -i ~/.ssh/sniper root@YOUR.IP:/var/log/sniper/engine.jsonl engine_day1.jsonl
```
Upload `engine_day1.jsonl` to me here. I check that the send is 300 ms after the second opens, the wake-up is under a
millisecond, the round trip to the sequencer, that the feed and the chain agree on every gate, and the two readouts.
If one setting needs changing I tell you which line.

---

## Part 4. Money on the chain with Phantom (20 minutes, about $110)

Phantom supports Robinhood Chain natively (added July 2026). You do not need any other wallet.

**14. Turn the network on.** Update Phantom to the latest version. In Phantom: **Settings** (the gear or your avatar,
bottom right) → **Active Networks** → switch **Robinhood Chain** on. Go back.

**15. Get ETH into Phantom.** On your exchange, withdraw about **$110 of ETH** to Phantom. Two ways, best first:
- If the exchange's withdrawal screen offers **Robinhood Chain** as the network, pick it and send to your Phantom
  address for Robinhood Chain (in Phantom: **Receive** → choose **Robinhood Chain** → copy the address). Done; skip 16.
- Otherwise withdraw ETH on the **Base** network to Phantom's Base address (**Receive** → **Base**). Cheapest
  withdrawal, arrives in minutes.

**16. Move it to Robinhood Chain inside Phantom.** In Phantom open the **Trade** tab (the arrows icon). Tap the
**You Pay** selector → network **Base** → token **ETH** (if Base is not offered here, pick **Ethereum**; if neither,
use step 16b). Tap the **You Receive** selector → network **Robinhood Chain** → token **ETH**. Enter the amount (all
of it minus a little for the Base fee), tap **Swap**, confirm. A few minutes and a few dollars of fees.

*16b, only if Phantom does not offer the route:* open `https://relay.link/bridge/robinhood` in the browser where the
Phantom extension is installed, **Connect** → Phantom, *From* **Base ETH**, *To* **Robinhood Chain ETH**, amount, and
confirm in Phantom.

**17. Send it to the machine.** In Phantom: **Send** → asset **ETH on Robinhood Chain** → paste the machine's
`ADDRESS` from step 6 → send all except about $1 (keep a little RH ETH in Phantom for fees later). Confirm.

**18. Check it arrived.** On the machine (replace the address):
```
/opt/sniper-venv/bin/python3 -c "import json,urllib.request;r=urllib.request.urlopen(urllib.request.Request('https://rpc.mainnet.chain.robinhood.com',data=json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_getBalance','params':['0xYourADDRESS','latest']}).encode(),headers={'Content-Type':'application/json'}));print(int(json.load(r)['result'],16)/1e18,'ETH')"
```
It prints something like `0.041 ETH`.

---

## Part 5. The first five real trades ($25 each)

**19. Copy the send step into place.** On the machine:
```
cp deploy/send_step.py /etc/sniper/send_step.py
chmod 600 /etc/sniper/send_step.py
```

**20. Turn it on.** `nano /etc/sniper/engine.env`, set these three lines, save (Ctrl-O, Enter, Ctrl-X):
```
SEND_MODULE=/etc/sniper/send_step.py
PRIVATE_KEY=0xYourKEYfromStep6
STAKE_MAX=25
```

**21. Restart and check.**
```
systemctl restart sniper-engine
sleep 5
grep -o '"dry_run": [a-z]*' /var/log/sniper/engine.jsonl | tail -1
grep send_step_loaded /var/log/sniper/engine.jsonl | tail -1
```
The first prints `"dry_run": false`, the second shows your address. If the engine did not start, run
`journalctl -u sniper-engine -n 20`: a line saying the key does not match `WALLET` means a typo in step 9 or 20.

**22. Wait for five trades.** Count them:
```
grep -c trade_done /var/log/sniper/engine.jsonl
```
On a busy day that is one to three hours. Each trade puts $25 in for about five seconds.

**23. Run the checker.** On the machine (replace with your HTTPS address from step 8):
```
cd /root/fomo-memebot && /opt/sniper-venv/bin/python3 src/analysis/live_check.py /var/log/sniper/engine.jsonl --rpc https://robinhood-mainnet.g.alchemy.com/v2/AbC123...
```
Read the table. Every row must show `first block` or `later block` in the *landed* column (never EARLY or LATE),
`100%` in *sold*, and *vs target* not worse than −25%. If any row fails:
```
systemctl stop sniper-engine
```
then send me the log and the checker's output and wait for my answer. If all five pass, continue.

---

## Part 6. Thirty trades

**24. Let the stake follow the money.** `nano /etc/sniper/engine.env`, change `STAKE_MAX=25` to `STAKE_MAX=300`,
save, then `systemctl restart sniper-engine`. The engine now reads your wallet's real balance every few seconds and
stakes 15% of it, never under $25. With $100 that is $25 a trade until the balance passes $167. Profits are staked
again by themselves; you do nothing.

**25. At thirty trades** (`grep -c trade_done ...`) run the checker of step 23 again and read its last line:
- **"matches the engine's scores"**: the tables hold on your machine. Leave it running. Send me the log anyway.
- **"below the engine's score ... interval excludes zero"**: `systemctl stop sniper-engine`, send me the log and the
  output. That is a timing problem on the machine, mine to find, not the market.
- **"too few trades"**: wait.

---

## Every evening (two minutes)

**26.** On the machine:
```
grep '"ev": "flow"' /var/log/sniper/engine.jsonl | tail -1
```
Five numbers: `rule_passing_last_6h` (a busy six hours is above 40), `mean_score_last_60` (should be above 0.03),
`follow_eth_last_60` (the demand: about 0.26 lately; under 0.2 is a thin day, expect little), `out1_share_last_60`
(the crowding: about 0.6 lately) and `bankroll_usd` (your money, read from the wallet).

**27.** The engine stops itself for the day when the money falls to half of the day's start, and closes any open
position on a crash or restart. You stop it by hand (`systemctl stop sniper-engine`) if the checker's live mean over
thirty trades is below zero while the engine's own scores are above +0.05, or if you see `"ev": "alarm"` lines.

---

## After the thirty trades

**28. Add money** only after step 25 passed: in Phantom, **Send** ETH on Robinhood Chain to the same `ADDRESS`. The
engine picks the new balance up by itself. Stakes are capped at $300 (`STAKE_MAX`); that cap is the curve's depth,
not a knob to raise.

**29. Take money out:** stop the engine, then on the machine send ETH from the wallet to your Phantom address with the
same kind of one-line script as step 18 (ask me for it when you are there), or import the KEY into a fresh wallet once.

**30. The E1 seat test** (runbook section 9) needs $60 to spare and a two-core machine in Ohio (AWS c6i.large). Ask me Since Sep 18 the test runs with the burst send of runbook 5e (engine 5.6): ten launches at $100, `BURST_N=5`, and `src/analysis/landing_check.py --log` reads where every shot landed.
when the bankroll is there.

---

**31. One buy per launch with any bet: the relay (Sep 19).** The burst sends many shots at one launch and, without help,
every shot after the first one also buys (Part 24.24 of the report: the night of Sep 18). Engine 5.93 stopped that by
betting the whole wallet; the relay contract stops it for any bet. Deploy it once, engine stopped, on Ohio:

```
sudo systemctl stop sniper-engine; cd ~/fomo-memebot && git pull origin claude/memecoin-strategy-research-vcdy6c && sudo /opt/sniper-venv/bin/python3 ~/fomo-memebot/deploy/relay_deploy.py --write-env
```

It shows the cost (a few cents), asks `deploy the BuyOnce relay now? (yes/no)`, type `yes`. It then verifies the
contract on the chain and writes `RELAY=0x...` into `/etc/sniper/engine.env` by itself. Set the bet and restart:

```
for kv in STAKE_MIN=15 STAKE_MAX=15; do k=${kv%%=*}; sudo sed -i "/^$k=/d" /etc/sniper/engine.env; echo "$kv" | sudo tee -a /etc/sniper/engine.env > /dev/null; done; sudo systemctl restart sniper-engine
```

From then on every launch bets $15 (change both numbers for another bet) and the wallet may hold any amount.

**32. The relay with the deadline (Sep 19, engine 5.96).** The relay now refuses to buy in a block after the seat's
second, so a burst the sequencer includes late costs a cent instead of a bad buy. It is a new contract: run step 31's
deploy command again (engine stopped, it writes the new address by itself), then restart. The engine refuses to start on
the old relay, so if it says "does not know the deadline", that is the reminder to run the deploy command.

## If something looks wrong

- `systemctl status sniper-engine` says whether it runs; `journalctl -u sniper-engine -n 50` says why it stopped.
- `feed_error` lines with growing waits mean the feed refused the machine; after five refusals in a row the engine
  switches to the Alchemy WebSocket by itself.
- `receipt_timeout` or `buy_reverted` in the log: stop the engine, send me the log.
- Lost the SSH key: the droplet's **Access** tab in the DigitalOcean console has a **Recovery Console**.
