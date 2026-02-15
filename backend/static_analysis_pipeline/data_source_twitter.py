# We use mock data / tweets since the twitter api was expensive and scraping it was bad #
import asyncio
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

from live_pipeline.validator_agent import ValidatorAgent
from live_pipeline.observer_agent import ObserverAgent
from live_pipeline.criticality_agent import CriticalityAgent
from db.db_writer import DBWriter



LOCATION_COORDS: Dict[str, Dict[str, float]] = {
    "Camden": {"lat": 51.5416, "long": -0.1420},
    "Westminster": {"lat": 51.4975, "long": -0.1357},
    "Hackney": {"lat": 51.5450, "long": -0.0553},
    "Islington": {"lat": 51.5380, "long": -0.0990},
    "Southwark": {"lat": 51.5035, "long": -0.0880},
    "Kensington": {"lat": 51.5009, "long": -0.1939},
    "Chelsea": {"lat": 51.4875, "long": -0.1687},
    "Brixton": {"lat": 51.4613, "long": -0.1156},
    "Shoreditch": {"lat": 51.5246, "long": -0.0781},
}


def _stable_id(tweet: Dict[str, Any]) -> str:
    """
    For dedupe: prefer tweet['id'], otherwise hash text+created_at.
    """
    tid = tweet.get("id")
    if tid is not None:
        return str(tid)

    text = str(tweet.get("text", ""))
    created_at = str(tweet.get("created_at", ""))
    h = hashlib.sha1(f"{text}|{created_at}".encode("utf-8")).hexdigest()
    return h


def _load_json_array(path: str) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Expected top-level JSON array")
    return data


def _attach_geo(tweet: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure tweet has lat/long. If not present, infer from location name.
    """
    if "lat" in tweet and "long" in tweet:
        return tweet

    loc = tweet.get("location")
    if isinstance(loc, str) and loc in LOCATION_COORDS:
        tweet["lat"] = LOCATION_COORDS[loc]["lat"]
        tweet["long"] = LOCATION_COORDS[loc]["long"]
    else:
        tweet["lat"] = tweet.get("lat", 0.0)
        tweet["long"] = tweet.get("long", 0.0)
    return tweet


def _tweet_to_validator_item(tweet: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validator expects 'items' similar to your bing pipeline.
    We shape a minimal dict with a 'url' for dedupe.
    """
    tid = _stable_id(tweet)
    url = tweet.get("url") or f"mock://twitter/{tid}"

    return {
        "url": url,
        "content": tweet.get("text", ""),
        "title": None,
        "source": "twitter_mock",
        "created_at": tweet.get("created_at"),
        "location_hint": tweet.get("location"),
        "lat": tweet.get("lat"),
        "long": tweet.get("long"),
        "_raw": tweet,
    }


async def main(
    json_path: str = "./mock_tweets.json",
    model: str = "claude-opus-4-6",
    alpha: float = 0.25,
    rate_limit_s: float = 0.0,
    use_validator: bool = True,
):
    validator = ValidatorAgent()
    observer = ObserverAgent()
    crit = CriticalityAgent(model=model)
    db = DBWriter()

    tweets = _load_json_array(json_path)
    print(f"Loaded {len(tweets)} mock tweets from {json_path}")

    seen = set()

    items: List[Dict[str, Any]] = []
    for t in tweets:
        t = _attach_geo(t)
        tid = _stable_id(t)
        if tid in seen:
            continue
        seen.add(tid)
        items.append(_tweet_to_validator_item(t))

    if not items:
        print("No items after dedupe.")
        return

    if use_validator:
        validated = validator.validate_batch(items)
        validated = observer.filter_validated(validated) 
    else:
        validated = items

    if not validated:
        print("No items after validation gate.")
        return


    written_posts = 0
    updated_truth = 0

    for v in validated:
        raw = v.get("_raw", {})
        lat = float(v.get("lat") or raw.get("lat") or 0.0)
        long = float(v.get("long") or raw.get("long") or 0.0)

        content = str(v.get("content") or "")
        if not content.strip():
            continue

        out = crit.assess(content)
        risk = float(out.final_severity)

        db.update_truth(
            lat=lat,
            long=long,
            category=out.category,  
            severity=risk,
            alpha=alpha,
        )
        updated_truth += 1

        if observer.should_write(out):
            db.insert_post(
                lat=lat,
                long=long,
                severity=out.final_severity,
                category=out.category,
                content=content,
                human=False,
            )
            written_posts += 1

        print(f"db write ok | cat={out.category} sev={out.final_severity:.2f} | {content[:80]}")

        if rate_limit_s > 0:
            await asyncio.sleep(rate_limit_s)

    print(f"Done. updated_truth={updated_truth} inserted_posts={written_posts}")


if __name__ == "__main__":
    asyncio.run(main())
