#!/usr/bin/env python3
"""
Example usage of the prompt generation module.

This script demonstrates how to use the prompt generator
programmatically in your own Python code.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from prompt_generator.persona_manager import PersonaManager
from prompt_generator.keyword_processor import KeywordProcessor
from prompt_generator.prompt_builder import PromptBuilder
from prompt_generator.generator import PromptGenerator


def example_persona_management():
    """Example: Working with personas."""
    print("=" * 60)
    print("Example 1: Persona Management")
    print("=" * 60)

    manager = PersonaManager('data/personas_template.json')

    # Get all personas
    personas = manager.get_all_personas()
    print(f"\nTotal personas: {len(personas)}")

    # Get statistics
    stats = manager.get_summary_stats()
    print(f"Persona names: {', '.join(stats['persona_names'])}")

    # Get distribution for 1000 prompts
    distribution = manager.get_persona_distribution(1000)
    print("\nDistribution for 1000 prompts:")
    for persona_id, count in distribution.items():
        persona = manager.get_persona_by_id(persona_id)
        print(f"  {persona['name']}: {count}")

    print()


def example_keyword_processing():
    """Example: Working with keywords."""
    print("=" * 60)
    print("Example 2: Keyword Processing")
    print("=" * 60)

    processor = KeywordProcessor('data/keywords_template.csv')

    # Get statistics
    stats = processor.get_summary_stats()
    print(f"\nTotal keywords: {stats['total_keywords']}")
    print(f"Total search volume: {stats['total_search_volume']:,}")
    print(f"Average search volume: {stats['average_search_volume']:.0f}")
    print(f"Intent types: {', '.join(stats['intent_types'])}")

    # Get high volume keywords
    high_volume = processor.get_high_volume_keywords(10000)
    print(f"\nHigh volume keywords (>10k): {len(high_volume)}")
    for kw in high_volume[:3]:
        print(f"  - {kw['keyword']} ({kw['search_volume']:,})")

    # Get keywords with competitors
    with_competitors = processor.get_keywords_with_competitors()
    print(f"\nKeywords with competitors: {len(with_competitors)}")

    # All competitors
    competitors = processor.get_all_competitors()
    print(f"Unique competitors: {len(competitors)}")
    print(f"Competitors: {', '.join(competitors[:5])}...")

    print()


def example_prompt_building():
    """Example: Building prompts."""
    print("=" * 60)
    print("Example 3: Prompt Building")
    print("=" * 60)

    builder = PromptBuilder(use_natural_language=True)

    # Build basic prompts
    print("\nBasic prompts:")
    keyword = "sleep training for babies"
    for intent in ['informational', 'how_to', 'recommendation']:
        prompt = builder.build_basic_prompt(keyword, intent)
        print(f"  [{intent}] {prompt}")

    # Build comparison prompt
    print("\nComparison prompt:")
    comparison = builder.build_comparison_prompt("baby monitor", "Nanit")
    print(f"  {comparison}")

    # Naturalize prompts
    print("\nNaturalized prompts:")
    base = "What's the best baby monitor?"
    for i in range(3):
        natural = builder.naturalize_prompt(base)
        print(f"  {natural}")

    print()


def example_full_generation():
    """Example: Full generation workflow (no API)."""
    print("=" * 60)
    print("Example 4: Full Generation (Template-Based)")
    print("=" * 60)

    # Initialize generator without API client
    generator = PromptGenerator(
        personas_file='data/personas_template.json',
        keywords_file='data/keywords_template.csv',
        api_client=None,
        use_ai_generation=False
    )

    print("\nGenerating 20 prompts using templates...")
    prompts = generator.generate_prompts(total_count=20, competitor_ratio=0.3)

    print(f"\n✓ Generated {len(prompts)} prompts")

    # Show samples
    print("\nSample prompts:")
    for i, prompt in enumerate(prompts[:5], 1):
        print(f"{i}. [{prompt['persona']} - {prompt['intent_type']}]")
        print(f"   {prompt['prompt_text']}")

    # Save to CSV
    output_file = 'data/example_generated_prompts.csv'
    generator.save_to_csv(output_file)

    # Generate report
    report_file = output_file.replace('.csv', '_summary.txt')
    generator.generate_summary_report(report_file)

    print()


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 8 + "Prompt Generation - Usage Examples" + " " * 16 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")

    example_persona_management()
    example_keyword_processing()
    example_prompt_building()
    example_full_generation()

    print("=" * 60)
    print("For more examples, see README.md")
    print("=" * 60)
    print()


if __name__ == '__main__':
    main()
