# Creator fee runbook (Pons V2, Robinhood Chain)

This is the A-to-Z for the one launchpad income that does not require selling to anyone: the creator's share of the trading
fee on tokens you launch. It is written from the measurements in `REPORT.md` sections 13.2 and 14.2 and from the
transactions decoded in this repository. It is deliberately not a launch-and-dump playbook: three rules below are
non-negotiable, and the numbers assume you follow them.

## 0. What you are doing, in one paragraph

Every token launched on Pons V2 charges 1% on every trade on its bonding curve (and on the Uniswap v4 pool after
graduation). About 70% of that fee accrues to the token's creator, 30% to the protocol. The fee accrues in the protocol's
fee position and is claimed by the creator; it does not depend on the creator holding or selling anything. Launching costs
0.0005 ETH (≈ $1.22) plus gas (sponsored until early October 2026, cents afterwards). Across five six-hour windows in
August–September 2026 (`REPORT.md` section 13.3), a wallet's first launch of the day with a dust initial buy (under $5)
earned a fee share of $4–23 mean and $0–2.7 median inside the window, and 24–76% of such launches covered the launch fee.
That is the number for this runbook. The larger means quoted in section 13.2 ($12–44) come from creators who staked
$25–600 in the launch block, and a stake that is kept loses more than its fee earns on every measured day; the fee only
nets positive with a stake if the stake is sold into the first buyers, which is the dump this runbook excludes. The flow
that produces the fee is the bots and traders that buy every fresh launch; it rises and falls with the launchpad's fee
cycle, and it can stop.

**Bottom line before you read on:** one wallet, one launch a day, no stake, all rules followed: $3–21 a day in mean,
$0–2.7 in median, a third to a half of days earning nothing beyond the $1.22 lost. Extra launches from the same wallet
earn roughly nothing each (section 13.3 (c)), because the bots buy first-time creators. This is a few dollars a day, not
an income; the rest of the document is here so the number can be checked and the mechanics are on record.

## 1. Rules (these are what make it not a rug)

1. **No launch-block buy that you sell into the first minutes.** Launch with a dust initial buy you intend to keep
   (0.00001 ETH is the smallest used on the chain; no creation in the 48,048 sampled had a zero buy, and whether the
   contract accepts zero is untested), or if you buy more, do not sell it for at least a day and expect to lose it. Selling the creator's buy into the first buyers is
   the launch-and-dump measured in sections 13–13.1; it is excluded here.
2. **No impersonation.** Do not name tokens after existing tokens, projects, people, or trending tickers. Original names only.
3. **No promotion claims.** No "team", "roadmap", "partnership" or price talk anywhere (name, symbol, image, metadata).
4. No bundle wallets, no wash trading, no buying your own token from other wallets.

If any of these is inconvenient, the strategy is not for you; the numbers below do not hold for the alternative and the
alternative is the scheme this repository declined to build.

## 2. Prerequisites

* A Robinhood Chain (chain id 4663) wallet you control, funded with ETH: 0.0005 ETH per launch plus a small gas buffer
  (0.02 ETH covers weeks). A hardware wallet or a fresh key used only for this.
* Public RPC `https://rpc.mainnet.chain.robinhood.com` (needs a browser-like User-Agent; batches ≤ 100; rate-limited).
* Python 3 with `web3` / `eth_account` for signing (the repository does not include a launch script; see §4).
* The two read-only tools in this repository:
  * `src/analysis/creator_fee_gauge.py` tells you whether the current flow is paying (last N hours of first-time creators:
    fee per launch mean / median / share covering the fee).
  * `src/analysis/creator_fee_tracker.py <your address>` lists every token you launched, its trades, volume and accrued fee share.

## 3. Go / no-go before each session

Run the gauge for the last two hours:

```
python3 src/analysis/creator_fee_gauge.py --hours 2
```

* Read the first line, "single launch, initial buy < $5": that is your cohort. Go if its median is ≥ $1 and ≥ 50% of
  those launches cover the launch fee (the measured windows printed medians of $0.03–2.7 and 24–76% covering; only
  Aug 27 and Sep 2 pass this bar). Ignore the "initial buy ≥ $5" line unless you are willing to lose the stake.
* No-go if the first line's median is under $0.5 or fewer than a third of the launches cover the fee. Do not launch into a dead hour to "catch
  the next wave"; the fee is earned on flow that exists now.
* Also no-go: the day the gas subsidy ends until you have measured the real per-launch gas cost (a creation is 3–7M gas;
  at the Sep 1–2 congestion prices that was $20–60, which would erase the median launch).

