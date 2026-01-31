"""
Brand Configuration Manager

Manages brand_config.json files with schema versioning, migration, and validation.
Supports v1.0 (flat competitor list) and v2.0 (categorized competitors with business goals).
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import shutil


class BrandConfigManager:
    """Manages brand configuration files with schema versioning and migration."""

    SCHEMA_VERSION = "2.0"

    COMPETITOR_CATEGORIES = ["direct", "adjacent", "aspirational"]
    DISCOVERED_STATUSES = ["emerging_threat", "occasional_mention"]

    def __init__(self):
        """Initialize the BrandConfigManager."""
        pass

    def load_config(self, path: str) -> dict:
        """
        Load brand configuration from file.
        Automatically migrates v1.0 configs to v2.0.

        Args:
            path: Path to brand_config.json file

        Returns:
            dict: Brand configuration (v2.0 schema)

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Brand config not found: {path}")

        with open(path, 'r') as f:
            config = json.load(f)

        # Check schema version
        schema_version = config.get('metadata', {}).get('schema_version', '1.0')

        if schema_version == '1.0':
            # Auto-migrate to v2.0
            print(f"Migrating {path} from v1.0 to v2.0...")
            config = self.migrate_v1_to_v2(config)

        return config

    def save_config(self, path: str, config: dict) -> None:
        """
        Save brand configuration to file with validation.
        Uses atomic write (write to temp, then rename) to prevent corruption.

        Args:
            path: Path to brand_config.json file
            config: Brand configuration dict (v2.0 schema)

        Raises:
            ValueError: If config fails validation
        """
        # Validate schema
        is_valid, errors = self.validate_schema(config)
        if not is_valid:
            raise ValueError(f"Invalid brand config schema: {', '.join(errors)}")

        # Update last_modified timestamp
        if 'metadata' not in config:
            config['metadata'] = {}
        config['metadata']['last_modified'] = datetime.utcnow().isoformat() + 'Z'
        config['metadata']['schema_version'] = self.SCHEMA_VERSION

        # Atomic write: write to temp file, then rename
        temp_path = f"{path}.tmp"
        try:
            with open(temp_path, 'w') as f:
                json.dump(config, f, indent=2)

            # Rename temp to actual (atomic operation)
            shutil.move(temp_path, path)
        except Exception as e:
            # Clean up temp file if something went wrong
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

    def migrate_v1_to_v2(self, old_config: dict) -> dict:
        """
        Migrate v1.0 brand config to v2.0 schema.

        v1.0: Flat competitor list
        v2.0: Categorized competitors, business goals, discovered competitors

        Args:
            old_config: v1.0 configuration

        Returns:
            dict: v2.0 configuration
        """
        new_config = {
            'brand': old_config.get('brand', {}),
            'competitors': {
                'expected': [],
                'discovered': []
            },
            'metadata': {
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'last_modified': datetime.utcnow().isoformat() + 'Z',
                'schema_version': self.SCHEMA_VERSION
            },
            'legacy_settings': {}
        }

        # Add business_goals to brand section
        if 'business_goals' not in new_config['brand']:
            new_config['brand']['business_goals'] = {
                'revenue_targets': '',
                'market_positioning': '',
                'target_metrics': [],
                'freeform_notes': ''
            }

        # Migrate old competitors to categorized structure
        old_competitors = old_config.get('competitors', [])

        for i, comp in enumerate(old_competitors):
            # Categorize: First 2 = direct, Next 2 = adjacent, Rest = aspirational
            if i < 2:
                category = 'direct'
            elif i < 4:
                category = 'adjacent'
            else:
                category = 'aspirational'

            new_config['competitors']['expected'].append({
                'name': comp.get('name', 'Unknown'),
                'website': comp.get('website', ''),
                'category': category,
                'added_date': datetime.utcnow().strftime('%Y-%m-%d'),
                'notes': 'Auto-migrated from v1.0'
            })

        # Preserve any other top-level keys in legacy_settings
        for key in old_config:
            if key not in ['brand', 'competitors']:
                new_config['legacy_settings'][key] = old_config[key]

        return new_config

    def validate_schema(self, config: dict) -> Tuple[bool, List[str]]:
        """
        Validate brand config against v2.0 schema.

        Args:
            config: Brand configuration to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check top-level keys
        required_keys = ['brand', 'competitors', 'metadata']
        for key in required_keys:
            if key not in config:
                errors.append(f"Missing required key: {key}")

        if errors:
            return False, errors

        # Validate brand section
        brand = config['brand']
        if 'name' not in brand or not brand['name']:
            errors.append("brand.name is required")

        # Validate competitors structure
        competitors = config['competitors']
        if 'expected' not in competitors or not isinstance(competitors['expected'], list):
            errors.append("competitors.expected must be a list")
        if 'discovered' not in competitors or not isinstance(competitors['discovered'], list):
            errors.append("competitors.discovered must be a list")

        # Validate expected competitors
        for i, comp in enumerate(competitors.get('expected', [])):
            if 'name' not in comp:
                errors.append(f"competitors.expected[{i}] missing 'name' field")
            if 'category' not in comp:
                errors.append(f"competitors.expected[{i}] missing 'category' field")
            elif comp['category'] not in self.COMPETITOR_CATEGORIES:
                errors.append(
                    f"competitors.expected[{i}] has invalid category: {comp['category']} "
                    f"(must be one of: {', '.join(self.COMPETITOR_CATEGORIES)})"
                )

        # Validate discovered competitors
        for i, comp in enumerate(competitors.get('discovered', [])):
            if 'name' not in comp:
                errors.append(f"competitors.discovered[{i}] missing 'name' field")
            if 'status' not in comp:
                errors.append(f"competitors.discovered[{i}] missing 'status' field")
            elif comp['status'] not in self.DISCOVERED_STATUSES:
                errors.append(
                    f"competitors.discovered[{i}] has invalid status: {comp['status']} "
                    f"(must be one of: {', '.join(self.DISCOVERED_STATUSES)})"
                )

        # Validate metadata
        metadata = config['metadata']
        if 'schema_version' not in metadata:
            errors.append("metadata.schema_version is required")

        return len(errors) == 0, errors

    def add_competitor(
        self,
        config: dict,
        name: str,
        website: str = '',
        category: str = 'direct',
        notes: str = ''
    ) -> dict:
        """
        Add a competitor to the expected list.

        Args:
            config: Brand configuration
            name: Competitor name
            website: Competitor website URL
            category: Category (direct, adjacent, aspirational)
            notes: Optional notes about this competitor

        Returns:
            dict: Updated configuration

        Raises:
            ValueError: If category is invalid
        """
        if category not in self.COMPETITOR_CATEGORIES:
            raise ValueError(
                f"Invalid category: {category}. Must be one of: {', '.join(self.COMPETITOR_CATEGORIES)}"
            )

        # Check if competitor already exists
        expected_competitors = config.get('competitors', {}).get('expected', [])
        for comp in expected_competitors:
            if comp['name'].lower() == name.lower():
                raise ValueError(f"Competitor '{name}' already exists in expected list")

        new_competitor = {
            'name': name,
            'website': website,
            'category': category,
            'added_date': datetime.utcnow().strftime('%Y-%m-%d'),
            'notes': notes
        }

        if 'competitors' not in config:
            config['competitors'] = {'expected': [], 'discovered': []}
        if 'expected' not in config['competitors']:
            config['competitors']['expected'] = []

        config['competitors']['expected'].append(new_competitor)

        return config

    def remove_competitor(self, config: dict, competitor_name: str) -> dict:
        """
        Remove a competitor from the expected list.

        Args:
            config: Brand configuration
            competitor_name: Name of competitor to remove

        Returns:
            dict: Updated configuration
        """
        expected_competitors = config.get('competitors', {}).get('expected', [])
        config['competitors']['expected'] = [
            comp for comp in expected_competitors
            if comp['name'].lower() != competitor_name.lower()
        ]

        return config

    def update_competitor(
        self,
        config: dict,
        competitor_name: str,
        category: Optional[str] = None,
        website: Optional[str] = None,
        notes: Optional[str] = None
    ) -> dict:
        """
        Update an existing competitor in the expected list.

        Args:
            config: Brand configuration
            competitor_name: Name of competitor to update
            category: New category (if provided)
            website: New website (if provided)
            notes: New notes (if provided)

        Returns:
            dict: Updated configuration

        Raises:
            ValueError: If competitor not found or category is invalid
        """
        expected_competitors = config.get('competitors', {}).get('expected', [])

        found = False
        for comp in expected_competitors:
            if comp['name'].lower() == competitor_name.lower():
                found = True
                if category is not None:
                    if category not in self.COMPETITOR_CATEGORIES:
                        raise ValueError(
                            f"Invalid category: {category}. "
                            f"Must be one of: {', '.join(self.COMPETITOR_CATEGORIES)}"
                        )
                    comp['category'] = category
                if website is not None:
                    comp['website'] = website
                if notes is not None:
                    comp['notes'] = notes
                break

        if not found:
            raise ValueError(f"Competitor '{competitor_name}' not found in expected list")

        return config

    def promote_discovered_competitor(
        self,
        config: dict,
        discovered_name: str,
        category: str,
        notes: str = ''
    ) -> dict:
        """
        Promote a discovered competitor to the expected list.
        Removes it from discovered list and adds to expected list.

        Args:
            config: Brand configuration
            discovered_name: Name of discovered competitor to promote
            category: Category to assign (direct, adjacent, aspirational)
            notes: Optional notes about this competitor

        Returns:
            dict: Updated configuration

        Raises:
            ValueError: If competitor not found in discovered list or category is invalid
        """
        if category not in self.COMPETITOR_CATEGORIES:
            raise ValueError(
                f"Invalid category: {category}. Must be one of: {', '.join(self.COMPETITOR_CATEGORIES)}"
            )

        discovered_competitors = config.get('competitors', {}).get('discovered', [])

        # Find the discovered competitor
        discovered_comp = None
        for comp in discovered_competitors:
            if comp['name'].lower() == discovered_name.lower():
                discovered_comp = comp
                break

        if not discovered_comp:
            raise ValueError(f"Competitor '{discovered_name}' not found in discovered list")

        # Add to expected list
        new_expected = {
            'name': discovered_comp['name'],
            'website': '',
            'category': category,
            'added_date': datetime.utcnow().strftime('%Y-%m-%d'),
            'notes': notes or f"Promoted from discovered competitors (first seen {discovered_comp.get('first_seen', 'unknown')})"
        }

        if 'expected' not in config['competitors']:
            config['competitors']['expected'] = []

        config['competitors']['expected'].append(new_expected)

        # Mark as promoted in discovered list (keep for historical record)
        discovered_comp['promoted_to_expected'] = True
        discovered_comp['promoted_date'] = datetime.utcnow().strftime('%Y-%m-%d')

        return config

    def dismiss_discovered_competitor(self, config: dict, discovered_name: str) -> dict:
        """
        Remove a discovered competitor from the list (user doesn't want to track it).

        Args:
            config: Brand configuration
            discovered_name: Name of discovered competitor to dismiss

        Returns:
            dict: Updated configuration
        """
        discovered_competitors = config.get('competitors', {}).get('discovered', [])
        config['competitors']['discovered'] = [
            comp for comp in discovered_competitors
            if comp['name'].lower() != discovered_name.lower()
        ]

        return config

    def update_discovered_competitors(
        self,
        config: dict,
        unlisted_brands: List[dict]
    ) -> dict:
        """
        Update discovered competitors list from tracker analysis.
        Merges new discoveries with existing, updating mention counts.

        Args:
            config: Brand configuration
            unlisted_brands: List of discovered brands from CompetitorAnalyzer
                             Format: [{'name': '', 'mention_count': 0, 'mention_rate': 0.0}, ...]

        Returns:
            dict: Updated configuration
        """
        if 'competitors' not in config:
            config['competitors'] = {'expected': [], 'discovered': []}
        if 'discovered' not in config['competitors']:
            config['competitors']['discovered'] = []

        discovered_competitors = config['competitors']['discovered']

        for brand in unlisted_brands:
            name = brand.get('name', '')
            mention_count = brand.get('mention_count', 0)
            mention_rate = brand.get('mention_rate', 0.0)

            # Determine status based on mention count
            status = 'emerging_threat' if mention_count >= 5 else 'occasional_mention'

            # Check if this competitor already exists in discovered list
            existing = None
            for comp in discovered_competitors:
                if comp['name'].lower() == name.lower():
                    existing = comp
                    break

            if existing:
                # Update existing entry
                existing['mention_count'] = mention_count
                existing['mention_rate'] = mention_rate
                existing['status'] = status
                existing['last_updated'] = datetime.utcnow().strftime('%Y-%m-%d')
            else:
                # Add new discovered competitor
                discovered_competitors.append({
                    'name': name,
                    'first_seen': datetime.utcnow().strftime('%Y-%m-%d'),
                    'mention_count': mention_count,
                    'mention_rate': mention_rate,
                    'status': status,
                    'promoted_to_expected': False,
                    'last_updated': datetime.utcnow().strftime('%Y-%m-%d')
                })

        return config

    def create_default_config(
        self,
        brand_name: str,
        website: str = '',
        description: str = '',
        aliases: List[str] = None
    ) -> dict:
        """
        Create a new default brand configuration with v2.0 schema.

        Args:
            brand_name: Name of the brand
            website: Brand website URL
            description: Brand description
            aliases: List of brand aliases/alternative names

        Returns:
            dict: New brand configuration
        """
        return {
            'brand': {
                'name': brand_name,
                'aliases': aliases or [],
                'description': description,
                'website': website,
                'business_goals': {
                    'revenue_targets': '',
                    'market_positioning': '',
                    'target_metrics': [],
                    'freeform_notes': ''
                }
            },
            'competitors': {
                'expected': [],
                'discovered': []
            },
            'metadata': {
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'last_modified': datetime.utcnow().isoformat() + 'Z',
                'schema_version': self.SCHEMA_VERSION
            },
            'legacy_settings': {}
        }
