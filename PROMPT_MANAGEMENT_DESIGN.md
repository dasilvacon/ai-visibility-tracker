# Prompt Lifecycle Management Design

## Problem Statement
When adding new prompts over time, you need to:
- Track when each batch was added and why
- Distinguish between baseline prompts and new additions
- Remove/archive prompts that are no longer relevant
- See in reports which prompts are new vs. established

## Solution: Prompt Batches with Metadata

### Concept: Every prompt belongs to a "batch"

**Batch = A group of prompts added at the same time for a specific reason**

Example batches:
- **Batch 1:** "Initial baseline prompts" (Jan 2026, 100 prompts)
- **Batch 2:** "New lipstick line launch" (Mar 2026, 25 prompts)
- **Batch 3:** "Summer campaign keywords" (Jun 2026, 30 prompts)
- **Batch 4:** "Holiday shopping season" (Nov 2026, 40 prompts)

---

## User Flow: Adding New Prompts

### Current State: Generate Page

**When you click "Generate Prompts", you'll see:**

```
┌─────────────────────────────────────────────────────────┐
│  🎯 Generate Prompts                                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  You have 100 existing prompts for Rare Beauty          │
│                                                           │
│  What do you want to do?                                 │
│                                                           │
│  ○ Start Fresh (Replace all 100 existing prompts)       │
│     Use this for annual refresh or complete strategy    │
│     change                                               │
│                                                           │
│  ● Add New Prompts (Keep existing 100, add more)        │
│     Use this for product launches, campaigns, or        │
│     expanding your tracking set                          │
│                                                           │
├─────────────────────────────────────────────────────────┤
│  ADD NEW PROMPTS DETAILS:                                │
│                                                           │
│  Reason/Campaign Name: [New Lipstick Line Launch    ]   │
│                                                           │
│  Notes (optional):                                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Testing visibility for 3 new lipstick shades     │  │
│  │ launched March 15. Will track through Q2.        │  │
│  └───────────────────────────────────────────────────┘  │
│                                                           │
│  Number of new prompts to generate: [25]                │
│                                                           │
│  [Generate New Batch]                                   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Data Structure: Enhanced Prompt Metadata

### Each prompt now includes:

```csv
prompt_id,prompt_text,persona,category,intent_type,expected_visibility_score,batch_id,batch_name,date_added,status,notes
prompt_001,best luxury eyeshadow,Luxury Buyer,Product,commercial,0.75,batch_baseline,Initial Baseline,2026-01-15,active,Core tracking set
prompt_002,how to apply eyeshadow,Info Seeker,Tutorial,informational,0.65,batch_baseline,Initial Baseline,2026-01-15,active,Core tracking set
prompt_101,new nude lipstick,Makeup Lover,Product,commercial,0.70,batch_lipstick_launch,New Lipstick Line Launch,2026-03-15,active,Testing new product visibility
prompt_102,best spring lipstick,Seasonal Buyer,Seasonal,commercial,0.72,batch_lipstick_launch,New Lipstick Line Launch,2026-03-15,active,Q2 campaign focus
```

### Key Fields:
- **batch_id**: Unique identifier (e.g., `batch_baseline`, `batch_lipstick_launch`)
- **batch_name**: Human-readable name (e.g., "Initial Baseline", "New Lipstick Line Launch")
- **date_added**: When this batch was created
- **status**: `active`, `archived`, or `removed`
- **notes**: Optional context about this batch

---

## New Feature: Prompt Library Manager

### New page in navigation: "📚 Prompt Library"

Shows all your prompts organized by batch:

```
┌─────────────────────────────────────────────────────────────────┐
│  📚 Prompt Library - Rare Beauty                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ✅ ACTIVE BATCHES (195 total prompts)                           │
│                                                                   │
│  ╔═══════════════════════════════════════════════════════════╗  │
│  ║ 🌟 Initial Baseline                                       ║  │
│  ║ Added: Jan 15, 2026 | 100 prompts | Always active        ║  │
│  ║ Notes: Core tracking set for monthly reports              ║  │
│  ╠═══════════════════════════════════════════════════════════╣  │
│  ║ [View Prompts] [Export] [Archive Batch]                  ║  │
│  ╚═══════════════════════════════════════════════════════════╝  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 💄 New Lipstick Line Launch                               │  │
│  │ Added: Mar 15, 2026 | 25 prompts | Active                │  │
│  │ Notes: Testing 3 new lipstick shades through Q2          │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │ [View Prompts] [Export] [Archive Batch]                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ ☀️ Summer Campaign Keywords                               │  │
│  │ Added: Jun 1, 2026 | 30 prompts | Active                 │  │
│  │ Notes: Q3 summer makeup campaign focus                    │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │ [View Prompts] [Export] [Archive Batch]                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 🎄 Holiday Shopping Season                                │  │
│  │ Added: Nov 1, 2026 | 40 prompts | Active                 │  │
│  │ Notes: Holiday gift guide keywords                        │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │ [View Prompts] [Export] [Archive Batch]                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  📦 ARCHIVED BATCHES (25 total prompts)                          │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 🍂 Fall Collection Test (Archived)                        │  │
│  │ Added: Sep 1, 2025 | 25 prompts | Archived Oct 15, 2025  │  │
│  │ Reason: Campaign ended, low performance                   │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │ [View Archived Prompts] [Restore Batch] [Delete Forever] │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Report Integration: Batch Visibility

