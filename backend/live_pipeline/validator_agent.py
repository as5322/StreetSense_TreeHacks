from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from perplexity import Perplexity


# -----------------------------
# Structured output schema
# -----------------------------

class Evidence(BaseModel):
    url: str
    quote: Optional[str] = None


class ValidationResult(BaseModel):
    title: str
    source_url: str
    cleaned_content: str
    summary: str
    plausibility: float = Field(ge=0.0, le=1.0)
    severity_hint: float = Field(ge=0.0, le=1.0)
    flags: List[str]
    evidence: List[Evidence]


# -----------------------------
# Agent
# -----------------------------

class ValidatorAgent:
    """
    Perplexity-backed validation layer.
    """

    def __init__(self, model: str = "sonar-pro"):
        self.client = Perplexity(api_key="")
        self.model = model

    def _build_prompt(self, item: Dict[str, Any]) -> str:
        return f"""
You are a fact-validation and risk-assessment system.

Given the following news item:

TITLE:
{item.get("title")}

URL:
{item.get("url")}

SNIPPET:
{item.get("snippet")}

TASK:

1. Clean and normalize the content into a short factual description.
2. Provide a concise summary.
3. Estimate plausibility (0 to 1) based on:
   - credibility of source
   - presence of corroboration
   - sensational tone
4. Estimate severity_hint (0 to 1) assuming the claim is true.
   Severity reflects impact on public safety or disruption.
5. List any flags:
   - sensational_language
   - unverifiable
   - suspicious_source
   - low_information
6. Provide supporting evidence URLs if available.

Return only structured JSON matching the schema.
"""

    def validate_item(self, item: Dict[str, Any]) -> ValidationResult:
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": self._build_prompt(item)
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "schema": ValidationResult.model_json_schema()
                }
            }
        )

        return ValidationResult.model_validate_json(
            completion.choices[0].message.content
        )

    def validate_batch(self, items: List[Dict[str, Any]]) -> List[ValidationResult]:
        results = []
        for item in items:
            try:
                res = self.validate_item(item)
                results.append(res)
            except Exception as e:
                print(f"Validation failed for {item.get('url')}: {e}")
        return results
