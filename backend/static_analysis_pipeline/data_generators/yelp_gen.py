import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# -----------------------------
# CONFIG
# -----------------------------

LOCATIONS = [
    "Camden", "Westminster", "Hackney", "Islington", "Southwark",
    "Kensington", "Chelsea", "Brixton", "Shoreditch",
]

CATEGORIES = [
    "Cafe", "Restaurant", "Bar", "Nightclub", "Gym",
    "Park", "Hotel", "Convenience Store", "Fast Food",
]

BUSINESS_NAME_TEMPLATES = [
    "{location} {category} House",
    "The {location} {category}",
    "{category} on {location} High St",
    "{location} Corner {category}",
    "{location} {category} & Co.",
]

AUTHOR_FIRST = ["Ava", "Noah", "Mia", "Leo", "Sofia", "Ethan", "Zara", "Omar", "Ella", "Kai"]
AUTHOR_LAST = ["Patel", "Smith", "Nguyen", "Brown", "Khan", "Garcia", "Lee", "Jones", "Taylor", "Ali"]

# Longer-form review “paragraph chunks” with optional safety signals
POSITIVE_BITS = [
    "The staff were genuinely friendly and checked in on us a couple of times.",
    "The place was clean, well-lit, and felt comfortable even late in the evening.",
    "Great vibe and music at a reasonable volume—easy to talk.",
    "Food came out quickly and everything tasted fresh.",
    "Pricing was fair for the area and portions were solid.",
    "Bathrooms were clean and stocked, which I always appreciate.",
]

NEUTRAL_BITS = [
    "It was busy but the queue moved faster than expected.",
    "Service was a little slow, but they were clearly understaffed.",
    "The menu is pretty standard—nothing groundbreaking but decent.",
    "Seating is a bit tight if you’re with a big group.",
    "Music can get loud on weekends, so not ideal if you want a quiet chat.",
]

NEGATIVE_BITS = [
    "The lighting outside was poor and the street felt a bit sketchy walking back.",
    "Had an uncomfortable interaction with someone hanging around the entrance.",
    "Security was inconsistent—some people got checked, others didn’t.",
    "There was a lot of shouting outside and it made the area feel unsafe.",
    "I saw a fight start nearby and we left early.",
    "Someone tried to pickpocket my friend in the crowd—keep your belongings close.",
    "Drinks were overpriced and the staff seemed stressed and dismissive.",
    "We waited ages and our order was wrong twice.",
]

SAFETY_TAGS = [
    "well_lit", "crowded", "security_present", "pickpocket_reports",
    "fight_nearby", "harassment_report", "poor_lighting", "police_seen",
]

PRICE_LEVEL = ["£", "££", "£££", "££££"]

# -----------------------------
# HELPERS
# -----------------------------

def rand_ts(days_back: int = 90) -> str:
    now = datetime.utcnow()
    delta = timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    return (now - delta).isoformat() + "Z"


def sample_author() -> str:
    return f"{random.choice(AUTHOR_FIRST)} {random.choice(AUTHOR_LAST)}"


def build_business_name(location: str, category: str) -> str:
    return random.choice(BUSINESS_NAME_TEMPLATES).format(location=location, category=category)


def choose_rating(safety_negative: bool) -> int:
    """
    Slightly lower ratings if safety-negative signals exist.
    """
    if safety_negative:
        # skew 1-3
        return random.choices([1, 2, 3], weights=[0.25, 0.45, 0.30])[0]
    # skew 3-5
    return random.choices([3, 4, 5], weights=[0.25, 0.45, 0.30])[0]


def make_review_text(safety_negative: bool) -> str:
    """
    Create a longer-form review with multiple sentences.
    """
    chunks = []

    # Always include some context
    opener = random.choice([
        "Came here with a friend after work.",
        "Visited on a Saturday night.",
        "Stopped in for a quick bite.",
        "Dropped by while exploring the area.",
        "Went here for a date night.",
    ])
    chunks.append(opener)

    # Mix: positive + neutral, optionally negative
    chunks.extend(random.sample(POSITIVE_BITS, k=random.randint(1, 2)))
    chunks.extend(random.sample(NEUTRAL_BITS, k=random.randint(1, 2)))

    if safety_negative:
        chunks.extend(random.sample(NEGATIVE_BITS, k=random.randint(1, 2)))
    else:
        # add extra positive to balance length
        chunks.append(random.choice(POSITIVE_BITS))

    # Closing
    closing = random.choice([
        "Would come back, but I’d probably go earlier next time.",
        "Overall it was decent—just manage expectations.",
        "I’d return for the atmosphere, but keep an eye on your stuff.",
        "I’ll be back, especially if they fix the small issues.",
        "Worth a visit if you’re in the area.",
    ])
    chunks.append(closing)

    return " ".join(chunks)


def infer_safety_tags(safety_negative: bool) -> List[str]:
    """
    Attach a few safety-related tags to help your analyzer tests.
    """
    tags = []

    # baseline
    tags.append(random.choice(["crowded", "security_present", "well_lit"]))

    if safety_negative:
        tags.extend(random.sample(
            ["poor_lighting", "pickpocket_reports", "fight_nearby", "harassment_report", "police_seen"],
            k=random.randint(1, 2)
        ))
    else:
        # more positive-ish tags
        tags.append(random.choice(["well_lit", "security_present"]))

    # unique
    return sorted(list(set(tags)))


# -----------------------------
# GENERATOR
# -----------------------------

def generate_review(
    location: Optional[str] = None,
    category: Optional[str] = None,
    safety_negative: Optional[bool] = None,
) -> Dict:
    location = location or random.choice(LOCATIONS)
    category = category or random.choice(CATEGORIES)

    if safety_negative is None:
        # ~30% of reviews mention something safety-negative
        safety_negative = random.random() < 0.30

    business_name = build_business_name(location, category)
    tags = infer_safety_tags(safety_negative)
    rating = choose_rating(safety_negative)

    text = make_review_text(safety_negative)

    return {
        "id": random.randint(10_000_000, 99_999_999),
        "source": "mock_yelp",
        "business": {
            "name": business_name,
            "category": category,
            "location": location,
            "price": random.choice(PRICE_LEVEL),
        },
        "author": sample_author(),
        "rating": rating,
        "created_at": rand_ts(),
        "text": text,
        "safety_tags": tags,          # useful for unit tests / evaluation
        "safety_negative": safety_negative,  # ground truth label
    }


def generate_batch(n: int) -> List[Dict]:
    return [generate_review() for _ in range(n)]


def generate_for_all(location_list: List[str], category_list: List[str], per_combo: int = 5) -> List[Dict]:
    """
    Useful for your worker idea: iterate locations x categories and generate reviews per combo.
    """
    out = []
    for loc in location_list:
        for cat in category_list:
            for _ in range(per_combo):
                out.append(generate_review(location=loc, category=cat))
    return out


# -----------------------------
# SAVE
# -----------------------------

def save_json(items: List[Dict], filename: str = "mock_yelp_reviews.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Example 1: random set
    reviews = generate_batch(30)

    # Example 2: deterministic coverage by location/category
    # reviews = generate_for_all(LOCATIONS[:3], CATEGORIES[:4], per_combo=3)

    for r in reviews[:3]:
        print(f"{r['business']['name']} ({r['rating']}★) - {r['business']['location']}")
        print(r["text"])
        print("tags:", r["safety_tags"])
        print("---")

    save_json(reviews)
    print(f"\nSaved {len(reviews)} reviews to mock_yelp_reviews.json")
