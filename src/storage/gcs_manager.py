"""
DEPRECATED: src/storage/gcs_manager.GCSManager has been consolidated into
src/client_manager/gcs_sync.GCSClientSync — the single source of truth for
all GCS reads and writes.

This shim exists only to keep legacy imports working. New code must use
GCSClientSync directly:

    from client_manager.gcs_sync import GCSClientSync
    gcs = GCSClientSync()
    gcs.get_report_content(client, filename)
    gcs.list_client_reports(client)
    gcs.check_report_exists(client, filename)

Do not add new methods here. Migrate callers and delete this file in a
future cleanup pass.
"""

import warnings
from typing import Optional

# Import using a path that works whether callers use `src.X` or added
# `src/` to sys.path. Fall back to the bare import if the src-prefixed
# form isn't importable (Streamlit adds `src/` to sys.path directly).
try:
    from src.client_manager.gcs_sync import GCSClientSync
except ModuleNotFoundError:  # pragma: no cover
    from client_manager.gcs_sync import GCSClientSync  # type: ignore


class GCSManager(GCSClientSync):
    """Deprecated alias for GCSClientSync. Kept for backward compatibility."""

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        credentials_path: Optional[str] = None,
    ):
        warnings.warn(
            "GCSManager is deprecated; use GCSClientSync from "
            "src.client_manager.gcs_sync instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        # credentials_path is ignored — GCSClientSync uses application default
        # credentials (Cloud Run service account or gcloud auth) exclusively.
        super().__init__(bucket_name=bucket_name or 'ai-visibility-reports-dasilva')
