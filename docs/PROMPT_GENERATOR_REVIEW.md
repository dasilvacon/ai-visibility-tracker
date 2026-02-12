# Prompt Generator App - Comprehensive Review & Improvement Plan

**Date:** February 12, 2026
**Reviewer:** Claude
**Status:** Critical UX Issues Identified

---

## 🚨 CRITICAL ISSUE FOUND

### Problem: User Was Running The Wrong App

**What Happened:**
- You were running `streamlit_app_html.py` (the main AI Visibility Tracker dashboard)
- You should have been running `prompt_generator_app.py` (the Prompt Generator tool)
- This is why you didn't see the quality scoring features I added

**Root Cause:**
The project has **TWO separate Streamlit apps** with no clear indication of which one to use:

1. **`streamlit_app_html.py`** - Main AI Visibility Tracker
   - Client-facing dashboard with authentication
   - Shows HTML reports for test results
   - Collapsed sidebar, report viewer

2. **`prompt_generator_app.py`** - Prompt Generator (Admin Tool)
   - Admin-only tool for creating and managing prompts
   - Has pages: Client Manager, Generate, Review & Approve, Export, Library
   - **THIS is where quality scoring was added**

---

## 📊 Current Architecture Analysis

### App Structure

```
ai-visibility-tracker/
├── streamlit_app_html.py       ← Main Tracker (CLIENT-FACING)
├── prompt_generator_app.py     ← Prompt Generator (ADMIN ONLY)
├── prompt_generator_pages/     ← Pages for prompt generator
│   ├── generate.py             ← Generation with quality scoring
│   ├── review.py               ← Review & approval
│   ├── export_page.py          ← Export approved prompts
│   ├── library.py              ← Prompt library management
│   └── settings.py             ← Client manager
└── src/
    ├── prompt_generator/       ← Core generation logic
    │   ├── generator.py        ← Main generator (has quality scoring!)
    │   ├── quality_scorer.py   ← NEW quality scoring system
    │   └── approval_manager.py
    └── authentication.py
```

### Data Flow (Current State)

```
1. PROMPT GENERATION (prompt_generator_app.py)
   ├── Client Manager → Select client (e.g., Natasha Denona)
   ├── Generate → Create prompts with quality scores
   ├── Review & Approve → Filter and approve prompts
   └── Export → Save to CSV

2. AI VISIBILITY TESTING (streamlit_app_html.py)
   ├── ??? How do prompts get imported? ???
   ├── Run tests against AI chatbots
   └── Display results in dashboard
```

**MISSING LINK:** No clear workflow from Export → Main Tracker!

---

## ⚠️ UX Issues Identified

### 1. **App Confusion (CRITICAL)**
**Issue:** Users don't know which app to run
**Impact:** User ran wrong app for 10+ minutes
**Fix:**
- Rename apps with clear names:
  - `streamlit_app_html.py` → `ai_visibility_dashboard.py`
  - `prompt_generator_app.py` → `prompt_generator.py`
- Add README in root with clear instructions
- Add startup messages showing which app is running

### 2. **No Integration Between Apps**
**Issue:** Prompt Generator exports CSVs, but how do they get into the main tracker?
**Impact:** Manual, error-prone workflow
**Fix:**
- Add "Import Prompts" page to main tracker
- OR consolidate both apps into one with role-based access

### 3. **Client Data Confusion**
**Issue:** "Say I Do" client disappeared because:
- No persistence before Feb 10
- Data only in session state
- Never re-created after persistence system added

**Impact:** Lost work, confusion
**Fix:** Already fixed with `clients.json` registry

### 4. **Quality Scores Not Visible**
**Issue:** User couldn't see quality scores because:
- Running wrong app
- Changes not deployed to Streamlit Cloud
- No indication feature exists

