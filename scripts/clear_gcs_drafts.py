#!/usr/bin/env python3
"""
Clear all prompt drafts from GCS for a specific client.

Usage:
    python scripts/clear_gcs_drafts.py "Saint Javelin"
    python scripts/clear_gcs_drafts.py --all    # clear ALL drafts

This is a standalone script that directly cleans GCS without
needing the dashboard. Run it when old prompts keep coming back.
"""

import json
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/clear_gcs_drafts.py <client_name>")
        print("       python scripts/clear_gcs_drafts.py --all")
        sys.exit(1)

    target = sys.argv[1]
    clear_all = (target == '--all')

    # ── GCS cleanup ──
    print("Connecting to GCS...")
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from src.client_manager.gcs_sync import GCSClientSync
        gcs = GCSClientSync()
        bucket = gcs.bucket
        print(f"✓ Connected to bucket: {bucket.name}")
    except Exception as e:
        print(f"✗ Failed to connect to GCS: {e}")
        sys.exit(1)

    # List all draft blobs
    prefix = "prompt-data/drafts/"
    blobs = list(bucket.list_blobs(prefix=prefix))
    print(f"Found {len(blobs)} draft files in GCS")

    deleted = 0
    for blob in blobs:
        if clear_all:
            print(f"  Deleting: {blob.name}")
            blob.delete()
            deleted += 1
        else:
            # Check if this draft belongs to the target client
            try:
                content = blob.download_as_text()
                data = json.loads(content)
                if data.get('client_name') == target:
                    print(f"  Deleting: {blob.name} (client: {target})")
                    blob.delete()
                    deleted += 1
                else:
                    print(f"  Keeping:  {blob.name} (client: {data.get('client_name', '?')})")
            except Exception as e:
                print(f"  Error reading {blob.name}: {e}")

    print(f"\n✓ Deleted {deleted} draft files from GCS")

    # Also clean batch metadata
    batch_blob = bucket.blob("prompt-data/prompt_batches.json")
    if batch_blob.exists():
        try:
            content = batch_blob.download_as_text()
            batches = json.loads(content)
            before = len(batches)
            if clear_all:
                batches = {}
            else:
                batches = {k: v for k, v in batches.items()
                           if v.get('client_name') != target}
            after = len(batches)
            batch_blob.upload_from_string(json.dumps(batches, indent=2, default=str))
            print(f"✓ Cleaned batch metadata: {before} → {after} entries")
        except Exception as e:
            print(f"⚠ Batch metadata cleanup failed: {e}")

    # ── Local cleanup ──
    draft_dir = Path('data/prompt_generation/drafts')
    local_deleted = 0
    if draft_dir.exists():
        for df in draft_dir.glob('batch_*_prompts.json'):
            try:
                with open(df, 'r') as f:
                    data = json.load(f)
                if clear_all or data.get('client_name') == target:
                    df.unlink()
                    local_deleted += 1
            except Exception:
                pass
    print(f"✓ Deleted {local_deleted} local draft files")

    batches_file = Path('data/prompt_batches.json')
    if batches_file.exists():
        try:
            with open(batches_file, 'r') as f:
                batches = json.load(f)
            if clear_all:
                batches = {}
            else:
                batches = {k: v for k, v in batches.items()
                           if v.get('client_name') != target}
            with open(batches_file, 'w') as f:
                json.dump(batches, f, indent=2, default=str)
            print("✓ Cleaned local batch metadata")
        except Exception:
            pass

    print(f"\nDone! Old prompts for {'ALL clients' if clear_all else target} have been purged.")
    print("Now redeploy or restart the container to start fresh.")


if __name__ == '__main__':
    main()
