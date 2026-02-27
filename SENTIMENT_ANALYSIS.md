# Sentiment Analysis Feature

## What It Measures

**Sentiment Analysis** answers: **"How does the AI describe your brand when it mentions you?"**

This maps directly to the first pillar of AI visibility:

> **Sentiment** — How the AI describes your strengths and weaknesses in the areas that influence buying decisions (e.g., price, quality, reliability, innovation, customer support).

---

## How It Works

When your brand IS mentioned in AI responses, the sentiment analyzer:

### 1. **Extracts All Brand Mentions**
- Finds every response where your brand appears
- Captures the full context around the mention

### 2. **Analyzes Six Key Categories**

Based on factors that influence buying decisions:

#### **Price**
- Positive: affordable, value, worth, reasonable, cost-effective
- Negative: expensive, overpriced, costly, pricey
- Neutral: premium, luxury, investment

#### **Quality**
- Positive: high-quality, excellent, superior, professional, luxurious
- Negative: low-quality, poor, inferior, cheap, inconsistent
- Neutral: quality, formulation, ingredients

#### **Reliability**
- Positive: reliable, consistent, dependable, trustworthy, proven
- Negative: unreliable, inconsistent, unpredictable
- Neutral: brand, company, established

#### **Innovation**
- Positive: innovative, unique, cutting-edge, revolutionary, modern
- Negative: outdated, old-fashioned, behind, basic, generic
- Neutral: technology, formula, approach

#### **Customer Support**
- Positive: excellent service, responsive, helpful, easy returns
- Negative: poor service, unresponsive, difficult, bad support
- Neutral: customer service, support, warranty

#### **Performance**
- Positive: effective, works well, delivers, pigmented, long-wearing
- Negative: ineffective, patchy, fades quickly, chalky
- Neutral: performance, wear, application

### 3. **Scores Each Mention**
- Calculates sentiment score (-100 to +100)
- Categorizes as positive, neutral, or negative
- Tracks frequency of descriptors

### 4. **Compares to Competitors**
- Analyzes sentiment for competitors in same queries
- Identifies where competitors have better/worse sentiment
- Shows category-by-category comparison

---

## What You Get

### Overall Sentiment Score (0-100)
- **70-100 (A):** Excellent - AI describes you very positively
- **60-69 (B):** Good - Mostly positive sentiment
- **50-59 (C):** Average - Mixed sentiment
- **40-49 (D):** Below Average - More negative than positive
- **0-39 (F):** Poor - Predominantly negative sentiment

### Category Breakdown
For each category (price, quality, etc.):
- Score showing positive vs negative language
- Top descriptors used (both positive and negative)
- Number of mentions
- Comparison to competitors

### Key Strengths & Weaknesses
- Top 3 areas where sentiment is strongly positive
- Top 3 areas where sentiment is negative or behind competitors
- Specific examples of language used

### Actionable Recommendations
- Specific content to create to improve sentiment
- Areas to address negative perceptions
- Opportunities to amplify positive sentiment

---

## Example Output

```
Sentiment Analysis for Natasha Denona

Overall Score: 68/100 (B - Good)

✅ Strengths:
1. Quality (Score: 85/100)
   - Descriptors: "high-quality", "luxurious", "professional"
   - 47 positive mentions

2. Innovation (Score: 72/100)
   - Descriptors: "unique", "modern", "cutting-edge"
   - 31 positive mentions

3. Performance (Score: 65/100)
   - Descriptors: "pigmented", "blendable", "long-wearing"
   - 28 positive mentions

⚠️ Weaknesses:
1. Price (Score: -32/100)
   - Descriptors: "expensive", "pricey", "overpriced"
   - 43 negative mentions

2. Customer Support (Score: -12/100)
   - Descriptors: "difficult", "poor service"
   - 8 negative mentions

📊 vs Competitors:
- Quality: +15 points ahead
- Innovation: +8 points ahead
- Price: -28 points behind
- Performance: Equal
- Reliability: +5 points ahead
- Customer Support: -10 points behind

🎯 Recommendations:
1. Create content addressing price perception
   - Show value comparisons vs competitors
   - Highlight product longevity and cost-per-use
   - Feature professional testimonials on investment value

2. Improve customer support visibility
   - Add detailed FAQ sections
   - Feature customer support success stories
   - Highlight return policy and guarantees
```

---

## How to Use This Data

### 1. **Content Strategy**
- If price sentiment is negative, create content showing value
- If quality sentiment is high, amplify it across all content
- Address negative perceptions head-on with evidence

### 2. **Messaging**
- Use the same positive descriptors AI platforms already associate with you
- Counter negative descriptors with specific proof points
- Align your website copy with the language AI uses positively

### 3. **Competitive Positioning**
- Double down on categories where you beat competitors
- Address categories where competitors have better sentiment
- Create comparison content highlighting your strengths

### 4. **Product Marketing**
- Highlight features that drive positive sentiment
- Address concerns that drive negative sentiment
- Use customer testimonials that reinforce positive descriptors

---

## Technical Details

**Runs automatically** when you generate reports:
```bash
./run_natasha_report.sh
```

**Analyzes:**
- Every brand mention in AI responses
- Context around the mention
- Comparison to competitor mentions
- Patterns across platforms (OpenAI, Anthropic, Perplexity, Gemini)

**Output:**
- Included in HTML reports
- Part of executive summary
- Available in raw data CSV

---

## Why This Matters

Traditional SEO focused on **getting mentioned**.

AI visibility is about **how you're described when mentioned**.

Two brands with 80% visibility can have vastly different outcomes:
- **Brand A:** Mentioned 80% of the time, but described as "expensive" and "overpriced"
- **Brand B:** Mentioned 80% of the time, described as "high-quality" and "worth the investment"

**Brand B wins the sale** even though visibility is equal.

Sentiment analysis helps you understand and improve HOW AI describes you, not just IF it mentions you.

---

**Next:** See MESSAGING_ANALYSIS.md for tracking your value propositions
