"""
Website content analyzer for verifying actual content gaps.
Scrapes and analyzes brand and competitor websites to verify recommendations.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Set
import re
from urllib.parse import urljoin, urlparse
import time
from collections import defaultdict


class WebsiteAnalyzer:
    """Analyzes website content to verify content gaps."""

    def __init__(self, user_agent: str = None):
        """
        Initialize the website analyzer.

        Args:
            user_agent: Custom user agent string for requests
        """
        self.user_agent = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})

    def analyze_website(self, base_url: str, max_pages: int = 50,
                       rate_limit: float = 1.0) -> Dict[str, Any]:
        """
        Analyze a website to identify what content types exist.

        Args:
            base_url: Base URL of the website to analyze
            max_pages: Maximum number of pages to crawl
            rate_limit: Seconds to wait between requests

        Returns:
            Dictionary with content analysis
        """
        print(f"\n🔍 Analyzing website: {base_url}")

        pages_analyzed = []
        content_inventory = {
            'educational': [],
            'how_to': [],
            'comparison': [],
            'faq': [],
            'product_info': [],
            'blog': [],
            'reviews': [],
            'guides': [],
            'tutorials': [],
            'about': []
        }

        # Start with base URL
        to_visit = [base_url]
        visited = set()
        pages_crawled = 0

        while to_visit and pages_crawled < max_pages:
            url = to_visit.pop(0)

            if url in visited:
                continue

            try:
                print(f"  Crawling: {url}")
                time.sleep(rate_limit)  # Rate limiting

                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                visited.add(url)
                pages_crawled += 1

                soup = BeautifulSoup(response.content, 'html.parser')

                # Analyze page content
                page_analysis = self._analyze_page(url, soup)
                pages_analyzed.append(page_analysis)

                # Categorize content
                for content_type, urls in page_analysis['content_types'].items():
                    if urls:
                        content_inventory[content_type].append({
                            'url': url,
                            'title': page_analysis['title'],
                            'signals': page_analysis['content_types'][content_type]
                        })

                # Find more pages to crawl (same domain only)
                if pages_crawled < max_pages:
                    links = self._extract_internal_links(url, soup, base_url)
                    for link in links:
                        if link not in visited and link not in to_visit:
                            to_visit.append(link)

            except Exception as e:
                print(f"  ⚠️  Error crawling {url}: {str(e)}")
                continue

        print(f"\n✓ Analyzed {pages_crawled} pages")

        # Summarize findings
        summary = self._summarize_content(content_inventory)

        return {
            'base_url': base_url,
            'pages_analyzed': pages_crawled,
            'content_inventory': content_inventory,
            'summary': summary,
            'detailed_pages': pages_analyzed
        }

    def _analyze_page(self, url: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze a single page to identify content types."""

        # Extract text content
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ''

        # Get all text content
        for script in soup(['script', 'style']):
            script.decompose()
        text_content = soup.get_text().lower()

        # Get headings
        headings = [h.get_text().strip().lower() for h in soup.find_all(['h1', 'h2', 'h3', 'h4'])]

        # Analyze URL structure
        url_lower = url.lower()
        path = urlparse(url).path.lower()

        content_types = {
            'educational': [],
            'how_to': [],
            'comparison': [],
            'faq': [],
            'product_info': [],
            'blog': [],
            'reviews': [],
            'guides': [],
            'tutorials': [],
            'about': []
        }

        # Educational content signals
        educational_signals = [
            'learn', 'guide', 'education', 'tutorial', 'course',
            'what is', 'understanding', 'explained', 'basics'
        ]
        if any(signal in text_content or signal in url_lower for signal in educational_signals):
            content_types['educational'].append('keyword_match')

        # How-to content signals
        howto_signals = [
            'how to', 'how do', 'step by step', 'diy', 'tutorial',
            'instructions', 'guide to'
        ]
        if any(signal in text_content or signal in url_lower for signal in howto_signals):
            content_types['how_to'].append('keyword_match')
        if any('how to' in h for h in headings):
            content_types['how_to'].append('heading_match')

        # Comparison content signals
        comparison_signals = [
            'vs', 'versus', 'compare', 'comparison', 'difference between',
            'which is better', 'alternative'
        ]
        if any(signal in text_content or signal in url_lower for signal in comparison_signals):
            content_types['comparison'].append('keyword_match')

        # FAQ signals
        faq_signals = ['faq', 'frequently asked', 'questions', 'q&a', 'q and a']
        if any(signal in url_lower for signal in faq_signals):
            content_types['faq'].append('url_match')
        if any(signal in text_content for signal in ['frequently asked', 'q&a']):
            content_types['faq'].append('content_match')

        # Product info signals
        product_signals = [
            'product', 'shop', 'buy', 'price', 'purchase',
            'add to cart', 'specifications', 'features'
        ]
        if any(signal in url_lower for signal in product_signals):
            content_types['product_info'].append('url_match')

        # Blog signals
        blog_signals = ['blog', 'article', 'post', 'news']
        if any(signal in url_lower for signal in blog_signals):
            content_types['blog'].append('url_match')

        # Review signals
        review_signals = ['review', 'rating', 'testimonial', 'customer feedback']
        if any(signal in text_content or signal in url_lower for signal in review_signals):
            content_types['reviews'].append('keyword_match')

        # Guide signals
        guide_signals = [
            'guide', 'complete guide', 'ultimate guide', 'beginner',
            'handbook', 'manual'
        ]
        if any(signal in text_content or signal in url_lower for signal in guide_signals):
            content_types['guides'].append('keyword_match')

        # Tutorial signals
        tutorial_signals = ['tutorial', 'lesson', 'workshop', 'training']
        if any(signal in text_content or signal in url_lower for signal in tutorial_signals):
            content_types['tutorials'].append('keyword_match')

        # About/brand info signals
        about_signals = ['about', 'our story', 'who we are', 'mission', 'values']
        if any(signal in url_lower for signal in about_signals):
            content_types['about'].append('url_match')

        return {
            'url': url,
            'title': title_text,
            'headings': headings,
            'content_types': content_types,
            'word_count': len(text_content.split())
        }

    def _extract_internal_links(self, current_url: str, soup: BeautifulSoup,
                               base_domain: str) -> List[str]:
        """Extract internal links from a page."""
        links = []
        base_parsed = urlparse(base_domain)

        for link in soup.find_all('a', href=True):
            href = link['href']

            # Convert relative URLs to absolute
            absolute_url = urljoin(current_url, href)
            parsed = urlparse(absolute_url)

            # Only include links from same domain, skip fragments, files
            if (parsed.netloc == base_parsed.netloc and
                not parsed.fragment and
                not parsed.path.endswith(('.pdf', '.jpg', '.png', '.gif', '.zip'))):
                links.append(absolute_url)

        return list(set(links))  # Remove duplicates

    def _summarize_content(self, content_inventory: Dict[str, List]) -> Dict[str, Any]:
        """Summarize content findings."""
        summary = {}

        for content_type, pages in content_inventory.items():
            summary[content_type] = {
                'exists': len(pages) > 0,
                'page_count': len(pages),
                'example_urls': [p['url'] for p in pages[:3]]  # First 3 examples
            }

        return summary

    def compare_websites(self, brand_analysis: Dict[str, Any],
                        competitor_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare brand website against competitor websites.

        Args:
            brand_analysis: Analysis results for the brand
            competitor_analyses: List of analysis results for competitors

        Returns:
            Dictionary with comparison and verified gaps
        """
        print("\n📊 Comparing website content...")

        verified_gaps = []
        false_positives = []

        content_types = [
            'educational', 'how_to', 'comparison', 'faq',
            'product_info', 'blog', 'reviews', 'guides', 'tutorials'
        ]

        for content_type in content_types:
            brand_has = brand_analysis['summary'][content_type]['exists']
            brand_count = brand_analysis['summary'][content_type]['page_count']

            # Check how many competitors have this content type
            competitors_with_content = []
            for comp_analysis in competitor_analyses:
                if comp_analysis['summary'][content_type]['exists']:
                    competitors_with_content.append({
                        'url': comp_analysis['base_url'],
                        'page_count': comp_analysis['summary'][content_type]['page_count'],
                        'examples': comp_analysis['summary'][content_type]['example_urls']
                    })

            comp_count = len(competitors_with_content)
            total_comps = len(competitor_analyses)

            # Determine if this is a real gap
            if comp_count >= 2 and not brand_has:
                # Multiple competitors have it, brand doesn't = VERIFIED GAP
                verified_gaps.append({
                    'content_type': content_type,
                    'status': 'verified_gap',
                    'brand_has': False,
                    'competitors_with': comp_count,
                    'total_competitors': total_comps,
                    'competitor_examples': competitors_with_content[:2],  # Top 2
                    'recommendation': f'Create {content_type.replace("_", " ")} content',
                    'priority': 'high' if comp_count >= 3 else 'medium'
                })
            elif comp_count >= 2 and brand_has and brand_count < 3:
                # Competitors have more = OPPORTUNITY TO EXPAND
                verified_gaps.append({
                    'content_type': content_type,
                    'status': 'expansion_opportunity',
                    'brand_has': True,
                    'brand_count': brand_count,
                    'competitors_with': comp_count,
                    'total_competitors': total_comps,
                    'competitor_examples': competitors_with_content[:2],
                    'recommendation': f'Expand {content_type.replace("_", " ")} content (you have {brand_count} pages, competitors average more)',
                    'priority': 'medium'
                })
            elif not brand_has and comp_count == 0:
                # Nobody has it = NOT A GAP, just unexplored territory
                false_positives.append({
                    'content_type': content_type,
                    'status': 'not_a_gap',
                    'reason': 'No competitors have this content either',
                    'recommendation': 'Optional: pioneer this content type'
                })
            elif brand_has and comp_count <= 1:
                # You have it, competitors don't = COMPETITIVE ADVANTAGE
                false_positives.append({
                    'content_type': content_type,
                    'status': 'competitive_advantage',
                    'brand_count': brand_count,
                    'reason': f'You have {brand_count} pages, most competitors don\'t',
                    'recommendation': 'Maintain and promote this content'
                })

        return {
            'verified_gaps': sorted(verified_gaps,
                                   key=lambda x: (x['priority'] == 'high', x['competitors_with']),
                                   reverse=True),
            'false_positives': false_positives,
            'total_content_types_analyzed': len(content_types),
            'verified_gap_count': len([g for g in verified_gaps if g['status'] == 'verified_gap']),
            'expansion_opportunity_count': len([g for g in verified_gaps if g['status'] == 'expansion_opportunity'])
        }


def analyze_brand_and_competitors(brand_url: str, competitor_urls: List[str],
                                  max_pages: int = 50) -> Dict[str, Any]:
    """
    Main function to analyze brand and competitor websites.

    Args:
        brand_url: URL of the brand website
        competitor_urls: List of competitor website URLs
        max_pages: Maximum pages to crawl per site

    Returns:
        Complete analysis with verified gaps
    """
    analyzer = WebsiteAnalyzer()

    print("=" * 80)
    print("WEBSITE CONTENT VERIFICATION")
    print("=" * 80)

    # Analyze brand website
    print(f"\n📍 ANALYZING YOUR WEBSITE: {brand_url}")
    brand_analysis = analyzer.analyze_website(brand_url, max_pages=max_pages)

    # Analyze competitor websites
    competitor_analyses = []
    for comp_url in competitor_urls:
        print(f"\n📍 ANALYZING COMPETITOR: {comp_url}")
        try:
            comp_analysis = analyzer.analyze_website(comp_url, max_pages=max_pages)
            competitor_analyses.append(comp_analysis)
        except Exception as e:
            print(f"  ⚠️  Could not analyze {comp_url}: {str(e)}")

    # Compare and identify verified gaps
    comparison = analyzer.compare_websites(brand_analysis, competitor_analyses)

    print("\n" + "=" * 80)
    print(f"✓ ANALYSIS COMPLETE")
    print(f"  - Verified gaps: {comparison['verified_gap_count']}")
    print(f"  - Expansion opportunities: {comparison['expansion_opportunity_count']}")
    print("=" * 80)

    return {
        'brand_analysis': brand_analysis,
        'competitor_analyses': competitor_analyses,
        'comparison': comparison,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
