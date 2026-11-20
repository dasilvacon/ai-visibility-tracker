# Decision and Change Log

Newest first. Add an entry for every decision, model change, prompt-set change and deploy.

## 2026-11-20 Search on, 5 runs per prompt, measurement checks in the report

Goal set by Tiffany: a working tracker today to show the SR&ED reviewer next week, improved next week.

Decisions by Tiffany (2026-11-20):
- Example client for today: DaSilva Consulting.
- Claude changes the API calls (this replaces the Nov 17 plan that Tiffany would change them herself).
- "Estimated monthly mentions": asked for Claude's suggestion. Claude suggested removing it because the
  Measurement Standard already bans it. Removed on the branch. Tiffany can reverse this.

Waiting on Tiffany:
- Model names (check 2). Proposed: ChatGPT `gpt-6-sol`, Claude `claude-opus-5-5`. Basis: third-party pages
  dated Nov 2026 saying GPT-6 Sol is the ChatGPT default on paid plans (GPT-6 Luna on Free and Go) and
  Opus 5.5 is the claude.ai default. Vendor documentation not yet checked, so check 2 is NOT passed.
  Gemini is still `gemini-2.5-flash` and Perplexity `sonar`; neither was checked against the consumer product today.
- DaSilva Consulting competitor list and prompt list (53 prompts: 45 buyer-decision, 8 branded).
  Competitors proposed from names ChatGPT gave in a test answer: Romain Marketing, Marc Nashaat,
  Jason Faber, Jess Joyce, Kingmaker Search.
