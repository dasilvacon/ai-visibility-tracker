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
from api_clients.perplexity_client import PerplexityClient
from api_clients.gemini_client import GeminiClient
from api_clients.serpapi_client import SerpAPIClient
from api_clients.copilot_client import CopilotClient
from database.prompts_db import PromptsDatabase
from tracking.results_tracker import ResultsTracker
from reporting.report_generator import ReportGenerator
from prompt_generator.generator import PromptGenerator
from analysis.visibility_scorer import VisibilityScorer
from analysis.fanout_collector import FanoutCollector
from analysis.topic_cluster_analyzer import TopicClusterAnalyzer
from analysis.competitor_analyzer import CompetitorAnalyzer
from analysis.gap_analyzer import GapAnalyzer
from analysis.source_analyzer import SourceAnalyzer
from analysis.head_to_head_analyzer import HeadToHeadAnalyzer
from analysis.citation_classifier import CitationClassifier
from analysis.composite_scorer import CompositeScorer
from analysis.sentiment_analyzer import SentimentAnalyzer
from reporting.html_report_generator import HTMLReportGenerator
from reporting.csv_exporter import CSVExporter
from reporting.pdf_exporter import PDFExporter


class VisibilityTracker:
    """Main orchestrator for visibility tracking."""

    def __init__(self, config_path: str, brand_config_path: str = None):
        """
        Initialize the visibility tracker.

        Args:
            config_path: Path to configuration file
            brand_config_path: Path to brand config file (for per-client isolation)
        """
        self.config = self._load_config(config_path)
        self.clients = {}
        self._initialize_clients()

        # Extract client_slug and brand_config if provided
        self.client_slug = None
        self.brand_config = {}
        if brand_config_path and os.path.exists(brand_config_path):
            try:
                with open(brand_config_path, 'r') as f:
                    self.brand_config = json.load(f)
                brand_name = self.brand_config.get('brand', {}).get('name', '')
                self.client_slug = brand_name.lower().replace(' ', '_')
                print(f"✓ Client identified: {self.client_slug}")
            except Exception as e:
                print(f"⚠️ Could not extract client from brand config: {e}")

        # Initialize components with per-client isolation
        reports_dir = self.config.get('output', {}).get('reports_directory', 'data/reports')

        if self.client_slug:
            # Per-client isolated paths
            self.results_tracker = ResultsTracker(client_slug=self.client_slug)
            self.reports_dir = os.path.join(reports_dir, self.client_slug)
        else:
            # Fallback to legacy shared path (for backwards compatibility)
            results_dir = self.config.get('output', {}).get('results_directory', 'data/results')
            self.results_tracker = ResultsTracker(client_slug='_legacy', base_dir=results_dir)
            self.reports_dir = reports_dir

        os.makedirs(self.reports_dir, exist_ok=True)
        self.report_generator = ReportGenerator(self.reports_dir)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file or Streamlit secrets."""
        # Try loading from config file first
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)

        # Fallback to Streamlit secrets (for Cloud Run deployment)
        try:
            import streamlit as st
            api_keys = dict(st.secrets.get('api_keys', {}))
            if api_keys:
                print("✓ Loading config from Streamlit secrets")
                azure_cfg = dict(st.secrets.get('azure_openai', {}))
                return {
                    'api_keys': api_keys,
                    'models': {
                        # gpt-4.1: non-reasoning model. We tried gpt-5 (reasoning)
                        # and it consumed the entire max_completion_tokens budget
                        # on hidden chain-of-thought, leaving zero tokens for
                        # visible output. 100% of openai responses came back
                        # empty (finish_reason='length', completion_tokens=1000,
                        # response_text=''). gpt-4.1 returns full text directly,
                        # which is what brand-visibility tracking actually needs:
                        # the answer a real ChatGPT.com user would see.
                        'openai': 'gpt-4.1',
                        'anthropic': 'claude-sonnet-4-6',
                        'perplexity': 'sonar',
                        'gemini': 'gemini-2.5-flash',
                        'serpapi': 'google_ai_overview',
                        'copilot': azure_cfg.get('deployment', 'gpt-5.4-mini')
                    },
                    'azure_openai': azure_cfg,
                    'testing': {
                        'default_temperature': 0.7,
                        'max_tokens': 1000,
                        'timeout_seconds': 30
                    },
                    'output': {
                        'results_directory': 'data/results',
                        'reports_directory': 'data/reports'
                    }
                }
        except Exception as e:
            print(f"Could not load Streamlit secrets: {e}")

        # Fallback to environment variables (for subprocess calls from dashboard)
        api_keys = {
            'openai': os.getenv('OPENAI_API_KEY', ''),
            'anthropic': os.getenv('ANTHROPIC_API_KEY', ''),
            'perplexity': os.getenv('PERPLEXITY_API_KEY', ''),
            'gemini': os.getenv('GEMINI_API_KEY', ''),
            'serpapi': os.getenv('SERPAPI_API_KEY', ''),
            'copilot': os.getenv('AZURE_OPENAI_API_KEY', '')
        }
        # Filter out empty values
        api_keys = {k: v for k, v in api_keys.items() if v}

        if api_keys:
            print("✓ Loading config from environment variables")
            # Also pull structured Azure config from env (set by run_report.py)
            azure_cfg = {
                k: v for k, v in {
                    'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', ''),
                    'deployment': os.getenv('AZURE_OPENAI_DEPLOYMENT', ''),
                    'api_version': os.getenv('AZURE_OPENAI_API_VERSION', ''),
                }.items() if v
            }
            return {
                'api_keys': api_keys,
                'models': {
                    # See note at line ~103 — gpt-4.1 (non-reasoning) instead
                    # of gpt-5 (reasoning) so we get visible response text
                    # rather than empty completions.
                    'openai': 'gpt-4.1',
                    'anthropic': 'claude-sonnet-4-6',
                    'perplexity': 'sonar',
                    'gemini': 'gemini-2.5-flash',
                    'serpapi': 'google_ai_overview',
                    'copilot': azure_cfg.get('deployment') or 'gpt-5.4-mini'
                },
                'azure_openai': azure_cfg,
                'testing': {
                    'default_temperature': 0.7,
                    'max_tokens': 1000,
                    'timeout_seconds': 30
                },
                'output': {
                    'results_directory': 'data/results',
                    'reports_directory': 'data/reports'
                }
            }

        print(f"Error: Config file not found at {config_path}")
        print("Please copy config/config.template.json to config/config.json and add your API keys.")
        sys.exit(1)

    def _initialize_clients(self) -> None:
        """Initialize API clients for available platforms."""
        api_keys = self.config.get('api_keys', {})
        models = self.config.get('models', {})

        # OpenAI
        if api_keys.get('openai') and not api_keys['openai'].startswith('YOUR_'):
            try:
                self.clients['openai'] = OpenAIClient(
                    api_key=api_keys['openai'],
                    model=models.get('openai', 'gpt-5'),
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
                    model=models.get('anthropic', 'claude-sonnet-4-6'),
                    config=self.config
                )
                print("✓ Anthropic client initialized")
            except Exception as e:
                print(f"✗ Failed to initialize Anthropic client: {e}")

        # Perplexity
        if api_keys.get('perplexity') and not api_keys['perplexity'].startswith('YOUR_'):
            try:
                self.clients['perplexity'] = PerplexityClient(
                    api_key=api_keys['perplexity'],
                    model=models.get('perplexity', 'sonar'),
                    config=self.config
                )
                print("✓ Perplexity client initialized")
            except Exception as e:
                print(f"✗ Failed to initialize Perplexity client: {e}")

        # Gemini
        if api_keys.get('gemini') and not api_keys['gemini'].startswith('YOUR_'):
            try:
                self.clients['gemini'] = GeminiClient(
                    api_key=api_keys['gemini'],
                    model=models.get('gemini', 'gemini-2.5-flash'),
                    config=self.config
                )
                print("✓ Gemini client initialized")
            except Exception as e:
                print(f"✗ Failed to initialize Gemini client: {e}")

        # Google AI Overviews (via SerpAPI)
        serpapi_key = api_keys.get('serpapi') or os.getenv('SERPAPI_API_KEY', '')
        if serpapi_key and not serpapi_key.startswith('YOUR_'):
            try:
                self.clients['google_ai_overview'] = SerpAPIClient(
                    api_key=serpapi_key,
                    model='google_ai_overview',
                    config=self.config
                )
                print("✓ Google AI Overviews client initialized (via SerpAPI)")
            except Exception as e:
                print(f"✗ Failed to initialize SerpAPI client: {e}")

        # Microsoft Copilot (via Azure OpenAI)
        copilot_key = api_keys.get('copilot') or api_keys.get('azure_openai') or os.getenv('AZURE_OPENAI_API_KEY', '')
        if copilot_key and not copilot_key.startswith('YOUR_'):
            try:
                self.clients['copilot'] = CopilotClient(
                    api_key=copilot_key,
                    model=models.get('copilot', 'gpt-5.4-mini'),
                    config=self.config
                )
                print("✓ Microsoft Copilot client initialized")
            except Exception as e:
                print(f"✗ Failed to initialize Copilot client: {e}")

        if not self.clients:
            print("Error: No API clients could be initialized. Please check your config.json")
            sys.exit(1)

    def _get_completed_tests(self) -> set:
        """
        Get set of (prompt_id, platform) tuples already tested in this run.
        Used for resume capability — skips prompts that were already tested.

        Returns:
            Set of (prompt_id, platform) tuples
        """
        existing = self.results_tracker.load_results_summary()
        return {(r['prompt_id'], r['platform']) for r in existing if r.get('prompt_id') and r.get('platform')}

    def run_tests(self, prompts_file: str, platforms: List[str] = None,
                  force_rerun: bool = False) -> List[Dict[str, Any]]:
        """
        Run visibility tests on prompts. Supports resume — skips prompts
        that already have results from a previous interrupted run.

        Args:
            prompts_file: Path to prompts CSV file
            platforms: List of platforms to test (None = all available)
            force_rerun: If True, ignore existing test data and re-run every
                prompt against every platform. Use when underlying test data
                is bad (e.g. previous run used a broken model and stored
                empty responses). Adds full API spend cost — only use when
                needed.

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

        # Check for existing results (resume support).
        # When force_rerun=True we skip the resume check entirely and
        # re-run every (prompt, platform) combination from scratch.
        if force_rerun:
            print(f"\n⚠️  FORCE RERUN: ignoring existing test data and re-running every prompt × platform")
            completed = set()
        else:
            completed = self._get_completed_tests()
        total_expected = len(prompts) * len(test_platforms)

        if completed:
            print(f"\n⚡ RESUME MODE: Found {len(completed)} existing results out of {total_expected} total")
            print(f"   Skipping already-tested prompt+platform combinations")

        remaining = 0
        for prompt in prompts:
            for platform in test_platforms:
                if (prompt['prompt_id'], platform) not in completed:
                    remaining += 1

        if remaining == 0:
            print(f"\n✓ All {total_expected} tests already completed! Nothing to do.")
            # Return existing results so reports can be generated
            return [{'already_complete': True}]

        print(f"Testing on platforms: {', '.join(test_platforms)}")
        print(f"Total: {total_expected} | Already done: {len(completed)} | Remaining: {remaining}\n")

        # Run tests
        all_results = []
        skipped = 0
        tested = 0
        for i, prompt in enumerate(prompts, 1):
            prompt_has_work = any(
                (prompt['prompt_id'], p) not in completed
                for p in test_platforms
            )

            if not prompt_has_work:
                skipped += len(test_platforms)
                continue

            print(f"[{i}/{len(prompts)}] Testing prompt: {prompt['prompt_id']}")

            for platform in test_platforms:
                # Skip if already tested
                if (prompt['prompt_id'], platform) in completed:
                    skipped += 1
                    continue

                client = self.clients[platform]
                print(f"  → {platform}...", end=" ", flush=True)

                # Add prompt metadata to result (including cluster fields if present)
                metadata = {
                    'persona': prompt['persona'],
                    'category': prompt['category'],
                    'intent_type': prompt['intent_type'],
                    'notes': prompt['notes']
                }

                # Pass through topic cluster metadata for fan-out analysis
                for cluster_field in ('topic_cluster_id', 'cluster_role', 'cluster_topic', 'fanout_angle'):
                    if cluster_field in prompt:
                        metadata[cluster_field] = prompt[cluster_field]

                result = client.test_prompt(
                    prompt_id=prompt['prompt_id'],
                    prompt_text=prompt['prompt_text'],
                    expected_score=prompt['expected_visibility_score'],
                    metadata=metadata
                )

                # Log result
                test_id = self.results_tracker.log_result(result)
                all_results.append(result)
                tested += 1

                if result['success']:
                    print(f"✓ {result['latency_seconds']}s")
                else:
                    print(f"✗ {result.get('error', 'Unknown error')}")

        print(f"\n✓ Completed {tested} new tests (skipped {skipped} already done)")
        print(f"✓ Total results for this client: {len(completed) + tested}")

        # Collect real fan-out queries from Gemini grounding metadata
        if self.client_slug and all_results:
            try:
                fanout_collector = FanoutCollector(client_slug=self.client_slug)
                fanout_stats = fanout_collector.collect_from_results(all_results)
                if fanout_stats['new_queries'] > 0:
                    fanout_collector.save()
                    print(f"\n🔍 Fan-out collection: {fanout_stats['new_queries']} real Google sub-queries captured")
                    print(f"   Topics with fan-out data: {fanout_stats['topics_with_fanout']}")
                    print(f"   Total unique queries: {fanout_stats['total_unique_queries']}")
                else:
                    print("\n🔍 Fan-out collection: No new Gemini fan-out queries in this run")
            except Exception as e:
                print(f"\n⚠️ Fan-out collection failed (non-critical): {e}")

        return all_results

    def check_test_completeness(self, prompts_file: str, platforms: List[str] = None) -> dict:
        """
        Check if all prompts have been tested on all platforms.

        Args:
            prompts_file: Path to prompts CSV file
            platforms: Platforms to check (None = all available)

        Returns:
            Dict with 'complete' bool, 'total', 'done', 'missing' counts
        """
        prompts_db = PromptsDatabase(prompts_file)
        prompts = prompts_db.load_prompts()
        test_platforms = platforms or list(self.clients.keys())
        completed = self._get_completed_tests()

        total = len(prompts) * len(test_platforms)
        done = sum(1 for p in prompts for plat in test_platforms if (p['prompt_id'], plat) in completed)
        missing = total - done

        return {
            'complete': missing == 0,
            'total': total,
            'done': done,
            'missing': missing,
            'prompts': len(prompts),
            'platforms': len(test_platforms)
        }

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

        # Initialize generator with brand context and quality floor
        generator = PromptGenerator(
            personas_file=personas_file,
            keywords_file=keywords_file,
            api_client=api_client,
            use_ai_generation=use_ai,
            brand_config=self.brand_config,
            quality_floor=60.0
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

        # Handle both old format (list) and new format (dict with 'expected' and 'discovered').
        # Also extract per-competitor aliases so detection can match acronyms and
        # common variations (e.g., "Canadian Centre for Caregiving Excellence" → "CCCE").
        competitors_raw = brand_config.get('competitors', [])
        competitors = []
        competitor_aliases: Dict[str, List[str]] = {}

        if isinstance(competitors_raw, dict):
            # New format: {'expected': [...], 'discovered': [...]}
            # `expected` is the human-curated competitor list we trust for
            # scoring and reporting. `discovered` is auto-populated each run by
            # a regex in CompetitorAnalyzer.find_all_brands_mentioned — it's
            # noisy (geographic terms like "Ukraine", product-category nouns
            # like "Palette", verbs like "Give" all get captured). Feeding
            # `discovered` straight back into the scorer turns those false
            # positives into "competitors" that dominate the competitive
            # landscape table.
            #
            # Fix: only use discovered entries that have been manually reviewed
            # and flipped to promoted_to_expected=True. Everything else stays
            # in brand_config as a staging area for Tiffany's review but does
            # NOT feed the scorer.
            expected = competitors_raw.get('expected', [])
            discovered = competitors_raw.get('discovered', [])
            promoted_discovered = [
                c for c in discovered
                if isinstance(c, dict) and c.get('promoted_to_expected') is True
            ]
            all_competitors = expected + promoted_discovered

            for comp in all_competitors:
                if isinstance(comp, dict) and 'name' in comp:
                    competitors.append(comp['name'])
                    aliases = comp.get('aliases') or []
                    if aliases:
                        competitor_aliases[comp['name']] = list(aliases)
                elif isinstance(comp, str):
                    competitors.append(comp)
        elif isinstance(competitors_raw, list):
            # Old format: direct list
            for comp in competitors_raw:
                if isinstance(comp, str):
                    competitors.append(comp)
                elif isinstance(comp, dict):
                    name = comp.get('name', comp.get('website', ''))
                    competitors.append(name)
                    aliases = comp.get('aliases') or []
                    if aliases and name:
                        competitor_aliases[name] = list(aliases)

        print(f"\nBrand: {brand_name}")
        print(f"Competitors: {', '.join(competitors)}")

        # Load test results
        print("\nLoading test results...")
        results = self.results_tracker.load_results_summary()

        if not results:
            print("Error: No test results found. Run tests first.")
            return {}

        # Load full results (with response text). Phase 3 (per-competitor
        # source lens) and Phase 4 (positioning profile) BOTH need response_text
        # on each scored result. If load_full_result silently fails, both
        # sections render to nothing and there's no signal in logs.
        print("Loading detailed responses...")
        full_results = []
        load_failures = 0
        first_failure_id = None
        for result in results:
            test_id = result.get('test_id')
            if not test_id:
                continue
            try:
                full_result = self.results_tracker.load_full_result(test_id)
                full_results.append(full_result)
            except FileNotFoundError:
                load_failures += 1
                if first_failure_id is None:
                    first_failure_id = test_id
            except Exception as e:
                load_failures += 1
                if first_failure_id is None:
                    first_failure_id = test_id
                print(f"⚠️  load_full_result({test_id}) raised {type(e).__name__}: {e}")

        if load_failures:
            print(
                f"⚠️  {load_failures}/{len(results)} test results failed to load "
                f"(first failure: {first_failure_id}). "
                f"Phase 3 source-tier and Phase 4 positioning sections "
                f"need response_text — they will render empty for these results."
            )

        # Diagnostic: how many of the loaded full_results have response_text?
        # This is the single most important Phase 3+4 health signal.
        with_response = sum(
            1 for r in full_results
            if (r.get('response_text') or r.get('response'))
        )
        print(
            f"   Loaded {len(full_results)} full results, "
            f"{with_response} have response_text "
            f"({100*with_response/max(len(full_results),1):.0f}%)"
        )

        if not full_results:
            print("Error: No detailed results found.")
            print(f"  Results dir: {self.results_tracker.results_dir}")
            print(f"  Summary results loaded: {len(results)}")
            return {}

        print(f"Analyzing {len(full_results)} test results...")

        # Debug: Show sample of what we're analyzing
        if full_results:
            sample = full_results[0]
            print(f"  Sample prompt: {sample.get('prompt_text', 'N/A')[:60]}...")
            response_preview = sample.get('response_text', '')[:100] if sample.get('response_text') else 'NO RESPONSE'
            print(f"  Sample response: {response_preview}...")

        # Load known_sources and industry_keywords from brand_config
        known_sources = brand_config.get('known_sources', [])
        source_categories = brand_config.get('source_categories', {})

        # Initialize analyzers
        scorer = VisibilityScorer(
            brand_name=brand_name,
            brand_aliases=brand_aliases,
            competitor_names=competitors,
            competitor_aliases=competitor_aliases,
            known_sources=known_sources
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
        source_analysis = source_analyzer.analyze_sources(scored_results, brand_config=brand_config)

        # Topic cluster / fan-out analysis
        topic_cluster_analysis = None
        has_cluster_data = any(r.get('metadata', {}).get('cluster_topic') for r in scored_results)
        if has_cluster_data:
            print("3.7. Analyzing topic cluster fan-out visibility...")
            try:
                tc_analyzer = TopicClusterAnalyzer(brand_name=brand_name)
                topic_cluster_analysis = tc_analyzer.analyze(scored_results)
                summary = topic_cluster_analysis.get('summary', {})
                print(f"   ✓ {summary.get('total_topics', 0)} topics analyzed")
                recs = topic_cluster_analysis.get('content_recommendations', [])
                print(f"   ✓ {len(recs)} content recommendations")
                sys_gaps = summary.get('systematic_angle_gaps', [])
                if sys_gaps:
                    print(f"   ⚠️  Systematic weak spots: {', '.join(sys_gaps)}")

                # Also collect real fan-out queries if available
                if self.client_slug:
                    try:
                        fanout_collector = FanoutCollector(client_slug=self.client_slug)
                        fanout_stats = fanout_collector.collect_from_results(scored_results)
                        if fanout_stats['new_queries'] > 0:
                            fanout_collector.save()
                            word_analysis = fanout_collector.analyze_word_additions()
                            topic_cluster_analysis['real_fanout'] = {
                                'stats': fanout_stats,
                                'word_additions': word_analysis,
                                'topics': fanout_collector.get_all_fanout_topics()
                            }
                            print(f"   ✓ {fanout_stats['new_queries']} real Google fan-out queries collected")
                    except Exception as e:
                        print(f"   ⚠️ Fan-out collection skipped: {e}")
            except Exception as e:
                print(f"   ⚠️ Topic cluster analysis failed: {e}")
        else:
            print("3.7. Topic cluster analysis: No cluster data in prompts (skipped)")

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

        # Generate GEO/AEO quick wins (legacy — kept for fallback)
        geo_aeo_wins = gap_analyzer.generate_geo_aeo_quick_wins(scored_results)
        action_plan['geo_aeo_quick_wins'] = geo_aeo_wins

        # Generate evidence-based competitor intelligence recommendations
        print("5.5. Researching competitor strategies...")
        try:
            from src.analysis.competitor_researcher import CompetitorResearcher
            comp_researcher = CompetitorResearcher(
                brand_name=brand_name,
                brand_config=brand_config
            )
            competitor_intelligence = comp_researcher.analyze_competitors(scored_results)
            action_plan['competitor_intelligence'] = competitor_intelligence
            evidence_recs = competitor_intelligence.get('evidence_recommendations', [])
            if evidence_recs:
                print(f"   ✓ {len(evidence_recs)} evidence-based recommendations generated")
                for i, rec in enumerate(evidence_recs, 1):
                    print(f"     {i}. {rec['competitor']}: {rec['strategy']}")
            else:
                print("   ⚠️ No evidence-based recommendations (insufficient competitor data)")
        except Exception as e:
            print(f"   ⚠️ Competitor research skipped: {str(e)}")
            action_plan['competitor_intelligence'] = {}

        # Generate prioritized audiences and content gaps for new "Where to Focus" section
        prioritized_audiences = gap_analyzer.get_prioritized_audiences(scored_results)
        prioritized_content_gaps = gap_analyzer.get_prioritized_content_gaps(scored_results)
        gap_analysis['prioritized_audiences'] = prioritized_audiences
        gap_analysis['prioritized_content_gaps'] = prioritized_content_gaps

        # Compute per-platform breakdown for time-series tracking. We aggregate
        # scored_results by platform so HistoricalTracker can store snapshot
        # data per platform — used by the dashboard's platform trend lines
        # and the "what changed this week" panel.
        platform_results: Dict[str, Dict[str, Any]] = {}
        try:
            from collections import defaultdict
            buckets = defaultdict(lambda: {
                'total_prompts': 0,
                'brand_mentions': 0,
                'competitor_mentions': 0,
                'prominence_sum': 0.0,
                'prominence_count': 0,
            })
            for r in scored_results:
                platform = r.get('platform', 'unknown')
                vis = r.get('visibility', {}) or {}
                buckets[platform]['total_prompts'] += 1
                if vis.get('brand_mentioned'):
                    buckets[platform]['brand_mentions'] += 1
                if vis.get('competitors_mentioned'):
                    buckets[platform]['competitor_mentions'] += 1
                prom = vis.get('prominence_score')
                if prom is not None:
                    buckets[platform]['prominence_sum'] += float(prom)
                    buckets[platform]['prominence_count'] += 1

            for platform, b in buckets.items():
                vis_rate = (b['brand_mentions'] / b['total_prompts'] * 100) if b['total_prompts'] else 0.0
                avg_prom = (b['prominence_sum'] / b['prominence_count']) if b['prominence_count'] else 0.0
                platform_results[platform] = {
                    'total_prompts': b['total_prompts'],
                    'brand_mentions': b['brand_mentions'],
                    'competitor_mentions': b['competitor_mentions'],
                    'visibility_rate': vis_rate,
                    'avg_prominence': avg_prom,
                }
        except Exception as e:
            print(f"⚠️  Could not compute per-platform breakdown: {e}")
            platform_results = {}

        # Save historical tracking data and get trend data for momentum labels
        trend_data = None
        if self.client_slug:
            try:
                from src.tracking.historical_tracker import HistoricalTracker
                hist_tracker = HistoricalTracker(client_slug=self.client_slug)
                hist_tracker.save_monthly_scores(
                    client_name=brand_name,
                    visibility_summary=visibility_summary,
                    platform_results=platform_results or None,
                )
                print(f"✓ Historical tracking data saved (with {len(platform_results)} platforms)")
                # Get trend data for momentum labels in report
                trend_data = hist_tracker.get_latest_vs_previous(brand_name)
                if trend_data:
                    print(f"   ✓ Trend comparison: {trend_data.get('trend', 'new')}")
                # Also log week-over-week delta if we have it (informational only — the
                # report consumers don't use this yet; the dashboard panel will)
                wow = hist_tracker.get_week_over_week_delta(brand_name)
                if wow:
                    vis_d = wow['metrics']['visibility_rate']['delta']
                    print(f"   ✓ Week-over-week visibility delta: {vis_d:+.1f}%")
            except Exception as e:
                print(f"⚠️  Could not save historical data: {str(e)}")

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
            self.reports_dir,
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

        # Run competitive analysis features
        print("6. Running competitive analysis features...")

        # Extract brand domains and competitor domains from config
        brand_website = brand_config['brand'].get('website', '')
        brand_domains = [brand_website.replace('https://', '').replace('http://', '')] if brand_website else []

        competitor_domains_dict = {}
        for comp in competitors_raw:
            if isinstance(comp, dict) and 'name' in comp and 'website' in comp:
                comp_name = comp['name']
                comp_website = comp['website']
                comp_domain = comp_website.replace('https://', '').replace('http://', '')
                competitor_domains_dict[comp_name] = [comp_domain]

        # Head-to-head analysis
        h2h_analyzer = HeadToHeadAnalyzer(
            brand_name=brand_name,
            competitor_names=competitors
        )
        h2h_results = h2h_analyzer.aggregate_head_to_head_results(scored_results)
        print(f"   ✓ Found {h2h_results['total_comparison_queries']} comparison queries")
        print(f"   ✓ Win rate: {h2h_results['overall_win_rate']:.1f}%")

        # Citation classification
        citation_classifier = CitationClassifier(
            brand_domains=brand_domains,
            competitor_domains=competitor_domains_dict
        )
        citation_stats = citation_classifier.classify_all_sources(scored_results, source_categories=source_categories)
        print(f"   ✓ Citation authority: {citation_stats['citation_authority_score']:.1f}/100")

        # Sentiment analysis
        sentiment_analyzer = SentimentAnalyzer(
            brand_name=brand_name,
            competitor_names=competitors
        )
        sentiment_analysis = sentiment_analyzer.analyze_sentiment(scored_results)
        sentiment_score = sentiment_analysis.get('overall_score', {}).get('score', 0)
        print(f"   ✓ Sentiment score: {sentiment_score:.1f}/100 ({sentiment_analysis['overall_score']['grade']})")

        # Composite scoring
        composite_scorer = CompositeScorer()
        composite_metrics = {
            'visibility_rate': visibility_summary.get('brand_visibility_rate', 0),
            'prominence_rate': visibility_summary.get('average_prominence_score', 0) * 10,
            'competitive_win_rate': h2h_results.get('overall_win_rate', 0),
            'total_comparison_queries': h2h_results.get('total_comparison_queries', 0),
            'citation_authority_score': citation_stats.get('citation_authority_score', 0),
            'total_citations': citation_stats.get('total_citations', 0),
            'positioning_quality_score': 70  # Default
        }
        scorecard = composite_scorer.create_full_scorecard(composite_metrics)
        maturity_stage = scorecard['maturity_stage']
        print(f"   ✓ Overall maturity: {maturity_stage} ({scorecard['composite_score']:.0f}/100)")

        # Generate HTML report
        print("7. Generating HTML report with competitive features...")
        html_generator = HTMLReportGenerator(self.reports_dir)

        html_report_path = html_generator.generate_report(
            brand_name=brand_name,
            visibility_summary=visibility_summary,
            competitive_analysis=competitive_analysis,
            gap_analysis=gap_analysis,
            action_plan=action_plan,
            scored_results=scored_results,
            composite_scorecard=scorecard,
            head_to_head_results=h2h_results,
            citation_stats=citation_stats,
            sentiment_analysis=sentiment_analysis,
            website_verification=website_verification,
            source_analysis=source_analysis,
            trend_data=trend_data
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
            'topic_cluster_analysis': topic_cluster_analysis,
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
        lines.append("Where are brands being mentioned? This section shows which third-party sites,")
        lines.append("publications, and communities are citing which brands in AI responses.")
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
                    lines.append(f"   Top competitor: {source.get('top_competitor')} ({source.get('top_competitor_mentions', 0)} mentions)")
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
                    lines.append(f"   Top competitor: {target.get('top_competitor')} ({target.get('top_competitor_mentions', 0)} mentions)")

                # Suggested action
                lines.append("")
                lines.append("   ACTION TO TAKE:")
                if 'reddit' in target['source'].lower():
                    lines.append("   → Increase Reddit presence - answer questions, engage authentically")
                    lines.append("   → Consider sponsoring relevant subreddit threads")
                elif 'youtube' in target['source'].lower() or 'channel' in target['source'].lower():
                    lines.append("   → Identify relevant creators in your space and open an outreach conversation")
                    lines.append("   → Explore sponsored content, interviews, or collaboration opportunities")
                elif any(word in target['source'].lower() for word in ['blog', 'review', 'magazine', 'journal']):
                    lines.append("   → Pitch editorial features, case studies, or guest contributions")
                    lines.append("   → Offer subject-matter expertise or client stories relevant to their audience")
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
        exports = {}

        # Initialize exporters with per-client reports directory
        csv_exporter = CSVExporter(self.reports_dir)
        pdf_exporter = PDFExporter(self.reports_dir)

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
        choices=['openai', 'anthropic', 'perplexity', 'gemini', 'google_ai_overview', 'copilot'],
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

    # Local-iteration helpers (Patch 6).
    #
    # --regenerate-only: skip prompt-running and any API calls. Just re-load
    # existing test data from disk, re-run scoring + analysis, and rebuild
    # the HTML report. Cuts the iteration loop on copy/layout changes from
    # ~45-90 min (deploy weekly job → wait → pull) to under a minute.
    #
    # --client SLUG: auto-resolves --brand-config to data/{slug}/{slug}_brand_config.json
    # so we don't have to type the full path every time.
    parser.add_argument(
        '--regenerate-only',
        action='store_true',
        help=(
            'Re-generate analysis + report from existing local test data only. '
            'No API calls, no GCS, no prompt-running. Use this for fast '
            'iteration on report copy/layout changes. Pair with --client SLUG.'
        )
    )
    # Patch 8: bypass the resume-from-existing-tests logic. Use when the
    # underlying test data is bad (e.g. previous run used a broken model
    # config and stored empty responses). Adds full API spend cost.
    # Also accepts FORCE_RERUN=true env var for use in Cloud Run Jobs.
    parser.add_argument(
        '--force-rerun',
        action='store_true',
        help=(
            'Re-run every prompt × platform from scratch, ignoring existing '
            'test data. Use only when underlying data is bad — adds full '
            'API spend cost. Also activatable via FORCE_RERUN=true env var.'
        )
    )
    parser.add_argument(
        '--client',
        default=None,
        help=(
            'Client slug (e.g. "ontario_caregiver_organization"). When set, '
            'auto-resolves --brand-config to data/{slug}/{slug}_brand_config.json. '
            'Convenient with --regenerate-only.'
        )
    )

    args = parser.parse_args()

    # If --client was passed, auto-resolve brand-config path
    if args.client:
        resolved_brand_config = f'data/{args.client}/{args.client}_brand_config.json'
        if not os.path.exists(resolved_brand_config):
            print(f"✗ --client {args.client!r}: brand config not found at {resolved_brand_config}")
            print(f"  Available clients in data/:")
            try:
                for entry in sorted(os.listdir('data')):
                    candidate = f'data/{entry}/{entry}_brand_config.json'
                    if os.path.exists(candidate):
                        print(f"    {entry}")
            except FileNotFoundError:
                pass
            sys.exit(1)
        args.brand_config = resolved_brand_config

    # Initialize tracker with brand config for per-client isolation
    tracker = VisibilityTracker(args.config, brand_config_path=args.brand_config)

    # --regenerate-only short-circuits all the prompt-running paths. We just
    # want analysis + report from whatever's already on disk.
    if args.regenerate_only:
        print(f"📊 Regenerating report from local data (no API calls)")
        print(f"   brand_config: {args.brand_config}")
        if not args.client:
            print(f"   ⚠️  --client not set — make sure --brand-config points at the right client")

        result = tracker.analyze_results(args.brand_config)
        if not result:
            print("\n✗ analyze_results returned empty. Common causes:")
            print("   • No test data in data/results/{slug}/results_summary.csv")
            print("   • brand_config path is wrong")
            sys.exit(1)

        # Surface where the HTML landed so the user can open it immediately
        reports_dir = tracker.config.get('output', {}).get('reports_directory', 'data/reports')
        client_slug = args.client or 'unknown'
        print(f"\n✓ Report regenerated. Look in:")
        print(f"   {reports_dir}/{client_slug}/  (per-client dir, if isolation is on)")
        print(f"   {reports_dir}/                (legacy shared dir)")
        sys.exit(0)

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

    elif args.analyze and not args.generate_prompts and not args.prompts:
        # Standalone analysis of existing results
        tracker.analyze_results(args.brand_config)

    elif args.report_only:
        # Only generate reports
        tracker.generate_reports()
    else:
        # Run tests (with automatic resume if partial results exist)
        # FORCE_RERUN env var (or --force-rerun flag) bypasses resume and
        # re-runs every prompt — used when underlying test data is bad and
        # we need fresh API responses.
        force_rerun = args.force_rerun or os.environ.get('FORCE_RERUN', '').lower() in ('1', 'true', 'yes')
        results = tracker.run_tests(args.prompts, args.platforms, force_rerun=force_rerun)

        if results:
            # Only generate reports if ALL prompts are tested
            completeness = tracker.check_test_completeness(args.prompts, args.platforms)
            if completeness['complete']:
                print(f"\n✓ All {completeness['total']} tests complete — generating reports")
                tracker.generate_reports()

                # Run analysis if requested
                if args.analyze:
                    tracker.analyze_results(args.brand_config)
            else:
                print(f"\n⚠️ Test incomplete: {completeness['done']}/{completeness['total']} done, {completeness['missing']} remaining")
                print("Reports will NOT be generated until all prompts are tested.")
                print("Re-run this command to resume and complete the remaining tests.")
                sys.exit(2)  # Exit code 2 = incomplete (not failed, just needs resume)


if __name__ == '__main__':
    main()
