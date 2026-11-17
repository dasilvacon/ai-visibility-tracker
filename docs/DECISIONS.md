# Decision and Change Log

Newest first. Add an entry for every decision, model change, prompt-set change and deploy.

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
