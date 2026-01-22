"""
Report generator for visibility test results.
"""

import os
from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict


class ReportGenerator:
    """Generates reports from test results."""

    def __init__(self, reports_dir: str):
        """
        Initialize the report generator.

        Args:
            reports_dir: Directory to save reports
        """
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)

    def generate_summary_report(self, results: List[Dict[str, Any]]) -> str:
        """
        Generate a summary report from results.

        Args:
            results: List of result dictionaries

        Returns:
            Path to the generated report file
        """
        if not results:
            return self._save_report("No results to report.", "summary_report.txt")

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("AI VISIBILITY TRACKER - SUMMARY REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Total Tests: {len(results)}")
        report_lines.append("")

        # Overall statistics
        successful = [r for r in results if r.get('success') == 'True' or r.get('success') is True]
        failed = [r for r in results if r.get('success') == 'False' or r.get('success') is False]

        report_lines.append("OVERALL STATISTICS")
        report_lines.append("-" * 80)
        report_lines.append(f"Successful Tests: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
        report_lines.append(f"Failed Tests: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
        report_lines.append("")

        # Platform breakdown
        platform_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'failed': 0})
        for result in results:
            platform = result.get('platform', 'unknown')
            platform_stats[platform]['total'] += 1
            if result.get('success') == 'True' or result.get('success') is True:
                platform_stats[platform]['success'] += 1
            else:
                platform_stats[platform]['failed'] += 1

        report_lines.append("PLATFORM BREAKDOWN")
        report_lines.append("-" * 80)
        for platform, stats in sorted(platform_stats.items()):
            success_rate = stats['success'] / stats['total'] * 100 if stats['total'] > 0 else 0
            report_lines.append(f"{platform.upper()}")
            report_lines.append(f"  Total: {stats['total']}")
            report_lines.append(f"  Successful: {stats['success']}")
            report_lines.append(f"  Failed: {stats['failed']}")
            report_lines.append(f"  Success Rate: {success_rate:.1f}%")
            report_lines.append("")

        # Category breakdown
        category_stats = defaultdict(int)
        for result in results:
            category = result.get('category', 'unknown')
            category_stats[category] += 1

        report_lines.append("CATEGORY BREAKDOWN")
        report_lines.append("-" * 80)
        for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"{category}: {count} tests")
        report_lines.append("")

        # Performance metrics
        latencies = [float(r.get('latency_seconds', 0)) for r in results if r.get('latency_seconds')]
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)

            report_lines.append("PERFORMANCE METRICS")
            report_lines.append("-" * 80)
            report_lines.append(f"Average Latency: {avg_latency:.2f}s")
            report_lines.append(f"Min Latency: {min_latency:.2f}s")
            report_lines.append(f"Max Latency: {max_latency:.2f}s")
            report_lines.append("")

        # Errors summary
        errors = [r for r in failed if r.get('error')]
        if errors:
            report_lines.append("ERROR SUMMARY")
            report_lines.append("-" * 80)
            error_counts = defaultdict(int)
            for error in errors:
                error_msg = error.get('error', 'Unknown error')
                error_counts[error_msg] += 1

            for error_msg, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                report_lines.append(f"{count}x: {error_msg}")
            report_lines.append("")

        report_lines.append("=" * 80)

        report_text = "\n".join(report_lines)
        filename = f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        return self._save_report(report_text, filename)

    def generate_platform_comparison(self, results: List[Dict[str, Any]]) -> str:
        """
        Generate a platform comparison report.

        Args:
            results: List of result dictionaries

        Returns:
            Path to the generated report file
        """
        if not results:
            return self._save_report("No results to report.", "platform_comparison.txt")

        # Group results by prompt_id and platform
        prompt_platforms = defaultdict(dict)
        for result in results:
            prompt_id = result.get('prompt_id', 'unknown')
            platform = result.get('platform', 'unknown')
            success = result.get('success') == 'True' or result.get('success') is True
            prompt_platforms[prompt_id][platform] = success

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("PLATFORM COMPARISON REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Get all unique platforms
        all_platforms = set()
        for platforms in prompt_platforms.values():
            all_platforms.update(platforms.keys())
        all_platforms = sorted(all_platforms)

        # Header
        header = f"{'Prompt ID':<15}"
        for platform in all_platforms:
            header += f"{platform:<15}"
        report_lines.append(header)
        report_lines.append("-" * 80)

        # Results
        for prompt_id, platforms in sorted(prompt_platforms.items()):
            row = f"{prompt_id:<15}"
            for platform in all_platforms:
                status = "PASS" if platforms.get(platform) else "FAIL" if platform in platforms else "N/A"
                row += f"{status:<15}"
            report_lines.append(row)

        report_lines.append("")
        report_lines.append("=" * 80)

        report_text = "\n".join(report_lines)
        filename = f"platform_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        return self._save_report(report_text, filename)

    def _save_report(self, content: str, filename: str) -> str:
        """
        Save report content to file.

        Args:
            content: Report content
            filename: Filename for the report

        Returns:
            Path to the saved report
        """
        report_path = os.path.join(self.reports_dir, filename)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return report_path

    def print_quick_summary(self, results: List[Dict[str, Any]]) -> None:
        """
        Print a quick summary to console.

        Args:
            results: List of result dictionaries
        """
        if not results:
            print("No results to display.")
            return

        successful = sum(1 for r in results if r.get('success') == 'True' or r.get('success') is True)
        failed = len(results) - successful

        print("\n" + "=" * 60)
        print("QUICK SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {len(results)}")
        print(f"Successful: {successful} ({successful/len(results)*100:.1f}%)")
        print(f"Failed: {failed} ({failed/len(results)*100:.1f}%)")
        print("=" * 60 + "\n")
