#!/usr/bin/env python3
"""
Test script for new Perplexity and Gemini integrations.
This verifies the clients can be instantiated and basic structure is correct.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api_clients.perplexity_client import PerplexityClient
from api_clients.gemini_client import GeminiClient


def test_client_initialization():
    """Test that clients can be instantiated."""
    print("Testing client initialization...\n")

    # Test config
    test_config = {
        'testing': {
            'default_temperature': 0.7,
            'max_tokens': 1000,
            'timeout_seconds': 30
        }
    }

    # Test Perplexity Client
    print("1. Testing Perplexity Client...")
    try:
        perplexity_client = PerplexityClient(
            api_key="test_key",
            model="pplx-70b-online",
            config=test_config
        )
        assert perplexity_client.platform_name == 'perplexity'
        assert perplexity_client.model == 'pplx-70b-online'
        print("   ✓ Perplexity client instantiated successfully")
        print(f"   ✓ Platform name: {perplexity_client.platform_name}")
        print(f"   ✓ Model: {perplexity_client.model}")
    except Exception as e:
        print(f"   ✗ Failed to instantiate Perplexity client: {e}")
        return False

    print()

    # Test Gemini Client
    print("2. Testing Gemini Client...")
    try:
        gemini_client = GeminiClient(
            api_key="test_key",
            model="gemini-2.0-flash-exp",
            config=test_config
        )
        assert gemini_client.platform_name == 'gemini'
        assert gemini_client.model == 'gemini-2.0-flash-exp'
        print("   ✓ Gemini client instantiated successfully")
        print(f"   ✓ Platform name: {gemini_client.platform_name}")
        print(f"   ✓ Model: {gemini_client.model}")
    except Exception as e:
        print(f"   ✗ Failed to instantiate Gemini client: {e}")
        return False

    print()
    return True


def test_method_existence():
    """Test that required methods exist."""
    print("Testing required methods exist...\n")

    test_config = {'testing': {}}

    # Test Perplexity
    print("1. Checking Perplexity methods...")
    perplexity_client = PerplexityClient("test", "pplx-70b-online", test_config)
    assert hasattr(perplexity_client, 'send_prompt')
    assert hasattr(perplexity_client, 'test_prompt')
    assert hasattr(perplexity_client, 'validate_config')
    print("   ✓ All required methods present")

    print()

    # Test Gemini
    print("2. Checking Gemini methods...")
    gemini_client = GeminiClient("test", "gemini-2.0-flash-exp", test_config)
    assert hasattr(gemini_client, 'send_prompt')
    assert hasattr(gemini_client, 'test_prompt')
    assert hasattr(gemini_client, 'validate_config')
    print("   ✓ All required methods present")

    print()
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing New Platform Integrations: Perplexity & Gemini")
    print("=" * 60)
    print()

    tests = [
        test_client_initialization,
        test_method_existence,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ✗ Test failed with exception: {e}")
            failed += 1

    print("=" * 60)
    print(f"Tests Passed: {passed}/{len(tests)}")
    print(f"Tests Failed: {failed}/{len(tests)}")
    print("=" * 60)
    print()

    if failed == 0:
        print("✓ All tests passed! Clients are ready to use.")
        print()
        print("Next steps:")
        print("1. Add your API keys to config/config.json:")
        print("   - Perplexity: https://docs.perplexity.ai/")
        print("   - Gemini: https://ai.google.dev/")
        print("2. Install new dependency: pip install google-generativeai")
        print("3. Run: python main.py --help to see usage")
        return 0
    else:
        print("✗ Some tests failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
