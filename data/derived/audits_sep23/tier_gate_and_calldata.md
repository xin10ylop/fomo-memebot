# Sep 20 tier refusals: did Pons change something?

**Short answer: no.** The selector, the calldata layout, the factory and the way the tier is encoded were the same on Sep 19, Sep 20 and Sep 23. Word 13 matched the chain's fee on every launch I checked. The 11 refusals on Sep 20 were real 1%-tier launches. In that window, 44 of the 53 bundled launches were 1%-tier, most of them from a few operators who reuse the same wallets. At the same time, 2-3% launches were scarce. Since then, 2-3% launches have come back to their highest level in this data.

All numbers come from the public RPC. Blocks were located by binary search on block timestamps.

| window | blocks | UTC |
|---|---|---|
| A | 66851211-67065503 | Sep 19 06:00-12:00 |
| B | 67957288-68064803 | Sep 20 13:00-16:00 (13:30 = 67975164, 15:00 = 68028931) |
| C | 70216800-70324231 | Sep 23 04:10-07:10 |

## 1. V2F creation logs and calldata

V2F emits one log type only: topic 0xdcacba5e…, 4 topics. There were 1918 logs in A, 1142 in B and 564 in C.

| | A (6 h) | B (3 h) | C (3 h) |
|---|---|---|---|
| V2F creations (per hour) | 1918 (321) | 1142 (381) | 564 (188) |
| selector f85f8e41, `to` = V2F | 1709 (89.1%) | 994 (87.0%) | 493 (87.4%) |
| other selectors (router wrappers, 0x6319141d… etc.) | 209 | 148 | 71 |
| f85f8e41: word 0 = 224 (the struct offset) | 1709/1709 | 994/994 | 493/493 |
| f85f8e41: words per tx (mode) | 38-45 | 38-45 | 38-45 (plus 58) |
| f85f8e41: word 13 > 2000 | 0 | 0 | 0 |
| word 13 = 0 / 100 / 200 / 300 / 150 | 491 / 408 / 451 / 65 / 62 | 267 / 202 / 254 / 80 / 67 | 80 / 87 / 201 / 44 / 16 |
| share with word 13 = 0 | 28.7% | 26.9% | 16.2% |
| share with word 13 in 100-200 | 60.3% | 53.7% | 63.5% |
| quote word = 0 | 1603 | 869 | 440 |
| ≥3 named (address-like words other than the creator) | 335 | 193 | 52 |
| pass the calldata rule (quote 0 and ≥3 named) | 322 (18.8%) | 178 (17.9%) | 40 (8.1%) |

- The mode of address-like words is 2 in every period (word 5 and word 12, both usually the creator).
- The layout has not moved. Word 0 = 224 points to a struct at word 7, and the struct keeps offsets 320/384/448… at words 7-11, an address at word 12, the tax at word 13, 0 at word 14 and a constant at word 15.
- The engine's 335/398 "cannot pass from the calldata" (84%) is the normal rate: 81-82% of f85f8e41 creations fail that rule in A and B.
- CREATE_SELS also lists 3f707e6b. It appeared once: tx 0xa615d02f…, `to` 0x9c450e65…, a wrapper.
- An hourly scan of all 85 hours from Sep 19 12:00 to Sep 23 04:10 found an f85f8e41 share of 71.5-98.3% in every hour. No hour shows a new selector taking over.

## 2. The tier on the chain vs word 13

The Buy event data carries 4 words: gross ETH, tokens, the 1% protocol fee and the token tax. So the chain states each token's tax directly, and I checked word 13 against three chain measures.

