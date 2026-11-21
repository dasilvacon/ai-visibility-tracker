"""
Measurement checks and "named in X of N" rates.

Implements the parts of docs/MEASUREMENT_STANDARD.md that can be checked
from saved responses:

  Check 1  Web search is on: at least half of a platform's answers include
           the links the AI used.
  Check 3  The platform label is true: Copilot results are left out.
  Check 5  Each prompt runs several times; report a rate, never a single
           yes or no.
  Check 6  A platform is in the report only when every prompt has all its
           runs. Platforms left out are named.

Checks 2 and 4 (model matches the consumer product, hand spot check) are
done by a person and written in docs/DECISIONS.md.
"""

import csv
import html
import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Tuple

PLATFORM_LABELS = {
    'openai': 'ChatGPT paid plans (OpenAI API, web search on)',
    'openai_free': 'ChatGPT free plan (OpenAI API, web search on)',
    'anthropic': 'Claude paid plans (Anthropic API, web search on)',
    'anthropic_free': 'Claude free plan (Anthropic API, web search on)',
    'perplexity': 'Perplexity',
    'gemini': 'Gemini (Google Search grounding on)',
    'google_ai_overview': 'Google AI Overviews',
    'copilot': 'Copilot',
}

# Platforms whose label is not true for the data collected (check 3).
UNTRUE_LABEL_PLATFORMS = {
    'copilot': 'The calls went to a GPT mini model on Azure with no Bing search, not to Copilot.',
}

MIN_SHARE_WITH_LINKS = 0.5


def _has_answer(result: Dict[str, Any]) -> bool:
    return bool(result.get('response_text') or result.get('response'))


def _has_links(result: Dict[str, Any]) -> bool:
    meta = result.get('metadata', {}) or {}
    return bool(result.get('cited_urls') or meta.get('cited_urls') or meta.get('references'))


def _is_success(result: Dict[str, Any]) -> bool:
    return str(result.get('success', '')).lower() == 'true'


