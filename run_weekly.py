#!/usr/bin/env python3
"""
Cloud Run Job entrypoint for weekly automated AI visibility tests.

Triggered once per week per client by Cloud Scheduler → Cloud Run Job.

Flow:
  1. Read CLIENT_SLUG from env
  2. Load API keys from mounted secrets.toml → export as env vars
  3. Download latest client files from GCS (brand_config, personas, keywords, prompts)
  4. Invoke main.py as subprocess (--prompts … --brand-config … --analyze)
  5. Upload results + reports to GCS:
       - test-results/{slug}/                          (latest — dashboard reads here)
       - test-results/{slug}/weekly/{YYYY-WW}/         (immutable weekly snapshot)
       - reports/{slug}/                               (latest)
       - reports/{slug}/weekly/{YYYY-WW}/              (immutable weekly snapshot)
  6. Exit with main.py's exit code

Env vars:
  CLIENT_SLUG              required — e.g. "ontario_caregiver_organization"
  GOOGLE_CLOUD_PROJECT     auto-set by Cloud Run
  STREAMLIT_SECRETS_PATH   optional — override default /app/.streamlit/secrets.toml
"""

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------- config ----------------
PROJECT_ROOT = Path(__file__).parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"
SECRETS_PATH = Path(
    os.environ.get("STREAMLIT_SECRETS_PATH", "/app/.streamlit/secrets.toml")
)


def log(msg: str) -> None:
    """Print with a UTC timestamp prefix (visible in Cloud Run Job logs)."""
    print(f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {msg}", flush=True)


# ---------------- secrets ----------------
def load_secrets_into_env() -> None:
    """Parse mounted secrets.toml and export API keys as env vars for main.py."""
    if not SECRETS_PATH.exists():
        log(f"No secrets file at {SECRETS_PATH} — relying on existing env vars")
        return

    try:
        import tomllib  # Python 3.11+
    except ImportError:
        import tomli as tomllib  # type: ignore

    with SECRETS_PATH.open("rb") as f:
        secrets = tomllib.load(f)

    api_keys = secrets.get("api_keys", {}) or {}

    mapping = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "perplexity": "PERPLEXITY_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "serpapi": "SERPAPI_API_KEY",
    }
    exported = []
    for key, env_var in mapping.items():
        val = api_keys.get(key)
        if val:
            os.environ[env_var] = val
            exported.append(env_var)

    azure_key = api_keys.get("copilot") or api_keys.get("azure_openai")
    if azure_key:
        os.environ["AZURE_OPENAI_API_KEY"] = azure_key
        exported.append("AZURE_OPENAI_API_KEY")
    azure_endpoint = api_keys.get("azure_openai_endpoint")
    if azure_endpoint:
        os.environ["AZURE_OPENAI_ENDPOINT"] = azure_endpoint
        exported.append("AZURE_OPENAI_ENDPOINT")

    log(f"Exported {len(exported)} API keys to env: {', '.join(exported)}")


