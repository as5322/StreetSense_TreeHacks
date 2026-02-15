from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any

@dataclass
class ScrapedItem:
    source: str                # e.g. "bing_news"
    query: str                 # the user query / landmark
    title: str
    url: str
    publisher: Optional[str] = None
    published_at: Optional[str] = None  # ISO string if available
    snippet: Optional[str] = None
    raw_text: Optional[str] = None      # optional: extracted article text if you do it
    raw_html: Optional[str] = None      # optional: for auditing / reprocessing
    fetch_ts: Optional[str] = None      # when we scraped it

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ValidationInput:
    items: List[Dict[str, Any]]  # list of ScrapedItem dicts
    policy: Dict[str, Any]       # observer-provided thresholds/settings