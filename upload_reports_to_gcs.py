#!/usr/bin/env python3
"""
Upload Reports to Google Cloud Storage

This script uploads all generated reports to GCS after running visibility tests.
Run this after ./run_natasha_report.sh completes.

Usage:
    python upload_reports_to_gcs.py --client "Natasha Denona"
    python upload_reports_to_gcs.py --all  # Upload all clients
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from storage.gcs_manager import GCSManager


def upload_client_reports(client_name: str, gcs: GCSManager):
    """
    Upload all reports for a specific client.

    Args:
        client_name: Name of the client
        gcs: GCS Manager instance
    """
    print(f"\n📤 Uploading reports for: {client_name}")
    print("=" * 60)

    try:
        uploaded_files = gcs.upload_client_reports(client_name, reports_dir='data/reports')

        if uploaded_files:
            print(f"\n✅ Successfully uploaded {len(uploaded_files)} files:")
            for file_path in uploaded_files:
                print(f"   • {file_path}")
        else:
            print(f"\n⚠️  No reports found for {client_name}")
            print(f"   Make sure you've run the visibility tests first.")

    except Exception as e:
        print(f"\n❌ Error uploading reports: {e}")
        sys.exit(1)


def get_all_clients_from_reports(reports_dir: str = 'data/reports') -> list:
    """
    Get list of all clients from report files.

    Args:
        reports_dir: Directory containing reports

    Returns:
        List of client names
    """
    reports_path = Path(reports_dir)

    if not reports_path.exists():
        return []

    clients = set()

    # Find all HTML reports (visibility_report_*.html)
    for html_file in reports_path.glob('visibility_report_*.html'):
        # Extract client name from filename
        name_part = html_file.stem.replace('visibility_report_', '')
        # Convert slug to client name
        client_name = name_part.replace('_', ' ')
        clients.add(client_name)

    return sorted(list(clients))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Upload visibility reports to Google Cloud Storage"
    )

    parser.add_argument(
        '--client',
        help='Client name to upload reports for'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Upload reports for all clients found in data/reports/'
    )

    parser.add_argument(
        '--bucket',
        help='GCS bucket name (overrides config)'
    )

    parser.add_argument(
        '--credentials',
        help='Path to GCS service account JSON file'
    )

    args = parser.parse_args()

    if not args.client and not args.all:
        parser.error("Must specify either --client or --all")

    # Check for credentials
    if not args.credentials:
        # Try to find credentials file
        possible_paths = [
            'gcs-credentials.json',
            '.gcs-credentials.json',
            Path.home() / '.gcs-credentials.json'
        ]

        for path in possible_paths:
            if Path(path).exists():
                args.credentials = str(path)
                break

    if not args.credentials:
        print("❌ Error: GCS credentials file not found.")
        print("\nPlease provide credentials using:")
        print("  --credentials path/to/gcs-credentials.json")
        print("\nOr place gcs-credentials.json in the project root directory.")
        print("\nSee GOOGLE_CLOUD_SETUP.md for setup instructions.")
        sys.exit(1)

    print("🔐 Using credentials:", args.credentials)

    # Initialize GCS Manager
    try:
        gcs = GCSManager(
            bucket_name=args.bucket,
            credentials_path=args.credentials
        )
        print(f"✓ Connected to GCS bucket: {gcs.bucket_name}")
    except Exception as e:
        print(f"❌ Failed to connect to GCS: {e}")
        print("\nCheck that:")
        print("  1. Credentials file is valid")
        print("  2. Bucket name is correct")
        print("  3. Service account has Storage Object Admin role")
        sys.exit(1)

    # Upload reports
    if args.all:
        print("\n📊 Finding all clients in data/reports/...")
        clients = get_all_clients_from_reports()

        if not clients:
            print("❌ No client reports found in data/reports/")
            print("   Run visibility tests first: ./run_natasha_report.sh")
            sys.exit(1)

        print(f"   Found {len(clients)} clients:")
        for client in clients:
            print(f"   • {client}")

        print("\n📤 Uploading all reports...")

        total_uploaded = 0
        for client in clients:
            upload_client_reports(client, gcs)
            # Count uploaded files
            uploaded_files = gcs.list_client_reports(client)
            total_uploaded += len(uploaded_files)

        print("\n" + "=" * 60)
        print(f"🎉 Upload Complete!")
        print(f"   Total clients: {len(clients)}")
        print(f"   Total files uploaded: {total_uploaded}")
        print("\n💡 Tip: Reboot your Streamlit Cloud app to see the new reports")
        print("=" * 60)

    else:
        upload_client_reports(args.client, gcs)

        print("\n" + "=" * 60)
        print(f"🎉 Upload Complete for {args.client}!")
        print("\n💡 Tip: Reboot your Streamlit Cloud app to see the new report")
        print("=" * 60)


if __name__ == '__main__':
    main()
