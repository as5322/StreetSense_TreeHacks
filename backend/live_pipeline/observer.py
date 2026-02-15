# from typing import Any, Dict, List


# class Observer:
#     def __init__(self):
#         self.policy: Dict[str, Any] = {
#             "min_items": 1,
#             "max_items": 5,
#             "dom_settle_seconds": 3,
#             "dedupe_by_url": True,
#         }

#     def tune_scraper(self, scraper) -> Dict[str, Any]:
#         # Example: if failures or low-quality output, increase settle time and reduce items.
#         return scraper.set_params(
#             max_items=self.policy["max_items"],
#             dom_settle_seconds=self.policy["dom_settle_seconds"],
#         )

#     def prepare_validation_payload(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
#         if self.policy["dedupe_by_url"]:
#             seen = set()
#             deduped = []
#             for it in items:
#                 u = it.get("url")
#                 if u and u not in seen:
#                     seen.add(u)
#                     deduped.append(it)
#             items = deduped

#         return {
#             "items": items,
#             "policy": {
#                 "min_items": self.policy["min_items"],
#                 # you can include more knobs for the validator here
#             },
#         }

#     def should_write(self, out) -> bool:
#         return float(out.final_severity) >= 0.6

