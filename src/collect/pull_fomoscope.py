import json, urllib.request, time, os, sys
BASE="https://api.fomoscope.xyz"
def get(u, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"curl/8"}), timeout=60) as r: return json.load(r)
        except Exception as e:
            err=e; time.sleep(5*(i+1))
    print("FAIL",u,err,file=sys.stderr); return None
ids={}
for w in ["1d","7d","30d","all_time"]:
    d=get(f"{BASE}/traders?window={w}&limit=500")
    if not d: continue
    json.dump(d, open(f"fs/traders/{w}.json","w"))
    for it in d["items"]: ids[it["traderId"]]=it
    time.sleep(2.2)
print("distinct traders",len(ids),file=sys.stderr)
json.dump(ids, open("fs/traders/all_ids.json","w"))
for i,(tid,it) in enumerate(ids.items()):
    out=f"fs/positions/{tid}.json"
    if os.path.exists(out): continue
    d=get(f"{BASE}/traders/{tid}/positions?limit=500")
    if d is not None: json.dump(d, open(out,"w"))
    if i%50==0: print("pos",i,len(ids),file=sys.stderr)
    time.sleep(2.1)
print("DONE",file=sys.stderr)
