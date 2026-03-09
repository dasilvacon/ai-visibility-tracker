#!/usr/bin/env python3
"""
Manual script to sync ALL app data to Google Cloud Storage.

Use this script to:
1. Upload all local data to GCS before deployment
2. Recover after data loss by uploading local backups
3. Manually sync all data changes

Data synced:
- Client registry (clients.json)
- Prompt data (generated_prompts.csv, drafts, batches)
- Test results (results_summary.csv, individual tests, monthly scores)
- Reports (HTML, PDF, CSV files)

Prerequisites:
- Google Cloud SDK authenticated (gcloud auth application-default login)
- Or running on a machine with GCS access
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')


def count_files(directory: Path, pattern: str) -> int:
    """Count files matching pattern in directory."""
    if not directory.exists():
        return 0
    return len(list(directory.glob(pattern)))


def main():
    """Sync all app data to GCS."""
    print("=" * 60)
    print("FULL DATA SYNC TO GOOGLE CLOUD STORAGE")
    print("=" * 60)

    # Check what local data exists
    print("\n1. Checking local data...")

    data_summary = []

    # Client registry
    clients_json = Path('data/clients.json')
    if clients_json.exists():
        data_summary.append("   ✓ Client registry (clients.json)")

    # Prompt data
    main_csv = Path('data/generated_prompts.csv')
    if main_csv.exists():
        with open(main_csv, 'r') as f:
            lines = f.readlines()
        prompt_count = len(lines) - 1
        data_summary.append(f"   ✓ Prompts ({prompt_count} in generated_prompts.csv)")

    drafts_count = count_files(Path('data/prompt_generation/drafts'), '*.json')
    if drafts_count:
        data_summary.append(f"   ✓ Draft batches ({drafts_count} files)")

    # Test results
    results_dir = Path('data/results')
    if results_dir.exists():
        test_count = count_files(results_dir, 'test_*.json')
        if test_count:
            data_summary.append(f"   ✓ Test results ({test_count} tests)")
        if (results_dir / 'monthly_scores.json').exists():
            data_summary.append("   ✓ Historical scores (monthly_scores.json)")

    # Reports
    reports_dir = Path('data/reports')
    if reports_dir.exists():
        html_count = count_files(reports_dir, '*.html')
        pdf_count = count_files(reports_dir, '*.pdf')
        csv_count = count_files(reports_dir, '*.csv')
        if html_count or pdf_count or csv_count:
            data_summary.append(f"   ✓ Reports ({html_count} HTML, {pdf_count} PDF, {csv_count} CSV)")

    if not data_summary:
        print("\n   No data found locally!")
        print("   Nothing to sync.")
        return 0

    print("\n   Found the following data:")
    for item in data_summary:
        print(item)

    # Confirm sync
    print("\n2. Ready to sync to GCS...")
    response = input("   Continue? (y/n): ")

    if response.lower() != 'y':
        print("   Cancelled.")
        return 0

    # Perform sync
    print("\n3. Syncing to Google Cloud Storage...")

    try:
        from src.client_manager.gcs_sync import GCSClientSync

        gcs_sync = GCSClientSync()
        success = gcs_sync.sync_all_data()

        if success:
            print("\n" + "=" * 60)
            print("SUCCESS! All data synced to GCS.")
            print("=" * 60)
            print("\nYour data is now safely stored in cloud storage.")
            print("Future deployments will automatically download this data.")
        else:
            print("\n" + "=" * 60)
            print("SOME SYNCS FAILED - See errors above")
            print("=" * 60)
            return 1

    except Exception as e:
        print(f"\n   ERROR: {e}")
        print("\n   Make sure you're authenticated with Google Cloud:")
        print("   1. Install gcloud CLI")
        print("   2. Run: gcloud auth application-default login")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
