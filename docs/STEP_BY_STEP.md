# Step by step: from nothing to the first thirty live trades

Plain words, in order. Budget: about $120 ($100 of trading money, $20 for the machine, the bridge and gas). Time: about
a week. Every command below runs on the Ohio machine unless it says "on your computer". The engine never signs
anything until step 14, and even then only with the file you copy in step 14.

Send me two things when the guide says so: the engine's log file and, later, the output of the checker. I read them and
tell you what to change. Never send the private key to anyone, including me.

## Day 0: accounts (about one hour)

1. **AWS.** Make an account at aws.amazon.com. In the console, top right, set the region to **US East (Ohio)**. Go to EC2,
   click *Launch instance*: name `sniper`, image **Ubuntu Server 24.04**, type **t3.small**, create a new key pair
   (download the `.pem` file, keep it), storage 20 GB, and in *Network settings* allow SSH **from My IP only**. Launch.
   Copy the instance's public IP from the list. Cost: about $0.60 a day.
2. **Provider key.** Make a free account at alchemy.com. Create an app, choose the network **Robinhood Chain**, and copy
   its two addresses: the HTTPS one (`https://robinhood-mainnet.g.alchemy.com/v2/...`) and the WebSocket one
   (`wss://robinhood-mainnet.g.alchemy.com/v2/...`). Free tier is enough.
3. **Connect.** On your computer, in a terminal:
   `ssh -i sniper.pem ubuntu@YOUR.IP` (on Mac or Linux first run `chmod 400 sniper.pem`). You are on the machine.

## Day 0: install (ten minutes)

4. Get the code and install everything:
   ```
   git clone https://github.com/xin10ylop/fomo-memebot.git
   cd fomo-memebot
   git checkout claude/memecoin-strategy-research-vcdy6c
   sudo bash deploy/ohio_setup.sh
   ```
   This installs the clock sync, Python, the engine as a service in **dry run** (it watches and logs, sends nothing).
5. **Make the wallet on the machine.** This wallet is used for nothing else, ever.
   ```
   /opt/sniper-venv/bin/python3 -c "from eth_account import Account; a=Account.create(); k=a.key.hex(); print('ADDRESS', a.address); print('KEY', k if k.startswith('0x') else '0x'+k)"
   ```
   Write both lines down somewhere safe (a password manager). The ADDRESS is public. The KEY is the money.
6. **Fill in the settings file:** `sudo nano /etc/sniper/engine.env`. Change only these lines, leave the rest:
   ```
   RPC_URL=<the HTTPS address from step 2>
   PROVIDER_WS=<the WebSocket address from step 2>
   WALLET=<your ADDRESS from step 5>
   BANKROLL_USD=100
   ```
   Leave `SEND_MODULE=` and `PRIVATE_KEY=` empty for now. Save (Ctrl-O, Enter, Ctrl-X). Then
   `sudo systemctl restart sniper-engine`.
7. **See it run:** `tail -f /var/log/sniper/engine.jsonl`. Within a minute you see a `start` line and `feed_connected`;
   within a few minutes `creation` lines. Ctrl-C to stop watching (the engine keeps running). Then run the latency
   probe once and leave it ten minutes:
   `sudo systemctl start sniper-probe && sleep 620 && cat /var/log/sniper/latency_probe.json`.

## Day 1: the dry-run day

8. Leave it alone for 24 hours. The engine logs every launch, what it would have done, and scores every launch the way
   the tables do. Nothing is sent.
9. Next day, get me the log. On your computer:
   `scp -i sniper.pem ubuntu@YOUR.IP:/var/log/sniper/engine.jsonl engine_day1.jsonl`
   and either upload it to me here or put it in the repository (`data/live/engine_day1.jsonl`) and push. I check the
   timing numbers (the send 300 ms after the seat's second, the wake under a millisecond, the round trip to the
   sequencer a few milliseconds), that the feed and the chain agree on every gate, and the two readouts. If something
   is off I tell you what to change in `engine.env` (usually one number).

## Day 1: money on the chain ($110)

10. Buy about $110 of ETH on the exchange you already use. Withdraw it to a wallet in your browser (MetaMask or Rabby)
    on the **Base** network (the cheap withdrawal). Do not withdraw to the machine's address yet: bridges need a
    browser wallet to click through.
11. In the browser wallet, bridge from Base to **Robinhood Chain** with a bridge that lists it (relay.link is the usual
    one; Across or LiFi if not). Bridge ETH, not a token. A few dollars of fees, a few minutes.
