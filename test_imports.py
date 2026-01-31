"""Test if all imports work"""
import sys
sys.path.insert(0, 'src')

print("Testing imports...")

try:
    from prompt_generator_pages import settings
    print("✓ settings imported")
except Exception as e:
    print(f"✗ settings import failed: {e}")

try:
    from prompt_generator_pages import simple_client_setup
    print("✓ simple_client_setup imported")
except Exception as e:
    print(f"✗ simple_client_setup import failed: {e}")

try:
    from prompt_generator_pages import library
    print("✓ library imported")
except Exception as e:
    print(f"✗ library import failed: {e}")

try:
    from src.prompt_generator.batch_manager import BatchManager
    print("✓ batch_manager imported")
except Exception as e:
    print(f"✗ batch_manager import failed: {e}")

print("\nAll import tests complete!")
