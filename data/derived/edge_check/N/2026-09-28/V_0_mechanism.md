# V_0 (mechanism lens): engine 6.8 (`aa0f85a`, unchanged at `f38556f`) against 6.7 (`34265b9`), Sep 28

Scripts:
- `V_0_mechanism_check.py` / `.txt` is the cut-off run. It reads the gates at the block where the bundle wait first passes.
- `V_0_mechanism_q.py` / `.txt` is this run. It joins the B/D tapes (every Buy event, its fee as `e1_multi.py` computes it) to the crowd rows (each transaction as the engine sees it) and to D's values. It folds both engines' own `watch_curve` at **every** read offset from 0 to k, on all 518 launches past the pre-gates (392 of them have a tape).

Nothing under `src/` or `tests/` was modified. Nothing was committed.

**Verdict: not refuted.** The bundle half matches the tables and has no side effect on the week. The nonce half fixes no observed skip, and its stated premise is false for two send paths. Its harm is bounded, so it goes to the follow-ups.

## Q1. What 6.8 counts, against e1_multi's exempt rule (`V_0_mechanism_q.txt`, Q1)
Removing the close changes no classification. It only lets the engine keep counting after the first outsider.

Everything 6.8 adds is table-exempt. Over 392 launches, that is 351 transactions after 6.7's close carrying 17.112 ETH, which produced 413 Buy events. All 413 are exempt, totalling 17.112 ETH. None is taxed and none reverted. By category:

| category | what 6.8 adds after the close | tables |
|---|---|---|
| named direct | 26 txs, 1.216 ETH | 26/26 exempt |
| named sender through a helper | 320 txs, 10.375 ETH | 320/320 exempt |
| helper naming its buyers in calldata | 5 txs, 5.521 ETH, 67 buys | all exempt |
| creator direct | 0 on the week | |
| taxed helper `4d819a2a` | 0 named uses (all calls with this selector came from outsiders, so they count as outsider calls) | |
| outsider | never counted, by 6.7 or by 6.8 | never exempt |

On the outsider row:
- 68 direct calls: 65 reverted, and 3 were taxed buys worth 0.031 ETH.
- 4,483 value-carrying calls: none bought in the creation second.

Pre-existing differences, not 6.8's:
- One named direct buy reverted. The engine counts its value anyway.
- Helper call values total 322.8 ETH, against 290.8 ETH of exempt buys (see Q3).
- 13 launches have 61 exempt buys (6.32 ETH) in transactions that neither target nor name the curve. The crowd reconstruction cannot see them. The replay also refuses all 13 ("bundle 0/2 < 3"), and 12 of the 13 have at most 1 fleet.

k ≤ 9 on every launch, so the engine's 9-block window always covers the creation second.

## Q2. Was the close protecting anything?
**Monotone.** Without the close, the count and the ETH can only grow; this was asserted on every (launch, offset) pair. So the count gate and the 0.3 floor can only be newly passed. The 3.0 cap is the only gate 6.8 can newly fail.

