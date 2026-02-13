"""
Test script to verify prompt generator produces clean, natural prompts.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from prompt_generator.prompt_builder import PromptBuilder

def test_prompt_generation():
    """Generate 10 sample prompts and verify they're clean."""
    builder = PromptBuilder(use_natural_language=True)

    # Test data
    keywords = [
        "luxury eyeshadow palette",
        "long lasting eyeshadow",
        "eyeshadow for oily lids",
        "neutral eyeshadow palette",
        "professional eyeshadow",
    ]

    intents = ['informational', 'recommendation', 'comparison', 'review']
    personas = [
        'Luxury Beauty Enthusiast',
        'Professional Makeup Artist',
        'Specific Need Shopper',
        'Beauty Beginner'
    ]
    competitors = ['Charlotte Tilbury', 'Pat McGrath Labs']

    print("\n" + "="*80)
    print("PROMPT GENERATION TEST - 10 SAMPLES")
    print("="*80)
    print("\nVerifying prompts are:")
    print("✓ Clean (no 'Hi,', 'Quick question:', 'Thanks!')")
    print("✓ Natural (conversational or direct)")
    print("✓ Token-efficient (10-25 words)")
    print("\n" + "="*80 + "\n")

    # Generate 10 prompts
    for i in range(10):
        if i < 3:
            # Test basic prompts
            keyword = keywords[i % len(keywords)]
            intent = intents[i % len(intents)]
            prompt = builder.build_basic_prompt(keyword, intent)
        elif i < 6:
            # Test comparison prompts
            keyword = keywords[i % len(keywords)]
            competitor = competitors[i % len(competitors)]
            prompt = builder.build_comparison_prompt(keyword, competitor)
        else:
            # Test persona prompts
            keyword = keywords[i % len(keywords)]
            persona = personas[i % len(personas)]
            intent = intents[i % len(intents)]
            prompt = builder.build_persona_prompt(keyword, persona, intent)

        # Apply naturalization (should do nothing now)
        prompt = builder.naturalize_prompt(prompt)

        # Count words
        word_count = len(prompt.split())

        # Check for filler words
        filler_check = "✓ CLEAN"
        filler_words = ['Hi,', 'Hey,', 'Hello,', 'Quick question:', 'Can anyone help?', 'Thanks!', 'Thank you!']
        for filler in filler_words:
            if filler in prompt:
                filler_check = f"❌ CONTAINS FILLER: {filler}"
                break

        # Check word count
        token_check = "✓ EFFICIENT" if 5 <= word_count <= 25 else f"⚠️  {word_count} words"

        # Determine style
        if prompt[0].isupper() and any(word in prompt.lower() for word in ['looking', 'need', 'want', 'trying', 'should', 'how does']):
            style = "Conversational"
        else:
            style = "Direct"

        print(f"{i+1}. {prompt}")
        print(f"   [{style} | {word_count} words | {filler_check} | {token_check}]")
        print()

if __name__ == '__main__':
    test_prompt_generation()
