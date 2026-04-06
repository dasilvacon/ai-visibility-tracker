#!/usr/bin/env python3
"""
Run visibility tests for all active clients, sequentially.

Can be triggered by:
1. Cloud Scheduler → Cloud Run Job (automatic monthly)
2. Manual invocation from the terminal
3. The "Run All" button in the dashboard

Tests run ONE client at a time to avoid rate limiting.
Each client's test supports resume (skips already-tested prompts).
Reports only generate when ALL prompts for a client are complete.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)


def load_clients():
    """Load all active clients from registry."""
    clients_file = Path('data/clients.json')
    if not clients_file.exists():
        print("ERROR: data/clients.json not found")
        return []

    with open(clients_file) as f:
        data = json.load(f)

    return data.get('clients', [])


def get_client_files(client):
    """Get prompts and brand config file paths for a client."""
    slug = client['slug']
    files = client.get('files', {})

    # Prompts file
    prompts = files.get('prompts') or f'data/{slug}/{slug}_prompts.csv'
    if not Path(prompts).exists():
        return None, None, f"Prompts file not found: {prompts}"

    # Brand config
    brand_config = files.get('brand_config') or f'data/{slug}/{slug}_brand_config.json'
    if not Path(brand_config).exists():
        return None, None, f"Brand config not found: {brand_config}"

    return prompts, brand_config, None


def run_client_test(client, prompts_file, brand_config):
    """
    Run a visibility test for a single client.

    Returns:
        (success: bool, message: str)
    """
    name = client['name']
    slug = client['slug']

    print(f"\n{'='*60}")
    print(f"  TESTING: {name}")
    print(f"  Prompts: {prompts_file}")
    print(f"  Config:  {brand_config}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    cmd = [
        sys.executable, 'main.py',
        '--prompts', prompts_file,
        '--analyze',
        '--brand-config', brand_config
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            timeout=7200,  # 2 hour max per client
            capture_output=False  # Show output in real time
        )

        if result.returncode == 0:
            print(f"\n✓ {name}: Test COMPLETE — reports generated")
            # Upload to GCS
            try:
                from src.client_manager.gcs_sync import GCSClientSync
                gcs = GCSClientSync()
                gcs.upload_test_results(slug)
                gcs.upload_reports(slug)
                print(f"✓ {name}: Results and reports uploaded to GCS")
            except Exception as e:
                print(f"⚠ {name}: GCS upload failed: {e}")
            return True, "Complete"

        elif result.returncode == 2:
            print(f"\n⚠ {name}: Test INCOMPLETE — partial results saved")
            # Upload partial results
            try:
                from src.client_manager.gcs_sync import GCSClientSync
                gcs = GCSClientSync()
                gcs.upload_test_results(slug)
                print(f"✓ {name}: Partial results uploaded to GCS")
            except Exception as e:
                print(f"⚠ {name}: GCS upload failed: {e}")
            return False, "Incomplete — needs resume"

        else:
            print(f"\n✗ {name}: Test FAILED (exit code {result.returncode})")
            return False, f"Failed with exit code {result.returncode}"

    except subprocess.TimeoutExpired:
        print(f"\n✗ {name}: Test TIMED OUT after 2 hours")
        return False, "Timed out"
    except Exception as e:
        print(f"\n✗ {name}: Test ERROR: {e}")
        return False, str(e)


def main():
    """Run tests for all clients sequentially."""
    print(f"\n{'#'*60}")
    print(f"  AI VISIBILITY TRACKER — BATCH TEST RUN")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    clients = load_clients()
    if not clients:
        print("No clients found. Exiting.")
        sys.exit(1)

    print(f"\nFound {len(clients)} clients: {', '.join(c['name'] for c in clients)}\n")

    results = {}
    for client in clients:
        name = client['name']

        # Get files
        prompts, brand_config, error = get_client_files(client)
        if error:
            print(f"\n⚠ SKIPPING {name}: {error}")
            results[name] = ('skipped', error)
            continue

        # Run test
        success, message = run_client_test(client, prompts, brand_config)
        results[name] = ('success' if success else 'failed', message)

        # Brief pause between clients to avoid rate limit carryover
        if client != clients[-1]:
            print(f"\n⏳ Waiting 30 seconds before next client...")
            time.sleep(30)

    # Summary
    print(f"\n\n{'#'*60}")
    print(f"  BATCH TEST SUMMARY")
    print(f"  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}\n")

    for name, (status, message) in results.items():
        icon = '✓' if status == 'success' else '⚠' if status == 'skipped' else '✗'
        print(f"  {icon} {name}: {message}")

    # Exit with error if any failed
    failures = [n for n, (s, _) in results.items() if s == 'failed']
    if failures:
        print(f"\n{len(failures)} client(s) failed or incomplete. Re-run to resume.")
        sys.exit(1)
    else:
        print(f"\nAll {len(results)} clients completed successfully!")
        sys.exit(0)


if __name__ == '__main__':
    main()
