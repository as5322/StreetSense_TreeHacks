from typing import Literal
from pydantic import BaseModel, Field
from anthropic import Anthropic
import os

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

class CriticalityAgent:
    def __init__(self, model: str = "claude-opus-4-6"):
        api_key = ""
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")

        self.client = Anthropic(api_key=api_key)
        self.model = model

        self.tool_name = "emit_criticality"
        self.tool_schema = {
            "name": self.tool_name,
            "description": "Classify a human location report into severity and category.",
            "input_schema": CriticalityOutput.model_json_schema(),
        }

    def assess(self, content: str) -> CriticalityOutput:
        system = (
            "You classify short human incident reports. "
            "Severity is impact-if-true from 0 (negligible) to 1 (critical). "
            "Return only structured tool output."
        )

        user = f"""
Report:
{content}

Return:
- final_severity (0-1)
- category (enum)
"""

        resp = self.client.messages.create(
            model=self.model,
            system=system,
            max_tokens=200,
            temperature=0.1,
            messages=[{"role": "user", "content": user}],
            tools=[self.tool_schema],
            tool_choice={"type": "tool", "name": self.tool_name},
        )

        tool_calls = [
            c for c in resp.content
            if getattr(c, "type", None) == "tool_use"
            and getattr(c, "name", None) == self.tool_name
        ]

        if not tool_calls:
            raise RuntimeError("Claude did not return structured output")

        return CriticalityOutput.model_validate(tool_calls[0].input)

