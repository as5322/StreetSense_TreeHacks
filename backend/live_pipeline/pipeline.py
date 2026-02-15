import asyncio
from live_pipeline.scraper_agent import ScraperAgent
from live_pipeline.validator_agent import ValidatorAgent
from live_pipeline.criticality_agent import CriticalityAgent
from live_pipeline.observer_agent import ObserverAgent
from db.db_writer import DBWriter


async def main():
    scraper = ScraperAgent()
    observer = ObserverAgent()
    validator = ValidatorAgent()
    crit = CriticalityAgent(model="claude-opus-4-6")
    db = DBWriter()

    seen_urls = set()

    await scraper.start()
    try:
        observer.tune_scraper(scraper)
        jobs = observer.plan_all_queries()

        for job in jobs:
            items = await scraper.bing_news_search(job["query"], location_hint="")

            # attach geo + dedupe
            new_items = []
            for item in items:
                item["lat"] = job["location"].lat
                item["long"] = job["location"].long
                item["category"] = job["category"]


                u = item.get("url")
                if not u or u in seen_urls:
                    continue
                seen_urls.add(u)
                new_items.append(item)

            if not new_items:
                print("No new items for:", job["query"])
                await asyncio.sleep(10)
                continue

            # 2) VALIDATE (only new items)
            validated = validator.validate_batch(new_items)
            validated = observer.filter_validated(validated)  # plausibility >= 0.5 gate

            # 4) CRITICALITY/TWEET
            for v in validated:
                out = crit.assess(v)

                risk = float(out.final_severity)

                db.update_truth(
                    lat=job["location"].lat,
                    long=job["location"].long,
                    category=job["category"],   # category enum must match truth columns
                    severity=risk,              # store risk in truth (not raw severity)
                    alpha=0.25,                 # tune smoothing
                )

                if observer.should_write(out):
                    db.insert_post(
                        lat=job["location"].lat,      
                        long=job["location"].long,
                        severity=out.final_severity,
                        category=job["category"],
                        content=out.tweet,
                        human=False,
                    )

                print("written to db")

            # rate limit without blocking async loop
            await asyncio.sleep(40)

    finally:
        await scraper.end()


if __name__ == "__main__":
    asyncio.run(main())