**At every offset** (`q.txt`, Q2):
- 6.8 admits where 6.7 refused: 118 pairs on 25 launches.
- 6.8 refuses where 6.7 admitted: **0**.
- On the 6 launches 6.7 counted only partly, 6.8's ETH equals the tables' exempt ETH exactly: 1.101, 1.000, 0.589, 0.531, 0.411 and 0.368. The nearest to the cap is 1.9 ETH below it.
- The largest 6.8 bundle among the newly admitted launches is 1.776 ETH (`0xba059c17`, which is also the tables' figure).
- This confirms the check's "refuses 0". No launch can newly cross 0.3 or 3.0 because of the change.

**Tier and crowd gate.**
- Tier comes from the calldata and is untouched.
- `note_attack` and the rival record in `fold_buy` are unchanged; the diff removes only the flag.

**One position.** No "position open" rows appear at the usual view on the week (`rows_k1reg`), so no added fire blocked another launch.

**Contested launch? No evidence.** The closers are rivals' early shots, not buys.
- `0x8191c327` (`cce7ec13` via `0xbd7c6f67`) is the closer in 16–17 of the added launches. It made 188 calls in the creation second across 22 launches, and none bought. In the seat block, 20 of its 34 calls bought. It is an E1 sniper, which is crowd, and the fleets gate already counts it on its own.
- A taxed stranger's buy ahead of the team's third exempt buy happened on 0 of 392 launches.
- A stranger's direct call ahead of the team happened on 3 launches. Their mean model return at h11 is -2.6%, against +1.8% on the other 389.
- Under a looser definition (a direct call anywhere before the team's third counted call) there are 38 launches with mean +5.3%, including 20 fires worth +$23.46.

## Q3. The 12 "ETH > 3.0" launches (e.g. 15.478 against 4.233)
This is not a close matter: 6.7 and 6.8 give identical counts on all 12.

The cause is that the engine takes a helper call's ETH to be the call's value, while the tables take the ETH its Buy events spent. On the 12 launches, the helper calls carried 81.085 ETH and their Buy events spent 47.656 ETH, all exempt (`q.txt`, Q3). So the difference comes from the value field. The engine is not counting anything the tables call non-exempt.

It changes no decision on the week:
- All 12 are above 3.0 on the tables' own ETH (the lowest is 3.125), and the replay refuses all 12 at the cap. The check's heading "while the replay's bundle gates pass" is wrong.
- Reading both at k-1 with real values on 385 launches, 374 fall on the same side of 0.3 and 3.0. The other 11 are the 10 launches with invisible helpers from Q1 (which the replay refuses too) and one timing artifact with 0 fleets.

It is a separate follow-up, not something 6.8 should have fixed.

## Q4. The nonce half
**The observed skip.** At 19:44:59 the gate refused on `nonce is None` after `release_reservation()` (line 1668). That happens whether the window is 30 s or 60 s. The poll had not failed, so the 2 s retry never ran. 6.8 does nothing for this skip, yet runbook 5z still files the 60 s change under "(19:44:59)".

**Is the 60 s window safe? Not fully.** The claim "our own sends advance the nonce locally" holds only for the trade reservation (line 1963). `shooter_topup` (line 1635) and `relay_topup` (line 1656) send from WALLET at `next_nonce()` and never write `state["nonce"]`.
- `shooter_topup` runs inside `chain_loop`, after the poll. It waits up to 5 s for each receipt. A slow top-up is therefore exactly the stall that ages `chain_at` past 30 s, and during it `state["nonce"]` falls behind by the number of transfers sent.
- 6.7 refused launches once that stall passed 30 s. 6.8 admits them until 60 s, on a nonce it knows is stale.

**The consequence is bounded.**
- Shooters are live, so the burst uses the shooters' own nonces.
- The stale WALLET nonce is used only for the approve (line 2154). That approve gets "nonce too low".
- `ensure_approved` (line 1521) then re-sends it at a fresh nonce: a 1 s receipt wait, an allowance read, then up to 1.5 s for the new approve to confirm. The sell leaves about 1.5–2.5 s late on an 11-block hold. No position is lost.
- 6.7 already had the same exposure for about 10 s after every top-up and after every exit's `relay_topup`. 6.8 widens only the slow top-up case.
- How often such stalls happen cannot be measured from disk.

**The 2 s retry.**
- `failed` is set by any exception in the pass, not only by the nonce/gas read, and `n` advances on every retry.
- So during a failure streak the loop runs 5× as often. That includes the relay read on every second pass and the 70-call shooter refresh on every hundredth.
- That is the provider quota that set `CHAIN_POLL_S=10` on Sep 27. This is hygiene.

## Q5. The diff beyond the description
The source change is only the 16 lines described. Remaining hygiene:
- The `not w.get("bundle_closed")` reads remain; they are dead code and always true.
- The new test asserts the flag is absent, not the 12:52 order through `watch_curve`. Its last check does fail on 6.7 and pass on 6.8.
- The test's docstring still blames `0xd43ed726` on the 6.5 ordering bug.
- The commit also carried `R2/run_replay.py`.

Tests:
- Run as scripts, both pass on 6.8: 6/6 and 37/37.
- The pytest command as briefed does not work here. The system Python has no pytest. The uv-installed pytest, given the system site-packages, collects 0 tests because the files are scripts. Run together, `test_e0_wait` fails 9 checks because the two files import `sniper_engine` into one process with different environments. Run alone, it exits 0. This is the harness, not 6.8.

## Follow-ups (6.9, none blocking)
1. Make `shooter_topup` and `relay_topup` advance `state["nonce"]` under the lock, or set `chain_at = 0` after any WALLET send. Otherwise put the gate back to 30 s, since 60 s fixes nothing observed. Correct the 6.8 comment and the wording in runbook 5z.
2. Wake `chain_loop` at `release_reservation`. That is the real 19:44:59 path.
3. Give the retry a bounded backoff, and do not advance `n` on a failed pass.
4. Drop the dead `bundle_closed` reads. Add a `watch_curve` test of the 12:52 order (a stranger's value call at ix 3 ahead of the helper's buys in the same block).
5. In the morning reading, besides the log condition "no `bundle N < 3` with ≥ 3 exempt buyers", count `approve_missing` and `approve_not_seen` within 60 s of a `shooter_topup` line. Those would be the stale-nonce path.
