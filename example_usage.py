#!/usr/bin/env python3
"""
Example usage of the AI Visibility Tracker programmatically.

This script demonstrates how to use the tracker's components
directly in your own Python code.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.prompts_db import PromptsDatabase
from tracking.results_tracker import ResultsTracker
from reporting.report_generator import ReportGenerator


def example_prompts_management():
    """Example: Managing prompts database."""
    print("=" * 60)
    print("Example 1: Prompts Database Management")
    print("=" * 60)

    db = PromptsDatabase('data/prompts_template.csv')

    # Load all prompts
    prompts = db.load_prompts()
    print(f"\nTotal prompts: {len(prompts)}")

    # Get summary statistics
    stats = db.get_summary_stats()
    print(f"Unique personas: {stats['unique_personas']}")
    print(f"Personas: {', '.join(stats['personas'])}")

    # Filter prompts
    technical_prompts = db.filter_prompts(category='technical')
    print(f"\nTechnical prompts: {len(technical_prompts)}")

    # Get specific prompt
    prompt = db.get_prompt_by_id('1')
    if prompt:
        print(f"\nPrompt #1: {prompt['prompt_text'][:50]}...")

    print()


def example_results_analysis():
    """Example: Analyzing test results."""
    print("=" * 60)
    print("Example 2: Results Analysis")
    print("=" * 60)

    tracker = ResultsTracker('data/results')

    # Load all results
    results = tracker.load_results_summary()

    if not results:
        print("\nNo results found. Run some tests first!")
        print("Example: python main.py")
        return

    print(f"\nTotal test results: {len(results)}")

    # Analyze by platform
    platforms = set(r.get('platform') for r in results)
    print(f"Platforms tested: {', '.join(platforms)}")

    for platform in platforms:
        platform_results = tracker.get_results_by_platform(platform)
        successful = sum(1 for r in platform_results
                        if r.get('success') == 'True' or r.get('success') is True)
        print(f"  {platform}: {successful}/{len(platform_results)} successful")

    print()


def example_custom_reporting():
    """Example: Custom report generation."""
    print("=" * 60)
    print("Example 3: Custom Reporting")
    print("=" * 60)

    tracker = ResultsTracker('data/results')
    report_gen = ReportGenerator('data/reports')

    results = tracker.load_results_summary()

    if not results:
        print("\nNo results found. Run some tests first!")
        return

    # Generate quick summary
    report_gen.print_quick_summary(results)

    # Generate full reports
    summary_path = report_gen.generate_summary_report(results)
    print(f"Summary report saved to: {summary_path}")

    comparison_path = report_gen.generate_platform_comparison(results)
    print(f"Comparison report saved to: {comparison_path}")

    print()


def example_add_custom_prompt():
    """Example: Adding a custom prompt."""
    print("=" * 60)
    print("Example 4: Adding a Custom Prompt")
    print("=" * 60)

    # Note: This would add to the actual CSV file
    # Comment out if you don't want to modify the database

    print("\nThis example shows how to add a prompt programmatically.")
    print("(Commented out to avoid modifying your database)")
    print()

    # Uncomment to actually add a prompt:
    """
    db = PromptsDatabase('data/prompts_template.csv')

    new_prompt = {
        'prompt_id': '100',
        'persona': 'developer',
        'category': 'technical',
        'intent_type': 'code_review',
        'prompt_text': 'Review this Python code for security vulnerabilities.',
        'expected_visibility_score': 8.5,
        'notes': 'Security-focused code review'
    }

    success = db.add_prompt(new_prompt)
    if success:
        print("✓ Prompt added successfully!")
    else:
        print("✗ Failed to add prompt")
    """


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "AI Visibility Tracker - Usage Examples" + " " * 9 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")

    example_prompts_management()
    example_results_analysis()
    example_custom_reporting()
    example_add_custom_prompt()

    print("=" * 60)
    print("For more examples, see README.md")
    print("=" * 60)
    print()


if __name__ == '__main__':
    main()
