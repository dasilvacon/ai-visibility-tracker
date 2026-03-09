#!/bin/bash
# Simple upload script using gcloud storage

echo "📤 Uploading Natasha Denona report to GCS..."

# Upload just the HTML report
/opt/homebrew/share/google-cloud-sdk/bin/gcloud storage cp data/reports/visibility_report_Natasha_Denona.html \
  gs://ai-visibility-reports-dasilva/Natasha_Denona/visibility_report_Natasha_Denona.html \
  --content-type=text/html

if [ $? -eq 0 ]; then
  echo "✅ Upload complete!"
  echo ""
  echo "View your redesigned report at:"
  echo "https://dashboard.dasilvaconsulting.com"
  echo ""
  echo "Login: natasha_denona / natasha123"
else
  echo "❌ Upload failed"
  exit 1
fi
