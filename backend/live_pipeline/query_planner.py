from dataclasses import dataclass
from typing import List

@dataclass
class QueryPlan:
    location: str
    queries: List[str]

class QueryPlanner:
    def __init__(self):
        self.default_keywords = [
            "closure", "police", "crime", "protest", "attack",
            "fire", "accident", "tube", "bus", "traffic",
            "pedestrianisation", "tfL", "strike"
        ]

    def build_for_location(self, location, max_q: int = 8):
        base = f"{location.name} {location.city}"
        kws = location.keywords or self.default_keywords

        jobs = [{"query": base, "category": "other"}]  # base query is generic
        for kw in kws[: max_q - 1]:
            jobs.append({"query": f"{base} {kw}", "category": kw})
        return jobs


    def build(self, location: str, city: str = "London", keywords: List[str] | None = None, max_q: int = 8) -> QueryPlan:
        kws = keywords or self.default_keywords
        base = f"{location} {city}".strip()
        queries = [base]
        for kw in kws:
            queries.append(f"{base} {kw}")
        return QueryPlan(location=base, queries=queries[:max_q])
