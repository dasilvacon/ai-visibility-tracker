# Prompt Quality Scoring System

## Overview

The quality scoring system evaluates prompts across five key dimensions to ensure they're effective for AI visibility testing. Each prompt receives a score from 0-100 and a quality classification (Excellent, Good, Fair, or Poor).

## Scoring Dimensions

### 1. Naturalness (30% weight)
**What it measures:** Does the prompt sound like a real search query?

**Good prompts:**
- Direct and to-the-point
- No greetings ("Hi", "Hey", "Hello")
- No pleasantries ("Thanks!", "Appreciate it!")
- No conversational filler ("Quick question:", "Can anyone help?")

**Examples:**
- ✅ "Best long-lasting eyeshadow for oily lids" (100/100)
- ✅ "Compare luxury eyeshadow to Urban Decay" (100/100)
- ❌ "Hi! Can anyone help me find eyeshadow? Thanks!" (0/100)

**Penalties:**
- Greetings: -40 points
- Pleasantries: -35 points
- Filler phrases: -30 points
- Multiple infractions: -15 additional points

---

### 2. Clarity (25% weight)
**What it measures:** Is the intent clear and specific?

**Good prompts:**
- Have a specific topic/keyword
- Understandable intent
- Not too vague or generic

**Examples:**
- ✅ "Best eyeshadow for hooded eyes" (90/100) - specific need
- ✅ "Eyeshadow vs MAC" (80/100) - clear comparison
- ❌ "eyeshadow" (40/100) - too vague
- ❌ "something for makeup stuff" (20/100) - generic words

**Scoring factors:**
- Specific product/topic indicators: +10 points
- Clear question structure: +5 points
- Comparison language: +10 points
- Too many questions (>2): -15 points
- Generic words ("something", "stuff"): -20 points

---

### 3. Length (15% weight)
**What it measures:** Is the prompt an appropriate length?

**Ideal length:** 3-25 words (sweet spot: 5-15 words)

**Examples:**
- ✅ "Best luxury eyeshadow palette" (4 words) - 100/100
- ✅ "How to apply eyeshadow for hooded eyes step by step" (10 words) - 100/100
- ⚠️ "eyeshadow" (1 word) - 40/100, too vague
- ❌ 35+ word rambling query - 30/100, too long

**Scoring:**
- 3-25 words: 95-100 points
- 2 words: 70 points
- 1 word: 40 points
- 26-34 words: Gradual penalty (6 points per excess word)
- 35+ words: 30 points

---

### 4. Keyword Relevance (20% weight)
**What it measures:** Does the prompt align with the client's business?

**Scoring factors:**
- Main keyword present: +20 points
- Intent alignment: +10 points
  - Comparison intent + "vs"/"compared to"
  - How-to intent + "how"
  - Recommendation intent + "best"/"top"
  - Review intent + "review"/"worth it"
- Persona alignment: +10 points
  - Professional language for MUA personas
  - Beginner language for beginner personas
  - Luxury indicators for luxury personas

**Baseline:** 70/100 (assumes basic relevance)

---

### 5. Diversity (10% weight)
**What it measures:** Is this prompt unique from other prompts?

**How it works:**
- Uses Jaccard similarity (word overlap) with existing prompts
- High similarity to existing = low diversity score
- First prompt always gets 100/100 diversity

**Example:**
- Prompt 1: "Best eyeshadow palette" → 100/100 (first prompt)
- Prompt 2: "Best eyeshadow for oily lids" → 75/100 (some overlap)
- Prompt 3: "Eyeshadow tutorial" → 95/100 (very different)

---

## Overall Quality Classification

Final score is weighted average:
```
Overall = (Naturalness × 0.30) + (Clarity × 0.25) + (Length × 0.15) +
          (Relevance × 0.20) + (Diversity × 0.10)
```

**Quality Levels:**
- **Excellent** (90-100): High-quality, production-ready prompts
- **Good** (75-89): Solid prompts with minor issues
- **Fair** (60-74): Usable but need improvement
- **Poor** (<60): Significant quality issues, should be revised

---

## Quality Issues & Recommendations

The scorer automatically identifies issues and provides recommendations:

**Common Issues:**
- Contains greetings → "Remove greetings and pleasantries - make it direct"
- Contains pleasantries → "Phrase it like a real search query"
- Too vague → "Add more specific details about what you're looking for"
- Too short → "Add more context - aim for 5-15 words"
- Too long → "Simplify - remove unnecessary words"
- Very similar to existing → "Try a different angle or phrasing"

---

## Using Quality Scores

### During Generation
1. Prompts are scored automatically as they're generated
2. Quality stats are shown in the generation summary
3. Individual prompts show quality breakdowns

### During Review
1. Filter prompts by quality score range (0-100)
2. Filter by quality level (Excellent, Good, Fair, Poor)
3. View detailed quality breakdown for each prompt
4. See issues and recommendations for improvement

### In Exports
Quality scores are included in CSV exports:
- `quality_overall` - Overall score (0-100)
- `quality_level` - Classification (Excellent/Good/Fair/Poor)
- `quality_naturalness` - Naturalness dimension score
- `quality_clarity` - Clarity dimension score
- `quality_length` - Length dimension score
- `quality_relevance` - Relevance dimension score
- `quality_diversity` - Diversity dimension score

---

## Best Practices

### Aim for Excellent Prompts (90+)
✅ Direct and natural
✅ Clear specific intent
✅ 5-15 words
✅ Contains relevant keywords
✅ Unique phrasing

### Avoid Common Pitfalls
❌ Greetings and pleasantries
❌ Conversational filler
❌ Too vague (1-2 words)
❌ Too long (30+ words)
❌ Generic language ("stuff", "things")

### Quality Benchmarks
- **Initial generation:** Target 80%+ Excellent/Good prompts
- **After review:** Approve only Excellent/Good prompts
- **Final library:** 90%+ Excellent/Good prompts

---

## Technical Details

### Implementation
- **File:** `src/prompt_generator/quality_scorer.py`
- **Class:** `PromptQualityScorer`
- **Integration:** Automatic in `PromptGenerator`

### Performance
- Lightweight - no heavy NLP required
- Fast scoring (~0.001s per prompt)
- No external dependencies

### Extensibility
Easy to customize:
- Adjust weights in dimension calculation
- Add new dimensions
- Customize thresholds
- Add domain-specific rules
