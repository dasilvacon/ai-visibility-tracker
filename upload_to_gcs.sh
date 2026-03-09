#!/bin/bash
# Manual GCS upload script using gsutil

echo "☁️  Uploading Natasha Denona Reports to GCS"
echo "==========================================="
echo ""

BUCKET="gs://ai-visibility-reports-dasilva"
BRAND_FOLDER="Natasha_Denona"
LOCAL_PATH="data/reports/*Natasha_Denona*"

# Check if gsutil is available
if ! command -v gsutil &> /dev/null; then
    echo "❌ Error: gsutil not found"
    echo ""
    echo "Install Google Cloud SDK:"
    echo "  https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check authentication
if ! gcloud auth list 2>&1 | grep -q "ACTIVE"; then
    echo "❌ Not authenticated with Google Cloud"
    echo ""
    echo "Please authenticate first:"
    echo "  gcloud auth login"
    echo "  gcloud config set project gen-lang-client-0243073678"
    echo ""
    exit 1
fi

echo "✓ Authenticated with Google Cloud"
echo ""

# List files to upload
echo "Files to upload:"
ls -lh $LOCAL_PATH | awk '{print "  " $9 " (" $5 ")"}'
echo ""

read -p "Continue with upload? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Upload cancelled"
    exit 0
fi

echo ""
echo "Uploading..."
echo ""

# Upload all files
gsutil -m cp $LOCAL_PATH "$BUCKET/$BRAND_FOLDER/"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Upload complete!"
    echo ""
    echo "Reports available at:"
    echo "  https://ai-visibility-dashboard-96323652503.us-east1.run.app"
    echo ""
    echo "Login with:"
    echo "  Username: natasha_denona"
    echo "  Password: natasha123"
else
    echo ""
    echo "❌ Upload failed"
    exit 1
fi
