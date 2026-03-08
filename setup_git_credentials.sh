#!/bin/bash
# Setup Git Credentials for Cloud Run
# This script creates the necessary secrets in Google Secret Manager

set -e

# Set environment for gcloud
export PATH=/opt/homebrew/share/google-cloud-sdk/bin:$PATH
export CLOUDSDK_PYTHON=/opt/homebrew/bin/python3.13

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Setup Git Credentials for Cloud Run            ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

# Load configuration
if [ -f ".env.deployment" ]; then
    source .env.deployment
    PROJECT_ID="${PROJECT_ID:-${GCP_PROJECT_ID}}"
else
    echo -e "${YELLOW}⚠ No .env.deployment found${NC}"
    read -p "Enter your Google Cloud Project ID: " PROJECT_ID
fi

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}✗ Project ID required${NC}"
    exit 1
fi

echo -e "${GREEN}Using Project: ${PROJECT_ID}${NC}"
echo ""

# Set project
gcloud config set project ${PROJECT_ID}

# Enable Secret Manager API
echo -e "${BLUE}→ Enabling Secret Manager API...${NC}"
gcloud services enable secretmanager.googleapis.com
echo -e "${GREEN}✓ Secret Manager enabled${NC}"
echo ""

# GitHub Token
echo -e "${BLUE}Step 1: GitHub Personal Access Token${NC}"
echo ""
echo "You need a GitHub Personal Access Token with 'repo' scope."
echo ""
echo -e "${YELLOW}To create one:${NC}"
echo "  1. Go to: https://github.com/settings/tokens/new"
echo "  2. Name it: 'AI Visibility Dashboard - Cloud Run'"
echo "  3. Select scope: ✓ repo (Full control of private repositories)"
echo "  4. Click 'Generate token'"
echo "  5. Copy the token (starts with ghp_)"
echo ""
read -p "Enter your GitHub Personal Access Token: " -s GITHUB_TOKEN
echo ""

if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}✗ GitHub token required${NC}"
    exit 1
fi

# Validate token format
if [[ ! "$GITHUB_TOKEN" =~ ^ghp_ ]]; then
    echo -e "${YELLOW}⚠  Warning: Token doesn't start with 'ghp_'. Make sure it's a Personal Access Token.${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create or update the secret
echo ""
echo -e "${BLUE}→ Storing GitHub token in Secret Manager...${NC}"
echo "$GITHUB_TOKEN" | gcloud secrets create github-token --data-file=- 2>/dev/null || \
echo "$GITHUB_TOKEN" | gcloud secrets versions add github-token --data-file=-

echo -e "${GREEN}✓ GitHub token stored${NC}"
echo ""

# Grant Cloud Run service account access to the secret
echo -e "${BLUE}→ Granting Cloud Run access to secrets...${NC}"

# Get the project number
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)')
CLOUD_RUN_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Grant access
gcloud secrets add-iam-policy-binding github-token \
    --member="serviceAccount:${CLOUD_RUN_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

echo -e "${GREEN}✓ Permissions granted${NC}"
echo ""

# Summary
echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Git Credentials Setup Complete!         ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ GitHub token stored in Secret Manager${NC}"
echo -e "${GREEN}✓ Cloud Run has access to the secret${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Deploy your app: ./deploy_to_cloud_run.sh"
echo "  2. Client data will now persist via Git commits"
echo "  3. Changes will sync between local dev and Cloud Run"
echo ""
echo -e "${BLUE}What happens now:${NC}"
echo "  • When you create a client in Cloud Run, it will commit to GitHub"
echo "  • On next deployment, the latest data pulls from GitHub"
echo "  • Local dev and Cloud Run stay in sync"
echo ""
