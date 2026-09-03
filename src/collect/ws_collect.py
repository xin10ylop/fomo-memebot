import asyncio, json, time, sys, os
import websockets
K="fapi_38babbd7079b48aea53b44b32b0a3faf1cd6d4de865b46cb86e3bfb0b3e10c2a"
OUT="fapi/ws_alerts.jsonl"
async def run():
    backoff=5
    while True:
        try:
            async with websockets.connect(f"wss://api.fomoapi.io/ws/alerts?key={K}", ping_interval=20, max_size=8_000_000) as ws:
                print(time.strftime("%H:%M:%S"),"connected",file=sys.stderr,flush=True); backoff=5
                with open(OUT,"a") as f:
                    async for msg in ws:
                        try: d=json.loads(msg)
                        except Exception: d={"raw":msg}
                        d["_recv"]=int(time.time()*1000)
                        f.write(json.dumps(d)+"\n"); f.flush()
                        if d.get("type")!="alert": print(time.strftime("%H:%M:%S"),"msg",str(d)[:300],file=sys.stderr,flush=True)
        except Exception as e:
            print(time.strftime("%H:%M:%S"),"ws error",repr(e)[:200],"retry in",backoff,file=sys.stderr,flush=True)
            await asyncio.sleep(backoff); backoff=min(backoff*2,120)
asyncio.run(run())
