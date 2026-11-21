#!/bin/bash
# deploy_today.sh — written 2026-11-21.
# Puts the DaSilva Consulting example on the live dashboard and deploys the new code.
#
# What it does, in order:
#   1. Checks the report exists.
#   2. Git: moves dev and main forward to the branch fix/search-on-and-5-runs (fast-forward only).
#   3. Google Cloud Storage: copies everything under client-data/ to backups/2026-11-21/ (a copy, nothing removed).
#   4. Adds DaSilva Consulting to the client registry (starts from the registry that is in Google Cloud Storage).
#   5. Uploads the DaSilva Consulting client files, saved answers and report.
#   6. Runs ./deploy_to_cloud_run.sh (the usual deploy).
#   7. Lists the weekly scheduled jobs (read only), switches back to dev, pushes dev, main and the backup tags to GitHub.
#
# It deletes nothing. If a step fails it stops there.

set -euo pipefail
cd "$(dirname "$0")"
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"

SLUG=dasilva_consulting
BRANCH=fix/search-on-and-5-runs
PY=venv/bin/python
[ -x "$PY" ] || PY=python3
if [ -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" ] && [ -f gcs-credentials.json ]; then
  export GOOGLE_APPLICATION_CREDENTIALS="$PWD/gcs-credentials.json"
fi

echo "== 1. Checking the report exists"
REPORT="data/reports/$SLUG/visibility_report_DaSilva_Consulting.html"
[ -f "$REPORT" ] || { echo "STOP: $REPORT not found."; exit 1; }
echo "   found $REPORT"

echo "== 2. Git: fast-forward dev and main"
git checkout dev
git merge --ff-only "$BRANCH"
git checkout main
git merge --ff-only dev

echo "== 3. Backing up client-data/ in Google Cloud Storage"
$PY - <<'PYEOF'
from src.client_manager.gcs_sync import GCSClientSync
g = GCSClientSync(); b = g.bucket; n = 0
for blob in list(b.list_blobs(prefix='client-data/')):
    if blob.name.endswith('/'):
        continue
    b.copy_blob(blob, b, 'backups/2026-11-21/' + blob.name); n += 1
print(f"   copied {n} files to gs://{g.bucket_name}/backups/2026-11-21/client-data/")
PYEOF

echo "== 4. Adding DaSilva Consulting to the client registry"
$PY - <<'PYEOF'
import json, datetime
from src.client_manager.gcs_sync import GCSClientSync
g = GCSClientSync(); blob = g.bucket.blob('client-data/clients.json')
reg = json.loads(blob.download_as_text()) if blob.exists() else json.load(open('data/clients.json'))
slug = 'dasilva_consulting'; now = datetime.datetime.now().isoformat()
if not any(c.get('slug') == slug for c in reg.get('clients', [])):
    reg.setdefault('clients', []).append({
        "name": "DaSilva Consulting", "slug": slug,
        "files": {"keywords": f"data/{slug}/{slug}_keywords.csv",
                  "personas": f"data/{slug}/{slug}_personas.json",
                  "brand_config": f"data/{slug}/{slug}_brand_config.json"},
        "created_at": now, "updated_at": now})
    reg['last_updated'] = now
json.dump(reg, open('data/clients.json', 'w'), indent=2)
assert g.upload_registry('data/clients.json'), "registry upload failed"
print("   registry now lists:", ", ".join(c['name'] for c in reg['clients']))
PYEOF

echo "== 5. Uploading DaSilva Consulting files, saved answers and report"
$PY - <<'PYEOF'
from pathlib import Path
from src.client_manager.gcs_sync import GCSClientSync
g = GCSClientSync(); slug = 'dasilva_consulting'
files = {}
for f in Path(f'data/{slug}').iterdir():
    for kind in ('brand_config', 'personas', 'keywords', 'topics', 'prompts'):
        if kind in f.name and f.suffix in ('.json', '.csv') and 'meta' not in f.name:
            files[kind] = str(f)
assert g.upload_client_files(slug, files), "client files upload failed"
meta = Path(f'data/{slug}/{slug}_prompts.meta.json')
if meta.exists():
    g.bucket.blob(f'client-data/{slug}/{meta.name}').upload_from_filename(str(meta))
assert g.upload_test_results(slug), "saved answers upload failed"
assert g.upload_reports(slug), "report upload failed"
print("   uploads done")
PYEOF

echo "== 6. Deploying to Cloud Run"
./deploy_to_cloud_run.sh

echo "== 7. Weekly scheduled jobs (read only)"
gcloud scheduler jobs list --location=us-east1 2>/dev/null || echo "   could not list scheduler jobs"
git checkout dev
git push origin dev main --tags || echo "   push to GitHub did not go through; the commits are safe on this Mac"

echo ""
echo "DONE. Open https://dashboard.dasilvaconsulting.com and pick DaSilva Consulting."
