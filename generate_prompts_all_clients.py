#!/usr/bin/env python3
"""
Generate prompts for all clients in the registry.
"""

import json
import sys
import csv
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.prompt_generator.generator import PromptGenerator


def save_prompts_to_csv(prompts, output_file):
    """Save prompts to CSV file."""
    if not prompts:
        return

    # Get all keys from first prompt
    fieldnames = list(prompts[0].keys())

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(prompts)

    print(f"✓ Saved {len(prompts)} prompts to {output_file}")

# Client list
CLIENTS = [
    {
        'name': 'Natasha Denona',
        'slug': 'natasha_denona',
        'keywords_file': 'data/natasha_denona_keywords.csv',
        'personas_file': 'data/natasha_denona_personas.json',
        'prompt_count': 150
    },
    {
        'name': 'Say I Do',
        'slug': 'say_i_do',
        'keywords_file': 'data/say_i_do_keywords.csv',
        'personas_file': 'data/say_i_do_personas.json',
        'prompt_count': 150
    },
    {
        'name': 'Espresso Capital',
        'slug': 'espresso_capital',
        'keywords_file': 'data/espresso_capital_keywords.csv',
        'personas_file': 'data/espresso_capital_personas.json',
        'prompt_count': 150
    },
    {
        'name': 'Saint Javelin',
        'slug': 'saint_javelin',
        'keywords_file': 'data/saint_javelin_keywords.csv',
        'personas_file': 'data/saint_javelin_personas.json',
        'prompt_count': 150
    },
    {
        'name': 'Clearevent',
        'slug': 'clearevent',
        'keywords_file': 'data/clearevent_keywords.csv',
        'personas_file': 'data/clearevent_personas.json',
        'prompt_count': 150
    }
]


def generate_prompts_for_client(client_config):
    """Generate prompts for a single client."""
    print(f"\n{'='*60}")
    print(f"Generating prompts for {client_config['name']}")
    print(f"{'='*60}\n")

    # Initialize generator
    generator = PromptGenerator(
        personas_file=client_config['personas_file'],
        keywords_file=client_config['keywords_file']
    )

    # Generate prompts
    prompts = generator.generate_prompts(
        total_count=client_config['prompt_count']
    )

    # Save to client-specific file
    output_file = f"data/generated_prompts_{client_config['slug']}.csv"
    save_prompts_to_csv(prompts, output_file)

    print(f"\n✅ Generated {len(prompts)} prompts for {client_config['name']}")
    print(f"📁 Saved to: {output_file}")

    # Print summary
    print(f"\nPrompt Quality Summary:")
    quality_scores = [p.get('quality_score', 0) for p in prompts]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    print(f"  Average Quality Score: {avg_quality:.1f}/100")

    high_quality = len([s for s in quality_scores if s >= 75])
    print(f"  High Quality (75+): {high_quality} prompts ({high_quality/len(prompts)*100:.1f}%)")

    return prompts


def main():
    """Generate prompts for all clients."""
    print("\n" + "="*60)
    print("AI VISIBILITY TRACKER - BATCH PROMPT GENERATION")
    print("="*60)
    print(f"\nGenerating prompts for {len(CLIENTS)} clients...")

    all_results = {}

    for client_config in CLIENTS:
        try:
            prompts = generate_prompts_for_client(client_config)
            all_results[client_config['slug']] = {
                'success': True,
                'count': len(prompts),
                'file': f"data/generated_prompts_{client_config['slug']}.csv"
            }
        except Exception as e:
            print(f"\n❌ Error generating prompts for {client_config['name']}: {str(e)}")
            all_results[client_config['slug']] = {
                'success': False,
                'error': str(e)
            }

    # Print final summary
    print(f"\n{'='*60}")
    print("GENERATION COMPLETE - SUMMARY")
    print(f"{'='*60}\n")

    successful = sum(1 for r in all_results.values() if r.get('success'))
    print(f"✅ Successfully generated prompts for {successful}/{len(CLIENTS)} clients\n")

    for client_config in CLIENTS:
        slug = client_config['slug']
        result = all_results[slug]

        if result.get('success'):
            print(f"✓ {client_config['name']}: {result['count']} prompts → {result['file']}")
        else:
            print(f"✗ {client_config['name']}: Failed - {result.get('error', 'Unknown error')}")

    print("\n" + "="*60)
    print("Next steps:")
    print("1. Review generated prompts in the Streamlit app")
    print("2. Filter by quality score (recommend 75+)")
    print("3. Export approved prompts for testing")
    print("4. Run main.py with exported CSV to test AI visibility")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
