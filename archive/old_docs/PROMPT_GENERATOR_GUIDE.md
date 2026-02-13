# Prompt Generator & Approval Tool - User Guide

## Overview

The Prompt Generator & Approval Tool is a standalone Streamlit application for generating, reviewing, and approving prompts **before** importing them into the main AI Visibility Dashboard.

## Features

✨ **Flexible Generation**
- Choose how many prompts to generate (10-1000) with a prominent slider
- Adjust competitor mention ratio (0-50%)
- Configure AI vs template generation ratio
- Real-time deduplication during generation (not after)

🔍 **Advanced Review & Filtering**
- Filter by persona, category, intent type, score range
- Search within prompt text
- Filter by approval status
- Pagination for large datasets (50 prompts per page)

📊 **Batch Operations**
- Approve/reject all visible prompts with filters active
- Bulk approve by audience (e.g., approve all "Luxury Beauty Enthusiast" prompts)
- Individual prompt editing
- Undo last action

💾 **Safe Export**
- Append to existing `generated_prompts.csv` (default - prevents overwrites)
- Replace `generated_prompts.csv` (with confirmation)
- Export to custom location
- JSON export for full metadata
- Archive management

## Quick Start

### 1. Launch the App

```bash
streamlit run prompt_generator_app.py --server.port 8502
```

The app will run on **port 8502** (separate from the main dashboard on 8501).

### 2. Generate Prompts

1. Go to **Generate** page
2. Use the slider to choose how many prompts (e.g., 100)
3. Adjust competitor ratio (default 30%)
4. Select deduplication mode (recommended: "High Similarity 90%")
5. Click **"🚀 Generate Prompts"**
6. Wait for generation to complete
7. Review statistics and sample prompts

**Example Configuration:**
- Total prompts: 100
- Competitor mentions: 30%
- AI generation: 0% (template-based only for now)
- Deduplication: High Similarity (90%)

**Expected Results:**
- ~95-98 unique prompts generated
- ~2-5 duplicates removed automatically
- Distribution across personas based on weights

### 3. Review & Approve

1. Go to **Review & Approve** page
2. Use sidebar filters to narrow down prompts:
   - **Persona filter**: Select specific audiences
   - **Category filter**: Educational, technical, business
   - **Intent filter**: Informational, how-to, comparison, etc.
   - **Score range**: Focus on high-value prompts (e.g., 7-10)
   - **Text search**: Find specific keywords
3. Use bulk actions:
   - **"✓ Approve All Visible"** - Approves all prompts matching current filters
   - **"✗ Reject All Visible"** - Rejects all prompts matching current filters
   - **"↺ Reset All Visible"** - Resets to pending
4. Click on individual prompts to edit text or metadata
5. Track progress with stats dashboard at the top

**Example Workflow:**
- Filter by "Luxury Beauty Enthusiast" → Approve all visible (35 prompts)
- Filter by "Professional MUA" + Score > 7 → Approve all visible (20 prompts)
- Filter by "Beauty Beginner" → Review individually, approve 15 prompts
- Result: 70 approved prompts ready for export

### 4. Export

1. Go to **Export** page
2. Review breakdown charts (by persona, category, intent)
3. Choose export mode:
   - **Append** (recommended): Adds to existing prompts without overwriting
   - **Replace**: Replaces all prompts (requires confirmation)
   - **Custom location**: Download CSV to review before importing
4. Click **"📥 Export CSV"**
5. Approved prompts are saved to:
   - `data/prompt_generation/approved/approved_YYYYMMDD_HHMMSS.csv`
   - `data/generated_prompts.csv` (if append/replace mode)

**Export Tips:**
- Always use "Append" mode unless you want to start fresh
- Duplicate IDs are automatically skipped when appending
- Keep a copy in the `approved/` directory as a backup

### 5. Settings (Optional)

1. Go to **Settings** page
2. Configure data sources (personas JSON, keywords CSV)
3. Set generation defaults
4. Adjust pagination size and auto-save interval
5. Click **"💾 Save Settings"**

## Workflow Example

Here's a complete workflow for generating 200 prompts:

