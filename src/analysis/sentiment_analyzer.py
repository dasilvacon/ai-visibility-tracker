"""
Sentiment Analyzer - Analyzes how AI describes brands when mentioned.

Maps to: SENTIMENT pillar
- How the AI describes strengths and weaknesses
- Price, quality, reliability, innovation, customer support
"""

from typing import Dict, List, Any, Set
from collections import defaultdict, Counter
import re


class SentimentAnalyzer:
    """Analyzes sentiment and descriptors used when brand is mentioned."""

    def __init__(self, brand_name: str, competitor_names: List[str] = None):
        """
        Initialize sentiment analyzer.

        Args:
            brand_name: Primary brand name
            competitor_names: List of competitor names
        """
        self.brand_name = brand_name
        self.competitor_names = competitor_names or []

        # Descriptor categories based on buying decision factors
        self.descriptor_patterns = {
            'price': {
                'positive': ['affordable', 'value', 'worth', 'reasonable', 'budget-friendly',
                           'cost-effective', 'economical', 'fair price', 'great deal'],
                'negative': ['expensive', 'overpriced', 'costly', 'pricey', 'high-priced',
                           'not worth', 'too much', 'premium price'],
                'neutral': ['premium', 'luxury', 'high-end', 'investment', 'price point']
            },
            'quality': {
                'positive': ['high-quality', 'excellent', 'superior', 'top-tier', 'premium quality',
                           'well-made', 'durable', 'long-lasting', 'reliable', 'consistent',
                           'professional', 'luxurious', 'refined', 'exceptional'],
                'negative': ['low-quality', 'poor', 'inferior', 'cheap', 'flimsy', 'inconsistent',
                           'disappointing', 'subpar', 'mediocre'],
                'neutral': ['quality', 'formulation', 'ingredients', 'formula']
            },
            'reliability': {
                'positive': ['reliable', 'consistent', 'dependable', 'trustworthy', 'proven',
                           'established', 'reputable', 'trusted', 'safe', 'stable'],
                'negative': ['unreliable', 'inconsistent', 'unpredictable', 'questionable',
                           'risky', 'untested', 'unknown'],
                'neutral': ['brand', 'company', 'manufacturer', 'line']
            },
            'innovation': {
                'positive': ['innovative', 'unique', 'cutting-edge', 'advanced', 'revolutionary',
                           'groundbreaking', 'pioneering', 'trendsetting', 'modern', 'new',
                           'latest', 'patented', 'proprietary'],
                'negative': ['outdated', 'old-fashioned', 'behind', 'basic', 'generic',
                           'copycat', 'unoriginal'],
                'neutral': ['technology', 'formula', 'approach', 'method']
            },
            'customer_support': {
                'positive': ['excellent service', 'responsive', 'helpful', 'supportive',
                           'customer-friendly', 'easy returns', 'great support', 'attentive'],
                'negative': ['poor service', 'unresponsive', 'difficult', 'hard to reach',
                           'bad support', 'no returns', 'unhelpful'],
                'neutral': ['customer service', 'support', 'returns', 'warranty']
            },
            'performance': {
                'positive': ['effective', 'works well', 'delivers', 'performs', 'results',
                           'pigmented', 'blendable', 'smooth', 'creamy', 'buildable',
                           'long-wearing', 'stays put', 'doesn\'t crease'],
                'negative': ['ineffective', 'doesn\'t work', 'fails', 'poor performance',
                           'patchy', 'hard to blend', 'chalky', 'dry', 'fades quickly',
                           'creases', 'fallout'],
                'neutral': ['performance', 'wear', 'application', 'finish']
            }
        }

    def analyze_sentiment(self, scored_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sentiment across all mentions of the brand.

        Args:
            scored_results: List of results with visibility scores

        Returns:
            Comprehensive sentiment analysis
        """
        brand_mentions = self._extract_brand_mentions(scored_results)
        competitor_mentions = self._extract_competitor_mentions(scored_results)

        brand_sentiment = self._analyze_mentions(brand_mentions, self.brand_name)
        competitor_sentiment = self._analyze_competitor_sentiment(competitor_mentions)

        comparison = self._compare_sentiment(brand_sentiment, competitor_sentiment)

        return {
            'brand_sentiment': brand_sentiment,
            'competitor_sentiment': competitor_sentiment,
            'comparison': comparison,
            'overall_score': self._calculate_overall_sentiment_score(brand_sentiment),
            'key_strengths': self._identify_strengths(brand_sentiment),
            'key_weaknesses': self._identify_weaknesses(brand_sentiment),
            'recommendations': self._generate_sentiment_recommendations(brand_sentiment, comparison)
        }

    def _extract_brand_mentions(self, scored_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract all results where brand is mentioned."""
        mentions = []

        for result in scored_results:
            visibility = result.get('visibility', {})
            if visibility.get('brand_mentioned'):
                response_text = result.get('response', '')
                mentions.append({
                    'text': response_text,
                    'prompt': result.get('prompt_text', ''),
                    'platform': result.get('platform', 'Unknown'),
                    'prominence': visibility.get('prominence_score', 0),
                    'metadata': result.get('metadata', {})
                })

        return mentions

    def _extract_competitor_mentions(self, scored_results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Extract competitor mentions organized by competitor."""
        competitor_data = defaultdict(list)

        for result in scored_results:
            visibility = result.get('visibility', {})
            competitor_details = visibility.get('competitor_details', {})

            for comp_name, comp_data in competitor_details.items():
                if comp_name in self.competitor_names:
                    response_text = result.get('response', '')
                    competitor_data[comp_name].append({
                        'text': response_text,
                        'prominence': comp_data.get('prominence_score', 0),
                        'platform': result.get('platform', 'Unknown')
                    })

        return dict(competitor_data)

    def _analyze_mentions(self, mentions: List[Dict[str, Any]], entity_name: str) -> Dict[str, Any]:
        """Analyze sentiment for a specific entity's mentions."""
        if not mentions:
            return self._empty_sentiment_result()

        all_descriptors = defaultdict(lambda: defaultdict(list))
        sentiment_scores = []
        platform_sentiment = defaultdict(list)

        for mention in mentions:
            text = mention['text'].lower()
            platform = mention['platform']

            # Extract descriptors by category
            for category, patterns in self.descriptor_patterns.items():
                for sentiment_type, keywords in patterns.items():
                    found_keywords = [kw for kw in keywords if kw in text]
                    if found_keywords:
                        all_descriptors[category][sentiment_type].extend(found_keywords)

            # Calculate overall sentiment for this mention
            mention_sentiment = self._score_mention_sentiment(text)
            sentiment_scores.append(mention_sentiment)
            platform_sentiment[platform].append(mention_sentiment)

        # Aggregate results
        category_scores = {}
        for category, sentiments in all_descriptors.items():
            positive_count = len(sentiments.get('positive', []))
            negative_count = len(sentiments.get('negative', []))
            neutral_count = len(sentiments.get('neutral', []))
            total = positive_count + negative_count + neutral_count

            if total > 0:
                category_scores[category] = {
                    'score': (positive_count - negative_count) / total * 100,
                    'positive_count': positive_count,
                    'negative_count': negative_count,
                    'neutral_count': neutral_count,
                    'top_positive': Counter(sentiments.get('positive', [])).most_common(3),
                    'top_negative': Counter(sentiments.get('negative', [])).most_common(3),
                    'mentions': total
                }

        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

        return {
            'total_mentions': len(mentions),
            'average_sentiment_score': round(avg_sentiment, 2),
            'category_breakdown': category_scores,
            'platform_sentiment': {
                platform: round(sum(scores) / len(scores), 2) if scores else 0
                for platform, scores in platform_sentiment.items()
            },
            'sentiment_distribution': self._calculate_distribution(sentiment_scores)
        }

    def _analyze_competitor_sentiment(self, competitor_mentions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze sentiment for all competitors."""
        competitor_analysis = {}

        for comp_name, mentions in competitor_mentions.items():
            competitor_analysis[comp_name] = self._analyze_mentions(mentions, comp_name)

        # Calculate average competitor sentiment
        if competitor_analysis:
            avg_competitor_scores = [
                data['average_sentiment_score']
                for data in competitor_analysis.values()
            ]
            avg_competitor_sentiment = sum(avg_competitor_scores) / len(avg_competitor_scores)
        else:
            avg_competitor_sentiment = 0

        return {
            'by_competitor': competitor_analysis,
            'average_competitor_sentiment': round(avg_competitor_sentiment, 2)
        }

    def _score_mention_sentiment(self, text: str) -> float:
        """
        Score sentiment of a single mention (-100 to +100).

        Analyzes the context around brand mentions for positive/negative language.
        """
        positive_count = 0
        negative_count = 0

        # Count positive and negative descriptors across all categories
        for category, patterns in self.descriptor_patterns.items():
            for keyword in patterns['positive']:
                if keyword in text:
                    positive_count += 1
            for keyword in patterns['negative']:
                if keyword in text:
                    negative_count += 1

        # Additional sentiment indicators
        positive_indicators = ['best', 'great', 'love', 'recommend', 'favorite', 'perfect',
                              'amazing', 'excellent', 'top', 'popular', 'highly rated']
        negative_indicators = ['avoid', 'disappointed', 'worst', 'hate', 'skip', 'overrated',
                              'not recommended', 'wouldn\'t', 'don\'t buy']

        for indicator in positive_indicators:
            if indicator in text:
                positive_count += 1

        for indicator in negative_indicators:
            if indicator in text:
                negative_count += 1

        # Calculate score
        total = positive_count + negative_count
        if total == 0:
            return 0  # Neutral

        return ((positive_count - negative_count) / total) * 100

    def _calculate_distribution(self, sentiment_scores: List[float]) -> Dict[str, Any]:
        """Calculate sentiment distribution."""
        if not sentiment_scores:
            return {'positive': 0, 'neutral': 0, 'negative': 0}

        positive = sum(1 for s in sentiment_scores if s > 20)
        negative = sum(1 for s in sentiment_scores if s < -20)
        neutral = len(sentiment_scores) - positive - negative

        total = len(sentiment_scores)

        return {
            'positive': round(positive / total * 100, 1),
            'neutral': round(neutral / total * 100, 1),
            'negative': round(negative / total * 100, 1),
            'positive_count': positive,
            'neutral_count': neutral,
            'negative_count': negative
        }

    def _compare_sentiment(self, brand_sentiment: Dict[str, Any],
                          competitor_sentiment: Dict[str, Any]) -> Dict[str, Any]:
        """Compare brand sentiment vs competitors."""
        brand_score = brand_sentiment.get('average_sentiment_score', 0)
        comp_avg = competitor_sentiment.get('average_competitor_sentiment', 0)

        difference = brand_score - comp_avg

        # Category comparison
        brand_categories = brand_sentiment.get('category_breakdown', {})
        category_comparison = {}

        for category in self.descriptor_patterns.keys():
            brand_cat_score = brand_categories.get(category, {}).get('score', 0)

            # Get average competitor score for this category
            comp_cat_scores = []
            for comp_data in competitor_sentiment.get('by_competitor', {}).values():
                comp_categories = comp_data.get('category_breakdown', {})
                if category in comp_categories:
                    comp_cat_scores.append(comp_categories[category]['score'])

            comp_cat_avg = sum(comp_cat_scores) / len(comp_cat_scores) if comp_cat_scores else 0

            category_comparison[category] = {
                'brand_score': round(brand_cat_score, 1),
                'competitor_avg': round(comp_cat_avg, 1),
                'difference': round(brand_cat_score - comp_cat_avg, 1),
                'relative_position': 'ahead' if brand_cat_score > comp_cat_avg else 'behind' if brand_cat_score < comp_cat_avg else 'equal'
            }

        return {
            'overall_difference': round(difference, 1),
            'relative_position': 'ahead' if difference > 10 else 'behind' if difference < -10 else 'equal',
            'category_comparison': category_comparison,
            'brand_score': brand_score,
            'competitor_avg': comp_avg
        }

    def _calculate_overall_sentiment_score(self, brand_sentiment: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall sentiment score out of 100."""
        avg_sentiment = brand_sentiment.get('average_sentiment_score', 0)

        # Convert -100 to +100 scale to 0-100 scale
        score = (avg_sentiment + 100) / 2

        if score >= 70:
            grade = 'A'
            description = 'Excellent - AI describes you very positively'
        elif score >= 60:
            grade = 'B'
            description = 'Good - Mostly positive sentiment'
        elif score >= 50:
            grade = 'C'
            description = 'Average - Mixed sentiment'
        elif score >= 40:
            grade = 'D'
            description = 'Below Average - More negative than positive'
        else:
            grade = 'F'
            description = 'Poor - Predominantly negative sentiment'

        return {
            'score': round(score, 1),
            'grade': grade,
            'description': description,
            'raw_sentiment': avg_sentiment
        }

    def _identify_strengths(self, brand_sentiment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify top 3 strength areas based on sentiment."""
        category_breakdown = brand_sentiment.get('category_breakdown', {})

        strengths = []
        for category, data in category_breakdown.items():
            if data['score'] > 20 and data['positive_count'] > 0:
                strengths.append({
                    'category': category.replace('_', ' ').title(),
                    'score': round(data['score'], 1),
                    'examples': [kw[0] for kw in data['top_positive']],
                    'mention_count': data['positive_count']
                })

        # Sort by score
        strengths.sort(key=lambda x: x['score'], reverse=True)
        return strengths[:3]

    def _identify_weaknesses(self, brand_sentiment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify top 3 weakness areas based on sentiment."""
        category_breakdown = brand_sentiment.get('category_breakdown', {})

        weaknesses = []
        for category, data in category_breakdown.items():
            if data['score'] < -10 or (data['negative_count'] > data['positive_count'] and data['negative_count'] > 0):
                weaknesses.append({
                    'category': category.replace('_', ' ').title(),
                    'score': round(data['score'], 1),
                    'examples': [kw[0] for kw in data['top_negative']],
                    'mention_count': data['negative_count']
                })

        # Sort by score (most negative first)
        weaknesses.sort(key=lambda x: x['score'])
        return weaknesses[:3]

    def _generate_sentiment_recommendations(self, brand_sentiment: Dict[str, Any],
                                           comparison: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on sentiment analysis."""
        recommendations = []

        # Overall sentiment recommendations
        overall_score = self._calculate_overall_sentiment_score(brand_sentiment)
        if overall_score['score'] < 60:
            recommendations.append(
                "⚠️ Overall sentiment is below average. Focus on addressing negative perceptions "
                "and amplifying positive narratives across your content."
            )

        # Category-specific recommendations
        category_comp = comparison.get('category_comparison', {})

        for category, data in category_comp.items():
            if data['relative_position'] == 'behind' and data['difference'] < -20:
                category_name = category.replace('_', ' ').title()
                recommendations.append(
                    f"🎯 {category_name}: You're significantly behind competitors "
                    f"({data['difference']} points). Create content that highlights your {category} advantages."
                )

        # Weakness-specific recommendations
        weaknesses = self._identify_weaknesses(brand_sentiment)
        for weakness in weaknesses[:2]:  # Top 2 weaknesses
            recommendations.append(
                f"🔧 Address {weakness['category']}: Negative mentions include '{', '.join(weakness['examples'][:2])}'. "
                f"Create content that directly counters these perceptions with evidence and examples."
            )

        return recommendations[:5]  # Max 5 recommendations

    def _empty_sentiment_result(self) -> Dict[str, Any]:
        """Return empty sentiment result structure."""
        return {
            'total_mentions': 0,
            'average_sentiment_score': 0,
            'category_breakdown': {},
            'platform_sentiment': {},
            'sentiment_distribution': {'positive': 0, 'neutral': 0, 'negative': 0}
        }