# ---------------- GCS data download ----------------
def download_client_data(slug: str) -> dict:
    """Pull latest client files from GCS. Returns paths to brand_config + prompts."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.client_manager.gcs_sync import GCSClientSync

    gcs = GCSClientSync()

    client_dir = DATA_DIR / slug
    client_dir.mkdir(parents=True, exist_ok=True)

    # Download everything under client-data/{slug}/ into data/{slug}/
    prefix = f"client-data/{slug}/"
    downloaded = 0
    for blob in gcs.bucket.list_blobs(prefix=prefix):
        if blob.name.endswith("/"):
            continue
        filename = blob.name[len(prefix):]
        if "/" in filename:  # skip nested folders (shouldn't exist, but safe)
            continue
        dest = client_dir / filename
        blob.download_to_filename(str(dest))
        downloaded += 1
    log(f"Downloaded {downloaded} client files from gs://.../{prefix}")

    # Also pull the registry so HistoricalTracker / other lookups see the client
    registry_blob = gcs.bucket.blob("client-data/clients.json")
    if registry_blob.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        registry_blob.download_to_filename(str(DATA_DIR / "clients.json"))

    # Canonical file paths
    brand_config = client_dir / f"{slug}_brand_config.json"
    prompts = client_dir / f"{slug}_prompts.csv"

    if not brand_config.exists():
        raise FileNotFoundError(f"Missing brand_config: {brand_config}")
    if not prompts.exists():
        raise FileNotFoundError(f"Missing prompts: {prompts}")

    return {"brand_config": str(brand_config), "prompts": str(prompts)}


# ---------------- main.py invocation ----------------
def run_tests(brand_config: str, prompts: str) -> int:
    """Invoke main.py as a subprocess. Returns its exit code."""
    cmd = [
        sys.executable,
        "main.py",
        "--brand-config", brand_config,
        "--prompts", prompts,
        "--analyze",
    ]
    log(f"→ Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    log(f"→ main.py exited with code {result.returncode}")
    return result.returncode


# ---------------- upload + snapshot ----------------
def iso_week_tag(now: datetime | None = None) -> str:
    """Return ISO-week tag like '2026-W16'."""
    now = now or datetime.now(timezone.utc)
    year, week, _ = now.isocalendar()
    return f"{year}-W{week:02d}"


def upload_results(slug: str, week_tag: str) -> None:
    """
    Upload to GCS in two places:
      - test-results/{slug}/ and reports/{slug}/           (latest, dashboard reads)
      - test-results/{slug}/weekly/{YYYY-WW}/ and reports/{slug}/weekly/{YYYY-WW}/
        (immutable weekly snapshots for trend analysis)
    """
    from src.client_manager.gcs_sync import GCSClientSync

    gcs = GCSClientSync()

    # 1. Upload to "latest" paths — existing behavior, keeps dashboard working
    try:
        gcs.upload_test_results(slug)
    except Exception as e:
        log(f"⚠️  upload_test_results failed: {e}")
    try:
        gcs.upload_reports(slug)
    except Exception as e:
        log(f"⚠️  upload_reports failed: {e}")

    # 2. Snapshot to immutable weekly paths
    results_dir = DATA_DIR / "results" / slug
    reports_dir = DATA_DIR / "reports" / slug
    snapshots = [
        (results_dir, f"test-results/{slug}/weekly/{week_tag}/"),
        (reports_dir, f"reports/{slug}/weekly/{week_tag}/"),
    ]
    count = 0
    for local_dir, gcs_prefix in snapshots:
        if not local_dir.exists():
            continue
        for f in local_dir.rglob("*"):
            if not f.is_file():
                continue
            rel = f.relative_to(local_dir)
            blob = gcs.bucket.blob(f"{gcs_prefix}{rel.as_posix()}")
            blob.upload_from_filename(str(f))
            count += 1
    log(f"Snapshotted {count} files to weekly/{week_tag}/")


# ---------------- entrypoint ----------------
def main() -> int:
    slug = os.environ.get("CLIENT_SLUG", "").strip()
    if not slug:
        log("✗ CLIENT_SLUG env var required")
        return 1

    week_tag = iso_week_tag()
    log(f"=== Weekly run: client={slug} week={week_tag} ===")

    load_secrets_into_env()

    try:
        paths = download_client_data(slug)
    except Exception as e:
        log(f"✗ Failed to download client data: {e}")
        return 1

    rc = run_tests(paths["brand_config"], paths["prompts"])

    # Upload even on partial success — rc=2 means "incomplete, resume later"
    # rc=0 means full success. rc=1 means hard failure (still upload what we have).
    try:
        upload_results(slug, week_tag)
    except Exception as e:
        log(f"⚠️  Upload step failed: {e}")
        # Don't mask main.py's exit code with an upload error

    log(f"=== Weekly run complete: client={slug} exit={rc} ===")
    return rc


if __name__ == "__main__":
    sys.exit(main())
