from typing import Dict, Any, List
from live_pipeline.query_planner import QueryPlanner
from live_pipeline.locations import MONITORED_LOCATIONS

class ObserverAgent:
    def __init__(self):
        self.planner = QueryPlanner()
        self.state: Dict[str, Any] = {
            "max_items_per_query": 3,
            "dom_settle_seconds": 6,
            "open_article_top_k": 2,   # deep fetch only for top-k by plausibility*severity_hint
            "min_plausibility_keep": 0.2,
        }

    def tune_scraper(self, scraper) -> None:
        scraper.set_params(
            max_items=self.state["max_items_per_query"],
            dom_settle_seconds=self.state["dom_settle_seconds"],
        )

    def plan_queries(self, location: str, city: str = "London") -> List[str]:
        plan = self.planner.build(location, city=city, max_q=8)
        return plan.queries
    
    def plan_all_queries(self):
        all_jobs = []
        for loc in MONITORED_LOCATIONS:
            loc_jobs = self.planner.build_for_location(loc, max_q=8)
            for j in loc_jobs:
                all_jobs.append({
                    "query": j["query"],
                    "category": j["category"],
                    "location": loc,
                })
        return all_jobs
    
    def choose_deep_fetch(self, validated_results) -> List[str]:
        scored = []
        for v in validated_results:
            score = float(v.plausibility) * float(v.severity_hint)
            scored.append((score, v.source_url))
        scored.sort(reverse=True)
        return [u for _, u in scored[: self.state["open_article_top_k"]]]
    
    def filter_validated(self, validated_results):
        kept = []
        dropped = []

        for v in validated_results:
            p = float(v.plausibility)
            if p >= 0.5:
                kept.append(v)
            else:
                dropped.append(v)

        print(f"Dropped {len(dropped)} low-plausibility items (<0.5)")
        return kept
    
    def should_write(self, out) -> bool:
        return float(out.final_severity) >= 0.6