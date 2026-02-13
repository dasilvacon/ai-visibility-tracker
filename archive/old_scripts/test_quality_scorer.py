#!/usr/bin/env python3
"""
Test script for the PromptQualityScorer.

This script tests the quality scorer with sample prompts
to verify it's working correctly.
"""

import sys
from pathlib import Path

sys.path.insert(0, 'src')

from src.prompt_generator.quality_scorer import PromptQualityScorer


def test_quality_scorer():
    """Test the quality scorer with various prompt examples."""

    scorer = PromptQualityScorer()

    # Test cases: (prompt, expected_quality_level, description)
    test_cases = [
        # Excellent prompts
        (
            "Best long-lasting eyeshadow palette for oily lids",
            "Excellent",
            "Natural, clear, specific"
        ),
        (
            "Compare luxury eyeshadow palettes to Urban Decay Naked",
            "Excellent",
            "Natural comparison query"
        ),
        (
            "How to apply eyeshadow for hooded eyes step by step",
            "Excellent",
            "Clear how-to query"
        ),

        # Good prompts
        (
            "Looking for high-end eyeshadow that lasts all day",
            "Good",
            "Conversational but clear"
        ),
        (
            "Is luxury eyeshadow worth the price",
            "Good",
            "Simple, direct question"
        ),

        # Fair prompts
        (
            "eyeshadow",
            "Fair",
            "Too short, vague"
        ),
        (
            "I'm looking for some really amazing eyeshadow that works great and has wonderful colors and is affordable but also high quality and long lasting and perfect for sensitive eyes",
            "Fair",
            "Too long, rambling"
        ),

        # Poor prompts
        (
            "Hi! Can anyone help me? I'm looking for eyeshadow. Thanks!",
            "Poor",
            "Has greetings and pleasantries"
        ),
        (
            "Quick question: What's the best eyeshadow? Any advice would be appreciated!",
            "Poor",
            "Has filler phrases and pleasantries"
        ),
    ]

    print("=" * 80)
    print("PROMPT QUALITY SCORER TEST")
    print("=" * 80)
    print()

    results = []
    for prompt, expected_level, description in test_cases:
        # Score the prompt
        score_data = scorer.score_prompt(
            prompt,
            context={
                'keyword': 'eyeshadow',
                'intent_type': 'informational',
                'persona': 'Beauty Enthusiast'
            },
            existing_prompts=[]
        )

        results.append((prompt, score_data, expected_level, description))

        # Display results
        print(f"Prompt: \"{prompt}\"")
        print(f"Description: {description}")
        print(f"Overall Score: {score_data['overall_score']}/100")
        print(f"Quality Level: {score_data['quality_level']} (Expected: {expected_level})")
        print()
        print("Dimension Scores:")
        for dim, score in score_data['dimension_scores'].items():
            print(f"  - {dim.replace('_', ' ').title()}: {score:.1f}/100")
        print()

        if score_data['issues']:
            print("Issues Found:")
            for issue in score_data['issues']:
                print(f"  - {issue}")
            print()

        if score_data['recommendations']:
            print("Recommendations:")
            for rec in score_data['recommendations']:
                print(f"  - {rec}")
            print()

        print("-" * 80)
        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    total = len(results)
    correct = sum(1 for _, score_data, expected, _ in results
                  if score_data['quality_level'] == expected)

    print(f"Total Test Cases: {total}")
    print(f"Correct Classifications: {correct}/{total} ({correct/total*100:.1f}%)")
    print()

    # Show distribution
    levels = [score_data['quality_level'] for _, score_data, _, _ in results]
    for level in ["Excellent", "Good", "Fair", "Poor"]:
        count = levels.count(level)
        print(f"{level}: {count} prompts")

    print()
    print("✅ Quality scorer test complete!")


if __name__ == "__main__":
    test_quality_scorer()
