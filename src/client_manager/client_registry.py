"""
Client registry manager - tracks all clients and their files.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class ClientRegistry:
    """Manages the registry of all clients."""

    def __init__(self, registry_path: str = 'data/clients.json'):
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize registry if it doesn't exist
        if not self.registry_path.exists():
            self._save_registry({'clients': [], 'last_updated': datetime.utcnow().isoformat()})

    def _load_registry(self) -> Dict:
        """Load the registry from disk."""
        try:
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {'clients': [], 'last_updated': datetime.utcnow().isoformat()}

    def _save_registry(self, registry: Dict):
        """Save the registry to disk."""
        registry['last_updated'] = datetime.utcnow().isoformat()
        with open(self.registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

    def add_client(self, client_name: str, client_slug: str, files: Dict[str, str]):
        """
        Add a client to the registry.

        Args:
            client_name: Display name of the client
            client_slug: URL-safe slug (e.g., 'natasha_denona')
            files: Dict of file paths (keywords, personas, brand_config)
        """
        registry = self._load_registry()

        # Check if client already exists
        for client in registry['clients']:
            if client['slug'] == client_slug:
                # Update existing client
                client['name'] = client_name
                client['files'] = files
                client['updated_at'] = datetime.utcnow().isoformat()
                self._save_registry(registry)
                return

        # Add new client
        registry['clients'].append({
            'name': client_name,
            'slug': client_slug,
            'files': files,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        })

        self._save_registry(registry)

    def get_all_clients(self) -> List[Dict]:
        """Get all registered clients."""
        registry = self._load_registry()
        return registry.get('clients', [])

    def get_client(self, client_slug: str) -> Optional[Dict]:
        """Get a specific client by slug."""
        registry = self._load_registry()
        for client in registry['clients']:
            if client['slug'] == client_slug:
                return client
        return None

    def remove_client(self, client_slug: str):
        """Remove a client from the registry and clean up prompt drafts."""
        # Get client name before removing (needed for draft cleanup)
        client_data = self.get_client(client_slug)
        client_name = client_data.get('name', '') if client_data else ''

        # Remove from registry
        registry = self._load_registry()
        registry['clients'] = [c for c in registry['clients'] if c['slug'] != client_slug]
        self._save_registry(registry)

        # Clean up prompt drafts for this client
        if client_name:
            self._cleanup_prompt_drafts(client_name)

    def _cleanup_prompt_drafts(self, client_name: str):
        """Delete all prompt draft files belonging to a client."""
        draft_dir = Path('data/prompt_generation/drafts')
        if not draft_dir.exists():
            return

        deleted = 0
        for draft_file in draft_dir.glob('batch_*_prompts.json'):
            try:
                with open(draft_file, 'r') as f:
                    draft_data = json.load(f)
                if draft_data.get('client_name') == client_name:
                    draft_file.unlink()
                    deleted += 1
            except Exception:
                pass

        # Also clean up batch metadata
        batches_file = Path('data/prompt_batches.json')
        if batches_file.exists():
            try:
                with open(batches_file, 'r') as f:
                    batches = json.load(f)
                # Remove batches for this client
                batches = {k: v for k, v in batches.items()
                           if v.get('client_name') != client_name}
                with open(batches_file, 'w') as f:
                    json.dump(batches, f, indent=2, default=str)
            except Exception:
                pass

    def check_missing_files(self) -> Dict[str, List[str]]:
        """
        Check which client files are missing from disk.

        Returns:
            Dict mapping client slugs to lists of missing file paths
        """
        missing = {}
        registry = self._load_registry()

        for client in registry['clients']:
            client_missing = []
            for file_type, file_path in client['files'].items():
                if not Path(file_path).exists():
                    client_missing.append(file_path)

            if client_missing:
                missing[client['slug']] = client_missing

        return missing

    def check_uncommitted_files(self) -> Dict[str, List[str]]:
        """
        Check which client files exist but aren't committed to git.

        Returns:
            Dict mapping client slugs to lists of uncommitted file paths
        """
        import subprocess

        uncommitted = {}
        registry = self._load_registry()

        try:
            # Get list of untracked and modified files
            result = subprocess.run(
                ['git', 'status', '--porcelain', 'data/'],
                capture_output=True,
                text=True,
                check=True
            )

            untracked_files = set()
            for line in result.stdout.split('\n'):
                if line.strip():
                    status = line[:2]
                    filepath = line[3:].strip()
                    if status in ['??', ' M', 'M ', 'A ']:  # Untracked or modified
                        untracked_files.add(filepath)

            # Check each client's files
            for client in registry['clients']:
                client_uncommitted = []
                for file_type, file_path in client['files'].items():
                    if file_path in untracked_files or any(file_path in f for f in untracked_files):
                        client_uncommitted.append(file_path)

                if client_uncommitted:
                    uncommitted[client['slug']] = client_uncommitted

        except Exception:
            # If git check fails, return empty dict
            pass

        return uncommitted
