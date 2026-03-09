#!/bin/bash
# Deploy Streamlit secrets to Cloud Run
# This script updates the secrets for the AI Visibility Dashboard on Cloud Run

echo "🔐 Deploying Streamlit Secrets to Cloud Run"
echo "============================================"

PROJECT_ID="gen-lang-client-0243073678"
SERVICE_NAME="ai-visibility-dashboard"
REGION="us-east1"

# Check if .streamlit/secrets.toml exists
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo "❌ Error: .streamlit/secrets.toml not found"
    exit 1
fi

echo "✓ Found .streamlit/secrets.toml"
echo ""

# Create or update the secret
echo "📤 Updating secret in Google Cloud Secret Manager..."

# Check if secret exists
if gcloud secrets describe streamlit-secrets --project=$PROJECT_ID &>/dev/null; then
    echo "Secret exists, creating new version..."
    gcloud secrets versions add streamlit-secrets \
        --data-file=".streamlit/secrets.toml" \
        --project=$PROJECT_ID
else
    echo "Creating new secret..."
    gcloud secrets create streamlit-secrets \
        --data-file=".streamlit/secrets.toml" \
        --project=$PROJECT_ID
fi

if [ $? -eq 0 ]; then
    echo "✓ Secret updated successfully"
else
    echo "❌ Failed to update secret"
    exit 1
fi

echo ""
echo "🚀 Updating Cloud Run service to use new secret..."

# Update the Cloud Run service to mount the secret
gcloud run services update $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --update-secrets=/app/.streamlit/secrets.toml=streamlit-secrets:latest

if [ $? -eq 0 ]; then
    echo "✓ Cloud Run service updated successfully"
    echo ""
    echo "🎉 Deployment complete!"
    echo ""
    echo "The dashboard should now be accessible at:"
    echo "https://ai-visibility-dashboard-96323652503.us-east1.run.app"
    echo ""
    echo "Login credentials:"
    echo "  Username: natasha_denona"
    echo "  Password: natasha123"
else
    echo "❌ Failed to update Cloud Run service"
    exit 1
fi
