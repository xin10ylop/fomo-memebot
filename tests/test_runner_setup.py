"""6.26 (runbook 5bk): deploy/runner_setup.sh's file handling, run against fake env files (no root, no systemd, no network):
upgrade rewrites runner.env from the template keeping the wallet, the key and the books, drops a copied sniper provider key, copies
the box's timing calibration from the sniper's env, removes keys the template no longer has, leaves no placeholder and keeps every
file 0600 with a backup; base refuses to overwrite a recorded base and adds a later deposit; the guards in dry/live are present."""
import os, subprocess, tempfile, stat
checks = 0
def ok(cond, what):
    global checks
    if not cond: raise SystemExit("FAIL " + what)
    checks += 1; print("ok  ", what)
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); T = tempfile.mkdtemp()
open(f"{T}/engine.env", "w").write("SEND_MODULE=/etc/sniper/send_step.py\nPRIVATE_KEY=0xsniper\nWALLET=0xE0686DC72b04c12CeEFeea75E286E4Ef7C056f01\nFEED_URL=wss://feed.example\n"
    "RPC_URL=https://provider.invalid/v2/SNIPER\nLOGS_RPC_URL=https://logs.example\nSEQ_URL=https://seq.example\nSLOT_SEND=1\nSLOT_LEAD_MS=50\nFEED_LAG_MS=85\nMARGIN_MS=0\n")
KEY = "0x" + "11" * 32
open(f"{T}/runner.env", "w").write(f"SEND_MODULE=\nPRIVATE_KEY={KEY}\nWALLET=0x4c662C38729dB298730c80fae8736621bc536B9a\nRPC_URL=https://provider.invalid/v2/SNIPER\n"
    "BURST_N=1\nMARGIN_MS=60\nGAS_HEADROOM=2.0\nPNL_BASE=0.011100\nPNL_WITHDRAWN=0\n")
for f in ("engine.env", "runner.env"): os.chmod(f"{T}/{f}", 0o600)
s = open(f"{R}/deploy/runner_setup.sh").read()
s = s.replace("ENV=/etc/sniper/runner.env; SRC=/etc/sniper/engine.env", f"ENV={T}/runner.env; SRC={T}/engine.env")
s = s.replace('[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }', "true")
s = s.replace('  active runner-engine && { echo "runner-engine is running: sudo systemctl stop runner-engine runner-notify first"; exit 1; }\n', "")
s = s.replace('TPL="$REPO/deploy/runner.env.template"', f'TPL="{R}/deploy/runner.env.template"')
s = s.replace("echo \"next: $(sudo bash \"$0\" check 2>/dev/null | grep -v ' ok$' | head -3 | paste -sd';')\"", "true")
open(f"{T}/setup.sh", "w").write(s)
run = lambda *a: subprocess.run(["bash", f"{T}/setup.sh", *a], capture_output=True, text=True)
r = run("upgrade"); env = dict(l.split("=", 1) for l in open(f"{T}/runner.env").read().splitlines() if l and not l.startswith("#") and "=" in l)
ok(r.returncode == 0 and env["PRIVATE_KEY"] == KEY and env["WALLET"].startswith("0x4c662C") and env["PNL_BASE"] == "0.011100", "upgrade keeps the key, the wallet and the base")
ok(env["RPC_URL"] == "" and "sniper's key: dropped" in r.stdout, "a copied sniper provider key is dropped (set-rpc required)")
ok(env["SLOT_SEND"] == "1" and env["SLOT_LEAD_MS"] == "50" and env["FEED_LAG_MS"] == "85" and env["MARGIN_MS"] == "0", "the box's timing calibration comes from the sniper's env")
ok(env["BURST_N"] == "24" and "GAS_HEADROOM" not in env and env["TIER_EARLY"] == "1" and env["REQUIRE_FEED_LOCAL_ADDR"] == "1" and env["EXIT_MARK"] == "1", "the template's settings replace the old ones (the old BURST_N 1 and GAS_HEADROOM 2.0 gone)")
ok(env["FEED_URL"] == "wss://feed.example" and env["SEQ_URL"] == "https://seq.example" and "@" not in open(f"{T}/runner.env").read(), "the connections from the sniper's env, no placeholder left")
ok(all(stat.S_IMODE(os.stat(f"{T}/{f}").st_mode) == 0o600 for f in ("runner.env", "runner.env.bak")) and KEY in open(f"{T}/runner.env.bak").read(), "runner.env and its backup are 0600; the backup holds the old key")
r = run("base"); ok(r.returncode != 0 and "already 0.011100" in r.stdout, "base refuses to overwrite a recorded base")
r = run("base", "--add", "0.002"); ok("PNL_BASE=0.013100" in open(f"{T}/runner.env").read(), "base --add adds a later deposit")
r = run("upgrade"); env2 = dict(l.split("=", 1) for l in open(f"{T}/runner.env").read().splitlines() if l and not l.startswith("#") and "=" in l)
ok(env2["PNL_BASE"] == "0.013100" and env2["PRIVATE_KEY"] == KEY, "a second upgrade keeps the updated base and the key")
src = open(f"{R}/deploy/runner_setup.sh").read()
ok("own_rpc_ok; feed_ip_ok; no_open_position" in src and 'bash "$0" check >/dev/null || { bash "$0" check; exit 1; }' in src, "dry and live refuse without the runner's own key, its second address, or with a position open; live runs the full check")
ok("CPUAffinity=0" in src and "Nice=10" in src and "After=network-online.target chrony.service runner-ip.service" in src, "the runner's units keep it off the sniper's core and start after its address")
ok("/etc/needrestart/conf.d/engines.conf" in src and "$nrconf{override_rc}{qr(^runner-engine)} = 0;" in src and "qr(^sniper-engine)" in src, "units exclude the engines from needrestart (an unattended upgrade restarted sniper-notify on Oct 10)")
ok('[ "$U" != "$(val RPC_URL "$SRC")" ]' in src and "read -r -s -p" in src, "set-rpc reads the URL without echo and refuses the sniper's")
print(f"all {checks} checks passed")