12. Add Robinhood Chain to the browser wallet if the bridge did not do it (chain id **4663**, RPC
    `https://rpc.mainnet.chain.robinhood.com`, currency ETH). Then send the ETH from the browser wallet to the machine's
    ADDRESS from step 5, as a normal transfer on Robinhood Chain. Keep about $1 of ETH in the browser wallet for later.
13. Check it arrived, on the machine:
    ```
    /opt/sniper-venv/bin/python3 -c "import json,urllib.request;r=urllib.request.urlopen(urllib.request.Request('https://rpc.mainnet.chain.robinhood.com',data=json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_getBalance','params':['YOUR_ADDRESS','latest']}).encode(),headers={'Content-Type':'application/json'}));print(int(json.load(r)['result'],16)/1e18,'ETH')"
    ```

## Day 2: the first five real trades ($25 each)

14. Turn the send step on. It is one file, already written and tested:
    ```
    sudo cp deploy/send_step.py /etc/sniper/send_step.py
    sudo chmod 600 /etc/sniper/send_step.py
    sudo nano /etc/sniper/engine.env
    ```
    set these three lines, save:
    ```
    SEND_MODULE=/etc/sniper/send_step.py
    PRIVATE_KEY=<your KEY from step 5>
    STAKE_MAX=25
    ```
    then `sudo systemctl restart sniper-engine`. In the log the `start` line now says `"dry_run": false` and a
    `send_step_loaded` line names your address. If the key and the address do not match, the engine refuses to start
    and says so. From now on the engine reads your real balance and stakes 15% of it, never less than $25, never more
    than `STAKE_MAX`.
15. Wait for five trades. Count them with `grep -c trade_done /var/log/sniper/engine.jsonl`. On a busy day that is an
    hour or two; on a quiet one, longer. Each trade is $25, held about five seconds.
16. Run the checker:
    ```
    cd ~/fomo-memebot && /opt/sniper-venv/bin/python3 src/analysis/live_check.py /var/log/sniper/engine.jsonl --rpc <your HTTPS address>
    ```
    Read the table. Every row must say `first block` or `later block` (never EARLY or LATE), `sold 100%`, and
    `vs target` better than −25%. If any row fails: `sudo systemctl stop sniper-engine`, send me the log and the
    checker's output, and wait. If all pass, go on.

## Day 2 to 5: thirty trades

17. Let the stake follow the bankroll: in `engine.env` set `STAKE_MAX=300` (back to normal), restart. With $100 the
    stake stays $25 until the bankroll passes $167; then it grows with it. Leave it running.
18. At thirty trades (`grep -c trade_done ...` again) run the checker again. Its last line is the verdict:
    - "matches the engine's scores": the tables apply to your machine. Leave it running; it compounds by itself. Send me
      the log anyway so I can read the thirty.
    - "below the engine's score ... interval excludes zero": stop the engine, send me the log and the output. This is a
      timing or seat problem on the machine, not the market, and it is mine to find.
    - "too few trades": wait for more.

## Every evening (two minutes)

19. `grep '"ev": "flow"' /var/log/sniper/engine.jsonl | tail -1` shows the day in five numbers:
    `rule_passing_last_6h` (busy day above 40), `mean_score_last_60` (should be above +0.03; below that the day does
    not pay for gas), `follow_eth_last_60` (the demand: about 0.26 in September, under 0.2 means a thin day),
    `out1_share_last_60` (the crowding: about 0.6 in September) and `bankroll_usd` (your money, from the wallet).
20. The engine stops itself for the day if the bankroll falls to half of where the day started. You stop it yourself
    (`sudo systemctl stop sniper-engine`) if the checker's live mean over thirty trades is below zero while the
    engine's scores of the same launches are above +5%, or if the log shows `alarm` lines.

## After the thirty trades

21. Add money only after step 18 passed: send more ETH to the same ADDRESS on Robinhood Chain; the engine picks up the
    new balance by itself. Nothing else to change. Stakes are capped at $300 (`STAKE_MAX`), which is the curve's depth,
    not a setting to raise.
22. The E1 seat test (runbook section 9) waits until the bankroll has $60 to spare and needs a c6i.large instead of the
    t3.small. Ask me when you are there.

## If something breaks

- The engine restarts itself on any crash and closes an open position first. `sudo systemctl status sniper-engine`
  shows whether it is running; `sudo journalctl -u sniper-engine -n 50` shows why it stopped.
- `feed_error` lines with a backoff mean the feed refused the connection; five in a row and the engine switches to the
  provider by itself (`PROVIDER_WS`).
- To move the money out: the engine only ever holds ETH between trades. Stop the engine, then send the ETH from the
  machine's wallet with the same kind of one-line script as step 13, or import the KEY into the browser wallet once,
  send, and never use that browser wallet for anything else afterwards.
