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
                    # Preserve directory structure for client files
                    # GCS path: client-data/{slug}/{filename}
                    # Check if it's a nested path (slug/filename) or flat (filename only)
                    parts = relative_path.split('/')
                    if len(parts) == 2:
                        # Nested: client-data/slug/filename -> data/slug/filename
                        client_slug, filename = parts
                        destination = local_path / client_slug / filename
                    else:
                        # Flat: client-data/filename -> data/filename
                        destination = local_path / relative_path

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

    def upload_prompt_data(self) -> bool:
        """
        Upload prompt data files to GCS for persistence across deployments.

        This includes:
        - data/generated_prompts.csv (main prompt library)
        - data/archived_prompts.csv (archived prompts)
        - data/prompt_batches.json (batch metadata)
        - data/prompt_generation/drafts/*.json (draft batches)
        - data/prompt_generation/approved/*.csv (approved exports)

        Returns:
            True if successful, False otherwise
        """
        prompt_prefix = 'prompt-data/'

        try:
            uploaded_count = 0

            # Upload main prompt files
            main_files = [
                'data/generated_prompts.csv',
                'data/archived_prompts.csv',
                'data/prompt_batches.json',
            ]

            for local_path in main_files:
                local_file = Path(local_path)
                if local_file.exists():
                    gcs_path = f"{prompt_prefix}{local_file.name}"
                    blob = self.bucket.blob(gcs_path)
                    blob.upload_from_filename(str(local_file))
                    print(f"✓ Uploaded {local_path} → gs://{self.bucket_name}/{gcs_path}")
                    uploaded_count += 1

            # Upload draft batches
            drafts_dir = Path('data/prompt_generation/drafts')
            if drafts_dir.exists():
                for draft_file in drafts_dir.glob('*.json'):
                    gcs_path = f"{prompt_prefix}drafts/{draft_file.name}"
                    blob = self.bucket.blob(gcs_path)
                    blob.upload_from_filename(str(draft_file))
                    print(f"✓ Uploaded {draft_file} → gs://{self.bucket_name}/{gcs_path}")
                    uploaded_count += 1

            # Upload approved exports
            approved_dir = Path('data/prompt_generation/approved')
            if approved_dir.exists():
                for approved_file in approved_dir.glob('*.csv'):
                    gcs_path = f"{prompt_prefix}approved/{approved_file.name}"
                    blob = self.bucket.blob(gcs_path)
                    blob.upload_from_filename(str(approved_file))
                    print(f"✓ Uploaded {approved_file} → gs://{self.bucket_name}/{gcs_path}")
                    uploaded_count += 1

            print(f"✓ Uploaded {uploaded_count} prompt data files to GCS")
            return True

        except Exception as e:
            print(f"✗ Failed to upload prompt data: {e}")
            return False

    def download_prompt_data(self, local_dir: str = 'data') -> bool:
        """
        Download prompt data files from GCS.

        Args:
            local_dir: Base local directory

        Returns:
            True if successful, False otherwise
        """
        prompt_prefix = 'prompt-data/'

        try:
            local_path = Path(local_dir)

            # List all blobs with prompt-data/ prefix
            blobs = list(self.bucket.list_blobs(prefix=prompt_prefix))

            if not blobs:
                print("No prompt data found in GCS (this is OK for first run)")
                return True

            downloaded_count = 0
            for blob in blobs:
                # Skip directory markers
                if blob.name.endswith('/'):
                    continue

                # Extract relative path after prompt-data/
                relative_path = blob.name[len(prompt_prefix):]

                # Determine destination
                if relative_path.startswith('drafts/'):
                    destination = local_path / 'prompt_generation' / relative_path
                elif relative_path.startswith('approved/'):
                    destination = local_path / 'prompt_generation' / relative_path
                else:
                    # Main files go directly in data/
                    destination = local_path / relative_path

                destination.parent.mkdir(parents=True, exist_ok=True)
                blob.download_to_filename(str(destination))
                downloaded_count += 1
                print(f"✓ Downloaded gs://{self.bucket_name}/{blob.name} → {destination}")

            print(f"✓ Downloaded {downloaded_count} prompt data files from GCS")
            return True

        except Exception as e:
            print(f"✗ Failed to download prompt data: {e}")
            return False

    def upload_test_results(self, client_slug: str = None) -> bool:
        """
        Upload test results to GCS for persistence across deployments.

        This includes:
        - data/results/{client_slug}/*.json (individual test results)
        - data/results/{client_slug}/results_summary.csv (summary CSV)
        - data/results/{client_slug}/monthly_scores.json (historical tracking)

        Args:
            client_slug: Client identifier for per-client isolation

        Returns:
            True if successful, False otherwise
        """
        if not client_slug:
            print("⚠️ No client_slug provided to upload_test_results")
            return False

        results_prefix = f'test-results/{client_slug}/'

        try:
            uploaded_count = 0
            results_dir = Path(f'data/results/{client_slug}')

            if not results_dir.exists():
                print(f"No test results directory found for {client_slug} (this is OK for new setups)")
                return True

            # Upload results_summary.csv
            summary_csv = results_dir / 'results_summary.csv'
            if summary_csv.exists():
                gcs_path = f"{results_prefix}results_summary.csv"
                blob = self.bucket.blob(gcs_path)
                blob.upload_from_filename(str(summary_csv))
                print(f"✓ Uploaded {summary_csv} → gs://{self.bucket_name}/{gcs_path}")
                uploaded_count += 1

            # Upload monthly_scores.json
            monthly_scores = results_dir / 'monthly_scores.json'
            if monthly_scores.exists():
                gcs_path = f"{results_prefix}monthly_scores.json"
                blob = self.bucket.blob(gcs_path)
                blob.upload_from_filename(str(monthly_scores))
                print(f"✓ Uploaded {monthly_scores} → gs://{self.bucket_name}/{gcs_path}")
                uploaded_count += 1

            # Upload individual test result JSON files
            for json_file in results_dir.glob('test_*.json'):
                gcs_path = f"{results_prefix}tests/{json_file.name}"
                blob = self.bucket.blob(gcs_path)
                blob.upload_from_filename(str(json_file))
                uploaded_count += 1

            if uploaded_count > 0:
                print(f"✓ Uploaded {uploaded_count} test result files to GCS for {client_slug}")
            else:
                print(f"No test results to upload for {client_slug}")

            return True

        except Exception as e:
            print(f"✗ Failed to upload test results for {client_slug}: {e}")
            return False

    def download_test_results(self, client_slug: str = None, local_dir: str = 'data') -> bool:
        """
        Download test results from GCS for a specific client.

        Args:
            client_slug: Client identifier for per-client isolation (if None, downloads all)
            local_dir: Base local directory

        Returns:
            True if successful, False otherwise
        """
        try:
            local_path = Path(local_dir)
            downloaded_count = 0

            if client_slug:
                # Download for specific client
                results_prefix = f'test-results/{client_slug}/'
                results_dir = local_path / 'results' / client_slug
                results_dir.mkdir(parents=True, exist_ok=True)

                blobs = list(self.bucket.list_blobs(prefix=results_prefix))

                if not blobs:
                    print(f"No test results found in GCS for {client_slug} (this is OK for first run)")
                    return True

                for blob in blobs:
                    if blob.name.endswith('/'):
                        continue

                    relative_path = blob.name[len(results_prefix):]

                    if relative_path.startswith('tests/'):
                        filename = Path(relative_path).name
                        destination = results_dir / filename
                    else:
                        destination = results_dir / relative_path

                    destination.parent.mkdir(parents=True, exist_ok=True)
                    blob.download_to_filename(str(destination))
                    downloaded_count += 1

                if downloaded_count > 0:
                    print(f"✓ Downloaded {downloaded_count} test result files for {client_slug}")

            else:
                # Download for all clients
                results_prefix = 'test-results/'
                blobs = list(self.bucket.list_blobs(prefix=results_prefix))

                if not blobs:
                    print("No test results found in GCS (this is OK for first run)")
                    return True

                for blob in blobs:
                    if blob.name.endswith('/'):
                        continue

                    # Parse: test-results/{client_slug}/...
                    relative_path = blob.name[len(results_prefix):]
                    parts = relative_path.split('/', 1)
                    if len(parts) < 2:
                        continue

                    blob_client_slug = parts[0]
                    file_path = parts[1]

                    results_dir = local_path / 'results' / blob_client_slug

                    if file_path.startswith('tests/'):
                        filename = Path(file_path).name
                        destination = results_dir / filename
                    else:
                        destination = results_dir / file_path

                    destination.parent.mkdir(parents=True, exist_ok=True)
                    blob.download_to_filename(str(destination))
                    downloaded_count += 1

                if downloaded_count > 0:
                    print(f"✓ Downloaded {downloaded_count} test result files from GCS")

            return True

        except Exception as e:
            print(f"✗ Failed to download test results: {e}")
            return False

    def upload_reports(self, client_slug: str = None) -> bool:
        """
        Upload report files to GCS for persistence with per-client isolation.

        Args:
            client_slug: Client identifier for per-client isolation

        Returns:
            True if successful, False otherwise
        """
        if not client_slug:
            print("⚠️ No client_slug provided to upload_reports")
            return False

        reports_prefix = f'reports/{client_slug}/'

        try:
            uploaded_count = 0
            reports_dir = Path(f'data/reports/{client_slug}')

            if not reports_dir.exists():
                print(f"No reports directory found for {client_slug}")
                return True

            # Upload actual report files only — exclude ephemeral process status files
            # (.log, .pid, .status files are runtime process state, not reports)
            EXCLUDED_EXTENSIONS = {'.log', '.pid', '.status'}
            files_to_upload = list(reports_dir.glob('*.*'))
            files_to_upload = [
                f for f in files_to_upload
                if not f.name.startswith('.') and f.suffix not in EXCLUDED_EXTENSIONS
            ]

            for report_file in files_to_upload:
                gcs_path = f"{reports_prefix}{report_file.name}"
                blob = self.bucket.blob(gcs_path)
                blob.upload_from_filename(str(report_file))
                print(f"✓ Uploaded {report_file} → gs://{self.bucket_name}/{gcs_path}")
                uploaded_count += 1

            if uploaded_count > 0:
                print(f"✓ Uploaded {uploaded_count} report files to GCS for {client_slug}")
            else:
                print(f"No reports to upload for {client_slug}")

            return True

        except Exception as e:
            print(f"✗ Failed to upload reports for {client_slug}: {e}")
            return False

    def download_reports(self, client_slug: str = None, local_dir: str = 'data') -> bool:
        """
        Download report files from GCS with per-client isolation.

        Args:
            client_slug: Client identifier for per-client isolation (if None, downloads all)
            local_dir: Base local directory

        Returns:
            True if successful, False otherwise
        """
        try:
            local_path = Path(local_dir)
            downloaded_count = 0

            if client_slug:
                # Download for specific client
                reports_prefix = f'reports/{client_slug}/'
                reports_dir = local_path / 'reports' / client_slug
                reports_dir.mkdir(parents=True, exist_ok=True)

                blobs = list(self.bucket.list_blobs(prefix=reports_prefix))

                if not blobs:
                    print(f"No reports found in GCS for {client_slug} (this is OK for first run)")
                    return True

                # Skip ephemeral process status files (.log, .pid, .status)
                SKIP_EXTENSIONS = {'.log', '.pid', '.status'}

                for blob in blobs:
                    if blob.name.endswith('/'):
                        continue

                    filename = blob.name[len(reports_prefix):]
                    if Path(filename).suffix in SKIP_EXTENSIONS:
                        continue

                    destination = reports_dir / filename

                    blob.download_to_filename(str(destination))
                    downloaded_count += 1
                    print(f"✓ Downloaded gs://{self.bucket_name}/{blob.name} → {destination}")

                if downloaded_count > 0:
                    print(f"✓ Downloaded {downloaded_count} report files for {client_slug}")

            else:
                # Download for all clients
                reports_prefix = 'reports/'
                blobs = list(self.bucket.list_blobs(prefix=reports_prefix))

                if not blobs:
                    print("No reports found in GCS (this is OK for first run)")
                    return True

                # Skip ephemeral process status files (.log, .pid, .status)
                SKIP_EXTENSIONS = {'.log', '.pid', '.status'}

                for blob in blobs:
                    if blob.name.endswith('/'):
                        continue

                    # Parse: reports/{client_slug}/filename
                    relative_path = blob.name[len(reports_prefix):]
                    parts = relative_path.split('/', 1)
                    if len(parts) < 2:
                        continue

                    blob_client_slug = parts[0]
                    filename = parts[1]

                    if Path(filename).suffix in SKIP_EXTENSIONS:
                        continue

                    reports_dir = local_path / 'reports' / blob_client_slug
                    reports_dir.mkdir(parents=True, exist_ok=True)
                    destination = reports_dir / filename

                    blob.download_to_filename(str(destination))
                    downloaded_count += 1
                    print(f"✓ Downloaded gs://{self.bucket_name}/{blob.name} → {destination}")

                if downloaded_count > 0:
                    print(f"✓ Downloaded {downloaded_count} report files from GCS")

            return True

        except Exception as e:
            print(f"✗ Failed to download reports: {e}")
            return False

    def sync_all_data(self) -> bool:
        """
        Upload ALL app data to GCS (convenience method for full sync).
        Discovers client slugs from the client registry and syncs per-client data.

        Returns:
            True if all syncs successful, False otherwise
        """
        import json

        print("=" * 50)
        print("FULL DATA SYNC TO GCS")
        print("=" * 50)

        results = []

        print("\n1. Syncing client registry...")
        results.append(self.upload_registry())

        print("\n2. Syncing prompt data...")
        results.append(self.upload_prompt_data())

        # Discover client slugs from registry
        client_slugs = []
        try:
            registry_path = Path('data/clients.json')
            if registry_path.exists():
                with open(registry_path, 'r') as f:
                    registry = json.load(f)
                client_slugs = [c['slug'] for c in registry.get('clients', []) if c.get('slug')]
        except Exception:
            pass

        if client_slugs:
            for slug in client_slugs:
                print(f"\n3. Syncing test results for {slug}...")
                results.append(self.upload_test_results(slug))

                print(f"\n4. Syncing reports for {slug}...")
                results.append(self.upload_reports(slug))
        else:
            print("\n⚠️ No client slugs found in registry — skipping per-client sync")

        print("\n" + "=" * 50)
        if all(results):
            print("ALL DATA SYNCED SUCCESSFULLY")
        else:
            print("SOME SYNCS FAILED - check errors above")
        print("=" * 50)

        return all(results)
