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
August–September 2026, a first-time creator's fee share inside the window was $12–44 mean and $2–11 median per launch,
58–93% of launches covered the launch fee, and tokens with a tiny or no initial buy still averaged $9–22. The flow that
produces those fees is the bots and traders that buy every fresh launch; it rises and falls with the launchpad's fee
cycle, and it can stop.

## 1. Rules (these are what make it not a rug)

1. **No launch-block buy that you sell into the first minutes.** Either launch with no initial buy (or a trivial one you
   intend to keep), or if you buy, do not sell it for at least a day. Selling the creator's buy into the first buyers is
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

* Go if the median fee per first-time launch is ≥ $2 and ≥ 60% of launches cover the launch fee (the trough day, Aug 20,
  printed $2.1 / 58%; the peak day $10.8 / 89%).
* No-go if the median is under $1 or fewer than half the launches cover the fee. Do not launch into a dead hour to "catch
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

* Start with 20 launches at zero initial buy over one "go" session. Expected on the measured days: $12–44 mean and
  $2–11 median per launch, so $240–880 mean for the batch against $24 of launch fees, with most of it in one or two
  launches (the top 5% of launches are 36–65% of the fees).
* Stop and re-measure with the tracker after 20. Continue only if the batch's fee income is at least 3× its launch fees.
* If you add an initial buy to seed the curve (measured: a moderate buy roughly doubles fee income versus none), it is
  capital you are choosing to hold, not a trade; size it as something you can lose in full, because 92% of launches end
  below their first price.
* Rate: 30–60 launches an hour is the pace of the serial launchers in the census; there is no measured benefit to more,
  and the chain already sees 28,000 launches a day. Do not run more than one wallet.

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
median on days without; the tail is tokens that happen to run, and you do not control that. It contributes to the launch
spam the chain's 0.077% survival rate describes. The repository documents it because it is one of the two seats that
actually earned during the study; it does not include a launcher, and the author of this runbook would not run it at scale.
