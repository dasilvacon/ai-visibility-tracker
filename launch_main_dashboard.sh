#!/bin/bash
echo "🚀 Launching AI Visibility Dashboard..."
echo "📍 Running on: http://localhost:8501"
echo ""

# Activate virtual environment
source venv/bin/activate

streamlit run streamlit_app_html.py --server.port 8501
