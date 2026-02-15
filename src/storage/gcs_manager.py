"""
Google Cloud Storage Manager - Handle uploads and downloads of reports.
"""

import os
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from google.cloud import storage
from google.oauth2 import service_account
import streamlit as st


class GCSManager:
    """Manage Google Cloud Storage operations for visibility reports."""

    def __init__(self, bucket_name: Optional[str] = None, credentials_path: Optional[str] = None):
        """
        Initialize GCS Manager.

        Args:
            bucket_name: Name of the GCS bucket (reads from secrets if not provided)
            credentials_path: Path to service account JSON (reads from secrets if not provided)
        """
        # Try to get config from Streamlit secrets first (for cloud deployment)
        if hasattr(st, 'secrets') and 'gcs' in st.secrets:
            self.bucket_name = st.secrets['gcs'].get('bucket_name')

            # Check if credentials are provided as JSON string (Streamlit Cloud)
            if 'credentials' in st.secrets['gcs']:
                creds_dict = json.loads(st.secrets['gcs']['credentials'])
                self.credentials = service_account.Credentials.from_service_account_info(creds_dict)
            elif 'credentials_file' in st.secrets['gcs']:
                creds_path = st.secrets['gcs']['credentials_file']
                self.credentials = service_account.Credentials.from_service_account_file(creds_path)
            else:
                raise ValueError("No credentials found in Streamlit secrets")
        else:
            # Fall back to parameters or environment variables
            self.bucket_name = bucket_name or os.getenv('GCS_BUCKET_NAME')

            if credentials_path:
                self.credentials = service_account.Credentials.from_service_account_file(credentials_path)
            elif os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                self.credentials = service_account.Credentials.from_service_account_file(
                    os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                )
            else:
                # Try default credentials
                self.credentials = None

        if not self.bucket_name:
            raise ValueError("GCS bucket name not configured. Set bucket_name parameter or configure secrets.")

        # Initialize client
        self.client = storage.Client(credentials=self.credentials)
        self.bucket = self.client.bucket(self.bucket_name)

    def upload_report(self, local_path: str, client_name: str, keep_history: bool = True) -> str:
        """
        Upload a report file to GCS.

        Args:
            local_path: Path to local file
            client_name: Name of the client (used for folder structure)
            keep_history: If True, also save to history folder with timestamp

        Returns:
            GCS blob path
        """
        local_file = Path(local_path)

        if not local_file.exists():
            raise FileNotFoundError(f"File not found: {local_path}")

        # Sanitize client name for folder structure
        client_slug = client_name.replace(' ', '_')

        # Main file path (always overwrites latest)
        main_blob_path = f"{client_slug}/{local_file.name}"

        # Upload main file
        blob = self.bucket.blob(main_blob_path)
        blob.upload_from_filename(str(local_file))

        print(f"✓ Uploaded: {main_blob_path}")

        # Also save to history folder if requested
        if keep_history:
            timestamp = datetime.now().strftime('%Y-%m')
            history_blob_path = f"{client_slug}/history/{timestamp}/{local_file.name}"
            history_blob = self.bucket.blob(history_blob_path)
            history_blob.upload_from_filename(str(local_file))
            print(f"✓ Archived: {history_blob_path}")

        return main_blob_path

    def upload_client_reports(self, client_name: str, reports_dir: str = 'data/reports') -> List[str]:
        """
        Upload all reports for a specific client.

        Args:
            client_name: Name of the client
            reports_dir: Local directory containing reports

        Returns:
            List of uploaded blob paths
        """
        reports_path = Path(reports_dir)
        client_slug = client_name.replace(' ', '_')

        # Find all report files for this client
        patterns = [
            f"visibility_report_{client_slug}.html",
            f"executive_summary_{client_slug}.pdf",
            f"visibility_analysis_{client_slug}.txt",
            f"raw_data_{client_slug}.csv",
            f"competitors_{client_slug}.csv",
            f"sources_{client_slug}.csv",
            f"action_plan_{client_slug}.csv",
            f"personas_{client_slug}.csv",
        ]

        uploaded = []

        for pattern in patterns:
            file_path = reports_path / pattern
            if file_path.exists():
                try:
                    blob_path = self.upload_report(str(file_path), client_name, keep_history=True)
                    uploaded.append(blob_path)
                except Exception as e:
                    print(f"✗ Failed to upload {pattern}: {e}")

        return uploaded

    def download_report(self, client_name: str, filename: str, local_dir: str = '/tmp') -> str:
        """
        Download a report file from GCS.

        Args:
            client_name: Name of the client
            filename: Name of the file to download
            local_dir: Local directory to save file

        Returns:
            Path to downloaded file
        """
        client_slug = client_name.replace(' ', '_')
        blob_path = f"{client_slug}/{filename}"

        blob = self.bucket.blob(blob_path)

        if not blob.exists():
            raise FileNotFoundError(f"File not found in GCS: {blob_path}")

        local_path = Path(local_dir) / filename
        local_path.parent.mkdir(parents=True, exist_ok=True)

        blob.download_to_filename(str(local_path))

        return str(local_path)

    def get_report_content(self, client_name: str, filename: str) -> bytes:
        """
        Get report file content directly from GCS without downloading.

        Args:
            client_name: Name of the client
            filename: Name of the file

        Returns:
            File content as bytes
        """
        client_slug = client_name.replace(' ', '_')
        blob_path = f"{client_slug}/{filename}"

        blob = self.bucket.blob(blob_path)

        if not blob.exists():
            raise FileNotFoundError(f"File not found in GCS: {blob_path}")

        return blob.download_as_bytes()

    def list_client_reports(self, client_name: str) -> List[dict]:
        """
        List all reports available for a client.

        Args:
            client_name: Name of the client

        Returns:
            List of report metadata dicts
        """
        client_slug = client_name.replace(' ', '_')
        prefix = f"{client_slug}/"

        blobs = self.bucket.list_blobs(prefix=prefix)

        reports = []
        for blob in blobs:
            if '/history/' not in blob.name:  # Only current reports, not history
                reports.append({
                    'name': blob.name.split('/')[-1],
                    'path': blob.name,
                    'size': blob.size,
                    'updated': blob.updated,
                    'content_type': blob.content_type
                })

        return reports

    def check_report_exists(self, client_name: str, filename: str) -> bool:
        """
        Check if a report file exists in GCS.

        Args:
            client_name: Name of the client
            filename: Name of the file

        Returns:
            True if file exists, False otherwise
        """
        client_slug = client_name.replace(' ', '_')
        blob_path = f"{client_slug}/{filename}"

        blob = self.bucket.blob(blob_path)
        return blob.exists()

    def get_all_clients(self) -> List[str]:
        """
        Get list of all clients with reports in GCS.

        Returns:
            List of client names
        """
        blobs = self.bucket.list_blobs()

        clients = set()
        for blob in blobs:
            # Extract client name from path (first part before /)
            parts = blob.name.split('/')
            if len(parts) > 1:
                # Convert slug back to client name
                client_slug = parts[0]
                client_name = client_slug.replace('_', ' ')
                clients.add(client_name)

        return sorted(list(clients))
