from __future__ import annotations
import os
from typing import Literal, List
from pydantic import BaseModel, Field

from anthropic import Anthropic


Category = Literal[
    "crime",
    "public_safety",
    "transport",
    "infrastructure",
    "policy",
    "protest",
    "weather",
    "other",
]


class CriticalityOutput(BaseModel):
    final_severity: float = Field(ge=0.0, le=1.0)
    category: Category
    tweet: str = Field(max_length=280)


class CriticalityAgent:
    """
    THIS is the Anthropic layer.
    Input: validated result (Perplexity layer output)
    Output: final severity + category + tweet-ready summary.
    """

    def __init__(self, model: str = "claude-opus-4-6"):
        api_key = ""
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self.client = Anthropic(api_key=api_key)
        self.model = model

        # Define a tool whose input schema is exactly what we want back.
        self.tool_name = "emit_criticality"
        self.tool_schema = {
            "name": self.tool_name,
            "description": "Emit final severity, category, and a tweet-like update for a public feed.",
            "input_schema": CriticalityOutput.model_json_schema(),
        }

    def assess(self, validation_result) -> CriticalityOutput:
        # Compact evidence URLs (optional)
        evidence_urls: List[str] = []
        try:
            for e in (validation_result.evidence or [])[:3]:
                url = getattr(e, "url", None)
                if url:
                    evidence_urls.append(url)
        except Exception:
            pass

        # System-level instruction keeps output consistent and avoids hallucinations
        system = (
            "You generate location-based public updates. "
            "Never invent facts beyond the provided validated summary. "
            "Severity is impact-if-true (not probability-weighted). "
            "If plausibility < 0.5, the tweet MUST use uncertainty language."
        )

        user = f"""
Validated input:
- Title: {validation_result.title}
- Summary: {validation_result.summary}
- Plausibility (0-1): {validation_result.plausibility}
- Evidence URLs: {evidence_urls}

Return a tool call to {self.tool_name} with:
- final_severity (0-1)
- category (enum)
- tweet (<= 280 chars, neutral, feed-ready)

Tweet rules:
- If plausibility < 0.5, include "Unverified reports" or "Reports suggest".
- No emojis.
- Max 1 hashtag, only if truly useful.
- No calls to action, no speculation.
"""

        resp = self.client.messages.create(
            model=self.model,
            system=system,
            max_tokens=300,
            temperature=0.2,
            messages=[{"role": "user", "content": user}],
            tools=[self.tool_schema],
            tool_choice={"type": "tool", "name": self.tool_name},  # force structured tool output
        )

        # Extract tool args
        tool_calls = [c for c in resp.content if c.type == "tool_use" and c.name == self.tool_name]
        if not tool_calls:
            raise RuntimeError("Claude did not return the required tool output")

        args = tool_calls[0].input
        return CriticalityOutput.model_validate(args)
