#!/usr/bin/env python3
"""
AI Visibility Tracker - Main runner script.

Tests prompts across multiple AI platforms and tracks visibility scores.
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api_clients.openai_client import OpenAIClient
from api_clients.anthropic_client import AnthropicClient
from database.prompts_db import PromptsDatabase
from tracking.results_tracker import ResultsTracker
from reporting.report_generator import ReportGenerator
from prompt_generator.generator import PromptGenerator
from analysis.visibility_scorer import VisibilityScorer
from analysis.competitor_analyzer import CompetitorAnalyzer
from analysis.gap_analyzer import GapAnalyzer
from analysis.source_analyzer import SourceAnalyzer
from reporting.html_report_generator import HTMLReportGenerator
from reporting.csv_exporter import CSVExporter
from reporting.pdf_exporter import PDFExporter


class VisibilityTracker:
    """Main orchestrator for visibility tracking."""

    def __init__(self, config_path: str):
        """
        Initialize the visibility tracker.

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.clients = {}
        self._initialize_clients()

        # Initialize components
        results_dir = self.config.get('output', {}).get('results_directory', 'data/results')
        reports_dir = self.config.get('output', {}).get('reports_directory', 'data/reports')

        self.results_tracker = ResultsTracker(results_dir)
        self.report_generator = ReportGenerator(reports_dir)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if not os.path.exists(config_path):
            print(f"Error: Config file not found at {config_path}")
            print("Please copy config/config.template.json to config/config.json and add your API keys.")
            sys.exit(1)

        with open(config_path, 'r') as f:
            return json.load(f)

    def _initialize_clients(self) -> None:
        """Initialize API clients for available platforms."""
        api_keys = self.config.get('api_keys', {})
        models = self.config.get('models', {})

        # OpenAI
        if api_keys.get('openai') and not api_keys['openai'].startswith('YOUR_'):
            try:
                self.clients['openai'] = OpenAIClient(
                    api_key=api_keys['openai'],
                    model=models.get('openai', 'gpt-4'),
                    config=self.config
                )
                print("✓ OpenAI client initialized")
            except Exception as e:
                print(f"✗ Failed to initialize OpenAI client: {e}")

        # Anthropic
        if api_keys.get('anthropic') and not api_keys['anthropic'].startswith('YOUR_'):
            try:
                self.clients['anthropic'] = AnthropicClient(
                    api_key=api_keys['anthropic'],
                    model=models.get('anthropic', 'claude-3-5-sonnet-20241022'),
                    config=self.config
                )
                print("✓ Anthropic client initialized")
            except Exception as e:
                print(f"✗ Failed to initialize Anthropic client: {e}")

        if not self.clients:
            print("Error: No API clients could be initialized. Please check your config.json")
            sys.exit(1)

    def run_tests(self, prompts_file: str, platforms: List[str] = None) -> List[Dict[str, Any]]:
        """
        Run visibility tests on prompts.

        Args:
            prompts_file: Path to prompts CSV file
            platforms: List of platforms to test (None = all available)

        Returns:
            List of test results
        """
        # Load prompts
        prompts_db = PromptsDatabase(prompts_file)
        prompts = prompts_db.load_prompts()

        if not prompts:
            print("Error: No prompts found in database.")
            return []

        print(f"\nLoaded {len(prompts)} prompts from database")

        # Determine which platforms to test
        if platforms:
            test_platforms = [p for p in platforms if p in self.clients]
        else:
            test_platforms = list(self.clients.keys())

        if not test_platforms:
            print("Error: No valid platforms specified.")
            return []

        print(f"Testing on platforms: {', '.join(test_platforms)}")
        print(f"\nRunning {len(prompts) * len(test_platforms)} tests...\n")

        # Run tests
        all_results = []
        for i, prompt in enumerate(prompts, 1):
            print(f"[{i}/{len(prompts)}] Testing prompt: {prompt['prompt_id']}")

            for platform in test_platforms:
                client = self.clients[platform]
                print(f"  → {platform}...", end=" ", flush=True)

                # Add prompt metadata to result
                metadata = {
                    'persona': prompt['persona'],
                    'category': prompt['category'],
                    'intent_type': prompt['intent_type'],
                    'notes': prompt['notes']
                }

                result = client.test_prompt(
                    prompt_id=prompt['prompt_id'],
                    prompt_text=prompt['prompt_text'],
                    expected_score=prompt['expected_visibility_score'],
                    metadata=metadata
                )

                # Log result
                test_id = self.results_tracker.log_result(result)
                all_results.append(result)

                if result['success']:
                    print(f"✓ {result['latency_seconds']}s")
                else:
                    print(f"✗ {result.get('error', 'Unknown error')}")

        print(f"\n✓ Completed {len(all_results)} tests")
        return all_results

    def generate_reports(self) -> None:
        """Generate reports from logged results."""
        print("\nGenerating reports...")

        results = self.results_tracker.load_results_summary()

        if not results:
            print("No results found to generate reports.")
            return

        # Quick summary
        self.report_generator.print_quick_summary(results)

        # Summary report
        summary_path = self.report_generator.generate_summary_report(results)
        print(f"✓ Summary report: {summary_path}")

        # Platform comparison
        comparison_path = self.report_generator.generate_platform_comparison(results)
        print(f"✓ Platform comparison: {comparison_path}")

    def generate_prompts(self, personas_file: str, keywords_file: str,
                        output_file: str, count: int = 1000,
                        use_ai: bool = True) -> str:
        """
        Generate prompts using the prompt generator.

        Args:
            personas_file: Path to personas JSON file
            keywords_file: Path to keywords CSV file
            output_file: Path to output CSV file
            count: Number of prompts to generate
            use_ai: Whether to use AI API for generation

        Returns:
            Path to generated prompts file
        """
        print("\n" + "="*60)
        print("PROMPT GENERATION")
        print("="*60)

        # Get an API client for generation (prefer Anthropic, fall back to OpenAI)
        api_client = None
        if use_ai:
            if 'anthropic' in self.clients:
                api_client = self.clients['anthropic']
                print("Using Anthropic API for generation")
            elif 'openai' in self.clients:
                api_client = self.clients['openai']
                print("Using OpenAI API for generation")
            else:
                print("Warning: No API client available, using template-based generation")
                use_ai = False

        # Initialize generator
        generator = PromptGenerator(
            personas_file=personas_file,
            keywords_file=keywords_file,
            api_client=api_client,
            use_ai_generation=use_ai
        )

        # Generate prompts
        prompts = generator.generate_prompts(total_count=count, competitor_ratio=0.3)

        # Save to CSV
        generator.save_to_csv(output_file)

        # Generate summary report
        report_file = output_file.replace('.csv', '_summary.txt')
        generator.generate_summary_report(report_file)

        return output_file

    def analyze_results(self, brand_config_path: str) -> Dict[str, Any]:
        """
        Run visibility analysis on test results.

        Args:
            brand_config_path: Path to brand configuration JSON file

        Returns:
            Dictionary with complete analysis results
        """
        print("\n" + "="*60)
        print("VISIBILITY ANALYSIS")
        print("="*60)

        # Load brand config
        if not os.path.exists(brand_config_path):
            print(f"Error: Brand config file not found at {brand_config_path}")
            print("Please copy data/brand_config_template.json and customize it.")
            return {}

        with open(brand_config_path, 'r') as f:
            brand_config = json.load(f)

        brand_name = brand_config['brand']['name']
        brand_aliases = brand_config['brand'].get('aliases', [])

        # Handle both old format (list of strings) and new format (list of dicts with 'name' and 'website')
        competitors_raw = brand_config.get('competitors', [])
        competitors = []
        for comp in competitors_raw:
            if isinstance(comp, str):
                competitors.append(comp)
            elif isinstance(comp, dict):
                competitors.append(comp.get('name', comp.get('website', '')))

        print(f"\nBrand: {brand_name}")
        print(f"Competitors: {', '.join(competitors)}")

        # Load test results
        print("\nLoading test results...")
        results = self.results_tracker.load_results_summary()

        if not results:
            print("Error: No test results found. Run tests first.")
            return {}

        # Load full results (with response text)
        print("Loading detailed responses...")
        full_results = []
        for result in results:
            test_id = result.get('test_id')
            if test_id:
                try:
                    full_result = self.results_tracker.load_full_result(test_id)
                    full_results.append(full_result)
                except:
                    pass

        if not full_results:
            print("Error: No detailed results found.")
            return {}

        print(f"Analyzing {len(full_results)} test results...")

        # Initialize analyzers
        scorer = VisibilityScorer(
            brand_name=brand_name,
            brand_aliases=brand_aliases,
            competitor_names=competitors
        )

        comp_analyzer = CompetitorAnalyzer(brand_name)
        gap_analyzer = GapAnalyzer(brand_name)
        source_analyzer = SourceAnalyzer()

        # Score all results
        print("\n1. Scoring brand visibility...")
        scored_results = scorer.score_all_results(full_results)
        visibility_summary = scorer.get_visibility_summary(scored_results)

        # Analyze competitors
        print("2. Analyzing competitive landscape...")
        competitive_analysis = comp_analyzer.analyze_competitive_landscape(scored_results)

        # Find all brands mentioned (not just tracked competitors)
        all_brands_analysis = comp_analyzer.find_all_brands_mentioned(scored_results, competitors)
        competitive_analysis['all_brands'] = all_brands_analysis

        # Update brand_config with discovered competitors
        if brand_config_path and all_brands_analysis.get('for_brand_config'):
            try:
                import sys
                sys.path.insert(0, 'src')
                from src.data.brand_config_manager import BrandConfigManager

                manager = BrandConfigManager()
                config = manager.load_config(brand_config_path)
                config = manager.update_discovered_competitors(
                    config,
                    all_brands_analysis['for_brand_config']
                )
                manager.save_config(brand_config_path, config)
                print("✓ Updated brand_config with discovered competitors")
            except Exception as e:
                print(f"⚠️  Could not update brand_config with discovered competitors: {str(e)}")

        # Identify gaps
        print("3. Identifying visibility gaps...")
        gap_analysis = gap_analyzer.identify_gaps(scored_results)

        # Analyze sources and citations
        print("3.5. Analyzing sources and citations...")
        source_analysis = source_analyzer.analyze_sources(scored_results)

        # Run website verification if URLs are available
        website_verification = None
        brand_website = brand_config['brand'].get('website')
        competitor_urls = []
        for comp in competitors_raw:
            if isinstance(comp, dict) and 'website' in comp:
                competitor_urls.append(comp['website'])

        if brand_website and competitor_urls:
            print("4. Verifying content gaps on actual websites...")
            try:
                from src.analysis.website_analyzer import analyze_brand_and_competitors
                website_verification = analyze_brand_and_competitors(
                    brand_url=brand_website,
                    competitor_urls=competitor_urls,
                    max_pages=30  # Quick scan - 30 pages per site
                )
                print("✓ Website verification complete")
            except Exception as e:
                print(f"⚠️  Website verification skipped: {str(e)}")
                website_verification = None
        else:
            print("⚠️  Website verification skipped: No URLs in brand config")

        # Generate action plan (with website verification if available)
        print("5. Creating action plan...")
        action_plan = gap_analyzer.generate_action_plan(scored_results, website_verification)

        # Generate GEO/AEO quick wins
        geo_aeo_wins = gap_analyzer.generate_geo_aeo_quick_wins(scored_results)
        action_plan['geo_aeo_quick_wins'] = geo_aeo_wins

        # Generate prioritized audiences and content gaps for new "Where to Focus" section
        prioritized_audiences = gap_analyzer.get_prioritized_audiences(scored_results)
        prioritized_content_gaps = gap_analyzer.get_prioritized_content_gaps(scored_results)
        gap_analysis['prioritized_audiences'] = prioritized_audiences
        gap_analysis['prioritized_content_gaps'] = prioritized_content_gaps

        # Print summary
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print(f"\nBrand Visibility Rate: {visibility_summary['brand_visibility_rate']:.1f}%")
        print(f"Average Prominence Score: {visibility_summary['average_prominence_score']}/10")
        print(f"Competitor Mention Rate: {visibility_summary['competitor_mention_rate']:.1f}%")

        if visibility_summary['competitors_encountered']:
            print(f"\nCompetitors Encountered: {', '.join(visibility_summary['competitors_encountered'])}")

        print(f"\nTop Opportunities:")
        for i, opp in enumerate(action_plan['quick_wins'][:3], 1):
            print(f"  {i}. {opp['recommendation']} (Impact: {opp['impact_score']:.1f})")

        # Save analysis report
        analysis_report_path = os.path.join(
            self.config.get('output', {}).get('reports_directory', 'data/reports'),
            f'visibility_analysis_{brand_name.replace(" ", "_")}.txt'
        )

        self._save_analysis_report(
            analysis_report_path,
            brand_name,
            visibility_summary,
            competitive_analysis,
            gap_analysis,
            action_plan,
            scored_results,
            source_analysis
        )

        print(f"\n✓ Analysis report saved to: {analysis_report_path}")

        # Generate HTML report
        print("Generating HTML report...")
        html_generator = HTMLReportGenerator(
            self.config.get('output', {}).get('reports_directory', 'data/reports')
        )

        html_report_path = html_generator.generate_report(
            brand_name=brand_name,
            visibility_summary=visibility_summary,
            competitive_analysis=competitive_analysis,
            gap_analysis=gap_analysis,
            action_plan=action_plan,
            scored_results=scored_results,
            website_verification=website_verification,
            source_analysis=source_analysis
        )

        print(f"✓ HTML report saved to: {html_report_path}")

        # Generate all exports
        print("\n📊 Generating exports...")
        exports = self._generate_all_exports(
            brand_name=brand_name,
            visibility_summary=visibility_summary,
            competitive_analysis=competitive_analysis,
            gap_analysis=gap_analysis,
            source_analysis=source_analysis,
            scored_results=scored_results
        )

        print("\n✅ All exports generated:")
        for export_type, filepath in exports.items():
            if filepath:
                print(f"   • {export_type}: {filepath}")

        return {
            'visibility_summary': visibility_summary,
            'competitive_analysis': competitive_analysis,
            'gap_analysis': gap_analysis,
            'action_plan': action_plan,
            'scored_results': scored_results,
            'source_analysis': source_analysis,
            'text_report_path': analysis_report_path,
            'html_report_path': html_report_path,
            'exports': exports
        }

    def _save_analysis_report(self, report_path: str, brand_name: str,
                             visibility_summary: Dict[str, Any],
                             competitive_analysis: Dict[str, Any],
                             gap_analysis: Dict[str, Any],
                             action_plan: Dict[str, Any],
                             scored_results: List[Dict[str, Any]],
                             source_analysis: Dict[str, Any]) -> None:
        """Save detailed analysis report with DaSilva voice and examples."""
        lines = []
        lines.append("="*80)
        lines.append(f"AI VISIBILITY ANALYSIS - {brand_name}")
        lines.append("="*80)
        lines.append(f"Generated: {__import__('datetime').datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        lines.append("")

        # Section 1: THE BOTTOM LINE
        lines.append("="*80)
        lines.append("SECTION 1: THE BOTTOM LINE")
        lines.append("="*80)
        lines.append("")

        vis_rate = visibility_summary['brand_visibility_rate']
        prom_score = visibility_summary['average_prominence_score']

        # Status
        if vis_rate < 20:
            status = f"{brand_name} isn't showing up. You're visible in {vis_rate:.1f}% of responses."
        elif vis_rate < 40:
            status = f"{brand_name} shows up sometimes. You're visible in {vis_rate:.1f}% of responses."
        elif vis_rate < 60:
            status = f"{brand_name} has decent visibility. You're in {vis_rate:.1f}% of responses."
        else:
            status = f"{brand_name} is visible. You're in {vis_rate:.1f}% of responses."

        lines.append(status)
        lines.append("")

        # vs top competitor
        if competitive_analysis.get('top_competitors'):
            top_comp = competitive_analysis['top_competitors'][0]
            gap = top_comp['mention_rate'] - vis_rate
            lines.append(f"Your top competitor: {top_comp['name']} at {top_comp['mention_rate']:.1f}%")
            lines.append(f"The gap: {gap:.1f} percentage points")
        lines.append("")

        # Calculate persona breakdown from scored_results
        from collections import defaultdict
        persona_stats = defaultdict(lambda: {'mentions': 0, 'total': 0})
        for result in scored_results:
            persona = result.get('metadata', {}).get('persona', 'Unknown')
            persona_stats[persona]['total'] += 1
            if result.get('visibility', {}).get('brand_mentioned', False):
                persona_stats[persona]['mentions'] += 1

        persona_breakdown = []
        for persona, stats in persona_stats.items():
            if stats['total'] > 0:
                persona_breakdown.append({
                    'persona': persona,
                    'sample_size': stats['total'],
                    'mentions': stats['mentions'],
                    'visibility_rate': (stats['mentions'] / stats['total']) * 100
                })

        persona_breakdown.sort(key=lambda x: x['visibility_rate'], reverse=True)

        # Strongest and weakest by persona
        if persona_breakdown:
            lines.append("Your strongest persona: " + persona_breakdown[0]['persona'] +
                        f" ({persona_breakdown[0]['visibility_rate']:.1f}%)")
            lines.append("Your weakest persona: " + persona_breakdown[-1]['persona'] +
                        f" ({persona_breakdown[-1]['visibility_rate']:.1f}%)")
        lines.append("")
        lines.append("="*80)
        lines.append("")

        # Section 2: WHERE YOU'RE LOSING
        lines.append("="*80)
        lines.append("SECTION 2: WHERE YOU'RE LOSING")
        lines.append("="*80)
        lines.append("")

        # Find underperforming personas with examples
        for persona_data in persona_breakdown[-3:]:  # Bottom 3 personas
            persona = persona_data['persona']
            vis_rate_p = persona_data['visibility_rate']

            lines.append(f"→ {persona}")
            lines.append(f"   Tested: {persona_data['sample_size']} | Mentioned: {persona_data['mentions']} times | Rate: {vis_rate_p:.1f}%")
            lines.append("")

            # Find examples of losses for this persona
            persona_losses = [r for r in scored_results
                            if r.get('metadata', {}).get('persona') == persona
                            and not r.get('visibility', {}).get('brand_mentioned', False)
                            and r.get('visibility', {}).get('competitors_mentioned')
                            and r.get('prompt_text', '').strip()][:2]

            if persona_losses:
                lines.append("   Examples where you lost:")
                for loss in persona_losses:
                    prompt = loss.get('prompt_text', '').strip()[:100]
                    competitors = loss.get('visibility', {}).get('competitors_mentioned', [])
                    if prompt:
                        lines.append(f"   • Prompt: \"{prompt}{'...' if len(loss.get('prompt_text', '')) > 100 else ''}\"")
                        lines.append(f"     AI mentioned instead: {', '.join(competitors)}")
                lines.append("")

            # Specific fix
            lines.append(f"   Fix: Create content targeting {persona}. Focus on their pain points.")
            lines.append("")

        lines.append("="*80)
        lines.append("")

        # Section 3: WHERE YOU'RE WINNING
        lines.append("="*80)
        lines.append("SECTION 3: WHERE YOU'RE WINNING")
        lines.append("="*80)
        lines.append("")

        # Find top performing personas with examples
        for persona_data in persona_breakdown[:2]:  # Top 2 personas
            persona = persona_data['persona']
            vis_rate_p = persona_data['visibility_rate']

            if vis_rate_p > 15:  # Only show if actually winning
                lines.append(f"→ {persona}")
                lines.append(f"   Tested: {persona_data['sample_size']} | Mentioned: {persona_data['mentions']} times | Rate: {vis_rate_p:.1f}%")
                lines.append("")

                # Find examples of wins
                persona_wins = [r for r in scored_results
                              if r.get('metadata', {}).get('persona') == persona
                              and r.get('visibility', {}).get('brand_mentioned', False)
                              and r.get('prompt_text', '').strip()][:2]

                if persona_wins:
                    lines.append("   Examples where you won:")
                    for win in persona_wins:
                        prompt = win.get('prompt_text', '').strip()
                        prom = win.get('visibility', {}).get('prominence_score', 0)
                        response_snippet = win.get('response_text', '').strip()[:150]
                        if prompt:
                            lines.append(f"   • Prompt: \"{prompt[:100]}{'...' if len(prompt) > 100 else ''}\"")
                            lines.append(f"     Prominence: {prom:.1f}/10")
                            if response_snippet:
                                lines.append(f"     AI said: \"{response_snippet}{'...' if len(win.get('response_text', '')) > 150 else ''}\"")
                    lines.append("")

                lines.append(f"   Why you're winning: You have strong content for this persona.")
                lines.append(f"   Replicate this: Apply the same content strategy to other personas.")
                lines.append("")

        lines.append("="*80)
        lines.append("")

        # Section 4: ALL COMPETITORS
        lines.append("="*80)
        lines.append("SECTION 4: ALL COMPETITORS")
        lines.append("="*80)
        lines.append("")

        lines.append("Listed Competitors (you're tracking):")
        if competitive_analysis.get('top_competitors'):
            for i, comp in enumerate(competitive_analysis['top_competitors']):
                label = ""
                if i == 0:
                    label = " → Your top competitor"
                elif comp['mention_rate'] >= 10:
                    label = " → Rising threat"
                lines.append(f"  • {comp['name']}: {comp['mention_rate']:.1f}% | {comp['mentions']} mentions{label}")
        lines.append("")

        # All Brands Mentioned
        all_brands = competitive_analysis.get('all_brands', {})
        if all_brands.get('unlisted_brands'):
            lines.append("Other Brands That Showed Up (unlisted):")
            for brand in all_brands['unlisted_brands'][:10]:
                warning = " ⚠️ Consider tracking" if brand['should_track'] else ""
                lines.append(f"  • {brand['name']}: {brand['mention_rate']:.1f}% ({brand['mentions']} mentions){warning}")
            lines.append("")

            if all_brands.get('recommendations'):
                lines.append("⚠️ Update your competitor list. These brands appear frequently:")
                for rec in all_brands['recommendations']:
                    lines.append(f"   → Add {rec['name']} to tracking ({rec['mentions']} mentions)")
        else:
            lines.append("No unlisted brands found. All mentioned brands are on your tracking list.")

        lines.append("")
        lines.append("="*80)
        lines.append("")

        # Section 5: WHAT TO DO FIRST
        lines.append("="*80)
        lines.append("SECTION 5: WHAT TO DO FIRST")
        lines.append("="*80)
        lines.append("")

        lines.append("📊 HOW TO READ THIS REPORT")
        lines.append("")
        lines.append("Your Visibility Rate: How often you appear when people ask AI about luxury eyeshadow")
        lines.append("Competitor Rate: How often your competitors appear")
        lines.append("Gap: The difference (negative = you're losing ground)")
        lines.append("Missed Mentions: Estimated additional times per month you'd appear if you close the gap")
        lines.append("")
        lines.append("🔴 HIGH PRIORITY = Biggest gaps + most queries = biggest opportunity")
        lines.append("🟡 MEDIUM PRIORITY = Good opportunities to tackle after HIGH items")
        lines.append("🟢 LOW PRIORITY = Smaller gains, handle if resources allow")
        lines.append("")
        lines.append("="*80)
        lines.append("")

        # Organize opportunities by type
        all_opps = gap_analysis['priority_opportunities'][:10]
        content_opps = [opp for opp in all_opps if opp.get('group') == 'content']
        audience_opps = [opp for opp in all_opps if opp.get('group') == 'audience']

        # CONTENT TO CREATE
        if content_opps:
            lines.append("="*80)
            lines.append("CONTENT TO CREATE")
            lines.append("="*80)
            lines.append("")

            for i, opp in enumerate(content_opps, 1):
                priority_label = f"{opp.get('priority_emoji', '')} {opp.get('priority', 'MEDIUM')} PRIORITY"
                content_type = opp.get('content_type', opp['target'])

                lines.append(f"{i}. {content_type} {priority_label}")
                lines.append(f"   Gap: You show up {opp['current_visibility']:.1f}% | Competitors show up {opp.get('competitor_avg', 0):.1f}%")
                lines.append(f"   Missing: ~{opp.get('missed_monthly', 0)} mentions per month")
                lines.append("")

                # Show actual examples from test
                example_prompts = opp.get('example_prompts', [])
                if example_prompts:
                    lines.append("   Example questions you're missing:")
                    for ex in example_prompts:
                        prompt = ex.get('prompt', '')
                        if prompt:
                            # Truncate if too long
                            display_prompt = prompt if len(prompt) <= 80 else prompt[:77] + "..."
                            lines.append(f"   - \"{display_prompt}\"")

                    competitor_who_won = opp.get('competitor_who_won', 'competitors')
                    lines.append(f"   These are real questions where {competitor_who_won} appeared but you didn't.")
                    lines.append("")

                # Create section
                lines.append("   Create:")
                for action in opp.get('specific_actions', []):
                    lines.append(f"   • {action}")
                lines.append("")

                # Where to put it
                lines.append(f"   Put it: {opp.get('where_to_implement', 'Product pages, Blog, FAQ')}")

                # Target keywords
                keywords = opp.get('target_keywords', [])
                if keywords:
                    keywords_str = '", "'.join(keywords)
                    lines.append(f"   Keywords: \"{keywords_str}\"")
                lines.append("")

            lines.append("="*80)
            lines.append("")

        # AUDIENCES TO TARGET
        if audience_opps:
            lines.append("="*80)
            lines.append("AUDIENCES TO TARGET")
            lines.append("="*80)
            lines.append("")

            for i, opp in enumerate(audience_opps, 1):
                priority_label = f"{opp.get('priority_emoji', '')} {opp.get('priority', 'MEDIUM')} PRIORITY"

                lines.append(f"{i}. {opp['target']} {priority_label}")
                lines.append(f"   Gap: You show up {opp['current_visibility']:.1f}% | Competitors show up {opp.get('competitor_avg', 0):.1f}%")
                lines.append(f"   Missing: ~{opp.get('missed_monthly', 0)} mentions per month")
                if opp.get('value_prop'):
                    lines.append(f"   Why they matter: {opp.get('value_prop')}")
                lines.append("")

                # Show actual examples from test
                example_prompts = opp.get('example_prompts', [])
                if example_prompts:
                    lines.append("   Example questions you're missing:")
                    for ex in example_prompts:
                        prompt = ex.get('prompt', '')
                        if prompt:
                            # Truncate if too long
                            display_prompt = prompt if len(prompt) <= 80 else prompt[:77] + "..."
                            lines.append(f"   - \"{display_prompt}\"")

                    competitor_who_won = opp.get('competitor_who_won', 'competitors')
                    lines.append(f"   These are real questions where {competitor_who_won} appeared but you didn't.")
                    lines.append("")

                # Create section
                lines.append("   Create:")
                for action in opp.get('specific_actions', []):
                    lines.append(f"   • {action}")
                lines.append("")

                # Where to put it
                lines.append(f"   Put it: {opp.get('where_to_implement', 'Product pages, Blog')}")

                # Target keywords
                keywords = opp.get('target_keywords', [])
                if keywords:
                    keywords_str = '", "'.join(keywords)
                    lines.append(f"   Keywords: \"{keywords_str}\"")
                lines.append("")

            lines.append("="*80)
            lines.append("")

        lines.append("")

        # Section 6: SOURCES & CITATIONS
        lines.append("="*80)
        lines.append("SECTION 6: SOURCES & CITATIONS")
        lines.append("="*80)
        lines.append("")
        lines.append("Where are brands being mentioned? This section shows which third-party sites")
        lines.append("(Sephora, Reddit, beauty blogs) are citing which brands in AI responses.")
        lines.append("")

        total_sources = source_analysis.get('total_unique_sources', 0)
        brand_sources = source_analysis.get('sources_mentioning_brand', 0)
        gap_opportunities = source_analysis.get('gap_opportunities', 0)

        lines.append(f"Total unique sources found: {total_sources}")
        lines.append(f"Sources mentioning your brand: {brand_sources}")
        lines.append(f"Gap opportunities (competitors only): {gap_opportunities}")
        lines.append("")

        # Sources with your brand
        sources_with_brand = source_analysis.get('sources_with_your_brand', [])
        if sources_with_brand:
            lines.append("TOP SOURCES MENTIONING YOUR BRAND:")
            lines.append("")
            for i, source in enumerate(sources_with_brand[:5], 1):
                lines.append(f"{i}. {source['source']}")
                lines.append(f"   Total appearances: {source['total_appearances']}")
                lines.append(f"   Your brand: {source['mentions_your_brand']} mentions ({source['brand_mention_rate']}%)")
                lines.append(f"   Competitors: {source['competitor_count']} mentions ({source['competitor_rate']}%)")
                if source.get('top_competitor'):
                    lines.append(f"   Top competitor: {source['top_competitor']} ({source['top_competitor_mentions']} mentions)")
                if source.get('example_urls'):
                    lines.append(f"   Example: {source['example_urls'][0]}")
                lines.append("")
        else:
            lines.append("⚠️  No sources found mentioning your brand.")
            lines.append("")

        # Gap opportunities - sources with competitors but not you
        targets = source_analysis.get('recommended_targets', [])
        if targets:
            lines.append("="*80)
            lines.append("SOURCES YOU'RE MISSING (Competitors Present)")
            lines.append("="*80)
            lines.append("")
            lines.append("These are high-value sources where competitors are being cited but you're not.")
            lines.append("Reach out to these sites for features, reviews, or backlinks.")
            lines.append("")

            for i, target in enumerate(targets[:10], 1):
                lines.append(f"{i}. {target['source']} - Opportunity Score: {target['opportunity_score']:.0f}/100")
                lines.append(f"   Your brand: {target['mentions_your_brand']} mentions ({target['brand_mention_rate']}%)")
                lines.append(f"   Competitors: {target['competitor_count']} mentions ({target['competitor_rate']}%)")
                if target.get('top_competitor'):
                    lines.append(f"   Top competitor: {target['top_competitor']} ({target['top_competitor_mentions']} mentions)")

                # Suggested action
                lines.append("")
                lines.append("   ACTION TO TAKE:")
                if 'reddit' in target['source'].lower():
                    lines.append("   → Increase Reddit presence - answer questions, engage authentically")
                    lines.append("   → Consider sponsoring relevant subreddit threads")
                elif 'youtube' in target['source'].lower() or 'channel' in target['source'].lower():
                    lines.append("   → Send PR packages to top beauty YouTubers")
                    lines.append("   → Reach out for sponsored reviews or collaborations")
                elif any(word in target['source'].lower() for word in ['blog', 'temptalia', 'review']):
                    lines.append("   → Reach out for product review features")
                    lines.append("   → Send PR package with your best products")
                else:
                    lines.append("   → Reach out for backlink opportunities")
                    lines.append("   → Request product features or reviews")

                if target.get('example_urls'):
                    lines.append(f"   Example URL: {target['example_urls'][0]}")
                lines.append("")

            lines.append("="*80)
            lines.append("")
            lines.append(f"📊 Full source list exported to: sources_{brand_name.replace(' ', '_')}.csv")
            lines.append("")
        else:
            lines.append("✓ Good news! You're present in all sources where competitors appear.")
            lines.append("")

        lines.append("="*80)
        lines.append("")

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def _generate_all_exports(self, brand_name: str,
                            visibility_summary: Dict[str, Any],
                            competitive_analysis: Dict[str, Any],
                            gap_analysis: Dict[str, Any],
                            source_analysis: Dict[str, Any],
                            scored_results: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Generate all export formats.

        Args:
            brand_name: Brand name
            visibility_summary: Visibility summary data
            competitive_analysis: Competitive analysis data
            gap_analysis: Gap analysis data
            source_analysis: Source analysis data
            scored_results: List of scored results

        Returns:
            Dictionary mapping export type to file path
        """
        reports_dir = self.config.get('output', {}).get('reports_directory', 'data/reports')
        exports = {}

        # Initialize exporters
        csv_exporter = CSVExporter(reports_dir)
        pdf_exporter = PDFExporter(reports_dir)

        # 1. Source List CSV (for PR team)
        try:
            exports['Sources CSV'] = csv_exporter.export_sources(source_analysis, brand_name)
        except Exception as e:
            print(f"   ⚠️  Failed to generate Sources CSV: {e}")
            exports['Sources CSV'] = None

        # 2. Raw Data CSV (for analysts)
        try:
            exports['Raw Data CSV'] = csv_exporter.export_raw_data(scored_results, brand_name)
        except Exception as e:
            print(f"   ⚠️  Failed to generate Raw Data CSV: {e}")
            exports['Raw Data CSV'] = None

        # 3. Action Plan CSV (for content team)
        try:
            exports['Action Plan CSV'] = csv_exporter.export_action_plan(gap_analysis, brand_name)
        except Exception as e:
            print(f"   ⚠️  Failed to generate Action Plan CSV: {e}")
            exports['Action Plan CSV'] = None

        # 4. Competitors CSV
        try:
            exports['Competitors CSV'] = csv_exporter.export_competitors(
                competitive_analysis, visibility_summary, brand_name
            )
        except Exception as e:
            print(f"   ⚠️  Failed to generate Competitors CSV: {e}")
            exports['Competitors CSV'] = None

        # 5. Personas CSV
        try:
            exports['Personas CSV'] = csv_exporter.export_personas(
                scored_results, gap_analysis, brand_name
            )
        except Exception as e:
            print(f"   ⚠️  Failed to generate Personas CSV: {e}")
            exports['Personas CSV'] = None

        # 6. Executive Summary PDF
        try:
            exports['Executive PDF'] = pdf_exporter.generate_executive_summary(
                brand_name, visibility_summary, competitive_analysis,
                gap_analysis, source_analysis
            )
        except Exception as e:
            print(f"   ⚠️  Failed to generate Executive PDF: {e}")
            exports['Executive PDF'] = None

        return exports


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AI Visibility Tracker - Test prompts across multiple AI platforms"
    )
    parser.add_argument(
        '--config',
        default='config/config.json',
        help='Path to configuration file (default: config/config.json)'
    )
    parser.add_argument(
        '--prompts',
        default='data/prompts_template.csv',
        help='Path to prompts CSV file (default: data/prompts_template.csv)'
    )
    parser.add_argument(
        '--platforms',
        nargs='+',
        choices=['openai', 'anthropic', 'perplexity', 'deepseek', 'grok'],
        help='Platforms to test (default: all available)'
    )
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Only generate reports from existing results'
    )

    # Prompt generation arguments
    parser.add_argument(
        '--generate-prompts',
        action='store_true',
        help='Generate prompts using AI'
    )
    parser.add_argument(
        '--personas',
        default='data/personas_template.json',
        help='Path to personas JSON file (default: data/personas_template.json)'
    )
    parser.add_argument(
        '--keywords',
        default='data/keywords_template.csv',
        help='Path to keywords CSV file (default: data/keywords_template.csv)'
    )
    parser.add_argument(
        '--output',
        default='data/generated_prompts.csv',
        help='Output file for generated prompts (default: data/generated_prompts.csv)'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=100,
        help='Number of prompts to generate (default: 100)'
    )
    parser.add_argument(
        '--no-ai',
        action='store_true',
        help='Use template-based generation instead of AI'
    )
    parser.add_argument(
        '--full-pipeline',
        action='store_true',
        help='Generate prompts and then test them in sequence'
    )

    # Analysis arguments
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Run visibility analysis on test results'
    )
    parser.add_argument(
        '--brand-config',
        default='data/brand_config_template.json',
        help='Path to brand configuration JSON file (default: data/brand_config_template.json)'
    )

    args = parser.parse_args()

    # Initialize tracker
    tracker = VisibilityTracker(args.config)

    if args.generate_prompts or args.full_pipeline:
        # Generate prompts
        output_file = tracker.generate_prompts(
            personas_file=args.personas,
            keywords_file=args.keywords,
            output_file=args.output,
            count=args.count,
            use_ai=not args.no_ai
        )

        if args.full_pipeline:
            # Run tests on generated prompts
            print("\n" + "="*60)
            print("RUNNING VISIBILITY TESTS")
            print("="*60)
            results = tracker.run_tests(output_file, args.platforms)

            if results:
                tracker.generate_reports()

                # Run analysis if requested
                if args.analyze:
                    tracker.analyze_results(args.brand_config)

    elif args.analyze and not args.generate_prompts:
        # Standalone analysis of existing results
        tracker.analyze_results(args.brand_config)

    elif args.report_only:
        # Only generate reports
        tracker.generate_reports()
    else:
        # Run tests
        results = tracker.run_tests(args.prompts, args.platforms)

        if results:
            # Generate reports
            tracker.generate_reports()

            # Run analysis if requested
            if args.analyze:
                tracker.analyze_results(args.brand_config)


if __name__ == '__main__':
    main()
