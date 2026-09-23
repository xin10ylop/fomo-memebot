# E1-first seat: what the real first buyer made (from chain events only)

The scripts are in this folder. `e1_truth_fetch.py` is `e1_multi.py` with the qualification left verbatim. `e1_truth_analyze.py` scores the model at the incumbent's ETH stake. `e1_truth_report.py` prints the tables below.
Launch-level JSON: `e1_truth_launches_30h.json` and `e1_truth_launches_sep1819.json`. Raw events and receipts are in `raw/` and `raw_sep1819/`.
All calls went to the public RPC, with batches of 5 or fewer, a global gap of 0.3 s and 3 threads. That came to about 7,400 requests and 35 HTTP 429s, all retried. There were 0 launch errors.

## Coverage
* **Requested 30 h**: Sep 22 01:17 to Sep 23 07:14 UTC, blocks 69,257,094 to 70,326,294, in five 6-hour windows on a pinned head. The windows held 8,300 creations and **175 qualifying launches**: tier 2-3%, 3 or more named wallets, bundle of 0.3 ETH or more, E1 and E2 both found. 132 of the 175 had at least one Buy in the E1 block.
* **The backtest's own 141 launches**, Sep 18 13:27 to Sep 19 13:10 (`data/derived/e1_sep1819/e1m_*.json`), were refetched by (b0, curve) and all 141 re-qualified. `score()` reproduces the repo's E1_first_h15_250 on **141/141 launches with a maximum absolute difference of 0.0**, which gives **+9.3% mean**. 116 of the 141 had an E1 buyer. Our own wallet 0xe0686dc7… (via relay 0xe8e98c35…) held **15 of those 116 first seats** and 31 of positions 1-4. These are excluded from all "bot" numbers below.
* I stopped the extension past 30 h (BACK_H 30 onward) to spend the rate budget on the Sep 18-19 replication.