```
1. Generate Page
   - Set total prompts: 200
   - Competitor ratio: 30%
   - Deduplication: High Similarity
   - Click Generate
   - Result: ~195 unique prompts generated

2. Review & Approve Page
   Filter Approach #1: By Persona
   - Filter: "Luxury Beauty Enthusiast"
   - Review: 65 prompts visible
   - Action: Approve All Visible

   Filter Approach #2: By Intent + Score
   - Filter: Intent = "Comparison" + Score >= 8
   - Review: 25 prompts visible
   - Action: Approve All Visible

   Filter Approach #3: By Category
   - Filter: Category = "Educational"
   - Review: 40 prompts visible
   - Action: Review individually, approve 30

   Final Result: 120 approved prompts

3. Export Page
   - Review breakdown: 40% Luxury Beauty, 30% Professional, etc.
   - Choose: "Append to existing generated_prompts.csv"
   - Click: Export CSV
   - Result: 120 new prompts added to main dataset

4. Main Dashboard
   - Open: streamlit run streamlit_app.py
   - Verify: New prompts appear in prompt count
   - Run: Tracking tests on new prompts
```

## File Structure

```
ai-visibility-tracker/
├── prompt_generator_app.py              # Main entry point (port 8502)
├── prompt_generator_pages/              # UI pages
│   ├── generate.py                      # Generation controls
│   ├── review.py                        # Approval workflow
│   ├── export_page.py                   # Export options
│   └── settings.py                      # Configuration
├── src/prompt_generator/
│   ├── deduplicator.py                  # Real-time deduplication
│   ├── approval_manager.py              # Approval state management
│   └── generator.py                     # Modified with deduplication
├── data/
│   ├── generated_prompts.csv            # Main prompt database (for dashboard)
│   ├── natasha_denona_personas.json     # Persona definitions
│   ├── natasha_denona_keywords.csv      # Keyword sources
│   └── prompt_generation/               # Staging area (NEW)
│       ├── drafts/                      # Auto-saved sessions
│       ├── approved/                    # Approved exports
│       └── archived/                    # Historical generations
└── config/
    └── prompt_generator_config.json     # App settings
```

## Tips & Best Practices

### Deduplication
- **High Similarity (90%)** is recommended for most use cases
- Catches both exact duplicates and near-duplicates (e.g., "Best eyeshadow" vs "Best eyeshadows")
- Typically removes 2-5% of generated prompts

### Approval Strategy
- **Start broad, then narrow**: Approve all high-value personas first, then refine
- **Use filters strategically**: Combine persona + intent + score for targeted approval
- **Review individually for edge cases**: Use bulk for obvious approvals, review manually for borderline prompts

### Export Safety
- **Always use "Append" mode** unless starting fresh
- **Keep backups**: The `approved/` directory maintains copies of all exports
- **Check for duplicates**: The tool automatically skips duplicate IDs when appending

### Performance
- Generation: ~1 second per prompt (template mode)
- Deduplication: <100ms per prompt check
- Review page: Handles 1000+ prompts with pagination
- Export: <5 seconds for 1000 prompts

## Troubleshooting

### "No personas/keywords file found"
- Go to Settings page
- Verify file paths match actual file locations
- Check that files exist: `data/natasha_denona_personas.json`, `data/natasha_denona_keywords.csv`

### "Filters not showing any prompts"
- Click "Clear All Filters" in sidebar
- Check approval status filter (set to "All")
- Verify you have generated prompts first

### "Export button not working"
- Ensure you have approved prompts (not just pending)
- Go to Review & Approve page and approve some prompts first
- Check that export directory exists: `data/prompt_generation/approved/`

### "Deduplication removing too many prompts"
- Lower similarity threshold (use "Exact Match" instead of "High Similarity")
- Or disable deduplication entirely (set to "Disabled")

## Next Steps

After exporting approved prompts:

1. **Open main dashboard**: `streamlit run streamlit_app.py`
2. **Run tracking tests**: Test the new prompts against AI platforms
3. **Analyze results**: Review visibility scores and brand mentions
4. **Iterate**: Generate more prompts for under-represented personas or intents

## Support

For questions or issues, refer to the main project documentation or check the test results in the terminal output.

---

**Last Updated**: January 2026
**Version**: 1.0
