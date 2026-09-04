import json,collections,datetime,statistics as st,os,time
REPO='/home/user/fomo-memebot'
tok=json.load(open(f'{REPO}/data/derived/token_metrics.json')); tr=json.load(open(f'{REPO}/data/derived/trader_entry_metrics.json'))
hs=json.load(open('fapi/holders_series.json')); creators=json.load(open('rh/creators/creators.json'))
outcomes=open('entry_outcomes.txt').read()
def dt(ts): return datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M') if ts else ''
def m(x): 
    if x is None: return ''
    return f"${x/1e9:.1f}B" if abs(x)>=1e9 else (f"${x/1e6:.1f}M" if abs(x)>=1e6 else (f"${x/1e3:.0f}k" if abs(x)>=1e3 else f"${x:.0f}"))
def age(mins):
    if mins is None: return ''
    if mins<60: return f"{mins:.0f}m"
    if mins<1440: return f"{mins/60:.1f}h"
    return f"{mins/1440:.1f}d"
dep_count=collections.Counter(v.get('deployer') for v in creators.values() if v.get('deployer'))
memes=[t for t in tok.values() if t.get('category')=='meme' and not t.get('anomaly')]
memes.sort(key=lambda t:(-t['traders'],t['symbol']))
now=time.time()
L=[]
L.append("# Memecoin fundamentals per token and per trader\n")
L.append(f"Generated {datetime.datetime.utcnow():%Y-%m-%d %H:%M} UTC from `data/derived/token_metrics.json`, `data/derived/trader_entry_metrics.json`, `data/derived/entry_outcomes.json`.\n")
L.append("""This answers "at what market cap, how old, on which launchpad, with which holders and which dev did each leaderboard trader enter?", for every meme in `docs/MEMES.md` and every priced entry in `data/derived/positions_all.csv.gz` (columns `entry_fdv_usd`, `age_at_entry_min`, `launchpad`, `token_created`, `trader_is_dev`, `fdv_now`).

**Definitions and sources**

* **Entry FDV** = entry price × total supply. Entry price is fomo's `avgEntryPrice` for app positions, or fill USD ÷ amount for on-chain fills (Robinhood fills priced from GeckoTerminal candles at the block time, Solana fills from the USDC/SOL leg). Supply from GeckoTerminal (`total_supply`), else DexScreener FDV ÷ price. Tokens with no supply (dead, no pool anywhere) are the `unknown` bucket: that bucket is where most Solana losers live, so every "known FDV" number is survivor-biased upward.
* **Token created** = Robinhood mint block (first Transfer from 0x0, timestamp interpolated from block anchors), else DexScreener `pairCreatedAt`, else the earliest GeckoTerminal base pool. A DexScreener/GT pool can post-date the token, which is why a few entries show negative age (`before pool (data err)`).
* **Launchpad**: Solana by mint suffix (`pump`, `bonk`, `BAGS`); Robinhood by the mint-tx factory, characterised from the pools it produced: `0xa5aa…` = Pons V1 (v3 WETH pools, Jul 13 → Aug 30), `0xe33e…` = Pons V2 (v4 hook curve, native-ETH quote, from Aug 5), `0x22e9…` = LONG (v4 pools quoted in stock tokens; AI, BONER, MOO, AGI), `0xd9ec…` = the pre-Pons v3 factory (Jun 19 → Jul 11; CASHCAT, TENDIES, JUGGERNAUT), `0x7ed5…`, `0x5bd1…` (other v4 launchpads), `0x2660…` (v2 pools), EntryPoint = launched from the fomo app; then the DexScreener pool label and the quote asset for tokens with no mint tx found.
* **Dev**: Robinhood deployer = `from` of the mint transaction, replaced by the ERC-4337 `UserOperationEvent` sender (the user's smart-account wallet) when the mint went through the EntryPoint, i.e. a launch from the fomo app; `fee_recipient` = Pons locker `feeRedirects(token)` (returned zero for every token checked, so creator-fee redirection is not readable this way). fomoapi's holders and theses endpoints carry an `isDev` flag: false on every tracked holder row, true for the thesis author on 3 tokens. Solana creators were not resolved (pump.fun creator lives in the bonding-curve account; not pulled to save Helius credits).
* **Holders**: fomo's token boards (trending / most-held / graduated, 30-minute snapshots) give a total holder count and `fomoBuyers` for the ~60 tokens that make those boards; `/token/{address}/holders` gives the top-50 fomo-tracked holders (amount, cost basis, PnL) for the 160 most-traded memes. There is no cheap full holder count for the long tail (Blockscout is gated on Robinhood Chain); on-chain holder reconstruction was not done.
""")
# ---- outcome section
L.append("## Does entry market cap / age / launchpad predict the leaders' results?\n")
L.append("""One row per (trader, token) with a fully priced on-chain history (every buy and sell priced), meme tokens only, ≥ $20 invested. `cons` = realized proceeds − invested with any remaining bag at zero; `mtm` = remaining bag at today's DexScreener price (no impact, no liquidity check: this is the fomo-leaderboard way of counting). CI = 95% token-clustered bootstrap of the pooled conservative ROI. Read the `unknown` FDV row as the dead-token row.

```
"""+outcomes.strip()+"""
```

What this says:

* **The leaders are not early snipers.** By dollars, three quarters of their priced meme entries are at FDV above $10M and two thirds are in tokens older than seven days. Sub-$1M entries are a rounding error of their capital (≈ $1.6M of $59M) even though they are a quarter of their positions by count.
* **No entry-FDV bucket has a significantly positive realized (bag-at-zero) return.** The only bucket with a clearly non-zero pooled result is > $100M entries at −29% [−49%, −14%]: buying the mega-caps late lost money. Everything green is in the `mtm` column, i.e. unsold bags marked at the last price.
* **Age**: the < 1h bucket is small (46 positions, 21 tokens) and its CI spans zero; 1h–24h entries are negative after the bag-at-zero rule. Older-than-7-days entries are where the capital is, and they are flat realized / huge mark-to-market: the leaderboard PnL is a bag-holding phenomenon, not an entry-timing one.
* **Launchpad**: pump.fun and Solana/other are the loss-making venues on a realized basis (−10% and −21% with CIs excluding zero). The Robinhood venues where the capital sits are flat-to-negative realized and enormous marked: the pre-Pons v3 factory tokens (CASHCAT, TENDIES, JUGGERNAUT…; $18.8M invested, −14% realized, +407% marked), Pons V1 (−8% realized, +1193% marked, 7 tokens) and LONG stock-paired launches (+45% realized with a CI of −84%…+54% on 14 tokens, +2054% marked). Pons V2 curve launches, the current retail venue, are −33% realized.
* **Holder count** (today's fomo board count, hindsight): the ≥ 10k-holder tokens are the same 10 crowd tokens; their realized ROI is +0.7%. Being in the crowd token did not pay in cash; it paid on paper.
* **Dev involvement**: fomoapi's `isDev` flag is false on every tracked holder row; on the theses it marks a dev for 3 of 116 tokens with theses (FIRE, STONKBROKER, NASDANQ), none of them leaderboard handles. On-chain (mint-tx deployer, or the ERC-4337 userOp sender for the 38 tokens launched through the fomo app), exactly one traded meme was deployed by a leaderboard wallet (SANDIH by LehmanFarters). Serial deployers do exist in the traded set: one wallet deployed 17 of the memes the leaderboard traded, seven wallets deployed 30–54 of the 2,865 Robinhood tokens the leaderboard touched (per-token `deployer (n)` column).
""")
# ---- per trader
L.append("## Per trader: where they enter\n")
L.append("Median / interquartile entry FDV of priced meme entries (app positions + on-chain buys), share of entries below $1M and above $10M FDV, median token age at entry, share within 1h of creation and older than 7 days, main launchpads, tokens where the trader's EVM wallet deployed the token.\n")
L.append("| handle | class | entries | tokens | entry FDV median (p25–p75) | <$1M | >$10M | age median | <1h | >7d | launchpads | dev tokens |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
for h,v in sorted(tr.items(),key=lambda kv:-kv[1]['entries_priced']):
    lp=', '.join(f"{k.split(' (')[0]} {n}" for k,n in v['launchpads'].items())
    u1h='' if v['pct_under_1h'] is None else f"{v['pct_under_1h']:.0f}%"; o7d='' if v['pct_over_7d'] is None else f"{v['pct_over_7d']:.0f}%"
    L.append(f"| {h} | {v.get('class') or ''} | {v['entries_priced']} | {v['tokens']} | {m(v['entry_fdv_median'])} ({m(v['entry_fdv_p25'])}–{m(v['entry_fdv_p75'])}) | {v['pct_under_1m']:.0f}% | {v['pct_over_10m']:.0f}% | {age(v['age_median_min'])} | {u1h} | {o7d} | {lp} | {', '.join(v['dev_tokens']) or ''} |")
# ---- per token
L.append("\n## Per meme: fundamentals\n")
L.append("Memes with ≥ 2 leaderboard traders, ordered by number of leaderboard traders. `holders` = fomo board total holder count (blank = token never made a board); `tracked/lb` = fomo-tracked top holders / leaderboard handles among them; `top10%` = share of supply held by the 10 largest tracked holders; `deployer (n)` = mint-tx sender and how many traded tokens it deployed; `lb entry FDV` = median entry FDV of leaderboard entries; `first lb entry` = age of the token at the first leaderboard entry.\n")
L.append("| symbol | chain | launchpad | created | FDV now | liq | holders | tracked/lb | top10% | deployer (n) | lb traders | entries | lb entry FDV (min) | first lb entry | <$1M |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for t in memes:
    if t['traders']<2: continue
    b=hs.get(t['address']) or {}
    dep=t.get('deployer'); depS=f"{dep[:6]}…{dep[-4:]} ({dep_count.get(dep,0)})" if dep else ''
    if t.get('deployer_handle'): depS=f"**{t['deployer_handle']}** "+depS
    if t.get('dev_handles_thesis'): depS=(depS+' ' if depS else '')+'dev-thesis: '+', '.join(t['dev_handles_thesis'])
    trk=f"{t['tracked_holders']}/{t['lb_holders']}" if t.get('tracked_holders') else ''
    top10=f"{t['top10_tracked_pct_supply']:.0f}%" if t.get('tracked_holders') and t.get('top10_tracked_pct_supply') is not None else ''
    L.append(f"| {t['symbol']} | {t['chain']} | {t['launchpad']} | {dt(t['created'])} | {m(t['fdv'])} | {m(t['liq'])} | {b.get('holders_last') or ''} | {trk} | {top10} | {depS} | {t['traders']} | {t['n_entries_priced']} | {m(t.get('entry_fdv_median'))} ({m(t.get('entry_fdv_min'))}) | {age(t.get('first_lb_entry_age_min'))} | {('%.0f%%'%t['pct_entries_under_1m']) if t.get('pct_entries_under_1m') is not None else ''} |")
open(f'{REPO}/docs/TOKEN_METRICS.md','w').write('\n'.join(L)+'\n')
print('written',len(L),'lines; memes listed',sum(1 for t in memes if t['traders']>=2))
