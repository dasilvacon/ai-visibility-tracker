#!/bin/bash

echo "🛑 Stopping all Streamlit processes..."
pkill -9 streamlit 2>/dev/null
sleep 1

echo "🧹 Clearing caches..."
rm -rf ~/.streamlit/cache 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

echo "✨ Starting Prompt Generator on port 8502..."
echo "📍 Navigate to: http://localhost:8502"
echo ""
echo "🔄 App is loading..."
echo ""

streamlit run prompt_generator_app.py --server.port 8502
