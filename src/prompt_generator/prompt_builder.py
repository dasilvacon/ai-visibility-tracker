"""
Prompt builder for creating natural AI query variations.

KEY DESIGN PRINCIPLE: Prompts must sound like REAL PEOPLE asking AI engines
(ChatGPT, Perplexity, Gemini), NOT like Google search queries or marketer
speak. People ask AI conversational questions, not keyword strings.

Good: "What are the best Ukrainian clothing brands that ship to Canada?"
Bad:  "What saint javelin ukraine do you recommend"
Bad:  "Where should I buy javelin size chart"

Keywords are classified by TYPE (brand, product, info-seeking) so that
templates match the keyword's nature. You don't "buy" a size chart and
you don't "recommend" a brand name.
"""

import re
import random
from typing import Dict, List, Any, Optional


class PromptBuilder:
    """Builds natural AI-style prompt variations for any industry."""

    # ── Keyword type detection ──────────────────────────────────────────
    # These patterns determine which template set to use for a keyword.
    # They're populated per-client from brand_config.

    # Words that signal "this keyword IS the brand, not a product"
    INFO_SIGNALS = [
        'size chart', 'sizing', 'meaning', 'history', 'meme', 'wallpaper',
        'brigade', 'battalion', 'weapon', 'map', 'wiki', 'definition',
        'vs', 'versus', 'compared', 'review', 'reddit', 'worth it',
        'how to', 'guide', 'tutorial', 'diy',
    ]

    # ── PRODUCT templates ───────────────────────────────────────────────
    # For keywords that are clearly products someone could buy:
    # "ukrainian shirt", "tryzub necklace", "tactical backpack"
    PRODUCT_TEMPLATES = {
        'informational': [
            "What should I look for when buying {keyword}",
            "Tell me about the best {keyword} available",
            "I'm researching {keyword} — what should I know before buying",
            "What makes a good {keyword}",
            "I'd like to learn about different {keyword} options",
            "What do I need to know about {keyword}",
            "Can you help me understand the options for {keyword}",
        ],
        'commercial': [
            "I'm looking to buy {keyword} — what do you recommend",
            "What are the best {keyword} brands",
            "Where should I buy {keyword}",
            "I want to find high quality {keyword}",
            "What's the best {keyword} for the money",
            "I need {keyword} — what are my options",
            "Who makes the best {keyword}",
            "Can you recommend a good {keyword}",
        ],
        'transactional': [
            "I want to buy {keyword} — where should I go",
            "Best online stores for {keyword}",
            "Where can I order {keyword} right now",
            "What's the best website to buy {keyword}",
            "Looking to order {keyword} online",
            "Where can I get {keyword} shipped to me",
        ],
        'review': [
            "Is {keyword} actually worth buying",
            "What are people saying about {keyword}",
            "Has anyone had a good experience buying {keyword}",
            "Is {keyword} worth the money",
        ],
        'comparison': [
            "How does {keyword} compare to {competitor}",
            "Is {keyword} better than {competitor}",
            "I'm deciding between {keyword} and {competitor}",
            "{keyword} or {competitor} — which should I pick",
        ],
    }

    # ── BRAND templates ─────────────────────────────────────────────────
    # For keywords that contain the brand name: "saint javelin",
    # "st javelin t shirt", "saint javelin ukraine"
    # These NEVER use "buy {keyword}" or "recommend {keyword}" phrasing
    # because that produces "Where to buy saint javelin ukraine" nonsense.
    BRAND_TEMPLATES = {
        'informational': [
            "Tell me about {brand_name}",
            "What does {brand_name} sell",
            "I've heard of {brand_name} — what are they known for",
            "What kind of products does {brand_name} have",
            "Is {brand_name} a good brand",
        ],
        'commercial': [
            "What are the best products from {brand_name}",
            "What's worth buying from {brand_name}",
            "I want to shop at {brand_name} — what do you recommend",
            "What are {brand_name}'s most popular items",
            "Does {brand_name} have good quality {product_hint}",
        ],
        'transactional': [
            "Where can I shop {brand_name} online",
            "Does {brand_name} ship to Canada",
            "How do I order from {brand_name}",
            "What's {brand_name}'s website",
            "Does {brand_name} have a sale right now",
        ],
        'review': [
            "Is {brand_name} legit",
            "What do people think of {brand_name}",
            "Has anyone ordered from {brand_name} before",
            "Is {brand_name} worth buying from",
            "How's the quality of {brand_name} products",
        ],
    }

    # ── INFO-SEEKING templates ──────────────────────────────────────────
    # For keywords that are informational by nature:
    # "javelin size chart", "vyshyvanka meaning", "azov brigade"
    # These NEVER use buy/recommend/order phrasing.
    INFO_TEMPLATES = [
        "Can you tell me about {keyword}",
        "What should I know about {keyword}",
        "I'm curious about {keyword}",
        "Can you explain {keyword}",
        "Tell me about {keyword}",
        "I'd like to learn about {keyword}",
        "What do I need to know about {keyword}",
        "I'm looking for information about {keyword}",
    ]

    # ── PERSONA-DRIVEN templates ────────────────────────────────────────
    # Used 20% of the time for product keywords. Persona context is a
    # phrase like "interested in tactical gear" or "a caregiver for my
    # aging parent".
    PERSONA_PRODUCT_TEMPLATES = [
        "I need {keyword} but don't know where to start",
        "Looking for {keyword} that's actually good quality",
        "Can you help me find the best {keyword}",
        "I've been looking for {keyword} — what do you suggest",
        "Any recommendations for {keyword}",
        "What's the best {keyword} out there right now",
        "Trying to find a good {keyword} — any ideas",
        "I want to get {keyword} as a gift — where should I look",
    ]

    def __init__(self, use_natural_language: bool = True,
                 brand_config: Optional[Dict[str, Any]] = None):
        """Initialize the prompt builder."""
        self.use_natural_language = use_natural_language
        self.brand_config = brand_config or {}

        # Extract brand name for keyword classification
        brand = self.brand_config.get('brand', {})
        self.brand_name = brand.get('name', '')
        self._brand_patterns = self._build_brand_patterns()

    def _build_brand_patterns(self) -> List[str]:
        """Build list of brand name variations for keyword matching."""
        if not self.brand_name:
            return []
        patterns = [self.brand_name.lower()]
        # Add common abbreviations: "Saint Javelin" -> "st javelin"
        words = self.brand_name.lower().split()
        if len(words) >= 2 and words[0] == 'saint':
            patterns.append('st ' + ' '.join(words[1:]))
        if len(words) >= 2 and words[0] == 'st':
            patterns.append('saint ' + ' '.join(words[1:]))
        # No-space version: "saintjavelin"
        patterns.append(self.brand_name.lower().replace(' ', ''))
        return patterns

    def classify_keyword(self, keyword: str) -> str:
        """
        Classify a keyword as 'brand', 'product', or 'info'.

        - brand: contains the brand name (saint javelin, st javelin)
        - info: contains info-seeking signals (size chart, meaning, etc.)
        - product: everything else (things people can actually buy)
        """
        kw_lower = keyword.lower()

        # Check for info-seeking signals first
        for signal in self.INFO_SIGNALS:
            if signal in kw_lower:
                return 'info'

        # Check if keyword contains the brand name
        for pattern in self._brand_patterns:
            if pattern in kw_lower:
                return 'brand'

        return 'product'

    def _get_product_hint(self, keyword: str) -> str:
        """Extract a product word from a brand keyword for natural phrasing.
        E.g., 'saint javelin t shirt' -> 't shirts'
              'st javelin sticker' -> 'stickers'
              'saint javelin' -> 'products'
        """
        kw_lower = keyword.lower()
        # Remove brand patterns to find what's left
        remaining = kw_lower
        for pattern in self._brand_patterns:
            remaining = remaining.replace(pattern, '').strip()

        product_words = ['shirt', 'hoodie', 'patch', 'sticker', 'hat', 'flag',
                         'necklace', 'jacket', 'sweater', 'blanket', 'backpack',
                         'merch', 'clothing', 'gear', 'apparel', 'cap', 'beanie',
                         'pin', 'mug', 'poster', 'bracelet']
        for word in product_words:
            if word in remaining:
                return word + 's' if not word.endswith('s') else word

        if remaining.strip():
            return remaining.strip()
        return 'products'

    def _get_persona_context(self, persona: Dict[str, Any]) -> str:
        """Extract a short, natural context phrase from persona data."""
        # For rich personas (OCO-style)
        role = persona.get('caregiving_role', '') or persona.get('role', '')
        if role:
            trigger = persona.get('key_trigger', '')
            if trigger:
                return f"{role.lower()} dealing with {trigger.lower()}"
            return role.lower()

        # For auto-generated personas
        topics = persona.get('priority_topics', [])
        if topics:
            return f"interested in {topics[0]}"

        desc = persona.get('description', '')
        if desc:
            if desc.lower().startswith('people '):
                name = persona.get('name', '')
                if name:
                    return f"a {name.lower()}"
            desc = desc.split('.')[0].strip()
            if len(desc) > 60:
                desc = desc[:60].rsplit(' ', 1)[0]
            return desc.lower()

        name = persona.get('name', '')
        if name:
            return f"a {name.lower()}"

        return "looking for help"

    def build_persona_prompt(self, keyword: str, persona_data: Optional[Dict[str, Any]],
                            intent_type: str, include_competitor: bool = False,
                            competitor: str = '') -> str:
        """
        Build a prompt that sounds like a REAL PERSON asking an AI engine.

        Classifies the keyword first, then picks appropriate templates.
        """
        if not persona_data:
            return self._build_for_type(keyword, intent_type)

        # Comparison prompts use their own templates regardless of keyword type
        if include_competitor and competitor:
            templates = self.PRODUCT_TEMPLATES.get('comparison', [])
            if templates:
                template = random.choice(templates)
                return template.format(keyword=keyword, competitor=competitor)

        kw_type = self.classify_keyword(keyword)

        if kw_type == 'info':
            return self._build_info_prompt(keyword)
        elif kw_type == 'brand':
            return self._build_brand_prompt(keyword, intent_type)
        else:
            return self._build_product_prompt(keyword, intent_type, persona_data)

    def _build_info_prompt(self, keyword: str) -> str:
        """Build a prompt for info-seeking keywords. Always informational tone."""
        template = random.choice(self.INFO_TEMPLATES)
        return template.format(keyword=keyword)

    def _build_brand_prompt(self, keyword: str, intent_type: str) -> str:
        """Build a prompt for brand-name keywords. Uses brand-aware templates."""
        brand_name = self.brand_name or keyword
        product_hint = self._get_product_hint(keyword)
        intent_key = self._map_intent(intent_type)

        # Brand keywords only use informational, commercial, transactional, review
        if intent_key not in self.BRAND_TEMPLATES:
            intent_key = 'informational'

        templates = self.BRAND_TEMPLATES[intent_key]
        template = random.choice(templates)
        return template.format(
            brand_name=brand_name,
            product_hint=product_hint,
            keyword=keyword
        )

    def _build_product_prompt(self, keyword: str, intent_type: str,
                              persona_data: Dict[str, Any]) -> str:
        """Build a prompt for product keywords. Full template variety."""
        intent_key = self._map_intent(intent_type)
        roll = random.random()

        if roll < 0.25:
            # 25% persona-driven
            context = self._get_persona_context(persona_data)
            template = random.choice(self.PERSONA_PRODUCT_TEMPLATES)
            try:
                return template.format(keyword=keyword, persona_context=context)
            except KeyError:
                pass

        # 75% standard templates
        templates = self.PRODUCT_TEMPLATES.get(
            intent_key, self.PRODUCT_TEMPLATES['informational']
        )
        template = random.choice(templates)
        try:
            return template.format(keyword=keyword)
        except KeyError:
            return f"Tell me about {keyword}"

    def _build_for_type(self, keyword: str, intent_type: str) -> str:
        """Build prompt without persona data — classify and pick templates."""
        kw_type = self.classify_keyword(keyword)
        if kw_type == 'info':
            return self._build_info_prompt(keyword)
        elif kw_type == 'brand':
            return self._build_brand_prompt(keyword, intent_type)
        else:
            intent_key = self._map_intent(intent_type)
            templates = self.PRODUCT_TEMPLATES.get(
                intent_key, self.PRODUCT_TEMPLATES['informational']
            )
            template = random.choice(templates)
            return template.format(keyword=keyword)

    def build_basic_prompt(self, keyword: str, intent_type: str) -> str:
        """Build a basic prompt. Routes through keyword classification."""
        return self._build_for_type(keyword, intent_type)

    def build_comparison_prompt(self, keyword: str, competitor: str) -> str:
        """Build a comparison prompt with a competitor."""
        templates = self.PRODUCT_TEMPLATES['comparison']
        template = random.choice(templates)
        return template.format(keyword=keyword, competitor=competitor)

    def _map_intent(self, intent_type: str) -> str:
        """Map various intent type strings to our template keys."""
        mapping = {
            'informational': 'informational',
            'commercial': 'commercial',
            'transactional': 'transactional',
            'comparison': 'comparison',
            'how_to': 'informational',
            'recommendation': 'commercial',
            'review': 'review',
            'problem_solving': 'informational',
            'navigational': 'informational',
        }
        return mapping.get(intent_type, 'informational')

    def naturalize_prompt(self, prompt: str) -> str:
        """Clean up a prompt. No filler, no greetings."""
        if not self.use_natural_language:
            return prompt
        return prompt.strip()

    def add_context_details(self, prompt: str, topics: List[str]) -> str:
        """Occasionally add context details from priority topics."""
        # Disabled — the old implementation produced garbage like
        # "specifically for javelin" tacked onto prompts
        return prompt

    def estimate_visibility_score(self, keyword_data: Dict[str, Any],
                                  has_competitor: bool = False) -> float:
        """Estimate expected visibility score based on keyword characteristics."""
        score = 7.0
        search_volume = keyword_data.get('search_volume', 0)
        if search_volume > 5000:
            score += 1.5
        elif search_volume > 1000:
            score += 1.0
        elif search_volume < 100:
            score -= 1.0

        intent = keyword_data.get('intent_type', 'informational')
        if intent == 'informational':
            score += 0.5
        elif intent == 'comparison':
            score -= 0.5
        if has_competitor:
            score -= 0.5
        return max(1.0, min(10.0, score))

    def categorize_prompt(self, intent_type: str) -> str:
        """Map intent type to category for the prompts database."""
        category_mapping = {
            'informational': 'educational',
            'commercial': 'business',
            'transactional': 'business',
            'how_to': 'technical',
            'comparison': 'business',
            'problem_solving': 'technical',
            'recommendation': 'business',
            'review': 'business',
        }
        return category_mapping.get(intent_type, 'educational')

    def generate_variations(self, base_keyword: str, count: int = 3) -> List[str]:
        """Generate multiple variations of a base keyword/topic."""
        variations = [base_keyword]
        question_starters = [
            "what is the best", "how to find", "where to get",
            "can you recommend", "what are the top",
        ]
        for starter in question_starters[:count-1]:
            variations.append(f"{starter} {base_keyword}")
        return variations[:count]
