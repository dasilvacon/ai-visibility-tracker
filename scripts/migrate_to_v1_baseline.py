#!/usr/bin/env python3
"""
One-time migration: freeze all currently-active prompt CSVs as v1.0-baseline.

For each active client, this script:

1. Reads the current `data/{slug}/{slug}_prompts.csv`
2. Writes an archive copy under `data/prompt-archive/{slug}/v1.0-baseline/`
   (both `prompts.csv` and `meta.json`), and an active meta sidecar at
   `data/{slug}/{slug}_prompts.meta.json`
3. Mirrors both to GCS under `client-data/{slug}/` and
   `prompt-archive/{slug}/v1.0-baseline/` (optional, --no-gcs to skip)
4. Backfills `prompts_version` = `v1.0-baseline` on every row of
   `data/results/{slug}/results_summary.csv` (if it exists)

The script is idempotent: re-running it after a successful migration does
nothing new. See docs/prompt-versioning.md for the schema.

Usage:
    # Local + GCS, all clients
    python3 scripts/migrate_to_v1_baseline.py

    # Local only
    python3 scripts/migrate_to_v1_baseline.py --no-gcs

    # One client only
    python3 scripts/migrate_to_v1_baseline.py --client ontario_caregiver_organization

    # Dry run — report what would change, write nothing
    python3 scripts/migrate_to_v1_baseline.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import sys
from pathlib import Path
from typing import List, Optional

# Allow `from src...` imports when run from the repo root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.prompt_generator.version_manager import PromptVersionManager  # noqa: E402


# Clients we migrate. Keep this list in sync with data/clients.json — we
# intentionally list them explicitly here to fail loudly if a client folder
# is missing rather than silently skipping it.
DEFAULT_CLIENTS: List[str] = [
    'ontario_caregiver_organization',
    'uniuni',
    'say_i_do',
    'espresso_capital',
    'natasha_denona',
]

BASELINE_VERSION = 'v1.0-baseline'


# ---------------------------------------------------------------------------
# Migration per client
# ---------------------------------------------------------------------------

def migrate_client(
    slug: str,
    *,
    data_dir: Path,
    results_dir: Path,
    gcs_sync=None,
    dry_run: bool = False,
) -> bool:
    """
    Migrate a single client. Returns True on success (or already-migrated),
    False if the client has no active prompts file to migrate.
    """
    print(f"\n=== {slug} ===")

    active_csv = data_dir / slug / f"{slug}_prompts.csv"
    if not active_csv.exists():
        print(f"  ⚠️ Skipping — no active prompts CSV at {active_csv}")
        return False

    manager = PromptVersionManager(
        client_slug=slug,
        data_dir=data_dir,
        gcs=gcs_sync,
    )

    existing = manager.get_active_version()
    if existing and existing.get('version') == BASELINE_VERSION:
        print(f"  ✓ Already at {BASELINE_VERSION} — skipping archive step")
    else:
        if dry_run:
            print(f"  [dry-run] Would archive {active_csv.name} as {BASELINE_VERSION}")
        else:
            meta = manager.archive_current_as(
                BASELINE_VERSION,
                generated_by='scripts/migrate_to_v1_baseline.py',
                generator_version='1.0',
                source_model='legacy',
                format_tag='legacy',
                notes=(
                    'Frozen as v1.0-baseline during migration from unversioned '
                    'state. Content unchanged from the prompts CSV that was '
                    'live at migration time.'
                ),
                upload_to_gcs=gcs_sync is not None,
            )
            print(
                f"  ✓ Archived {meta['prompt_count']} prompts as {BASELINE_VERSION}"
                f" (hash {meta['content_hash'][:20]}…)"
            )

    # Backfill results_summary.csv
    results_csv = results_dir / slug / 'results_summary.csv'
    if results_csv.exists():
        if dry_run:
            needs = _count_rows_missing_version(results_csv)
            print(
                f"  [dry-run] Would backfill {needs} rows in {results_csv} "
                f"with prompts_version={BASELINE_VERSION}"
            )
        else:
            added = _backfill_results_version(results_csv, BASELINE_VERSION)
            if added == 0:
                print(f"  ✓ results_summary.csv already has prompts_version column")
            else:
                print(f"  ✓ Backfilled {added} rows in {results_csv}")
    else:
        print(f"  (no results_summary.csv at {results_csv} — nothing to backfill)")

    return True


# ---------------------------------------------------------------------------
# results_summary.csv backfill
# ---------------------------------------------------------------------------

def _count_rows_missing_version(csv_path: Path) -> int:
    """Count rows that would be touched by the backfill (dry-run helper)."""
    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        if 'prompts_version' not in (reader.fieldnames or []):
            return sum(1 for _ in reader)
        return sum(
            1 for row in reader
            if not (row.get('prompts_version') or '').strip()
        )


def _backfill_results_version(csv_path: Path, version: str) -> int:
    """
    Add a `prompts_version` column (if missing) and fill every blank cell
    with `version`. Writes atomically via a sibling temp file.

    Returns the number of rows that received a value. Returns 0 if the
    column already existed and was already fully populated.
    """
    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    if not rows:
        # Empty file — nothing to backfill. Still make sure the header
        # includes the new column so future writes line up.
        if 'prompts_version' not in fieldnames:
            fieldnames.append('prompts_version')
            tmp_path = csv_path.with_suffix(csv_path.suffix + '.tmp')
            with open(tmp_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            shutil.move(str(tmp_path), str(csv_path))
        return 0

    column_added = 'prompts_version' not in fieldnames
    if column_added:
        fieldnames.append('prompts_version')

    touched = 0
    for row in rows:
        current = (row.get('prompts_version') or '').strip()
        if not current:
            row['prompts_version'] = version
            touched += 1

    if touched == 0 and not column_added:
        return 0

    tmp_path = csv_path.with_suffix(csv_path.suffix + '.tmp')
    with open(tmp_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    shutil.move(str(tmp_path), str(csv_path))
    return touched


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--client',
        action='append',
        dest='clients',
        help=(
            'Client slug to migrate. Pass multiple times for multiple clients. '
            'Defaults to all known active clients.'
        ),
    )
    parser.add_argument(
        '--data-dir',
        default='data',
        help="Root of per-client data folders (default: data)",
    )
    parser.add_argument(
        '--results-dir',
        default='data/results',
        help="Root of per-client results folders (default: data/results)",
    )
    parser.add_argument(
        '--no-gcs',
        action='store_true',
        help="Skip GCS upload (local filesystem only)",
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Print what would happen; write nothing",
    )
    args = parser.parse_args()

    clients: List[str] = args.clients or DEFAULT_CLIENTS
    data_dir = Path(args.data_dir)
    results_dir = Path(args.results_dir)

    gcs_sync = None
    if not args.no_gcs and not args.dry_run:
        try:
            from src.client_manager.gcs_sync import GCSClientSync
            gcs_sync = GCSClientSync()
            print(f"✓ GCS sync enabled (bucket: {gcs_sync.bucket_name})")
        except Exception as exc:
            print(f"⚠️ Could not initialize GCS sync — continuing local-only: {exc}")
            gcs_sync = None
    else:
        if args.dry_run:
            print("(dry-run — GCS disabled)")
        else:
            print("(GCS disabled via --no-gcs)")

    print(f"Clients: {', '.join(clients)}")
    print(f"Data dir: {data_dir.resolve()}")
    print(f"Results dir: {results_dir.resolve()}")

    successes = 0
    failures: List[str] = []

    for slug in clients:
        try:
            ok = migrate_client(
                slug,
                data_dir=data_dir,
                results_dir=results_dir,
                gcs_sync=gcs_sync,
                dry_run=args.dry_run,
            )
            if ok:
                successes += 1
        except Exception as exc:
            failures.append(slug)
            print(f"  ✗ FAILED for {slug}: {exc}")

    print("\n" + "=" * 60)
    print(f"Migrated: {successes}/{len(clients)} client(s)")
    if failures:
        print(f"Failed:   {', '.join(failures)}")
        return 1
    if args.dry_run:
        print("Dry-run complete — no files were modified.")
    else:
        print("Migration complete.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
