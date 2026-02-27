#!/bin/bash
# Cloud Run Setup Script for AI Visibility Tracker
# This script guides you through deploying to Google Cloud Run

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Google Cloud Run Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Set environment variables
export PATH=/opt/homebrew/share/google-cloud-sdk/bin:$PATH
export CLOUDSDK_PYTHON=/opt/homebrew/bin/python3.13

# Step 1: Login
echo -e "${YELLOW}Step 1: Login to Google Cloud${NC}"
echo "This will open your browser for authentication..."
echo ""
gcloud auth login

echo -e "${GREEN}✓ Authentication successful${NC}"
echo ""

# Step 2: Create or select project
echo -e "${YELLOW}Step 2: Set up Google Cloud Project${NC}"
echo "Enter a project name (e.g., ai-visibility-tracker):"
read -r PROJECT_NAME

# Generate unique project ID
PROJECT_ID="${PROJECT_NAME}-$(date +%s)"
echo "Creating project with ID: ${PROJECT_ID}"

gcloud projects create "${PROJECT_ID}" --name="${PROJECT_NAME}" || {
    echo "Project creation failed. You may need to select an existing project."
    echo "List your projects:"
    gcloud projects list
    echo ""
    echo "Enter an existing project ID to use:"
    read -r PROJECT_ID
}

gcloud config set project "${PROJECT_ID}"
echo -e "${GREEN}✓ Project set to: ${PROJECT_ID}${NC}"
echo ""

# Step 3: Enable billing
echo -e "${YELLOW}Step 3: Enable Billing${NC}"
echo "You need to enable billing for this project."
echo "Opening billing page in browser..."
open "https://console.cloud.google.com/billing/projects/${PROJECT_ID}"
echo ""
echo "After enabling billing in your browser, press Enter to continue..."
read -r

# Step 4: Enable APIs
echo -e "${YELLOW}Step 4: Enable Required APIs${NC}"
echo "Enabling Cloud Run, Container Registry, and Secret Manager..."
gcloud services enable run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    storage.googleapis.com

echo -e "${GREEN}✓ APIs enabled${NC}"
echo ""

# Step 5: Create secret from .streamlit/secrets.toml
echo -e "${YELLOW}Step 5: Create Cloud Secret${NC}"
if [ -f ".streamlit/secrets.toml" ]; then
    gcloud secrets create streamlit-secrets \
        --data-file=.streamlit/secrets.toml \
        --replication-policy="automatic" || {
        echo "Secret already exists, updating..."
        gcloud secrets versions add streamlit-secrets \
            --data-file=.streamlit/secrets.toml
    }
    echo -e "${GREEN}✓ Secret created${NC}"
else
    echo -e "${YELLOW}Warning: .streamlit/secrets.toml not found${NC}"
    echo "Make sure your secrets file exists before deployment"
fi
echo ""

# Step 6: Get GCS bucket name
echo -e "${YELLOW}Step 6: Verify GCS Bucket${NC}"
echo "Enter your GCS bucket name (from .streamlit/secrets.toml):"
read -r BUCKET_NAME
export GCS_BUCKET_NAME="${BUCKET_NAME}"

echo "Testing GCS access..."
gsutil ls "gs://${BUCKET_NAME}/" > /dev/null 2>&1 && {
    echo -e "${GREEN}✓ GCS bucket accessible${NC}"
} || {
    echo -e "${YELLOW}Warning: Could not access bucket. Make sure it exists.${NC}"
}
echo ""

# Save environment variables
cat > .env.deployment << EOF
PROJECT_ID=${PROJECT_ID}
GCS_BUCKET_NAME=${GCS_BUCKET_NAME}
REGION=us-east1
SERVICE_NAME=ai-visibility-dashboard
EOF

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Configuration saved to .env.deployment"
echo ""
echo "Next step: Deploy to Cloud Run"
echo "Run: ./deploy_to_cloud_run.sh"
echo ""
