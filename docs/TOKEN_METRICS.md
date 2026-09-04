# Memecoin fundamentals per token and per trader

Generated 2026-09-04 07:51 UTC from `data/derived/token_metrics.json`, `data/derived/trader_entry_metrics.json`, `data/derived/entry_outcomes.json`.

This answers "at what market cap, how old, on which launchpad, with which holders and which dev did each leaderboard trader enter?", for every meme in `docs/MEMES.md` and every priced entry in `data/derived/positions_all.csv.gz` (columns `entry_fdv_usd`, `age_at_entry_min`, `launchpad`, `token_created`, `trader_is_dev`, `fdv_now`).

**Definitions and sources**

* **Entry FDV** = entry price × total supply. Entry price is fomo's `avgEntryPrice` for app positions, or fill USD ÷ amount for on-chain fills (Robinhood fills priced from GeckoTerminal candles at the block time, Solana fills from the USDC/SOL leg). Supply from GeckoTerminal (`total_supply`), else DexScreener FDV ÷ price. Tokens with no supply (dead, no pool anywhere) are the `unknown` bucket: that bucket is where most Solana losers live, so every "known FDV" number is survivor-biased upward.
* **Token created** = Robinhood mint block (first Transfer from 0x0, timestamp interpolated from block anchors), else DexScreener `pairCreatedAt`, else the earliest GeckoTerminal base pool. A DexScreener/GT pool can post-date the token, which is why a few entries show negative age (`before pool (data err)`).
* **Launchpad**: Solana by mint suffix (`pump`, `bonk`, `BAGS`); Robinhood by the mint-tx factory (Pons factory `0xa5aa…`), the DexScreener pool label (v3 = Pons V1 fixed pool, v4 = Pons V2 hook/curve) and the quote asset (a stock token quote = LONG stock-paired launch).
* **Dev**: Robinhood deployer = `from` of the mint transaction; `fee_recipient` = Pons locker `feeRedirects(token)` (returned zero for every token checked, so creator-fee redirection is not readable this way). fomoapi's holders endpoint carries an `isDev` flag: it was `false` for all 787 tracked holder rows pulled. Solana creators were not resolved (pump.fun creator lives in the bonding-curve account; not pulled to save Helius credits).
* **Holders**: fomo's token boards (trending / most-held / graduated, 30-minute snapshots) give a total holder count and `fomoBuyers` for the ~60 tokens that make those boards; `/token/{address}/holders` gives the top-50 fomo-tracked holders (amount, cost basis, PnL) for the 160 most-traded memes. There is no cheap full holder count for the long tail (Blockscout is gated on Robinhood Chain); on-chain holder reconstruction was not done.

## Does entry market cap / age / launchpad predict the leaders' results?

One row per (trader, token) with a fully priced on-chain history (every buy and sell priced), meme tokens only, ≥ $20 invested. `cons` = realized proceeds − invested with any remaining bag at zero; `mtm` = remaining bag at today's DexScreener price (no impact, no liquidity check: this is the fomo-leaderboard way of counting). CI = 95% token-clustered bootstrap of the pooled conservative ROI. Read the `unknown` FDV row as the dead-token row.

```
positions (handle,token) with full pricing: 1826 traders 126 tokens 560

## by entry FDV (first buy price x supply): n_pos, n_tok, win%, median ROI, pooled ROI (cons), pooled ROI (mtm), 95% CI pooled cons (token bootstrap)
<$100k                          11     7    64%   410.6%     26.6%    875.0%   [-52%, 181%]  invested $19,237
$100k–1M                       141    53    67%    85.9%      9.0%    276.7%   [-17%, 43%]  invested $1,623,925
$1M–10M                        326    73    64%    44.1%     28.8%   1146.9%   [-11%, 67%]  invested $10,353,842
$10M–100M                      197    31    70%    90.6%     -4.6%    630.4%   [-29%, 12%]  invested $19,847,955
>$100M                          78    10    72%    91.6%    -28.8%    270.4%   [-49%, -14%]  invested $17,026,046
unknown                       1073   455    26%   -34.2%    -26.4%    -26.4%   [-40%, -16%]  invested $8,855,199

## by token age at first buy: n_pos, n_tok, win%, median ROI, pooled ROI (cons), pooled ROI (mtm), 95% CI pooled cons (token bootstrap)
<1h                             46    21    59%    10.5%     83.5%    218.0%   [-3%, 148%]  invested $487,469
1h–24h                         111    34    56%     8.8%    -14.4%     22.3%   [-39%, -1%]  invested $3,515,060
1–7d                           153    47    57%    20.7%      6.8%   1079.5%   [-28%, 42%]  invested $3,774,179
>7d                            422    65    73%   167.2%     -7.4%    628.2%   [-22%, 16%]  invested $39,940,965
before pool (data err)          21     5    95%    50.7%     10.3%     95.5%   [-20%, 87%]  invested $1,153,331
unknown                       1073   455    26%   -34.2%    -26.4%    -26.4%   [-40%, -16%]  invested $8,855,199

## by launchpad: n_pos, n_tok, win%, median ROI, pooled ROI (cons), pooled ROI (mtm), 95% CI pooled cons (token bootstrap)
LONG (stock-paired)             69     8    86%  1955.2%     47.4%   2129.1%   [-97%, 53%]  invested $5,675,823
Pons (WETH pool)                17     4    41%     0.0%     -8.9%     -8.9%   [-85%, 75%]  invested $216,947
Pons V1 (v3 pool)              225    14    97%   433.4%    -12.3%    635.0%   [-22%, -1%]  invested $26,218,292
Pons V2 (v4 hook curve)         76    21    72%    78.5%    -23.3%    269.5%   [-64%, 27%]  invested $1,074,358
bags                            20    12    30%   -50.4%    -30.5%    -30.5%   [-74%, 17%]  invested $88,351
bonk (letsbonk)                 21     6    62%    10.7%    -43.3%     81.2%   [-97%, 318%]  invested $1,266,140
pump.fun                       841   320    30%   -24.7%    -10.2%     10.9%   [-21%, -3%]  invested $11,213,497
robinhood/other                 17     6    18%   -56.3%    -46.8%    -46.8%   [-63%, -13%]  invested $170,700
solana/other                   540   169    31%   -20.7%    -20.5%     -0.9%   [-37%, -7%]  invested $11,802,097

## by chain: n_pos, n_tok, win%, median ROI, pooled ROI (cons), pooled ROI (mtm), 95% CI pooled cons (token bootstrap)
robinhood                      404    53    85%   349.9%     -2.6%    869.8%   [-20%, 28%]  invested $33,356,120
solana                        1422   507    31%   -22.3%    -17.0%      8.7%   [-27%, -8%]  invested $24,370,084

## by current fomo holder count (boards; hindsight!): n_pos, n_tok, win%, median ROI, pooled ROI (cons), pooled ROI (mtm), 95% CI pooled cons (token bootstrap)
holders 1k–10k                  41     8    49%    -1.7%    -30.9%    172.6%   [-76%, 33%]  invested $662,949
holders≥10k                    252    10    87%   461.0%      0.7%    817.7%   [-12%, 38%]  invested $33,445,458
no board data                 1533   542    35%   -18.1%    -21.4%     74.6%   [-32%, -13%]  invested $23,617,797

## by chain x entry FDV: n_pos, n_tok, win%, median ROI, pooled ROI (cons), pooled ROI (mtm), 95% CI pooled cons (token bootstrap)
rob $100k–1M                    68    23    82%   393.3%     26.5%    620.1%   [-18%, 110%]  invested $683,572
rob $10M–100M                  104    13    98%   518.7%     -0.3%    810.0%   [-36%, 25%]  invested $15,306,939
rob $1M–10M                    181    40    76%   190.9%     47.7%   2125.5%   [-47%, 86%]  invested $5,446,123
rob >$100M                      45     3    96%   433.4%    -30.4%    386.6%   [-80%, 2%]  invested $11,907,834
sol $100k–1M                    73    30    53%     6.0%     -3.7%     27.1%   [-36%, 54%]  invested $940,353
sol $10M–100M                   93    18    38%    -9.4%    -19.2%     25.2%   [-41%, 3%]  invested $4,541,016
sol $1M–10M                    145    33    50%    -0.5%      8.0%     61.0%   [-4%, 26%]  invested $4,907,719
sol >$100M                      33     7    39%    -3.2%    -25.3%      0.1%   [-56%, -6%]  invested $5,118,212
sol unknown                   1073   455    26%   -34.2%    -26.4%    -26.4%   [-40%, -16%]  invested $8,855,199
```

What this says:

