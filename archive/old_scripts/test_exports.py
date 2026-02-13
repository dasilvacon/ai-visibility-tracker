#!/usr/bin/env python3
"""Quick test script to generate all exports using existing data."""

import sys
import os
sys.path.insert(0, 'src')

from main import VisibilityTracker

# Initialize tracker
tracker = VisibilityTracker('config/config.json')

# Run analysis (this will generate all exports)
print("Running analysis with exports...")
result = tracker.analyze_results('data/natasha_denona_brand_config.json')

print("\n✅ Analysis complete!")
print(f"Text report: {result.get('text_report_path')}")
print(f"HTML report: {result.get('html_report_path')}")

exports = result.get('exports', {})
print("\n📦 Exports generated:")
for export_type, path in exports.items():
    if path:
        file_size = os.path.getsize(path) / 1024  # KB
        print(f"  ✓ {export_type}: {path} ({file_size:.1f} KB)")
    else:
        print(f"  ✗ {export_type}: FAILED")
