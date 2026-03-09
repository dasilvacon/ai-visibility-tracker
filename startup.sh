#!/bin/bash
# Startup script for Cloud Run - downloads client data from GCS

# Don't exit on error - we'll handle errors manually
set +e

echo "🚀 Starting AI Visibility Dashboard..."

# Download client data from Google Cloud Storage
echo "📥 Syncing client data from Google Cloud Storage..."
python3 -c "
from src.client_manager.gcs_sync import GCSClientSync
import sys

try:
    gcs_sync = GCSClientSync()
    success = gcs_sync.download_all_client_data()
    sys.exit(0 if success else 1)
except Exception as e:
    print(f'⚠️  GCS client sync failed: {e}')
    print('   Continuing with local data (OK for first run)')
    sys.exit(0)  # Don't fail startup if GCS sync fails
"

if [ $? -eq 0 ]; then
    echo "✓ Client data synced from GCS"
else
    echo "⚠️  GCS client sync had issues, but continuing with startup"
fi

# Download prompt data from Google Cloud Storage
echo "📥 Syncing prompt data from Google Cloud Storage..."
python3 -c "
from src.client_manager.gcs_sync import GCSClientSync
import sys

try:
    gcs_sync = GCSClientSync()
    success = gcs_sync.download_prompt_data()
    sys.exit(0 if success else 1)
except Exception as e:
    print(f'⚠️  GCS prompt sync failed: {e}')
    print('   Continuing with local data (OK for first run)')
    sys.exit(0)  # Don't fail startup if GCS sync fails
"

if [ $? -eq 0 ]; then
    echo "✓ Prompt data synced from GCS"
else
    echo "⚠️  GCS prompt sync had issues, but continuing with startup"
fi

# Download test results from Google Cloud Storage
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
    sys.exit(0)  # Don't fail startup if GCS sync fails
"

if [ $? -eq 0 ]; then
    echo "✓ Test results synced from GCS"
else
    echo "⚠️  GCS test results sync had issues, but continuing with startup"
fi

# Download reports from Google Cloud Storage
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
    sys.exit(0)  # Don't fail startup if GCS sync fails
"

if [ $? -eq 0 ]; then
    echo "✓ Reports synced from GCS"
else
    echo "⚠️  GCS reports sync had issues, but continuing with startup"
fi

# Start Streamlit
echo "🌐 Starting Streamlit on port 8080..."
exec streamlit run streamlit_app_html.py \
    --server.port=8080 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    --server.enableCORS=false \
    --server.enableXsrfProtection=true
