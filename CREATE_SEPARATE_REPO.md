# Creating a Completely Separate Prompt Generator Repo

If you want **total separation**, create a new repository just for the prompt generator.

---

## Steps to Create Separate Repo

### 1. Create New GitHub Repository

1. Go to GitHub: https://github.com/new
2. Repository name: `ai-prompt-generator` (or your choice)
3. Description: "Prompt Generator & Approval Tool for AI Visibility Tracking"
4. Choose: Public or Private
5. Don't initialize with README (we'll push existing code)
6. Click "Create repository"

### 2. Copy Required Files

Create a new directory and copy files:

```bash
# Create new directory
cd ~/Desktop  # or wherever you want
mkdir ai-prompt-generator
cd ai-prompt-generator

# Initialize git
git init
git branch -M main

# Copy files from original repo
SOURCE="/Users/tiffanydasilva/Claude-Projects/ai-visibility-tracker"

# Main app
cp $SOURCE/prompt_generator_app.py .

# UI pages
cp -r $SOURCE/prompt_generator_pages .

# Core modules (need entire src structure)
mkdir -p src
cp -r $SOURCE/src/prompt_generator src/

# Data files
mkdir -p data
cp $SOURCE/data/natasha_denona_personas.json data/
cp $SOURCE/data/natasha_denona_keywords.csv data/

# Config
cp -r $SOURCE/.streamlit .

# Documentation
cp $SOURCE/PROMPT_GENERATOR_GUIDE.md .
cp $SOURCE/START_HERE.md .
```

### 3. Create requirements.txt

Create a minimal `requirements.txt` with only what prompt generator needs:

```txt
# Core dependencies
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.17.0
python-dateutil>=2.8.2
```

### 4. Create README.md

```bash
cat > README.md << 'EOF'
# AI Prompt Generator & Approval Tool

Standalone tool for generating, reviewing, and approving prompts for AI visibility tracking.

## Quick Start

```bash
streamlit run prompt_generator_app.py
```

See `PROMPT_GENERATOR_GUIDE.md` for detailed instructions.

## Features

- Generate 10-1000 prompts with customizable settings
- Real-time deduplication (removes duplicates during generation)
- Batch review with advanced filtering
- Export to CSV/JSON

## Deployment

Deploy to Streamlit Cloud:
1. Push this repo to GitHub
2. Go to https://share.streamlit.io
3. Deploy with main file: `prompt_generator_app.py`
EOF
```

### 5. Create .gitignore

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# Streamlit
.streamlit/secrets.toml

# Data (optional - keep generated files local)
data/prompt_generation/drafts/*
data/prompt_generation/approved/*
data/prompt_generation/archived/*

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
EOF
```

### 6. Push to GitHub

```bash
# Add all files
git add .

# Initial commit
git commit -m "Initial commit: Prompt Generator & Approval Tool"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/yourusername/ai-prompt-generator.git

# Push
git push -u origin main
```

### 7. Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click "New app"
3. Select: `yourusername/ai-prompt-generator`
4. Branch: `main`
5. Main file: `prompt_generator_app.py`
6. Deploy!

---

## Pros of Separate Repo

✅ **Total isolation** - Changes don't affect main dashboard
✅ **Cleaner organization** - Each repo has single purpose
✅ **Independent versioning** - Different release cycles
✅ **Separate access control** - Can grant different permissions
✅ **Simpler repo structure** - Only prompt generator files

## Cons of Separate Repo

⚠️ **Code duplication** - If you update core modules, need to update both repos
⚠️ **Data file sync** - Need to keep personas/keywords in sync manually
⚠️ **More maintenance** - Two repos to manage
⚠️ **Harder to share updates** - Changes to shared code require manual copying

---

## Recommendation

**If you want total separation and don't mind the maintenance overhead:**
→ Use separate repo

**If you want easier maintenance and shared code:**
→ Use same repo, two deployments (current approach)

For most use cases, **same repo with two deployments is simpler and better**.
