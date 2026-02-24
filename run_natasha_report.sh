#!/bin/bash
cd /Users/tiffanydasilva/Claude-Projects/ai-visibility-tracker
source venv/bin/activate

echo "🚀 Running Visibility Report for Natasha Denona"
echo "================================================"
echo ""

python main.py \
  --prompts data/generated_prompts.csv \
  --analyze \
  --brand-config data/natasha_denona_brand_config.json

echo ""
echo "✅ Report Complete!"
echo ""
echo "📊 View reports in:"
echo "   - HTML: data/reports/visibility_report_Natasha_Denona.html"
echo "   - PDF:  data/reports/executive_summary_Natasha_Denona.pdf"
echo "   - Text: data/reports/visibility_analysis_Natasha_Denona.txt"
