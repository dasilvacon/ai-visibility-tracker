#!/bin/bash
# Startup script for Cloud Run - downloads runtime data from GCS
#
# IMPORTANT: Client data files (brand configs, personas, keywords, prompts)
# are baked into the Docker image and synced TO GCS during deploy.
# On startup, we only download files that DON'T already exist locally.
# This prevents stale GCS data from overwriting newer files in the image.
#
# Runtime data (test results, reports, prompt drafts) is always downloaded
# from GCS since it's created at runtime and not in the Docker image.
#
# NOTE: GCS sync runs in BACKGROUND so Streamlit starts immediately
# and passes health checks. Data will be available within seconds.

# Don't exit on error - we'll handle errors manually
set +e

echo "🚀 Starting AI Visibility Dashboard..."

# Write Streamlit secrets from environment variable (Cloud Run)
if [ -n "$STREAMLIT_SECRETS" ]; then
    echo "🔐 Writing Streamlit secrets from environment..."
    mkdir -p .streamlit
    echo "$STREAMLIT_SECRETS" > .streamlit/secrets.toml
    chmod 600 .streamlit/secrets.toml
    echo "✓ Secrets file created"
else
    echo "⚠️  No STREAMLIT_SECRETS env var found (OK for local development)"
fi

# Run GCS sync in BACKGROUND so Streamlit starts immediately
# This prevents startup probe timeouts while still getting data
echo "📥 Starting background GCS sync..."
(
    sleep 2  # Let Streamlit start first
    echo "📥 Syncing client data from Google Cloud Storage (skip existing)..."
python3 -c "
from src.client_manager.gcs_sync import GCSClientSync
from pathlib import Path
import sys

try:
    gcs_sync = GCSClientSync()
    bucket = gcs_sync.bucket
    prefix = 'client-data/'
    local_dir = Path('data')
    downloaded = 0
    skipped = 0

    for blob in bucket.list_blobs(prefix=prefix):
        if blob.name.endswith('/'):
            continue
        relative_path = blob.name[len(prefix):]
        if relative_path == 'clients.json':
            destination = local_dir / 'clients.json'
        else:
            parts = relative_path.split('/')
            if len(parts) == 2:
                destination = local_dir / parts[0] / parts[1]
            else:
                destination = local_dir / relative_path

        # Only download if file doesn't already exist in the image
        if destination.exists():
            skipped += 1
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(destination))
        downloaded += 1
        print(f'  Downloaded {blob.name} (new)')

    print(f'Client data: {downloaded} downloaded, {skipped} already in image')
    sys.exit(0)
except Exception as e:
    print(f'⚠️  GCS client sync failed: {e}')
    print('   Continuing with Docker image data')
    sys.exit(0)
"

if [ $? -eq 0 ]; then
    echo "✓ Client data synced from GCS"
else
    echo "⚠️  GCS client sync had issues, but continuing with startup"
fi

# Download prompt drafts from GCS — only files that don't exist locally
# Approved prompts and main CSV are in the image; drafts are runtime data
echo "📥 Syncing prompt data from Google Cloud Storage (skip existing)..."
python3 -c "
from src.client_manager.gcs_sync import GCSClientSync
from pathlib import Path
import sys

try:
    gcs_sync = GCSClientSync()
    bucket = gcs_sync.bucket
    prefix = 'prompt-data/'
    local_dir = Path('data')
    downloaded = 0
    skipped = 0

    for blob in bucket.list_blobs(prefix=prefix):
        if blob.name.endswith('/'):
            continue
        relative_path = blob.name[len(prefix):]

        if relative_path.startswith('drafts/'):
            destination = local_dir / 'prompt_generation' / relative_path
        elif relative_path.startswith('approved/'):
            destination = local_dir / 'prompt_generation' / relative_path
        else:
            destination = local_dir / relative_path

        # Only download if file doesn't already exist
        if destination.exists():
            skipped += 1
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(destination))
        downloaded += 1
        print(f'  Downloaded {blob.name} (new)')

    print(f'Prompt data: {downloaded} downloaded, {skipped} already in image')
    sys.exit(0)
except Exception as e:
    print(f'⚠️  GCS prompt sync failed: {e}')
    print('   Continuing with Docker image data')
    sys.exit(0)
"

if [ $? -eq 0 ]; then
    echo "✓ Prompt data synced from GCS"
else
    echo "⚠️  GCS prompt sync had issues, but continuing with startup"
fi

# Download test results from GCS — ALWAYS download (runtime data, not in image)
echo "📥 Syncing test results from Google Cloud Storage..."
python3 -c "
from src.client_manager.gcs_sync import GCSClientSync
import sys

try:
    gcs_sync = GCSClientSync()
    success = gcs_sync.download_test_results()
    sys.exit(0 if success else 1)
except Exception as e:
    print(f'⚠️  GCS test results sync failed: {e}')
    print('   Continuing with local data (OK for first run)')
    sys.exit(0)
"

if [ $? -eq 0 ]; then
    echo "✓ Test results synced from GCS"
else
    echo "⚠️  GCS test results sync had issues, but continuing with startup"
fi

# Download reports from GCS — ALWAYS download (runtime data, not in image)
echo "📥 Syncing reports from Google Cloud Storage..."
python3 -c "
from src.client_manager.gcs_sync import GCSClientSync
import sys

try:
    gcs_sync = GCSClientSync()
    success = gcs_sync.download_reports()
    sys.exit(0 if success else 1)
except Exception as e:
    print(f'⚠️  GCS reports sync failed: {e}')
    print('   Continuing with local data (OK for first run)')
    sys.exit(0)
"

if [ $? -eq 0 ]; then
        echo "✓ Reports synced from GCS"
    else
        echo "⚠️  GCS reports sync had issues, but continuing"
    fi
    echo "✓ Background GCS sync complete"
) &

# Start Streamlit immediately (don't wait for GCS sync)
echo "🌐 Starting Streamlit on port 8080..."
exec streamlit run streamlit_app_html.py \
    --server.port=8080 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    --server.enableCORS=false \
    --server.enableXsrfProtection=true
