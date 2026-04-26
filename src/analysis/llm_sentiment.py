"""
LLM-based sentiment classifier for brand mentions in AI responses.

Why this exists:
  The keyword-based sentiment classifier in html_report_generator.py was
  systematically misclassifying favorable mentions as negative because it
  matched on words like "expensive" without understanding context. Lumo's
  audit found ALL 5 "negative" examples were actually positive — quotes
  like "Lumo eliminates the need for expensive separate controllers" got
  tagged Negative because the word "expensive" appeared, even though the
  sentence was praising Lumo for eliminating expense.

What this does:
  Takes (brand_name, context_snippet) → 'positive' | 'neutral' | 'negative'.
  Uses Claude Sonnet 4.6 with a focused prompt that explicitly handles
  negation, comparison, and "X eliminates Y" patterns.

Cost / caching:
  Cheap: ~$0.0014 per call at Sonnet 4.6 prices. A typical client report
  has 80-200 brand mentions, so first regen is ~$0.10-0.30. Subsequent
  regens hit a per-client cache keyed on hash(brand_name + context) and
  pay almost nothing.

Fallback:
  If ANTHROPIC_API_KEY is missing or the API call fails, classify() returns
  None so callers can fall back to the keyword classifier instead of
  silently returning a wrong answer.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Optional


CLASSIFICATION_PROMPT_TEMPLATE = """You are classifying how an AI search engine described the brand "{brand_name}" in the snippet below.

Classify the sentiment as exactly one of:
- positive: clearly favorable language about {brand_name} (e.g. "industry-leading", "best for X", "the standout choice", being recommended)
- neutral: factual or descriptive without clear opinion (e.g. listing features alongside competitors, describing what the product does, appearing in a comparison without judgment)
- negative: clearly unfavorable language about {brand_name} (e.g. "lacking", "outdated", "not as good as competitor X", being recommended against, or being explicitly excluded for a use case)

Crucial nuances:
- When negative words appear in the snippet, check whether they describe {brand_name} ITSELF or something {brand_name} AVOIDS, REPLACES, or BEATS. For example: "{brand_name} eliminates expensive controllers" is POSITIVE for {brand_name} (eliminating something expensive is good); "{brand_name} is expensive" is NEGATIVE for {brand_name}.
- Being listed alongside competitors in a feature comparison is NEUTRAL unless the comparison explicitly favors or disfavors {brand_name}.
- "Limited to small teams" or "designed for a specific niche" is NEUTRAL (just describes positioning), not negative.
- A factual feature description ("offers X, Y, and Z") is NEUTRAL.

Respond with exactly one lowercase word: positive, neutral, or negative. No explanation, no punctuation.

Snippet:
{context}"""


class LLMSentimentClassifier:
    """LLM-backed sentiment classifier with disk cache + keyword fallback."""

    def __init__(
        self,
        brand_name: str,
        client_slug: Optional[str] = None,
        cache_dir: str = "data/sentiment_cache",
        model: str = "claude-sonnet-4-6",
    ):
        self.brand_name = brand_name
        self.client_slug = client_slug
        self.model = model
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict = self._load_cache()
        self._client = None  # Lazy-init the Anthropic client
        self._client_init_attempted = False
        # Stats — useful for log lines / debugging
        self.calls = 0
        self.hits = 0
        self.fallbacks = 0

    # ------ cache ------

    def _cache_path(self) -> Path:
        slug = self.client_slug or "_global"
        return self.cache_dir / f"{slug}_sentiment.json"

    def _load_cache(self) -> dict:
        path = self._cache_path()
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_cache(self) -> None:
        try:
            self._cache_path().write_text(json.dumps(self._cache, indent=2))
        except OSError:
            # Cache write failure is non-fatal — we can recompute next run
            pass

    def _cache_key(self, context: str) -> str:
        h = hashlib.sha256()
        h.update((self.brand_name + "||" + context).encode("utf-8", errors="replace"))
        return h.hexdigest()

    # ------ client ------

    def _get_client(self):
        """Lazy-init the Anthropic client. Returns None if not available."""
        if self._client_init_attempted:
            return self._client
        self._client_init_attempted = True

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        try:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=api_key)
            return self._client
        except ImportError:
            return None

    # ------ public API ------

    def classify(self, context: str) -> Optional[str]:
        """
        Classify a single snippet.

        Returns 'positive', 'neutral', or 'negative' on success. Returns None
        if the LLM is unavailable or the call failed — caller should fall
        back to keyword classification.
        """
        if not context or not context.strip():
            return "neutral"

        # Cache hit
        key = self._cache_key(context)
        if key in self._cache:
            self.hits += 1
            return self._cache[key]

        client = self._get_client()
        if client is None:
            self.fallbacks += 1
            return None

        prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(
            brand_name=self.brand_name,
            context=context,
        )

        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=10,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            )
            self.calls += 1
            raw = response.content[0].text.strip().lower()
            # Defensive: only accept the three valid labels
            if raw not in ("positive", "neutral", "negative"):
                # Try to extract by prefix match — some models add punctuation
                for label in ("positive", "negative", "neutral"):
                    if raw.startswith(label):
                        raw = label
                        break
                else:
                    raw = "neutral"

            self._cache[key] = raw
            # Save every N calls so a crash mid-run doesn't lose all progress
            if self.calls % 25 == 0:
                self._save_cache()
            return raw
        except Exception:
            self.fallbacks += 1
            return None

    def flush(self) -> None:
        """Persist the cache. Call after a batch of classify() calls."""
        self._save_cache()

    def stats(self) -> dict:
        return {
            "calls": self.calls,
            "cache_hits": self.hits,
            "fallbacks": self.fallbacks,
            "cache_size": len(self._cache),
        }
