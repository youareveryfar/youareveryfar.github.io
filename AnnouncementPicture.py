import asyncio
import httpx

BASE = "https://search.kmb.hk/kmbwebsite/AnnouncementPicture.ashx?url="

t_start = 1785383632
t_end   = 1785385704

def gen_candidates():
    for t in range(t_start, t_end + 1):
        for r in range(0, 10000):
            yield t, r, f"{t}_{r:04d}_0.pdf"

async def check_one(client, t, r, url_param):
    url = BASE + url_param
    try:
        resp = await client.head(url, follow_redirects=True)
        if resp.status_code == 405:
            resp = await client.get(url, follow_redirects=True)
    except httpx.RequestError:
        return None

    if resp.status_code != 200:
        return None

    ctype = (resp.headers.get("content-type") or "").lower()
    # keep this check if you want only true PDFs:
    if "pdf" not in ctype:
        return None

    return (t, r, url)

async def main():
    timeout = httpx.Timeout(connect=10, read=30, write=30, pool=30)
    limits = httpx.Limits(max_connections=80)

    found = []

    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"},
        timeout=timeout,
        limits=limits
    ) as client:
        sem = asyncio.Semaphore(80)

        async def worker(t, r, url_param):
            async with sem:
                return await check_one(client, t, r, url_param)

        tasks = []
        # stream tasks in chunks so memory doesn’t explode
        CHUNK = 5000
        for i, (t, r, url_param) in enumerate(gen_candidates()):
            tasks.append(worker(t, r, url_param))
            if len(tasks) >= CHUNK:
                for coro in asyncio.as_completed(tasks):
                    res = await coro
                    if res:
                        found.append(res)
                tasks = []

        if tasks:
            for coro in asyncio.as_completed(tasks):
                res = await coro
                if res:
                    found.append(res)

    found.sort()
    print("Found count:", len(found))
    # Print or save results:
    for t, r, full_url in found:
        print(full_url)

if __name__ == "__main__":
    asyncio.run(main())