- "Tiffany DaSilva" is set as an alias of the brand, so an answer naming her counts as naming the company.
- Merge to dev and main, deploy, and the full run.
- Updating the status table in docs/MEASUREMENT_STANDARD.md (that file needs Tiffany's approval to change).

Git safety:
- Tag `backup/2026-11-20-dev-before-changes`: dev as it was.
- Tag `backup/2026-11-20-uncommitted-work`: the 5 tracked files that were edited but not committed.
- All work is on branch `fix/search-on-and-5-runs`. dev and main not touched. Nothing pushed, nothing deployed.

Security check (2026-11-20):
- config/config.json, gcs-credentials.json and .streamlit/secrets.toml are git-ignored and not tracked.
- Git history searched for API keys and private keys: 4 commits matched, all placeholder text in old docs.
- Keys are still in plain text on disk and still need rotating (open since Nov 17).

Changes made on the branch:
- src/api_clients/openai_client.py: Responses API with the `web_search` tool. Saves cited links,
  every page consulted and the search queries. Temperature left at the model default.
- src/api_clients/anthropic_client.py: Messages API with the `web_search_20250305` tool (max 5 searches).
  Saves the same fields. Handles `pause_turn`.
- src/api_clients/base_client.py: a client can ask for a longer timeout (search calls take 12 to 25 seconds).
- main.py: one model list (`DEFAULT_MODELS`) instead of two hardcoded copies. Copilot switched off
  (`COPILOT_ENABLED = False`). Each prompt runs 5 times per platform (`RUNS_PER_PROMPT`, default 5).
  A failed call is retried on the next pass, up to 3 failures, then the platform is reported incomplete.
- src/tracking/results_tracker.py: `run_number` saved with each result.
- src/analysis/run_rates.py (new): checks 1, 3, 5 and 6 run in code. A platform that does not pass is left
  out of the report and named with the reason. Writes `prompt_rates_*.csv` (named in X of N per prompt and
  platform) and `measurement_checks_*.json`.
- src/reporting/html_report_generator.py: new section "How This Was Measured" with the X of N tables.
  Methodology paragraph rewritten to describe what is done.
- Removed "estimated monthly mentions" and "monthly impressions" from gap_analyzer.py, csv_exporter.py,
  pdf_exporter.py, main.py, dashboard_pages/action_plan.py and dashboard_pages/overview.py.
  The CSV column "Estimated Monthly Impact" no longer exists; the dashboard shows Gap in its place.
- data/dasilva_consulting/: draft brand config, personas, keywords and 53 prompts.

Tests run (in a copy of the code outside the project folder, nothing written to GCS):
- 4 single calls: 2 on gpt-6-sol, 2 on claude-opus-5-5. All 4 searched the web and returned links.
- Mini run: 3 prompts x 2 runs x 4 platforms (ChatGPT, Claude, Perplexity, Gemini) = 24 calls, all completed,
  24 of 24 answers include links. Full analysis and HTML report generated.
  Copy saved as qa_reports/2026-11-20_TEST_dasilva_consulting_3_prompts.html. It is a test, not a result.
- Google AI Overviews was not in the mini run: there is no SerpAPI key in config/config.json on this Mac.
- Old data: ran the new checks on the stored OCO results (May 2026). All 6 platforms were left out
  (search off on ChatGPT, Claude and Copilot; incomplete runs on Perplexity, Gemini and AI Overviews).
  No stored client data passes the standard, so every current client needs a fresh run.

Measurement Standard checks, status for the new code:
- Check 1 (search on): passed in the mini run for ChatGPT, Claude, Perplexity, Gemini. AI Overviews not run.
- Check 2 (model matches consumer product): NOT done. Needs vendor documentation and Tiffany's approval.
- Check 3 (label true): Copilot off. ChatGPT and Claude are labelled as API with web search on.
- Check 4 (10-prompt hand spot check): NOT done.
- Check 5 (5 runs): built. Mini run used 2 runs to keep the test small.
- Check 6 (wave complete): built and enforced in the report.

Not tested: the dashboard pages, the Cloud Run deploy, the weekly job, GCS upload.

Seen in the mini run, not changed (next week):
- Trend line says "declining" on a first run with no history.
- "Impact: 6666.7" in the text report's top opportunities.
- Composite score ("Emerging, 24/100") and sentiment score: how they are calculated has not been reviewed.
- Stats in "How to Read This Report" (35% of consumers, 13.6%) have not been re-checked against their sources.

## 2026-11-17 Tracker review

Findings (UniUni export, 5,036 responses, Apr 22 to May 7 2026):
- ChatGPT, Claude and Copilot calls ran with web search off. Claude named UniUni in 0 of 964 responses.
- One run per prompt. Of 161 prompt and platform pairs where UniUni appeared at least once
  across two runs, 112 appeared in only one of the two.
- 482 prompts. 342 never named UniUni on any platform. 35 never named any tracked brand.
- Text report and action-plan file contained a 0.0% gap on every action row, an
  "estimated monthly mentions" figure, and another client's wording ("luxury eyeshadow").
- Correction: the hardcoded 90-day projection and "quick wins" code exists in
  html_report_generator.py (_build_roi_estimator, _build_quick_wins) but nothing calls it.
  It does not appear in the current HTML report.
- Last commit May 8 2026. Last local results May 7 2026.

Decisions by Tiffany:
- Open to buying captured answers, or to both captured answers and fixed API calls.
  Vendor not chosen yet.

- UniUni is no longer a client. The UniUni figures above stay as a record of how the tool
  behaved; they are not a current client result.
- Tracker client list to be refreshed to current clients, excluding DMZ clients
  (Access2Pay, Homekin, Enabled Talent, Ezofis). Final list awaiting Tiffany's confirmation.
  No change made to data/clients.json or GCS yet.
- Ahrefs Brand Radar is still collecting on the account (ClearEvent custom prompts returned
  data through 2026-11-17). Reports for three ended clients are still scheduled:
  UniUni, Say I Do, Felix Health.

- Client list confirmed by Tiffany: Lumo and Saint Javelin are not current.
  Current in tracker: Natasha Denona, Espresso Capital, ClearEvent, Dripos, OCO.
  Retired: UniUni, Say I Do, Lumo, Saint Javelin.
  To add: Powercart, Sofvie, BOMS, DaSilva Consulting. DMZ clients excluded.

Open:
- Rotate the OpenAI, Anthropic, Perplexity, Gemini and Azure keys (they were in plain text
  in config/config.json and were displayed in a Claude session on 2026-11-17).
- Choose the captured-answer vendor.
- Cut each client's prompt set to 40 to 60 buyer-decision prompts plus 5 to 10 branded prompts.
- CLAUDE.md section "PRIORITY: Per-Client Data Isolation" is out of date (see SESSION_NOTES_2026-04-19.md).

Changes made 2026-11-17:
- Added docs/MEASUREMENT_STANDARD.md and docs/DECISIONS.md.
- Added a pointer to both at the top of CLAUDE.md.
- CLAUDE.md: replaced "Other Clients" with the confirmed client list.
- deploy_weekly_jobs.sh: commented out the four retired clients in the weekly schedule list.
- data/clients.json and GCS not changed. Nothing committed yet.

Code fixes made 2026-11-17 (branch dev, not committed, not deployed, tested at function level only):
- main.py, src/reporting/pdf_exporter.py: removed "luxury eyeshadow" wording.
- src/reporting/csv_exporter.py: action-plan Gap column now shows the real gap (was always 0.0%).
- src/analysis/gap_analyzer.py: example prompts no longer repeat the same prompt.
- src/analysis/competitor_analyzer.py: place names, "In Canada"-style fragments and parts of
  tracked names ("Post") are no longer listed as other brands. Still imperfect: it finds
  brands by capital letters, so fragments such as "Express" can still appear.

Not changed, needs Tiffany's decision:
- "Estimated monthly impact / mentions per month" (gap_analyzer.py lines 167, 195, 222).
  The figure is the gap in this run multiplied by 4. Options: remove it, or relabel it as
  responses in this run. Removing or renaming touches the dashboard pages that read the column.
- Unused projection and quick-wins code: delete or leave.
