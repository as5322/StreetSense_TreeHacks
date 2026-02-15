import random
import json
from datetime import datetime, timedelta
from typing import List, Dict

# -----------------------------
# CONFIG
# -----------------------------

LOCATIONS = [
    "Camden",
    "Westminster",
    "Hackney",
    "Islington",
    "Southwark",
    "Kensington",
    "Chelsea",
    "Brixton",
    "Shoreditch",
]

INCIDENT_TYPES = [
    "fire",
    "robbery",
    "accident",
    "knife incident",
    "suspicious activity",
    "assault",
    "car theft",
    "explosion",
    "road blockage",
]

SEVERITY_WORDS = [
    "major",
    "serious",
    "minor",
    "large",
    "small",
    "ongoing",
    "reported",
    "confirmed",
]

EMOJIS = ["🚨", "🔥", "⚠️", "🚓", "🚑", "👀"]

TEMPLATES = [
    "{emoji} {severity} {incident} reported in {location}. Avoid the area.",
    "Hearing about a {incident} in {location} right now {emoji}",
    "{location} residents reporting {severity} {incident}. Stay safe everyone.",
    "Anyone else see what happened in {location}? {incident} situation {emoji}",
    "{emoji} Emergency services responding to a {incident} in {location}.",
    "Traffic building up in {location} due to {incident}.",
    "Reports of {severity} {incident} near central {location}.",
]

# -----------------------------
# TWEET GENERATOR
# -----------------------------

def random_timestamp(hours_back: int = 48) -> str:
    """
    Generate a random timestamp within the past X hours.
    """
    now = datetime.utcnow()
    delta = timedelta(
        hours=random.randint(0, hours_back),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    ts = now - delta
    return ts.isoformat() + "Z"


def generate_tweet() -> Dict:
    """
    Generate a single mock tweet.
    """
    template = random.choice(TEMPLATES)
    location = random.choice(LOCATIONS)
    incident = random.choice(INCIDENT_TYPES)
    severity = random.choice(SEVERITY_WORDS)
    emoji = random.choice(EMOJIS)

    text = template.format(
        location=location,
        incident=incident,
        severity=severity,
        emoji=emoji,
    )

    return {
        "id": random.randint(10_000_000, 99_999_999),
        "text": text,
        "location": location,
        "incident_type": incident,
        "created_at": random_timestamp(),
    }


def generate_batch(n: int) -> List[Dict]:
    """
    Generate N mock tweets.
    """
    return [generate_tweet() for _ in range(n)]


# -----------------------------
# OPTIONAL: SAVE FUNCTIONS
# -----------------------------

def save_json(tweets: List[Dict], filename: str = "mock_tweets.json"):
    with open(filename, "w") as f:
        json.dump(tweets, f, indent=2)


if __name__ == "__main__":
    # Example usage
    tweets = generate_batch(50)

    for t in tweets[:5]:
        print(t["text"])

    save_json(tweets)
    print("\nSaved 50 mock tweets to mock_tweets.json")
