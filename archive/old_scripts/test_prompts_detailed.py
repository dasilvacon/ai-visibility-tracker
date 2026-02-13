"""
Test script to show detailed persona-specific prompt variations.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from prompt_generator.prompt_builder import PromptBuilder

def test_persona_prompts():
    """Generate persona-specific prompts to show variety."""
    builder = PromptBuilder(use_natural_language=True)

    print("\n" + "="*80)
    print("PERSONA-SPECIFIC PROMPT EXAMPLES")
    print("="*80)
    print()

    # Test each persona with multiple attempts to get variety
    test_cases = [
        {
            'persona': 'Luxury Beauty Enthusiast',
            'keyword': 'eyeshadow palette',
            'intent': 'review',
            'iterations': 5
        },
        {
            'persona': 'Professional Makeup Artist',
            'keyword': 'long-lasting eyeshadow',
            'intent': 'recommendation',
            'iterations': 5
        },
        {
            'persona': 'Specific Need Shopper',
            'keyword': 'eyeshadow',
            'intent': 'problem_solving',
            'iterations': 5
        },
        {
            'persona': 'Beauty Beginner',
            'keyword': 'luxury eyeshadow',
            'intent': 'review',
            'iterations': 5
        },
    ]

    for test in test_cases:
        print(f"\n{test['persona']} ({test['intent']}):")
        print("-" * 80)

        # Generate multiple to show variety
        prompts_seen = set()
        attempts = 0
        shown = 0

        while shown < 3 and attempts < 20:
            prompt = builder.build_persona_prompt(
                test['keyword'],
                test['persona'],
                test['intent']
            )
            prompt = builder.naturalize_prompt(prompt)

            if prompt not in prompts_seen:
                prompts_seen.add(prompt)
                word_count = len(prompt.split())
                print(f"{shown + 1}. {prompt}")
                print(f"   [{word_count} words]")
                shown += 1

            attempts += 1

    print("\n" + "="*80)
    print("\nDirect Search Query Examples:")
    print("-" * 80)

    # Show direct style examples
    for i in range(5):
        # Force some to be shorter/direct by using basic prompts
        keywords = [
            'best luxury eyeshadow',
            'eyeshadow for hooded eyes',
            'long-lasting eyeshadow palette',
            'professional makeup artist eyeshadow',
            'neutral eyeshadow palette'
        ]
        keyword = keywords[i]

        # Generate with basic prompt (will randomly choose style)
        prompt = builder.build_basic_prompt(keyword, 'informational')
        word_count = len(prompt.split())
        print(f"{i + 1}. {prompt}")
        print(f"   [{word_count} words]")

    print("\n" + "="*80)
    print("\nComparison Examples:")
    print("-" * 80)

    comparisons = [
        ('Natasha Denona', 'Charlotte Tilbury'),
        ('luxury eyeshadow palette', 'Pat McGrath Labs'),
        ('professional eyeshadow', 'Tom Ford Beauty'),
    ]

    for i, (keyword, competitor) in enumerate(comparisons):
        prompt = builder.build_comparison_prompt(keyword, competitor)
        word_count = len(prompt.split())
        print(f"{i + 1}. {prompt}")
        print(f"   [{word_count} words]")

    print("\n" + "="*80)

if __name__ == '__main__':
    test_persona_prompts()
