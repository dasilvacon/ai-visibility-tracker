"""
Prompt builder for creating natural AI query variations.

KEY DESIGN PRINCIPLE: Prompts must sound like REAL PEOPLE asking AI engines
(ChatGPT, Perplexity, Gemini), NOT like Google search queries or marketer
speak. People ask AI conversational questions, not keyword strings.

Good: "What are the best Ukrainian clothing brands that ship to Canada?"
Bad:  "ukraine shirt services Ontario"
Bad:  "who qualifies for tryzub necklace"

Templates are INDUSTRY-AGNOSTIC — they work for any client (e-commerce,
services, nonprofits, B2B). Client-specific context comes from brand_config
and persona data, never hardcoded.
"""

import random
from typing import Dict, List, Any, Optional


class PromptBuilder:
    """Builds natural AI-style prompt variations for any industry."""

    # ── STYLE 1: Direct AI Questions (30%) ────────────────────────────
    # Clean, conversational questions people ask AI engines
    DIRECT_TEMPLATES = {
        'informational': [
            "What is {keyword}",
            "Tell me about {keyword}",
            "What should I know about {keyword}",
            "Can you explain {keyword}",
            "What are the best {keyword}",
        ],
        'commercial': [
            "Best {keyword} to buy",
            "Top rated {keyword}",
            "What {keyword} do you recommend",
            "Most popular {keyword}",
            "Where to buy {keyword}",
        ],
        'transactional': [
            "Where can I buy {keyword}",
            "Best place to order {keyword}",
            "Where to get {keyword} online",
            "{keyword} for sale",
            "Buy {keyword} online",
        ],
        'comparison': [
            "{keyword} vs {competitor}",
            "How does {keyword} compare to {competitor}",
            "Should I choose {keyword} or {competitor}",
            "What's the difference between {keyword} and {competitor}",
        ],
        'how_to': [
            "How to {keyword}",
            "Best way to {keyword}",
            "How do I {keyword}",
            "Step by step guide to {keyword}",
        ],
        'recommendation': [
            "What {keyword} do you recommend",
            "Best {keyword} right now",
            "Top {keyword} options",
            "Which {keyword} should I get",
        ],
        'review': [
            "Is {keyword} worth it",
            "Honest review of {keyword}",
            "{keyword} pros and cons",
            "What do people think about {keyword}",
        ],
    }

    # ── STYLE 2: Conversational AI Prompts (50%) ─────────────────────
    # These sound like how people actually talk to ChatGPT/Perplexity.
    # No hardcoded locations or industries — uses {context} from brand config.
    CONVERSATIONAL_TEMPLATES = {
        'informational': [
            "What are the best options for {keyword}",
            "I'm looking for information about {keyword}",
            "Can you help me understand {keyword}",
            "What do I need to know about {keyword}",
            "I want to learn more about {keyword}",
            "Tell me about the best {keyword} available",
            "What makes a good {keyword}",
            "I'm researching {keyword} — what should I know",
        ],
        'commercial': [
            "I'm looking to buy {keyword} — what do you recommend",
            "What are the best {keyword} brands",
            "Where should I buy {keyword}",
            "I want to find high quality {keyword}",
            "What's the best {keyword} for the money",
            "Can you recommend good {keyword}",
            "I need {keyword} — what are my options",
            "Who makes the best {keyword}",
        ],
        'transactional': [
            "I want to buy {keyword} — where should I go",
            "Best online stores for {keyword}",
            "Where can I order {keyword} right now",
            "I need to find {keyword} to purchase",
            "What's the best website to buy {keyword}",
            "Looking to order {keyword} online",
        ],
        'comparison': [
            "How does {keyword} compare to {competitor}",
            "Is {keyword} better than {competitor}",
            "I'm deciding between {keyword} and {competitor}",
            "{keyword} or {competitor} — which should I pick",
            "Compare {keyword} and {competitor} for me",
        ],
        'how_to': [
            "How do I {keyword}",
            "What's the best way to {keyword}",
            "Can you walk me through how to {keyword}",
            "I need help with {keyword}",
            "What's the process for {keyword}",
        ],
        'recommendation': [
            "What would you recommend for {keyword}",
            "I need a good {keyword} — any suggestions",
            "What's the best {keyword} you'd recommend",
            "Help me find the right {keyword}",
            "What {keyword} would work best",
        ],
        'review': [
            "Is {keyword} actually good",
            "What's the real deal with {keyword}",
            "Has anyone had a good experience with {keyword}",
            "What are people saying about {keyword}",
            "Is {keyword} worth the money",
        ],
    }

    # ── STYLE 3: Persona-Driven Situation Prompts (20%) ──────────────
    # These use the persona description to add context. The persona
    # description is used directly (not hardcoded trigger maps), making
    # this work for ANY industry.
    PERSONA_TEMPLATES = [
        # Situation-driven (persona_context is a phrase like "interested in X"
        # or "a caregiver for my aging parent")
        "I'm {persona_context} and I need {keyword}",
        "As someone {persona_context}, what {keyword} would you recommend",
        "I'm {persona_context} — where can I find {keyword}",
        "I need {keyword} because I'm {persona_context}",
        "What {keyword} would work for someone who is {persona_context}",

        # Need-driven (generic, works for any industry)
        "I need {keyword} but don't know where to start",
        "Looking for {keyword} that's actually good quality",
        "Can you help me find {keyword}",
        "What's the best {keyword} for my situation",
        "I've been looking for {keyword} — what do you suggest",
    ]

    def __init__(self, use_natural_language: bool = True,
                 brand_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the prompt builder.

        Args:
            use_natural_language: Whether to use natural language variations
            brand_config: Brand configuration for industry context
        """
        self.use_natural_language = use_natural_language
        self.brand_config = brand_config or {}

    def _get_persona_context(self, persona: Dict[str, Any]) -> str:
        """
        Extract a short, natural context phrase from persona data.
        Works with ANY persona structure — uses description, role,
        key_trigger, etc. Returns a phrase like "looking for Ukrainian
        clothing" or "a caregiver for my aging parent."

        For auto-generated personas (topic-clustered), uses priority_topics
        to create natural phrases like "interested in tactical backpacks"
        instead of the full description which reads badly in templates.
        """
        # For rich personas (OCO-style) — use caregiving_role or key_trigger
        role = persona.get('caregiving_role', '') or persona.get('role', '')
        if role:
            trigger = persona.get('key_trigger', '')
            if trigger:
                return f"{role.lower()} dealing with {trigger.lower()}"
            return role.lower()

        # For auto-generated personas — use priority_topics for natural phrases
        topics = persona.get('priority_topics', [])
        if topics:
            # Use the top topic to create a natural phrase
            top_topic = topics[0]
            return f"interested in {top_topic}"

        # Fall back to description, but clean it up
        desc = persona.get('description', '')
        if desc:
            # Skip auto-generated descriptions that start with "People searching for"
            if desc.lower().startswith('people '):
                name = persona.get('name', '')
                if name:
                    return f"a {name.lower()}"
            # Take first sentence or first 60 chars
            desc = desc.split('.')[0].strip()
            if len(desc) > 60:
                desc = desc[:60].rsplit(' ', 1)[0]
            return desc.lower()

        name = persona.get('name', '')
        if name:
            return f"a {name.lower()}"

        return "looking for help"

    def build_basic_prompt(self, keyword: str, intent_type: str) -> str:
        """Build a basic prompt (no persona context). Used as fallback."""
        # Map intent types that don't have direct templates
        intent_key = self._map_intent(intent_type)
        templates = self.DIRECT_TEMPLATES.get(intent_key, self.DIRECT_TEMPLATES['informational'])
        template = random.choice(templates)
        return template.format(keyword=keyword)

    def build_comparison_prompt(self, keyword: str, competitor: str) -> str:
        """Build a comparison prompt with a competitor."""
        templates = self.DIRECT_TEMPLATES['comparison'] + self.CONVERSATIONAL_TEMPLATES['comparison']
        template = random.choice(templates)
        return template.format(keyword=keyword, competitor=competitor)

    def build_persona_prompt(self, keyword: str, persona_data: Optional[Dict[str, Any]],
                            intent_type: str, include_competitor: bool = False,
                            competitor: str = '') -> str:
        """
        Build a prompt that sounds like a REAL PERSON asking an AI engine.

        The persona shapes the situational context but the persona LABEL
        never appears in the output text.

        50% conversational, 30% direct, 20% persona-driven situation.
        """
        if not persona_data:
            return self.build_basic_prompt(keyword, intent_type)

        # Comparison prompts
        if include_competitor and competitor:
            templates = self.CONVERSATIONAL_TEMPLATES.get('comparison', self.DIRECT_TEMPLATES['comparison'])
            template = random.choice(templates)
            return template.format(keyword=keyword, competitor=competitor)

        intent_key = self._map_intent(intent_type)
        roll = random.random()

        if roll < 0.30:
            # 30% direct AI questions
            return self.build_basic_prompt(keyword, intent_type)

        elif roll < 0.80:
            # 50% conversational AI prompts
            templates = self.CONVERSATIONAL_TEMPLATES.get(
                intent_key, self.CONVERSATIONAL_TEMPLATES['informational']
            )
            template = random.choice(templates)
            prompt = template.format(keyword=keyword)

        else:
            # 20% persona-driven situation prompts
            context = self._get_persona_context(persona_data)
            template = random.choice(self.PERSONA_TEMPLATES)
            try:
                prompt = template.format(keyword=keyword, persona_context=context)
            except KeyError:
                prompt = f"Can you help me find {keyword}"

        # Inject a priority topic naturally (15% of time)
        topics = persona_data.get('priority_topics', [])
        if topics and random.random() < 0.15:
            topic = random.choice(topics)
            suffixes = [
                f", specifically for {topic}",
                f" — especially related to {topic}",
                f" for {topic}",
            ]
            prompt += random.choice(suffixes)

        return prompt

    def _map_intent(self, intent_type: str) -> str:
        """Map various intent type strings to our template keys."""
        mapping = {
            'informational': 'informational',
            'commercial': 'commercial',
            'transactional': 'transactional',
            'comparison': 'comparison',
            'how_to': 'how_to',
            'recommendation': 'recommendation',
            'review': 'review',
            # Common aliases
            'problem_solving': 'how_to',
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
        if random.random() > 0.15 or not topics:
            return prompt

        topic = random.choice(topics)
        context_formats = [
            f"{prompt}, specifically for {topic}",
            f"{prompt} related to {topic}",
        ]
        result = random.choice(context_formats)
        if len(result.split()) > 25:
            return prompt
        return result

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
