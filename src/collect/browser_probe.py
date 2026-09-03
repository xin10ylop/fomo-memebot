import asyncio, json, os, sys
from playwright.async_api import async_playwright
async def main():
    reqs=[]
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, executable_path="/opt/pw-browsers/chromium", args=["--no-sandbox","--disable-gpu","--ignore-certificate-errors","--ssl-version-max=tls1.2"], proxy={"server": os.environ["HTTPS_PROXY"]})
        ctx = await b.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36", viewport={"width":1400,"height":1000}, ignore_https_errors=True)
        page = await ctx.new_page()
        async def on_resp(r):
            u=r.url
            if any(x in u for x in ["googletagmanager","facebook","gstatic","/fonts/","/images/","/assets/",".woff",".png",".webp",".svg",".css","datadog","posthog","statsig","app-actions","browser-intake","ingest","privy.io"]): return
            ct=r.headers.get("content-type",""); body=""
            if "json" in ct:
                try: body=(await r.text())[:1500]
                except Exception as e: body=f"<err {e}>"
            reqs.append({"url":u,"status":r.status,"method":r.request.method,"ct":ct,"hdrs":{k:v for k,v in r.request.headers.items() if k.lower() in ("authorization","x-supported-chains")},"body":body})
        page.on("response", on_resp)
        for i,url in enumerate(["https://fomo.family/profile/unipcs","https://fomo.family/clan/Fantom%20Troupe","https://fomo.family/"]):
            try:
                r = await page.goto(url, wait_until="load", timeout=90000)
                await page.wait_for_timeout(8000)
                print("NAV",url,"->",page.url,r.status if r else None, file=sys.stderr)
                print("TITLE",await page.title(), file=sys.stderr)
                txt=(await page.inner_text("body"))[:3000].replace("\n"," | ")
                print("TEXT",txt, file=sys.stderr)
                links = await page.eval_on_selector_all("a[href]", "els => els.map(e=>e.getAttribute('href'))")
                print("LINKS", sorted(set(l for l in links if l and l.startswith('/')))[:60], file=sys.stderr)
                await page.screenshot(path=f"app_shot_{i}.png", full_page=False)
            except Exception as e:
                print("ERR",url,str(e)[:300], file=sys.stderr)
        await b.close()
    json.dump(reqs, open("pw_app_reqs.json","w"), indent=1)
    for r in reqs:
        print(r["method"], r["status"], r["url"][:160], r["ct"][:20], r["hdrs"])
        if r["body"]: print("   BODY:", r["body"][:400])
asyncio.run(main())
