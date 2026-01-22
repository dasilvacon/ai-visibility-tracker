#!/usr/bin/env python3
"""
Clean conversational filler from existing prompts.
"""

import re
import csv
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.prompts_db import PromptsDatabase

def clean_prompt_text(prompt: str) -> str:
    """
    Remove conversational filler from prompt text.

    Args:
        prompt: Original prompt text

    Returns:
        Cleaned prompt text
    """
    # Define patterns to remove (case insensitive)
    filler_patterns = [
        r'^Hi,\s*',
        r'^Hey,\s*',
        r'^Hello,\s*',
        r'\s*Thanks!?\s*$',
        r'\s*Appreciate any help!?\s*$',
        r'\s*Any advice\??\s*$',
        r'^Can anyone help\?\s*',
        r'^Quick question:\s*',
        r'^I was wondering,\s*',
        r'\s*\(especially [^)]+\)\s*$',  # Remove "(especially xxx)" at end
    ]

    cleaned = prompt

    for pattern in filler_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # Clean up extra whitespace
    cleaned = ' '.join(cleaned.split())

    # Remove trailing punctuation that doesn't make sense
    cleaned = cleaned.strip(' .,!?')

    return cleaned


def main():
    """Clean all prompts in the CSV database."""

    csv_path = 'data/generated_prompts.csv'

    # Initialize database
    db = PromptsDatabase(csv_path)

    # Get all prompts
    prompts = db.load_prompts()

    print(f"Found {len(prompts)} prompts to clean")
    print("=" * 60)

    cleaned_count = 0
    cleaned_prompts = []

    for prompt in prompts:
        prompt_id = prompt['prompt_id']
        original_text = prompt['prompt_text']

        # Clean the text
        cleaned_text = clean_prompt_text(original_text)

        # Create updated prompt
        updated_prompt = prompt.copy()
        updated_prompt['prompt_text'] = cleaned_text

        cleaned_prompts.append(updated_prompt)

        # Only print if changed
        if cleaned_text != original_text:
            cleaned_count += 1

            if cleaned_count <= 10:  # Show first 10 examples
                print(f"\nPrompt ID: {prompt_id}")
                print(f"BEFORE: {original_text}")
                print(f"AFTER:  {cleaned_text}")

    # Write back to CSV
    print("\n" + "=" * 60)
    print(f"Writing {len(cleaned_prompts)} prompts back to CSV...")

    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=db.fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_prompts)

    print("\n" + "=" * 60)
    print(f"✓ Cleaned {cleaned_count} out of {len(prompts)} prompts")
    print(f"✓ CSV updated successfully at: {csv_path}")


if __name__ == '__main__':
    main()
