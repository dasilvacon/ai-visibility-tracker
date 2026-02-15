#!/bin/bash
# Complete workflow: Run visibility test + Upload to Google Cloud Storage

CLIENT_NAME="$1"

if [ -z "$CLIENT_NAME" ]; then
    echo "Usage: ./run_and_upload_report.sh \"Client Name\""
    echo ""
    echo "Examples:"
    echo "  ./run_and_upload_report.sh \"Natasha Denona\""
    echo "  ./run_and_upload_report.sh \"Client 2\""
    exit 1
fi

echo "🚀 Complete Report Workflow for: $CLIENT_NAME"
echo "================================================"
echo ""

# Convert client name to slug for file names
CLIENT_SLUG=$(echo "$CLIENT_NAME" | tr ' ' '_')

# Check if brand config exists
BRAND_CONFIG="data/${CLIENT_SLUG}_brand_config.json"
if [ ! -f "$BRAND_CONFIG" ]; then
    echo "❌ Error: Brand config not found: $BRAND_CONFIG"
    echo ""
    echo "Please create a brand config file first."
    exit 1
fi

# Check if prompts exist
if [ ! -f "data/generated_prompts.csv" ]; then
    echo "❌ Error: No prompts found in data/generated_prompts.csv"
    echo ""
    echo "Please generate prompts first using the Prompt Generator."
    exit 1
fi

# Activate virtual environment
cd "$(dirname "$0")"
source venv/bin/activate

echo "📊 Step 1: Running Visibility Tests"
echo "================================================"
echo ""

# Create temporary prompts file for this client
TEMP_PROMPTS="/tmp/${CLIENT_SLUG}_prompts.csv"

# Filter prompts for this client
head -1 data/generated_prompts.csv > "$TEMP_PROMPTS"
grep ",$CLIENT_NAME," data/generated_prompts.csv >> "$TEMP_PROMPTS" 2>/dev/null || true

PROMPT_COUNT=$(tail -n +2 "$TEMP_PROMPTS" | wc -l | tr -d ' ')

if [ "$PROMPT_COUNT" -eq 0 ]; then
    echo "❌ No prompts found for client: $CLIENT_NAME"
    echo ""
    echo "Make sure the client name in generated_prompts.csv matches exactly."
    rm -f "$TEMP_PROMPTS"
    exit 1
fi

echo "✓ Found $PROMPT_COUNT prompts for $CLIENT_NAME"
echo ""

# Run the visibility tests
python main.py \
  --prompts "$TEMP_PROMPTS" \
  --analyze \
  --brand-config "$BRAND_CONFIG"

TEST_RESULT=$?

# Clean up temp file
rm -f "$TEMP_PROMPTS"

if [ $TEST_RESULT -ne 0 ]; then
    echo ""
    echo "❌ Visibility tests failed. Not uploading to cloud."
    exit 1
fi

echo ""
echo "✅ Visibility Tests Complete!"
echo ""

# Check if GCS credentials exist
if [ ! -f "gcs-credentials.json" ]; then
    echo "⚠️  GCS credentials not found. Skipping cloud upload."
    echo ""
    echo "To enable cloud upload, follow the setup guide in GOOGLE_CLOUD_SETUP.md"
    echo ""
    echo "Reports are available locally in data/reports/"
    exit 0
fi

echo "📤 Step 2: Uploading Reports to Google Cloud Storage"
echo "================================================"
echo ""

# Upload to GCS
python upload_reports_to_gcs.py --client "$CLIENT_NAME"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS! Complete Workflow Finished"
    echo "================================================"
    echo ""
    echo "📊 Reports generated and uploaded for: $CLIENT_NAME"
    echo ""
    echo "Next steps:"
    echo "  1. Go to Streamlit Cloud app settings"
    echo "  2. Click 'Reboot app' to clear cache"
    echo "  3. Client can now view updated reports"
    echo ""
else
    echo ""
    echo "⚠️  Upload to cloud failed, but reports are available locally:"
    echo "   data/reports/visibility_report_${CLIENT_SLUG}.html"
    echo "   data/reports/executive_summary_${CLIENT_SLUG}.pdf"
    echo ""
fi
