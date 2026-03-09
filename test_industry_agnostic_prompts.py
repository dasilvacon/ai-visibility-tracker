#!/usr/bin/env python3
"""
Test script to verify industry-agnostic prompt generation works across different client types.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.prompt_generator.generator import PromptGenerator


def test_client_prompt_generation(client_name, personas_file, keywords_file):
    """Test prompt generation for a single client."""
    print(f"\n{'='*80}")
    print(f"Testing: {client_name}")
    print(f"{'='*80}")

    try:
        # Initialize generator (without AI, using templates only)
        generator = PromptGenerator(
            personas_file=personas_file,
            keywords_file=keywords_file,
            api_client=None,
            use_ai_generation=False,
            enable_deduplication=True,
            enable_quality_scoring=True
        )

        # Generate a small batch of prompts
        prompts = generator.generate_prompts(total_count=10, competitor_ratio=0.3)

        # Show samples
        print(f"\n✓ Successfully generated {len(prompts)} prompts")
        print(f"\nSample prompts:")
        for i, prompt in enumerate(prompts[:5], 1):
            print(f"\n{i}. [{prompt['persona']} - {prompt['intent_type']}]")
            print(f"   {prompt['prompt_text']}")
            if 'quality_score' in prompt:
                qs = prompt['quality_score']
                print(f"   Quality: {qs['quality_level']} ({qs['overall_score']}/10)")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Test all client types."""

    print("\n" + "="*80)
    print("INDUSTRY-AGNOSTIC PROMPT GENERATION TEST")
    print("="*80)
    print("\nTesting prompt generation across 4 different industries:")
    print("  1. Beauty (B2C Product)")
    print("  2. Finance (B2B Service)")
    print("  3. Healthcare (Nonprofit Service)")
    print("  4. Weddings (B2C Service)")
    print()

    clients_to_test = [
        {
            'name': 'Natasha Denona (Luxury Beauty)',
            'personas': 'data/natasha_denona_personas.json',
            'keywords': 'data/natasha_denona_keywords.csv'
        },
        {
            'name': 'Espresso Capital (VC/Finance)',
            'personas': 'data/espresso_capital/espresso_capital_personas.json',
            'keywords': 'data/espresso_capital/espresso_capital_keywords.csv'
        },
        {
            'name': 'Ontario Caregiver (Healthcare)',
            'personas': 'data/ontario_caregiver_organization/ontario_caregiver_organization_personas.json',
            'keywords': 'data/ontario_caregiver_organization/ontario_caregiver_organization_keywords.csv'
        },
        {
            'name': 'Say I Do (Weddings)',
            'personas': 'data/say_i_do/say_i_do_personas.json',
            'keywords': 'data/say_i_do/say_i_do_keywords.csv'
        }
    ]

    results = []
    for client in clients_to_test:
        success = test_client_prompt_generation(
            client['name'],
            client['personas'],
            client['keywords']
        )
        results.append((client['name'], success))

    # Summary
    print(f"\n\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(success for _, success in results)

    if all_passed:
        print(f"\n{'='*80}")
        print("✓ ALL TESTS PASSED - System is industry-agnostic!")
        print(f"{'='*80}\n")
        return 0
    else:
        print(f"\n{'='*80}")
        print("✗ SOME TESTS FAILED")
        print(f"{'='*80}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