| check | A | B | C |
|---|---|---|---|
| launches checked (calldata-eligible + 30 random) | 352 | 208 | 70 |
| Buy-event tax word (creator's buy) = word 13 | 352/352 | 208/208 | 70/70 |
| folded fee of the first non-creator buy **in the creation block**, within 0.08 pp of 1% + word 13 | 9/9 | 9/9 | 1/1 |
| folded fee of the first non-creator buy **in the creation second** (eligible launches) | 101/101 | 84/85 | 8/8 |
| folded fee of the creator's buy, eligible launches | 322/322 | 178/178 | 40/40 |

- Non-creator buys inside the creation block are rare: 19 of 540 eligible launches. The bundle usually lands 1-7 blocks later in the same second, so I also report the creation-second figure.
- **The single mismatch is not a tier error.** It is launch 0xc7907936324b6df57ed349eb02522f32bf6b4beca696c30efcfd1d0b6fa8e26b, with word 13 = 200. Its first outsider buy, 0x94e5632c44430d2b2f2e7a8af4dd5d5cac0110748cc36a0088f0e35b64b3aa12 (0.0396 ETH, block +3), paid 99.0%: that is the creation-second snipe tax. Its Buy-event tax word is 200 bps, the same as word 13.
- **11 of the 630 creator buys give a meaningless folded fee.**
  - 4 are dust buys under 1e-8 ETH, where the fold breaks down.
  - 7 paid an 86-98% effective fee, for example 0x08fa7780… (35.2 ETH).
  - All 11 are outside the eligible set, and the event tax word equals word 13 on all 11.
- **Rule replication check.** My rule gives exactly the same 22 qualifying launches in A as `src/analysis/e1_multi.py`'s `data/derived/e1_sep1819/e1m_last12.json` (22/22 curves).

## 3. Another factory?

Buy events chain-wide, blocks 70326870-70329870 (Sep 23 07:15-07:20): 706 Buy events on 73 curves.

- **V2F created 56 of the 73 curves:** 36 of them in the previous 20000 blocks, 20 earlier (found by a topic-filtered search of all of V2F's history).
- **The other 17 were all created by 0x7ed598bcef8bd9edd8c97a195c6d13f40801ec7e**, event 0x8d4aad49 with topics [token, curve, creator].
  - This is the core deployer under V2F. Every V2F creation receipt also contains this event, for example tx 0xba09498a….
  - The 17 are core launches made without V2F: called directly (selectors a72101af / f35abbcf), or through other routers (0x526a8be4… 6864efc9, 0x1a66d8ec… 56a5d543, 0x38e85543… 1ba34035, ERC-4337 entry points).
  - Their creation blocks run from 62614168 to 70328633, so they are not new.
- **The Pons creation event 0xdcacba5e is emitted only by V2F:** 153 logs over the 23000 blocks.
- **V2F's share of all core creations has not changed:**

| | A | B | C |
|---|---|---|---|
| V2F / core creations | 1918/2659 = 72.1% | 1142/1472 = 77.6% | 564/779 = 72.4% |
| core called directly (a72101af + f35abbcf) | 656 | 281 | 184 |

- Non-V2F curves carried 55 of the 706 Buy events (7.8%).
- **No new factory.**

## 4. What changed, when, and how many launches qualify

### What changed
- **Nothing in Pons.** The launch mix changed:

| | bundled launches (quote 0, ≥3 named, ≥0.3 ETH at the tier fee in the creation second) | 1%-tier (word 13 = 0) | 2-3% tier |
|---|---|---|---|
| A, Sep 19 06-12 | 33 | 11 (33%) | 22 |
| B, Sep 20 13-16 | 53 | 44 (83%) | 7 |
| Sep 20 13:30-15:00 (the engine's window) | 20 | 17 | 3 |

- **In the engine's window**, the chain shows 577 V2F creations: 491 f85f8e41 creations sent directly to V2F, and 68 that pass the calldata rule.
- **Who made the 44 tier-0 launches in B.** At least 38 come from about 6 operators who reuse the same wallets:
  - 9 from creator 0xd9cbc515cbcb8b2f11d7394e0cf67e819f840b48, always with the same 3 named wallets (0xf6e1f5ee…, 0x108bfeca…, 0x7784e766…). It also made 7 tier-0 launches in A.
  - 3 from 0x698352695b9f3e82ebcbdc6cdd9c4457e0fbf681.
  - About 27 from 4-5 clusters that use a fresh creator each time but recycle 13-29 named wallets. 151 named wallets appear in at least 2 bundled launches in B.
  - Wallet activity by cluster: 0x206ea449… Sep 19 19:19 → Sep 20 15:55; 0x9581719b… Sep 19 19:34 → Sep 20 15:00; 0x93f11a03… Sep 20 02:17 → 14:56; 0xc572ed85… Sep 20 15:21 → 16:05.
- **The chain fee of these launches is 1.00%** (event tax word 0). Example: 0xe17a4f117824d5cf92453fb144879111cedee911a839265acfc76a14a529a782, block 68004352, 13 named wallets, 0.853 ETH bundle.

### When
- **There is no protocol change to date.** The first tier-0 bundled launch in my data was at Sep 19 09:39:28, block 66981803, tx 0x3c7a839e58ea64aff262dddb965c4e8155242beca0ddc0594043f1e775ced02d (creator 0xd9cbc515…).
- **Share of tier-0 among bundled launches, per 24 hours:**

| 24 h window | tier-0 share of bundled launches |
|---|---|
| Sep 19 12:00 → Sep 20 12:00 | 270/401 = 67% |
| Sep 20 12:00 → Sep 21 12:00 | 261/349 = 75% |
| Sep 21 12:00 → Sep 22 12:00 | 272/458 = 59% |
| last 24 h | 168/357 = 47% |

- **Sep 20 13-16 was a low point for 2-3% launches, not a new regime.** Qualifying launches in the same clock hours (13:00-16:00 UTC) on each day:

| day | qualifying launches, 13:00-16:00 UTC |
|---|---|
| Sep 19 | 16 |
| **Sep 20** | **7** |
| Sep 21 | 27 |
| Sep 22 | 31 |

### Qualifying launches per hour
The rules: f85f8e41, quote 0, ≥3 named, word 13 in 100-200, bundle ≥0.3 ETH at the tier fee in the creation second.

| window | qualifying | per hour |
|---|---|---|
| Sep 19 06-12 (reference) | 22 | 3.7 |
| 24 h Sep 19 12:00 → Sep 20 12:00 | 107 | 4.5 |
| 24 h Sep 20 12:00 → Sep 21 12:00 | 70 | 2.9 |
| 24 h Sep 21 12:00 → Sep 22 12:00 | 152 | 6.3 |
| **last 24 h, Sep 22 07:10 → Sep 23 07:10** | **170** | **7.1** |
| Sep 20 13-16 (the refusal window) | 7 | 2.3 |
| last 3 h, Sep 23 04:10-07:10 | 4 | 1.3 |

- The last 3 hours are the quiet hours. The same hours, 04-07 UTC, gave 3 on Sep 20, 6 on Sep 21 and 4 on Sep 22.
- The last 3 hours' qualifying launches: 0x80c410612a784e2fdd0aeac797ff615fa8fcb8f1b81eca0f04d03def5ef53ccd (150 bps), 0x398c9687be9f7622d7e4cc3ec71d93b6bfb0802f5a69669e0dad3ee8b920fe02 (200), 0xc60988cb00f187cd4fe4e45ac68b0e337d27847f18980cd8171371e220b54687 (200), 0xc3a61711c67af17077cbf9694d9c99b72e4d46c386e0f37b65316fe668d8527e (100).
- **Busiest hours** (US hours, Sep 22 13:00-22:00 UTC): 5-20 per hour, for example 20 in the 20:08 hour and 17 in the 17:08 hour.
- The full hourly table is in hourly.json.

### Parser
- **The current `tax_bps_of` is correct. No selector change is needed.**
- Optional hardening: read the tax through the struct offset in word 0 instead of a fixed index. It gives identical output on all 3196 f85f8e41 creations in A, B and C. The code is in parser_proposal.py and was not applied:

```python
def tax_bps_of(sel, words):
    """the token's own tax in basis points, from the creation calldata of selector f85f8e41: field 6 of the launch struct whose
    offset is word 0 (always 0xe0 = 224 so far, i.e. the struct head starts at word 7 and the tax is word 13). 0 = the 1% tier,
    100 = 2%, 200 = 3%. Matched the Buy event's tax word on 630 of 630 launches Sep 19-23. None for another selector or layout:
    the gates then fail closed."""
    if sel.hex() != "f85f8e41" or len(words) < 14:
        return None
    off = int.from_bytes(words[0], "big")
    if off % 32 or not 7 <= off // 32 <= len(words) - 7:
        return None
    v = int.from_bytes(words[off // 32 + 6], "big")
    return v if v <= 2000 else None
```

## Leads on the engine side (not Pons)

1. **Three 2%-tier launches that qualify were not among the engine's 11 in its window:**
   - 0x5a828cd2456b5bb3ec367d955dba97518053a9e018812fddc01c17561ff942fb (14:11:28, block 67999930, creator 0x095ec4e4701b7a5b862d9a651b7e46da73980870, 4 named, 0.605 ETH)
   - 0xbc403b6a1af463638d5df10d2376793fb07faab624bbb72f4a3e922745b21cf8 (14:37:28, block 68015483, creator 0xb552d9106f6b226d8a61a871407bcdc78ef23854, 3 named, 0.530 ETH)
   - 0x0c73a27a71936e8e2e206e1b447593d16b0ca07bb7deea14e40b04d301519b4e (14:48:28, block 68022048, creator 0x2175e05497cc8e2da8f98fbce3293ae83d32cc03, 3 named, 0.542 ETH)

   All three have word 13 = 200, a chain fee of 3.00%, and a creator buy of at least 2% of supply. Search the engine log for these creators.
2. **The chain had 491 direct f85f8e41 creations from 13:30:00 to 14:59:59, against the 398 the engine logged.** If the engine's window really was 13:30-15:00, the feed missed 93 creations (19%). The log's exact first and last timestamps are needed to confirm this.
3. **Known blind spot, not new: wrapped creations.**
   - These are f85f8e41 calls embedded in router calls: 199 in A, 135 in B, 60 in C (7-10% of V2F creations).
   - The feed path cannot see them (`to` is not V2F), and the provider path skips them ("unknown selector").
   - They qualify rarely: 3 in A (6 h), 0 in B, 0 in C.

## Files (this directory)

- `findings.md` (this file)
- `blocks.json`: the window blocks
- `period_tables.json`: the step 1 tables
- `creations_parsed.json`: every creation's selector, words, word 13, quote and named count
- `v2f_logs.json`: the raw V2F logs
- `txcache.json`: the raw transactions
- `tiers_raw.json`: the curve Buy and Sell events per launch
- `tiers_analysis.json`: the per-launch chain tier vs word 13 and the bundles
- `bundled_list.txt`
- `factory_check.json`, `factory_check2.json`, `core_share.json`: step 3
- `farm_wallet_activity.json`
- `wrapped_creations.json`
- `timeline.json`, `hourly.json`: hour by hour, Sep 19 06:00 → Sep 23 07:10
- `parser_proposal.py`
- Scripts: `rpc.py`, `logs.py`, `txs.py`, `parse.py`, `tiers.py`, `analyze.py`, `factory.py`, `core.py`, `core2.py`, `wrapped.py`, `timeline.py`
