"""
Main prompt generation engine using AI APIs.
"""

import csv
import os
import random
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

import re as _re

from .persona_manager import PersonaManager
from .keyword_processor import KeywordProcessor
from .prompt_builder import PromptBuilder
from .deduplicator import PromptDeduplicator


class PromptGenerator:
    """Main engine for generating natural prompt variations."""

    def __init__(self, personas_file: str, keywords_file: str,
                 api_client: Optional[Any] = None,
                 use_ai_generation: bool = True,
                 deduplicator: Optional[PromptDeduplicator] = None,
                 enable_deduplication: bool = True,
                 brand_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the prompt generator.

        Args:
            personas_file: Path to personas JSON file
            keywords_file: Path to keywords CSV file
            api_client: Optional AI API client for advanced generation
            use_ai_generation: Whether to use AI API for generation
            deduplicator: Optional custom deduplicator instance
            enable_deduplication: Whether to enable deduplication during generation
            brand_config: Brand configuration dict (loaded from brand_config.json)
        """
        self.persona_manager = PersonaManager(personas_file)
        self.keyword_processor = KeywordProcessor(keywords_file)
        self.brand_config = brand_config or {}
        self.prompt_builder = PromptBuilder(
            use_natural_language=True,
            brand_config=self.brand_config
        )
        self.api_client = api_client
        self.use_ai_generation = use_ai_generation and api_client is not None

        # Initialize deduplicator
        self.enable_deduplication = enable_deduplication
        if enable_deduplication:
            self.deduplicator = deduplicator or PromptDeduplicator(
                exact_match=True,
                similarity_threshold=0.90
            )
        else:
            self.deduplicator = None

        # Quality scoring disabled — quality_scorer.py no longer used
        self.enable_quality_scoring = False
        self.quality_scorer = None

        self.generated_prompts = []
        self.generation_stats = {
            'total_generated': 0,
            'by_persona': {},
            'by_category': {},
            'by_intent': {},
            'with_competitors': 0,
            'duplicates_removed': 0,
            'start_time': None,
            'end_time': None
        }

    def generate_prompts(self, total_count: int = 1000,
                        competitor_ratio: float = 0.3) -> List[Dict[str, Any]]:
        """
        Generate a full set of prompts distributed across personas.

        Args:
            total_count: Total number of prompts to generate
            competitor_ratio: Ratio of prompts that should include competitor mentions

        Returns:
            List of generated prompt dictionaries
        """
        print(f"\n{'='*60}")
        print(f"Starting Prompt Generation")
        print(f"{'='*60}")
        print(f"Target: {total_count} prompts")
        print(f"Competitor mention ratio: {competitor_ratio*100}%")
        print(f"AI Generation: {'Enabled' if self.use_ai_generation else 'Disabled'}")
        print()

        self.generation_stats['start_time'] = datetime.now()
        self.generated_prompts = []

        # Get persona distribution
        distribution = self.persona_manager.get_persona_distribution(total_count)

        print("Persona Distribution:")
        for persona_id, count in distribution.items():
            persona = self.persona_manager.get_persona_by_id(persona_id)
            print(f"  {persona['name']}: {count} prompts ({count/total_count*100:.1f}%)")
        print()

        # Generate prompts for each persona
        for persona_id, count in distribution.items():
            print(f"Generating {count} prompts for {persona_id}...")
            persona_prompts = self._generate_for_persona(
                persona_id,
                count,
                competitor_ratio
            )
            self.generated_prompts.extend(persona_prompts)
            print(f"  ✓ Generated {len(persona_prompts)} prompts")

        self.generation_stats['end_time'] = datetime.now()
        self.generation_stats['total_generated'] = len(self.generated_prompts)

        print(f"\n✓ Total prompts generated: {len(self.generated_prompts)}")

        if self.enable_deduplication:
            duplicates = self.generation_stats['duplicates_removed']
            print(f"✓ Duplicates removed: {duplicates}")
            if duplicates > 0:
                dup_rate = (duplicates / (len(self.generated_prompts) + duplicates)) * 100
                print(f"  Deduplication rate: {dup_rate:.1f}%")

        return self.generated_prompts

    def _generate_for_persona(self, persona_id: str, count: int,
                             competitor_ratio: float) -> List[Dict[str, Any]]:
        """
        Generate prompts for a specific persona.

        Args:
            persona_id: The persona ID
            count: Number of prompts to generate
            competitor_ratio: Ratio with competitor mentions

        Returns:
            List of prompt dictionaries
        """
        persona = self.persona_manager.get_persona_by_id(persona_id)
        priority_topics = self.persona_manager.get_priority_topics(persona_id)
        prompts = []

        # Determine how many should have competitor mentions
        competitor_count = int(count * competitor_ratio)
        competitor_keywords = self.keyword_processor.get_keywords_with_competitors()

        # Allow retries for duplicate detection
        max_attempts = count * 2
        attempts = 0
        accepted = 0

        while accepted < count and attempts < max_attempts:
            # Decide if this prompt should include a competitor
            include_competitor = accepted < competitor_count and competitor_keywords

            # Select a keyword — 75% from priority topics (up from 60%)
            if priority_topics and random.random() < 0.75:
                topic = random.choice(priority_topics)
                keywords = self.keyword_processor.select_keywords_for_topic(topic, 5)
            else:
                keywords = self.keyword_processor.get_random_keywords(5)

            if not keywords:
                attempts += 1
                continue

            keyword_data = random.choice(keywords)
            attempts += 1

            # Skip junk keywords (currency conversions, bare numbers, etc.)
            if self._is_junk_keyword(keyword_data['keyword']):
                continue

            # Generate the prompt
            prompt_data = self._generate_single_prompt(
                persona,
                keyword_data,
                include_competitor
            )

            if not prompt_data:
                continue

            # Validate prompt text — reject cut-offs, broken grammar, etc.
            if not self._validate_prompt(prompt_data['prompt_text']):
                continue

            # Check for duplicates
            is_duplicate = False
            if self.enable_deduplication and self.deduplicator:
                dup_result = self.deduplicator.check_duplicate(prompt_data['prompt_text'])
                is_duplicate = dup_result['is_duplicate']
                if is_duplicate:
                    self.generation_stats['duplicates_removed'] += 1
                    continue

            # Accepted — add to results
            prompts.append(prompt_data)
            accepted += 1

            # Update stats
            category = prompt_data['category']
            intent = prompt_data['intent_type']

            self.generation_stats['by_persona'][persona_id] = \
                self.generation_stats['by_persona'].get(persona_id, 0) + 1
            self.generation_stats['by_category'][category] = \
                self.generation_stats['by_category'].get(category, 0) + 1
            self.generation_stats['by_intent'][intent] = \
                self.generation_stats['by_intent'].get(intent, 0) + 1

            if include_competitor:
                self.generation_stats['with_competitors'] += 1

        return prompts

    def _generate_single_prompt(self, persona: Dict[str, Any],
                                keyword_data: Dict[str, Any],
                                include_competitor: bool) -> Optional[Dict[str, Any]]:
        """
        Generate a single prompt.

        Args:
            persona: Persona dictionary
            keyword_data: Keyword data dictionary
            include_competitor: Whether to include competitor mention

        Returns:
            Prompt dictionary or None
        """
        keyword = keyword_data['keyword']

        # Pick from ALL intents for this keyword (not just primary)
        # This ensures a keyword flagged informational+commercial+transactional
        # gets prompts across all three intent types
        all_intents = keyword_data.get('all_intents', [keyword_data['intent_type']])
        if not all_intents:
            all_intents = [keyword_data['intent_type']]
        intent_type = random.choice(all_intents)

        # Use AI generation 80% of the time (up from 70%) — templates as fallback
        if self.use_ai_generation and random.random() < 0.8:
            prompt_text = self._generate_with_ai(persona, keyword, intent_type, include_competitor)
        else:
            # Fall back to template-based generation (persona-driven)
            prompt_text = self._generate_with_templates(persona, keyword, intent_type, include_competitor)

        if not prompt_text:
            return None

        # Build the complete prompt data
        category = self.prompt_builder.categorize_prompt(intent_type)
        visibility_score = self.prompt_builder.estimate_visibility_score(
            keyword_data,
            include_competitor
        )

        prompt_id = f"gen_{int(time.time()*1000)}_{random.randint(1000, 9999)}"

        competitor_note = ""
        if include_competitor and keyword_data['competitor_brands']:
            competitor_note = f" (vs {keyword_data['competitor_brands'][0]})"

        prompt_dict = {
            'prompt_id': prompt_id,
            'persona': persona['name'],
            'category': category,
            'intent_type': intent_type,
            'prompt_text': prompt_text,
            'expected_visibility_score': round(visibility_score, 1),
            'notes': f"Generated from keyword: {keyword}{competitor_note}"
        }

        return prompt_dict

    # ── Junk-keyword & bad-prompt filters ──────────────────────────────

    # Keywords that should never be used for prompts (currency, gibberish, etc.)
    _JUNK_KEYWORD_PATTERNS = [
        _re.compile(r'\d+\s*(cad|usd|eur|gbp|aud)\s*(to|in)\s*(cad|usd|eur|gbp|aud)', _re.I),
        _re.compile(r'^\d+(\.\d+)?$'),               # bare numbers
        _re.compile(r'^.{1,2}$'),                     # 1–2 char keywords
    ]

    @classmethod
    def _is_junk_keyword(cls, keyword: str) -> bool:
        """Return True if this keyword should be skipped entirely."""
        for pat in cls._JUNK_KEYWORD_PATTERNS:
            if pat.search(keyword):
                return True
        return False

    @staticmethod
    def _validate_prompt(text: str) -> bool:
        """
        Return True if the prompt text is acceptable quality.
        Rejects cut-offs, broken grammar, empty, or too-short text.
        """
        if not text or len(text.strip()) < 10:
            return False

        # Cut-off detection: ends with a single letter + optional whitespace
        stripped = text.rstrip()
        if _re.search(r'\s[a-zA-Z]$', stripped):
            return False

        # Broken "What is" + multi-word phrase (grammar mismatch)
        # e.g. "What is ukrainian shirts", "What is buy ukrainian products"
        # "What is X" only works with singular nouns, not phrases
        what_is_match = _re.match(r'^What is (.+)$', text, _re.I)
        if what_is_match:
            rest = what_is_match.group(1).strip()
            # If what follows "What is" has 2+ words, it's almost always broken
            if len(rest.split()) >= 2:
                return False

        # Duplicate word stutter: "the the", "for for"
        if _re.search(r'\b(\w+)\s+\1\b', text, _re.I):
            return False

        return True

    def _generate_with_templates(self, persona: Dict[str, Any], keyword: str,
                                 intent_type: str, include_competitor: bool) -> str:
        """
        Generate prompt using persona-driven templates (fallback method).

        Args:
            persona: Persona dictionary
            keyword: Keyword string
            intent_type: Intent type
            include_competitor: Whether to include competitor

        Returns:
            Generated prompt text
        """
        competitor = ''
        if include_competitor:
            competitors = self.keyword_processor.get_all_competitors()
            if competitors:
                competitor = random.choice(competitors)

        # Use the persona-driven builder (80% persona, 20% direct internally)
        prompt = self.prompt_builder.build_persona_prompt(
            keyword=keyword,
            persona_data=persona,
            intent_type=intent_type,
            include_competitor=include_competitor,
            competitor=competitor
        )

        # Naturalize
        prompt = self.prompt_builder.naturalize_prompt(prompt)

        return prompt

    def _build_brand_context(self) -> str:
        """Build industry context string from brand_config for AI prompts."""
        brand = self.brand_config.get('brand', {})
        brand_name = brand.get('name', '')
        description = brand.get('description', '')
        goals = brand.get('business_goals', {})
        positioning = goals.get('market_positioning', '')
        freeform = goals.get('freeform_notes', '')

        # Get competitor names
        competitors_section = self.brand_config.get('competitors', {})
        if isinstance(competitors_section, dict):
            competitor_names = [c.get('name', '') for c in competitors_section.get('expected', [])]
        elif isinstance(competitors_section, list):
            competitor_names = competitors_section
        else:
            competitor_names = []

        parts = []
        if brand_name:
            parts.append(f"Brand: {brand_name}")
        if description:
            parts.append(f"Industry: {description}")
        if positioning:
            parts.append(f"Positioning: {positioning}")
        if competitor_names:
            parts.append(f"Competitors: {', '.join(competitor_names[:5])}")
        if freeform:
            parts.append(f"Notes: {freeform[:200]}")

        return '\n'.join(parts)

    def _build_persona_context(self, persona: Dict[str, Any]) -> str:
        """Build rich persona context string using all available fields."""
        parts = [f"Persona: {persona.get('name', 'Unknown')}"]
        parts.append(f"Description: {persona.get('description', '')}")

        # Use rich persona fields when available (OCO-style personas)
        if persona.get('caregiving_role'):
            parts.append(f"Role: {persona['caregiving_role']}")
        if persona.get('key_trigger'):
            parts.append(f"Trigger: {persona['key_trigger']}")
        if persona.get('priority_program'):
            parts.append(f"Key program: {persona['priority_program']}")
        if persona.get('top_barrier'):
            parts.append(f"Barrier: {persona['top_barrier']}")
        if persona.get('priority_topics'):
            parts.append(f"Topics: {', '.join(persona['priority_topics'][:5])}")

        return '\n'.join(parts)

    def _generate_with_ai(self, persona: Dict[str, Any], keyword: str,
                         intent_type: str, include_competitor: bool) -> Optional[str]:
        """
        Generate prompt using AI API with full brand and persona context.

        Uses brand_config for industry-aware examples and persona fields
        for deeply personalized queries. No hardcoded industry examples.

        Args:
            persona: Persona dictionary
            keyword: Keyword string
            intent_type: Intent type
            include_competitor: Whether to include competitor

        Returns:
            Generated prompt text or None
        """
        if not self.api_client:
            return None

        # Build competitor context
        competitor_context = ""
        if include_competitor:
            competitors = self.keyword_processor.get_all_competitors()
            if competitors:
                competitor = random.choice(competitors)
                competitor_context = f"\nInclude a natural comparison or mention of '{competitor}'."

        # Build rich context from brand config and persona
        brand_context = self._build_brand_context()
        persona_context = self._build_persona_context(persona)

        # Vary the prompt structure to avoid repetitive output
        style = random.choice(['search_query', 'ai_assistant_question', 'voice_search'])
        style_instructions = {
            'search_query': "Generate a clean search query someone would type into Google.",
            'ai_assistant_question': "Generate a question someone would ask ChatGPT, Claude, or Perplexity.",
            'voice_search': "Generate a natural spoken question someone would ask a voice assistant."
        }

        system_prompt = f"""{style_instructions[style]}

--- BRAND CONTEXT ---
{brand_context}

--- PERSONA ---
{persona_context}

--- QUERY DETAILS ---
Keyword/Topic: {keyword}
Intent: {intent_type}
{competitor_context}

--- CRITICAL REQUIREMENTS ---
- Sound like a REAL PERSON searching, NOT a marketer describing a persona
- NEVER include persona labels like "as an adult child caregiver" or "for HR leaders"
- Real people say "my mom just got out of hospital what do I do" not "hospital discharge planning resources for adult child caregiver"
- NO greetings (no "Hi", "Hey", "Hello")
- NO pleasantries (no "Thanks!", "Appreciate any help!")
- NO conversational filler (no "Can anyone help?", "Quick question:")
- Vary structure — mix questions, statements, and comparison formats
- Keep it concise (1-2 sentences max, 5-20 words ideal)
- The persona's situation should shape the LANGUAGE and ANGLE of the query
- Use the keyword naturally — don't just repeat it verbatim
- Think: what would this person ACTUALLY type into Google or ask ChatGPT?

Return ONLY the clean query text, nothing else."""

        try:
            result = self.api_client.send_prompt(system_prompt, temperature=0.9, max_tokens=100)

            if result['success']:
                generated_text = result['response_text'].strip()
                # Clean up any quotes or extra formatting
                generated_text = generated_text.strip('"\'').strip()
                # Remove any leading/trailing quotation marks the AI might add
                if generated_text.startswith('"') and generated_text.endswith('"'):
                    generated_text = generated_text[1:-1].strip()
                return generated_text
            else:
                return self._generate_with_templates(persona, keyword, intent_type, include_competitor)

        except Exception as e:
            print(f"  Warning: AI generation failed: {e}")
            return self._generate_with_templates(persona, keyword, intent_type, include_competitor)

    def save_to_csv(self, output_file: str) -> str:
        """
        Save generated prompts to CSV file.

        Args:
            output_file: Path to output CSV file

        Returns:
            Path to saved file
        """
        if not self.generated_prompts:
            raise ValueError("No prompts to save. Run generate_prompts() first.")

        # Base fieldnames
        fieldnames = ['prompt_id', 'persona', 'category', 'intent_type',
                     'prompt_text', 'expected_visibility_score', 'notes']

        # Flatten prompts for CSV export
        export_prompts = []
        for prompt in self.generated_prompts:
            export_prompt = {
                'prompt_id': prompt['prompt_id'],
                'persona': prompt['persona'],
                'category': prompt['category'],
                'intent_type': prompt['intent_type'],
                'prompt_text': prompt['prompt_text'],
                'expected_visibility_score': prompt['expected_visibility_score'],
                'notes': prompt.get('notes', '')
            }

            export_prompts.append(export_prompt)

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(export_prompts)

        print(f"\n✓ Prompts saved to: {output_file}")
        return output_file

    def generate_summary_report(self, report_file: str) -> str:
        """
        Generate a summary report of the generation process.

        Args:
            report_file: Path to output report file

        Returns:
            Path to saved report
        """
        if not self.generated_prompts:
            raise ValueError("No prompts to report on. Run generate_prompts() first.")

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("PROMPT GENERATION SUMMARY REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Total Prompts: {self.generation_stats['total_generated']}")
        report_lines.append("")

        # Time taken
        if self.generation_stats['start_time'] and self.generation_stats['end_time']:
            duration = self.generation_stats['end_time'] - self.generation_stats['start_time']
            report_lines.append(f"Generation Time: {duration.total_seconds():.1f} seconds")
            report_lines.append("")

        # By Persona
        report_lines.append("BREAKDOWN BY PERSONA")
        report_lines.append("-" * 80)
        for persona_id, count in sorted(self.generation_stats['by_persona'].items()):
            persona = self.persona_manager.get_persona_by_id(persona_id)
            name = persona['name'] if persona else persona_id
            pct = count / self.generation_stats['total_generated'] * 100
            report_lines.append(f"{name}: {count} ({pct:.1f}%)")
        report_lines.append("")

        # By Category
        report_lines.append("BREAKDOWN BY CATEGORY")
        report_lines.append("-" * 80)
        for category, count in sorted(self.generation_stats['by_category'].items()):
            pct = count / self.generation_stats['total_generated'] * 100
            report_lines.append(f"{category}: {count} ({pct:.1f}%)")
        report_lines.append("")

        # By Intent
        report_lines.append("BREAKDOWN BY INTENT TYPE")
        report_lines.append("-" * 80)
        for intent, count in sorted(self.generation_stats['by_intent'].items()):
            pct = count / self.generation_stats['total_generated'] * 100
            report_lines.append(f"{intent}: {count} ({pct:.1f}%)")
        report_lines.append("")

        # Competitor mentions
        competitor_count = self.generation_stats['with_competitors']
        competitor_pct = competitor_count / self.generation_stats['total_generated'] * 100
        report_lines.append(f"Prompts with Competitor Mentions: {competitor_count} ({competitor_pct:.1f}%)")
        report_lines.append("")

        # Sample prompts
        report_lines.append("SAMPLE PROMPTS")
        report_lines.append("-" * 80)
        samples = random.sample(self.generated_prompts, min(10, len(self.generated_prompts)))
        for i, prompt in enumerate(samples, 1):
            report_lines.append(f"{i}. [{prompt['persona']} - {prompt['intent_type']}]")
            report_lines.append(f"   {prompt['prompt_text']}")
            report_lines.append("")

        report_lines.append("=" * 80)

        report_text = "\n".join(report_lines)

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)

        print(f"✓ Summary report saved to: {report_file}")
        return report_file