**Impact:** New feature completely invisible
**Fix:**
- Clear app naming (see #1)
- Deploy to cloud
- Add feature announcement in app

### 5. **Workflow Not Intuitive**
**Issue:** User doesn't understand the end-to-end flow:
1. Where do I start?
2. How do I create a new client?
3. How do prompts get to the tracker?
4. When do I use which app?

**Impact:** Confusion, inefficiency
**Fix:** Add guided onboarding + workflow diagram

---

## 🔧 Technical Issues Found

### 1. **Separate Apps = Separate State**
- Session state doesn't transfer between apps
- User data siloed
- Confusing authentication flow

### 2. **Export Process**
Looking at `export_page.py`:
- Exports approved prompts to CSV
- Archives drafts
- But... what happens next?
- No clear "Send to Tracker" button

### 3. **File Path Management**
- Both apps use same data directories
- Could cause conflicts
- No locking mechanism

### 4. **Quality Scoring Integration**
- Quality scorer IS integrated in generation
- CSV export includes quality columns
- UI displays quality metrics
- BUT: Only works in `prompt_generator_app.py` (which user wasn't running!)

---

## ✅ What's Working Well

### Strengths:
1. **Quality Scoring System** - Excellent implementation:
   - 5 dimensions (naturalness, clarity, length, relevance, diversity)
   - Clear classification (Excellent/Good/Fair/Poor)
   - Actionable recommendations
   - Integrated into generation workflow

2. **Batch Management** - Good structure:
   - Batch tracking with IDs
   - Draft persistence
   - Archive system

3. **Approval Workflow** - Well designed:
   - Filter system
   - Bulk actions
   - Client review export/import
   - Individual prompt editing

4. **Client Registry** - Solved data loss:
   - `clients.json` persistence
   - Auto-commit on creation
   - No more disappearing clients

---

## 🎯 Recommended Improvements

### Priority 1: CRITICAL (Do Immediately)

#### A. **Fix App Confusion**

**Rename Files:**
```bash
mv streamlit_app_html.py ai_visibility_dashboard.py
mv prompt_generator_app.py prompt_generator.py
```

**Add Startup Banners:**

In `prompt_generator.py` (after authentication):
```python
st.success("""
🎨 **PROMPT GENERATOR** - Admin Tool

Use this app to:
- Create and manage clients
- Generate test prompts with quality scoring
- Review and approve prompts
- Export prompts to CSV for testing

👉 **For viewing test results**, use the AI Visibility Dashboard instead.
""")
```

In `ai_visibility_dashboard.py`:
```python
st.info("""
📊 **AI VISIBILITY DASHBOARD** - Client Reports

This dashboard shows test results from AI chatbots.

👉 **To create new test prompts**, use the Prompt Generator tool instead.
""")
```

#### B. **Create Clear README**

Create `HOW_TO_USE.md`:
```markdown
# AI Visibility Tracker - Quick Start

## Which App Should I Use?

### 🎨 Prompt Generator (`prompt_generator.py`)
**Use this to CREATE prompts**

Run: `streamlit run prompt_generator.py`

Workflow:
1. Client Manager → Set up client
2. Generate → Create prompts (with quality scores!)
3. Review & Approve → Filter and approve
4. Export → Save to CSV

---

### 📊 AI Visibility Dashboard (`ai_visibility_dashboard.py`)
**Use this to VIEW results**

Run: `streamlit run ai_visibility_dashboard.py`

Workflow:
1. Login with client credentials
2. View HTML reports
3. See visibility scores

---

## Full Workflow

```
CREATE PROMPTS          TEST PROMPTS           VIEW RESULTS
(Prompt Generator) →    (CLI Tool) →           (Dashboard)
     ↓                      ↓                       ↓
  prompts.csv    →   Run tests against    →   HTML reports
                     ChatGPT, Claude,
                     Perplexity
```
```

#### C. **Deploy Quality Scoring to Cloud**

```bash
# Commit and push changes
git add src/prompt_generator/quality_scorer.py
git add src/prompt_generator/generator.py
git add prompt_generator_pages/generate.py
git add prompt_generator_pages/review.py
git add docs/

git commit -m "Add prompt quality scoring system

- 5-dimension quality evaluation
- Real-time scoring during generation
- Quality filters in review
- Documentation and tests"

git push origin main
```

Then wait for Streamlit Cloud to deploy.

---

### Priority 2: HIGH (Do This Week)

#### D. **Add Integration Between Apps**

**Option 1: Import Feature in Dashboard** (Quick fix)

Add new page to dashboard: "Import Prompts"
- File upload for CSV from Prompt Generator
- Validate and import
- Link to client account

**Option 2: Consolidate Apps** (Better long-term)

Merge both apps into one with role-based pages:
```python
if role == "admin":
    pages = ["Dashboard", "Prompt Generator", "Client Manager", ...]
else:  # client role
    pages = ["Dashboard", "My Reports"]
```

Benefits:
- Single authentication
- Shared state
- Clear workflow
- Easier to maintain

#### E. **Add Workflow Guidance**

Create first-run experience:
```python
if 'first_visit' not in st.session_state:
    st.session_state.first_visit = True

if st.session_state.first_visit:
    show_onboarding_tour()
```

Show step-by-step:
1. ✅ Set up client → 2. Generate prompts → 3. Review & approve → 4. Export

#### F. **Improve Client Setup**

Current state:
- `simple_client_setup.py` exists
- `edit_client.py` exists
- But workflow unclear

Improvements:
- Add "Quick Setup" wizard for new clients
- Template library for common industries (wedding, beauty, fashion)
- Validation before generation

---

### Priority 3: MEDIUM (Next Sprint)

#### G. **Better Prompt → Tracker Integration**

Add "Export for Testing" feature:
```python
# In export_page.py
if st.button("Export & Prepare for Testing"):
    # 1. Export approved prompts
    csv_path = export_approved_prompts()

    # 2. Create test config
    test_config = create_test_config(client_name, csv_path)

    # 3. Show CLI command
    st.code(f"python main.py --config {test_config}")

    # 4. OR: Auto-trigger test run
    run_tests_async(test_config)
```

#### H. **Add Analytics Dashboard**

Track across all generations:
- Average quality score trends
- Approval rates by persona
- Most common issues
- Quality improvements over time

#### I. **Prompt Quality Improvements**

Current: Template-based generation
Goal: AI-powered generation

Add real AI generation:
```python
# In generator.py
generator = PromptGenerator(
    personas_file=personas_file,
    keywords_file=keywords_file,
    api_client=AnthropicClient(),  # Add real API client
    use_ai_generation=True,        # Enable AI
    enable_quality_scoring=True
)
```

Benefits:
- More natural prompts
- Better diversity
- Higher quality scores
- Fewer "Poor" rated prompts

---

## 📋 Implementation Checklist

### Immediate Actions (Today):
- [ ] Rename apps for clarity
- [ ] Add startup banners
- [ ] Create HOW_TO_USE.md
- [ ] Commit and push quality scoring to cloud
- [ ] Test both apps work correctly

### This Week:
- [ ] Test full workflow end-to-end
- [ ] Document integration process
- [ ] Add onboarding tour
- [ ] Improve client setup wizard

### Next Sprint:
- [ ] Build prompt → tracker integration
- [ ] Add analytics dashboard
- [ ] Implement AI-powered generation
- [ ] Add automated testing

---

## 🎓 Recommended User Workflow

### For Agency Staff (Admin):

**CREATING PROMPTS:**
1. Open Terminal
2. Run: `streamlit run prompt_generator.py`
3. Go to "Client Manager" → Create/select client
4. Go to "Generate" → Set count to 100-300 prompts
5. Review quality metrics (should see 80%+ Excellent/Good)
6. Go to "Review & Approve" → Filter by quality, approve high-quality prompts
7. Go to "Export" → Download CSV
8. Run tests via CLI: `python main.py --prompts exported_prompts.csv`

**VIEWING RESULTS:**
1. Open Terminal
2. Run: `streamlit run ai_visibility_dashboard.py`
3. Login as admin
4. View reports and metrics

### For Clients:

1. Receive login credentials
2. Open dashboard link (Streamlit Cloud URL)
3. Login
4. View their brand's visibility reports
5. That's it! (No access to prompt generator)

---

## 🔮 Future Enhancements

1. **Real-time Collaboration**
   - Multiple users editing same batch
   - Comment threads on prompts
   - Version history

2. **Advanced Analytics**
   - Correlation: Quality score → Visibility score
   - A/B testing different prompt styles
   - Competitor benchmarking

3. **Automated Testing**
   - One-click "Generate → Approve → Test"
   - Scheduled monthly tests
   - Alert on visibility drops

4. **AI-Powered Insights**
   - "Your prompts are too formal for Gen Z audience"
   - "Add more comparison prompts for better coverage"
   - Auto-suggest improvements

---

## Summary

### What's Great:
✅ Quality scoring system is excellent
✅ Batch management works well
✅ Approval workflow is intuitive
✅ Persistence issues solved

### What Needs Fixing:
❌ App confusion (critical)
❌ No integration between apps
❌ Workflow not clear
❌ Missing onboarding

### Next Steps:
1. **TODAY**: Fix app naming, deploy quality scoring
2. **THIS WEEK**: Add integration, test end-to-end
3. **NEXT SPRINT**: Analytics, AI generation

---

## Contact for Questions

If you have questions about this review or implementation:
- Review the HOW_TO_USE.md guide
- Check docs/QUALITY_SCORING.md for quality system details
- Test the workflow end-to-end before deploying to clients