* **The leaders are not early snipers.** By dollars, three quarters of their priced meme entries are at FDV above $10M and two thirds are in tokens older than seven days. Sub-$1M entries are a rounding error of their capital (≈ $1.6M of $59M) even though they are a quarter of their positions by count.
* **No entry-FDV bucket has a significantly positive realized (bag-at-zero) return.** The only bucket with a clearly non-zero pooled result is > $100M entries at −29% [−49%, −14%]: buying the mega-caps late lost money. Everything green is in the `mtm` column, i.e. unsold bags marked at the last price.
* **Age**: the < 1h bucket is small (46 positions, 21 tokens) and its CI spans zero; 1h–24h entries are negative after the bag-at-zero rule. Older-than-7-days entries are where the capital is, and they are flat realized / huge mark-to-market: the leaderboard PnL is a bag-holding phenomenon, not an entry-timing one.
* **Launchpad**: pump.fun and Solana/other are the loss-making venues on a realized basis (−10% and −21% with CIs excluding zero). Robinhood Pons V1 tokens are −12% realized but +635% marked: the 14 tokens the whole leaderboard is sitting in. LONG stock-paired launches look spectacular marked (+2129%) and unproven realized (CI −97%…+53%, 8 tokens).
* **Holder count** (today's fomo board count, hindsight): the ≥ 10k-holder tokens are the same 10 crowd tokens; their realized ROI is +0.7%. Being in the crowd token did not pay in cash; it paid on paper.
* **Dev involvement**: fomoapi flags no dev among tracked holders and the Pons fee-redirect read is empty, so "is the trader the dev" is answered only by the mint-tx deployer; see the per-trader `dev tokens` column below (deployer wallet = leaderboard EVM wallet). Serial deployers do exist in the traded set (see the per-token `deployer` column, with the number of traded tokens from the same wallet).

## Per trader: where they enter

Median / interquartile entry FDV of priced meme entries (app positions + on-chain buys), share of entries below $1M and above $10M FDV, median token age at entry, share within 1h of creation and older than 7 days, main launchpads, tokens where the trader's EVM wallet deployed the token.

| handle | class | entries | tokens | entry FDV median (p25–p75) | <$1M | >$10M | age median | <1h | >7d | launchpads | dev tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gundam | concentrated_bag | 427 | 32 | $17.6M ($7.9M–$65.9M) | 0% | 70% | 31.1d | 0% | 85% | Pons V1 226, pump.fun 66, LONG 62, solana/other 45 |  |
| FartmanSacks | active_churner_negative | 384 | 35 | $10.2M ($8.3M–$14.7M) | 6% | 55% | 22.9d | 2% | 92% | Pons V1 163, LONG 103, pump.fun 87, Pons V2 21 |  |
| TheHappySwan | luck_one_bag | 350 | 29 | $28.2M ($17.8M–$64.5M) | 0% | 84% | 42.6d | 1% | 74% | LONG 132, Pons V1 85, pump.fun 75, Pons V2 35 |  |
| SolSwizzle | luck_one_bag | 314 | 37 | $10.0M ($4.7M–$21.3M) | 9% | 50% | 10.9d | 3% | 60% | pump.fun 133, LONG 63, Pons V1 58, solana/other 35 |  |
| seralberttrades | active_churner_negative | 306 | 39 | $11.2M ($5.3M–$30.4M) | 13% | 53% | 19.0d | 6% | 68% | Pons V1 128, pump.fun 67, solana/other 54, robinhood/other 28 |  |
| fr3ak | active_churner_negative | 295 | 33 | $27.5M ($24.1M–$57.0M) | 9% | 85% | 6.8d | 3% | 49% | pump.fun 199, LONG 45, Pons V1 30, robinhood/other 9 |  |
| loganlim_x | skill_candidate | 261 | 16 | $123.0M ($37.1M–$211.2M) | 2% | 81% | 52.6d | 1% | 84% | Pons V1 211, solana/other 22, LONG 11, pump.fun 7 |  |
| NachSOL | skill_candidate | 238 | 30 | $32.1M ($8.1M–$100.3M) | 3% | 70% | 25.6d | 2% | 81% | pump.fun 105, Pons V1 56, LONG 55, Pons V2 8 |  |
| 0xleo | active_churner_negative | 237 | 15 | $80.7M ($36.0M–$310.7M) | 3% | 96% | 19.1d | 0% | 81% | pump.fun 98, Pons V1 81, solana/other 50, base/other 3 |  |
| 0xnobi | luck_one_bag | 235 | 25 | $164.7M ($6.4M–$378.3M) | 13% | 72% | 36.7d | 1% | 85% | solana/other 145, Pons V1 67, pump.fun 6, Pons V2 5 |  |
| USronaldcarter | luck_one_bag | 232 | 17 | $12.2M ($8.4M–$24.1M) | 2% | 59% | 17.8h | 1% | 7% | pump.fun 111, solana/other 105, robinhood/other 6, Pons V2 3 |  |
| 0xdedrater | unknown | 223 | 107 | $2.4M ($149k–$8.9M) | 41% | 22% | 4.4d | 20% | 45% | Pons V1 63, Pons V2 40, Pons 37, robinhood/other 32 |  |
| Aurelius0121 | kol_flow_mover | 215 | 40 | $8.4M ($2.3M–$14.4M) | 14% | 41% | 12.7d | 1% | 70% | Pons V1 165, LONG 18, bsc/other 15, Pons 6 |  |
| cosby | luck_one_bag | 208 | 18 | $26.6M ($5.9M–$53.1M) | 1% | 64% | 23.2d | 0% | 90% | Pons V1 188, LONG 12, Pons V2 3, robinhood/other 2 |  |
| NotARandomUser | concentrated_bag | 201 | 41 | $3.0M ($1.4M–$9.2M) | 18% | 24% | 21.1d | 4% | 66% | LONG 70, Pons V1 44, Pons V2 41, Pons 29 |  |
| rasmr | unknown | 194 | 44 | $13.3M ($2.8M–$98.8M) | 10% | 56% | 9.2d | 7% | 61% | pump.fun 87, solana/other 41, Pons V1 30, Pons V2 20 |  |
| sadcrissy | unknown | 189 | 22 | $18.2M ($2.5M–$33.8M) | 11% | 61% | 8.9d | 2% | 68% | pump.fun 120, Pons V1 28, solana/other 25, bsc/other 4 |  |
| boosteryting | active_churner_negative | 185 | 9 | $12.2M ($4.0M–$15.9M) | 6% | 50% | 10.6d | 30% | 55% | pump.fun 175, Pons V2 7, bsc/other 2, robinhood/other 1 |  |
| insentos | luck_one_bag | 180 | 25 | $147.7M ($28.1M–$203.3M) | 9% | 76% | 10.4d | 10% | 80% | Pons V1 111, pump.fun 52, robinhood/other 13, LONG 2 |  |
| ericzhong | unknown | 166 | 60 | $2.3M ($495k–$4.4M) | 32% | 13% | 10.8d | 9% | 60% | Pons V1 83, Pons V2 27, LONG 22, robinhood/other 20 |  |
| change | kol_flow_mover | 163 | 15 | $76.5M ($12.1M–$223.1M) | 1% | 90% | 48.1d | 1% | 98% | Pons V1 89, LONG 43, Pons V2 26, Pons 2 |  |
| Alexandar | concentrated_bag | 159 | 34 | $2.2M ($686k–$9.8M) | 27% | 22% | 4.0d | 12% | 39% | pump.fun 59, solana/other 42, Pons V1 22, Pons V2 16 |  |
| The__Solstice | insider_or_allocation | 158 | 12 | $6.1M ($4.2M–$15.0M) | 4% | 33% | 1.5d | 22% | 27% | solana/other 106, Pons V1 24, pump.fun 23, base/other 3 |  |
| facap | unknown | 158 | 39 | $3.8M ($944k–$12.0M) | 27% | 30% | 14.3d | 1% | 65% | pump.fun 40, Pons V2 33, Pons V1 26, solana/other 24 |  |
| m0f0 | luck_one_bag | 149 | 33 | $6.4M ($4.1M–$19.3M) | 9% | 37% | 26.3d | 5% | 71% | LONG 46, solana/other 30, Pons 25, Pons V2 23 |  |
| SpicyPeruvian_ | luck_one_bag | 142 | 43 | $18.0M ($3.0M–$103.2M) | 14% | 64% | 20.5d | 4% | 64% | LONG 41, solana/other 32, pump.fun 20, Pons V2 19 |  |
| ether_monk | kol_flow_mover | 141 | 29 | $30.4M ($9.0M–$140.8M) | 6% | 67% | 36.2d | 3% | 78% | Pons V1 59, solana/other 28, pump.fun 25, LONG 11 |  |
| paidinfullintel | concentrated_bag | 127 | 60 | $4.4M ($600k–$28.6M) | 32% | 37% | 4.1d | 13% | 45% | pump.fun 24, robinhood/other 22, LONG 20, Pons V2 18 |  |
| FullPinkYak | concentrated_bag | 124 | 33 | $7.9M ($1.8M–$13.2M) | 10% | 42% | 11.5d | 7% | 61% | Pons V2 37, Pons V1 35, pump.fun 23, solana/other 19 |  |
| notanicecat69 | luck_one_bag | 123 | 23 | $10.6M ($3.2M–$98.0M) | 15% | 52% | 24.4d | 5% | 69% | LONG 44, solana/other 26, bonk 24, pump.fun 11 |  |
| bluntz_capital | skill_candidate | 122 | 31 | $18.7M ($4.0M–$131.8M) | 7% | 59% | 46.2d | 1% | 89% | Pons V1 65, LONG 15, solana/other 15, Pons V2 8 |  |
| pointfarmcap | luck_one_bag | 117 | 6 | $7.3M ($6.6M–$16.2M) | 1% | 32% | 50.5d | 0% | 97% | Pons V1 112, solana/other 2, Pons 2, base/other 1 |  |
| Tsukikage | active_churner_negative | 115 | 24 | $2.7M ($953k–$4.4M) | 26% | 17% | 8.1d | 4% | 64% | Pons V1 83, robinhood/other 15, Pons V2 9, Pons 2 |  |
| brrrgrrrz | luck_one_bag | 114 | 13 | $7.7M ($3.6M–$12.5M) | 6% | 34% | 19.7d | 1% | 96% | Pons V1 76, LONG 30, robinhood/other 4, Pons V2 3 |  |
| LowRivalRat | luck_one_bag | 110 | 14 | $19.6M ($6.2M–$33.5M) | 15% | 65% | 24.5d | 1% | 79% | Pons V1 98, robinhood/other 4, Pons 4, Pons V2 2 |  |
| Salem1299534 | kol_flow_mover | 109 | 16 | $7.3M ($3.5M–$12.2M) | 12% | 33% | 13.3d | 0% | 86% | LONG 86, Pons V1 12, robinhood/other 4, base/other 2 |  |
| 0xdetweiler | skill_candidate | 107 | 39 | $863k ($374k–$2.2M) | 56% | 3% | 5.5d | 5% | 46% | Pons V1 51, robinhood/other 17, Pons V2 15, LONG 10 |  |
| picadura | luck_one_bag | 106 | 41 | $2.8M ($348k–$15.1M) | 33% | 27% | 8.8d | 20% | 60% | solana/other 31, LONG 29, robinhood/other 19, pump.fun 10 |  |
| wileEcoyote | luck_one_bag | 104 | 34 | $8.5M ($2.2M–$23.8M) | 9% | 41% | 11.3d | 6% | 56% | LONG 35, pump.fun 19, solana/other 13, Pons V2 11 |  |
| montyMole44 | concentrated_bag | 103 | 20 | $6.7M ($4.5M–$9.4M) | 15% | 20% | 15.6d | 11% | 74% | pump.fun 69, LONG 11, robinhood/other 10, solana/other 6 |  |
| midcurver | active_churner_negative | 102 | 60 | $4.3M ($1.7M–$13.1M) | 15% | 28% | 1.9d | 19% | 36% | Pons V2 25, solana/other 24, robinhood/other 13, pump.fun 12 |  |
| Jols | luck_one_bag | 100 | 18 | $59.7M ($37.8M–$69.3M) | 2% | 87% | 39.3d | 0% | 92% | Pons V1 44, pump.fun 38, Pons V2 9, Pons 4 |  |
| LP1111 | luck_one_bag | 100 | 16 | $1.9M ($601k–$3.7M) | 35% | 4% | 41.2d | 2% | 93% | LONG 36, Pons V1 26, robinhood/other 19, Pons V2 13 |  |
| 81_tom | active_churner_negative | 99 | 13 | $56.9M ($21.4M–$84.7M) | 0% | 82% | 43.5d | 0% | 84% | LONG 66, pump.fun 21, solana/other 8, Pons V1 3 |  |
| Binkieee | luck_one_bag | 98 | 65 | $444k ($106k–$3.0M) | 59% | 14% | 3.2d | 21% | 34% | Pons V1 36, bsc/other 18, robinhood/other 15, Pons V2 14 |  |
| Rowdy | kol_flow_mover | 96 | 54 | $1.4M ($383k–$2.3M) | 36% | 11% | 1.1d | 28% | 20% | Pons V2 22, pump.fun 20, robinhood/other 18, solana/other 15 |  |
| B3NSS | luck_one_bag | 95 | 29 | $2.0M ($581k–$5.6M) | 38% | 2% | 4.4h | 12% | 3% | pump.fun 61, robinhood/other 12, solana/other 8, LONG 5 |  |
| CardinalSaint2 | concentrated_bag | 95 | 32 | $2.9M ($484k–$10.5M) | 37% | 26% | 14.6d | 8% | 67% | Pons V1 37, LONG 26, robinhood/other 12, solana/other 9 |  |
| vancute1112 | active_churner_negative | 95 | 31 | $68.5M ($9.3M–$179.2M) | 4% | 74% | 45.2d | 2% | 76% | Pons V2 19, Pons V1 19, LONG 17, pump.fun 15 |  |
| kyle | unknown | 93 | 30 | $2.7M ($998k–$3.5M) | 26% | 10% | 167.8d | 12% | 74% | pump.fun 53, Pons V2 11, LONG 9, base/other 5 |  |
| AnselFang | active_churner_negative | 90 | 19 | $268.1M ($88.1M–$360.9M) | 2% | 78% | 49.2d | 0% | 84% | LONG 54, Pons V1 26, Pons V2 5, robinhood/other 3 |  |
| NoGiOlMoKiNi | luck_one_bag | 84 | 13 | $10.4M ($4.5M–$13.9M) | 4% | 54% | 10.8d | 4% | 83% | Pons V1 68, robinhood/other 5, bonk 4, bsc/other 3 |  |
| econoar | active_churner_negative | 84 | 52 | $706k ($284k–$1.7M) | 61% | 8% | 2.7d | 16% | 34% | Pons V2 28, pump.fun 25, LONG 14, robinhood/other 11 |  |
| Onchainmetrics | concentrated_bag | 82 | 73 | $120k ($67k–$433k) | 83% | 1% | 2.0h | 44% | 14% | robinhood/other 39, LONG 17, Pons V2 16, base/other 4 |  |
| 397397 | luck_one_bag | 81 | 71 | $310k ($130k–$1.4M) | 68% | 4% | 7.8h | 42% | 21% | bsc/other 36, Pons V2 16, robinhood/other 11, pump.fun 8 |  |
| DumbCrayonEater | luck_one_bag | 77 | 30 | $3.2M ($1.3M–$6.0M) | 21% | 16% | 12.4d | 4% | 70% | LONG 29, Pons V1 14, pump.fun 13, Pons 8 |  |
| NorthPraetor | luck_one_bag | 74 | 29 | $9.6M ($566k–$14.7M) | 30% | 46% | 39.2d | 25% | 60% | pump.fun 33, Pons V2 14, LONG 7, Pons V1 7 |  |
| frankdegods | kol_flow_mover | 74 | 55 | $1.3M ($230k–$5.4M) | 45% | 18% | 1.9d | 31% | 37% | Pons V2 23, Pons V1 15, Pons 9, bsc/other 7 |  |
| figaro | unknown | 71 | 50 | $1.2M ($262k–$3.7M) | 45% | 10% | 5.5h | 29% | 15% | robinhood/other 15, pump.fun 15, Pons V2 13, solana/other 11 |  |
| panceramic | active_churner_negative | 71 | 53 | $1.1M ($351k–$2.1M) | 49% | 7% | 21.6h | 20% | 22% | Pons V2 32, robinhood/other 25, bsc/other 5, LONG 4 |  |
| CryptoTalkMan | active_churner_negative | 68 | 43 | $547k ($292k–$2.2M) | 56% | 12% | 2.6h | 36% | 12% | solana/other 21, robinhood/other 15, Pons V2 8, pump.fun 7 |  |
| derek518 | active_churner_negative | 64 | 23 | $88.5M ($3.4M–$168.0M) | 5% | 73% | 48.3d | 3% | 81% | Pons V1 17, LONG 15, bonk 14, Pons V2 10 |  |
| theveeman | insider_or_allocation | 63 | 27 | $6.0M ($2.5M–$92.0M) | 14% | 43% | 11.6d | 3% | 68% | pump.fun 25, Pons V1 13, solana/other 8, Pons V2 6 |  |
| RunningClam | unknown | 62 | 11 | $6.1M ($3.9M–$29.8M) | 16% | 47% | 12.4d | 0% | 71% | Pons V1 41, LONG 17, Pons V2 3, Pons 1 |  |
| ventikohi | luck_one_bag | 59 | 44 | $1.4M ($542k–$8.7M) | 44% | 22% | 4.1d | 21% | 42% | Pons V2 19, Pons V1 11, robinhood/other 7, solana/other 6 |  |
| elliotrades | active_churner_negative | 56 | 25 | $19.6M ($3.8M–$65.5M) | 2% | 55% | 41.0d | 4% | 65% | Pons V1 29, Pons V2 14, robinhood/other 3, base/other 3 |  |
| poker_kb_ | concentrated_bag | 56 | 16 | $8.7M ($6.5M–$15.9M) | 18% | 43% | 11.4d | 7% | 68% | pump.fun 33, LONG 7, robinhood/other 6, Pons V1 4 |  |
| soby0x | luck_one_bag | 52 | 25 | $5.3M ($1.2M–$9.4M) | 25% | 17% | 19.8d | 0% | 69% | LONG 21, Pons V2 10, Pons V1 10, robinhood/other 5 |  |
| workethic | luck_one_bag | 52 | 23 | $9.4M ($2.1M–$26.3M) | 15% | 46% | 17.0d | 2% | 77% | Pons V1 28, Pons V2 12, pump.fun 6, bsc/other 3 |  |
| cryptochi3f_ | luck_one_bag | 51 | 23 | $2.9M ($543k–$5.3M) | 35% | 20% | 1.4d | 18% | 40% | Pons V2 18, LONG 13, pump.fun 8, robinhood/other 3 |  |
| aki11a | luck_one_bag | 50 | 32 | $5.8M ($1.5M–$15.4M) | 22% | 34% | 7.9d | 12% | 56% | LONG 13, pump.fun 9, Pons V2 8, robinhood/other 8 |  |
| kv4rl | concentrated_bag | 49 | 18 | $32.6M ($3.9M–$236.1M) | 8% | 59% | 40.3d | 4% | 78% | pump.fun 25, base/other 10, Pons V1 7, eth/other 3 |  |
| goosemanjones1 | luck_one_bag | 47 | 21 | $10.8M ($2.0M–$17.0M) | 15% | 60% | 28.0d | 2% | 68% | Pons V2 21, LONG 10, robinhood/other 8, Pons V1 6 |  |
| inyourwalls | luck_one_bag | 45 | 20 | $1.7M ($379k–$2.8M) | 38% | 9% | 4.4d | 2% | 30% | pump.fun 15, LONG 12, Pons V2 7, robinhood/other 4 |  |
| AvgJoesCrypto | concentrated_bag | 44 | 29 | $1.3M ($202k–$3.6M) | 48% | 11% | 5.3d | 9% | 49% | Pons V2 17, solana/other 9, Pons V1 7, LONG 4 |  |
| gkisokay | unknown | 43 | 23 | $1.4M ($339k–$3.5M) | 44% | 5% | 13.9d | 7% | 65% | LONG 22, Pons V2 11, robinhood/other 4, Pons V1 4 |  |
| pianches | active_churner_negative | 43 | 21 | $13.1M ($2.4M–$75.4M) | 7% | 58% | 44.5d | 0% | 83% | Pons V1 18, bonk 7, pump.fun 6, bsc/other 5 |  |
| DipWheeler | unknown | 41 | 34 | $191k ($55k–$662k) | 76% | 2% | 9.6h | 30% | 12% | robinhood/other 21, Pons V2 7, bsc/other 5, LONG 4 |  |
| unipcs | kol_flow_mover | 41 | 19 | $6.3M ($3.4M–$52.5M) | 5% | 39% | 11.0d | 2% | 56% | bonk 14, Pons V2 11, Pons V1 11, Pons 3 |  |
| CoinGurruu | luck_one_bag | 40 | 16 | $3.0M ($964k–$7.8M) | 28% | 18% | 21.9d | 15% | 69% | LONG 23, robinhood/other 4, solana/other 3, Pons 3 |  |
| carlwheezor | luck_one_bag | 40 | 27 | $1.8M ($173k–$31.8M) | 40% | 32% | 8.7d | 14% | 58% | Pons V1 20, Pons V2 8, base/other 6, robinhood/other 3 |  |
| lordarbiter | luck_one_bag | 40 | 18 | $17.2M ($2.6M–$20.4M) | 15% | 60% | 23.2d | 5% | 70% | Pons V1 23, Pons V2 11, robinhood/other 3, bsc/other 1 |  |
| Quanterty | insider_or_allocation | 39 | 25 | $4.6M ($288k–$333.1M) | 44% | 38% | 1.8d | 17% | 39% | solana/other 9, bsc/other 8, robinhood/other 8, pump.fun 4 |  |
| RugDalio | luck_one_bag | 39 | 25 | $865k ($128k–$6.7M) | 51% | 18% | 10.0h | 24% | 26% | Pons V2 16, Pons V1 10, robinhood/other 6, LONG 2 |  |
| alpinestar17 | active_churner_negative | 39 | 24 | $4.6M ($981k–$41.0M) | 26% | 49% | 20.5d | 5% | 68% | pump.fun 12, Pons V2 9, Pons V1 7, robinhood/other 5 |  |
| Mirro7777 | concentrated_bag | 38 | 35 | $673k ($193k–$6.0M) | 63% | 24% | 1.5d | 11% | 34% | bsc/other 19, LONG 5, Pons V2 4, solana/other 4 |  |
| ogle | luck_one_bag | 38 | 32 | $1.1M ($189k–$3.0M) | 47% | 21% | 3.9d | 16% | 45% | Pons V1 16, Pons V2 9, robinhood/other 4, LONG 3 |  |
| error | luck_one_bag | 37 | 23 | $172k ($65k–$5.7M) | 62% | 19% | 1.5d | 24% | 41% | robinhood/other 14, LONG 9, Pons V1 8, solana/other 4 |  |
| 0xAvast | kol_flow_mover | 36 | 18 | $982k ($412k–$33.7M) | 50% | 36% | 7.3d | 15% | 55% | solana/other 9, Pons V1 8, Pons V2 7, pump.fun 5 |  |
| SerAvocado | kol_flow_mover | 36 | 14 | $3.7M ($2.7M–$7.7M) | 0% | 3% | 22.5h | 3% | 31% | solana/other 16, robinhood/other 9, Pons V2 5, bsc/other 3 |  |
| Milliardi | luck_one_bag | 35 | 18 | $15.0M ($4.7M–$149.7M) | 11% | 60% | 38.1d | 9% | 62% | Pons V1 13, LONG 7, robinhood/other 6, Pons V2 5 |  |
| justtesting | concentrated_bag | 35 | 17 | $5.6M ($644k–$21.3M) | 31% | 49% | 38.5d | 13% | 55% | LONG 14, robinhood/other 9, Pons V2 3, bsc/other 3 |  |
| jotagezin | luck_one_bag | 34 | 13 | $7.9M ($1.8M–$8.5M) | 21% | 12% | 28.2d | 3% | 84% | LONG 22, Pons V1 4, bsc/other 3, base/other 2 |  |
| Iknowwhyy | luck_one_bag | 32 | 15 | $3.3M ($1.3M–$7.0M) | 22% | 19% | 3.3d | 6% | 44% | bsc/other 12, Pons V2 10, Pons V1 7, pump.fun 2 |  |
| Samisa_btc | concentrated_bag | 32 | 19 | $3.3M ($744k–$15.5M) | 34% | 28% | 5.6d | 3% | 40% | Pons V1 15, pump.fun 5, bsc/other 4, robinhood/other 3 |  |
| corleonefnf | luck_one_bag | 31 | 22 | $722k ($252k–$1.6M) | 55% | 6% | 1.7d | 32% | 21% | LONG 9, pump.fun 8, robinhood/other 7, bsc/other 3 |  |
| kingofgotham | luck_one_bag | 31 | 16 | $3.9M ($871k–$11.9M) | 26% | 35% | 7.9d | 6% | 52% | Pons V2 8, Pons V1 7, LONG 7, Pons 6 |  |
| tikopumps | luck_one_bag | 31 | 7 | $7.7M ($5.1M–$13.8M) | 10% | 45% | 18.8h | 0% | 33% | pump.fun 21, solana/other 6, base/other 2, bsc/other 1 |  |
| sockzt | luck_one_bag | 30 | 17 | $2.3M ($792k–$4.2M) | 30% | 0% | 10.0d | 7% | 54% | Pons 11, LONG 9, Pons V2 5, robinhood/other 3 |  |
| Natan_benish | luck_one_bag | 29 | 21 | $2.1M ($170k–$6.5M) | 45% | 24% | 10.2d | 17% | 57% | base/other 15, LONG 5, Pons 3, solana/other 3 |  |
| XbtPika | active_churner_negative | 28 | 16 | $3.0M ($472k–$8.1M) | 39% | 7% | 1.2d | 23% | 4% | Pons V2 18, robinhood/other 6, bsc/other 3, Pons V1 1 |  |
| Dxranteth | active_churner_negative | 26 | 18 | $2.4M ($656k–$32.6M) | 27% | 31% | 9.6d | 17% | 54% | Pons V2 6, bsc/other 5, robinhood/other 4, pump.fun 4 |  |
| 0xExas | unknown | 25 | 23 | $1.0M ($397k–$5.1M) | 48% | 16% | 4.8d | 14% | 45% | base/other 12, robinhood/other 6, Pons V2 4, bsc/other 2 |  |
| Eagle_0X | luck_one_bag | 24 | 10 | $3.1M ($3.0M–$3.3M) | 12% | 4% | 9.0d | 5% | 82% | Pons 15, bsc/other 3, Pons V2 2, LONG 2 |  |
| cryptolyxe | active_churner_negative | 24 | 16 | $10.8M ($1.1M–$31.1M) | 25% | 50% | 48.1d | 4% | 61% | pump.fun 6, base/other 5, bonk 3, Pons V2 2 |  |
| Y0u_andme | unknown | 23 | 18 | $2.4M ($1.2M–$5.5M) | 13% | 17% | 2.6h | 38% | 29% | Pons V2 7, Pons V1 4, robinhood/other 4, bsc/other 3 |  |
| yeon__ | luck_one_bag | 23 | 23 | $316k ($104k–$1.0M) | 74% | 9% | 26.9d | 6% | 72% | robinhood/other 8, bsc/other 6, Pons V2 3, Pons V1 2 |  |
| Chubbi230 | luck_one_bag | 22 | 12 | $88.9M ($1.5M–$286.6M) | 18% | 73% | 44.1d | 5% | 86% | Pons V1 12, Pons V2 5, solana/other 2, base/other 1 |  |
| TheGasChad | active_churner_negative | 22 | 13 | $1.3M ($702k–$24.5M) | 50% | 36% | 42.5d | 11% | 79% | Pons V1 9, Pons V2 3, LONG 3, robinhood/other 2 |  |
| gweil0rd | luck_one_bag | 22 | 18 | $815k ($497k–$5.2M) | 55% | 14% | 11.0h | 19% | 19% | Pons V2 11, pump.fun 4, robinhood/other 4, LONG 3 |  |
| naP0Liano | concentrated_bag | 22 | 20 | $456k ($293k–$771k) | 77% | 0% | 1.6d | 24% | 29% | robinhood/other 7, LONG 6, Pons V2 5, bsc/other 2 |  |
| iruletrenches | luck_one_bag | 21 | 19 | $436k ($148k–$1.6M) | 71% | 14% | 5.1h | 30% | 25% | robinhood/other 9, Pons V2 4, pump.fun 2, bsc/other 2 |  |
| 0xSisyphus | luck_one_bag | 20 | 16 | $1.0M ($282k–$1.9M) | 50% | 10% | 8.3d | 0% | 50% | Pons V2 6, robinhood/other 4, LONG 4, solana/other 2 |  |
| IssaTheCooker | luck_one_bag | 20 | 18 | $7.6M ($2.5M–$47.4M) | 15% | 50% | 5.2d | 22% | 50% | base/other 12, bsc/other 3, Pons V1 2, solana/other 2 |  |
| fmpumpguy | luck_one_bag | 20 | 20 | $219k ($143k–$454k) | 95% | 0% | 21m | 68% | 0% | robinhood/other 11, bsc/other 4, LONG 4, solana/other 1 |  |
| LehmanFarters | luck_one_bag | 19 | 13 | $8.9M ($1.2M–$14.6M) | 21% | 47% | 1.4d | 21% | 47% | LONG 7, Pons V2 6, Pons V1 3, robinhood/other 1 |  |
| Pote_korea | luck_one_bag | 19 | 18 | $192k ($80k–$459k) | 84% | 0% | 3.7d | 31% | 31% | Pons V2 10, bsc/other 3, robinhood/other 3, LONG 2 |  |
| SweetPriorCod | luck_one_bag | 18 | 13 | $4.2M ($981k–$27.3M) | 28% | 28% | 8.3d | 17% | 50% | LONG 6, Pons V2 5, base/other 4, robinhood/other 1 |  |
| BigGoldPony | luck_one_bag | 17 | 17 | $84k ($43k–$517k) | 82% | 6% | 1.9d | 6% | 35% | robinhood/other 8, LONG 5, Pons V2 3, Pons 1 |  |
| MemeKingdom | unknown | 17 | 5 | $256k ($103k–$494k) | 76% | 0% | 214.9d | 6% | 88% | pump.fun 9, bonk 6, bsc/other 1, Pons 1 |  |
| 0xSporadic | active_churner_negative | 16 | 15 | $4.1M ($1.5M–$22.4M) | 25% | 31% | 3.2d | 7% | 40% | Pons V2 6, robinhood/other 5, eth/other 1, pump.fun 1 |  |
| BonerSqueeze | luck_one_bag | 16 | 14 | $2.1M ($476k–$8.6M) | 31% | 19% | 22.2h | 14% | 29% | LONG 5, bsc/other 3, Pons V2 2, robinhood/other 2 |  |
| MoneyLord | luck_one_bag | 16 | 9 | $4.6M ($951k–$12.3M) | 31% | 31% | 4.7d | 25% | 50% | bsc/other 5, Pons V1 4, Pons V2 3, base/other 2 |  |
| twaptops | luck_one_bag | 15 | 10 | $3.4M ($580k–$5.2M) | 33% | 20% | 31.7d | 0% | 93% | LONG 5, pump.fun 3, base/other 2, solana/other 2 |  |
| proxy_ | active_churner_negative | 14 | 14 | $1.4M ($430k–$12.5M) | 50% | 29% | 3.7d | 15% | 23% | robinhood/other 6, Pons V2 4, LONG 2, base/other 1 |  |
| smol_intern | concentrated_bag | 13 | 4 | $3.9M ($451k–$7.2M) | 38% | 0% | 43.1d | 23% | 77% | LONG 8, robinhood/other 4, Pons V2 1 |  |
| WuKong365 | concentrated_bag | 12 | 7 | $24.7M ($15.0M–$39.8M) | 8% | 75% | 10.6d | 0% | 50% | Pons V1 4, Pons V2 3, bsc/other 3, pump.fun 1 |  |
| frogmanhaha | concentrated_bag | 12 | 3 | $25.1M ($18.5M–$174.7M) | 8% | 92% | 40.5d | 0% | 92% | LONG 6, Pons V1 5, base/other 1 |  |
| GeorgeDroid | luck_one_bag | 11 | 8 | $25.5M ($4.2M–$47.6M) | 0% | 64% | 4.7d | 9% | 36% | pump.fun 3, Pons V2 2, solana/other 2, base/other 1 |  |
| ImChizx | unknown | 11 | 11 | $418k ($257k–$804k) | 82% | 9% | 1.2d | 9% | 27% | Pons V2 4, robinhood/other 2, bsc/other 2, Pons V1 2 |  |
| colintrades1 | unknown | 11 | 5 | $212.2M ($43.0M–$232.7M) | 0% | 82% | 59.6d | 0% | 82% | Pons V1 6, Pons V2 2, solana/other 2, pump.fun 1 |  |
| ethersole | concentrated_bag | 11 | 7 | $38.3M ($10.2M–$61.6M) | 0% | 82% | 9.7d | 0% | 55% | Pons V1 6, Pons V2 4, LONG 1 |  |
| himgajria | active_churner_negative | 11 | 6 | $76.0M ($2.5M–$79.2M) | 9% | 64% | 44.3d | 9% | 64% | LONG 6, Pons V2 5 |  |
| tummster | unknown | 11 | 7 | $35.9M ($26.1M–$78.8M) | 0% | 100% | 11.3d | 0% | 64% | base/other 6, LONG 1, Pons V2 1, pump.fun 1 |  |
| BumpyFancyCoral | luck_one_bag | 10 | 10 | $1.6M ($620k–$2.6M) | 40% | 0% | 1.8d | 50% | 40% | Pons V2 3, robinhood/other 2, bsc/other 2, Pons 1 |  |
| byszzz | luck_one_bag | 10 | 8 | $855k ($203k–$11.6M) | 50% | 30% | 11.0h | 38% | 38% | robinhood/other 4, pump.fun 3, Pons V2 2, bsc/other 1 |  |
| GuavaGuy2001 | luck_one_bag | 9 | 6 | $4.3M ($470k–$6.9M) | 33% | 11% | 6.4d | 0% | 44% | pump.fun 4, bsc/other 2, bonk 2, base/other 1 |  |
| ThePumponomics | luck_one_bag | 9 | 9 | $43.0M ($9.3M–$106.0M) | 11% | 56% | 35.9d | 0% | 78% | Pons V1 4, Pons V2 2, bsc/other 1, base/other 1 |  |
| PoorGoat_ | kol_flow_mover | 8 | 5 | $617k ($472k–$8.3M) | 62% | 12% | 26.1d | 12% | 75% | Pons V1 4, pump.fun 2, base/other 1, bsc/other 1 |  |
| memeking888 | luck_one_bag | 8 | 6 | $125.7M ($68.5M–$424.9M) | 0% | 88% | 48.2d | 0% | 88% | Pons V1 2, LONG 2, Pons V2 2, bsc/other 2 |  |
| smokey0x | luck_one_bag | 5 | 5 | $389k ($375k–$451k) | 80% | 0% | 4.9h | 0% | 0% | bsc/other 2, Pons 2, LONG 1 |  |
| vladsbutler | luck_one_bag | 5 | 5 | $43.1M ($2.9M–$46.0M) | 20% | 60% | 23.0d | 0% | 75% | Pons V2 2, Pons V1 1, robinhood/other 1, bsc/other 1 |  |
| hungryghost | unknown | 4 | 4 | $5.6M ($2.1M–$36.3M) | 0% | 25% | 20.7d | 0% | 50% | LONG 2, Pons V1 1, pump.fun 1 |  |
| The_Bogfather | concentrated_bag | 3 | 3 | $323.3M ($205.0M–$486.0M) | 0% | 100% | 53.4d | 0% | 100% | Pons V1 2, solana/other 1 |  |
| LuckyManRRR | luck_one_bag | 2 | 2 | $458k ($237k–$678k) | 100% | 0% | 5.5h | 50% | 0% | robinhood/other 2 |  |

## Per meme: fundamentals

Memes with ≥ 2 leaderboard traders, ordered by number of leaderboard traders. `holders` = fomo board total holder count (blank = token never made a board); `tracked/lb` = fomo-tracked top holders / leaderboard handles among them; `top10%` = share of supply held by the 10 largest tracked holders; `deployer (n)` = mint-tx sender and how many traded tokens it deployed; `lb entry FDV` = median entry FDV of leaderboard entries; `first lb entry` = age of the token at the first leaderboard entry.

| symbol | chain | launchpad | created | FDV now | liq | holders | tracked/lb | top10% | deployer (n) | lb traders | entries | lb entry FDV (min) | first lb entry | <$1M |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PONS | robinhood | Pons V1 (v3 pool) | 2026-07-13 20:42 | $423.8M | $6.3M | 61037 | 0/0 | 0% |  | 81 | 838 | $39.1M ($115k) | 1m | 0% |
| AI | robinhood | LONG (stock-paired) | 2026-07-14 17:48 | $253.7M | $5.9M | 29005 | 50/43 | 14% |  | 80 | 1321 | $11.1M ($449k) | 1.1h | 0% |
| CASHCAT | robinhood | Pons V1 (v3 pool) | 2026-07-01 12:56 | $302.1M | $6.0M | 102178 | 50/14 | 5% | 0xcdfc…ca90 (1) | 77 | 835 | $160.6M ($35.8M) | 7.1d | 0% |
| CATE | solana | pump.fun | 2026-08-02 01:55 | $37.1M | $18k | 118422 | 49/6 | 10% |  | 54 | 579 | $34.9M ($190k) | -9183m | 0% |
| BONER | robinhood | Pons V2 (v4 hook curve) | 2026-08-20 20:59 | $70.2M | $2.9M | 12498 | 50/21 | 14% |  | 52 | 53 | $32.6M ($73k) | 19m | 17% |
| ANSEM | solana | pump.fun | 2026-06-16 21:05 | $269.9M | $3.0M | 136495 | 49/4 | 2% |  | 51 | 177 | $184.9M ($4.3M) | 10.8d | 0% |
| Index | robinhood | Pons V1 (v3 pool) | 2026-07-03 09:19 | $65.4M | $1.3M |  | 49/5 | 4% |  | 47 | 318 | $15.4M ($2.6M) | 7.7d | 0% |
| DELTA | robinhood | Pons V1 (v3 pool) | 2026-07-31 22:59 | $17.0M | $1.2M |  | 49/8 | 12% |  | 45 | 33 | $18.5M ($718k) | 10.7d | 6% |
| TENDIES | robinhood | Pons V1 (v3 pool) | 2026-07-01 13:08 | $28.6M | $1.2M | 17053 | 0/0 | 0% |  | 43 | 374 | $13.6M ($2.7M) | 8.3d | 0% |
| iPHONE18 | solana | pump.fun |  |  |  |  | 49/2 |  |  | 43 | 0 |  () |  |  |
| YOLO | robinhood | Pons V1 (v3 pool) | 2026-07-15 07:15 | $11.3M | $468k | 11114 | 50/6 | 9% |  | 41 | 266 | $4.1M ($408k) | 2.6d | 9% |
| ETHMAXI | robinhood | Pons V2 (v4 hook curve) | 2026-08-29 21:12 | $24k | $14k |  | 0/0 | 0% |  | 39 | 0 |  () |  |  |
| fone | solana | pump.fun | 2026-08-27 00:03 | $16.8M | $764k | 26660 | 0/0 | 0% |  | 39 | 503 | $23.1M ($442k) | 6m | 1% |
| UPTOBER | robinhood | Pons V1 (v3 pool) | 2026-08-04 19:10 | $159k | $43k |  | 0/0 | 0% |  | 38 | 0 |  () |  |  |
| MarsCoin | bsc | bsc/other | 2026-07-27 13:23 | $107.6M | $1.7M | 36658 | 0/0 | 0% |  | 37 | 35 | $46.0M ($389k) | 3.0h | 6% |
| STONK | solana | solana/other | 2026-08-05 22:03 | $24.9M | $826k |  | 0/0 | 0% |  | 37 | 361 | $7.3M ($968k) | -2768m | 0% |
| microduck | robinhood | Pons V2 (v4 hook curve) | 2026-08-27 11:24 | $34.4M | $640k | 15564 | 49/12 | 16% |  | 37 | 36 | $17.5M ($233k) | 31m | 8% |
| JUGGERNAUT | robinhood | Pons V1 (v3 pool) | 2026-07-01 13:59 | $6.5M | $549k |  | 0/0 | 0% |  | 36 | 309 | $8.4M ($848k) | 6.5d | 0% |
| RAM | robinhood | robinhood/other | 2026-08-31 16:40 | $7.0M | $409k | 9418 | 0/0 | 0% |  | 36 | 28 | $11.3M ($3.9M) | -283m | 0% |
| 肥嘟嘟 | bsc | bsc/other | 2026-08-23 04:55 | $907k | $110k |  | 0/0 | 0% |  | 36 | 0 |  () |  |  |
| BTCB | bsc | bsc/other | 2025-11-14 03:56 | $5.3B | $26.0M |  | 0/0 | 0% |  | 35 | 0 |  () |  |  |
| HOOK | robinhood | Pons V2 (v4 hook curve) | 2026-08-18 21:00 | $46k | $28k |  | 0/0 | 0% |  | 35 | 0 |  () |  |  |
| MOO | robinhood | Pons V2 (v4 hook curve) | 2026-07-20 18:35 | $19.5M | $1.4M | 3341 | 0/0 | 0% |  | 35 | 66 | $24.4M ($137k) | 24.4d | 6% |
| MU | robinhood | robinhood/other | 2026-07-01 14:45 | $4.1M | $3.2M |  | 0/0 | 0% |  | 35 | 0 |  () |  |  |
| Rabbit | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 19:32 | $625k | $22k | 7778 | 0/0 | 0% |  | 34 | 23 | $6.8M ($2.2M) | 19m | 0% |
| ANTHRP | solana | solana/other |  |  |  |  | 48/8 |  |  | 31 | 0 |  () |  |  |
| CINEMA | robinhood | robinhood/other |  | $403k | $122k |  | 0/0 | 0% |  | 31 | 19 | $3.7M ($483k) |  | 21% |
| PENGU | solana | solana/other | 2025-11-26 18:12 | $791.2M | $4.2M |  | 0/0 | 0% |  | 31 | 22 | $843.8M ($760.8M) | -46605m | 0% |
| ZEC | solana | solana/other |  |  |  |  | 50/2 |  |  | 31 | 0 |  () |  |  |
| STONKBROKER | robinhood | Pons V2 (v4 hook curve) | 2026-07-17 23:29 | $52.5M | $4.0M | 32632 | 0/0 | 0% |  | 30 | 25 | $50.0M ($26.3M) | 4.1d | 0% |
| FXIon | bsc | bsc/other | 2026-08-19 09:08 | $390k | $12k |  | 0/0 | 0% |  | 29 | 0 |  () |  |  |
| XAUt | bsc | bsc/other | 2026-04-01 05:01 | $59.3M | $1.6M |  | 49/6 | 0% |  | 29 | 0 |  () |  |  |
| PIPEDOG | robinhood | Pons V1 (v3 pool) | 2026-07-28 20:31 | $29.8M | $9.1M |  |  |  |  | 28 | 10 | $41.2M ($14.7M) | 35m | 0% |
| SPYB | bsc | bsc/other | 2026-07-08 01:47 | $19.6M | $316k |  | 0/0 | 0% |  | 28 | 0 |  () |  |  |
| gld | robinhood | robinhood/other | 2026-08-13 14:59 | $4.3M | $3.0M |  | 47/5 | 0% |  | 28 | 1 | $4.3M ($4.3M) | 18.6d | 0% |
| AGI | robinhood | Pons V2 (v4 hook curve) | 2026-08-26 21:56 | $1.0M | $546k | 3738 |  |  |  | 27 | 11 | $1.5M ($293k) | 35m | 27% |
| FATCOIN | robinhood | Pons V2 (v4 hook curve) | 2026-09-01 15:25 | $8.5M | $488k |  | 0/0 | 0% | 0xf372…b995 (1) | 27 | 62 | $2.3M ($282k) | -42m | 23% |
| PROLOGUE | robinhood | Pons V2 (v4 hook curve) | 2026-08-17 16:52 | $12.4M | $725k | 6433 |  |  |  | 27 | 18 | $8.7M ($555k) | 1.9d | 6% |
| 牛来 | bsc | bsc/other | 2026-08-14 08:07 | $91.2M | $1.4M | 53082 | 50/11 | 10% |  | 27 | 23 | $41.1M ($10k) | -237m | 13% |
| HMM | robinhood | Pons V1 (v3 pool) | 2026-07-19 07:54 | $22.6M | $866k | 14062 |  |  |  | 26 | 11 | $21.5M ($3.9M) | 2.8d | 0% |
| DJT | robinhood | Pons V2 (v4 hook curve) | 2026-08-13 14:25 | $1.7M | $361k |  | 0/0 | 0% | 0x2b94…3a87 (5) | 25 | 0 |  () |  |  |
| Hobbes | solana | pump.fun |  |  |  |  |  |  |  | 25 | 0 |  () |  |  |
| KITTY | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 06:01 | $90k | $24k |  | 0/0 | 0% |  | 25 | 2 | $1.4M ($753k) | 23m | 50% |
| MARSCITY | bsc | bsc/other | 2026-09-03 09:45 | $18k | $14k |  | 0/0 | 0% |  | 25 | 0 |  () |  |  |
| SCALE | robinhood | robinhood/other | 2026-07-21 18:11 | $9k | $8k |  |  |  |  | 25 | 1 | $296k ($296k) | 2.0h | 100% |
| BUTTHOLE | solana | solana/other |  |  |  |  |  |  |  | 24 | 0 |  () |  |  |
| CARDS | solana | solana/other | 2025-08-29 18:54 | $359.6M | $3.1M |  |  |  |  | 24 | 256 | $363.4M ($91.4M) | 7.8d | 0% |
| CYBERLEEK | solana | solana/other | 2026-08-15 21:07 | $1.5M | $415k |  |  |  |  | 24 | 57 | $3.4M ($1.3M) | 2.9d | 0% |
| Dinger | solana | pump.fun |  |  |  |  |  |  |  | 24 | 0 |  () |  |  |
| HOOD10 | robinhood | robinhood/other | 2026-08-25 00:38 | $2.3M | $237k |  |  |  | 0xb3e3…679d (1) | 24 | 12 | $3.4M ($198k) | -664m | 17% |
| SPACEHOOD | robinhood | Pons V2 (v4 hook curve) | 2026-07-14 14:48 | $9.7M | $935k | 3842 |  |  |  | 24 | 84 | $837k ($57k) | 1.9h | 55% |
| AU | robinhood | LONG (stock-paired) | 2026-08-28 02:51 | $4.7M | $708k | 3275 |  |  |  | 23 | 13 | $2.5M ($578k) | 7m | 15% |
| DTF | robinhood | Pons (WETH pool) | 2026-08-25 01:26 | $7.2M | $297k | 8590 |  |  |  | 23 | 13 | $6.3M ($368k) | 32m | 15% |
| GrokBot | solana | pump.fun |  |  |  |  |  |  |  | 23 | 0 |  () |  |  |
| HOOKR | robinhood | Pons V2 (v4 hook curve) | 2026-08-06 04:20 | $18.3M | $910k |  |  |  | 0x5a52…4aa2 (1) | 23 | 16 | $14.4M ($1.8M) | 13.1d | 0% |
| NET | robinhood | robinhood/other | 2026-07-16 17:32 | $85.6M | $823k | 6541 |  |  |  | 23 | 7 | $75.0M ($23.3M) | 35.9d | 0% |
| SAYLORMOON | robinhood | LONG (stock-paired) | 2026-08-29 01:55 | $2.1M | $497k |  | 0/0 | 0% |  | 23 | 38 | $2.1M ($307k) | 47m | 8% |
| TA | robinhood | Pons V2 (v4 hook curve) | 2026-08-05 21:14 | $2.5M | $146k |  |  |  |  | 23 | 6 | $3.6M ($1.1M) | 14.0d | 0% |
| USELESS | solana | bonk (letsbonk) | 2025-05-10 14:23 | $188.7M | $4.2M |  |  |  |  | 23 | 96 | $114.6M ($19.8M) | 23.7h | 0% |
| AAPLc | base | base/other | 2026-08-13 09:31 | $1.8M | $1.1M |  | 0/0 | 0% |  | 22 | 0 |  () |  |  |
| BLINK | robinhood | Pons V1 (v3 pool) | 2026-08-09 01:12 | $3.7M | $400k |  |  |  |  | 22 | 8 | $3.2M ($1.5M) | 50m | 0% |
| GG | robinhood | Pons V2 (v4 hook curve) | 2026-08-28 23:59 | $4.2M | $193k | 5606 |  |  |  | 22 | 14 | $5.3M ($55k) | 19m | 7% |
| SIT | robinhood | Pons V2 (v4 hook curve) | 2026-08-27 22:54 | $2.1M | $710k |  | 49/8 | 16% |  | 22 | 17 | $763k ($103k) | 1.1h | 53% |
| TOAD | solana | pump.fun | 2026-08-08 13:59 | $4.2M | $349k |  |  |  |  | 22 | 87 | $9.8M ($1.1M) | 43m | 0% |
| BOW | robinhood | Pons V2 (v4 hook curve) | 2026-08-08 18:17 | $5.8M | $199k | 4957 |  |  |  | 21 | 7 | $4.0M ($118k) | 2.9d | 14% |
| CLIPPY | robinhood | LONG (stock-paired) | 2026-07-17 19:36 | $2.2M | $457k |  |  |  |  | 21 | 13 | $1.6M ($113k) | 19.9d | 23% |
| COST | robinhood | robinhood/other | 2026-07-02 01:30 | $1.6M | $921k |  | 0/0 | 0% |  | 21 | 0 |  () |  |  |
| FRONG | robinhood | Pons V2 (v4 hook curve) | 2026-07-30 20:16 | $10.2M | $880k | 14140 |  |  |  | 21 | 4 | $6.5M ($1.7M) | 1.7h | 0% |
| JINQIAN | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 13:32 | $2.2M | $2.0M |  | 0/0 | 0% |  | 21 | 15 | $33.7M ($7.2M) | 55m | 0% |
| NVDAc | base | base/other | 2026-08-12 19:31 | $3.0M | $1.9M |  | 0/0 | 0% |  | 21 | 0 |  () |  |  |
| ROBINDOG | evm? | evm?/other |  |  |  |  | 0/0 |  |  | 21 | 0 |  () |  |  |
| worth | robinhood | Pons V1 (v3 pool) | 2026-07-10 17:39 | $1.3M | $151k |  |  |  |  | 21 | 87 | $616k ($37k) | 2.1h | 72% |
| Basecat | base | base/other | 2026-08-15 18:03 | $50.5M | $1.1M |  | 0/0 | 0% |  | 20 | 21 | $25.9M ($1.8M) | 11.1h | 0% |
| CLAN | robinhood | Pons V2 (v4 hook curve) | 2026-08-26 22:35 | $1.7M | $122k | 5423 |  |  |  | 20 | 14 | $2.9M ($182k) | 5m | 7% |
| Fold | base | base/other | 2026-09-01 06:45 | $112k | $33k |  | 0/0 | 0% |  | 20 | 0 |  () |  |  |
| PUMP | solana | solana/other | 2025-07-14 16:55 | $3.7B | $22.5M |  |  |  |  | 20 | 24 | $3.6B ($1.7B) | 99.3d | 0% |
| RDDT | robinhood | robinhood/other | 2026-07-10 22:00 | $1.9M | $1.4M |  | 0/0 | 0% |  | 20 | 0 |  () |  |  |
| tOpenAI | solana | solana/other |  |  |  |  | 0/0 |  |  | 20 | 0 |  () |  |  |
| CTO | solana | solana/other | 2026-09-01 08:44 | $4.9M | $286k | 2942 | 0/0 | 0% |  | 19 | 100 | $2.9M ($22k) | -15m | 12% |
| Jimothy | solana | pump.fun | 2026-07-16 10:15 | $8.1M | $721k |  |  |  |  | 19 | 241 | $9.9M ($3.4M) | 1.2d | 0% |
| Liluni | robinhood | Pons V2 (v4 hook curve) | 2026-07-23 22:57 | $1.8M | $139k |  |  |  |  | 19 | 3 | $1.3M ($1.1M) | 9.1d | 0% |
| TRUMP | solana | solana/other | 2025-01-18 10:39 | $2.4B | $22.4M |  |  |  |  | 19 | 14 | $5.7B ($2.3B) | 282.2d | 0% |
| UBIK | robinhood | Pons V2 (v4 hook curve) | 2026-09-01 16:27 | $9.7M | $310k |  |  |  |  | 19 | 31 | $8.0M ($2.4M) | -29m | 0% |
| BE | robinhood | robinhood/other |  | $790k | $221k |  |  |  |  | 18 | 0 |  () |  |  |
| BRODIE | robinhood | Pons (WETH pool) | 2026-07-14 01:40 | $75k | $30k |  |  |  |  | 18 | 4 | $2.3M ($2.2M) | 9.8d | 0% |
| ICOIN | robinhood | LONG (stock-paired) | 2026-07-22 13:08 | $8.2M | $843k |  |  |  |  | 18 | 61 | $4.7M ($137k) | 40.2d | 7% |
| $ROBBIE | robinhood | Pons V2 (v4 hook curve) | 2026-08-14 03:11 | $2.2M | $137k |  |  |  |  | 17 | 4 | $2.4M ($84k) | -12m | 25% |
| BISCOTTI | robinhood | Pons V2 (v4 hook curve) | 2026-08-26 17:01 | $3.2M | $166k |  |  |  |  | 17 | 4 | $3.2M ($2.7M) | 7m | 0% |
| CETS | bsc | bsc/other | 2026-08-06 04:23 | $17.4M | $565k |  | 0/0 | 0% |  | 17 | 16 | $7.3M ($69k) | 1.1d | 12% |
| CRUDECAT | robinhood | Pons V1 (v3 pool) | 2026-07-25 23:26 | $9.3M | $259k |  |  |  |  | 17 | 1 | $4.6M ($4.6M) | 20.1d | 0% |
| FLORK | bsc | bsc/other | 2026-08-28 21:13 | $21.7M | $615k |  | 0/0 | 0% |  | 17 | 22 | $8.2M ($1.1M) | 51m | 0% |
| FONZ | robinhood | Pons V1 (v3 pool) | 2026-07-16 03:13 | $265k | $70k |  |  |  | 0xdd19…874e (1) | 17 | 4 | $428k ($258k) | 3.4d | 100% |
| Fartcoin  | solana | pump.fun | 2024-10-18 06:09 | $173.0M | $8.1M |  |  |  |  | 17 | 14 | $311.8M ($171.6M) | 411.5d | 0% |
| GOYBEAM | robinhood | LONG (stock-paired) | 2026-07-20 23:57 | $616k | $236k |  |  |  | 0xde78…2aab (1) | 17 | 7 | $1.1M ($182k) | 37.7d | 43% |
| MANLET | solana | solana/other |  |  |  |  |  |  |  | 17 | 0 |  () |  |  |
| MON | base | base/other |  |  |  |  | 0/0 |  |  | 17 | 0 |  () |  |  |
| SV151 | solana | solana/other |  |  |  |  |  |  |  | 17 | 0 |  () |  |  |
| DEMOTHREE | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 23:37 | $1.5M | $366k | 3895 |  |  |  | 16 | 16 | $2.5M ($602k) | 1.9h | 12% |
| LDOL2 | solana | solana/other |  |  |  |  | 0/0 |  |  | 16 | 0 |  () |  |  |
| MARTIANS | robinhood | Pons V2 (v4 hook curve) | 2026-08-23 21:45 | $541k | $69k |  |  |  |  | 16 | 2 | $3.5M ($2.1M) | 1.9d | 0% |
| MUSHU | solana | pump.fun | 2024-07-03 00:46 | $3.7M | $283k |  |  |  |  | 16 | 7 | $9.5M ($6.3M) | 593.3d | 0% |
| QC | robinhood | robinhood/other | 2026-08-30 18:23 | $460k | $84k |  |  |  |  | 16 | 10 | $1.4M ($205k) | 1.5h | 30% |
| REDACTED | solana | solana/other |  |  |  |  |  |  |  | 16 | 0 |  () |  |  |
| SHROOM | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 14:47 | $1.8M | $114k |  | 49/12 | 10% |  | 16 | 45 | $2.3M ($819k) | 1.1d | 2% |
| SNDK | robinhood | Pons V2 (v4 hook curve) | 2026-07-01 14:45 | $1.8M | $347k |  |  |  |  | 16 | 0 |  () |  |  |
| TA | robinhood | Pons (WETH pool) | 2026-07-25 20:13 | $12k | $11k |  |  |  |  | 16 | 1 | $2.1M ($2.1M) | 57m | 0% |
| TripleT | solana | pump.fun | 2026-02-24 08:43 | $12.3M | $743k |  |  |  |  | 16 | 18 | $13.2M ($166k) | 9.7h | 6% |
| USAR | robinhood | robinhood/other | 2026-07-01 14:46 | $643k | $226k |  |  |  |  | 16 | 0 |  () |  |  |
| cc | solana | pump.fun |  |  |  |  |  |  |  | 16 | 0 |  () |  |  |
| CACHE | robinhood | Pons V2 (v4 hook curve) | 2026-08-28 01:47 | $1.6M | $395k |  |  |  |  | 15 | 16 | $1.6M ($93k) | 3.5h | 38% |
| CLANKER | robinhood | robinhood/other | 2026-08-14 00:26 | $2.1M | $1.8M |  |  |  |  | 15 | 4 | $195k ($42k) | 1.7h | 100% |
| FIRE | robinhood | robinhood/other | 2026-07-18 01:25 | $2.3M | $195k |  |  |  |  | 15 | 4 | $2.5M ($678k) | 17.0h | 25% |
| INJOH | robinhood | Pons (WETH pool) | 2026-07-31 00:40 | $3.3M | $235k | 2315 |  |  |  | 15 | 12 | $4.2M ($171k) | 4.8d | 17% |
| PAIR | robinhood | LONG (stock-paired) | 2026-08-29 19:07 | $5.4M | $274k |  |  |  |  | 15 | 7 | $3.9M ($2.8M) | 4.3h | 0% |
| PERPSHOOD | robinhood | Pons V2 (v4 hook curve) | 2026-08-27 18:25 | $285k | $50k |  |  |  |  | 15 | 0 |  () |  |  |
| Pistacio | solana | solana/other | 2026-08-25 19:22 | $803k | $128k |  |  |  |  | 15 | 175 | $8.3M ($267k) | 37m | 4% |
| QUOTRON | robinhood | Pons (WETH pool) | 2026-08-13 15:16 | $25.3M | $418k |  |  |  |  | 15 | 2 | $16.6M ($1.9M) | 2.5d | 0% |
| YT | bsc | bsc/other | 2026-07-26 18:11 | $144k | $38k |  |  |  |  | 15 | 0 |  () |  |  |
| ASTEROID | robinhood | robinhood/other |  | $802k | $328k |  |  |  |  | 14 | 8 | $1.2M ($125k) |  | 50% |
| BABYCATE | solana | pump.fun |  |  |  |  |  |  |  | 14 | 0 |  () |  |  |
| BGEX | solana | solana/other |  |  |  |  |  |  |  | 14 | 0 |  () |  |  |
| BLUECHIP | base | base/other | 2026-08-20 14:42 | $14.3M | $486k |  |  |  |  | 14 | 12 | $8.9M ($145k) | 1.5d | 8% |
| BUDDY | robinhood | Pons V1 (v3 pool) | 2026-07-22 00:07 | $15k | $11k |  |  |  |  | 14 | 1 | $27.7M ($27.7M) | 40.6d | 0% |
| CHILL | robinhood | Pons V2 (v4 hook curve) | 2026-08-07 14:42 | $890k | $88k |  |  |  |  | 14 | 2 | $265k ($117k) | 16.4d | 100% |
| DOPAMEME | solana | pump.fun |  |  |  |  |  |  |  | 14 | 0 |  () |  |  |
| EYE | solana | solana/other |  |  |  |  |  |  |  | 14 | 0 |  () |  |  |
| GMERALD | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 20:12 | $530k | $60k |  |  |  |  | 14 | 4 | $813k ($232k) | 1.1h | 100% |
| GTA | solana | pump.fun |  |  |  |  |  |  |  | 14 | 0 |  () |  |  |
| LIGER | robinhood | Pons V1 (v3 pool) | 2026-07-08 06:58 | $1.4M | $163k |  |  |  |  | 14 | 85 | $906k ($116k) | 3.7d | 53% |
| LONGDOG | robinhood | LONG (stock-paired) | 2026-08-25 19:11 | $667k | $233k |  |  |  |  | 14 | 9 | $475k ($186k) | 2.8d | 67% |
| NASDANQ | robinhood | Pons V1 (v3 pool) | 2026-08-04 00:49 | $2.2M | $198k |  |  |  |  | 14 | 3 | $2.4M ($296k) | 1.2d | 33% |
| SCHIFFY | robinhood | robinhood/other | 2026-08-29 18:24 | $3.0M | $295k |  |  |  |  | 14 | 16 | $1.3M ($1.0M) | 1.2h | 0% |
| VAULT | robinhood | Pons V1 (v3 pool) | 2026-07-27 20:43 | $612k | $118k |  |  |  |  | 14 | 3 | $2.3M ($771k) | 31.0d | 33% |
| AAPLCAT | robinhood | LONG (stock-paired) | 2026-07-17 14:01 | $411k | $166k |  |  |  |  | 13 | 4 | $641k ($494k) | 42.6d | 75% |
| Analyst | robinhood | robinhood/other | 2026-08-30 04:37 | $430k | $52k | 1879 |  |  |  | 13 | 8 | $1.1M ($618k) | 40m | 25% |
| BACKED | robinhood | Pons V2 (v4 hook curve) | 2026-07-17 13:09 | $888k | $136k |  |  |  |  | 13 | 3 | $1.2M ($261k) | 35.8d | 33% |
| BULL | robinhood | Pons V2 (v4 hook curve) | 2026-08-07 14:53 | $2.0M | $130k |  |  |  |  | 13 | 5 | $2.8M ($1.9M) | 12.7h | 0% |
| CATE | solana | pump.fun |  |  |  |  |  |  |  | 13 | 0 |  () |  |  |
| CLAUDE | robinhood | Pons (WETH pool) | 2026-07-24 00:28 | $3k | $4k |  |  |  |  | 13 | 0 |  () |  |  |
| DJT | robinhood | robinhood/other |  | $38k | $18k |  |  |  |  | 13 | 5 | $1.6M ($249k) |  | 40% |
| HOODon | robinhood | robinhood/other | 2026-07-23 05:38 | $462k | $73k |  |  |  |  | 13 | 0 |  () |  |  |
| KITSU | robinhood | Pons V1 (v3 pool) | 2026-07-01 12:13 | $1.9M | $170k |  |  |  |  | 13 | 0 |  () |  |  |
| LIGMA | robinhood | Pons V2 (v4 hook curve) | 2026-09-01 16:06 | $2.5M | $207k |  |  |  |  | 13 | 15 | $2.9M ($638k) | 56m | 7% |
| LOOKSMAX | solana | pump.fun | 2026-08-13 09:19 | $452k | $87k |  |  |  |  | 13 | 58 | $1.1M ($232k) | 1.3d | 43% |
| MUB | bsc | bsc/other | 2026-06-24 08:35 | $38.3M | $32k |  |  |  |  | 13 | 0 |  () |  |  |
| NAVIDIA | base | base/other | 2026-08-26 14:34 | $24k | $16k |  |  |  |  | 13 | 0 |  () |  |  |
| NUDES | robinhood | Pons V2 (v4 hook curve) | 2026-09-01 19:37 | $22.4M | $618k |  |  |  |  | 13 | 13 | $11.6M ($142k) | 32m | 8% |
| ORBIO | robinhood | LONG (stock-paired) | 2026-09-01 00:45 | $5.8M | $216k | 1370 |  |  |  | 13 | 23 | $5.3M ($733k) | 2.5h | 4% |
| PACK | robinhood | robinhood/other | 2026-08-12 21:31 | $581k | $117k |  |  |  | 0x6149…396d (1) | 13 | 2 | $2.2M ($1.5M) | 13.0d | 0% |
| PEPE | solana | solana/other | 2024-06-01 23:31 | $147k | $37k |  |  |  |  | 13 | 0 |  () |  |  |
| ROBINHOOD | robinhood | Pons V1 (v3 pool) | 2026-07-15 05:13 | $63k | $26k |  |  |  |  | 13 | 3 | $134k ($76k) | 42.2d | 100% |
| SPYX | solana | solana/other | 2026-02-11 11:14 | $777k | $2.0M |  |  |  |  | 13 | 0 |  () |  |  |
| UP | robinhood | Pons V1 (v3 pool) | 2026-07-21 03:27 | $404.7M | $2.4M |  |  |  |  | 13 | 2 | $403.0M ($157.6M) | 21.5d | 0% |
| AIW3 | bsc | bsc/other | 2026-08-03 09:25 | $39.7M | $1.0M |  |  |  |  | 12 | 0 |  () |  |  |
| BIGLY | robinhood | Pons V2 (v4 hook curve) | 2026-08-15 13:58 | $468k | $57k |  |  |  |  | 12 | 8 | $1.1M ($63k) | -6m | 50% |
| BUCK | robinhood | robinhood/other |  | $574k | $150k |  |  |  |  | 12 | 4 | $378k ($174k) |  | 75% |
| CBULLX | solana | solana/other |  |  |  |  |  |  |  | 12 | 0 |  () |  |  |
| CLAWX | solana | solana/other |  |  |  |  |  |  |  | 12 | 0 |  () |  |  |
| CUM | robinhood | Pons V2 (v4 hook curve) | 2026-09-01 22:22 | $301k | $150k |  |  |  |  | 12 | 10 | $468k ($67k) | 25m | 90% |
| EARN | robinhood | LONG (stock-paired) | 2026-07-23 16:16 | $2.9M | $525k |  |  |  |  | 12 | 5 | $1.7M ($1.4M) | 31.7d | 0% |
| FROGE | robinhood | robinhood/other | 2026-08-06 02:00 | $134k | $245k |  |  |  | 0x24ec…ba46 (1) | 12 | 3 | $2.8M ($203k) | 31m | 33% |
| GPRO | solana | solana/other |  |  |  |  |  |  |  | 12 | 0 |  () |  |  |
| HOODRAT | robinhood | Pons (WETH pool) | 2026-07-03 02:08 | $3.0M | $369k |  |  |  |  | 12 | 2 | $3.0M ($1.8M) | 29.2d | 0% |
| LINK | robinhood | Pons V1 (v3 pool) | 2026-07-14 04:18 | $513k | $93k |  |  |  |  | 12 | 103 | $925k ($32k) | 2.3h | 53% |
| LUCiC | bsc | bsc/other | 2024-09-19 07:06 | $29.3M | $3.6M |  |  |  |  | 12 | 0 |  () |  |  |
| Marketplier | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 19:05 | $80k | $23k | 3047 |  |  |  | 12 | 7 | $1.7M ($119k) | 2.5h | 29% |
| PEPE | robinhood | Pons V1 (v3 pool) | 2026-08-16 15:50 | $86k | $28k |  |  |  |  | 12 | 0 |  () |  |  |
| POOLS | robinhood | robinhood/other | 2026-07-30 16:41 | $2.2M | $455k |  |  |  |  | 12 | 1 | $1.4M ($1.4M) | 6.1d | 0% |
| Plumber | solana | pump.fun | 2026-08-11 05:39 | $119k | $52k |  |  |  |  | 12 | 60 | $708k ($36k) | 8.8h | 53% |
| RIBBITX | solana | solana/other |  |  |  |  |  |  |  | 12 | 0 |  () |  |  |
| SIRIUS | robinhood | Pons V2 (v4 hook curve) | 2026-08-30 09:03 | $1.7M | $105k |  |  |  |  | 12 | 8 | $1.0M ($513k) | 30m | 50% |
| TIM | robinhood | LONG (stock-paired) | 2026-07-14 18:01 | $56k | $59k |  |  |  |  | 12 | 14 | $424k ($67k) | 3.0d | 100% |
| TTWO | solana | solana/other |  |  |  |  |  |  |  | 12 | 0 |  () |  |  |
| Token | solana | pump.fun |  |  |  |  |  |  |  | 12 | 0 |  () |  |  |
| win | robinhood | Pons (WETH pool) | 2026-07-20 20:25 | $174k | $46k |  |  |  |  | 12 | 1 | $198k ($198k) | 41.0d | 100% |
| 圣心 | bsc | bsc/other | 2026-07-10 09:25 | $925k | $110k |  |  |  |  | 12 | 0 |  () |  |  |
| AAPLX | solana | solana/other |  |  |  |  |  |  |  | 11 | 0 |  () |  |  |
| ABTC | robinhood | Pons V2 (v4 hook curve) | 2026-08-30 01:21 | $51k | $21k |  |  |  |  | 11 | 0 |  () |  |  |
| BAWSAQ | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 21:50 | $2.2M | $122k |  |  |  |  | 11 | 8 | $6.1M ($498k) | 17.5h | 12% |
| CATSTR | robinhood | robinhood/other | 2026-07-14 20:25 | $89k | $30k |  |  |  |  | 11 | 1 | $193k ($193k) | 25.8d | 100% |
| CHILLHOUSE | solana | pump.fun | 2025-04-30 05:22 | $3.5M | $652k |  |  |  |  | 11 | 4 | $3.4M ($3.0M) | 452.1d | 0% |
| COOKWARE | robinhood | robinhood/other | 2026-07-30 13:24 | $180k | $78k |  |  |  |  | 11 | 3 | $137k ($109k) | 52m | 67% |
| FOLD | eth | eth/other | 2026-07-10 14:25 | $67.7M | $1.5M |  |  |  |  | 11 | 11 | $114.4M ($43.2M) | 40.0d | 0% |
| FROGE | solana | solana/other |  |  |  |  |  |  |  | 11 | 0 |  () |  |  |
| GPRO | solana | solana/other | 2026-09-01 00:30 | $144k | $49k | 8930 |  |  |  | 11 | 19 | $1.4M ($272k) | 9m | 42% |
| GRASS | robinhood | Pons V2 (v4 hook curve) | 2026-09-03 15:56 | $2.2M | $164k |  |  |  | 0x2154…8d25 (1) | 11 | 26 | $2.6M ($379k) | -2m | 12% |
| HENT | robinhood | robinhood/other | 2026-08-28 22:10 | $225k | $173k |  |  |  |  | 11 | 5 | $318k ($203k) | 31m | 100% |
| NILF | robinhood | Pons V1 (v3 pool) | 2026-07-20 20:11 | $6k | $6k |  |  |  |  | 11 | 2 | $233k ($164k) | 9.3d | 100% |
| OOF | robinhood | Pons V2 (v4 hook curve) | 2026-07-30 00:31 | $293k | $139k |  |  |  |  | 11 | 10 | $738k ($294k) | 32.7d | 70% |
| OPENAI | solana | solana/other |  |  |  |  |  |  |  | 11 | 0 |  () |  |  |
| PONGO | robinhood | Pons V1 (v3 pool) | 2026-07-14 18:52 | $2.5M | $205k |  |  |  |  | 11 | 1 | $3.8M ($3.8M) | 46.7d | 0% |
| ROBINCAT | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 22:17 | $8.1M | $231k | 5175 |  |  |  | 11 | 13 | $3.5M ($1.0M) | 23m | 0% |
| SPCXx | solana | solana/other |  |  |  |  |  |  |  | 11 | 0 |  () |  |  |
| TYGR | robinhood | Pons V1 (v3 pool) | 2026-07-20 17:34 | $371k | $80k |  |  |  |  | 11 | 1 | $309k ($309k) | 3.1d | 100% |
| BUN | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 15:37 | $14.6M | $356k |  |  |  | 0xc433…f68b (1) | 10 | 34 | $15.2M ($3.1M) | 2m | 0% |
| BUTTERCOIN | robinhood | Pons V1 (v3 pool) | 2026-07-20 18:20 | $41k | $22k |  |  |  |  | 10 | 1 | $356k ($356k) | 1.3d | 100% |
| CHOMP | solana | pump.fun | 2026-09-01 07:21 | $45k | $19k |  |  |  |  | 10 | 0 |  () |  |  |
| CLUG | solana | solana/other |  |  |  |  |  |  |  | 10 | 0 |  () |  |  |
| COAT | robinhood | Pons V2 (v4 hook curve) | 2026-08-18 06:07 | $327k | $188k |  |  |  |  | 10 | 4 | $595k ($94k) | 5.6d | 75% |
| COPPERINU | robinhood | Pons V2 (v4 hook curve) | 2026-08-29 09:35 | $5.2M | $220k |  |  |  |  | 10 | 5 | $11.2M ($8.6M) | 2m | 0% |
| FINDER | robinhood | LONG (stock-paired) | 2026-07-22 14:27 | $79k | $75k |  |  |  |  | 10 | 4 | $152k ($62k) | 37.4d | 100% |
| GIWA | robinhood | Pons V1 (v3 pool) | 2026-07-27 08:07 | $268k | $61k |  |  |  |  | 10 | 0 |  () |  |  |
| GJIM | solana | solana/other |  |  |  |  |  |  |  | 10 | 0 |  () |  |  |
| GOOGLB | bsc | bsc/other | 2026-07-31 07:29 | $30.2M | $851k |  |  |  |  | 10 | 0 |  () |  |  |
| GTR | robinhood | robinhood/other | 2026-07-24 15:34 | $596k | $118k |  |  |  |  | 10 | 2 | $2.0M ($766k) | 1.1h | 50% |
| HUGCOIN | robinhood | LONG (stock-paired) | 2026-09-03 13:56 | $189k | $45k |  |  |  |  | 10 | 10 | $930k ($342k) | 6m | 60% |
| KINS | solana | pump.fun |  |  |  |  |  |  |  | 10 | 0 |  () |  |  |
| KISS | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 09:44 | $54k | $22k |  |  |  | 0x3cc3…e29a (1) | 10 | 1 | $1.4M ($1.4M) | 21m | 0% |
| LONGCAT | robinhood | robinhood/other | 2026-08-06 00:10 | $35k | $17k |  |  |  |  | 10 | 1 | $745k ($745k) | 4.1d | 100% |
| MARSCOIN | robinhood | LONG (stock-paired) | 2026-07-23 11:24 | $45k | $84k |  |  |  |  | 10 | 1 | $724k ($724k) | 2.9h | 100% |
| MOS | solana | solana/other | 2026-08-11 22:34 | $1.6M | $309k |  |  |  |  | 10 | 37 | $456k ($286k) | 6m | 92% |
| NTF | robinhood | Pons V2 (v4 hook curve) | 2026-08-28 17:43 | $65k | $24k |  |  |  |  | 10 | 2 | $804k ($646k) | 1.4h | 100% |
| NVDAX | solana | solana/other |  |  |  |  |  |  |  | 10 | 0 |  () |  |  |
| PEAR | robinhood | LONG (stock-paired) | 2026-08-26 12:58 | $85k | $26k |  |  |  |  | 10 | 3 | $478k ($91k) | 1.3d | 100% |
| PMAV | robinhood | robinhood/other | 2026-07-16 01:57 | $62k | $75k |  |  |  |  | 10 | 1 | $624k ($624k) | 3.0d | 100% |
| PRISM | robinhood | Pons (WETH pool) | 2026-08-03 23:56 | $3.1M | $236k |  |  |  | 0x9bb0…3933 (1) | 10 | 3 | $2.6M ($324k) | 6.4h | 33% |
| SEMI | robinhood | Pons V2 (v4 hook curve) | 2026-08-13 23:07 | $2.0M | $1.0M |  |  |  |  | 10 | 3 | $807k ($612k) | 14.2d | 67% |
| SKHYB | bsc | bsc/other | 2026-07-14 05:30 | $25.0M | $1.0M |  |  |  |  | 10 | 0 |  () |  |  |
| STUPIDINU | robinhood | Pons V2 (v4 hook curve) | 2026-08-30 21:54 | $91k | $28k |  |  |  |  | 10 | 7 | $180k ($142k) | 23.7h | 100% |
| TAIWAN | robinhood | LONG (stock-paired) | 2026-08-31 17:46 | $542k | $214k | 1310 |  |  |  | 10 | 3 | $595k ($556k) | 10m | 67% |
| TRIPLET | robinhood | Pons V1 (v3 pool) | 2026-07-15 04:57 | $91k | $32k |  |  |  |  | 10 | 7 | $430k ($141k) | 46.6d | 86% |
| TSLAx | solana | solana/other | 2026-02-11 11:43 | $378k | $2.1M |  |  |  |  | 10 | 0 |  () |  |  |
| TTWO | robinhood | Pons V1 (v3 pool) | 2026-08-28 16:33 | $1.9M | $838k |  |  |  |  | 10 | 0 |  () |  |  |
| VYNEX | robinhood | Pons V2 (v4 hook curve) | 2026-08-27 13:40 | $203k | $42k |  |  |  |  | 10 | 4 | $1.5M ($1.0M) | 20.4h | 0% |
| memestock | bsc | bsc/other | 2026-08-12 13:45 | $868.9M | $39.3M |  |  |  |  | 10 | 9 | $3.1M ($259k) | 1.9h | 33% |
| 222 | robinhood | robinhood/other | 2026-08-07 23:16 | $185k | $64k |  |  |  |  | 9 | 0 |  () |  |  |
| 67 | solana | pump.fun |  |  |  |  |  |  |  | 9 | 0 |  () |  |  |
| AIAIAI | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 11:37 | $1.8M | $291k | 1565 |  |  |  | 9 | 5 | $1.5M ($306k) | 14.1h | 20% |
| BOT | solana | solana/other |  |  |  |  |  |  |  | 9 | 0 |  () |  |  |
| CARTEL | solana | solana/other |  |  |  |  |  |  |  | 9 | 0 |  () |  |  |
| CHUD | robinhood | Pons V2 (v4 hook curve) | 2026-08-06 16:25 | $81k | $26k |  |  |  | 0x7c7b…cdb5 (1) | 9 | 3 | $18k ($8k) | -795m | 100% |
| FORESKIN | robinhood | LONG (stock-paired) | 2026-08-30 21:49 | $1.2M | $135k |  |  |  | 0x4112…412d (1) | 9 | 5 | $834k ($662k) | 1.9d | 60% |
| GAEJUKI | robinhood | Pons V2 (v4 hook curve) | 2026-08-08 05:32 | $66k | $24k |  |  |  |  | 9 | 1 | $44k ($44k) | 2.5d | 100% |
| GOLD | solana | solana/other |  |  |  |  |  |  |  | 9 | 0 |  () |  |  |
| Givest | robinhood | Pons (WETH pool) | 2026-07-15 19:38 | $201k | $75k |  |  |  | 0xb6b5…b523 (1) | 9 | 2 | $581k ($211k) | 2.5d | 100% |
| K-HOME | solana | pump.fun |  |  |  |  |  |  |  | 9 | 0 |  () |  |  |
| LUCIA | robinhood | robinhood/other |  | $324k | $214k |  |  |  |  | 9 | 12 | $1.2M ($298k) |  | 25% |
| Link | solana | solana/other |  |  |  |  |  |  |  | 9 | 0 |  () |  |  |
| MANCER | robinhood | Pons V1 (v3 pool) | 2026-08-07 00:37 | $12.1M | $690k |  |  |  |  | 9 | 9 | $12.2M ($8.7M) | 22.3d | 0% |
| MCDX | solana | solana/other |  |  |  |  |  |  |  | 9 | 0 |  () |  |  |
| MEOWSHI | robinhood | Pons (WETH pool) | 2026-07-29 16:24 | $35k | $23k |  |  |  |  | 9 | 2 | $411k ($363k) | 5.0d | 100% |
| NAV | robinhood | Pons V1 (v3 pool) | 2026-08-31 20:31 | $302k | $128k |  |  |  |  | 9 | 6 | $1.3M ($219k) | 42m | 33% |
| PENGUIN | solana | pump.fun | 2026-01-16 19:29 | $1.2M | $249k |  |  |  |  | 9 | 24 | $49.8M ($392k) | 2.3d | 4% |
| PERV | robinhood | LONG (stock-paired) | 2026-09-03 02:54 | $60k | $51k |  |  |  |  | 9 | 0 |  () |  |  |
| PONSTR | robinhood | Pons V1 (v3 pool) | 2026-07-21 18:04 | $189k | $56k |  |  |  |  | 9 | 1 | $60k ($60k) | 56m | 100% |
| PONZI | solana | solana/other |  |  |  |  |  |  |  | 9 | 0 |  () |  |  |
| PRINTER | robinhood | robinhood/other | 2026-08-15 03:12 | $2.2M | $441k |  |  |  |  | 9 | 3 | $2.3M ($1.9M) | 2.7d | 0% |
| Qenis | solana | pump.fun |  |  |  |  |  |  |  | 9 | 0 |  () |  |  |
| SCFROGN | solana | solana/other |  |  |  |  |  |  |  | 9 | 0 |  () |  |  |
| SENDER | robinhood | LONG (stock-paired) | 2026-09-01 01:45 | $240k | $122k | 904 |  |  |  | 9 | 4 | $387k ($298k) | 26m | 100% |
| SNOO | robinhood | robinhood/other | 2026-08-03 06:15 | $144k | $163k |  |  |  |  | 9 | 4 | $115k ($53k) | 10.7d | 100% |
| TWO | robinhood | Pons V2 (v4 hook curve) | 2026-08-28 19:47 | $2.3M | $207k |  |  |  |  | 9 | 5 | $2.1M ($1.9M) | 4.3h | 0% |
| VACCINU | robinhood | Pons V2 (v4 hook curve) | 2026-09-01 22:36 | $331k | $151k |  |  |  |  | 9 | 9 | $1.1M ($77k) | 1.5h | 44% |
| VEX | robinhood | robinhood/other | 2026-07-03 16:34 | $4.4M | $365k |  |  |  |  | 9 | 1 | $4.6M ($4.6M) | 57.5d | 0% |
| WISHBONE | robinhood | Pons (WETH pool) | 2026-07-08 16:58 | $1.7M | $194k |  |  |  |  | 9 | 62 | $1.9M ($702k) | 1.1d | 2% |
| fih | solana | pump.fun |  |  |  |  |  |  |  | 9 | 0 |  () |  |  |
| fomo | solana | pump.fun |  |  |  |  |  |  |  | 9 | 0 |  () |  |  |
| jellyfish | solana | pump.fun |  |  |  |  |  |  |  | 9 | 0 |  () |  |  |
| neet | solana | pump.fun | 2025-04-27 00:58 | $31.0M | $1.8M |  |  |  |  | 9 | 17 | $30.3M ($17.2M) | 309.6d | 0% |
| nosis | solana | pump.fun |  |  |  |  |  |  |  | 9 | 0 |  () |  |  |
| wtCOIN | base | base/other | 2026-02-10 01:33 | $146k | $35k |  |  |  |  | 9 | 0 |  () |  |  |
| 牛13 | bsc | bsc/other | 2026-05-21 12:44 | $379k | $83k |  |  |  |  | 9 | 0 |  () |  |  |
| 0xZAPS | robinhood | Pons (WETH pool) | 2026-07-21 14:30 | $1.4M | $546k |  |  |  |  | 8 | 3 | $1.4M ($1.1M) | 40.2d | 0% |
| 6 | robinhood | robinhood/other | 2026-08-24 17:37 | $35k | $16k |  |  |  |  | 8 | 1 | $383k ($383k) | 6.9h | 100% |
| AP | robinhood | LONG (stock-paired) | 2026-07-13 12:13 | $1.8M | $377k |  |  |  |  | 8 | 5 | $871k ($379k) | 14.2d | 60% |
| BABAB | bsc | bsc/other | 2026-08-03 07:01 | $3.7M | $416k |  |  |  |  | 8 | 0 |  () |  |  |
| BE | robinhood | robinhood/other | 2026-09-03 03:02 | $52k | $136k |  |  |  |  | 8 | 0 |  () |  |  |
| BOOMER | robinhood | Pons V2 (v4 hook curve) | 2026-08-08 00:27 | $1.2M | $111k |  |  |  |  | 8 | 2 | $707k ($114k) | 3.2h | 50% |
| BOWYER | robinhood | robinhood/other | 2026-07-14 00:09 | $102k | $53k |  |  |  |  | 8 | 1 | $574k ($574k) | 8.9d | 100% |
| Buttcoin | solana | pump.fun | 2026-01-09 13:36 | $12.3M | $845k |  |  |  |  | 8 | 60 | $13.9M ($804k) | 2.1d | 2% |
| CASH | solana | solana/other |  |  |  |  |  |  |  | 8 | 0 |  () |  |  |
| CGRINX | solana | solana/other |  |  |  |  |  |  |  | 8 | 0 |  () |  |  |
| COCO | robinhood | Pons (WETH pool) | 2026-07-08 22:18 | $467k | $86k |  |  |  |  | 8 | 1 | $138k ($138k) | 32.1d | 100% |
| COGBULL2 | solana | solana/other |  |  |  |  |  |  |  | 8 | 0 |  () |  |  |
| CPEPE2 | solana | solana/other |  |  |  |  |  |  |  | 8 | 0 |  () |  |  |
| CVXV666 | solana | pump.fun |  |  |  |  |  |  |  | 8 | 0 |  () |  |  |
| ELOTÉ | solana | solana/other |  |  |  |  |  |  |  | 8 | 0 |  () |  |  |
| FAFO | robinhood | Pons V2 (v4 hook curve) | 2026-08-30 03:10 | $628k | $66k |  |  |  |  | 8 | 3 | $9.3M ($4.1M) | 15m | 0% |
| GMEX | solana | solana/other |  |  |  |  |  |  |  | 8 | 0 |  () |  |  |
| GOLD | solana | solana/other |  |  |  |  |  |  |  | 8 | 0 |  () |  |  |
| GOOGOL | robinhood | robinhood/other |  | $8k | $10k |  |  |  |  | 8 | 7 | $391k ($49k) |  | 100% |
| HARAM | robinhood | Pons V2 (v4 hook curve) | 2026-09-03 16:57 | $614k | $214k |  |  |  |  | 8 | 7 | $801k ($187k) | 5m | 71% |
| HARDER | robinhood | robinhood/other | 2026-09-03 21:42 | $226k | $126k |  |  |  |  | 8 | 8 | $199k ($65k) | 1m | 100% |
| HOTDOG | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 21:47 | $3.7M | $178k |  |  |  | 0xd636…0428 (1) | 8 | 31 | $4.0M ($2.1M) | -31m | 0% |
| Max | bsc | bsc/other | 2026-08-01 07:50 | $10.9M | $435k |  |  |  |  | 8 | 9 | $5.3M ($3.0M) | 23.1d | 0% |
| OGDOGE | solana | solana/other |  |  |  |  |  |  |  | 8 | 0 |  () |  |  |
| ORCL | robinhood | robinhood/other | 2026-07-01 14:46 | $595k | $35k |  |  |  |  | 8 | 0 |  () |  |  |
| PAWFIVEN | solana | solana/other |  |  |  |  |  |  |  | 8 | 0 |  () |  |  |
| PLTS | robinhood | Pons (WETH pool) | 2026-07-26 15:36 | $146k | $136k |  |  |  |  | 8 | 1 | $1.1M ($1.1M) | 1.4d | 0% |
| PURR | robinhood | Pons V2 (v4 hook curve) | 2026-08-08 06:17 | $269k | $48k |  |  |  |  | 8 | 3 | $897k ($710k) | 1.6d | 67% |
| PosM | robinhood | robinhood/other | 2026-08-06 02:29 | $365k | $143k |  |  |  |  | 8 | 2 | $175k ($118k) | 51m | 100% |
| ROBIN | robinhood | Pons V2 (v4 hook curve) | 2026-08-25 18:29 | $86k | $81k |  |  |  |  | 8 | 2 | $650k ($233k) | 51m | 50% |
| SCAM | solana | pump.fun |  |  |  |  |  |  |  | 8 | 0 |  () |  |  |
| STRATTON | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 16:41 | $3.2M | $152k |  |  |  |  | 8 | 8 | $4.4M ($2.3M) | 44m | 0% |
| TIMELESS | bsc | bsc/other | 2026-06-16 15:27 | $645k | $85k |  |  |  |  | 8 | 0 |  () |  |  |
| TJR | solana | pump.fun |  |  |  |  |  |  |  | 8 | 0 |  () |  |  |
| TROOPET | solana | solana/other |  |  |  |  |  |  |  | 8 | 0 |  () |  |  |
| TSMI | robinhood | robinhood/other |  | $350k | $78k |  |  |  |  | 8 | 5 | $400k ($182k) |  | 100% |
| YUGE | robinhood | robinhood/other |  | $5k | $3k |  |  |  |  | 8 | 1 | $177k ($177k) |  | 100% |
| inuzard | solana | pump.fun | 2026-08-28 22:22 | $134k | $40k |  |  |  |  | 8 | 36 | $475k ($121k) | 5.9h | 100% |
| plumber | base | base/other | 2026-08-12 00:34 | $4.6M | $245k |  |  |  |  | 8 | 8 | $1.2M ($157k) | 5.0d | 25% |
| tKalshi | solana | solana/other | 2026-05-13 14:30 | $652k | $624k |  |  |  |  | 8 | 0 |  () |  |  |
| unc | solana | pump.fun |  |  |  |  |  |  |  | 8 | 0 |  () |  |  |
| 富贵 | bsc | bsc/other | 2026-07-07 01:36 | $2.1M | $232k |  |  |  |  | 8 | 8 | $1.0M ($346k) | 45.1d | 50% |
| 🚀 | robinhood | robinhood/other |  | $660k | $79k |  |  |  |  | 8 | 3 | $1.5M ($583k) |  | 33% |
| 67coin | solana | pump.fun |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| ANDURL | solana | solana/other |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| APEC | solana | solana/other |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| ASH | solana | solana/other |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| Artcoin | robinhood | Pons (WETH pool) | 2026-07-24 21:40 | $100k | $34k |  |  |  |  | 7 | 1 | $101k ($101k) | 29.0d | 100% |
| BALD | base | base/other | 2026-08-23 16:00 | $161k | $62k |  |  |  |  | 7 | 3 | $259k ($91k) | 4.1d | 100% |
| BEAVER | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 17:59 | $1.4M | $361k |  |  |  |  | 7 | 22 | $2.0M ($281k) | 46m | 14% |
| BFINGERN | solana | solana/other |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| BOIÚNA | solana | pump.fun |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| CASHCOW | robinhood | robinhood/other | 2026-08-29 19:35 | $180k | $33k |  |  |  |  | 7 | 2 | $1.5M ($287k) | 44m | 50% |
| CHANCE | solana | pump.fun |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| DATABEAR | robinhood | Pons (WETH pool) | 2026-07-09 12:32 | $46k | $24k |  |  |  |  | 7 | 1 | $1.3M ($1.3M) | 3.4d | 0% |
| DIH | robinhood | Pons V1 (v3 pool) | 2026-07-02 08:44 | $180k | $75k |  |  |  | 0xe1c3…75c2 (1) | 7 | 0 |  () |  |  |
| DOGGYSTYLE | solana | pump.fun |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| FRANKLIN | robinhood | Pons V1 (v3 pool) | 2026-07-14 20:42 | $37k | $19k |  |  |  |  | 7 | 0 |  () |  |  |
| FWA | eth | eth/other | 2026-07-16 17:43 | $12.6M | $869k |  |  |  |  | 7 | 7 | $27.3M ($11.6M) | 23.2d | 0% |
| GTA6 | solana | solana/other |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| GUNICORN | solana | pump.fun |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| HANTA | solana | solana/other |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| HEDGE | robinhood | robinhood/other | 2026-08-20 16:04 | $20k | $21k |  |  |  |  | 7 | 1 | $2.3M ($2.3M) | 5.7d | 0% |
| HODL | robinhood | Pons V1 (v3 pool) | 2026-07-02 12:36 | $288k | $63k |  |  |  |  | 7 | 10 | $186k ($157k) | 7.3d | 100% |
| KET | solana | pump.fun |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| KITTY | solana | bonk (letsbonk) | 2025-10-02 18:34 | $4.6M | $380k |  |  |  |  | 7 | 10 | $338k ($103k) | 214.9d | 60% |
| LAMBO | robinhood | Pons V2 (v4 hook curve) | 2026-09-03 08:24 | $82k | $27k |  |  |  |  | 7 | 0 |  () |  |  |
| MACRODUCK | solana | pump.fun |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| MERD | robinhood | Pons V1 (v3 pool) | 2026-08-01 17:50 | $72k | $28k |  |  |  | 0x1cc1…effa (1) | 7 | 1 | $238k ($238k) | 9.6d | 100% |
| MICRODICK | robinhood | robinhood/other |  | $117k | $126k |  |  |  |  | 7 | 0 |  () |  |  |
| MOSAIC | robinhood | Pons V2 (v4 hook curve) | 2026-08-25 19:09 | $129k | $33k |  |  |  |  | 7 | 1 | $543k ($543k) | 2.8d | 100% |
| MOTION | robinhood | Pons V1 (v3 pool) | 2026-07-19 18:09 | $3.8M | $238k |  |  |  |  | 7 | 2 | $7.7M ($5.0M) | 22.4d | 0% |
| MRVL | robinhood | Pons V1 (v3 pool) | 2026-07-30 05:18 | $340k | $249k |  |  |  |  | 7 | 0 |  () |  |  |
| Machi | solana | pump.fun |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| Martians | solana | pump.fun |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| Momota | solana | pump.fun |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| PF | robinhood | robinhood/other | 2026-08-30 22:10 | $15k | $16k |  |  |  |  | 7 | 5 | $313k ($263k) | 38m | 100% |
| PONSBOT | robinhood | Pons V2 (v4 hook curve) | 2026-08-25 20:19 | $380k | $59k |  |  |  |  | 7 | 3 | $605k ($489k) | 3.9h | 100% |
| Packz | robinhood | Pons (WETH pool) | 2026-07-16 15:08 | $7k | $10k |  |  |  |  | 7 | 2 | $332k ($323k) | 27m | 100% |
| QUANTA | robinhood | robinhood/other | 2026-08-25 23:51 | $48k | $174 |  |  |  |  | 7 | 2 | $319k ($288k) | -6m | 100% |
| REAL | robinhood | LONG (stock-paired) | 2026-07-20 04:08 | $49k | $71k |  |  |  |  | 7 | 1 | $1.2M ($1.2M) | 2.1d | 0% |
| ROBINHOOD | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 17:53 | $58k | $20k |  |  |  |  | 7 | 5 | $1.1M ($491k) | 5m | 40% |
| ROBINVAULT | robinhood | Pons V2 (v4 hook curve) | 2026-08-15 12:58 | $705k | $106k |  |  |  |  | 7 | 2 | $414k ($202k) | 11.2d | 100% |
| SCOPL | robinhood | Pons V2 (v4 hook curve) | 2026-08-18 08:48 | $809k | $134k |  |  |  |  | 7 | 5 | $651k ($50k) | 2.3d | 80% |
| SNIFF | solana | solana/other |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| SOXLB | bsc | bsc/other | 2026-08-27 14:58 | $18.7M | $278k |  |  |  |  | 7 | 0 |  () |  |  |
| STACK | robinhood | Pons V2 (v4 hook curve) | 2026-08-12 18:35 | $682k | $91k |  |  |  | 0x7322…e25b (1) | 7 | 2 | $1.6M ($1.4M) | 1.3d | 0% |
| STONKS | robinhood | robinhood/other | 2026-08-12 22:57 | $11k | $6k |  |  |  |  | 7 | 1 | $1.5M ($1.5M) | -0m | 0% |
| UNIPEG | robinhood | robinhood/other | 2026-08-05 04:02 | $273k | $119k |  |  |  |  | 7 | 2 | $115k ($75k) | 19.2d | 100% |
| VISTA | robinhood | Pons (WETH pool) | 2026-07-13 20:37 | $2.6M | $239k |  |  |  |  | 7 | 48 | $4.3M ($308k) | 51.1d | 4% |
| VLR | robinhood | robinhood/other | 2026-08-29 23:57 | $20k | $32k |  |  |  |  | 7 | 1 | $3.0M ($3.0M) | 1.7d | 0% |
| WIF | robinhood | Pons V2 (v4 hook curve) | 2026-08-06 09:42 | $597k | $72k |  |  |  |  | 7 | 5 | $2.1M ($370k) | 3.4d | 20% |
| ZOE | robinhood | robinhood/other | 2026-09-03 10:53 | $141k | $105k |  |  |  |  | 7 | 7 | $343k ($64k) | 8m | 100% |
| Zoe | solana | pump.fun | 2026-08-17 21:00 | $91k | $35k |  |  |  |  | 7 | 64 | $1.5M ($199k) | 6.8d | 19% |
| catalyst | solana | pump.fun |  |  |  |  |  |  |  | 7 | 0 |  () |  |  |
| meow | robinhood | Pons (WETH pool) | 2026-07-11 09:14 | $241k | $61k |  |  |  |  | 7 | 1 | $396k ($396k) | 53.3d | 100% |
| moon | robinhood | Pons (WETH pool) | 2026-08-20 23:04 | $4.3M | $334k |  |  |  |  | 7 | 3 | $1.2M ($256k) | -325m | 33% |
| r0b | robinhood | Pons V1 (v3 pool) | 2026-07-21 18:49 | $12k | $10k |  |  |  |  | 7 | 2 | $748k ($265k) | 59m | 50% |
| $USA | robinhood | LONG (stock-paired) | 2026-08-22 00:52 | $34k | $56k |  |  |  |  | 6 | 0 |  () |  |  |
| ANSUM | solana | pump.fun |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| BAWSAQ | robinhood | robinhood/other |  | $409k | $45k |  |  |  |  | 6 | 7 | $1.8M ($392k) |  | 29% |
| BUCK | robinhood | LONG (stock-paired) | 2026-07-22 21:25 | $38k | $34k |  |  |  |  | 6 | 1 | $57k ($57k) | 27.1d | 100% |
| BULLSHIT | solana | solana/other | 2026-08-17 18:59 | $3.1M | $258k |  |  |  |  | 6 | 22 | $1.5M ($851k) | 23m | 23% |
| BUT | solana | solana/other |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| CASHBIRD | robinhood | Pons V2 (v4 hook curve) | 2026-09-01 21:50 | $213k | $124k |  |  |  |  | 6 | 7 | $481k ($126k) | 13m | 86% |
| CAYENNE | robinhood | LONG (stock-paired) | 2026-09-02 21:19 | $291k | $45k |  |  |  |  | 6 | 4 | $1.6M ($381k) | 51m | 25% |
| CHIPS | robinhood | Pons V2 (v4 hook curve) | 2026-08-26 13:53 | $315k | $16k |  |  |  |  | 6 | 3 | $335k ($199k) | 3.9d | 100% |
| CLANKER | solana | solana/other |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| DCR | robinhood | Pons (WETH pool) | 2026-07-30 18:34 | $5k | $5k |  |  |  |  | 6 | 2 | $462k ($175k) | 12.1h | 100% |
| DINO | robinhood | LONG (stock-paired) | 2026-09-02 07:37 | $3.4M | $153k |  |  |  | 0x619a…3e42 (1) | 6 | 32 | $2.7M ($383k) | 25m | 6% |
| DROYD | solana | solana/other |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| EARLY | robinhood | robinhood/other |  | $22k | $11k |  |  |  |  | 6 | 1 | $562k ($562k) |  | 100% |
| ELON | robinhood | LONG (stock-paired) | 2026-08-30 00:05 | $102k | $26k |  |  |  |  | 6 | 5 | $258k ($29k) | 10.4h | 100% |
| EQUITY | robinhood | robinhood/other | 2026-08-12 22:32 | $8k | $8k |  |  |  |  | 6 | 1 | $619k ($619k) | 6.0h | 100% |
| FEFI | robinhood | Pons V2 (v4 hook curve) | 2026-07-29 03:08 | $97k | $33k |  |  |  |  | 6 | 0 |  () |  |  |
| FLUSHCAT | robinhood | robinhood/other |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| GAPPY | robinhood | Pons V1 (v3 pool) | 2026-07-15 11:09 | $12k | $9k |  |  |  |  | 6 | 1 | $169k ($169k) | 3.5d | 100% |
| GASOLINU | robinhood | robinhood/other | 2026-09-02 19:07 | $475k | $218k |  |  |  | 0x3505…3e52 (1) | 6 | 5 | $424k ($164k) | 22m | 80% |
| GM | robinhood | robinhood/other | 2026-08-27 17:29 | $49k | $17k |  |  |  |  | 6 | 2 | $279k ($149k) | 36m | 100% |
| HA | robinhood | LONG (stock-paired) | 2026-08-29 01:56 | $12k | $11k |  |  |  |  | 6 | 1 | $70k ($70k) | 11.6h | 100% |
| HDD | robinhood | robinhood/other | 2026-08-28 22:03 | $67k | $80k |  |  |  |  | 6 | 3 | $49k ($40k) | 31m | 100% |
| HOTDOG | robinhood | robinhood/other |  | $9k | $12k |  |  |  |  | 6 | 1 | $93k ($93k) |  | 100% |
| HOTDOG | robinhood | Pons V2 (v4 hook curve) | 2026-08-30 00:13 | $685k | $69k |  |  |  |  | 6 | 5 | $1.4M ($1.3M) | 3.1d | 0% |
| HUNNY | robinhood | Pons (WETH pool) | 2026-07-28 19:22 | $17k | $14k |  |  |  |  | 6 | 3 | $146k ($24k) | 11.8h | 100% |
| I | robinhood | Pons V2 (v4 hook curve) | 2026-09-01 02:36 | $186k | $109k |  |  |  |  | 6 | 4 | $289k ($231k) | 1.3d | 100% |
| IA | robinhood | robinhood/other | 2026-08-13 20:11 | $707k | $757k |  |  |  |  | 6 | 2 | $55k ($39k) | 6m | 100% |
| INVEST | robinhood | robinhood/other | 2026-08-21 21:45 | $114k | $49k |  |  |  |  | 6 | 2 | $124k ($53k) | 0m | 100% |
| JNJ | robinhood | robinhood/other | 2026-08-13 21:09 | $511k | $336k |  |  |  |  | 6 | 0 |  () |  |  |
| LLM | robinhood | robinhood/other | 2026-08-28 02:06 | $77k | $84k |  |  |  |  | 6 | 2 | $124k ($89k) | 3m | 100% |
| LOCK | robinhood | Pons V1 (v3 pool) | 2026-08-01 19:12 | $151k | $43k |  |  |  |  | 6 | 2 | $536k ($440k) | 22.1d | 100% |
| MADE | solana | solana/other |  |  |  | 4245 |  |  |  | 6 | 0 |  () |  |  |
| MARKET | solana | solana/other |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| MENSA | solana | pump.fun | 2026-07-02 02:29 | $619k | $112k |  |  |  |  | 6 | 46 | $2.1M ($251k) | 21.4h | 4% |
| MEOW | solana | pump.fun |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| MU | robinhood | robinhood/other | 2026-08-29 10:25 | $191k | $36k |  |  |  |  | 6 | 3 | $829k ($398k) | 4.7h | 100% |
| NP500 | robinhood | robinhood/other | 2026-08-29 14:44 | $10k | $9k |  |  |  |  | 6 | 2 | $158k ($77k) | 1.1h | 100% |
| NUBTC | robinhood | robinhood/other |  | $52k | $67k |  |  |  |  | 6 | 4 | $119k ($74k) |  | 100% |
| OPTIMUS | robinhood | LONG (stock-paired) | 2026-08-29 06:36 | $7.3M | $235k |  |  |  | 0x3057…1fe5 (1) | 6 | 15 | $9.7M ($393k) | 3.7d | 7% |
| OTC | solana | pump.fun | 2026-08-28 13:33 | $2.1M | $220k |  |  |  |  | 6 | 11 | $780k ($383k) | 25m | 55% |
| PARE | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 23:31 | $2.8M | $154k |  |  |  | 0x854d…7022 (1) | 6 | 34 | $4.3M ($658k) | 3.7h | 3% |
| PIXELCAT | robinhood | Pons V2 (v4 hook curve) | 2026-09-03 15:18 | $1.2M | $90k |  |  |  |  | 6 | 46 | $2.3M ($66k) | 18m | 17% |
| PLUMHORNN | solana | solana/other |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| POKERX | solana | solana/other |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| PONGETTE | robinhood | robinhood/other | 2026-08-12 18:01 | $41k | $19k |  |  |  |  | 6 | 0 |  () |  |  |
| POOH | robinhood | Pons V1 (v3 pool) | 2026-07-16 01:53 | $44k | $21k |  |  |  |  | 6 | 1 | $202k ($202k) | 8.1d | 100% |
| PUMPCADE | solana | solana/other | 2025-09-21 00:06 | $8.2M | $371k |  |  |  |  | 6 | 18 | $4.1M ($170k) | 3.5h | 11% |
| PURRS | robinhood | robinhood/other | 2026-08-14 22:32 | $356k | $71k |  |  |  |  | 6 | 17 | $1.3M ($297k) | 18.8d | 24% |
| QUBIT | robinhood | robinhood/other | 2026-08-28 17:00 | $824k | $245k |  |  |  |  | 6 | 4 | $408k ($164k) | 1.2h | 100% |
| RIP | robinhood | robinhood/other | 2026-07-27 13:41 | $1.5M | $287k |  |  |  |  | 6 | 5 | $2.2M ($321k) | 28.0d | 20% |
| ROCKET | robinhood | Pons V1 (v3 pool) | 2026-07-20 14:50 | $261k | $57k |  |  |  |  | 6 | 1 | $132k ($132k) | 14.6h | 100% |
| SILV | solana | solana/other |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| SISYPUSS | solana | pump.fun |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| SPARKY | solana | solana/other |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| SPCSEX | robinhood | LONG (stock-paired) | 2026-08-31 03:04 | $112k | $32k |  |  |  | 0x809c…9a6a (1) | 6 | 4 | $87k ($25k) | -574m | 100% |
| STACKS | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 19:38 | $273k | $52k |  |  |  |  | 6 | 6 | $881k ($320k) | 47m | 83% |
| STONKS | robinhood | Pons (WETH pool) | 2026-06-29 08:33 | $131k | $42k |  |  |  |  | 6 | 1 | $1.6M ($1.6M) | 18.5d | 0% |
| STOX | robinhood | Pons V1 (v3 pool) | 2026-09-01 16:12 | $40k | $20k |  |  |  |  | 6 | 2 | $195k ($84k) | 11m | 100% |
| SWOLE | robinhood | LONG (stock-paired) | 2026-08-26 01:18 | $876k | $128k |  |  |  |  | 6 | 3 | $1.5M ($1.3M) | 7.8d | 0% |
| SZR | robinhood | Pons V2 (v4 hook curve) | 2026-07-23 21:27 | $1.7M | $22k |  |  |  |  | 6 | 3 | $1.8M ($1.7M) | 3.6d | 0% |
| Sparky | solana | pump.fun |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| TREE | solana | solana/other |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| TREX | robinhood | LONG (stock-paired) | 2026-07-22 15:28 | $188k | $102k |  |  |  |  | 6 | 1 | $760k ($760k) | 2.5h | 100% |
| TSM | robinhood | robinhood/other |  | $1.6M | $616k |  |  |  |  | 6 | 0 |  () |  |  |
| UMBRA | solana | solana/other |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| VORX | solana | solana/other |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| X | robinhood | LONG (stock-paired) | 2026-08-28 09:14 | $36k | $16k |  |  |  |  | 6 | 5 | $571k ($426k) | 1.6d | 100% |
| biketyson | solana | pump.fun |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| butthole | robinhood | robinhood/other | 2026-09-03 08:25 | $220k | $99k |  |  |  | 0x5ffa…5df5 (1) | 6 | 6 | $697k ($347k) | -5m | 67% |
| der Wald | robinhood | Pons V1 (v3 pool) | 2026-07-21 20:25 | $44k | $21k |  |  |  |  | 6 | 1 | $141k ($141k) | 16.0h | 100% |
| kylie | solana | pump.fun |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| titcoin | solana | pump.fun |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| 🐂🀄 | solana | pump.fun |  |  |  |  |  |  |  | 6 | 0 |  () |  |  |
| 4663 | robinhood | Pons (WETH pool) | 2026-06-29 08:45 | $440k | $82k |  |  |  |  | 5 | 1 | $360k ($360k) | 63.0d | 100% |
| 530A | robinhood | Pons (WETH pool) | 2026-07-11 16:03 | $11k | $13k |  |  |  |  | 5 | 1 | $379k ($379k) | 3.6d | 100% |
| A | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 23:28 | $320k | $157k |  |  |  | 0xf80f…01df (1) | 5 | 3 | $276k ($217k) | 1.2d | 100% |
| AAPLon | bsc | bsc/other | 2025-11-07 19:32 | $3.4M | $8k |  |  |  |  | 5 | 0 |  () |  |  |
| AIRDROP | solana | solana/other | 2026-08-05 23:00 | $55k | $36k |  |  |  |  | 5 | 13 | $215k ($79k) | 19m | 100% |
| ASS | robinhood | robinhood/other | 2026-09-02 18:36 | $879k | $104k |  |  |  |  | 5 | 8 | $505k ($276k) | 1.0h | 100% |
| ATM | robinhood | robinhood/other | 2026-08-27 16:32 | $36k | $24k |  |  |  | 0xb8d1…b267 (1) | 5 | 1 | $438k ($438k) | 22m | 100% |
| BASELINE | base | base/other | 2026-08-28 10:01 | $403k | $72k |  |  |  |  | 5 | 6 | $2.8M ($533k) | 45m | 17% |
| BB | robinhood | Pons V2 (v4 hook curve) | 2026-08-13 15:52 | $375k | $77k |  |  |  |  | 5 | 0 |  () |  |  |
| BBB | robinhood | robinhood/other | 2026-09-01 16:55 | $22k | $22k |  |  |  | 0x91e7…5908 (2) | 5 | 3 | $171k ($71k) | 1.2h | 100% |
| BELIEVE | robinhood | LONG (stock-paired) | 2026-09-01 04:27 | $211k | $147k |  |  |  | 0x64f3…efd3 (1) | 5 | 4 | $155k ($97k) | 3m | 100% |
| BULL | solana | pump.fun |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| BURNIE | solana | pump.fun | 2026-04-03 03:08 | $1.7M | $262k |  |  |  |  | 5 | 9 | $9.1M ($1.6M) | 2.7d | 0% |
| BUTTHOLE | robinhood | robinhood/other | 2026-09-04 00:51 | $2.2M | $246k |  |  |  |  | 5 | 6 | $623k ($420k) | 26m | 67% |
| BYCOCKET | robinhood | Pons (WETH pool) | 2026-07-10 18:03 | $42k | $29k |  |  |  |  | 5 | 1 | $931k ($931k) | 6.0h | 100% |
| Binanceman | bsc | bsc/other | 2026-08-03 15:12 | $68k | $29k |  |  |  |  | 5 | 0 |  () |  |  |
| CAMELTOE | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 03:19 | $884k | $115k |  |  |  |  | 5 | 6 | $1.7M ($652k) | 1.9h | 33% |
| CC | robinhood | Pons V1 (v3 pool) | 2026-07-19 16:40 | $17k | $13k |  |  |  |  | 5 | 1 | $1.1M ($1.1M) | 2.4d | 0% |
| CHARIZARD | solana | solana/other |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| CUM | robinhood | robinhood/other |  | $10k | $10k |  |  |  |  | 5 | 2 | $52k ($38k) |  | 100% |
| DOBERMANN | solana | solana/other |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| EARTHCOIN | robinhood | LONG (stock-paired) | 2026-08-04 21:25 | $254k | $47k |  |  |  |  | 5 | 3 | $77k ($57k) | 4.5h | 100% |
| FART | solana | solana/other |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| FLETCH | robinhood | Pons (WETH pool) | 2026-07-13 19:16 | $242k | $69k |  |  |  |  | 5 | 1 | $928k ($928k) | 7.6d | 100% |
| FLOPS | robinhood | LONG (stock-paired) | 2026-08-28 03:07 | $183k | $105k |  |  |  |  | 5 | 1 | $262k ($262k) | 6.6d | 100% |
| FOMO | robinhood | robinhood/other | 2026-09-03 20:01 | $153k | $157k |  |  |  |  | 5 | 14 | $901k ($451k) | 8m | 57% |
| FOX | robinhood | robinhood/other | 2026-08-31 20:29 | $25k | $15k |  |  |  |  | 5 | 2 | $415k ($152k) | 10.7h | 100% |
| Froge | robinhood | robinhood/other | 2026-09-03 08:28 | $581k | $85k |  |  |  |  | 5 | 6 | $527k ($447k) | 9m | 100% |
| GATO | robinhood | robinhood/other | 2026-08-11 21:06 | $42k | $19k |  |  |  |  | 5 | 1 | $388k ($388k) | 1.6d | 100% |
| GENTLE | solana | pump.fun |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| GMEOW | robinhood | robinhood/other |  | $5k | $6k |  |  |  |  | 5 | 2 | $160k ($85k) |  | 100% |
| GODL | solana | solana/other |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| GOLDINU | solana | solana/other |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| GOOGLon | bsc | bsc/other | 2026-05-04 21:09 | $10.0M | $3k |  |  |  |  | 5 | 0 |  () |  |  |
| GRACE | robinhood | Pons V1 (v3 pool) | 2026-07-15 04:54 | $57k | $28k |  |  |  |  | 5 | 0 |  () |  |  |
| GUH | robinhood | LONG (stock-paired) | 2026-08-29 21:32 | $179k | $34k |  |  |  |  | 5 | 1 | $343k ($343k) | 3.0d | 100% |
| Guy | robinhood | Pons (WETH pool) | 2026-07-08 18:46 | $142k | $43k |  |  |  |  | 5 | 1 | $527k ($527k) | 47.9d | 100% |
| HOME | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 05:36 | $35k | $17k |  |  |  |  | 5 | 2 | $3.5M ($2.8M) | 1.6h | 0% |
| HOODIE | robinhood | Pons (WETH pool) | 2026-07-08 15:42 | $98k | $3.5M |  |  |  |  | 5 | 1 | $1.7M ($1.7M) | 1.9d | 0% |
| Huhcat | solana | solana/other |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| INCEL | robinhood | LONG (stock-paired) | 2026-07-22 13:20 | $1.2M | $287k |  |  |  | 0x37e7…0dfb (1) | 5 | 6 | $977k ($49k) | 36.5d | 50% |
| INTERN | robinhood | robinhood/other | 2026-07-28 22:35 | $117k | $26k |  |  |  |  | 5 | 1 | $823k ($823k) | 14.9d | 100% |
| JANITOR | robinhood | Pons V2 (v4 hook curve) | 2026-08-05 21:55 | $31k | $18k |  |  |  |  | 5 | 3 | $73k ($25k) | 4.8d | 100% |
| JEET | robinhood | Pons V2 (v4 hook curve) | 2026-09-03 18:50 | $572k | $149k |  |  |  |  | 5 | 5 | $479k ($218k) | 3m | 80% |
| JOHNDOG | robinhood | robinhood/other | 2026-09-02 01:25 | $939k | $307k |  |  |  |  | 5 | 5 | $995k ($432k) | 12.5h | 60% |
| LEGS | robinhood | Pons V2 (v4 hook curve) | 2026-09-03 21:03 | $2.8M | $154k |  |  |  |  | 5 | 10 | $3.9M ($2.9M) | 2m | 0% |
| MANIFEST | solana | pump.fun | 2026-05-17 04:07 | $12.5M | $529k |  |  |  |  | 5 | 2 | $26.2M ($13.2M) | 31.9d | 0% |
| MAST | robinhood | Pons V2 (v4 hook curve) | 2026-08-28 01:15 | $647k | $75k |  |  |  |  | 5 | 1 | $2.3M ($2.3M) | 1.9d | 0% |
| MEME | robinhood | Pons V2 (v4 hook curve) | 2026-09-03 20:30 | $215k | $116k |  |  |  |  | 5 | 6 | $4.2M ($135k) | 30m | 17% |
| MM | evm? | evm?/other |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| MODERATOR | robinhood | robinhood/other | 2026-07-30 01:16 | $37k | $63k |  |  |  |  | 5 | 2 | $62k ($24k) | 32.7d | 100% |
| MSFTB | bsc | bsc/other | 2026-07-20 16:44 | $2.9M | $180k |  |  |  |  | 5 | 0 |  () |  |  |
| MSFTon | bsc | bsc/other | 2026-06-24 12:59 | $3.0M | $124 |  |  |  |  | 5 | 0 |  () |  |  |
| MUMU | robinhood | Pons (WETH pool) | 2026-07-15 15:02 | $232k | $37k |  |  |  |  | 5 | 3 | $1.2M ($550k) | 18.3d | 33% |
| MarketCat | robinhood | Pons (WETH pool) | 2026-07-29 06:01 | $20k | $13k |  |  |  |  | 5 | 1 | $292k ($292k) | 12.8h | 100% |
| Morty | solana | pump.fun |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| NASDOG | robinhood | Pons (WETH pool) | 2026-07-10 08:46 | $14k | $12k |  |  |  |  | 5 | 1 | $143k ($143k) | 9.1h | 100% |
| NORMIE | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 02:25 | $79k | $23k |  |  |  |  | 5 | 4 | $727k ($238k) | 29m | 50% |
| OPTIMUS | robinhood | LONG (stock-paired) | 2026-07-19 09:30 | $402k | $156k |  |  |  |  | 5 | 3 | $1.4M ($853k) | 44.5d | 33% |
| OZZY | robinhood | Pons (WETH pool) | 2026-07-13 22:59 | $144k | $41k |  |  |  |  | 5 | 1 | $223k ($223k) | 47.2d | 100% |
| PENNYSTOCK | robinhood | LONG (stock-paired) | 2026-08-31 20:25 | $18k | $11k |  |  |  | 0x9ace…d51b (2) | 5 | 2 | $77k ($44k) | 1.1d | 100% |
| PEPARK | solana | pump.fun |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| PICKLES | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 23:59 | $208k | $37k |  |  |  |  | 5 | 10 | $879k ($228k) | 35m | 50% |
| PONSHOOD | robinhood | Pons V1 (v3 pool) | 2026-07-13 21:01 | $183k | $53k |  |  |  |  | 5 | 2 | $141k ($103k) | 9.1d | 100% |
| PONSTAR | robinhood | Pons (WETH pool) | 2026-07-14 00:35 | $78k | $33k |  |  |  |  | 5 | 1 | $78k ($78k) | 4.5d | 100% |
| POWERBALL | robinhood | robinhood/other | 2026-08-12 05:32 | $35k | $17k |  |  |  |  | 5 | 1 | $129k ($129k) | 18.2d | 100% |
| PRESS | robinhood | Pons V2 (v4 hook curve) | 2026-09-01 21:33 | $44k | $20k |  |  |  |  | 5 | 3 | $785k ($604k) | 20m | 100% |
| PUMPRPG | solana | pump.fun |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| QQQon | bsc | bsc/other | 2026-05-24 14:45 | $6.6M | $2k |  |  |  |  | 5 | 0 |  () |  |  |
| QTARD | robinhood | robinhood/other | 2026-09-01 08:10 | $14k | $11k |  |  |  |  | 5 | 3 | $301k ($41k) | 30m | 100% |
| RJGN | solana | pump.fun |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| ROB | robinhood | Pons V1 (v3 pool) | 2026-07-05 19:16 | $102k | $48k |  |  |  |  | 5 | 1 | $3.0M ($3.0M) | 3.9d | 0% |
| ROBINHOOD | robinhood | Pons V1 (v3 pool) | 2026-06-19 14:15 | $82k | $33k |  |  |  |  | 5 | 10 | $514k ($254k) | 22.0d | 70% |
| ROCK | robinhood | robinhood/other | 2026-08-31 21:35 | $177k | $106k | 760 |  |  |  | 5 | 2 | $289k ($250k) | 8m | 100% |
| RUBY | robinhood | robinhood/other | 2026-08-08 04:54 | $6k | $5k |  |  |  |  | 5 | 1 | $313k ($313k) | 42m | 100% |
| RWOG | robinhood | Pons (WETH pool) | 2026-07-22 16:02 | $27k | $16k |  |  |  |  | 5 | 0 |  () |  |  |
| Ram | solana | pump.fun | 2026-01-28 08:29 | $140k | $37k |  |  |  |  | 5 | 0 |  () |  |  |
| SANDIH | robinhood | robinhood/other | 2026-08-31 23:08 | $106k | $92k |  |  |  |  | 5 | 3 | $93k ($45k) | 7m | 100% |
| SHARE | robinhood | robinhood/other | 2026-08-14 01:13 | $5k | $6k |  |  |  |  | 5 | 1 | $125k ($125k) | 15.0h | 100% |
| SHORT | robinhood | robinhood/other |  | $24k | $11k |  |  |  |  | 5 | 1 | $77k ($77k) |  | 100% |
| SKHY | robinhood | robinhood/other | 2026-07-13 15:07 | $732k | $224k |  |  |  |  | 5 | 0 |  () |  |  |
| SMOOVIE | robinhood | robinhood/other | 2026-08-17 22:20 | $216k | $67k |  |  |  | 0x1aa7…9ed9 (1) | 5 | 1 | $297k ($297k) | 9.1d | 100% |
| SOLANGELES | solana | pump.fun | 2026-05-21 21:02 | $827k | $130k |  |  |  |  | 5 | 47 | $1.7M ($398k) | 5.7d | 21% |
| SPACETIME | robinhood | Pons V1 (v3 pool) | 2026-08-30 16:37 | $230k | $1.5M |  |  |  | 0x0095…c115 (1) | 5 | 4 | $314k ($81k) | -1268m | 100% |
| SPYon | bsc | bsc/other | 2025-12-22 13:48 | $3.5M | $874 |  |  |  |  | 5 | 0 |  () |  |  |
| STARTUP | robinhood | robinhood/other |  | $67k | $18k |  |  |  | 0x9ace…d51b (2) | 5 | 4 | $794k ($277k) |  | 100% |
| STONKS | solana | solana/other |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| STRIKE | robinhood | robinhood/other | 2026-09-01 20:34 | $14k | $10k |  |  |  |  | 5 | 2 | $779k ($706k) | 4.1h | 100% |
| Sisyphus | solana | pump.fun |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| TCG | solana | pump.fun |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| TRUMP2028 | solana | pump.fun |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| UFG | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 21:44 | $1.9M | $128k |  |  |  |  | 5 | 4 | $1.2M ($559k) | 6.3h | 50% |
| UNICORN | robinhood | LONG (stock-paired) | 2026-09-03 03:08 | $530k | $84k |  |  |  | 0x45af…eb7b (1) | 5 | 13 | $2.1M ($1.9M) | 2.0h | 0% |
| USO | robinhood | robinhood/other |  | $1.5M | $527k |  |  |  |  | 5 | 0 |  () |  |  |
| VEGGIES | robinhood | Pons V2 (v4 hook curve) | 2026-08-26 16:47 | $53k | $24k |  |  |  |  | 5 | 1 | $257k ($257k) | 1.5d | 100% |
| VOXEL | robinhood | Pons V2 (v4 hook curve) | 2026-09-01 17:44 | $3.3M | $170k |  |  |  |  | 5 | 19 | $3.9M ($157k) | 1.6d | 11% |
| WLAI | robinhood | Pons V2 (v4 hook curve) | 2026-08-27 16:58 | $1.5M | $193k |  |  |  |  | 5 | 0 |  () |  |  |
| WOJAK | solana | pump.fun | 2025-11-03 20:41 | $1.7M | $311k |  |  |  |  | 5 | 59 | $10.2M ($2.8M) | 1.5d | 0% |
| WORTHLESS | robinhood | Pons V1 (v3 pool) | 2026-07-23 19:37 | $2.4M | $158k |  |  |  | 0x6454…c9f6 (1) | 5 | 13 | $1.9M ($528k) | 32.2d | 15% |
| WindChill | solana | pump.fun |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| XOM | robinhood | robinhood/other | 2026-07-02 01:24 | $111k | $31k |  |  |  |  | 5 | 0 |  () |  |  |
| XST | solana | solana/other |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| ZERO | solana | pump.fun |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| ZOE | robinhood | robinhood/other |  | $26k | $12k |  |  |  |  | 5 | 4 | $93k ($30k) |  | 100% |
| aoc | solana | solana/other |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| betANSEM | robinhood | Pons V1 (v3 pool) | 2026-07-22 23:41 | $3k | $3k |  |  |  | 0x7d22…4e66 (25) | 5 | 0 |  () |  |  |
| gubby | robinhood | robinhood/other | 2026-09-01 16:04 | $40k | $39k |  |  |  |  | 5 | 4 | $124k ($57k) | 4m | 100% |
| honse | solana | pump.fun |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| lickingcat | solana | pump.fun |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| sushicat | robinhood | Pons (WETH pool) | 2026-08-11 11:43 | $411k | $142k |  |  |  | 0x5793…13af (1) | 5 | 1 | $633k ($633k) | 1.6d | 100% |
| traindog | solana | pump.fun |  |  |  |  |  |  |  | 5 | 0 |  () |  |  |
| 十八bro | bsc | bsc/other | 2026-08-25 07:16 | $219k | $62k |  |  |  |  | 5 | 6 | $858k ($528k) | 2.7h | 67% |
| 淘公仔 | bsc | bsc/other |  | $77k | $29k |  |  |  |  | 5 | 5 | $219k ($26k) |  | 100% |
| 猴子币 | bsc | bsc/other | 2026-08-15 16:11 | $17k | $15k |  |  |  |  | 5 | 2 | $1.1M ($62k) | 7.1h | 50% |
| $GTS | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| $WIF | solana | solana/other | 2024-05-18 20:45 | $217.1M | $152k |  |  |  |  | 4 | 0 |  () |  |  |
| 401K | robinhood | Pons V2 (v4 hook curve) | 2026-08-27 11:04 | $220k | $39k |  |  |  |  | 4 | 2 | $274k ($208k) | 3.1d | 100% |
| 401k | robinhood | Pons (WETH pool) | 2026-07-09 13:20 | $31k | $28k |  |  |  |  | 4 | 1 | $375k ($375k) | 4.9h | 100% |
| 69 | robinhood | robinhood/other | 2026-08-30 09:53 | $121k | $28k |  |  |  |  | 4 | 1 | $186k ($186k) | 3.7d | 100% |
| APEONIFONE | robinhood | LONG (stock-paired) | 2026-09-01 23:38 | $24k | $73k |  |  |  |  | 4 | 3 | $88k ($38k) | 5m | 100% |
| ASTEROID | base | base/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| AUM0 | robinhood | robinhood/other | 2026-08-31 07:57 | $212k | $44k |  |  |  |  | 4 | 2 | $143k ($137k) | 9.5h | 100% |
| App | solana | solana/other | 2026-08-11 19:29 | $267k | $72k |  |  |  |  | 4 | 10 | $710k ($59k) | 13m | 100% |
| Axelus | robinhood | Pons V1 (v3 pool) | 2026-07-20 19:15 | $4k | $4k |  |  |  | 0x6ab0…10ee (1) | 4 | 0 |  () |  |  |
| BBL | robinhood | robinhood/other |  | $29k | $16k |  |  |  |  | 4 | 3 | $171k ($169k) |  | 100% |
| BEARER | evm? | evm?/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| BERRY | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 08:05 | $16k | $12k |  |  |  |  | 4 | 0 |  () |  |  |
| BLOKKS | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 22:51 | $507k | $66k |  |  |  |  | 4 | 3 | $497k ($251k) | 3m | 100% |
| BOBA | robinhood | Pons (WETH pool) | 2026-07-09 17:19 | $9k | $8k |  |  |  | 0x5b6a…5e67 (1) | 4 | 1 | $190k ($190k) | 4.5h | 100% |
| BOT | solana | solana/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| CACKLE | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| CATAMINE | robinhood | Pons V2 (v4 hook curve) | 2026-09-03 18:37 | $546k | $68k |  |  |  |  | 4 | 4 | $434k ($248k) | 2m | 75% |
| CATJAK | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| CLOCKIN | robinhood | robinhood/other | 2026-08-13 22:48 | $375 | $143 |  |  |  |  | 4 | 4 | $1.1M ($1.1M) | -1m | 0% |
| CNPY | robinhood | Pons (WETH pool) | 2026-07-11 17:25 | $1.5M | $179k |  |  |  |  | 4 | 0 |  () |  |  |
| COPPERINU | robinhood | Pons V2 (v4 hook curve) | 2026-07-22 06:08 | $73k | $59k |  |  |  |  | 4 | 0 |  () |  |  |
| CORGI | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| CRASHIUS | solana | solana/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| CRIME | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| CRYPTO | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| CUTE | robinhood | Pons V2 (v4 hook curve) | 2026-09-03 18:13 | $41k | $16k |  |  |  |  | 4 | 4 | $277k ($93k) | 5m | 100% |
| DEGS | solana | solana/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| DIDDY | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 20:08 | $303k | $69k |  |  |  | 0xb1a6…7f98 (1) | 4 | 4 | $176k ($63k) | 1.0d | 100% |
| DOLORES | robinhood | robinhood/other | 2026-08-26 02:48 | $57k | $524k |  |  |  |  | 4 | 1 | $750k ($750k) | 10m | 100% |
| DOUGH | robinhood | robinhood/other | 2026-09-03 04:55 | $421k | $54k |  |  |  |  | 4 | 5 | $511k ($143k) | 6.5h | 100% |
| Doom | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| ELON | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| ELONOMIST | evm? | evm?/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| FGL | robinhood | robinhood/other | 2026-09-01 09:01 | $7k | $15k |  |  |  |  | 4 | 3 | $2.0M ($147k) | 29m | 33% |
| FLETCHER | robinhood | robinhood/other | 2026-07-11 14:24 | $293k | $86k |  |  |  |  | 4 | 2 | $326k ($300k) | 47.1d | 100% |
| FLOCK | robinhood | robinhood/other |  | $53k | $19k |  |  |  |  | 4 | 4 | $121k ($17k) |  | 100% |
| FLOOR | robinhood | Pons (WETH pool) | 2026-07-03 01:34 | $2k | $6 |  |  |  |  | 4 | 1 | $2.0M ($2.0M) | 6.8d | 0% |
| FLYWHEEL | robinhood | robinhood/other |  | $424k | $162k |  |  |  |  | 4 | 3 | $495k ($364k) |  | 100% |
| FOMO | solana | solana/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| FRANK | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| FRIEND | base | base/other | 2024-05-03 05:34 | $625k | $149k |  |  |  |  | 4 | 2 | $7.0M ($5.7M) | 846.0d | 0% |
| FRIES | solana | solana/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| FRIES | solana | solana/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| FTM | evm? | evm?/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| GAMESTONK | robinhood | Pons V1 (v3 pool) | 2026-08-24 15:18 | $226k | $29k |  |  |  |  | 4 | 2 | $466k ($409k) | 7.8d | 100% |
| GB | robinhood | robinhood/other |  | $461k | $96k |  |  |  |  | 4 | 3 | $560k ($506k) |  | 100% |
| GLIZZY | robinhood | Pons V2 (v4 hook curve) | 2026-08-27 23:34 | $44k | $17k |  |  |  |  | 4 | 3 | $97k ($37k) | 1.2h | 100% |
| GOOGLc | base | base/other | 2026-08-13 13:03 | $2.2M | $1.3M |  |  |  |  | 4 | 0 |  () |  |  |
| GPRO | robinhood | robinhood/other | 2026-08-31 18:55 | $17k | $9k |  |  |  |  | 4 | 2 | $1.1M ($874k) | 5m | 50% |
| GTA | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| GWOOD | robinhood | Pons (WETH pool) | 2026-07-20 23:45 | $5.2M | $219k |  |  |  |  | 4 | 2 | $4.3M ($2.6M) | 1.8d | 0% |
| Geeg | solana | solana/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| HALF | robinhood | robinhood/other | 2026-08-30 00:20 | $3k | $5k |  |  |  |  | 4 | 2 | $324k ($275k) | 46m | 100% |
| HARMONIC | robinhood | Pons V2 (v4 hook curve) | 2026-08-29 05:25 | $707k | $82k |  |  |  |  | 4 | 7 | $711k ($542k) | 3.6d | 100% |
| HAVEN | robinhood | robinhood/other | 2026-08-24 20:33 | $24k | $14k |  |  |  |  | 4 | 1 | $169k ($169k) | 5.8h | 100% |
| HAWK | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 15:41 | $12k | $8k |  |  |  |  | 4 | 2 | $104k ($19k) | 1.7h | 100% |
| HIGHER | robinhood | robinhood/other |  | $17k | $11k |  |  |  |  | 4 | 2 | $213k ($23k) |  | 100% |
| HOMER | bsc | bsc/other | 2026-08-25 15:02 | $309k | $63k |  |  |  |  | 4 | 3 | $593k ($464k) | 1.8d | 100% |
| Hamster  | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| INVEST | robinhood | Pons (WETH pool) | 2026-08-26 18:31 | $1.0M | $73k |  |  |  |  | 4 | 1 | $7.2M ($7.2M) | 22m | 0% |
| IOO | robinhood | robinhood/other | 2026-09-02 12:22 | $9k | $9k |  |  |  |  | 4 | 4 | $591k ($310k) | 7m | 100% |
| Inu | robinhood | robinhood/other | 2026-09-04 01:04 | $3.1M | $130k |  |  |  |  | 4 | 0 |  () |  |  |
| JACKET | robinhood | LONG (stock-paired) | 2026-07-14 18:39 | $177k | $166k |  |  |  |  | 4 | 1 | $151k ($151k) | 44.7d | 100% |
| KAO | robinhood | robinhood/other | 2026-08-14 01:16 | $9k | $13k |  |  |  |  | 4 | 1 | $174k ($174k) | 1.9d | 100% |
| KINGPINS | eth | eth/other | 2026-08-13 20:12 | $270 | $4 |  |  |  |  | 4 | 4 | $317k ($203k) | -19m | 100% |
| KIRKLAND | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 23:36 | $284k | $43k |  |  |  |  | 4 | 4 | $532k ($192k) | 5m | 100% |
| KYOKO | solana | solana/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| LARP | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| LIBTARD | robinhood | robinhood/other |  | $60k | $83k |  |  |  |  | 4 | 3 | $103k ($56k) |  | 100% |
| LIGHTNINGCAT | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 00:37 | $67k | $24k |  |  |  | 0x8f5e…7365 (1) | 4 | 0 |  () |  |  |
| LNKS | robinhood | robinhood/other | 2026-09-02 15:23 | $4k | $6k |  |  |  |  | 4 | 3 | $183k ($150k) | 11m | 100% |
| LOG | robinhood | robinhood/other | 2026-08-25 15:05 | $6k | $7k |  |  |  |  | 4 | 1 | $262k ($262k) | 17m | 100% |
| LOONG | bsc | bsc/other | 2026-09-02 12:41 | $102k | $32k |  |  |  |  | 4 | 4 | $397k ($195k) | 15m | 100% |
| LUCIA | robinhood | robinhood/other | 2026-09-01 15:45 | $6k | $9k |  |  |  |  | 4 | 2 | $462k ($354k) | 52m | 100% |
| Launch | robinhood | robinhood/other | 2026-07-12 10:40 | $157k | $30k |  |  |  |  | 4 | 2 | $430k ($381k) | 52.9d | 100% |
| Lucia | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| MANY | robinhood | Pons V2 (v4 hook curve) | 2026-09-01 11:40 | $486k | $65k | 1559 |  |  |  | 4 | 4 | $1.1M ($152k) | 2.2h | 25% |
| MARIAN | robinhood | Pons V1 (v3 pool) | 2026-06-15 15:00 | $1.4M | $206k |  |  |  | 0x9379…2d5c (1) | 4 | 6 | $4.9M ($1.4M) | 29.3d | 0% |
| MIM | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| MONEROCHAN | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| NAVEN | robinhood | Pons (WETH pool) | 2026-07-10 13:33 | $594k | $96k |  |  |  |  | 4 | 2 | $542k ($457k) | 8.7d | 100% |
| NORMIE | solana | pump.fun | 2026-07-02 12:49 | $2.4M | $157k |  |  |  |  | 4 | 3 | $16.9M ($15.6M) | 20.5d | 0% |
| NVM | robinhood | robinhood/other | 2026-08-29 00:48 | $11k | $69k |  |  |  | 0x310e…19c9 (1) | 4 | 1 | $649k ($649k) | 1.3d | 100% |
| OCEAN | bsc | bsc/other | 2026-07-08 14:29 | $617k | $62k |  |  |  |  | 4 | 0 |  () |  |  |
| OTTR | robinhood | Pons V1 (v3 pool) | 2026-07-22 13:18 | $3k | $4k |  |  |  | 0x8e65…a882 (14) | 4 | 0 |  () |  |  |
| OUROBOROS | robinhood | robinhood/other | 2026-09-01 21:52 | $790k | $93k |  |  |  |  | 4 | 35 | $914k ($543k) | 7.1h | 74% |
| OpenCodeJr | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| PANTS | solana | solana/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| PDEX | robinhood | robinhood/other | 2026-08-28 16:10 | $12k | $8k |  |  |  |  | 4 | 2 | $1.9M ($1.6M) | 20.6h | 0% |
| PEPTIDES | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 08:33 | $5.9M | $738k |  |  |  |  | 4 | 12 | $1.2M ($457k) | 49m | 25% |
| PIG | robinhood | Pons V2 (v4 hook curve) | 2026-09-01 23:10 | $34k | $15k |  |  |  |  | 4 | 4 | $333k ($112k) | 4m | 100% |
| PLTRX | solana | solana/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| PONSGUY | robinhood | robinhood/other | 2026-08-29 22:33 | $88k | $27k |  |  |  |  | 4 | 0 |  () |  |  |
| Pixel Cat | robinhood | robinhood/other | 2026-09-03 15:18 | $30k | $13k |  |  |  |  | 4 | 3 | $996k ($745k) | 5m | 67% |
| QUANT | robinhood | LONG (stock-paired) | 2026-08-30 23:46 | $95k | $68k |  |  |  |  | 4 | 3 | $2.4M ($1.1M) | 3.8h | 0% |
| RADON | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| RATRACE | robinhood | LONG (stock-paired) | 2026-08-29 21:13 | $32k | $36k |  |  |  | 0x72bd…5395 (1) | 4 | 1 | $385k ($385k) | 37m | 100% |
| RETARD | solana | pump.fun | 2026-06-01 23:27 | $167k | $43k |  |  |  |  | 4 | 13 | $545k ($448k) | 33.8d | 85% |
| RIALTOES | robinhood | Pons (WETH pool) | 2026-07-27 15:22 | $89k | $91k |  |  |  |  | 4 | 1 | $1.4M ($1.4M) | 26m | 0% |
| RISK | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| ROBUX | robinhood | robinhood/other | 2026-08-19 22:25 | $97k | $107k |  |  |  |  | 4 | 2 | $127k ($77k) | 13.7d | 100% |
| ROCKET | robinhood | robinhood/other |  | $3k | $5k |  |  |  |  | 4 | 3 | $173k ($142k) |  | 100% |
| RWI | robinhood | Pons V1 (v3 pool) | 2026-07-18 16:29 | $13k | $11k |  |  |  |  | 4 | 2 | $101k ($96k) | 9.5d | 100% |
| SEND | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 16:04 | $73k | $30k |  |  |  |  | 4 | 5 | $218k ($145k) | 1.1h | 100% |
| SHERWOOD | robinhood | robinhood/other | 2026-08-10 13:57 | $381k | $58k |  |  |  |  | 4 | 2 | $532k ($339k) | 15.0d | 100% |
| SIDELINED | evm? | evm?/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| SINGIT | base | base/other | 2026-06-08 20:08 | $269k | $151k |  |  |  |  | 4 | 3 | $951k ($512k) | 76.9d | 67% |
| SLATE | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 21:28 | $4k | $7k |  |  |  |  | 4 | 3 | $656k ($208k) | 7m | 100% |
| SNCK | robinhood | Pons (WETH pool) | 2026-07-09 20:24 | $32k | $19k |  |  |  |  | 4 | 1 | $155k ($155k) | 49.0d | 100% |
| SPARKY | robinhood | robinhood/other |  | $19k | $12k |  |  |  |  | 4 | 1 | $265k ($265k) |  | 100% |
| SQUIRE | solana | solana/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| STJUDE | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| STONKEX | base | base/other | 2026-08-24 15:19 | $2.1M | $191k |  |  |  |  | 4 | 4 | $1.7M ($377k) | 2.3h | 25% |
| STOOLPRESIDEN | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| STR | evm? | evm?/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| SUCC | robinhood | robinhood/other | 2026-08-27 17:47 | $132 | $336 |  |  |  |  | 4 | 1 | $310k ($310k) | 12m | 100% |
| SUMMER | bsc | bsc/other | 2026-08-05 12:04 | $590k | $104k |  |  |  |  | 4 | 5 | $2.0M ($530k) | 2.3d | 20% |
| SURFER | robinhood | LONG (stock-paired) | 2026-09-02 00:35 | $93k | $95k |  |  |  |  | 4 | 4 | $271k ($35k) | 21.0h | 100% |
| Stockcoin | robinhood | LONG (stock-paired) | 2026-07-24 15:30 | $16k | $18k |  |  |  |  | 4 | 1 | $451k ($451k) | 3.7h | 100% |
| TRUMP2028 | robinhood | Pons (WETH pool) | 2026-07-25 02:32 | $13k | $10k |  |  |  |  | 4 | 1 | $301k ($301k) | 21m | 100% |
| TUZKI | bsc | bsc/other | 2026-09-03 08:22 | $1.6M | $133k |  |  |  |  | 4 | 3 | $2.1M ($63k) | 1.4h | 33% |
| TUZKI | bsc | bsc/other | 2026-09-03 12:26 | $1 | $0 |  |  |  |  | 4 | 0 |  () |  |  |
| UBI | robinhood | robinhood/other | 2026-08-30 22:15 | $6k | $7k |  |  |  |  | 4 | 1 | $336k ($336k) | 6m | 100% |
| UMBRA | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 15:19 | $44k | $20k |  |  |  |  | 4 | 0 |  () |  |  |
| UNIPCS | robinhood | Pons (WETH pool) | 2026-07-09 19:03 | $9k | $8k |  |  |  |  | 4 | 3 | $10k ($10k) | 22.9h | 100% |
| VEGETA | robinhood | robinhood/other | 2026-09-03 13:05 | $33k | $17k |  |  |  |  | 4 | 0 |  () |  |  |
| VIBE | eth | eth/other | 2026-07-29 19:32 | $10.8M | $1.6M |  |  |  |  | 4 | 4 | $5.2M ($481k) | -1295m | 25% |
| WC | solana | solana/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| WIZARD | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| WOJAK | robinhood | Pons (WETH pool) | 2026-06-30 19:36 | $1.5M | $148k |  |  |  |  | 4 | 1 | $5.8M ($5.8M) | 42.2d | 0% |
| WORLD | robinhood | Pons V2 (v4 hook curve) | 2026-08-15 07:52 | $74k | $25k |  |  |  |  | 4 | 1 | $125k ($125k) | 16.1d | 100% |
| Wilbur | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| XCCXX | solana | solana/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| agostino | solana | solana/other |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| bid | robinhood | robinhood/other | 2026-09-01 01:20 | $4k | $6k |  |  |  |  | 4 | 2 | $213k ($199k) | 1.4h | 100% |
| claudius | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| fable | robinhood | robinhood/other | 2026-09-01 08:38 | $69k | $62k | 4051 |  |  |  | 4 | 4 | $1.2M ($722k) | 20m | 25% |
| gSPEED | base | base/other | 2026-05-27 23:19 | $959k | $127k |  |  |  |  | 4 | 0 |  () |  |  |
| gork | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| jailstool | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| naseem | robinhood | Pons V1 (v3 pool) | 2026-07-26 12:48 | $3k | $3k |  |  |  | 0x96bb…c27f (21) | 4 | 0 |  () |  |  |
| nuBTC | robinhood | LONG (stock-paired) | 2026-09-02 17:06 | $52k | $25k |  |  |  | 0xd55f…4f86 (1) | 4 | 4 | $263k ($215k) | 48m | 100% |
| pBTC | robinhood | robinhood/other | 2026-08-26 14:20 | $57k | $25k |  |  |  |  | 4 | 0 |  () |  |  |
| pBTC3x | robinhood | Pons V2 (v4 hook curve) | 2026-08-26 12:45 | $81k | $29k |  |  |  |  | 4 | 0 |  () |  |  |
| pHOOD3x | robinhood | robinhood/other | 2026-08-26 14:19 | $518k | $61k |  |  |  |  | 4 | 0 |  () |  |  |
| pepescobar | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| sami | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| son | robinhood | Pons V1 (v3 pool) | 2026-07-22 14:18 | $3k | $4k |  |  |  | 0x96bb…c27f (21) | 4 | 0 |  () |  |  |
| splashdog | solana | pump.fun |  |  |  |  |  |  |  | 4 | 0 |  () |  |  |
| tomochi | solana | solana/other | 2026-07-21 14:18 | $953k | $90k |  |  |  |  | 4 | 12 | $643k ($259k) | 5.9h | 75% |
| utopia | robinhood | Pons (WETH pool) | 2026-07-19 02:53 | $8k | $11k |  |  |  | 0xb192…b2d5 (1) | 4 | 1 | $276k ($276k) | 1.1d | 100% |
| 孙小圣 | bsc | bsc/other | 2026-08-29 03:37 | $729k | $116k |  |  |  |  | 4 | 4 | $2.0M ($192k) | 24m | 25% |
| 币有 | bsc | bsc/other | 2026-07-31 12:04 | $1.7M | $196k |  |  |  |  | 4 | 3 | $10.2M ($1.9M) | 3.6d | 0% |
| 牛屎 | bsc | bsc/other |  | $96k | $41k |  |  |  |  | 4 | 4 | $368k ($268k) |  | 100% |
| 邵逸夫币 | bsc | bsc/other | 2026-08-22 15:18 | $20k | $17k |  |  |  |  | 4 | 4 | $349k ($241k) | 1.1h | 100% |
| $1 | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 11:00 | $1.4M | $100k |  |  |  |  | 3 | 3 | $1.7M ($1.5M) | 42m | 0% |
| $AHHH | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| 1000000000 | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| 530A | robinhood | Pons V1 (v3 pool) | 2026-07-06 14:43 | $39k | $22k |  |  |  |  | 3 | 0 |  () |  |  |
| : - ) | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| ACRE | robinhood | robinhood/other | 2026-08-28 17:44 | $6k | $5k |  |  |  |  | 3 | 1 | $190k ($190k) | 22.2h | 100% |
| AERO | base | base/other | 2023-09-07 22:50 | $1.0B | $29.7M |  |  |  |  | 3 | 0 |  () |  |  |
| AGI | robinhood | robinhood/other | 2026-09-03 09:05 | $16k | $10k |  |  |  | 0xfddf…66cf (1) | 3 | 3 | $63k ($40k) | 54m | 100% |
| ANT | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| AOS | robinhood | robinhood/other | 2026-08-27 10:22 | $44k | $19k |  |  |  |  | 3 | 2 | $143k ($88k) | 3.6d | 100% |
| ARCADEHOUSE | robinhood | Pons V2 (v4 hook curve) | 2026-09-03 20:17 | $11k | $9k |  |  |  |  | 3 | 3 | $83k ($31k) | 4m | 100% |
| ARCADS | robinhood | robinhood/other | 2026-08-31 19:15 | $101k | $31k |  |  |  |  | 3 | 2 | $250k ($97k) | 14m | 100% |
| ARROW | robinhood | Pons (WETH pool) | 2026-07-10 00:22 | $8.7M | $4.7M |  |  |  |  | 3 | 0 |  () |  |  |
| ASTEROID | bsc | bsc/other | 2026-08-01 00:39 | $644k | $127k |  |  |  |  | 3 | 2 | $2.4M ($2.1M) | 11m | 0% |
| ATM | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| BANKLESS | robinhood | robinhood/other | 2026-08-31 16:07 | $104k | $31k |  |  |  |  | 3 | 1 | $330k ($330k) | 1.4h | 100% |
| BEAVER | robinhood | robinhood/other |  | $31k | $18k |  |  |  |  | 3 | 3 | $143k ($28k) |  | 100% |
| BEBEH | robinhood | Pons V1 (v3 pool) | 2026-07-15 09:38 | $14k | $11k |  |  |  |  | 3 | 1 | $33k ($33k) | 11.3d | 100% |
| BEDROCK | robinhood | robinhood/other | 2026-09-01 02:52 | $8k | $10k |  |  |  |  | 3 | 2 | $419k ($411k) | 29m | 100% |
| BELIEVE | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| BIAO | robinhood | LONG (stock-paired) | 2026-09-01 14:03 | $12k | $15k |  |  |  |  | 3 | 2 | $441k ($419k) | 1m | 100% |
| BLUEHOUSE | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| BOMBA | robinhood | LONG (stock-paired) | 2026-08-31 18:30 | $73k | $60k |  |  |  |  | 3 | 3 | $203k ($137k) | 23.5h | 100% |
| BRICKS | robinhood | Pons V2 (v4 hook curve) | 2026-08-28 19:33 | $371k | $57k |  |  |  |  | 3 | 3 | $391k ($349k) | 3.9d | 100% |
| BSTONK | base | base/other | 2026-08-17 01:06 | $1.6M | $115k |  |  |  |  | 3 | 2 | $2.0M ($1.3M) | 5.8d | 0% |
| BUCKAZOIDS | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 11:30 | $60k | $23k |  |  |  |  | 3 | 3 | $124k ($67k) | 4m | 100% |
| BUDDY | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| BUILD | robinhood | robinhood/other |  | $14k | $12k |  |  |  |  | 3 | 1 | $93k ($93k) |  | 100% |
| BUNKEE | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| BUWA | robinhood | robinhood/other | 2026-08-30 22:17 | $60k | $23k |  |  |  |  | 3 | 2 | $352k ($331k) | 18.5h | 100% |
| Bots | base | base/other | 2026-08-22 21:09 | $482k | $180k |  |  |  |  | 3 | 2 | $2.7M ($1.8M) | 5.6d | 0% |
| Butcher | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| CHANG | robinhood | robinhood/other |  | $293k | $152k |  |  |  |  | 3 | 3 | $190k ($106k) |  | 100% |
| CHIPS | robinhood | robinhood/other | 2026-08-15 22:23 | $718k | $717k |  |  |  |  | 3 | 3 | $33k ($29k) | 1.3h | 100% |
| CHOYI | bsc | bsc/other | 2026-09-02 02:32 | $42k | $21k |  |  |  |  | 3 | 3 | $511k ($109k) | 1.6d | 100% |
| CHUMP | robinhood | Pons V1 (v3 pool) | 2026-07-31 01:44 | $45.5M | $1.2M |  |  |  | 0x5bad…4b20 (1) | 3 | 1 | $19.7M ($19.7M) | 28.5d | 0% |
| COCO | robinhood | Pons (WETH pool) | 2026-07-15 05:11 | $20k | $14k |  |  |  |  | 3 | 1 | $93k ($93k) | 30.6d | 100% |
| CODEX | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| COMPANY | robinhood | robinhood/other | 2026-08-23 21:37 | $5k | $7k |  |  |  |  | 3 | 1 | $68k ($68k) | 11m | 100% |
| COUGH | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| CRCL | robinhood | robinhood/other | 2026-09-04 01:26 | $3.3M | $63k |  |  |  |  | 3 | 3 | $490k ($197k) | -3m | 100% |
| CRIBS | robinhood | robinhood/other | 2026-09-01 17:26 | $100k | $29k |  |  |  |  | 3 | 2 | $411k ($258k) | 48m | 100% |
| CULT | robinhood | robinhood/other | 2026-08-30 00:20 | $350k | $55k |  |  |  |  | 3 | 1 | $366k ($366k) | 4.5d | 100% |
| CUMMIES | robinhood | robinhood/other |  | $21k | $14k |  |  |  |  | 3 | 3 | $142k ($42k) |  | 100% |
| CUTE | robinhood | Pons (WETH pool) | 2026-07-20 18:52 | $22k | $14k |  |  |  |  | 3 | 2 | $104k ($45k) | 23.1d | 100% |
| Chiikawa | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| Chonketha | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| Cred | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| DAHOOD | robinhood | Pons V1 (v3 pool) | 2026-07-28 04:19 | $30k | $19k |  |  |  |  | 3 | 1 | $262k ($262k) | 5.0h | 100% |
| DAWG | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| DAWN | robinhood | LONG (stock-paired) | 2026-08-28 00:56 | $10k | $9k |  |  |  | 0x7d70…e05e (1) | 3 | 1 | $183k ($183k) | 12m | 100% |
| DELLICOPTER | robinhood | robinhood/other | 2026-09-01 22:42 | $51k | $36k |  |  |  |  | 3 | 2 | $48k ($36k) | 2m | 100% |
| DICE | robinhood | Pons V1 (v3 pool) | 2026-07-28 21:41 | $744k | $105k |  |  |  |  | 3 | 1 | $235k ($235k) | 8.4h | 100% |
| DICKBUTT | robinhood | Pons V2 (v4 hook curve) | 2026-08-25 15:09 | $52k | $22k |  |  |  |  | 3 | 3 | $154k ($138k) | 42m | 100% |
| DICKBUTT | bsc | bsc/other | 2026-07-31 00:35 | $141k | $51k |  |  |  |  | 3 | 4 | $173k ($88k) | 38m | 100% |
| DIH | robinhood | LONG (stock-paired) | 2026-09-03 03:08 | $362k | $49k |  |  |  |  | 3 | 3 | $424k ($419k) | 8m | 100% |
| DIP | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| DO | robinhood | robinhood/other |  | $33k | $18k |  |  |  |  | 3 | 2 | $68k ($34k) |  | 100% |
| DOGE | bsc | bsc/other | 2021-07-16 11:31 | $1.5M | $2.8M |  |  |  |  | 3 | 0 |  () |  |  |
| DONJR | robinhood | robinhood/other |  | $8k | $7k |  |  |  |  | 3 | 1 | $136k ($136k) |  | 100% |
| DRV | base | base/other | 2026-04-16 04:45 | $24.8M | $724k |  |  |  |  | 3 | 4 | $25.0M ($17.9M) | 127.1d | 0% |
| DTG | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| Dealer | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| Ducks | robinhood | robinhood/other |  | $7k | $7k |  |  |  |  | 3 | 1 | $55k ($55k) |  | 100% |
| ELO | robinhood | Pons V2 (v4 hook curve) | 2026-08-24 02:10 | $43k | $19k |  |  |  |  | 3 | 2 | $69k ($62k) | 5.6d | 100% |
| ETHICS | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| ElonRWA | base | base/other | 2024-03-20 20:32 | $1.8M | $623k |  |  |  |  | 3 | 3 | $7.6M ($5.5M) | 890.8d | 0% |
| Emilio | robinhood | Pons (WETH pool) | 2026-07-09 05:05 | $8k | $7k |  |  |  |  | 3 | 1 | $67k ($67k) | 16.1h | 100% |
| FOMO | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| FRENS | robinhood | Pons V2 (v4 hook curve) | 2026-08-29 17:41 | $13k | $11k |  |  |  |  | 3 | 1 | $486k ($486k) | 7.3h | 100% |
| FRUG | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| FTR | robinhood | LONG (stock-paired) | 2026-08-24 23:37 | $54k | $55k |  |  |  |  | 3 | 0 |  () |  |  |
| FWOG | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| Figure03 | robinhood | LONG (stock-paired) | 2026-09-03 13:10 | $140k | $33k |  |  |  |  | 3 | 3 | $158k ($128k) | 1.9h | 100% |
| FoMo | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| Fraggle | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| Froggie | bsc | bsc/other | 2026-08-27 17:35 | $668k | $100k |  |  |  |  | 3 | 3 | $688k ($200k) | 1.5h | 100% |
| GLDX | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| GOAT | evm? | evm?/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| GOOGLX | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| GOONER | robinhood | Pons V2 (v4 hook curve) | 2026-08-30 11:53 | $910k | $100k |  |  |  |  | 3 | 3 | $1.1M ($934k) | 2m | 33% |
| GOVC | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| GOYBEAM | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| GTAVI | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| GYM | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| HISS | robinhood | Pons V2 (v4 hook curve) | 2026-07-11 17:55 | $32k | $27k |  |  |  |  | 3 | 0 |  () |  |  |
| HM | robinhood | robinhood/other | 2026-08-29 18:38 | $211k | $106k |  |  |  |  | 3 | 3 | $415k ($333k) | 1.9d | 100% |
| HOODCAT | robinhood | Pons V2 (v4 hook curve) | 2026-09-03 05:58 | $33k | $18k |  |  |  |  | 3 | 2 | $185k ($69k) | 19m | 100% |
| HOODCAT | robinhood | robinhood/other | 2026-08-31 22:18 | $12k | $105k |  |  |  |  | 3 | 1 | $119k ($119k) | 1m | 100% |
| HOOTS | solana | pump.fun | 2026-08-26 15:18 | $85k | $25k |  |  |  |  | 3 | 5 | $62k ($7k) | -4m | 100% |
| HUGGY | robinhood | LONG (stock-paired) | 2026-08-28 02:03 | $285k | $144k |  |  |  |  | 3 | 1 | $385k ($385k) | 6.4d | 100% |
| HULK | robinhood | robinhood/other |  | $31k | $16k |  |  |  |  | 3 | 3 | $124k ($38k) |  | 100% |
| HeeHaw | solana | pump.fun | 2026-08-30 16:11 | $443k | $83k |  |  |  |  | 3 | 8 | $1.1M ($458k) | 3.1h | 50% |
| INNIT | evm? | evm?/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| INSIDERS | robinhood | robinhood/other | 2026-08-22 19:00 | $22k | $14k |  |  |  | 0xd87f…f374 (1) | 3 | 0 |  () |  |  |
| INTISMERAN | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| IPOD | base | base/other | 2026-08-27 13:47 | $204k | $112k |  |  |  |  | 3 | 3 | $257k ($210k) | 4.2d | 100% |
| ISO | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| JARVIS | robinhood | robinhood/other | 2026-09-02 09:49 | $52k | $47k |  |  |  |  | 3 | 1 | $64k ($64k) | 40m | 100% |
| Jotchua | solana | pump.fun | 2026-06-07 05:15 | $2.7M | $272k |  |  |  |  | 3 | 12 | $5.5M ($275k) | 1.5d | 17% |
| KIRKINATOR | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| KYNIX | robinhood | robinhood/other | 2026-08-31 12:44 | $3k | $8k |  |  |  |  | 3 | 1 | $182k ($182k) | 21m | 100% |
| LA | robinhood | robinhood/other | 2026-08-27 01:10 | $129k | $127k |  |  |  |  | 3 | 2 | $246k ($111k) | 1.7d | 100% |
| LIT | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| LMAO! | solana | pump.fun | 2025-10-18 03:00 | $2.4M | $268k |  |  |  |  | 3 | 0 |  () |  |  |
| LMEOW | robinhood | robinhood/other | 2026-08-31 18:14 | $193k | $39k |  |  |  |  | 3 | 1 | $547k ($547k) | 5.4h | 100% |
| LOGOS | robinhood | robinhood/other | 2026-08-09 01:53 | $1.2M | $133k |  |  |  |  | 3 | 1 | $1.5M ($1.5M) | 23.7d | 0% |
| Loopr | robinhood | robinhood/other | 2026-09-02 21:20 | $959k | $94k |  |  |  |  | 3 | 3 | $643k ($590k) | 4m | 100% |
| MACROHARD | robinhood | LONG (stock-paired) | 2026-09-02 06:10 | $48k | $25k |  |  |  |  | 3 | 0 |  () |  |  |
| MARKETPLIER | robinhood | robinhood/other | 2026-09-01 10:59 | $26k | $24k |  |  |  |  | 3 | 2 | $99k ($58k) | 3.2h | 100% |
| MARS | robinhood | LONG (stock-paired) | 2026-07-27 15:28 | $78k | $76k |  |  |  |  | 3 | 1 | $251k ($251k) | 14m | 100% |
| MERIT | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 16:13 | $13k | $11k |  |  |  |  | 3 | 1 | $475k ($475k) | 35m | 100% |
| MIM | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| MINI | solana | solana/other | 2026-09-03 20:54 | $514k | $80k |  |  |  |  | 3 | 7 | $1.1M ($779k) | 9m | 43% |
| MLG | robinhood | robinhood/other |  | $27k | $12k |  |  |  |  | 3 | 3 | $299k ($61k) |  | 100% |
| MOMO | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| MRNA | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| MSTRX | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| MUGSHOT | robinhood | robinhood/other | 2026-08-13 17:43 | $25k | $31k |  |  |  |  | 3 | 1 | $121k ($121k) | 2.5h | 100% |
| Miu | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| NEURALINK | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| NFTWIZ | base | base/other | 2026-03-05 14:35 | $170k | $32k |  |  |  |  | 3 | 0 |  () |  |  |
| NOBI VENTURES | robinhood | Pons (WETH pool) | 2026-07-15 06:24 | $26k | $16k |  |  |  |  | 3 | 0 |  () |  |  |
| NOCODE | solana | bags |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| NPC | robinhood | robinhood/other | 2026-08-28 12:13 | $34k | $18k |  |  |  |  | 3 | 1 | $111k ($111k) | 1.6h | 100% |
| NSTOCKS | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 20:58 | $45k | $24k |  |  |  |  | 3 | 0 |  () |  |  |
| NUMI | robinhood | robinhood/other | 2026-08-26 15:12 | $50k | $20k |  |  |  |  | 3 | 2 | $284k ($281k) | 3.9d | 100% |
| NVDAon | bsc | bsc/other |  | $16.8M | $2k |  |  |  |  | 3 | 0 |  () |  |  |
| Niles | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| Normie | robinhood | Pons (WETH pool) | 2026-07-23 20:34 | $4k | $5k |  |  |  |  | 3 | 1 | $179k ($179k) | 2.0h | 100% |
| OMOGGLE | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| OOB | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| Oilinu | robinhood | robinhood/other |  | $28k | $176k |  |  |  |  | 3 | 3 | $185k ($113k) |  | 100% |
| PAXG | eth | eth/other | 2025-10-22 13:31 | $1.9B | $6.1M |  |  |  |  | 3 | 0 |  () |  |  |
| PCAT | robinhood | Pons V1 (v3 pool) | 2026-07-20 03:28 | $85k | $31k |  |  |  | 0x5353…c549 (1) | 3 | 1 | $321k ($321k) | 35.3d | 100% |
| PEER | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 16:59 | $30k | $16k |  |  |  |  | 3 | 1 | $160k ($160k) | 1.8d | 100% |
| PENGU | robinhood | Pons V2 (v4 hook curve) | 2026-08-27 14:38 | $374k | $185k |  |  |  |  | 3 | 0 |  () |  |  |
| PFE | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 03:02 | $349k | $124k |  |  |  |  | 3 | 0 |  () |  |  |
| PICKLES | robinhood | Pons V2 (v4 hook curve) | 2026-08-31 23:57 | $1.2M | $103k |  |  |  |  | 3 | 3 | $540k ($455k) | 32m | 100% |
| PIRANHA | robinhood | robinhood/other | 2026-09-01 18:25 | $14k | $44k |  |  |  |  | 3 | 2 | $799k ($657k) | 9m | 100% |
| PLUMBER | robinhood | robinhood/other | 2026-08-30 06:35 | $29k | $16k |  |  |  |  | 3 | 1 | $119k ($119k) | 3.4d | 100% |
| POKE | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| POKEMON | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| POND | robinhood | Pons (WETH pool) | 2026-07-19 03:17 | $7k | $8k |  |  |  |  | 3 | 1 | $430k ($430k) | 1.5d | 100% |
| PONSFOLIO | robinhood | Pons V2 (v4 hook curve) | 2026-08-27 22:00 | $285k | $50k |  |  |  |  | 3 | 2 | $426k ($423k) | 2m | 100% |
| PONSION | robinhood | Pons V2 (v4 hook curve) | 2026-08-30 01:10 | $34k | $17k |  |  |  |  | 3 | 1 | $152k ($152k) | 3.8h | 100% |
| PONSTER | robinhood | robinhood/other | 2026-08-30 14:11 | $13k | $11k |  |  |  |  | 3 | 2 | $672k ($602k) | 41m | 100% |
| PUBERT | robinhood | Pons (WETH pool) | 2026-07-10 12:38 | $8k | $7k |  |  |  |  | 3 | 1 | $182k ($182k) | 3.0d | 100% |
| PVP | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| QNTX | solana | solana/other | 2026-08-25 22:32 | $6.4M | $202k |  |  |  |  | 3 | 0 |  () |  |  |
| RAXOL | robinhood | robinhood/other | 2026-07-02 12:21 | $1.8M | $319k |  |  |  |  | 3 | 24 | $3.7M ($2.9M) | 60.3d | 0% |
| RBLX | robinhood | robinhood/other | 2026-07-02 01:31 | $1.0M | $972k |  |  |  |  | 3 | 0 |  () |  |  |
| REACHY | robinhood | LONG (stock-paired) | 2026-08-27 13:16 | $100k | $28k |  |  |  |  | 3 | 2 | $343k ($316k) | 1.8d | 100% |
| REDDIT | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| RETA | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| RIPE | robinhood | LONG (stock-paired) | 2026-08-28 21:00 | $847k | $188k |  |  |  |  | 3 | 2 | $2.0M ($1.4M) | 3.7d | 0% |
| RIZO | robinhood | LONG (stock-paired) | 2026-08-30 15:53 | $13k | $11k |  |  |  | 0x9d5e…8c28 (1) | 3 | 2 | $109k ($30k) | 1.6d | 100% |
| RIZO | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| RIZZLER | robinhood | LONG (stock-paired) | 2026-09-02 18:21 | $21k | $14k |  |  |  |  | 3 | 2 | $306k ($284k) | 6m | 100% |
| ROBINCAT | robinhood | LONG (stock-paired) | 2026-08-31 22:32 | $29k | $19k |  |  |  |  | 3 | 1 | $314k ($314k) | 23.5h | 100% |
| ROBINHOODS | robinhood | Pons (WETH pool) | 2026-07-21 06:46 | $6k | $6k |  |  |  |  | 3 | 1 | $131k ($131k) | 5.5d | 100% |
| Ralph | solana | bags |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| SABL | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| SELLOR | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| SHELLY | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| SHIT | robinhood | robinhood/other |  | $69k | $23k |  |  |  |  | 3 | 1 | $194k ($194k) |  | 100% |
| SHR | robinhood | Pons (WETH pool) | 2026-06-29 10:11 | $107k | $35k |  |  |  |  | 3 | 1 | $145k ($145k) | 38.1d | 100% |
| SMK2 | robinhood | Pons (WETH pool) | 2026-07-09 22:54 | $683.3M | $254k |  |  |  |  | 3 | 3 | $2.2B ($971.4M) | 55.1d | 0% |
| SNOO | robinhood | robinhood/other |  | $8k | $8k |  |  |  |  | 3 | 1 | $31k ($31k) |  | 100% |
| SOCK | robinhood | robinhood/other | 2026-09-03 21:09 | $91k | $88k |  |  |  |  | 3 | 3 | $542k ($230k) | 12m | 100% |
| STAIR | eth | eth/other |  |  |  |  |  |  |  | 3 | 3 | $52k ($51k) |  | 100% |
| STAR | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| STATICS | robinhood | Pons (WETH pool) | 2026-08-27 19:24 | $19.8M | $13.1M |  |  |  |  | 3 | 2 | $37.0M ($36.3M) | 3.0d | 0% |
| STOCKERS | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| STONKS | robinhood | robinhood/other |  | $1.2M | $91k |  |  |  |  | 3 | 3 | $2.1M ($891k) |  | 33% |
| Stokki | robinhood | robinhood/other | 2026-08-13 23:17 | $3k | $5k |  |  |  | 0xf9d0…73a4 (1) | 3 | 1 | $186k ($186k) | 54m | 100% |
| Strawberita | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| Surplus | base | base/other | 2026-05-16 15:20 | $4.1M | $1.7M |  |  |  |  | 3 | 4 | $5.2M ($4.8M) | 11.2d | 0% |
| TACO | robinhood | Pons (WETH pool) | 2026-07-13 23:31 | $26k | $15k |  |  |  |  | 3 | 0 |  () |  |  |
| TAM | robinhood | robinhood/other | 2026-09-03 22:13 | $705k | $219k |  |  |  |  | 3 | 3 | $584k ($268k) | 2m | 67% |
| TAM | robinhood | Pons V1 (v3 pool) | 2026-08-30 22:40 | $146k | $63k |  |  |  |  | 3 | 1 | $91k ($91k) | 3.9d | 100% |
| TAOBAO | robinhood | LONG (stock-paired) | 2026-09-03 05:08 | $44k | $23k |  |  |  |  | 3 | 3 | $375k ($44k) | 1.9h | 100% |
| TEST | robinhood | Pons V1 (v3 pool) | 2026-07-13 11:12 | $168k | $49k |  |  |  |  | 3 | 0 |  () |  |  |
| TESTIBULL | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| THINK | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| TICKER | robinhood | robinhood/other | 2026-09-01 13:42 | $4k | $6k |  |  |  |  | 3 | 1 | $132k ($132k) | 27m | 100% |
| TIE | robinhood | robinhood/other | 2026-08-30 09:01 | $96k | $17k |  |  |  |  | 3 | 1 | $52k ($52k) | 1.7d | 100% |
| TOGI | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| TRENCH | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| TROLL | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| TWT | bsc | bsc/other | 2023-08-13 14:03 | $578.7M | $604k |  |  |  |  | 3 | 0 |  () |  |  |
| URANUS | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| USDUC | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| V4 | base | base/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| VIAGRA | robinhood | Pons V2 (v4 hook curve) | 2026-09-03 00:03 | $269k | $48k |  |  |  |  | 3 | 3 | $412k ($254k) | 16.5h | 100% |
| VIBE CAT | robinhood | Pons (WETH pool) | 2026-07-08 02:33 | $512k | $87k |  |  |  |  | 3 | 9 | $2.1M ($173k) | 1.7d | 22% |
| WIBWOB | robinhood | Pons V1 (v3 pool) | 2026-07-25 04:03 | $4k | $4k |  |  |  | 0xcfa6…43c5 (1) | 3 | 0 |  () |  |  |
| Yee | ethereum | ethereum/other | 2023-04-28 10:55 | $3.6M | $454k |  |  |  |  | 3 | 0 |  () |  |  |
| bcat | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| cheesebank | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| chrome | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| chudhouse | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| delusional  | robinhood | robinhood/other | 2026-09-02 20:38 | $21k | $15k |  |  |  |  | 3 | 3 | $191k ($187k) | 6m | 100% |
| glorp | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| nice | robinhood | Pons (WETH pool) | 2026-07-20 00:39 | $5k | $5k |  |  |  |  | 3 | 1 | $82k ($82k) | 34m | 100% |
| oora | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| people | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 01:34 | $158k | $38k |  |  |  |  | 3 | 1 | $635k ($635k) | 43m | 100% |
| pussy | evm? | evm?/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| rehanfal | solana | solana/other |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| sami | base | base/other | 2026-08-11 06:15 | $83k | $90k |  |  |  |  | 3 | 3 | $967k ($107k) | 1.5h | 67% |
| testicle | solana | pump.fun | 2025-12-21 11:52 | $688k | $222k |  |  |  |  | 3 | 81 | $9.9M ($567k) | 9.9h | 1% |
| urmom | robinhood | LONG (stock-paired) | 2026-09-01 06:38 | $612k | $74k |  |  |  |  | 3 | 1 | $154k ($154k) | 1.4d | 100% |
| utility | bsc | bsc/other | 2026-08-12 12:55 | $141.3M | $17.7M |  |  |  |  | 3 | 3 | $2.8M ($1.3M) | 19m | 0% |
| website | robinhood | Pons V1 (v3 pool) | 2026-08-03 18:43 | $4.3M | $258k |  |  |  | 0xc73c…5094 (1) | 3 | 1 | $1.5M ($1.5M) | 28.6d | 0% |
| zazu | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| 哈基米 | bsc | bsc/other | 2025-10-07 23:09 | $19.3M | $1.5M |  |  |  |  | 3 | 3 | $15.9M ($15.5M) | 319.8d | 0% |
| 犇 | bsc | bsc/other | 2026-09-02 12:34 | $180k | $44k |  |  |  |  | 3 | 4 | $196k ($153k) | 50m | 100% |
| 🦁  | solana | pump.fun |  |  |  |  |  |  |  | 3 | 0 |  () |  |  |
| $WIFH | robinhood | Pons V1 (v3 pool) | 2026-07-10 12:05 | $105k | $37k |  |  |  |  | 2 | 0 |  () |  |  |
| (3,3) | robinhood | Pons (WETH pool) | 2026-08-10 22:33 | $17k | $13k |  |  |  |  | 2 | 2 | $40k ($18k) | 20.5d | 100% |
| 1% | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| 1000X | base | base/other | 2024-12-13 02:31 | $2.4M | $287k |  |  |  |  | 2 | 2 | $2.1M ($1.5M) | 620.6d | 0% |
| 129303 | robinhood | LONG (stock-paired) | 2026-09-03 12:12 | $48k | $20k |  |  |  |  | 2 | 2 | $325k ($238k) | 1.3h | 100% |
| 1F916 | base | base/other | 2026-08-06 06:52 | $731k | $303k |  |  |  |  | 2 | 2 | $842k ($595k) | 16.8h | 50% |
| 530A | robinhood | Pons (WETH pool) | 2026-07-06 08:12 | $16k | $6k |  |  |  |  | 2 | 1 | $359k ($359k) | 5.4d | 100% |
| 530A | robinhood | robinhood/other |  | $16k | $11k |  |  |  |  | 2 | 2 | $71k ($27k) |  | 100% |
| 911 | robinhood | LONG (stock-paired) | 2026-09-01 05:32 | $246k | $63k |  |  |  |  | 2 | 2 | $339k ($303k) | 1.0d | 100% |
| A | robinhood | robinhood/other |  | $11k | $10k |  |  |  |  | 2 | 1 | $70k ($70k) |  | 100% |
| AAPLDOG | robinhood | LONG (stock-paired) | 2026-09-01 22:37 | $82k | $120k |  |  |  | 0xdf86…b57a (1) | 2 | 0 |  () |  |  |
| ABE | robinhood | robinhood/other | 2026-07-30 17:14 | $102k | $36k |  |  |  |  | 2 | 1 | $59k ($59k) | 33.6d | 100% |
| AGENTHQ | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| AI | robinhood | robinhood/other |  | $12k | $10k |  |  |  |  | 2 | 1 | $128k ($128k) |  | 100% |
| ALZHEIMERS | robinhood | robinhood/other | 2026-09-03 16:25 | $336k | $146k |  |  |  |  | 2 | 2 | $461k ($460k) | 17m | 100% |
| ANONCOIN | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| ANT | robinhood | robinhood/other | 2026-09-02 05:01 | $7k | $7k |  |  |  |  | 2 | 0 |  () |  |  |
| ANTSEM | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| AOC | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| AP | evm? | evm?/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| APES | robinhood | Pons (WETH pool) | 2026-07-23 17:08 | $32k | $18k |  |  |  |  | 2 | 1 | $1.8M ($1.8M) | 8.4d | 0% |
| APIMart | robinhood | robinhood/other |  | $210k | $0 |  |  |  |  | 2 | 2 | $499.7M ($46k) |  | 50% |
| APU | robinhood | Pons V2 (v4 hook curve) | 2026-09-01 23:52 | $326k | $145k |  |  |  |  | 2 | 2 | $555k ($472k) | 18.3h | 100% |
| APU | robinhood | Pons (WETH pool) | 2026-07-08 07:37 | $19k | $13k |  |  |  |  | 2 | 1 | $48k ($48k) | 34.7d | 100% |
| ARMIC | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| AST | bsc | bsc/other | 2026-08-28 14:53 | $583k | $95k |  |  |  |  | 2 | 2 | $2.0M ($1.4M) | 3.9d | 0% |
| ASTRAYA | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| AURN | robinhood | robinhood/other | 2026-08-29 10:08 | $66k | $24k |  |  |  | 0x17e4…a487 (1) | 2 | 1 | $140k ($140k) | 7.2h | 100% |
| Adrien | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Apple Juice | base | base/other | 2026-08-20 16:24 | $96k | $36k |  |  |  |  | 2 | 2 | $309k ($288k) | 2.6d | 100% |
| Ash | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| BA | robinhood | robinhood/other | 2026-09-02 13:38 | $179k | $48k |  |  |  |  | 2 | 0 |  () |  |  |
| BABYPONS | robinhood | Pons V2 (v4 hook curve) | 2026-08-29 10:46 | $63k | $24k |  |  |  |  | 2 | 1 | $81k ($81k) | 5.6d | 100% |
| BASEJUICE | base | base/other | 2026-08-15 18:43 | $965k | $142k |  |  |  |  | 2 | 2 | $678k ($128k) | 1.4d | 50% |
| BASEMENT | robinhood | Pons V2 (v4 hook curve) | 2026-08-28 13:19 | $74k | $59k |  |  |  |  | 2 | 1 | $128k ($128k) | 60m | 100% |
| BELKA | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| BISCOTTI | robinhood | robinhood/other | 2026-08-24 20:34 | $6k | $7k |  |  |  | 0xe565…ea47 (1) | 2 | 1 | $610k ($610k) | 17m | 100% |
| BITAGENTS | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| BITCAT | robinhood | robinhood/other | 2026-08-29 17:27 | $12k | $10k |  |  |  |  | 2 | 1 | $165k ($165k) | 14m | 100% |
| BNDRYL | robinhood | robinhood/other | 2026-08-06 01:19 | $24k | $46k |  |  |  | 0x7fc1…6831 (1) | 2 | 1 | $151k ($151k) | 1.6h | 100% |
| BOBO | robinhood | robinhood/other | 2026-08-31 23:11 | $38k | $25k |  |  |  |  | 2 | 1 | $123k ($123k) | 13.7h | 100% |
| BOE | robinhood | Pons (WETH pool) | 2026-07-10 18:41 | $5k | $5k |  |  |  |  | 2 | 1 | $81k ($81k) | 20.2h | 100% |
| BONK | solana | solana/other | 2022-12-25 15:00 | $283.1M | $218k |  |  |  |  | 2 | 0 |  () |  |  |
| BOOZEBAG | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| BOT | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| BOYZ | robinhood | Pons (WETH pool) | 2026-07-24 23:55 | $70k | $38k |  |  |  |  | 2 | 1 | $4.5M ($4.5M) | 15.0d | 0% |
| BUFFCAT | robinhood | Pons V1 (v3 pool) | 2026-07-01 20:11 | $52k | $26k |  |  |  |  | 2 | 0 |  () |  |  |
| BULL | robinhood | robinhood/other | 2026-09-02 20:34 | $156k | $46k |  |  |  |  | 2 | 2 | $388k ($343k) | 40m | 100% |
| BURGER | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| BUSINESS | solana | bags |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Ban | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Blobby | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Bulltardio | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Burpcoin | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| CATE | bsc | bsc/other | 2026-08-02 04:09 | $6k | $9k |  |  |  |  | 2 | 2 | $125k ($117k) | 26m | 100% |
| CAVEMAN | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| CEILINGCAT | robinhood | robinhood/other | 2026-08-25 00:59 | $22k | $10k |  |  |  |  | 2 | 2 | $877k ($58k) | 21.1h | 50% |
| CEZ | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| CHAD | robinhood | Pons V1 (v3 pool) | 2026-07-20 21:19 | $3k | $3k |  |  |  | 0x0bbb…dc3e (1) | 2 | 1 | $893k ($893k) | 35.9d | 100% |
| CHEEMS | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| CHILLZ | robinhood | LONG (stock-paired) | 2026-08-31 22:00 | $453k | $69k |  |  |  |  | 2 | 1 | $239k ($239k) | 1.0d | 100% |
| CHIP | robinhood | robinhood/other |  | $123k | $30k |  |  |  |  | 2 | 1 | $491k ($491k) |  | 100% |
| CHIPS | robinhood | LONG (stock-paired) | 2026-07-15 09:20 | $65k | $62k |  |  |  |  | 2 | 1 | $57k ($57k) | 6.4d | 100% |
| CHIRPS | robinhood | Pons (WETH pool) | 2026-07-13 05:31 | $5k | $11k |  |  |  |  | 2 | 1 | $225k ($225k) | 31m | 100% |
| CHUDSOME | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| CHYPERION | robinhood | Pons (WETH pool) | 2026-08-10 16:08 | $4k | $4k |  |  |  |  | 2 | 0 |  () |  |  |
| CJ | robinhood | robinhood/other | 2026-08-20 21:34 | $66k | $66k |  |  |  |  | 2 | 1 | $102k ($102k) | 2.9d | 100% |
| CL1 | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| CLANKER | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| CLAWD | robinhood | robinhood/other | 2026-09-03 23:33 | $807k | $477k |  |  |  |  | 2 | 2 | $1.1M ($374k) | 16m | 50% |
| CLAWRA | solana | bags |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| CLUG | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| CLZD | bsc | bsc/other | 2025-11-14 19:56 | $23k | $16k |  |  |  |  | 2 | 0 |  () |  |  |
| COINX | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| COW | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| COW | robinhood | Pons (WETH pool) | 2026-07-24 13:41 | $4k | $5k |  |  |  |  | 2 | 2 | $119k ($80k) | 2.3h | 100% |
| CPX | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| CRACK | robinhood | Pons V2 (v4 hook curve) | 2026-08-28 23:47 | $85k | $26k |  |  |  |  | 2 | 1 | $73k ($73k) | -103m | 100% |
| CRCL | evm? | evm?/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| CZ | bsc | bsc/other | 2026-06-28 07:04 | $86k | $35k |  |  |  |  | 2 | 2 | $3.9M ($608k) | 6.7d | 50% |
| Cali | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Chud | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Claude | robinhood | robinhood/other | 2026-08-27 14:13 |  |  |  |  |  |  | 2 | 1 | $6.3M ($6.3M) | 12m | 0% |
| Claude | robinhood | Pons (WETH pool) | 2026-07-30 23:45 | $3k | $4k |  |  |  |  | 2 | 0 |  () |  |  |
| DATFRONG | robinhood | Pons V2 (v4 hook curve) | 2026-08-08 09:48 | $420k | $120k |  |  |  |  | 2 | 0 |  () |  |  |
| DE | robinhood | robinhood/other | 2026-09-02 01:42 | $16k | $11k |  |  |  |  | 2 | 2 | $61k ($43k) | 1.9h | 100% |
| DELL | robinhood | Pons V1 (v3 pool) | 2026-06-25 16:28 | $375k | $552k |  |  |  |  | 2 | 0 |  () |  |  |
| DELULU | evm? | evm?/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| DEUS | base | base/other | 2026-05-27 13:04 | $16.2M | $710k |  |  |  |  | 2 | 2 | $21.6M ($21.5M) | 76.0d | 0% |
| DOGE-1  | solana | solana/other | 2025-08-12 20:08 | $4.2M | $231k |  |  |  |  | 2 | 4 | $3.6M ($3.6M) | 385.9d | 0% |
| DOGGYCOIN | evm? | evm?/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| DOWNS | robinhood | robinhood/other | 2026-09-02 01:56 | $40k | $85k |  |  |  |  | 2 | 2 | $81k ($63k) | 6.5h | 100% |
| DUST | evm? | evm?/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Dinger | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| EBT | robinhood | robinhood/other | 2026-09-02 13:30 | $74k | $87k |  |  |  |  | 2 | 2 | $160k ($144k) | 14.9h | 100% |
| EITHER | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| EVE | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| EVERYTHING | bsc | bsc/other |  | $12k | $13k |  |  |  |  | 2 | 3 | $393k ($287k) |  | 100% |
| ElonCoin | bsc | bsc/other | 2026-08-20 20:08 | $216k | $53k |  |  |  |  | 2 | 2 | $254k ($238k) | 23m | 100% |
| FAKER | bsc | bsc/other | 2026-08-19 10:48 | $26k | $17k |  |  |  |  | 2 | 2 | $115k ($109k) | 4.3d | 100% |
| FIH | robinhood | Pons (WETH pool) | 2026-07-02 10:52 | $1.2M | $125k |  |  |  |  | 2 | 0 |  () |  |  |
| FINANCE | robinhood | robinhood/other |  | $7k | $7k |  |  |  |  | 2 | 1 | $72k ($72k) |  | 100% |
| FIRE | base | base/other |  |  |  |  |  |  |  | 2 | 2 | $1.4M ($1.1M) |  | 0% |
| FKH | robinhood | Pons V2 (v4 hook curve) | 2026-09-03 20:11 | $15k | $11k |  |  |  |  | 2 | 3 | $46k ($38k) | -0m | 100% |
| FLOPS | robinhood | robinhood/other | 2026-09-03 18:30 | $41k | $38k |  |  |  |  | 2 | 1 | $36k ($36k) | 8m | 100% |
| FLTCH | robinhood | Pons V2 (v4 hook curve) | 2026-09-01 15:45 | $182k | $41k |  |  |  |  | 2 | 0 |  () |  |  |
| FNVDAB | bsc | bsc/other | 2026-09-02 16:50 | $2k | $182k |  |  |  |  | 2 | 0 |  () |  |  |
| FOX | robinhood | Pons V1 (v3 pool) | 2026-07-10 22:29 | $1.3M | $181k |  |  |  |  | 2 | 1 | $706k ($706k) | 34.0d | 100% |
| FRANKIE | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| FREEDOM | robinhood | robinhood/other | 2026-09-03 00:32 | $20k | $13k |  |  |  |  | 2 | 0 |  () |  |  |
| FROGE | robinhood | robinhood/other | 2026-09-03 23:25 | $198k | $46k |  |  |  |  | 2 | 2 | $779k ($718k) | 2.1h | 100% |
| FRONT | robinhood | Pons V2 (v4 hook curve) | 2026-08-30 13:37 | $71k | $25k |  |  |  |  | 2 | 0 |  () |  |  |
| FUEL | robinhood | robinhood/other | 2026-08-25 12:12 | $418k | $60k |  |  |  |  | 2 | 1 | $950k ($950k) | 8.0d | 100% |
| Fapcoin | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| GARY | robinhood | robinhood/other | 2026-09-01 20:59 | $12k | $10k |  |  |  |  | 2 | 2 | $110k ($43k) | 9.6h | 100% |
| GAY | robinhood | robinhood/other |  | $9k | $7k |  |  |  |  | 2 | 0 |  () |  |  |
| GEM | robinhood | Pons V2 (v4 hook curve) | 2026-09-01 21:57 | $79k | $64k |  |  |  |  | 2 | 2 | $347k ($304k) | 25m | 100% |
| GGS | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| GIF | robinhood | Pons V1 (v3 pool) | 2026-07-26 10:00 | $4k | $4k |  |  |  | 0x7de5…b06b (13) | 2 | 0 |  () |  |  |
| GL | robinhood | robinhood/other | 2026-08-29 05:12 | $23k | $116k |  |  |  |  | 2 | 1 | $224k ($224k) | 19m | 100% |
| GLUE | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| GM | robinhood | Pons (WETH pool) | 2026-07-08 05:29 | $6k | $7k |  |  |  |  | 2 | 1 | $75k ($75k) | 1.8d | 100% |
| GOLD | solana | pump.fun | 2026-06-21 18:50 | $5.5M | $207k |  |  |  |  | 2 | 0 |  () |  |  |
| GOLDINU | robinhood | Pons V2 (v4 hook curve) | 2026-08-19 22:46 | $48k | $44k |  |  |  |  | 2 | 0 |  () |  |  |
| GPRO | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| GPU | robinhood | LONG (stock-paired) | 2026-08-28 15:12 | $19k | $8k |  |  |  |  | 2 | 2 | $227k ($158k) | 14m | 100% |
| GRID | robinhood | Pons V1 (v3 pool) | 2026-07-17 09:00 | $3.5M | $178k |  |  |  |  | 2 | 1 | $2.1M ($2.1M) | 45.6d | 0% |
| GROTTO | robinhood | robinhood/other |  |  |  |  |  |  |  | 2 | 1 | $26k ($26k) |  | 100% |
| GT | robinhood | robinhood/other | 2026-08-31 11:41 | $3k | $5k |  |  |  | 0xe7f1…3bfe (1) | 2 | 1 | $85k ($85k) | 12m | 100% |
| GTAVI | robinhood | robinhood/other | 2026-08-13 12:07 | $109k | $37k | 1097 |  |  |  | 2 | 1 | $275k ($275k) | 19.1d | 100% |
| HAMM | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| HELLO | robinhood | LONG (stock-paired) | 2026-07-22 15:48 | $52k | $51k |  |  |  |  | 2 | 2 | $235k ($78k) | 42.1d | 100% |
| HENTAI | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| HOD | robinhood | LONG (stock-paired) | 2026-09-03 09:48 | $47k | $42k |  |  |  |  | 2 | 0 |  () |  |  |
| HODL | bsc | bsc/other | 2026-08-01 00:26 | $74k | $31k |  |  |  |  | 2 | 2 | $171k ($152k) | 1.8d | 100% |
| HONTER | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| HOOTS | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| HORNET | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| HUGGY | bsc | bsc/other |  | $116k | $36k |  |  |  |  | 2 | 3 | $122k ($18k) |  | 100% |
| HarvestFi | robinhood | robinhood/other | 2026-08-13 22:51 | $4k | $6k |  |  |  |  | 2 | 1 | $34k ($34k) | 23.6h | 100% |
| Hosico | solana | bonk (letsbonk) |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Hussing | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| INCOME | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| INFERRA | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| JACKET | bsc | bsc/other | 2026-08-03 14:21 | $800k | $136k |  |  |  |  | 2 | 2 | $7.8M ($7.3M) | 23.8h | 0% |
| JAMES | base | base/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| JOEING | robinhood | LONG (stock-paired) | 2026-09-01 02:44 | $18k | $12k |  |  |  |  | 2 | 2 | $89k ($88k) | 18.1h | 100% |
| JUGGERNAUT | robinhood | robinhood/other | 2026-09-01 20:17 | $16k | $13k |  |  |  |  | 2 | 1 | $88k ($88k) | 23.6h | 100% |
| JWA | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Jacket | bsc | bsc/other |  | $492k | $103k |  |  |  |  | 2 | 2 | $546k ($316k) |  | 100% |
| KEKODYSSEUS | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| KETCHUP | evm? | evm?/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| KETCHUP | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| KISS | bsc | bsc/other |  | $5k | $7k |  |  |  |  | 2 | 2 | $142k ($113k) |  | 100% |
| KITTENS | robinhood | robinhood/other | 2026-09-02 16:19 | $4k | $6k |  |  |  |  | 2 | 2 | $237k ($161k) | 21m | 100% |
| KORI | solana | bonk (letsbonk) | 2025-05-13 13:15 | $2.8M | $448k |  |  |  |  | 2 | 0 |  () |  |  |
| KOSPI | robinhood | robinhood/other | 2026-09-01 22:08 | $47k | $62k |  |  |  | 0x5cbc…0f7e (1) | 2 | 2 | $164k ($112k) | 17m | 100% |
| KURO | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| KUTTA | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Karma | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 12:56 | $24k | $11k |  |  |  |  | 2 | 1 | $105k ($105k) | 16m | 100% |
| Korokke | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| LARPY | robinhood | Pons V2 (v4 hook curve) | 2026-08-29 17:42 | $297k | $51k |  |  |  | 0x4c8c…ef77 (1) | 2 | 1 | $352k ($352k) | 1.3d | 100% |
| LATINAS | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| LAYOFF | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| LEGS | robinhood | Pons V1 (v3 pool) | 2026-07-19 04:10 | $25k | $17k |  |  |  | 0xc3fd…1992 (1) | 2 | 1 | $14k ($14k) | 10m | 100% |
| LEGS | robinhood | robinhood/other | 2026-09-03 19:20 | $734k | $30 |  |  |  | 0xe916…c63c (1) | 2 | 2 | $579k ($171k) | -2m | 100% |
| LIGHTNING | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| LMT | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| LOOOOONG | robinhood | robinhood/other | 2026-09-01 11:27 | $43k | $43k |  |  |  |  | 2 | 1 | $123k ($123k) | 4m | 100% |
| LULU | evm? | evm?/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| LUNA | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Lara | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Lenny  | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| MATE | robinhood | robinhood/other | 2026-08-25 19:01 | $5k | $7k |  |  |  |  | 2 | 1 | $678k ($678k) | 2m | 100% |
| MBS | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| MCAP | robinhood | robinhood/other | 2026-08-30 05:37 | $24k | $25 |  |  |  | 0xe5a7…ed7a (1) | 2 | 0 |  () |  |  |
| MEDUSA | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| MEGUSTA | robinhood | Pons (WETH pool) | 2026-07-14 02:20 | $8k | $7k |  |  |  |  | 2 | 2 | $25k ($21k) | 15.0h | 100% |
| MEME | base | base/other | 2026-08-17 03:09 | $587k | $102k |  |  |  |  | 2 | 2 | $548k ($411k) | 17.2d | 100% |
| MEME | robinhood | Pons (WETH pool) | 2026-07-13 00:02 | $5k | $4k |  |  |  |  | 2 | 1 | $127k ($127k) | 2.7h | 100% |
| MEME | robinhood | LONG (stock-paired) | 2026-07-22 16:45 | $116k | $92k |  |  |  |  | 2 | 2 | $149k ($141k) | 37.8d | 100% |
| MEMECHILDREN | robinhood | robinhood/other | 2026-08-30 10:00 | $4k | $5k |  |  |  |  | 2 | 1 | $136k ($136k) | 36m | 100% |
| MEMESTOCK | bsc | bsc/other | 2026-07-30 09:55 | $16k | $16k |  |  |  |  | 2 | 2 | $179k ($99k) | 5.2d | 100% |
| MEMESTOCK | robinhood | robinhood/other | 2026-08-06 17:28 | $12k | $11k |  |  |  |  | 2 | 1 | $115k ($115k) | 17.9d | 100% |
| MEOW | base | base/other | 2026-07-17 10:40 | $320k | $37k |  |  |  |  | 2 | 2 | $642k ($270k) | 31.4d | 50% |
| MEOW | robinhood | robinhood/other | 2026-09-03 19:03 | $32k | $16k |  |  |  |  | 2 | 2 | $231k ($190k) | 3m | 100% |
| MERA | robinhood | Pons V2 (v4 hook curve) | 2026-09-03 20:38 | $34k | $18k |  |  |  |  | 2 | 2 | $153k ($89k) | 15m | 100% |
| MICRODUCK | robinhood | LONG (stock-paired) | 2026-08-27 11:23 | $26k | $26k |  |  |  |  | 2 | 2 | $30k ($27k) | 21m | 100% |
| MIM | robinhood | Pons V2 (v4 hook curve) | 2026-08-28 19:13 | $59k | $23k |  |  |  |  | 2 | 2 | $271k ($101k) | 5.9d | 100% |
| MINIPI | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| MIT | robinhood | robinhood/other | 2026-08-31 14:41 | $16k | $11k |  |  |  |  | 2 | 1 | $29k ($29k) | -16m | 100% |
| MITCH | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| MOBY | solana | pump.fun | 2025-01-13 18:07 | $1.6M | $338k |  |  |  |  | 2 | 1 | $5.5M ($5.5M) | 382.2d | 0% |
| MOLT | base | base/other | 2026-01-28 17:21 | $334k | $1.3M |  |  |  |  | 2 | 4 | $43.8M ($34.3M) | 2.3d | 0% |
| MUFASA | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Magatard | robinhood | robinhood/other |  | $825k | $79k |  |  |  |  | 2 | 2 | $564k ($231k) |  | 100% |
| MatthewCoin | bsc | bsc/other | 2026-08-10 09:20 | $12k | $14k |  |  |  |  | 2 | 1 | $66k ($66k) | 3.4d | 100% |
| Mbappe | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Microduck | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Mugi | bsc | bsc/other |  | $12k | $11k |  |  |  |  | 2 | 2 | $76k ($54k) |  | 100% |
| NEEGY | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| NINJA | robinhood | LONG (stock-paired) | 2026-09-01 23:41 | $41k | $17k |  |  |  |  | 2 | 2 | $444k ($296k) | 4m | 100% |
| NOKI | base | base/other |  |  |  |  |  |  |  | 2 | 2 | $214k ($201k) |  | 100% |
| NOSTRATEGY | robinhood | LONG (stock-paired) | 2026-09-02 14:53 | $52k | $52k |  |  |  |  | 2 | 2 | $264k ($246k) | 1m | 100% |
| NPCCAT | robinhood | robinhood/other | 2026-08-26 16:23 | $6k | $211k |  |  |  |  | 2 | 1 | $989k ($989k) | 20m | 100% |
| NYAN | solana | pump.fun | 2025-11-27 06:44 | $1.1M | $161k |  |  |  |  | 2 | 14 | $773k ($50k) | 159.4d | 50% |
| Niko | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| OBAMWICH | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| OCTO | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| ODRIPN | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| ODYSSEY | robinhood | Pons V1 (v3 pool) | 2026-07-09 18:58 | $15k | $15k |  |  |  | 0xeeef…2d2e (1) | 2 | 1 | $83k ($83k) | 46.2d | 100% |
| OWL | robinhood | Pons (WETH pool) | 2026-07-26 14:02 | $3k | $3k |  |  |  |  | 2 | 0 |  () |  |  |
| Onboard | robinhood | Pons V1 (v3 pool) | 2026-07-18 23:56 | $4k | $4k |  |  |  | 0x2ad4…3e55 (1) | 2 | 1 | $116k ($116k) | 1.9h | 100% |
| PABLO | robinhood | robinhood/other | 2026-09-02 20:46 | $17k | $13k |  |  |  |  | 2 | 2 | $83k ($80k) | 17.1h | 100% |
| PARASITE | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| PATAGONIA | robinhood | robinhood/other |  | $2k | $4k |  |  |  |  | 2 | 0 |  () |  |  |
| PCC | robinhood | Pons V1 (v3 pool) | 2026-08-25 01:56 | $5.9M | $289k |  |  |  |  | 2 | 2 | $7.7M ($7.0M) | 1.6d | 0% |
| PDF | robinhood | robinhood/other | 2026-09-03 21:30 | $61k | $206k |  |  |  |  | 2 | 2 | $140k ($93k) | 11m | 100% |
| PECCY | robinhood | robinhood/other |  | $16k | $10k |  |  |  |  | 2 | 1 | $193k ($193k) |  | 100% |
| PEPE | bsc | bsc/other | 2023-05-19 02:22 | $1.6M | $255k |  |  |  |  | 2 | 0 |  () |  |  |
| PEPTIDE | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| PFWA | robinhood | Pons V1 (v3 pool) | 2026-08-01 23:09 | $518k | $92k |  |  |  |  | 2 | 1 | $333k ($333k) | 27.9d | 100% |
| PIBBLE | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| PIGEON  | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| PINDEX | robinhood | Pons V2 (v4 hook curve) | 2026-08-25 23:26 | $51k | $21k |  |  |  |  | 2 | 1 | $183k ($183k) | 4.3d | 100% |
| PIZZA | bsc | bsc/other | 2026-08-02 04:28 | $168k | $61k |  |  |  |  | 2 | 2 | $362k ($104k) | 25m | 100% |
| PLUMBED | robinhood | robinhood/other |  | $58k | $59k |  |  |  |  | 2 | 1 | $24k ($24k) |  | 100% |
| PON | robinhood | robinhood/other |  | $3k | $4k |  |  |  |  | 2 | 1 | $91k ($91k) |  | 100% |
| PONSBOY | robinhood | robinhood/other | 2026-08-26 03:30 | $15k | $11k |  |  |  |  | 2 | 1 | $38k ($38k) | -1m | 100% |
| PONSGUY | robinhood | Pons (WETH pool) | 2026-07-15 04:34 | $38k | $20k |  |  |  |  | 2 | 0 |  () |  |  |
| PONSI | robinhood | Pons (WETH pool) | 2026-07-21 06:14 | $4k | $4k |  |  |  |  | 2 | 1 | $132k ($132k) | 32m | 100% |
| PONSTERS | robinhood | robinhood/other | 2026-08-20 16:45 | $3k | $5k |  |  |  |  | 2 | 1 | $74k ($74k) | 20m | 100% |
| PUMPBULL | solana | pump.fun | 2026-08-06 18:31 | $116k | $29k |  |  |  |  | 2 | 0 |  () |  |  |
| PURCH | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| PVE | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Pointless | robinhood | Pons (WETH pool) | 2026-07-11 09:12 | $42k | $23k |  |  |  |  | 2 | 1 | $117k ($117k) | 45.0d | 100% |
| Potato | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Pringles | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| QI | robinhood | robinhood/other | 2026-09-01 06:48 | $280k | $65k |  |  |  |  | 2 | 2 | $643k ($210k) | 29m | 50% |
| QQQX | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| QUACKD | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| QUBY | bsc | bsc/other | 2026-09-02 22:21 | $204k | $46k |  |  |  |  | 2 | 2 | $470k ($317k) | 4.1h | 100% |
| RAIL | eth | eth/other | 2021-12-29 15:49 | $121.7M | $5.3M |  |  |  |  | 2 | 2 | $105.5M ($94.6M) | 1604.4d | 0% |
| RATHBUN | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| RAWR | base | base/other | 2026-08-20 14:11 | $803k | $109k |  |  |  |  | 2 | 3 | $473k ($7k) | 3.4h | 67% |
| RBRC | robinhood | robinhood/other | 2026-08-31 07:40 | $8k | $8k |  |  |  |  | 2 | 1 | $249k ($249k) | 16m | 100% |
| RCA | robinhood | LONG (stock-paired) | 2026-08-18 21:34 | $3k | $4k |  |  |  |  | 2 | 1 | $20k ($20k) | 2.4h | 100% |
| REDWOODJS | solana | bags |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| RETAIL | robinhood | robinhood/other | 2026-09-02 08:12 | $8k | $7k |  |  |  |  | 2 | 2 | $355k ($278k) | 23m | 100% |
| RETARD | robinhood | Pons V2 (v4 hook curve) | 2026-09-01 21:49 | $43k | $22k |  |  |  |  | 2 | 2 | $130k ($77k) | 18m | 100% |
| RFLX | robinhood | robinhood/other | 2026-07-31 19:44 | $129k | $32k |  |  |  |  | 2 | 1 | $157k ($157k) | 32.4d | 100% |
| RICH | robinhood | robinhood/other | 2026-07-23 03:23 | $21 | $5 |  |  |  | 0xad40…3e51 (1) | 2 | 1 | $74k ($74k) | -7m | 100% |
| RING | robinhood | Pons V2 (v4 hook curve) | 2026-09-01 19:37 | $140k | $94k |  |  |  |  | 2 | 1 | $39k ($39k) | 46m | 100% |
| RIVN | robinhood | robinhood/other | 2026-09-02 03:50 | $31k | $20k |  |  |  |  | 2 | 2 | $164k ($39k) | 5m | 100% |
| ROBAI | robinhood | Pons (WETH pool) | 2026-08-07 14:18 | $2k | $4k |  |  |  |  | 2 | 1 | $744k ($744k) | 12m | 100% |
| ROBINGPT | evm? | evm?/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| ROBLOXIANS | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 10:03 | $2.1M | $137k |  |  |  |  | 2 | 6 | $2.6M ($2.1M) | 12.3h | 0% |
| ROSCOE | robinhood | robinhood/other |  | $5k | $7k |  |  |  |  | 2 | 0 |  () |  |  |
| RUBIUS | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| RUNIT | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| RURU | robinhood | robinhood/other | 2026-09-02 21:42 | $20k | $13k |  |  |  |  | 2 | 1 | $104k ($104k) | 1.4h | 100% |
| Ratspeak | base | base/other | 2026-05-18 20:05 | $1.8M | $412k |  |  |  |  | 2 | 2 | $3.5M ($1.4M) | 96.9d | 0% |
| RayRay | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Regulardude | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Rocket | robinhood | Pons (WETH pool) | 2026-07-11 21:34 | $7k | $8k |  |  |  | 0x68b9…6c7d (1) | 2 | 1 | $684k ($684k) | 2.1d | 100% |
| Rubio | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| S&amp;P500 | robinhood | Pons (WETH pool) | 2026-07-11 20:48 | $10k | $13k |  |  |  |  | 2 | 1 | $272k ($272k) | 3.4d | 100% |
| SANDISK | robinhood | robinhood/other | 2026-09-03 19:46 | $4k | $6k |  |  |  |  | 2 | 2 | $173k ($98k) | 10m | 100% |
| SAPA | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| SATURN | bsc | bsc/other | 2026-08-28 15:47 | $371k | $70k |  |  |  |  | 2 | 1 | $1.3M ($1.3M) | 9.9h | 0% |
| SCI6900 | bsc | bsc/other | 2026-08-05 08:20 | $11k | $12k |  |  |  |  | 2 | 2 | $145k ($29k) | 1.5h | 100% |
| SFEAD | robinhood | robinhood/other | 2026-08-27 18:30 | $10.4M | $1.4M |  |  |  |  | 2 | 1 | $4.0M ($4.0M) | 8m | 0% |
| SHERBERT | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| SHERWOOD | robinhood | Pons V2 (v4 hook curve) | 2026-09-03 19:23 | $737k | $70k |  |  |  |  | 2 | 2 | $2.4M ($2.3M) | 14m | 0% |
| SHINJUKU | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| SHRUB | robinhood | robinhood/other |  | $22k | $13k |  |  |  |  | 2 | 1 | $1.1M ($1.1M) |  | 0% |
| SILVERBACK | robinhood | robinhood/other |  | $29k | $40k |  |  |  |  | 2 | 2 | $114k ($112k) |  | 100% |
| SIRIUS | bsc | bsc/other | 2026-08-02 10:51 | $45k | $26k |  |  |  |  | 2 | 2 | $166k ($122k) | 19.2d | 100% |
| SLIPPY | robinhood | Pons V2 (v4 hook curve) | 2026-07-16 12:05 | $2.0M | $236k |  |  |  |  | 2 | 1 | $1.4M ($1.4M) | 9.8d | 0% |
| SOLANA | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| SOLANA | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| SOLCAT | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| SOUNDER | robinhood | Pons V2 (v4 hook curve) | 2026-09-03 20:36 | $64k | $23k |  |  |  |  | 2 | 2 | $154k ($108k) | 6m | 100% |
| SPARKY | robinhood | LONG (stock-paired) | 2026-08-26 19:57 | $25k | $21k |  |  |  |  | 2 | 1 | $22k ($22k) | 1.4h | 100% |
| SPDR | robinhood | robinhood/other |  | $8k | $7k |  |  |  |  | 2 | 2 | $100k ($44k) |  | 100% |
| STACY | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| STOCKER | eth | eth/other | 2026-09-03 22:58 | $2.0M | $146k |  |  |  |  | 2 | 2 | $1.5M ($1.0M) | 3.2h | 0% |
| STRAY | robinhood | robinhood/other |  |  |  |  |  |  |  | 2 | 1 | $434k ($434k) |  | 100% |
| SUIT | robinhood | Pons (WETH pool) | 2026-07-09 15:08 | $22k | $15k |  |  |  |  | 2 | 1 | $783k ($783k) | 22.4h | 100% |
| Spoderman | robinhood | robinhood/other | 2026-09-02 08:57 | $55k | $28k |  |  |  |  | 2 | 1 | $84k ($84k) | 6m | 100% |
| Sue | bsc | bsc/other | 2026-08-24 12:48 | $660k | $109k |  |  |  |  | 2 | 2 | $3.0M ($2.6M) | 1.9d | 0% |
| TABBY | robinhood | robinhood/other | 2026-09-02 16:05 | $7k | $7k |  |  |  |  | 2 | 1 | $80k ($80k) | 4m | 100% |
| TAM | robinhood | robinhood/other |  | $6k | $10k |  |  |  |  | 2 | 1 | $135k ($135k) |  | 100% |
| TBB | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| TBILL | robinhood | robinhood/other | 2026-07-26 21:40 | $13k | $38 |  |  |  | 0x5bb5…4fca (1) | 2 | 1 | $114k ($114k) | -13677m | 100% |
| TIMMY | robinhood | robinhood/other |  | $6k | $6k |  |  |  |  | 2 | 2 | $156k ($51k) |  | 100% |
| TITCOIN | robinhood | robinhood/other |  | $1.0M | $91k |  |  |  |  | 2 | 2 | $277k ($233k) |  | 100% |
| TJF | robinhood | Pons (WETH pool) | 2026-07-11 15:14 | $3k | $6k |  |  |  |  | 2 | 1 | $263k ($263k) | 25m | 100% |
| TRIPLET | robinhood | Pons (WETH pool) | 2026-07-02 08:41 | $20k | $13k |  |  |  |  | 2 | 1 | $32k ($32k) | 59.5d | 100% |
| TRUSTY | bsc | bsc/other | 2026-09-02 03:01 | $91k | $31k |  |  |  |  | 2 | 1 | $130k ($130k) | 52m | 100% |
| TRUTH | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| TULIP | robinhood | robinhood/other |  | $16k | $9k |  |  |  |  | 2 | 1 | $109k ($109k) |  | 100% |
| UBI | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| UMIA | base | base/other | 2026-09-02 12:10 | $28.8M | $3.1M |  |  |  |  | 2 | 2 | $29.5M ($28.6M) | 0m | 0% |
| UMIA | evm? | evm?/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| UNDERDOG | robinhood | Pons (WETH pool) | 2026-07-22 03:21 | $5k | $5k |  |  |  |  | 2 | 1 | $10k ($10k) | 12m | 100% |
| URANUS | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| UwU | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| VAMP | solana | bags |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| VARO | robinhood | Pons (WETH pool) | 2026-07-27 15:27 | $101k | $101k |  |  |  |  | 2 | 1 | $186k ($186k) | 1.4h | 100% |
| VEGA | robinhood | LONG (stock-paired) | 2026-08-29 08:56 | $6k | $6k |  |  |  |  | 2 | 1 | $234k ($234k) | 3m | 100% |
| VEIL | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| VERD | robinhood | Pons (WETH pool) | 2026-08-03 16:47 | $4k | $4k |  |  |  |  | 2 | 1 | $128k ($128k) | 52m | 100% |
| VERONA | robinhood | robinhood/other | 2026-08-29 00:19 | $6k | $26k |  |  |  |  | 2 | 1 | $102k ($102k) | 1.1h | 100% |
| VIAGRA | robinhood | LONG (stock-paired) | 2026-09-03 16:31 | $29k | $121k |  |  |  |  | 2 | 2 | $117k ($95k) | 3m | 100% |
| VOICEBOX | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| VOXIE | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| VPN | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| VUNIX | robinhood | robinhood/other | 2026-09-03 12:40 | $5k | $9k |  |  |  |  | 2 | 2 | $318k ($308k) | 35m | 100% |
| Viagra | robinhood | robinhood/other |  | $10k | $8k |  |  |  |  | 2 | 2 | $48k ($21k) |  | 100% |
| WAY | robinhood | Pons (WETH pool) | 2026-08-27 17:24 | $2.1M | $232k |  |  |  |  | 2 | 2 | $1.8M ($1.6M) | 6.4d | 0% |
| WDOG | robinhood | LONG (stock-paired) | 2026-09-03 04:15 | $10k | $8k |  |  |  |  | 2 | 2 | $98k ($79k) | 47m | 100% |
| WELF | evm? | evm?/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| WFNT | robinhood | LONG (stock-paired) | 2026-09-03 01:44 | $143k | $42k |  |  |  | 0xd571…7baf (1) | 2 | 2 | $237k ($193k) | 1.6h | 100% |
| WOJAK | robinhood | Pons V2 (v4 hook curve) | 2026-09-02 15:03 | $98k | $69k |  |  |  |  | 2 | 0 |  () |  |  |
| WOOF | robinhood | Pons V1 (v3 pool) | 2026-07-27 22:57 | $977k | $132k |  |  |  |  | 2 | 0 |  () |  |  |
| WRESTLER | robinhood | Pons V2 (v4 hook curve) | 2026-09-03 03:24 | $128k | $43k |  |  |  |  | 2 | 2 | $169k ($164k) | 17.4h | 100% |
| WSOLP | solana | pump.fun | 2026-06-16 12:32 | $2.1M | $160k |  |  |  |  | 2 | 5 | $362k ($190k) | 4.7h | 80% |
| WTFO | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Walruse | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| Wreckit | solana | bags |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| XIAO | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| XPD | robinhood | robinhood/other | 2026-09-02 12:48 | $206k | $102k |  |  |  | 0x6d67…ebaa (1) | 2 | 1 | $218k ($218k) | 59m | 100% |
| XRP | base | base/other | 2026-04-16 04:51 | $177.1M | $496k |  |  |  |  | 2 | 2 | $173.0M ($168.2M) | 137.1d | 0% |
| XWH | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| YOMOGI | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| YOMOGI | eth | eth/other | 2026-08-23 00:11 | $27k | $13k |  |  |  |  | 2 | 2 | $1.0M ($905k) | 2.9h | 50% |
| YOUDECIDE | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| ZCAT | solana | solana/other | 2026-08-30 23:29 | $3.4M | $259k |  |  |  |  | 2 | 5 | $388k ($365k) | 52m | 100% |
| ZUCC | robinhood | LONG (stock-paired) | 2026-07-14 17:44 | $87k | $69k |  |  |  |  | 2 | 2 | $74k ($35k) | 7.0d | 100% |
| Zipper | robinhood | robinhood/other | 2026-08-30 07:06 | $69k | $25k |  |  |  |  | 2 | 1 | $610k ($610k) | 14.2h | 100% |
| b-money | bsc | bsc/other | 2026-08-22 20:29 | $785k | $104k |  |  |  |  | 2 | 1 | $1.0M ($1.0M) | 5.4h | 0% |
| bFUND | bsc | bsc/other | 2026-07-28 17:44 | $12k | $13k |  |  |  |  | 2 | 0 |  () |  |  |
| claude | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| diVINE | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| dildo | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| gib | robinhood | robinhood/other | 2026-08-14 22:31 | $58k | $30k |  |  |  |  | 2 | 1 | $12.8M ($12.8M) | 2.7h | 0% |
| human | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| kash | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| looong | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| magacock | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| mamAOCita | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| memecoin | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| mj | bsc | bsc/other | 2026-08-07 09:33 | $11k | $11k |  |  |  |  | 2 | 0 |  () |  |  |
| pixeldog | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| pre-rich | bsc | bsc/other | 2026-07-24 23:47 | $10k | $12k |  |  |  |  | 2 | 2 | $130k ($21k) | 3.6h | 100% |
| pumpkets | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| pwease | solana | pump.fun | 2025-03-02 22:01 | $1.6M | $526k |  |  |  |  | 2 | 52 | $2.9M ($873k) | 163.9d | 12% |
| rasmr | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| rehanfal | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| rudi | solana | bonk (letsbonk) |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| spanki | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| spurdo | solana | solana/other |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| stockcoin | robinhood | Pons V1 (v3 pool) | 2026-07-27 20:33 | $4k | $4k |  |  |  | 0x96bb…c27f (21) | 2 | 0 |  () |  |  |
| trust | bsc | bsc/other | 2026-08-31 11:48 | $265k | $53k |  |  |  |  | 2 | 2 | $231k ($148k) | 8.3h | 100% |
| wiwiwi | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| 傻孩子 | bsc | bsc/other | 2026-08-30 16:27 | $269k | $57k |  |  |  |  | 2 | 2 | $265k ($141k) | 1.2h | 100% |
| 墩墩 | bsc | bsc/other |  | $22k | $16k |  |  |  |  | 2 | 2 | $1.2M ($215k) |  | 50% |
| 奶蛙 | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| 小鼻嘎 | bsc | bsc/other | 2026-08-27 03:21 | $4k | $6k |  |  |  |  | 2 | 2 | $159k ($149k) | 1.7h | 100% |
| 币安人生 | bsc | bsc/other | 2025-10-04 15:01 | $497.5M | $7.9M |  |  |  |  | 2 | 0 |  () |  |  |
| 我的刀盾 | solana | pump.fun |  |  |  |  |  |  |  | 2 | 0 |  () |  |  |
| 熊猫 | bsc | bsc/other |  | $45k | $27k |  |  |  |  | 2 | 2 | $143k ($89k) |  | 100% |
| 牛来 | bsc | bsc/other |  | $9k | $10k |  |  |  |  | 2 | 2 | $460k ($381k) |  | 100% |
| 牛棚 | bsc | bsc/other |  | $17k | $14k |  |  |  |  | 2 | 2 | $61k ($46k) |  | 100% |
| 猪猪侠 | bsc | bsc/other |  | $10k | $11k |  |  |  |  | 2 | 2 | $105k ($72k) |  | 100% |
| 甜甜币 | bsc | bsc/other | 2026-08-28 12:14 | $6k | $8k |  |  |  |  | 2 | 2 | $371k ($288k) | 18m | 100% |
| 继续走下 | bsc | bsc/other |  | $3k | $5k |  |  |  |  | 2 | 2 | $41k ($28k) |  | 100% |
| 金狗 | bsc | bsc/other | 2026-07-28 14:01 | $297k | $72k |  |  |  |  | 2 | 1 | $83k ($83k) | 14.1d | 100% |
