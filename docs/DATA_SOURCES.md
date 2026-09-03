# Data sources (discovered 2026-09-03)

| Source | What | Access | Limits |
|---|---|---|---|
| fomoapi.io (`api.fomoapi.io`) | Mirrors the fomo app live: leaderboards (24h/7d/30d/all, top 100), per-trader trades (open + last ~25 closed), balances, token holders, theses, realtime app feed (WebSocket `/ws/alerts`) | `authorization: Bearer fapi_…` (the "third-party fomo API key") | Free plan: 10,000 req/month, 60 req/min, 25 wallet resolutions/month (`/v2/users/{handle}` only). |
| fomoscope.xyz | Older mirror of fomo leaderboards/positions/events. Stale (events stopped 2026-09-02), leaderboard rows contain bugged PnL (9e19). Low value. | free, per-IP | 30 req/min |
| fomoscan.sh | Identity API (handle -> wallets). Not our key. | `fsk_live_…` | n/a |
| fomo.family web app | Landing + profile/clan/coin routes. No public leaderboard route; data endpoints (`prod-api.fomo.family`) need a Privy login token. | browser (needs `--ssl-version-max=tls1.2` in this sandbox) | n/a |
| Helius RPC | Solana on-chain history for traders' Solana wallets | api-key | 850k credits (1 credit per RPC call, 100 per enhanced-tx page) |
| Robinhood Chain public RPC `rpc.mainnet.chain.robinhood.com` | EVM chain 4663 where most fomo flow is now (Pons launchpad) | none | unknown |
| GeckoTerminal | Minute OHLCV for Solana and Robinhood pools (1000 candles/page, `before_timestamp` paging, >=30 days back) | none | ~30 req/min |
| DexScreener | Pair metadata / current stats incl. robinhood chain | none | ~300 req/min |
