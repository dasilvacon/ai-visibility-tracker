"""
Prompt builder for creating natural query variations.

KEY DESIGN PRINCIPLE: Prompts must sound like REAL PEOPLE searching,
NOT like a marketer describing a persona. A caregiver doesn't type
"Adult child of aging parent looking for respite care" — they type
"my mom just got out of hospital and I don't know what to do."

Persona influence works by shaping the SITUATION and LANGUAGE,
not by inserting persona labels into the query text.
"""

import random
from typing import Dict, List, Any, Optional


class PromptBuilder:
    """Builds natural prompt variations that sound like real humans searching."""

    # ── STYLE 1: Direct Search Query (20%) ──────────────────────────
    # Clean keyword-focused queries with no persona context
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
            "Which {keyword} to choose",
        ],
        'review': [
            "{keyword} review",
            "{keyword} worth it",
            "Is {keyword} good",
            "{keyword} quality",
        ]
    }

    # ── STYLE 2: Situational (80%) ──────────────────────────────────
    # These sound like real people in real situations searching.
    # The persona shapes WHICH templates are selected, but the
    # persona label never appears in the output text.
    #
    # Placeholder fields:
    #   {keyword}      = the SEO keyword
    #   {situation}    = natural language description of their situation
    #   {need}         = what they're looking for
    #   {topic}        = a priority topic from the persona

    SITUATIONAL_TEMPLATES = {
        'informational': [
            "{keyword} in Ontario",
            "what is {keyword}",
            "{keyword} near me",
            "free {keyword}",
            "{keyword} programs Ontario",
            "where to find {keyword}",
            "{keyword} options in my area",
            "how does {keyword} work",
            "what {keyword} is available",
            "{keyword} services Ontario",
            "who qualifies for {keyword}",
            "information about {keyword}",
        ],
        'how_to': [
            "how to get {keyword}",
            "how to find {keyword} near me",
            "how to access {keyword} in Ontario",
            "how to apply for {keyword}",
            "how do I get {keyword}",
            "where can I get {keyword}",
            "steps to get {keyword}",
            "how to start {keyword}",
        ],
        'comparison': [
            "{keyword} vs {competitor}",
            "is {keyword} or {competitor} better",
            "{keyword} compared to {competitor}",
            "should I use {keyword} or {competitor}",
            "what's the difference between {keyword} and {competitor}",
        ],
        'problem_solving': [
            "I need help with {keyword}",
            "{keyword} not available what do I do",
            "can't find {keyword} in my area",
            "struggling with {keyword}",
            "{keyword} waitlist alternatives",
            "I don't know where to start with {keyword}",
        ],
        'recommendation': [
            "best {keyword} in Ontario",
            "recommended {keyword} near me",
            "top {keyword} programs",
            "good {keyword} options",
            "what {keyword} should I use",
        ],
        'review': [
            "is {keyword} worth it",
            "does {keyword} actually help",
            "{keyword} reviews",
            "has anyone tried {keyword}",
            "what's {keyword} like",
        ]
    }

    # ── STYLE 3: First-Person Situation (for when we have rich persona data) ──
    # These incorporate the persona's SITUATION naturally, without labels.
    # Used when the persona has key_trigger, top_barrier, etc.
    FIRST_PERSON_TEMPLATES = [
        # Trigger-driven (something just happened)
        "{situation} and I need {keyword}",
        "{situation} where can I find {keyword}",
        "{situation} what are my options for {keyword}",
        "just found out {situation} need help with {keyword}",
        "{situation} looking for {keyword}",

        # Barrier-driven (they're stuck on something)
        "I don't know {barrier_phrase} for {keyword}",
        "can't figure out {keyword} {barrier_phrase}",
        "where do you even start with {keyword}",
        "is there {keyword} that {removes_barrier}",

        # Need-driven (they need a specific thing)
        "I need {keyword} but don't know where to start",
        "looking for {keyword} that's actually helpful",
        "does anyone know about {keyword}",
        "where to find good {keyword}",
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

    def _get_natural_situation(self, persona: Dict[str, Any]) -> Dict[str, str]:
        """
        Convert persona fields into natural language fragments that
        sound like real people, NOT like marketer labels.

        Returns dict with: situation, barrier_phrase, removes_barrier, need
        """
        trigger = persona.get('key_trigger', '')
        barrier = persona.get('top_barrier', '')
        description = persona.get('description', '')
        role = persona.get('caregiving_role', '')

        # Convert clinical trigger labels into natural language
        trigger_map = {
            'Hospital discharge / diagnosis': random.choice([
                'my parent just got out of the hospital',
                'my mom was just diagnosed',
                'dad just got discharged',
                'parent just came home from hospital',
            ]),
            "Parent's progressive decline": random.choice([
                'my parent is getting worse',
                "my mom's condition is getting worse",
                'my parent needs more and more help',
                "dad can't do things on his own anymore",
            ]),
            'Gradual role intensification': random.choice([
                'I feel like I do everything for my spouse now',
                'caring for my husband is taking over my life',
                'my wife needs constant care now',
            ]),
            'Diagnosis or transition milestone': random.choice([
                'my child was just diagnosed',
                'my kid is transitioning to adult services',
                'we just got a diagnosis for my child',
            ]),
            "Loved one's crisis episode": random.choice([
                'my family member just had a mental health crisis',
                'someone I love had a breakdown',
                'my sibling was just hospitalized for mental health',
            ]),
            'Family crisis / growing responsibility': random.choice([
                'I have to take care of my parent and I am still in school',
                'I am young and caring for a family member',
                'I am a teenager looking after my mom',
            ]),
            'Staff burnout / poor caregiver comms': random.choice([
                'our staff is burning out dealing with patient families',
                'we need better communication with caregivers',
                'our hospital needs caregiver inclusion training',
            ]),
            'Staff caregiving impact on work': random.choice([
                'employees are missing work to care for family',
                'staff are struggling with caregiving responsibilities',
                'we need a caregiver-friendly workplace policy',
            ]),
        }

        # Convert barrier labels into natural language
        barrier_map = {
            "Doesn't know OCO exists": random.choice([
                'where to even look',
                'what organizations can help',
                'who to call',
            ]),
            'Time / skepticism of soft support': random.choice([
                'if support groups actually help',
                'where to find time for this',
                'if peer support is worth it',
            ]),
            "Doesn't identify as caregiver": random.choice([
                'if what I am doing counts as caregiving',
                'whether I am actually a caregiver',
                'if there is help for people like me',
            ]),
            'Sees OCO as elder-care focused': random.choice([
                'where to find help for my child',
                'if there is support for parents of special needs kids',
                'programs that are not just for seniors',
            ]),
            'Stigma / privacy concerns': random.choice([
                'how to get help without anyone knowing',
                'if there is confidential support',
                'where to get private help',
            ]),
            'Self-identification / visibility': random.choice([
                'if there is help for young people like me',
                'where young people caring for family can get support',
                'if anyone else my age is dealing with this',
            ]),
            'Organizational buy-in': random.choice([
                'how to convince leadership',
                'how to get management on board',
                'how to build the case for this',
            ]),
            "Doesn't know where to start": random.choice([
                'where to even begin',
                'how to start supporting caregivers at work',
                'what the first step is',
            ]),
        }

        # Get natural situation text
        situation = trigger_map.get(trigger, '')
        if not situation and description:
            # Fallback: use a generic situational phrase
            situation = random.choice([
                'I am dealing with a lot right now',
                'our family is going through something difficult',
                'I need help but I am not sure what kind',
            ])

        barrier_phrase = barrier_map.get(barrier, 'where to start')

        # "removes_barrier" is the positive flip
        removes_barrier = random.choice([
            'is easy to access',
            'is actually free',
            'is confidential',
            'does not have a long waitlist',
            'works for my schedule',
        ])

        return {
            'situation': situation,
            'barrier_phrase': barrier_phrase,
            'removes_barrier': removes_barrier,
        }

    def build_basic_prompt(self, keyword: str, intent_type: str) -> str:
        """Build a basic prompt (no persona context). Used as fallback."""
        if intent_type == 'comparison':
            intent_type = 'informational'

        templates = self.DIRECT_TEMPLATES.get(intent_type, self.DIRECT_TEMPLATES['informational'])
        template = random.choice(templates)
        return template.format(keyword=keyword)

    def build_comparison_prompt(self, keyword: str, competitor: str) -> str:
        """Build a comparison prompt with a competitor."""
        templates = self.DIRECT_TEMPLATES['comparison'] + self.SITUATIONAL_TEMPLATES['comparison']
        template = random.choice(templates)
        return template.format(keyword=keyword, competitor=competitor)

    def build_persona_prompt(self, keyword: str, persona_data: Optional[Dict[str, Any]],
                            intent_type: str, include_competitor: bool = False,
                            competitor: str = '') -> str:
        """
        Build a prompt that sounds like a REAL PERSON searching.

        The persona shapes which templates are used and provides
        situational context, but the persona LABEL never appears
        in the output text.

        80% situational/first-person, 20% direct keyword queries.
        """
        if not persona_data:
            return self.build_basic_prompt(keyword, intent_type)

        # Comparison prompts
        if include_competitor and competitor:
            templates = self.SITUATIONAL_TEMPLATES.get('comparison', self.DIRECT_TEMPLATES['comparison'])
            template = random.choice(templates)
            return template.format(keyword=keyword, competitor=competitor)

        # ── 80% human-sounding, 20% direct ──
        use_human = random.random() < 0.80

        if not use_human:
            return self.build_basic_prompt(keyword, intent_type)

        # Decide between situational templates and first-person templates
        has_rich_data = persona_data.get('key_trigger') or persona_data.get('top_barrier')

        if has_rich_data and random.random() < 0.40:
            # 40% of human prompts use first-person situation templates
            natural = self._get_natural_situation(persona_data)
            template = random.choice(self.FIRST_PERSON_TEMPLATES)
            try:
                prompt = template.format(keyword=keyword, **natural)
            except KeyError:
                prompt = f"I need help with {keyword}"
        else:
            # 60% of human prompts use situational templates
            templates = self.SITUATIONAL_TEMPLATES.get(
                intent_type, self.SITUATIONAL_TEMPLATES['informational']
            )
            template = random.choice(templates)
            prompt = template.format(keyword=keyword)

        # Inject a priority topic naturally (20% of time)
        topics = persona_data.get('priority_topics', [])
        if topics and random.random() < 0.20:
            topic = random.choice(topics)
            suffixes = [
                f" for {topic}",
                f" especially {topic}",
                f" related to {topic}",
            ]
            prompt += random.choice(suffixes)

        return prompt

    def naturalize_prompt(self, prompt: str) -> str:
        """Clean up a prompt. No filler, no greetings."""
        if not self.use_natural_language:
            return prompt
        return prompt.strip()

    def add_context_details(self, prompt: str, topics: List[str]) -> str:
        """Occasionally add context details from priority topics."""
        if random.random() > 0.20 or not topics:
            return prompt

        topic = random.choice(topics)
        context_formats = [
            f"{prompt} for {topic}",
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
        question_words = ["how to", "what is", "why", "when to", "where to find"]
        for qword in question_words[:count-1]:
            variations.append(f"{qword} {base_keyword}")
        return variations[:count]
