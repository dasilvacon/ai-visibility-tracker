#!/usr/bin/env python3
"""
Simple test to verify API keys work for Perplexity and Gemini.
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api_clients.perplexity_client import PerplexityClient
from api_clients.gemini_client import GeminiClient


def test_api_keys():
    """Test that API keys work."""

    # Load config
    try:
        with open('config/config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print('✗ config/config.json not found')
        print('  Please copy config/config.template.json to config/config.json')
        return False

    api_keys = config.get('api_keys', {})

    print("="*60)
    print("Testing API Keys")
    print("="*60)

    success_count = 0

    # Test Perplexity
    print("\n1. Testing Perplexity API...")
    if 'perplexity' in api_keys and not api_keys['perplexity'].startswith('YOUR_'):
        try:
            client = PerplexityClient(
                api_key=api_keys['perplexity'],
                model=config.get('models', {}).get('perplexity', 'sonar'),
                config=config
            )
            result = client.send_prompt('What is 2+2?', temperature=0.7, max_tokens=50)

            if result['success']:
                print('   ✓ Perplexity API works!')
                print(f'   Response: {result["response_text"][:80]}...')
                success_count += 1
            else:
                print(f'   ✗ Error: {result["error"]}')
        except Exception as e:
            print(f'   ✗ Exception: {e}')
    else:
        print('   ⊘ API key not configured')

    # Test Gemini
    print("\n2. Testing Gemini API...")
    if 'gemini' in api_keys and not api_keys['gemini'].startswith('YOUR_'):
        try:
            client = GeminiClient(
                api_key=api_keys['gemini'],
                model=config.get('models', {}).get('gemini', 'gemini-1.5-flash'),
                config=config
            )
            result = client.send_prompt('What is 2+2?', temperature=0.7, max_tokens=50)

            if result['success']:
                print('   ✓ Gemini API works!')
                print(f'   Response: {result["response_text"][:80]}...')
                success_count += 1
            else:
                print(f'   ✗ Error: {result["error"]}')
        except Exception as e:
            print(f'   ✗ Exception: {e}')
    else:
        print('   ⊘ API key not configured')

    print("\n" + "="*60)
    if success_count == 2:
        print("✓ All API keys working! You're ready to run visibility tests.")
        print("\nNext step:")
        print("  python3 main.py --platforms perplexity gemini --prompts data/prompts.csv")
        return True
    elif success_count > 0:
        print(f"⚠ {success_count}/2 API keys working")
        return True
    else:
        print("✗ No API keys working. Please check your config/config.json")
        return False


if __name__ == '__main__':
    success = test_api_keys()
    sys.exit(0 if success else 1)
