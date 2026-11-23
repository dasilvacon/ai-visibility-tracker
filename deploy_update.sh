#!/bin/bash
# deploy_update.sh — written 2026-11-23.
# Ships the report-headline change: moves main forward to dev, uploads the regenerated
# DaSilva Consulting report, runs the usual deploy, then pushes to GitHub. Deletes nothing.
set -euo pipefail
cd "$(dirname "$0")"
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
PY=venv/bin/python; [ -x "$PY" ] || PY=python3
if [ -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" ] && [ -f gcs-credentials.json ]; then
  export GOOGLE_APPLICATION_CREDENTIALS="$PWD/gcs-credentials.json"
fi
echo "== 1. Git: fast-forward main to dev"
git checkout main
git merge --ff-only dev
echo "== 2. Uploading the regenerated DaSilva Consulting report"
$PY - <<'PYEOF'
from src.client_manager.gcs_sync import GCSClientSync
assert GCSClientSync().upload_reports('dasilva_consulting'), "report upload failed"
print("   report uploaded")
PYEOF
echo "== 3. Deploying to Cloud Run"
./deploy_to_cloud_run.sh
echo "== 4. Back to dev, push to GitHub"
git checkout dev
git push origin dev main --tags || echo "   push did not go through; commits are safe on this Mac"
echo ""
echo "DONE. Reload https://dashboard.dasilvaconsulting.com and open DaSilva Consulting."
