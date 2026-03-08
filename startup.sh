#!/bin/bash
# Startup script for Cloud Run - sets up git and syncs data

set -e

echo "🚀 Starting AI Visibility Dashboard..."

# Configure git if credentials are provided
if [ -n "$GIT_USER_NAME" ] && [ -n "$GIT_USER_EMAIL" ]; then
    echo "📝 Configuring git..."
    git config --global user.name "$GIT_USER_NAME"
    git config --global user.email "$GIT_USER_EMAIL"
    echo "✓ Git configured"
fi

# Set up GitHub authentication with Personal Access Token
if [ -n "$GITHUB_TOKEN" ]; then
    echo "🔐 Setting up GitHub authentication..."

    # Change remote from SSH to HTTPS with token
    git remote set-url origin https://${GITHUB_TOKEN}@github.com/dasilvacon/ai-visibility-tracker.git

    echo "✓ GitHub authentication configured"

    # Pull latest client data from repository
    echo "📥 Syncing client data from GitHub..."
    if git pull origin main --rebase; then
        echo "✓ Client data synced"
    else
        echo "⚠️  Git pull failed, continuing with existing data..."
    fi
else
    echo "⚠️  No GITHUB_TOKEN found - git operations will be disabled"
    echo "   Client data changes will not persist between deployments"
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
