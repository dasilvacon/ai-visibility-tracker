"""
Prompt-set versioning.

Stores the active prompt set at a stable path (`data/{slug}/{slug}_prompts.csv`)
alongside a `{slug}_prompts.meta.json` sidecar describing the version.
Every version ever deployed is also archived, read-only, under
`data/prompt-archive/{slug}/{version_id}/`.

See `docs/prompt-versioning.md` for the schema and rationale.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from src.client_manager.gcs_sync import GCSClientSync
except ModuleNotFoundError:  # Streamlit adds src/ to sys.path directly
    from client_manager.gcs_sync import GCSClientSync  # type: ignore


# ---------------------------------------------------------------------------
# Version identifier
# ---------------------------------------------------------------------------

VERSION_RE = re.compile(r'^v(\d+)\.(\d+)-([a-z0-9][a-z0-9-]*)$')
TAG_RE = re.compile(r'^[a-z0-9][a-z0-9-]*$')


@dataclass(frozen=True)
class VersionId:
    """Parsed `v{MAJOR}.{MINOR}-{tag}` identifier."""

    major: int
    minor: int
    tag: str

    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}-{self.tag}"

    @classmethod
    def parse(cls, raw: str) -> 'VersionId':
        m = VERSION_RE.match(raw)
        if not m:
            raise ValueError(
                f"Invalid version id: {raw!r}. "
                f"Expected format: v{{MAJOR}}.{{MINOR}}-{{tag}}, "
                f"e.g. 'v2.0-intent-context'."
            )
        return cls(major=int(m.group(1)), minor=int(m.group(2)), tag=m.group(3))

    @classmethod
    def make(cls, major: int, minor: int, tag: str) -> 'VersionId':
        if major < 0 or minor < 0:
            raise ValueError("major/minor must be non-negative integers")
        if not TAG_RE.match(tag):
            raise ValueError(
                f"Invalid tag {tag!r}. Must be lowercase alphanumeric + "
                f"hyphens, starting with a letter or digit."
            )
        return cls(major=major, minor=minor, tag=tag)


# ---------------------------------------------------------------------------
# Version metadata
# ---------------------------------------------------------------------------

REQUIRED_META_FIELDS = {
    'version',
    'client_slug',
    'generated_at',
    'generated_by',
    'generator_version',
    'source_model',
    'prompt_count',
    'format',
    'personas',
    'categories',
    'predecessor',  # may be null for the very first version
    'content_hash',
}


def validate_meta(meta: Dict) -> None:
    """Raise ValueError if `meta` is missing required fields or malformed."""
    missing = REQUIRED_META_FIELDS - meta.keys()
    if missing:
        raise ValueError(f"meta.json missing required fields: {sorted(missing)}")
    # Parse the version id to validate its shape
    VersionId.parse(meta['version'])
    if not isinstance(meta['prompt_count'], int) or meta['prompt_count'] < 0:
        raise ValueError("prompt_count must be a non-negative integer")
    if not isinstance(meta['personas'], list):
        raise ValueError("personas must be a list")
    if not isinstance(meta['categories'], list):
        raise ValueError("categories must be a list")


def compute_content_hash(csv_content: str | bytes) -> str:
    """Return 'sha256:<hex>' for the given CSV content."""
    if isinstance(csv_content, str):
        csv_content = csv_content.encode('utf-8')
    return 'sha256:' + hashlib.sha256(csv_content).hexdigest()


def utc_now_iso() -> str:
    """Return current UTC time as an ISO-8601 string with Z suffix."""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

@dataclass
class PromptVersionManager:
    """
    Orchestrates active + archive storage for one client's prompt set.

    Local disk layout:
        data/{slug}/{slug}_prompts.csv          # active CSV
        data/{slug}/{slug}_prompts.meta.json    # active meta sidecar
        data/prompt-archive/{slug}/{ver}/prompts.csv
        data/prompt-archive/{slug}/{ver}/meta.json

    GCS layout mirrors local under the same prefixes:
        client-data/{slug}/{slug}_prompts.csv
        client-data/{slug}/{slug}_prompts.meta.json
        prompt-archive/{slug}/{ver}/prompts.csv
        prompt-archive/{slug}/{ver}/meta.json
    """

    client_slug: str
    data_dir: Path = field(default_factory=lambda: Path('data'))
    gcs: Optional[GCSClientSync] = None

    # ----- paths --------------------------------------------------------

    @property
    def active_csv_path(self) -> Path:
        return self.data_dir / self.client_slug / f"{self.client_slug}_prompts.csv"

    @property
    def active_meta_path(self) -> Path:
        return self.data_dir / self.client_slug / f"{self.client_slug}_prompts.meta.json"

    def archive_dir(self, version_id: str) -> Path:
        return self.data_dir / 'prompt-archive' / self.client_slug / version_id

    def archive_csv_path(self, version_id: str) -> Path:
        return self.archive_dir(version_id) / 'prompts.csv'

    def archive_meta_path(self, version_id: str) -> Path:
        return self.archive_dir(version_id) / 'meta.json'

    # ----- read ---------------------------------------------------------

    def get_active_version(self) -> Optional[Dict]:
        """Return the active `meta.json` dict, or None if no meta exists."""
        if not self.active_meta_path.exists():
            return None
        with open(self.active_meta_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_active_version_id(self) -> Optional[str]:
        """Return the active version string, or None if no meta exists."""
        meta = self.get_active_version()
        return meta['version'] if meta else None

    def list_archived_versions(self) -> List[Dict]:
        """Return meta dicts for all archived versions, newest first by generated_at."""
        root = self.data_dir / 'prompt-archive' / self.client_slug
        if not root.exists():
            return []

        versions = []
        for version_dir in root.iterdir():
            if not version_dir.is_dir():
                continue
            meta_path = version_dir / 'meta.json'
            if not meta_path.exists():
                continue
            with open(meta_path, 'r', encoding='utf-8') as f:
                versions.append(json.load(f))
        versions.sort(key=lambda m: m.get('generated_at', ''), reverse=True)
        return versions

    def load_archive_version(self, version_id: str) -> Tuple[str, Dict]:
        """
        Return (csv_content, meta_dict) for `version_id`.

        Raises FileNotFoundError if the version isn't archived locally.
        """
        VersionId.parse(version_id)  # validate format
        csv_path = self.archive_csv_path(version_id)
        meta_path = self.archive_meta_path(version_id)
        if not csv_path.exists() or not meta_path.exists():
            raise FileNotFoundError(
                f"Archived version {version_id!r} not found at {csv_path.parent}"
            )
        csv_content = csv_path.read_text(encoding='utf-8')
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        return csv_content, meta

    # ----- write --------------------------------------------------------

    def write_new_version(
        self,
        csv_content: str,
        meta: Dict,
        *,
        upload_to_gcs: bool = True,
    ) -> Dict:
        """
        Archive + activate a new prompt version.

        Writes to archive first, then overwrites the active path, so that
        if activation fails the archive still contains the new version
        (recoverable) and the live active path still serves the previous
        version (no outage).

        Returns the meta dict with `content_hash` filled in.
        """
        # Fill in content_hash if not provided; this is canonical
        meta = dict(meta)
        meta['content_hash'] = compute_content_hash(csv_content)
        if meta.get('client_slug') is None:
            meta['client_slug'] = self.client_slug
        if meta.get('generated_at') is None:
            meta['generated_at'] = utc_now_iso()
        if meta.get('prompt_count') is None:
            # CSV is prompt_id,... — count data rows (exclude header)
            lines = csv_content.splitlines()
            meta['prompt_count'] = max(len(lines) - 1, 0)
        validate_meta(meta)

        if meta['client_slug'] != self.client_slug:
            raise ValueError(
                f"meta.client_slug {meta['client_slug']!r} does not match "
                f"manager slug {self.client_slug!r}"
            )

        version_id = meta['version']

        # 1. Archive
        archive_dir = self.archive_dir(version_id)
        if archive_dir.exists() and any(archive_dir.iterdir()):
            # Refuse to overwrite an existing archive entry — each archive
            # is immutable. Bump the minor or tag instead.
            raise FileExistsError(
                f"Version {version_id!r} already archived at {archive_dir}. "
                f"Archive entries are immutable; bump the version id."
            )
        archive_dir.mkdir(parents=True, exist_ok=True)
        self.archive_csv_path(version_id).write_text(csv_content, encoding='utf-8')
        with open(self.archive_meta_path(version_id), 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
            f.write('\n')

        # 2. Activate
        self.active_csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.active_csv_path.write_text(csv_content, encoding='utf-8')
        with open(self.active_meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
            f.write('\n')

        # 3. GCS (best-effort; local is source of truth for this call)
        if upload_to_gcs and self.gcs is not None:
            self._upload_version_to_gcs(version_id, csv_content, meta)

        return meta

    def archive_current_as(
        self,
        version_id: str,
        *,
        generated_by: str = 'pre-versioning-migration',
        generator_version: str = '1.0',
        source_model: str = 'legacy',
        format_tag: str = 'legacy',
        notes: Optional[str] = None,
        personas: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        upload_to_gcs: bool = True,
    ) -> Dict:
        """
        Freeze the currently-active CSV as an archive entry labeled
        `version_id` and write a matching active meta.json sidecar.

        Used for the one-time migration from unversioned state to v1.0-baseline.
        Safe to re-run: if the version is already archived and the active
        meta already points to it, returns the existing meta without changes.
        """
        if not self.active_csv_path.exists():
            raise FileNotFoundError(
                f"No active prompts CSV for {self.client_slug} at {self.active_csv_path}"
            )

        # If already migrated, return the existing active meta
        existing = self.get_active_version()
        if existing is not None and existing.get('version') == version_id:
            return existing

        csv_content = self.active_csv_path.read_text(encoding='utf-8')

        # Derive personas / categories from the CSV if caller didn't supply them
        if personas is None or categories is None:
            derived_personas, derived_categories = _scan_csv_personas_and_categories(csv_content)
            personas = personas if personas is not None else derived_personas
            categories = categories if categories is not None else derived_categories

        lines = csv_content.splitlines()
        prompt_count = max(len(lines) - 1, 0)

        meta = {
            'version': version_id,
            'client_slug': self.client_slug,
            'generated_at': utc_now_iso(),
            'generated_by': generated_by,
            'generator_version': generator_version,
            'source_model': source_model,
            'prompt_count': prompt_count,
            'format': format_tag,
            'personas': personas,
            'categories': categories,
            'predecessor': None,
            'content_hash': compute_content_hash(csv_content),
        }
        if notes is not None:
            meta['notes'] = notes

        validate_meta(meta)

        # Archive (idempotent — skip if already present with matching hash)
        archive_csv = self.archive_csv_path(version_id)
        archive_meta = self.archive_meta_path(version_id)
        if archive_csv.exists() and archive_meta.exists():
            existing_hash = compute_content_hash(archive_csv.read_text(encoding='utf-8'))
            if existing_hash != meta['content_hash']:
                raise FileExistsError(
                    f"Archive for {version_id!r} already exists at {archive_csv} "
                    f"with a different content hash. Refusing to overwrite."
                )
        else:
            archive_csv.parent.mkdir(parents=True, exist_ok=True)
            archive_csv.write_text(csv_content, encoding='utf-8')
            with open(archive_meta, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
                f.write('\n')

        # Write active meta sidecar
        with open(self.active_meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
            f.write('\n')

        # GCS
        if upload_to_gcs and self.gcs is not None:
            self._upload_version_to_gcs(version_id, csv_content, meta)

        return meta

    # ----- GCS ----------------------------------------------------------

    def _upload_version_to_gcs(
        self,
        version_id: str,
        csv_content: str,
        meta: Dict,
    ) -> None:
        """Upload active + archive to GCS. Best-effort; logs but does not raise."""
        try:
            bucket = self.gcs.bucket
            slug = self.client_slug

            # Active
            bucket.blob(f"client-data/{slug}/{slug}_prompts.csv").upload_from_string(
                csv_content, content_type='text/csv'
            )
            bucket.blob(f"client-data/{slug}/{slug}_prompts.meta.json").upload_from_string(
                json.dumps(meta, indent=2, ensure_ascii=False),
                content_type='application/json',
            )

            # Archive
            bucket.blob(f"prompt-archive/{slug}/{version_id}/prompts.csv").upload_from_string(
                csv_content, content_type='text/csv'
            )
            bucket.blob(f"prompt-archive/{slug}/{version_id}/meta.json").upload_from_string(
                json.dumps(meta, indent=2, ensure_ascii=False),
                content_type='application/json',
            )
            print(f"✓ Uploaded version {version_id} to GCS for {slug}")

        except Exception as exc:  # pragma: no cover — network errors
            print(f"⚠️ GCS upload failed for {self.client_slug} {version_id}: {exc}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scan_csv_personas_and_categories(csv_content: str) -> Tuple[List[str], List[str]]:
    """Return (sorted unique personas, sorted unique categories) from a prompts CSV."""
    import csv as _csv
    from io import StringIO

    reader = _csv.DictReader(StringIO(csv_content))
    personas: set = set()
    categories: set = set()
    for row in reader:
        persona = (row.get('persona') or '').strip()
        category = (row.get('category') or '').strip()
        if persona:
            personas.add(persona)
        if category:
            categories.add(category)
    return sorted(personas), sorted(categories)
