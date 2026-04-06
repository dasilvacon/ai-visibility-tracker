#!/bin/bash

# AI Visibility Dashboard - Google Cloud Run Deployment Script
# This script deploys your Streamlit dashboard to Google Cloud Run

set -e  # Exit on error

# Set environment for gcloud
export PATH=/opt/homebrew/share/google-cloud-sdk/bin:$PATH
export CLOUDSDK_PYTHON=/opt/homebrew/bin/python3.13

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   AI Visibility Dashboard - Cloud Run Deployment      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Load configuration from setup if available
if [ -f ".env.deployment" ]; then
    echo -e "${GREEN}✓ Loading configuration from .env.deployment${NC}"
    source .env.deployment
else
    echo -e "${YELLOW}⚠ No .env.deployment found. Run ./setup_cloud_run.sh first${NC}"
fi

# Configuration
PROJECT_ID="${PROJECT_ID:-${GCP_PROJECT_ID:-your-project-id}}"
SERVICE_NAME="${SERVICE_NAME:-ai-visibility-dashboard}"
REGION="${REGION:-${GCP_REGION:-us-east1}}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}✗ gcloud CLI not found${NC}"
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo -e "${GREEN}✓ gcloud CLI found${NC}"

# Check if project ID is set
if [ "$PROJECT_ID" == "your-project-id" ]; then
    echo -e "${YELLOW}⚠ Project ID not set${NC}"
    echo ""
    echo "Please set your Google Cloud Project ID:"
    read -p "Enter Project ID: " PROJECT_ID

    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}✗ Project ID required${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  Project ID: ${PROJECT_ID}"
echo "  Service Name: ${SERVICE_NAME}"
echo "  Region: ${REGION}"
echo "  Image: ${IMAGE_NAME}"
echo ""

# Set project
echo -e "${BLUE}→ Setting active project...${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "${BLUE}→ Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable storage-api.googleapis.com
echo -e "${GREEN}✓ APIs enabled${NC}"

# Sync client data to GCS BEFORE building the image
# This ensures GCS (source of truth) always has the latest files
echo ""
echo -e "${BLUE}→ Syncing client data to GCS...${NC}"
echo "  This ensures the live app uses the latest client files"
python3 -c "
import os, sys
os.environ.setdefault('GOOGLE_CLOUD_PROJECT', '${PROJECT_ID}')
sys.path.insert(0, '.')
from src.client_manager.gcs_sync import GCSClientSync
from pathlib import Path
try:
    gcs = GCSClientSync()
    # Find all client folders and upload their files
    data_dir = Path('data')
    uploaded = 0
    for client_dir in sorted(data_dir.iterdir()):
        if not client_dir.is_dir() or client_dir.name in ('results', 'reports', 'prompt_generation', 'temp'):
            continue
        files = {}
        for f in client_dir.iterdir():
            if f.suffix in ('.json', '.csv') and not f.name.startswith('.'):
                file_type = f.stem.split('_')[-1]  # brand_config, personas, keywords, prompts
                if 'brand_config' in f.name: file_type = 'brand_config'
                elif 'personas' in f.name: file_type = 'personas'
                elif 'keywords' in f.name: file_type = 'keywords'
                elif 'prompts' in f.name: file_type = 'prompts'
                files[file_type] = str(f)
        if files:
            gcs.upload_client_files(client_dir.name, files)
            uploaded += len(files)
    # Also upload registry if it exists
    if (data_dir / 'clients.json').exists():
        gcs.upload_registry(str(data_dir / 'clients.json'))
    print(f'Synced {uploaded} client files to GCS')
except Exception as e:
    print(f'Warning: GCS sync failed: {e}')
    print('Continuing with deploy anyway...')
" 2>&1 | while read line; do echo "  $line"; done
echo -e "${GREEN}✓ Client data synced to GCS${NC}"

# Build container image
echo ""
echo -e "${BLUE}→ Building container image...${NC}"
echo "  This may take 3-5 minutes..."
gcloud builds submit --tag ${IMAGE_NAME}
echo -e "${GREEN}✓ Image built successfully${NC}"

# Check if secrets are configured (non-interactive - assumes secrets exist)
echo ""
echo -e "${BLUE}→ Checking secrets configuration...${NC}"
if gcloud secrets describe streamlit-secrets &>/dev/null; then
    echo -e "${GREEN}✓ Secret 'streamlit-secrets' exists${NC}"
else
    echo -e "${YELLOW}→ Creating secret from .streamlit/secrets.toml...${NC}"
    if [ -f ".streamlit/secrets.toml" ]; then
        gcloud secrets create streamlit-secrets --data-file=.streamlit/secrets.toml 2>/dev/null || \
        gcloud secrets versions add streamlit-secrets --data-file=.streamlit/secrets.toml
        echo -e "${GREEN}✓ Secret created${NC}"
    else
        echo -e "${RED}✗ .streamlit/secrets.toml not found${NC}"
        echo "Please create this file with your authentication credentials"
        exit 1
    fi
fi

# Deploy to Cloud Run
echo ""
echo -e "${BLUE}→ Deploying to Cloud Run...${NC}"
echo "  Data persistence: Google Cloud Storage (GCS)"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --cpu-boost \
    --timeout 3600 \
    --min-instances 1 \
    --max-instances 10 \
    --set-secrets="/app/.streamlit/secrets.toml=streamlit-secrets:latest" \
    --port 8080

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Deployment Successful! 🎉                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo -e "${GREEN}Your dashboard is now live at:${NC}"
echo -e "${BLUE}${SERVICE_URL}${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Visit the URL above to access your dashboard"
echo "  2. All data automatically syncs to Google Cloud Storage"
echo "  3. Share the URL with your clients"
echo ""
echo -e "${YELLOW}Custom domain (optional):${NC}"
echo "  • Map a custom domain in Cloud Run console"
echo "  • Example: dashboard.dasilvaconsulting.com"
echo ""
echo -e "${YELLOW}Estimated monthly cost:${NC}"
echo "  • Cloud Run: ~\$5-10/month (based on usage)"
echo "  • Cloud Storage: ~\$1-2/month"
echo "  • Total: ~\$6-12/month"
echo ""
