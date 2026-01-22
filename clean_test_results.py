#!/usr/bin/env python3
"""
Clean conversational filler from test result files.
"""

import re
import json
import glob
import os


def clean_prompt_text(prompt: str) -> str:
    """Remove conversational filler from prompt text."""
    filler_patterns = [
        r'^Hi,\s*',
        r'^Hey,\s*',
        r'^Hello,\s*',
        r'\s*Thanks!?\s*$',
        r'\s*Appreciate any help!?\s*$',
        r'\s*Any advice\??',  # Remove "Any advice" anywhere
        r'^Can anyone help\?\s*',
        r'^Quick question:\s*',
        r'^I was wondering,\s*',
        r'\s*\(especially [^)]+\)',  # Remove "(especially xxx)" anywhere
        r'\s*Specifically interested in [^.?!]+',  # Remove "Specifically interested in xxx"
    ]

    cleaned = prompt
    for pattern in filler_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # Clean up extra whitespace and punctuation
    cleaned = ' '.join(cleaned.split())
    cleaned = cleaned.strip(' .,!?')

    # Fix double question marks or weird punctuation
    cleaned = re.sub(r'\?\?+', '?', cleaned)
    cleaned = re.sub(r'\s+\?', '?', cleaned)

    return cleaned


def main():
    """Clean all test result JSON files."""

    result_files = glob.glob('data/results/*.json')

    print(f"Found {len(result_files)} result files to clean")
    print("=" * 60)

    cleaned_count = 0

    for filepath in result_files:
        try:
            # Read the JSON file
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check if it has a prompt_text field
            if 'prompt_text' in data:
                original = data['prompt_text']
                cleaned = clean_prompt_text(original)

                if cleaned != original:
                    cleaned_count += 1
                    data['prompt_text'] = cleaned

                    # Write back
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)

                    if cleaned_count <= 5:  # Show first 5 examples
                        print(f"\nFile: {os.path.basename(filepath)}")
                        print(f"BEFORE: {original}")
                        print(f"AFTER:  {cleaned}")

        except Exception as e:
            print(f"ERROR processing {filepath}: {e}")

    print("\n" + "=" * 60)
    print(f"✓ Cleaned {cleaned_count} out of {len(result_files)} result files")


if __name__ == '__main__':
    main()
