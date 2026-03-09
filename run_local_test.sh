#!/bin/bash
# Quick script to run the dashboard locally with GCS enabled

echo "🚀 Starting AI Visibility Dashboard (Local Test with GCS)"
echo "=========================================================="
echo ""
echo "This will:"
echo "  - Use your GCS credentials from ~/.config/gcloud"
echo "  - Enable GCS storage (USE_GCS_STORAGE=true)"
echo "  - Start on http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop the container"
echo ""

# Run Docker with GCS enabled
docker run -p 8080:8080 \
    -v ~/.config/gcloud:/root/.config/gcloud \
    -e GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json \
    -e USE_GCS_STORAGE=true \
    -e GCS_BUCKET=ai-visibility-reports-dasilva \
    dashboard-test

echo ""
echo "Container stopped."
