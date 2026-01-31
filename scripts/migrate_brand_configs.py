#!/usr/bin/env python3
"""
Migrate Brand Config Files from v1.0 to v2.0

This script migrates all existing brand_config.json files in the data/ directory
from v1.0 schema (flat competitor list) to v2.0 schema (categorized competitors,
business goals, discovered competitors).

Run this once after deploying the new Client Manager features.

Usage:
    python3 scripts/migrate_brand_configs.py

    or with backup:
    python3 scripts/migrate_brand_configs.py --backup
"""

import sys
from pathlib import Path
import json
import shutil
from datetime import datetime
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.brand_config_manager import BrandConfigManager


def backup_file(file_path: Path, backup_dir: Path) -> None:
    """
    Create a backup of a file.

    Args:
        file_path: Path to file to backup
        backup_dir: Directory to store backup
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
    backup_path = backup_dir / backup_name

    shutil.copy2(file_path, backup_path)
    print(f"  ✓ Backup created: {backup_path}")


def migrate_all_clients(create_backups: bool = True) -> None:
    """
    Migrate all brand_config.json files in the data directory.

    Args:
        create_backups: If True, create backups before migration
    """
    data_dir = Path('data')
    backup_dir = Path('data/backups')

    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return

    # Create backup directory if needed
    if create_backups:
        backup_dir.mkdir(exist_ok=True)
        print(f"📁 Backups will be saved to: {backup_dir}\n")

    # Find all brand_config.json files
    config_files = list(data_dir.glob('*_brand_config.json'))

    if not config_files:
        print("✅ No brand config files found to migrate.")
        return

    print(f"Found {len(config_files)} brand config file(s) to migrate:\n")

    manager = BrandConfigManager()
    migrated_count = 0
    skipped_count = 0
    error_count = 0

    for config_file in config_files:
        print(f"Processing: {config_file.name}")

        try:
            # Load config (auto-migrates if needed)
            with open(config_file, 'r') as f:
                current_config = json.load(f)

            # Check if already v2.0
            schema_version = current_config.get('metadata', {}).get('schema_version', '1.0')

            if schema_version == '2.0':
                print(f"  ⏭️  Already v2.0, skipping\n")
                skipped_count += 1
                continue

            # Create backup if requested
            if create_backups:
                backup_file(config_file, backup_dir)

            # Load and migrate
            config = manager.load_config(str(config_file))

            # Save migrated config
            manager.save_config(str(config_file), config)

            print(f"  ✅ Successfully migrated to v2.0")

            # Show summary of migration
            expected_count = len(config.get('competitors', {}).get('expected', []))
            print(f"  📊 Migrated {expected_count} competitors to categorized structure\n")

            migrated_count += 1

        except Exception as e:
            print(f"  ❌ Error migrating {config_file.name}: {str(e)}\n")
            error_count += 1

    # Summary
    print("=" * 60)
    print("Migration Summary:")
    print(f"  ✅ Migrated: {migrated_count}")
    print(f"  ⏭️  Skipped (already v2.0): {skipped_count}")
    print(f"  ❌ Errors: {error_count}")
    print("=" * 60)

    if error_count == 0:
        print("\n🎉 All migrations completed successfully!")
    else:
        print(f"\n⚠️  {error_count} file(s) failed to migrate. Check errors above.")


def verify_migration(file_path: Path) -> None:
    """
    Verify a migrated config file.

    Args:
        file_path: Path to config file to verify
    """
    print(f"\n🔍 Verifying: {file_path.name}")

    manager = BrandConfigManager()

    try:
        config = manager.load_config(str(file_path))

        is_valid, errors = manager.validate_schema(config)

        if is_valid:
            print("  ✅ Schema validation passed")

            # Show stats
            brand_name = config['brand']['name']
            expected_count = len(config.get('competitors', {}).get('expected', []))
            discovered_count = len(config.get('competitors', {}).get('discovered', []))

            print(f"  📋 Brand: {brand_name}")
            print(f"  📊 Expected competitors: {expected_count}")
            print(f"  🔍 Discovered competitors: {discovered_count}")

            # Show competitor categories
            if expected_count > 0:
                categories = {}
                for comp in config['competitors']['expected']:
                    cat = comp.get('category', 'unknown')
                    categories[cat] = categories.get(cat, 0) + 1

                print("  📂 Categories:")
                for cat, count in categories.items():
                    print(f"     - {cat}: {count}")
        else:
            print("  ❌ Schema validation failed:")
            for error in errors:
                print(f"     - {error}")

    except Exception as e:
        print(f"  ❌ Error verifying: {str(e)}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Migrate brand_config.json files from v1.0 to v2.0'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating backups before migration'
    )
    parser.add_argument(
        '--verify',
        type=str,
        metavar='FILE',
        help='Verify a specific config file after migration'
    )

    args = parser.parse_args()

    if args.verify:
        verify_migration(Path(args.verify))
    else:
        print("🔄 Brand Config Migration Script")
        print("=" * 60)
        migrate_all_clients(create_backups=not args.no_backup)
