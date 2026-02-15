import os
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
import asyncio
from stagehand import UnprocessableEntityError

from stagehand import AsyncStagehand

from live_pipeline.pipeline_models import ScrapedItem


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ScraperAgent:
    """
    Owns the browser session and exposes functions the Observer can call.
    """

    def __init__(self, model_name: str = "openai/gpt-4o-mini"):
        self.model_name = model_name
        self.client: Optional[AsyncStagehand] = None
        self.session = None
        self.state: Dict[str, Any] = {
            "max_items": 5,
            "dom_settle_seconds": 3,
            "extract_schema_strict": True,
        }

    async def start(self) -> str:
        self.client = AsyncStagehand(
            browserbase_api_key="",
            browserbase_project_id="",
            model_api_key="",
        )
        await self.client.__aenter__()  # enter async context manually

        self.session = await self.client.sessions.start(model_name=self.model_name)
        return self.session.id

    async def end(self) -> None:
        if self.session:
            await self.session.end()
            self.session = None
        if self.client:
            await self.client.__aexit__(None, None, None)
            self.client = None

    # --- functions the Observer can call ---

    def set_params(self, **kwargs) -> Dict[str, Any]:
        """
        Observer updates scraper behavior without rewriting prompts.
        """
        self.state.update(kwargs)
        return dict(self.state)

    async def bing_news_search(self, query: str, location_hint: str = "London") -> List[Dict[str, Any]]:
        """
        Returns a list[ScrapedItem dict] ready for the validation layer.
        Robust against schema-mismatch by using a fallback extraction.
        """
        assert self.session is not None, "Call start() first"

        q = f"{query} {location_hint}".strip()
        url = f"https://www.bing.com/news/search?q={quote_plus(q)}"
        await self.session.navigate(url=url)
        await asyncio.sleep(self.state["dom_settle_seconds"])

        max_items = int(self.state["max_items"])

        # ✅ Relaxed schema: allow additionalProperties, optional fields, allow empty articles
        schema = {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "articles": {
                    "type": "array",
                    "maxItems": max_items,
                    "items": {
                        "type": "object",
                        "additionalProperties": True,
                        "properties": {
                            "title": {"type": "string"},
                            "url": {"type": "string"},
                            "publisher": {"type": "string"},
                            "published_at": {"type": "string"},
                            "snippet": {"type": "string"},
                        },
                        "required": ["title", "url"],
                    },
                }
            },
            "required": ["articles"],
        }

        # ✅ Much stricter instruction language
        instruction = (
            f"From this Bing News results page, return a JSON object with key 'articles'. "
            f"'articles' must be an array of up to {max_items} objects. "
            f"Each object must have EXACTLY: title (string) and url (string). "
            f"Optionally include: publisher, published_at, snippet (strings). "
            f"If you cannot find any articles, return {{\"articles\": []}}. "
            f"Do not include commentary or extra top-level keys."
        )

        try:
            resp = await self.session.extract(instruction=instruction, schema=schema)
            articles = (resp.data.result or {}).get("articles", [])
        except UnprocessableEntityError:
            # ✅ Fallback path: ask for minimal (title,url) only with an even simpler schema
            fallback_schema = {
                "type": "object",
                "properties": {
                    "articles": {
                        "type": "array",
                        "maxItems": max_items,
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "url": {"type": "string"},
                            },
                            "required": ["title", "url"],
                            "additionalProperties": True,
                        },
                    }
                },
                "required": ["articles"],
                "additionalProperties": True,
            }

            fallback_instruction = (
                f"Return ONLY JSON: {{\"articles\": [ ... ]}}. "
                f"Extract up to {max_items} items. "
                f"Each item MUST have 'title' and 'url'. "
                f"If none, return {{\"articles\": []}}."
            )

            resp = await self.session.extract(instruction=fallback_instruction, schema=fallback_schema)
            articles = (resp.data.result or {}).get("articles", [])

        out: List[Dict[str, Any]] = []
        for a in articles:
            item = ScrapedItem(
                source="bing_news",
                query=q,
                title=(a.get("title") or "").strip(),
                url=(a.get("url") or "").strip(),
                publisher=(a.get("publisher") or None),
                published_at=(a.get("published_at") or None),
                snippet=(a.get("snippet") or None),
                fetch_ts=now_iso(),
            )
            if item.title and item.url and item.url.startswith("http"):
                out.append(item.to_dict())

        return out


    async def open_and_capture(self, url: str, capture_html: bool = False, capture_text: bool = True) -> Dict[str, Any]:
        """
        Optional: open an article page and capture text/html for better validation later.
        Observer can choose when to call this (e.g., only for high-severity candidates).
        """
        assert self.session is not None, "Call start() first"

        await self.session.navigate(url=url)
        await asyncio.sleep(self.state["dom_settle_seconds"])

        schema = {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "title": {"type": "string"},
            },
            "required": [],
        }

        instruction = (
            "Extract the main article title and the main readable article text from the page. "
            "If blocked, paywalled, or not accessible, return empty strings. Do not invent."
        )
        resp = await self.session.extract(instruction=instruction, schema=schema)
        result = resp.data.result or {}

        payload = {
            "url": url,
            "captured_at": now_iso(),
            "title": (result.get("title") or "").strip() if capture_text else None,
            "text": (result.get("text") or "").strip() if capture_text else None,
        }

        if capture_html:
            # Stagehand may have a method for raw html; if not, you can remove this.
            # Keep placeholder so the interface is stable.
            payload["html"] = None

        return payload
