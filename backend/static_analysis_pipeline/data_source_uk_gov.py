# data_source_police_api.py
import asyncio
import math
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from live_pipeline.observer_agent import ObserverAgent
from live_pipeline.criticality_agent import CriticalityAgent
from db.db_writer import DBWriter


POLICE_API_BASE = "https://data.police.uk/api"

class TokenBucket:
    def __init__(self, rate_per_sec: float, capacity: int):
        self.rate = rate_per_sec
        self.capacity = capacity
        self.tokens = float(capacity)
        self.updated = asyncio.get_event_loop().time()
        self._lock = asyncio.Lock()

    async def acquire(self, amount: float = 1.0) -> None:
        async with self._lock:
            while True:
                now = asyncio.get_event_loop().time()
                elapsed = now - self.updated
                self.updated = now

                # refill
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

                if self.tokens >= amount:
                    self.tokens -= amount
                    return

                needed = amount - self.tokens
                wait_s = needed / self.rate if self.rate > 0 else 0.1
                await asyncio.sleep(max(0.01, wait_s))

@dataclass
class PoliceAPIClient:
    session: aiohttp.ClientSession
    limiter: TokenBucket

    async def _get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        await self.limiter.acquire(1.0)
        url = f"{POLICE_API_BASE}{path}"

        async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=25)) as resp:
            if resp.status == 429:
                # Backoff on rate-limit
                retry_after = resp.headers.get("Retry-After")
                sleep_s = float(retry_after) if retry_after else 2.0
                await asyncio.sleep(sleep_s)
                raise RuntimeError(f"Rate limited (429) on {url} params={params}")

            resp.raise_for_status()
            return await resp.json()

    async def latest_month(self) -> str:
        """
        Uses crimes-street-dates which returns available YYYY-MM values.
        """
        data = await self._get_json("/crimes-street-dates")
        if not data or not isinstance(data, list):
            raise RuntimeError("Unexpected crimes-street-dates response")

        first = data[0]
        date = first.get("date")
        if not isinstance(date, str) or len(date) != 7:
            raise RuntimeError("Could not parse latest YYYY-MM date from crimes-street-dates")
        return date

    async def crimes_all(self, *, lat: float, lng: float, date_yyyymm: str) -> List[Dict[str, Any]]:
        params = {"lat": lat, "lng": lng, "date": date_yyyymm}
        return await self._get_json("/crimes-street/all-crime", params=params)


def _crime_summary_report(
    *,
    lat: float,
    lng: float,
    month: str,
    crimes: List[Dict[str, Any]],
    top_k: int = 6
) -> Tuple[str, float]:
    total = len(crimes)
    if total == 0:
        return (
            f"UK Police street-level crime data for {month} near ({lat:.5f}, {lng:.5f}): no crimes returned.",
            0.0,
        )

    cats = [c.get("category", "unknown") for c in crimes]
    counts = Counter(cats)
    top = counts.most_common(top_k)

    intensity = 1.0 - math.exp(-total / 40.0) 

    lines = [
        f"UK Police street-level crime data summary for {month} near ({lat:.5f}, {lng:.5f}).",
        f"Total crimes returned: {total}.",
        "Top categories:",
    ]
    for cat, n in top:
        lines.append(f"- {cat}: {n}")

    streets = []
    for c in crimes[:10]:
        loc = c.get("location") or {}
        street = (loc.get("street") or {}).get("name")
        if isinstance(street, str) and street and street not in streets:
            streets.append(street)
        if len(streets) >= 4:
            break
    if streets:
        lines.append("Example nearby streets mentioned:")
        for s in streets:
            lines.append(f"- {s}")

    report = "\n".join(lines)
    return report, float(intensity)


async def main(
    model: str = "claude-opus-4-6",
    alpha: float = 0.25,
    max_concurrency: int = 6,
):
    observer = ObserverAgent()
    crit = CriticalityAgent(model=model)
    db = DBWriter()

    limiter = TokenBucket(rate_per_sec=15.0, capacity=30)

    connector = aiohttp.TCPConnector(limit=50, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        api = PoliceAPIClient(session=session, limiter=limiter)

        month = await api.latest_month()
        print("Police API latest available month:", month)

        jobs = observer.plan_all_queries()

        crime_jobs = [j for j in jobs if j.get("category") == "crime"]
        if not crime_jobs:
            print("No 'crime' jobs found from observer.plan_all_queries().")
            return

        sem = asyncio.Semaphore(max_concurrency)

        async def process_job(job: Dict[str, Any]) -> None:
            async with sem:
                loc = job["location"]
                lat = float(loc.lat)
                lng = float(loc.long)

                try:
                    crimes = await api.crimes_all(lat=lat, lng=lng, date_yyyymm=month)
                except Exception as e:
                    print("Police API fetch failed:", job.get("query"), e)
                    return

                report, intensity = _crime_summary_report(lat=lat, lng=lng, month=month, crimes=crimes)

                out = crit.assess(report)

                risk = float(out.final_severity)
                risk = max(0.0, min(1.0, 0.65 * risk + 0.35 * intensity))

                db.update_truth(
                    lat=lat,
                    long=lng,
                    category="crime",   
                    severity=risk,
                    alpha=alpha,
                )

                if observer.should_write(out):
                    db.insert_post(
                        lat=lat,
                        long=lng,
                        severity=risk,
                        category="crime",
                        content=report,
                        human=False,
                    )

                print(f"[crime] wrote truth/post at ({lat:.4f},{lng:.4f}) risk={risk:.2f} crimes={len(crimes)}")

        await asyncio.gather(*(process_job(j) for j in crime_jobs))


if __name__ == "__main__":
    asyncio.run(main())
