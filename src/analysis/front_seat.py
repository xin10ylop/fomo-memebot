"""the front of second one, dissected: (a) when the first outsider lands in second one, (b) when the team's own exempt
second-one buys land, (c) what the seat pays as a function of how fast we land, (d) its tail. Rows carry no sender, so
'team' = a plain-tax buy in second one (exempt wallets), 'outsider' = a buy carrying the 6.18% surcharge."""
import os, statistics as st, random, collections
exec(open("/home/user/fomo-memebot/src/analysis/indep_replay.py").read().split("recs = []")[0])
def ci(xs, n=600):
    random.seed(3); b = sorted(st.mean(random.choice(xs) for _ in xs) for _ in range(n)); return b[int(0.025*n)], b[int(0.975*n)]
for pname, pf in (("NEW Sep 16-17", lambda d: d >= "2026-09-16"), ("Sep 12-15", lambda d: "2026-09-12" <= d <= "2026-09-15")):
    Ls = [L for (d, w), dd in data.items() if pf(d) for cv, (L, f) in dd.items()]
    first_out, team_first, team_eth, team_n = [], [], [], 0
    for L in Ls:
        tier = L["tier"]; pos = L["ts"] % 1.0; b1 = 1.0 - pos
        s1 = [r for r in L["rows"][1:] if r[1] == "B" and b1 <= r[0] < b1 + 1.0]
        outs = [r for r in s1 if 0.05 <= r[5] - tier <= 0.075]; team = [r for r in s1 if r[5] - tier <= 0.0008]
        if outs: first_out.append(outs[0][0] - b1)
        if team: team_first.append(team[0][0] - b1); team_eth.append(sum(r[2] for r in team)); team_n += 1
    print(f"\n=== {pname}: {len(Ls)} bundled launches")
    print(f"(a) first OUTSIDER buy in second one: on {len(first_out)} launches; lands at median {1000*st.median(first_out):.0f} ms, 25th pct {1000*sorted(first_out)[len(first_out)//4]:.0f} ms, 10th pct {1000*sorted(first_out)[len(first_out)//10]:.0f} ms after the second opens")
    print(f"(b) the TEAM buys in second one on {team_n} launches ({100*team_n/len(Ls):.0f}%): first team buy at median {1000*st.median(team_first):.0f} ms; team puts a median {st.median(team_eth):.3f} ETH into second one")
    print(f"(c) the seat's return by how fast we land in second one (ahead of everything that lands later), $25, hold 2 s, take-profit +50%:")
    print(f"    {'land at':>8s} {'ALL mean':>9s} {'95%':>17s} {'median':>7s} {'win':>5s} {'worst':>7s} {'<-30%':>6s} | {'clean-s1':>9s} {'crowded':>8s} {'>=3 bots':>8s}")
    for ms in (0, 30, 60, 100, 150, 200, 300):
        res = [(sim(L, "E1", stake_usd=25, wait=ms/1000, hold=2.0, tp=0.5)["roi"], feats(L)) for L in Ls]
        a = [r for r, g in res]; lo, hi = ci(a)
        cl = [r for r, g in res if g["out1"] == 0]; cr = [r for r, g in res if g["out1"] > 0]; b3 = [r for r, g in res if g["out1"] >= 3]
        print(f"    {ms:6d}ms {100*st.mean(a):+8.1f}% [{100*lo:+6.1f}%,{100*hi:+6.1f}%] {100*st.median(a):+6.1f}% {100*sum(x>0 for x in a)/len(a):4.0f}% {100*min(a):+6.0f}% {100*sum(x<-0.3 for x in a)/len(a):5.1f}% | {100*st.mean(cl) if cl else 0:+8.1f}% {100*st.mean(cr) if cr else 0:+7.1f}% {100*st.mean(b3) if b3 else 0:+7.1f}%")
    # (d) the same seat but entering only AFTER the team's second-one buys (if the team lands at the flip, this is what is reachable)
    res = []
    for L in Ls:
        tier = L["tier"]; pos = L["ts"] % 1.0; b1 = 1.0 - pos
        team = [r for r in L["rows"][1:] if r[1] == "B" and b1 <= r[0] < b1 + 1.0 and r[5] - tier <= 0.0008]
        t_after_team = (team[-1][0] - b1 + 0.001) if team else 0.0
        res.append(sim(L, "E1", stake_usd=25, wait=max(0.0, t_after_team), hold=2.0, tp=0.5)["roi"])
    lo, hi = ci(res)
    print(f"(d) if the team's second-one buys always land before us (we enter right after the last of them): mean {100*st.mean(res):+.1f}% [{100*lo:+.1f}%, {100*hi:+.1f}%], win {100*sum(x>0 for x in res)/len(res):.0f}%")
