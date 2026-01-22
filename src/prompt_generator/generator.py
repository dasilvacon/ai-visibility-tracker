"""
Main prompt generation engine using AI APIs.
"""

import csv
import os
import random
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .persona_manager import PersonaManager
from .keyword_processor import KeywordProcessor
from .prompt_builder import PromptBuilder


class PromptGenerator:
    """Main engine for generating natural prompt variations."""

    def __init__(self, personas_file: str, keywords_file: str,
                 api_client: Optional[Any] = None,
                 use_ai_generation: bool = True):
        """
        Initialize the prompt generator.

        Args:
            personas_file: Path to personas JSON file
            keywords_file: Path to keywords CSV file
            api_client: Optional AI API client for advanced generation
            use_ai_generation: Whether to use AI API for generation
        """
        self.persona_manager = PersonaManager(personas_file)
        self.keyword_processor = KeywordProcessor(keywords_file)
        self.prompt_builder = PromptBuilder(use_natural_language=True)
        self.api_client = api_client
        self.use_ai_generation = use_ai_generation and api_client is not None

        self.generated_prompts = []
        self.generation_stats = {
            'total_generated': 0,
            'by_persona': {},
            'by_category': {},
            'by_intent': {},
            'with_competitors': 0,
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

        for i in range(count):
            # Decide if this prompt should include a competitor
            include_competitor = i < competitor_count and competitor_keywords

            # Select a keyword
            if priority_topics and random.random() < 0.6:
                # 60% of time use priority topics
                topic = random.choice(priority_topics)
                keywords = self.keyword_processor.select_keywords_for_topic(topic, 5)
            else:
                # 40% of time use random keywords
                keywords = self.keyword_processor.get_random_keywords(5)

            if not keywords:
                continue

            keyword_data = random.choice(keywords)

            # Generate the prompt
            prompt_data = self._generate_single_prompt(
                persona,
                keyword_data,
                include_competitor
            )

            if prompt_data:
                prompts.append(prompt_data)

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
        intent_type = keyword_data['intent_type']

        # Use AI generation if available and enabled
        if self.use_ai_generation and random.random() < 0.7:  # Use AI 70% of the time
            prompt_text = self._generate_with_ai(persona, keyword, intent_type, include_competitor)
        else:
            # Fall back to template-based generation
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

        return {
            'prompt_id': prompt_id,
            'persona': persona['name'],
            'category': category,
            'intent_type': intent_type,
            'prompt_text': prompt_text,
            'expected_visibility_score': round(visibility_score, 1),
            'notes': f"Generated from keyword: {keyword}{competitor_note}"
        }

    def _generate_with_templates(self, persona: Dict[str, Any], keyword: str,
                                 intent_type: str, include_competitor: bool) -> str:
        """
        Generate prompt using templates (fallback method).

        Args:
            persona: Persona dictionary
            keyword: Keyword string
            intent_type: Intent type
            include_competitor: Whether to include competitor

        Returns:
            Generated prompt text
        """
        if include_competitor:
            competitors = self.keyword_processor.get_all_competitors()
            if competitors:
                competitor = random.choice(competitors)
                prompt = self.prompt_builder.build_comparison_prompt(keyword, competitor)
            else:
                prompt = self.prompt_builder.build_basic_prompt(keyword, intent_type)
        else:
            prompt = self.prompt_builder.build_basic_prompt(keyword, intent_type)

        # Naturalize the prompt
        prompt = self.prompt_builder.naturalize_prompt(prompt)

        # Occasionally add context from priority topics
        priority_topics = persona.get('priority_topics', [])
        if priority_topics:
            prompt = self.prompt_builder.add_context_details(prompt, priority_topics)

        return prompt

    def _generate_with_ai(self, persona: Dict[str, Any], keyword: str,
                         intent_type: str, include_competitor: bool) -> Optional[str]:
        """
        Generate prompt using AI API for more natural variations.

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

        # Build context for the AI
        competitor_context = ""
        if include_competitor:
            competitors = self.keyword_processor.get_all_competitors()
            if competitors:
                competitor = random.choice(competitors)
                competitor_context = f" Include a natural comparison or mention of '{competitor}'."

        system_prompt = f"""Generate a clean, direct search query that someone would type into a search engine or AI assistant.

Persona: {persona['name']}
Description: {persona['description']}
Keyword/Topic: {keyword}
Intent: {intent_type}
{competitor_context}

Requirements:
- Make it direct and to-the-point, like actual search queries
- NO greetings (no "Hi", "Hey", "Hello")
- NO pleasantries (no "Thanks!", "Appreciate any help!", "Any advice?")
- NO conversational filler (no "Can anyone help?", "Quick question:", "I was wondering")
- Vary the structure - not all queries should be questions
- Keep it concise (1-2 sentences max)
- Make it specific to the persona's needs

Good examples:
- "Compare best luxury eyeshadow palette to Charlotte Tilbury"
- "How to apply eyeshadow for beginners"
- "Long lasting eyeshadow for oily lids vs Urban Decay"

Bad examples:
- "Hi, Compare best luxury eyeshadow palette to Charlotte Tilbury Thanks!"
- "Can anyone help? What's better: eyeshadow or MAC? Any advice?"
- "Quick question: How to apply eyeshadow for beginners Appreciate any help!"

Return ONLY the clean query text, nothing else."""

        try:
            # Use the API client to generate
            result = self.api_client.send_prompt(system_prompt, temperature=0.9, max_tokens=100)

            if result['success']:
                generated_text = result['response_text'].strip()
                # Clean up any quotes or extra formatting
                generated_text = generated_text.strip('"\'').strip()
                return generated_text
            else:
                # Fall back to template
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

        fieldnames = ['prompt_id', 'persona', 'category', 'intent_type',
                     'prompt_text', 'expected_visibility_score', 'notes']

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.generated_prompts)

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
