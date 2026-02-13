# Website Content Verification System

## Overview

This system solves a **critical flaw** in the original AI Visibility Tracker: recommendations were based purely on AI response patterns, not actual website content.

### The Problem (Before)

❌ **Assumed Gaps**: If AI mentioned competitors for "how-to" queries, the system assumed:
- Competitors have how-to content
- You don't have how-to content
- **Without actually checking either website!**

This led to potentially false recommendations like "Create how-to content" when:
- You might already have that content (AI just doesn't know about it)
- Competitors might NOT have that content (AI might be wrong/outdated)

### The Solution (Now)

✅ **Verified Gaps**: The system now:
1. **Scrapes your actual website** to see what content exists
2. **Scrapes competitor websites** to see what they actually have
3. **Compares real content** to identify true gaps
4. **Labels recommendations** as "verified" vs "assumed"

---

## How It Works

### 1. Website Crawling

The analyzer crawls up to 50 pages per website (configurable) and identifies:

- **Educational content** (learn, guide, explained, etc.)
- **How-to content** (tutorials, step-by-step, instructions)
- **Comparison content** (vs, versus, compare, alternatives)
- **FAQ pages** (frequently asked questions)
- **Product information** (specifications, features)
- **Blog/articles**
- **Reviews/testimonials**
- **Guides** (ultimate guide, beginner's guide)
- **About pages**

### 2. Content Classification

Each page is analyzed for:
- **URL structure** (/blog/, /how-to/, /faq/)
- **Page title** keywords
- **Heading content** (H1, H2, H3, H4)
- **Body text** patterns
- **Multiple signals** = higher confidence

### 3. Gap Verification

Compares content inventories to identify:

#### ✅ **Verified Gaps** (HIGH PRIORITY)
- Multiple competitors (2+) have this content type
- You don't have it
- **Recommendation**: Create this content

#### 📈 **Expansion Opportunities** (MEDIUM PRIORITY)
- You have some pages (1-2)
- Competitors have significantly more
- **Recommendation**: Expand this content type

#### ✗ **False Positives** (NOT GAPS)
- **Competitive Advantage**: You have it, competitors don't
- **Nobody Has It**: Neither you nor competitors have it
- **Recommendation**: Don't waste time on these

---

## Usage

### Run Website Verification

```bash
# Basic usage (50 pages per site)
python3 verify_websites.py --brand-config data/natasha_denona_brand_config.json

# Quick test (10 pages per site)
python3 verify_websites.py --brand-config data/natasha_denona_brand_config.json --max-pages 10

# Thorough analysis (100 pages per site)
python3 verify_websites.py --brand-config data/natasha_denona_brand_config.json --max-pages 100
```

### Output Files

The script generates two reports:

1. **JSON (Full Details)**: `data/reports/website_verification_Natasha_Denona.json`
   - Complete crawl data
   - All pages analyzed
   - URLs for every content type

2. **TXT (Human-Readable)**: `data/reports/website_verification_Natasha_Denona.txt`
   - Summary of findings
   - Verified gaps
   - Expansion opportunities
   - False positives

---

## Configuration

### Adding Website URLs to Brand Config

Update `data/natasha_denona_brand_config.json`:

```json
{
  "brand": {
    "name": "Natasha Denona",
    "aliases": ["ND", "Natasha Denona Beauty"],
    "website": "https://natashadenona.com"
  },
  "competitors": [
    {
      "name": "Charlotte Tilbury",
      "website": "https://charlottetilbury.com"
    },
    {
      "name": "Pat McGrath Labs",
      "website": "https://patmcgrath.com"
    }
  ]
}
```

**Backward compatible**: Still supports old format (list of competitor name strings).

---

## Integration with Gap Analysis

### Phase 1: Standalone Verification ✅ COMPLETE
- Run website verification separately
- Review verified gaps manually
- Compare against AI-based recommendations

### Phase 2: Integrated Verification (NEXT)
- Automatically run website verification during analysis
- Label recommendations in report as:
  - **✅ VERIFIED GAP** (seen on competitor sites, missing from yours)
  - **⚠️ ASSUMED GAP** (AI mentions competitors, not verified)
- Show competitor example URLs in recommendations
- Filter quick wins to "verified gaps only"

### Phase 3: Smart Caching (FUTURE)
- Cache website analyses (valid for 30 days)
- Only re-crawl if cache expired
- Speed up repeat analyses

---

## Example Output

```
VERIFIED CONTENT GAPS
------------------------------------------------------------------------

1. How To Content [HIGH]
   Status: MISSING from your site
   Competitors with this: 4/5
   Recommendation: Create how-to content
   Competitor examples:
     - https://charlottetilbury.com/how-to (8 pages)
       → https://charlottetilbury.com/how-to/apply-eyeshadow
       → https://charlottetilbury.com/how-to/smoky-eye-tutorial
     - https://hudabeauty.com/tutorials (12 pages)
       → https://hudabeauty.com/tutorials/cut-crease
       → https://hudabeauty.com/tutorials/halo-eye

2. FAQ Pages [MEDIUM]
   Status: MISSING from your site
   Competitors with this: 3/5
   Recommendation: Create FAQ content

EXPANSION OPPORTUNITIES
------------------------------------------------------------------------

• Educational Content
  You have: 2 pages
  Competitors with more: 4/5
  Recommendation: Expand educational content

FALSE POSITIVES (NOT REAL GAPS)
------------------------------------------------------------------------

• Comparison Content
  Status: Competitive Advantage
  Reason: You have 5 pages, most competitors don't
  Recommendation: Maintain and promote this content
```

---

## Technical Details

### Dependencies
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing

### Rate Limiting
- Default: 1 second between requests
- Respects robots.txt (configurable)
- User-agent: Identifies as research crawler

### Content Detection Accuracy

**High Confidence** (multiple signals):
- URL + Title + Heading match = Very likely correct

**Medium Confidence** (single strong signal):
- URL structure match = Probably correct

**Low Confidence** (body text only):
- Keyword in text = Possibly false positive

---

## Limitations & Considerations

### Current Limitations

1. **JavaScript-Rendered Content**: Only crawls static HTML
   - Some sites (React/Vue SPAs) may not be fully captured
   - Workaround: Increase max_pages to get more coverage

2. **Login-Protected Content**: Can't access member-only areas
   - Brand portals, pro sections not analyzed
   - Manually verify if these exist

3. **Subdomains**: Only crawls main domain
   - blog.example.com separate from example.com
   - Specify subdomain URLs separately if needed

4. **Language**: English-only content detection
   - International sites may need localization

### Best Practices

1. **Start Small**: Use --max-pages 10 for testing
2. **Review Results**: Check example URLs to verify accuracy
3. **Manual Verification**: Spot-check 2-3 competitor URLs
4. **Run Quarterly**: Websites change, re-verify every 3 months

---

## What This Means for Clients

### Before (AI-Only Analysis)
> "AI doesn't mention you for how-to queries. Competitors appear 62% of the time."
>
> **Assumed recommendation**: Create how-to content
> **Risk**: You might already have it, or competitors might not

### After (Website-Verified Analysis)
> "✅ VERIFIED GAP: How-to content
>
> - Your site: ✗ No how-to pages found
> - Charlotte Tilbury: ✓ 8 how-to pages (examples: apply-eyeshadow, smoky-eye)
> - Huda Beauty: ✓ 12 tutorial pages (examples: cut-crease, halo-eye)
> - Pat McGrath: ✓ 6 technique guides
>
> **Verified recommendation**: Create how-to content - 3/5 competitors have this, you don't"
> **Evidence**: We checked. This is a real gap.

### Impact

- **Higher confidence** in recommendations
- **Specific examples** to learn from (competitor URLs)
- **No wasted effort** on content you already have
- **Prioritize real gaps** over AI assumptions

---

## Future Enhancements

1. **Screenshot Capture**: Save visual proof of competitor pages
2. **Content Quality Scoring**: Not just "exists" but "how good is it?"
3. **Keyword Density Analysis**: What topics competitors emphasize
4. **Backlink Discovery**: Where competitors get citations from
5. **Update Frequency Detection**: How often competitors publish
6. **Mobile vs Desktop**: Different content on different devices
7. **Schema.org Detection**: Which sites use structured data (better for AI)

---

## Summary

**This solves the original system's biggest flaw**: blindly trusting AI without verification.

Now you can confidently tell clients:
- ✅ "We verified competitors actually have this content"
- ✅ "We checked your site - this content is missing"
- ✅ "Here are specific examples to study"
- ✅ "These are real gaps, not AI hallucinations"

**The recommendations went from assumptions to facts.**
