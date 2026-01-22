#!/bin/bash
# Setup script for AI Visibility Tracker

echo "=========================================="
echo "AI Visibility Tracker - Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "Error: Python 3 not found. Please install Python 3.9 or higher."
    exit 1
fi

echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed"
echo ""

# Create config file if it doesn't exist
if [ ! -f "config/config.json" ]; then
    echo "Creating config file from template..."
    cp config/config.template.json config/config.json
    echo "✓ Config file created at config/config.json"
    echo ""
    echo "⚠️  IMPORTANT: Edit config/config.json and add your API keys before running tests!"
else
    echo "✓ Config file already exists"
fi

echo ""

# Create necessary directories
mkdir -p data/results
mkdir -p data/reports

echo "✓ Output directories created"
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit config/config.json and add your API keys"
echo "2. (Optional) Customize data/prompts_template.csv with your prompts"
echo "3. Activate the virtual environment: source venv/bin/activate"
echo "4. Run the tracker: python main.py"
echo ""
echo "For more information, see README.md"
echo ""