def apply_measurement_checks(full_results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Run checks 1, 3 and 6 per platform and drop platforms that do not pass.

    Returns:
        (results from passing platforms only, checks summary)
    """
    by_platform: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in full_results:
        by_platform[r.get('platform', '') or 'unknown'].append(r)

    all_prompt_ids = sorted({r.get('prompt_id') for r in full_results if r.get('prompt_id')})

    platforms: Dict[str, Any] = {}
    for platform, rows in sorted(by_platform.items()):
        successes = [r for r in rows if _is_success(r)]
        answers = [r for r in successes if _has_answer(r)]
        with_links = [r for r in answers if _has_links(r)]
        share = (len(with_links) / len(answers)) if answers else 0.0

        runs_expected = max(
            [int(r.get('runs_per_prompt') or (r.get('metadata', {}) or {}).get('runs_per_prompt') or 1) for r in rows] or [1]
        )
        runs_by_prompt: Dict[str, int] = defaultdict(int)
        for r in successes:
            runs_by_prompt[r.get('prompt_id')] += 1
        short = [pid for pid in all_prompt_ids if runs_by_prompt.get(pid, 0) < runs_expected]

        reasons = []
        if platform in UNTRUE_LABEL_PLATFORMS:
            reasons.append('Label not true. ' + UNTRUE_LABEL_PLATFORMS[platform])
        if not answers:
            reasons.append('No answers saved.')
        elif share < MIN_SHARE_WITH_LINKS:
            reasons.append(
                f'Web search check not met: {len(with_links)} of {len(answers)} answers include links '
                f'({share:.0%}); the standard needs at least half.'
            )
        if short:
            reasons.append(
                f'Wave incomplete: {len(short)} of {len(all_prompt_ids)} prompts have fewer than '
                f'{runs_expected} completed runs.'
            )

        platforms[platform] = {
            'label': PLATFORM_LABELS.get(platform, platform),
            'models': sorted({str(r.get('model', '')) for r in rows if r.get('model')}),
            'calls_saved': len(rows),
            'calls_completed': len(successes),
            'answers': len(answers),
            'answers_with_links': len(with_links),
            'share_with_links': round(share, 4),
            'runs_per_prompt': runs_expected,
            'prompts': len(all_prompt_ids),
            'prompts_short_of_runs': len(short),
            'included_in_report': not reasons,
            'reasons_left_out': reasons,
        }

    included = {p for p, info in platforms.items() if info['included_in_report']}
    kept = [r for r in full_results if (r.get('platform', '') or 'unknown') in included]

    timestamps = sorted(str(r.get('timestamp', '')) for r in full_results if r.get('timestamp'))
    checks = {
        'platforms': platforms,
        'platforms_included': sorted(included),
        'platforms_left_out': sorted(set(platforms) - included),
        'prompts': len(all_prompt_ids),
        'first_response': timestamps[0] if timestamps else '',
        'last_response': timestamps[-1] if timestamps else '',
        'checks_run_by_code': ['1 web search on', '3 platform label', '5 runs per prompt', '6 wave complete'],
        'checks_done_by_hand': ['2 model matches the consumer product', '4 ten-prompt spot check'],
    }
    return kept, checks


def build_prompt_rates(scored_results: List[Dict[str, Any]], brand_name: str,
                       competitors: List[str]) -> List[Dict[str, Any]]:
    """
    One row per prompt and platform: how many of the runs named the brand
    and each tracked competitor.
    """
    groups: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for r in scored_results:
        key = (r.get('prompt_id', ''), r.get('platform', ''))
        g = groups.setdefault(key, {
            'prompt_id': key[0],
            'platform': key[1],
            'prompt_text': r.get('prompt_text', ''),
            'category': (r.get('metadata', {}) or {}).get('category', ''),
            'runs': 0,
            'runs_with_answer': 0,
            'brand_named': 0,
            'competitors': defaultdict(int),
        })
        vis = r.get('visibility', {}) or {}
        g['runs'] += 1
        if not vis.get('ai_overview_absent'):
            g['runs_with_answer'] += 1
        if vis.get('brand_mentioned'):
            g['brand_named'] += 1
        for comp in vis.get('competitors_mentioned', []) or []:
            g['competitors'][comp] += 1

    rows = []
    for key in sorted(groups):
        g = groups[key]
        row = {
            'prompt_id': g['prompt_id'],
            'platform': g['platform'],
            'category': g['category'],
            'prompt_text': g['prompt_text'],
            'runs': g['runs'],
            'runs_with_answer': g['runs_with_answer'],
            f'{brand_name} named in': g['brand_named'],
            'rate': f"{g['brand_named']} of {g['runs']}",
        }
        for comp in competitors:
            row[f'{comp} named in'] = g['competitors'].get(comp, 0)
        rows.append(row)
    return rows


def save_outputs(reports_dir: str, brand_name: str, checks: Dict[str, Any],
                 rates: List[Dict[str, Any]], period: str) -> Dict[str, str]:
    """Write the rates CSV and the checks JSON next to the other exports."""
    os.makedirs(reports_dir, exist_ok=True)
    safe = brand_name.replace(' ', '_')
    rates_path = os.path.join(reports_dir, f'prompt_rates_{safe}_{period}.csv')
    checks_path = os.path.join(reports_dir, f'measurement_checks_{safe}_{period}.json')
    if rates:
        with open(rates_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(rates[0].keys()))
            writer.writeheader()
            writer.writerows(rates)
    with open(checks_path, 'w', encoding='utf-8') as f:
        json.dump(checks, f, indent=2)
    return {'prompt_rates': rates_path if rates else '', 'measurement_checks': checks_path}


def render_html(checks: Dict[str, Any], rates: List[Dict[str, Any]], brand_name: str) -> str:
    """HTML block for the report: what was measured, what passed, and the rates."""
    e = html.escape
    brand_col = f'{brand_name} named in'
    cell = 'padding: 10px 12px; border-bottom: 1px solid #E8E0E4; text-align: left; vertical-align: top;'
    head = 'padding: 10px 12px; border-bottom: 2px solid #4D2E3A; text-align: left; color: #4D2E3A;'

    platform_rows = []
    for platform, info in checks['platforms'].items():
        status = 'In this report' if info['included_in_report'] else 'Left out: ' + ' '.join(info['reasons_left_out'])
        platform_rows.append(
            f"<tr><td style='{cell}'>{e(info['label'])}</td>"
            f"<td style='{cell}'>{e(', '.join(info['models']) or 'not recorded')}</td>"
            f"<td style='{cell}'>{info['calls_completed']} of {info['prompts'] * info['runs_per_prompt']}</td>"
            f"<td style='{cell}'>{info['answers_with_links']} of {info['answers']}</td>"
            f"<td style='{cell}'>{e(status)}</td></tr>"
        )

    by_platform: Dict[str, Dict[str, int]] = defaultdict(lambda: {'prompts': 0, 'ever': 0, 'always': 0, 'named': 0, 'runs': 0})
    by_prompt: Dict[str, Dict[str, Any]] = {}
    for row in rates:
        p = by_platform[row['platform']]
        p['prompts'] += 1
        p['runs'] += row['runs']
        p['named'] += row[brand_col]
        if row[brand_col] > 0:
            p['ever'] += 1
        if row['runs'] and row[brand_col] == row['runs']:
            p['always'] += 1
        bp = by_prompt.setdefault(row['prompt_id'], {'text': row['prompt_text'], 'cells': {}})
        bp['cells'][row['platform']] = f"{row[brand_col]} of {row['runs']}"

    summary_rows = []
    for platform in checks['platforms_included']:
        p = by_platform.get(platform)
        if not p:
            continue
        summary_rows.append(
            f"<tr><td style='{cell}'>{e(PLATFORM_LABELS.get(platform, platform))}</td>"
            f"<td style='{cell}'>{p['named']} of {p['runs']}</td>"
            f"<td style='{cell}'>{p['ever']} of {p['prompts']}</td>"
            f"<td style='{cell}'>{p['always']} of {p['prompts']}</td></tr>"
        )

    included = checks['platforms_included']
    prompt_rows = []
    for pid in sorted(by_prompt):
        bp = by_prompt[pid]
        cells = ''.join(f"<td style='{cell}'>{e(bp['cells'].get(pl, 'no data'))}</td>" for pl in included)
        prompt_rows.append(f"<tr><td style='{cell}'>{e(bp['text'])}</td>{cells}</tr>")
    prompt_head = ''.join(f"<th style='{head}'>{e(PLATFORM_LABELS.get(pl, pl).split(' (')[0])}</th>" for pl in included)

    left_out = checks['platforms_left_out']
    left_out_line = (
        'Platforms left out of this report: ' + ', '.join(e(checks['platforms'][p]['label']) for p in left_out) + '.'
        if left_out else 'No platform was left out of this report.'
    )

    return f"""
        <div class="section" style="margin: 32px 0;">
            <h2>How This Was Measured</h2>
            <p style="color: #4D2E3A; line-height: 1.7;">
                {checks['prompts']} prompts. Responses collected {e(checks['first_response'])} to {e(checks['last_response'])}.
                A platform is in this report only when web search was on (at least half of its answers include
                the links the AI used) and every prompt has all of its runs. {left_out_line}
            </p>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px; margin: 16px 0;">
                <tr><th style="{head}">Platform</th><th style="{head}">Model</th><th style="{head}">Runs completed</th>
                <th style="{head}">Answers that include links</th><th style="{head}">Status</th></tr>
                {''.join(platform_rows)}
            </table>
            <p style="color: #4D2E3A; line-height: 1.7; font-size: 14px;">
                Checked by code: web search on, platform label, runs per prompt, wave complete.
                Checked by hand and recorded in the decision log: model matches the consumer product, 10-prompt spot check.
                API answers can differ from what a signed-in person sees in the app.
            </p>

            <h3 style="color: #4D2E3A; margin-top: 32px;">How often {e(brand_name)} was named</h3>
            <p style="color: #4D2E3A; line-height: 1.7;">
                AI answers change from one run to the next, so each prompt ran several times on each platform.
                The figures below count runs, not a single yes or no.
            </p>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px; margin: 16px 0;">
                <tr><th style="{head}">Platform</th><th style="{head}">Runs that named {e(brand_name)}</th>
                <th style="{head}">Prompts named at least once</th><th style="{head}">Prompts named in every run</th></tr>
                {''.join(summary_rows)}
            </table>
            <div class="accordion-group" style="margin: 16px 0;">
                <button class="accordion-button" onclick="toggleAccordion(this)">
                    <span>Every prompt: runs that named {e(brand_name)}</span>
                    <span class="accordion-icon">▼</span>
                </button>
                <div class="accordion-content">
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                        <tr><th style="{head}">Prompt</th>{prompt_head}</tr>
                        {''.join(prompt_rows)}
                    </table>
                </div>
            </div>
        </div>
    """
