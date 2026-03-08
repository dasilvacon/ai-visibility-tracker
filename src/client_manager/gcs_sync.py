"""
Google Cloud Storage sync for client data.
Replaces fragile git auto-commit with reliable GCS storage.
"""

import os
from pathlib import Path
from typing import Optional
from google.cloud import storage


class GCSClientSync:
    """Manages syncing client data to/from Google Cloud Storage."""

    def __init__(self, bucket_name: str = 'ai-visibility-reports-dasilva'):
        """
        Initialize GCS sync.

        Args:
            bucket_name: GCS bucket name
        """
        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.gcs_prefix = 'client-data/'

    def upload_client_files(self, client_slug: str, files: dict) -> bool:
        """
        Upload client files to GCS.

        Args:
            client_slug: Client identifier (e.g., 'natasha_denona')
            files: Dict of file paths {type: local_path}

        Returns:
            True if successful, False otherwise
        """
        try:
            for file_type, local_path in files.items():
                if not local_path:
                    continue

                local_file = Path(local_path)
                if not local_file.exists():
                    print(f"Warning: {local_path} does not exist, skipping")
                    continue

                # Upload to GCS: client-data/{slug}/filename
                gcs_path = f"{self.gcs_prefix}{client_slug}/{local_file.name}"
                blob = self.bucket.blob(gcs_path)
                blob.upload_from_filename(str(local_file))
                print(f"✓ Uploaded {local_path} → gs://{self.bucket_name}/{gcs_path}")

            return True

        except Exception as e:
            print(f"✗ Failed to upload client files: {e}")
            return False

    def upload_registry(self, registry_path: str = 'data/clients.json') -> bool:
        """
        Upload the client registry to GCS.

        Args:
            registry_path: Path to clients.json

        Returns:
            True if successful, False otherwise
        """
        try:
            registry_file = Path(registry_path)
            if not registry_file.exists():
                print(f"Warning: {registry_path} does not exist")
                return False

            gcs_path = f"{self.gcs_prefix}clients.json"
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_filename(str(registry_file))
            print(f"✓ Uploaded registry → gs://{self.bucket_name}/{gcs_path}")
            return True

        except Exception as e:
            print(f"✗ Failed to upload registry: {e}")
            return False

    def download_all_client_data(self, local_dir: str = 'data') -> bool:
        """
        Download all client data from GCS to local directory.

        Args:
            local_dir: Local directory to download to

        Returns:
            True if successful, False otherwise
        """
        try:
            local_path = Path(local_dir)
            local_path.mkdir(parents=True, exist_ok=True)

            # List all blobs with client-data/ prefix
            blobs = self.bucket.list_blobs(prefix=self.gcs_prefix)

            downloaded_count = 0
            for blob in blobs:
                # Skip directory markers
                if blob.name.endswith('/'):
                    continue

                # Extract relative path after client-data/
                relative_path = blob.name[len(self.gcs_prefix):]

                # Download to local directory
                if relative_path == 'clients.json':
                    # Registry goes directly in data/
                    destination = local_path / 'clients.json'
                else:
                    # Client files go in data/ (e.g., data/natasha_denona_keywords.csv)
                    # Extract just the filename (not the slug subdirectory)
                    filename = Path(relative_path).name
                    destination = local_path / filename

                destination.parent.mkdir(parents=True, exist_ok=True)
                blob.download_to_filename(str(destination))
                downloaded_count += 1
                print(f"✓ Downloaded gs://{self.bucket_name}/{blob.name} → {destination}")

            if downloaded_count == 0:
                print(f"No client data found in GCS (this is OK for first run)")
            else:
                print(f"✓ Downloaded {downloaded_count} files from GCS")

            return True

        except Exception as e:
            print(f"✗ Failed to download client data: {e}")
            return False

    def sync_client_to_gcs(self, client_slug: str, files: dict) -> bool:
        """
        Convenience method: Upload client files AND registry in one call.

        Args:
            client_slug: Client identifier
            files: Dict of file paths

        Returns:
            True if both operations successful
        """
        files_ok = self.upload_client_files(client_slug, files)
        registry_ok = self.upload_registry()
        return files_ok and registry_ok