## Definitions
* **Position k**: the k-th Buy event in the E1 block, ordered by logIndex.
* **Realized**: the ETH-out of that buyer's Sells on the same curve up to E1+100 blocks, divided by the Buy's gross ETH in, minus 1. Lots are matched FIFO. The lot counts as sold when at least 99.9% of its tokens were sold. Pos-1 had no prior buy on the same curve in any launch.
* **A** (actual): the realized return if the lot was sold, otherwise the lot marked by the curve at E1+15 (the backtest's exit rule).
* **Eventual**: the realized return when the lot was closed within 6,000 blocks (about 10 min).
* **C**: `score(bE1, "first", SUR 0.0618, hold 15, stake = the incumbent's ETH)`. This is the backtest's number at the same stake.
* **B**: the same as C with the incumbent's own E1 buy and its sells removed from the tape, so we take its seat instead of standing in front of it.

## 1. Fees and the entry/exit mechanics: exact
* Pos-1 is the **first curve event of the E1 block in 132/132 (Sep 22-23) and 101/101 (Sep 18-19)**. The model's entry state is therefore exactly what the real first buyer faced.
* The fee the first buyer effectively paid equals **tier + 6.18% within 0.0005 in 130/132 and 101/101**. The 2 exceptions are insiders, below.
* **443/443** tracked Sells returned exactly (1 − tier) × the curve-model gross. The maximum deviation was 0.00000.
* Where the incumbent sold exactly at E1+15, B equals realized to **0.04 pts (n=6) and 0.07 pts (n=8)** mean absolute error.
* So the curve, the surcharge and the tier are not where anything breaks.

## 2. By position (our own fills excluded)

**Sep 22 01:17 to Sep 23 07:14 (30 h, 175 launches; model mean +1.5% at $250)**

| pos | n | sold all ≤100 blk | realized mean / median / win | ETH-wtd realized | A (held→mark@15) mean / med / win | eventual n, mean / med / win, ETH-wtd | median hold, blk (s) | median stake ETH |
|---|---|---|---|---|---|---|---|---|
| 1 | 132 | 64 (48%) | −11.9% / −9.5% / 27% | −1.1% | −2.7% / −7.8% / 35% | 97, −9.9% / −9.0% / 34%, +1.3% | 18.5 (1.5 s) | 0.040 |
| 2 | 101 | 47 (47%) | −20.5% / −11.3% / 26% | +1.2% | −6.6% / −8.3% / 33% | 72, −17.2% / −11.1% / 29%, −6.5% | 21 (2 s) | 0.010 |
| 3 | 74 | 33 (45%) | −13.0% / −11.9% / 27% | +20.8% | −6.1% / −9.7% / 34% | 47, −12.3% / −11.6% / 30%, +16.9% | 21 (2 s) | 0.010 |
| 4 | 54 | 19 (35%) | −21.0% / −24.6% / 21% | −11.9% | −6.4% / −10.9% / 35% | 33, −15.4% / −11.6% / 33%, −8.4% | 21 (2 s) | 0.007 |

**Sep 18-19 (the +9.3% launches; bots only, our 15/31 fills excluded)**

| pos | n | sold all ≤100 blk | realized mean / median / win | ETH-wtd realized | A mean / med / win | eventual n, mean / med / win, ETH-wtd | median hold, blk (s) | median stake ETH |
|---|---|---|---|---|---|---|---|---|
| 1 | 101 | 47 (47%) | +6.1% / +1.8% / 57% | +3.5% | +7.2% / +0.1% / 51% | 82, +3.8% / +0.3% / 52%, +1.7% | 40 (4 s) | 0.035 |
| 2 | 81 | 33 (41%) | +1.4% / −0.8% / 45% | −3.8% | +6.4% / +0.4% / 52% | 62, +5.0% / −3.5% / 42%, −3.8% | 36 (3 s) | 0.040 |
| 3 | 64 | 24 (38%) | +5.5% / −5.2% / 33% | +3.9% | +7.5% / −0.8% / 47% | 41, +6.9% / −4.7% / 39%, +0.7% | 48.5 (4 s) | 0.043 |
| 4 | 49 | 15 (31%) | −6.5% / −9.7% / 33% | −4.6% | +6.8% / +0.3% / 51% | 31, −12.3% / −9.7% / 32%, −7.3% | 31 (3 s) | 0.025 |

The bots do **not** hold 15 blocks:
* Of pos-1 sellers within 100 blocks, only 26/64 (Sep 22-23) and 7/47 (Sep 18-19) sold between 10 and 20 blocks.
* About half did not close within 100 blocks. For those, the median eventual last sell was 544 blocks (Sep 22-23) and 151 blocks (Sep 18-19).

## 3. Matched pairs: pos-1 actual vs the backtest at the same ETH stake

A − C = (B − A reversed: the exit timing) + (C − B: the incumbent's own buy left behind us).

| sample / subset | n | A mean / med | C mean / med | **A−C mean / med** | C−B mean / med | B−A mean / med | ETH-wtd A / B / C |
|---|---|---|---|---|---|---|---|
| Sep 22-23 all | 132 | −2.7% / −7.8% | +4.3% / −2.1% | **−7.0% / −2.4%** | +4.6% / +1.7% | +2.4% / 0.0% | +2.3% / +2.5% / +14.0% |
| Sep 22-23 sold ≤100 | 64 | −11.9% / −9.5% | −4.5% / −5.5% | **−7.5% / −0.9%** | +2.4% / +0.3% | +5.1% / 0.0% | −1.1% / −1.2% / +2.2% |
| Sep 22-23 stake at 3% CAP | 31 | −0.8% / −2.9% | +8.8% / +6.2% | −9.5% / −10.2% | +10.8% / +10.3% | −1.2% / 0.0% | −0.7% / −1.0% / +13.3% |
| Sep 18-19 all | 101 | +7.2% / +0.1% | +14.2% / +8.8% | **−7.0% / −2.0%** | +5.4% / +2.0% | +1.6% / 0.0% | +5.2% / +8.0% / +19.0% |
| Sep 18-19 sold ≤100 | 47 | +6.1% / +1.8% | +16.9% / +12.8% | **−10.8% / −10.9%** | +7.3% / +5.0% | +3.5% / +2.3% | +3.5% / +8.1% / +18.5% |
| Sep 18-19 stake at 3% CAP | 24 | +2.8% / +0.4% | +20.5% / +16.6% | −17.8% / −19.0% | +13.2% / +13.3% | +4.6% / +3.1% | +2.7% / +6.7% / +19.8% |

**Biggest disagreements** (b0 / E1 block / pos-1 / stake / A vs C / buy tx / sell tx):

Sep 22-23:
* 70128063 / 70128072 / 0x2abdd72b… / 0.0032 / **−72.3% vs −7.3%** (held 32 blk) / buy 0x73c7ef701695c9b16e18f01244fc8bf71e59f30f35cd727be5524be0e8be6951 / sell 0xb2e1789d7232b641203924ddc3cfa9e53aeb8b4da18c6613f1bfa1beb21c309c
* 69951764 / 69951773 / 0x6d9b2677… / 0.0054 / **−60.7% vs −4.9%** (27 blk) / 0xe1bec479a1270bb78ec928216f3083fdf6926ad6055a3e1e115fb1cac47dda31 / 0x72d32fabe7d90c17e0f17bb74aafc296f74b89d29a49ec253c26060348b9fb82
* 69903860 / 69903868 / 0x5bc235ac… / 0.030 / **−63.9% vs −9.7%** (33 blk) / 0x2c83f250fabd4cf01df8087bc8d18ded0de2d6bfd5ff7892e7b6358cb0be6d9a / 0x60efc01771606d991bf92294a9dc8414562b91f44506f7b984de87304a5e3b95
* 69888895 / 69888904 / 0xdae16233… / 0.0054 / **−63.5% vs −9.3%** (59 blk) / 0xad5493730e716f3ede8f43b79eb9670541627dbcfe83caf5e3eaf73abf6a850e / 0xd0989f711cca06ad005f1eaed4bf1e4e7706ac6d998f55f08a0dea6db4b4cad3
* 70136547 / 70136553 / 0x5051e45b… / 0.50 / **+29.5% vs +70.0%**, B +38.2% (partial) / 0x8ce2a84c42391db1653cfa643eee81b403acefac2a94a50431df1f0dd8e3e9d1 / 0x19817f736eb4bd4b1995f089126e046fb6bd130582420a18ec05e356f0cb40d4
* 70239434 / 70239439 / 0x5051e45b… / 0.50 / **+1.9% vs +30.7%**, B +1.6% (held) / 0x0bc46bc2f1ea5adb045b03bac064e76488a157132e9f00f3d823221a190532c8 / -

Sep 18-19:
* 66558210 / 66558216 / 0x6c56103c… / 0.15 / **−53.7% vs +6.1%**, B −5.8% (23 blk) / 0x6f7a9085bc32c61f52e67cba12da52c5fa63aca4573ac3cdfe41345cea9bed6c / 0x4e6ab86f37252c5d4e4929c00a6c41c88610b604e47dfc9f13e41e050378c0db
* 66486701 / 66486710 / 0x26558f89… / 0.039 / **+19.5% vs +76.8%** (94 blk) / 0x3854b46a2647177c2ee9961aa3dc92a97996476252e938875d457b2f589c644a / 0x1fd6e6727fb766fbc3214ee3d7c2c86ab93198179109bc497f1b8bbb709d55f8
* 67045115 / 67045121 / 0x6c56103c… / 0.15 / **+28.1% vs +61.6%**, B +39.2% (22 blk) / 0x95e5298c951da5ea92b3238f06389736b290f658c2e198f67f4fff1dba28174e / 0xdbce03a190ce73815163201f324ebf94f25b725490f804b5f6d58b69d0a21492
* 66448819 / 66448828 / 0x6c56103c… / 0.15 / **+14.6% vs +40.9%**, B +23.2% (49 blk) / 0xcb167dc54404090a80f49767126750f8c5bb23058e053176a1f14aa705a639b3 / 0x56a51e9f7794707fb5a568471a6ca572415e2fc9ef94c3069569df77b251785e
* 66877669 / 66877675 / 0x147ca3d8… / 0.002 / **+33.3% vs −9.1%** (100 blk) / 0x2216109cd623e42ced3d079e807fa1f1f66190bee2aa3d03afb6cbbe7ece93cc / 0xe0aea72faccbc13e767b43684fe596f0f21e181b925af5451b7c17c7c1d514a6

`report_30h.txt` and `report_sep1819.txt` hold the full top 10 for each sample.

## 4. Who holds seat 1

There were 44 distinct pos-1 addresses (Sep 22-23) and 35 (Sep 18-19). The top 5 took 41% and 50% of the seats.

| address | window | n | stake | median hold | realized P&L (sold) | eventual P&L | A mean | C mean |
|---|---|---|---|---|---|---|---|---|
| **0x6c56103c6af4891be46cb3666c1fa354cc79eaca** (contract, rotating EOAs) | Sep 22-23 | 20 | 0.1487 fixed | 14.5 blk (1.0 s), 20/20 sold | **+0.0025 ETH on 2.974** (+0.08%) | same | +0.1% | +2.6% |
| same | Sep 18-19 | 16 | 0.15 fixed | 48.5 blk (4.5 s), 16/16 sold | **+0.0470 ETH on 2.400** (+2.0%) | same | +2.0% | **+24.7%** |
| 0xb316a9ccf21ca0c71701a5e756faf270b18e3060 | Sep 22-23 | 10 | 0.05 | 69 blk | −0.0033 on 0.50 | same | −0.7% | +1.0% |
| 0xfb5b10615a2008c6507d9fa02a55310159969f1e | Sep 22-23 | 9 | 0.005 | 21 blk | −0.0169 on 0.135 | same | −17.4% | −16.4% |
| 0x5bc235acecff3dde394f4bfc696f7c35efd502f0 | Sep 22-23 | 8 | 0.03 | 12 blk | −0.0725 on 0.120 (4 sold) | −0.0725 (4/8 closed) | −35.6% | −27.8% |
| 0x5051e45b2dbecf1b2041af3937bd85fc0dc43cd4 | Sep 22-23 | 7 | 0.50 | never sold ≤10 min | 0 | 0/7 closed | +1.6% (mark) | +23.5% |
| 0x924378f23c4cc4b0b245d0219d0351309839492f | Sep 22-23 | 6 | 0.21 | >100 blk | 0 | +0.242 ETH (6/6 closed) | +4.8% | +21.3% |
| 0xfefe306eb0e5eaf0d6821a1d2935ffc5cfa8cc1b | Sep 18-19 | 13 | 0.03 | 79 blk | +0.0079 on 0.243 | +0.0176 (13/13) | −2.4% | −3.5% |
| 0xb316a9cc… | Sep 18-19 | 4 | 0.055 | 82 blk | +0.0448 on 0.220 | same | +20.3% | +28.5% |

About 0x6c56103c, the bot that runs our strategy:
* On Sep 22-23, on its 14 exits at 15 blocks or fewer, C = B = +0.04% mean against a realized +1.6%.
* On its 6 exits at 16 blocks, C was **+8.7%** against a realized −3.5% and B −3.3%. The model exits at +15 and keeps this bot's 0.149 ETH buy but not its dump one block later. Examples: b0 69907660, C +0.1% vs −9.8%; 69963221, +1.9% vs −8.2%; 69761441, +15.9% vs +2.2%; 69980028, +23.4% vs +8.3%.

Gas for all of these bots is negligible: 0.00037 ETH across 0x6c56's 20 round trips.

## 5. Insiders, reverts and what comes before pos-1

**Insiders.** Named calldata wallets held pos-1 in 2/132 launches on Sep 22-23:
* 0x9ccef731b9ef1077dc46f234afd69f1bc05ab932, b0 69715385, tx 0xc7981d0c4b3b286498cb677a3e718c64a076b7acc9bd5d92d2cb66c2623a874a
* 0xbb2009ba06a024ee5c4faed81b1977845c02afac, b0 69934789, tx 0xf52faf7d88fdd4ad4ace51631013858a7b84677622f09f4ec759b0d8dc9ddd7d

Insiders appeared 7 times in positions 1-4, and **all 7 paid the tier only (no 6.18% surcharge)**. On Sep 18-19: 0 at pos-1, 1 at pos-2, also tier only. The creator was never among the first 4.

**Txs before pos-1** (index 0 is ArbOS):
* Pos-1 was the first user tx (index 1) in 56/132 launches (Sep 22-23) and 50/101 (Sep 18-19). User txs came before it in 76/132 and 51/101.
* Sep 22-23: 389 such txs, 84 reverted, 105 receipts not fetched (a cap of 10 per block).
* Sep 18-19: 331 txs, 66 reverted, 127 receipts not fetched.
* None of the fetched receipts carries a log from the curve.
* The main reverter on Sep 22-23 is 0xb316a9cc…, through its contract 0xa95fe1ca… (0.05 ETH, selector eca314af): **22 reverted txs ahead of someone else's pos-1, against 17 landed E1 buys**.
* On Sep 18-19 the main reverters are the contracts 0x198f7836… (selector ad5f0941, 0.15-0.25 ETH) and 0xf300b2c0… (0xfefe306e's, 0.0099 ETH).
* I did not measure whether these reverts were buy attempts on this curve. It would need traces, and I did not call `debug_trace*`.

## 6. Verdict
1. **Does the E1-first seat pay for the bots that really get it?**
   * **Sep 22-23: no.** Pos-1 realized −11.9% mean / −9.5% median / 27% win (n=64). Including held lots it is −2.7% / −7.8%. Eventual closes were −9.9% / −9.0%. ETH-weighted it is −1.1% to +2.3%, which is break-even for size and a loss per trade.
   * **Sep 18-19: barely.** Realized was +6.1% mean / +1.8% median (n=47), +3.5% ETH-weighted. Eventual closes were +3.8% / +0.3%, +1.7% ETH-weighted.
   * The best-run seat bot, 0x6c56103c, made **+2.0%** (0.047 ETH on 2.4 ETH) and then **+0.08%** (0.0025 ETH on 2.97 ETH).
   * Small-stake bots (under 0.01 ETH) lost −24% on average (A) on Sep 22-23 by holding 20-70 blocks into −55% to −72% dumps.
2. **Does +9.3% survive? No.**
   * On the same 141 launches, the seats' real holders made +3.5% (ETH-weighted, sold) and +1.7% (eventual), with a median of about 0. The model at their stakes says +14.2% mean / **+8.8% median**.
   * The matched-pair gap is −7.0 pts mean / −2.0 median over all seats, and −10.8 / −10.9 over those who sold.
   * The model itself fell to **+1.5%** on Sep 22-23 under the same filter, against a pos-1 A of −2.7% there. The live −0.8% is within the range of these numbers.
3. **Where it breaks.**
   * **Not the entry price and not the fee model.** Both are exact: first curve event 233/233, fee tier + 6.18% in 231/233 (2 were insiders), sells 443/443 exact.
   * **The exit price, through the insertion.** The backtest's "E1 first" puts us in front of the real seat holder and keeps that holder's buy in the tape behind us. The winner's own stake becomes our exit liquidity. This accounts for **+4.6 to +5.4 pts of mean** (+10.8 to +13.2 pts on the 55 seats taken at 0.10-0.50 ETH, where the model's 3% CAP also shrinks our stake below theirs).
   * **The hold.** The bots do not hold 15 blocks: under half close within 100 blocks, and of the sellers only 26/64 (Sep 22-23) and 7/47 (Sep 18-19) exit in 10-20 blocks. The winners' own exit timing, measured against the 15-block rule, costs another **+1.6 to +2.4 pts mean** (+3.5 to +5.1 among sellers). The median effect is about 0, so this is a tail loss.
   * **The regime.** The model's own number fell from +9.3% to +1.5% between Sep 18-19 and Sep 22-23. The seat is worth being in front of the winner, and no one realizes that position.

## Not measured
* 35 pos-1 lots on Sep 22-23 and 19 on Sep 18-19 (bots only) were not fully closed within 6,000 blocks. For those only the curve mark at +15 is available.
* 7 held pos-1 lots in each sample (Sep 18-19 count includes our wallet) were moved by token Transfer to other addresses, and their P&L could not be followed.
* P&L is measured at the Buy/Sell recipient, which is often a bot contract. The bots' reverted attempts, relay costs and other off-curve costs are not included.
* Gas comes from receipts of the buy and sell txs only.
