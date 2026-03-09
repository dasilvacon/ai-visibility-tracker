#!/usr/bin/env python3
"""Quick script to upload Natasha Denona report to GCS"""

from google.cloud import storage
import os

def upload_report():
    """Upload the redesigned HTML report to GCS"""

    # Initialize GCS client (uses default credentials from gcloud)
    client = storage.Client(project='gen-lang-client-0243073678')
    bucket = client.bucket('ai-visibility-reports-dasilva')

    # Files to upload
    files_to_upload = [
        ('data/reports/visibility_report_Natasha_Denona.html', 'Natasha_Denona/visibility_report_Natasha_Denona.html'),
        ('data/reports/action_plan_Natasha_Denona.csv', 'Natasha_Denona/action_plan_Natasha_Denona.csv'),
        ('data/reports/competitors_Natasha_Denona.csv', 'Natasha_Denona/competitors_Natasha_Denona.csv'),
        ('data/reports/raw_data_Natasha_Denona.csv', 'Natasha_Denona/raw_data_Natasha_Denona.csv'),
        ('data/reports/sources_Natasha_Denona.csv', 'Natasha_Denona/sources_Natasha_Denona.csv'),
        ('data/reports/visibility_analysis_Natasha_Denona.txt', 'Natasha_Denona/visibility_analysis_Natasha_Denona.txt'),
    ]

    print("📤 Uploading Natasha Denona reports to GCS...\n")

    for local_path, gcs_path in files_to_upload:
        if not os.path.exists(local_path):
            print(f"⚠️  Skipping {local_path} (not found)")
            continue

        print(f"   Uploading {os.path.basename(local_path)}...", end=" ")

        try:
            blob = bucket.blob(gcs_path)

            # Set content type based on file extension
            if local_path.endswith('.html'):
                blob.content_type = 'text/html'
            elif local_path.endswith('.csv'):
                blob.content_type = 'text/csv'
            elif local_path.endswith('.txt'):
                blob.content_type = 'text/plain'

            blob.upload_from_filename(local_path)
            print("✅")
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    print("\n✅ Upload complete!")
    print("\nYour redesigned report is now live at:")
    print("   https://dashboard.dasilvaconsulting.com")
    print("\nLogin with:")
    print("   Username: natasha_denona")
    print("   Password: (from secrets.toml)")

    return True

if __name__ == '__main__':
    upload_report()