### In Main Dashboard Reports:

**Overview page shows breakdown by batch:**

```
╔════════════════════════════════════════════════════════╗
║  📊 Visibility by Prompt Batch                          ║
╠════════════════════════════════════════════════════════╣
║                                                          ║
║  🌟 Initial Baseline (100 prompts)                      ║
║  Current: 35% visibility | Last month: 32% (+3%)       ║
║  ═══════════════════════════════ 35%                   ║
║                                                          ║
║  💄 New Lipstick Line Launch (25 prompts)               ║
║  Current: 18% visibility | Last month: 12% (+6%)       ║
║  ══════════ 18%                                         ║
║  📌 Added Mar 2026 - New product launch                 ║
║                                                          ║
║  ☀️ Summer Campaign (30 prompts)                        ║
║  Current: 28% visibility | Last month: 22% (+6%)       ║
║  ═══════════════════ 28%                                ║
║  📌 Added Jun 2026 - Q3 campaign                        ║
║                                                          ║
╚════════════════════════════════════════════════════════╝
```

### Export includes batch information:

When exporting results to client, the report clearly shows:
- Which prompts are baseline (always tracked)
- Which prompts are new additions (and why)
- Performance comparisons are only shown for prompts that existed in both reporting periods

---

## Benefits of This System

### ✅ Organized Tracking
- See exactly which prompts were added when and why
- Baseline prompts stay consistent month-over-month
- New prompts are clearly labeled in reports

### ✅ Flexible Management
- Archive prompts from expired campaigns
- Remove underperforming test batches
- Expand tracking set strategically

### ✅ Clear Client Communication
- Reports show: "Your core 100 prompts improved 32% → 35%"
- Reports show: "New lipstick launch prompts at 18% visibility"
- Clients understand what's baseline vs. what's new

### ✅ Campaign Testing
- Test new keywords for specific campaigns
- Archive them when campaign ends
- Don't pollute your core tracking set

---

## Implementation Priority

### Phase 1 (Essential):
1. Add batch metadata to prompt generation
2. Ask "Start Fresh" vs "Add New" when generating
3. Collect batch name and notes
4. Store batch info in CSV

### Phase 2 (Important):
1. Create Prompt Library Manager page
2. Show batches grouped by status
3. Add archive/restore functionality
4. Add individual prompt archival

### Phase 3 (Nice to Have):
1. Visual batch performance charts
2. Batch comparison tool
3. Export by batch
4. Batch scheduling (auto-archive after date)

---

## Questions for You:

1. **Does this match what you're looking for?**
2. **Would you want to archive entire batches or individual prompts?** (Or both?)
3. **Should archived prompts still show in old reports?** (For historical comparison)
4. **Any other metadata you'd want to track?** (e.g., campaign budget, expected end date, etc.)

Let me know and I'll start building this!
