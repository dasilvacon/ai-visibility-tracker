"""
Prompt builder for creating natural query variations.
"""

import random
from typing import Dict, List, Any, Optional


class PromptBuilder:
    """Builds natural prompt variations from keywords and personas."""

    # STYLE 1: Direct Search Query (40%) - Clean, keyword-focused, no fluff
    DIRECT_TEMPLATES = {
        'informational': [
            "Best {keyword}",
            "{keyword} guide",
            "{keyword} explained",
            "Top {keyword} options",
            "{keyword} recommendations",
        ],
        'how_to': [
            "How to {keyword}",
            "{keyword} tutorial",
            "{keyword} step by step",
            "Best way to {keyword}",
        ],
        'comparison': [
            "{keyword} vs {competitor}",
            "{keyword} compared to {competitor}",
            "{keyword} or {competitor}",
            "Differences between {keyword} and {competitor}",
        ],
        'problem_solving': [
            "{keyword} solution",
            "Fix {keyword}",
            "{keyword} not working",
            "Solve {keyword}",
        ],
        'recommendation': [
            "Best {keyword}",
            "Top {keyword}",
            "{keyword} recommendations",
            "Which {keyword} to buy",
        ],
        'review': [
            "{keyword} review",
            "{keyword} worth it",
            "Is {keyword} good",
            "{keyword} quality",
        ]
    }

    # STYLE 2: Conversational Question (60%) - Natural with context, NO greetings
    CONVERSATIONAL_TEMPLATES = {
        'informational': [
            "Looking for information on {keyword}",
            "I need to understand {keyword}",
            "What makes {keyword} different from other options",
            "Can someone explain {keyword}",
            "Trying to learn about {keyword}",
        ],
        'how_to': [
            "I want to learn how to {keyword}",
            "What's the right way to {keyword}",
            "Need help learning to {keyword}",
            "Trying to figure out how to {keyword}",
        ],
        'comparison': [
            "How does {keyword} compare to {competitor}",
            "Should I choose {keyword} or {competitor}",
            "What's the difference between {keyword} and {competitor}",
            "Is {keyword} better than {competitor}",
            "Trying to decide between {keyword} and {competitor}",
        ],
        'problem_solving': [
            "I'm having trouble with {keyword}",
            "Need help fixing {keyword}",
            "{keyword} keeps failing, what works better",
            "Struggling with {keyword}, any solutions",
        ],
        'recommendation': [
            "Looking for the best {keyword}",
            "I need a good {keyword}",
            "What {keyword} should I get",
            "Need recommendations for {keyword}",
        ],
        'review': [
            "Is {keyword} actually worth it",
            "Should I invest in {keyword}",
            "Anyone have experience with {keyword}",
            "Is {keyword} worth the price",
        ]
    }

    # Persona-specific context patterns
    PERSONA_CONTEXTS = {
        'Luxury Beauty Enthusiast': [
            "Looking for high-end {keyword} with {quality}",
            "Is {keyword} worth the investment",
            "Want luxury {keyword} that {benefit}",
            "Interested in premium {keyword}",
        ],
        'Professional Makeup Artist': [
            "Working makeup artist looking for {keyword} that {performance}",
            "Best {keyword} for bridal work",
            "Professional-grade {keyword} recommendations",
            "Need {keyword} that lasts 12+ hours for clients",
        ],
        'Specific Need Shopper': [
            "I have {problem} and {keyword} always {fails}, what works",
            "Best {keyword} for {specific_need}",
            "{keyword} that actually works on {condition}",
            "My {problem} means most {keyword} fails, need better options",
        ],
        'Beauty Beginner': [
            "New to luxury makeup, is {keyword} beginner-friendly",
            "First high-end palette, which {keyword} is easiest to use",
            "Best {keyword} for someone just learning",
            "Learning makeup, is {keyword} good for beginners",
        ],
    }

    # Pain points and specific needs by category
    PAIN_POINTS = {
        'oily skin': ['creasing', 'fading by noon', 'sliding off'],
        'hooded eyes': ['disappearing', 'transferring to crease', 'not visible'],
        'mature skin': ['settling in lines', 'emphasizing texture', 'looking cakey'],
        'sensitive skin': ['irritation', 'redness', 'burning'],
    }

    SPECIFIC_NEEDS = [
        'oily lids', 'hooded eyes', 'mature skin', 'deep skin tones',
        'pale skin', 'sensitive eyes', 'contact lenses'
    ]

    QUALITIES = [
        'excellent pigmentation', 'smooth blending', 'zero fallout',
        'long wear', 'buildable coverage', 'true color payoff'
    ]

    PERFORMANCE_REQS = [
        'lasts 12+ hours', 'no creasing', 'stays vibrant',
        'photographs well', 'blends easily', 'minimal fallout'
    ]

    def __init__(self, use_natural_language: bool = True):
        """
        Initialize the prompt builder.

        Args:
            use_natural_language: Whether to use natural language variations
        """
        self.use_natural_language = use_natural_language

    def build_basic_prompt(self, keyword: str, intent_type: str) -> str:
        """
        Build a basic prompt from a keyword and intent.

        Args:
            keyword: The keyword or topic
            intent_type: The intent type

        Returns:
            Generated prompt string
        """
        # Avoid comparison templates for basic prompts
        if intent_type == 'comparison':
            intent_type = 'informational'

        # 40% direct, 60% conversational
        use_direct = random.random() < 0.4

        if use_direct:
            templates = self.DIRECT_TEMPLATES.get(intent_type, self.DIRECT_TEMPLATES['informational'])
        else:
            templates = self.CONVERSATIONAL_TEMPLATES.get(intent_type, self.CONVERSATIONAL_TEMPLATES['informational'])

        template = random.choice(templates)
        return template.format(keyword=keyword)

    def build_comparison_prompt(self, keyword: str, competitor: str) -> str:
        """
        Build a comparison prompt with a competitor.

        Args:
            keyword: The main keyword/product
            competitor: The competitor to compare against

        Returns:
            Generated comparison prompt
        """
        # 40% direct, 60% conversational
        use_direct = random.random() < 0.4

        if use_direct:
            templates = self.DIRECT_TEMPLATES['comparison']
        else:
            templates = self.CONVERSATIONAL_TEMPLATES['comparison']

        template = random.choice(templates)
        return template.format(keyword=keyword, competitor=competitor)

    def build_persona_prompt(self, keyword: str, persona_context: str, intent_type: str) -> str:
        """
        Build a prompt that incorporates persona context naturally.

        Args:
            keyword: The keyword or topic
            persona_context: Context about the persona
            intent_type: The intent type

        Returns:
            Generated prompt with persona context
        """
        # Try to use persona-specific templates 30% of the time
        if random.random() < 0.3:
            persona_templates = self.PERSONA_CONTEXTS.get(persona_context, [])
            if persona_templates:
                template = random.choice(persona_templates)

                # Fill in placeholders
                filled = template.replace('{keyword}', keyword)

                # Add contextual details
                if '{quality}' in filled:
                    filled = filled.replace('{quality}', random.choice(self.QUALITIES))
                if '{performance}' in filled:
                    filled = filled.replace('{performance}', random.choice(self.PERFORMANCE_REQS))
                if '{benefit}' in filled:
                    benefits = ['lasts all day', 'blends perfectly', 'looks natural']
                    filled = filled.replace('{benefit}', random.choice(benefits))
                if '{problem}' in filled:
                    problems = ['oily lids', 'hooded eyes', 'mature skin', 'deep skin tone']
                    filled = filled.replace('{problem}', random.choice(problems))
                if '{specific_need}' in filled:
                    filled = filled.replace('{specific_need}', random.choice(self.SPECIFIC_NEEDS))
                if '{fails}' in filled:
                    fails = ['creases', 'fades', 'disappears', 'transfers']
                    filled = filled.replace('{fails}', random.choice(fails))
                if '{condition}' in filled:
                    filled = filled.replace('{condition}', random.choice(self.SPECIFIC_NEEDS))

                return filled

        # Otherwise build a standard prompt
        base_prompt = self.build_basic_prompt(keyword, intent_type)

        # Add natural persona framing occasionally (30% of the time)
        if random.random() < 0.3:
            persona_frames = [
                f"I'm a {persona_context.lower()}, {base_prompt.lower()}",
                f"{base_prompt} - I'm {persona_context.lower()}",
            ]
            return random.choice(persona_frames)

        return base_prompt

    def naturalize_prompt(self, prompt: str) -> str:
        """
        Make a prompt sound more natural (NO FILLER WORDS).

        Args:
            prompt: The prompt to naturalize

        Returns:
            Natural-sounding prompt without greetings or fluff
        """
        if not self.use_natural_language:
            return prompt

        # NO greetings, NO filler, NO pleasantries
        # Just return the prompt as-is since templates are already natural
        return prompt.strip()

    def add_context_details(self, prompt: str, topics: List[str]) -> str:
        """
        Occasionally add context details from priority topics.

        Args:
            prompt: The base prompt
            topics: List of relevant topics to potentially reference

        Returns:
            Prompt with optional context
        """
        # Only add context 15% of the time to keep prompts diverse
        if random.random() > 0.15 or not topics:
            return prompt

        topic = random.choice(topics)

        # Add context naturally without adding token bloat
        context_formats = [
            f"{prompt} specifically for {topic}",
            f"{prompt} focused on {topic}",
        ]

        result = random.choice(context_formats)

        # Keep it under 25 words
        word_count = len(result.split())
        if word_count > 25:
            return prompt

        return result

    def estimate_visibility_score(self, keyword_data: Dict[str, Any],
                                  has_competitor: bool = False) -> float:
        """
        Estimate expected visibility score based on keyword characteristics.

        Args:
            keyword_data: Dictionary with keyword information
            has_competitor: Whether this prompt includes a competitor mention

        Returns:
            Estimated visibility score (1-10)
        """
        # Base score starts at 7
        score = 7.0

        # High search volume keywords likely have more content = higher visibility
        search_volume = keyword_data.get('search_volume', 0)
        if search_volume > 5000:
            score += 1.5
        elif search_volume > 1000:
            score += 1.0
        elif search_volume < 100:
            score -= 1.0

        # Informational queries typically have good coverage
        intent = keyword_data.get('intent_type', 'informational')
        if intent == 'informational':
            score += 0.5
        elif intent == 'comparison':
            score -= 0.5  # Comparison queries may have less direct coverage

        # Competitor mentions might reduce score if brand isn't well positioned
        if has_competitor:
            score -= 0.5

        # Clamp between 1 and 10
        return max(1.0, min(10.0, score))

    def categorize_prompt(self, intent_type: str) -> str:
        """
        Map intent type to category for the prompts database.

        Args:
            intent_type: The intent type

        Returns:
            Category string
        """
        category_mapping = {
            'informational': 'educational',
            'how_to': 'technical',
            'comparison': 'business',
            'problem_solving': 'technical',
            'recommendation': 'business',
            'review': 'business',
        }
        return category_mapping.get(intent_type, 'educational')

    def generate_variations(self, base_keyword: str, count: int = 3) -> List[str]:
        """
        Generate multiple variations of a base keyword/topic.

        Args:
            base_keyword: The base keyword
            count: Number of variations to generate

        Returns:
            List of keyword variations
        """
        # Simple variation strategies
        variations = [base_keyword]

        # Add question words
        question_words = ["how to", "what is", "why", "when to", "where to find"]
        for qword in question_words[:count-1]:
            variations.append(f"{qword} {base_keyword}")

        return variations[:count]
