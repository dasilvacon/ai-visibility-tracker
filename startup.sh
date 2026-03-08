#!/bin/bash
# Startup script for Cloud Run - sets up git and syncs data

# Don't exit on error - we'll handle errors manually
set +e

echo "🚀 Starting AI Visibility Dashboard..."

# Configure git if credentials are provided
if [ -n "$GIT_USER_NAME" ] && [ -n "$GIT_USER_EMAIL" ]; then
    echo "📝 Configuring git..."
    git config --global user.name "$GIT_USER_NAME"
    git config --global user.email "$GIT_USER_EMAIL"
    echo "✓ Git configured"
fi

# Set up GitHub authentication and sync data
if [ -n "$GITHUB_TOKEN" ]; then
    echo "🔐 Setting up GitHub authentication..."
    echo "   Token length: ${#GITHUB_TOKEN} characters"

    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo "📦 Initializing git repository..."
        git init

        echo "   Adding remote..."
        REMOTE_URL="https://${GITHUB_TOKEN}@github.com/dasilvacon/ai-visibility-tracker.git"
        if git remote add origin "$REMOTE_URL"; then
            echo "✓ Remote added successfully"
        else
            echo "✗ Failed to add remote"
            # Continue anyway to start Streamlit
        fi

        # Fetch initial data from remote
        echo "📥 Fetching initial data from GitHub..."
        if git fetch origin main 2>&1; then
            # Checkout the main branch
            git checkout -b main origin/main
            echo "✓ Client data synced from GitHub"
        else
            echo "⚠️  Git fetch failed, continuing with existing data..."
        fi
    else
        # Update remote URL with token
        REMOTE_URL="https://${GITHUB_TOKEN}@github.com/dasilvacon/ai-visibility-tracker.git"
        git remote set-url origin "$REMOTE_URL"
        echo "✓ GitHub authentication configured"

        # Fetch and reset to match remote
        echo "📥 Syncing client data from GitHub..."
        if git fetch origin main && git reset --hard origin/main; then
            echo "✓ Client data synced from GitHub"
        else
            echo "⚠️  Git sync failed, continuing with existing data..."
        fi
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