## 4. The launch transaction (facts decoded from real creations)

* Contract: Pons V2 factory `0xe33e9e479df8802cb0866d5d05258bec4cf62948`, function selector `0xf85f8e41`.
* `value` = 0.0005 ETH launch fee + the initial buy amount (0 if none) for ETH-quoted launches.
* Calldata layout (ABI-encoded): a tuple at arg0 (offset 0xe0) holding the `name`, `symbol` and `uri` strings (the uri is
  an `ipfs://…` image/metadata pointer) and the creator/fee-recipient address; top-level args carry the quote asset
  (`0x0000…0000` for native ETH; a token address for USDG/NVDA/MU-quoted curves), the initial buy amount, and the
  creator address. The simplest correct way to build it is to copy the calldata of an existing ETH-quoted creation
  (any recent event from the factory; e.g. the one decoded in the session had `value` 0.0105 ETH = 0.0005 fee + 0.01 buy)
  and substitute name, symbol, uri, creator address and amounts. Verify on a first launch with no initial buy.
* The creation emits the factory event with topics `[sig, token, curve, creator]`; the curve contract is where trading
  happens (Buy `0xec36bf57…`, Sell `0x8113d738…` events) until graduation at 4.2 ETH into a Uniswap v4 pool.
* Quote asset: use native ETH. ETH-quoted launches earned the highest fee per launch in the sample (pooled ROI on stake
  +49% vs +27% for USDG-quoted); stock-quoted curves need the stock token on hand.

## 5. Naming and metadata policy

* Original two-word or invented names, a 3–6 letter symbol that is not an existing ticker on the chain (check with
  fomoapi `/v2/tokens/search?q=` or DexScreener before launching), an image you made or have rights to, pinned to IPFS.
* Keep a list of everything you launched with the transaction hash, token, curve, name, symbol.

## 6. Cadence and sizing

* One launch per wallet per day, with a dust initial buy. That is the only cohort measured positive: $4–23 mean fee
  per launch, $0–2.7 median (section 13.3 (a), the "< $5" column).
* Do not batch. The second to ninth launches from the same wallet in a day earned a quarter or less of the first and the
  tenth onward about the launch fee or less on every measured day (section 13.3 (c)), because the sniper bots that
  supply the fee buy first-time creators only. Twenty launches from one wallet are worth $0–5 net each, not twenty
  times the one-off number.
* Do not open fresh wallets to get around that. One wallet per launch is exactly the serial-launcher pattern of
  section 13.1, and it is excluded from this runbook.
* Do not seed the curve with a real stake to attract the bots. It raises the fee (a $100+ stake earned $26–53 of fee
  per launch) but the stake itself ended 50–90% down in every window, so the kept-stake version nets −$150 to −$490
  per launch (section 13.3 (b)). The only way that cohort is positive is to sell the stake, which is rule 1.
* Re-measure with the tracker after 20 launch-days. Continue only if the fee income is at least 3× the launch fees paid.

## 7. Claiming

Fees do not arrive in your wallet per trade (a buy's full quote amount goes into the curve; the fee is accounted, not paid
out). They are claimed from the protocol's fee position: the Pons app exposes the claim for the creator address; on-chain
it is the locker contract's claim call (the V1 locker was `0x736d76699c26d0d966744cae304c000d471f7f35`; for V2 copy the
app's claim transaction once and reuse its calldata). Claim weekly or when the tracker shows more than ~$50 accrued;
claiming costs gas only.

## 8. Tracking and kill criteria

* Daily: `creator_fee_tracker.py <address>` for the running total; the gauge before each session.
* Kill the whole thing if: the gauge median stays under $1 for three sessions in a row; Pons changes the fee split or the
  launch fee; the gas subsidy ends and a creation costs more than the median launch earns; or the bots that buy fresh
  launches disappear (the gauge's "launches nobody else traded" line rising above ~60%).

## 9. What this is not

It is not a trade and it has no edge in the market sense: you are being paid the launchpad's creator share for supplying
tokens that bots and traders churn. The income is a lottery ticket with a positive mean on days with flow and a near-zero
median on days without; the tail is tokens that happen to run, and you do not control that. Measured under its own rules
it is $3–21 a day per wallet in mean and $0–2.7 in median, and it does not scale, because every way of scaling it (more
launches per wallet, more wallets, a real stake) is either measured to earn nothing or is the dump. It contributes to the launch
spam the chain's 0.077% survival rate describes. The repository documents it because it is one of the two seats that
actually earned during the study; it does not include a launcher, and the author of this runbook would not run it at scale.
