# Measurement Standard

Written 2026-11-17. This is the rule for whether tracker data can be shown to a client.
A change to this file needs Tiffany's approval and an entry in docs/DECISIONS.md.

## The rule

"The API call returned an answer" does not mean the data is right.
Data is right only when it matches what a real person would see in that AI product.

## Checks every platform must pass before its numbers appear in a report

1. Web search is on. Proof: the saved response includes the links the AI used.
   A platform where fewer than half of responses include links fails.
2. The model is the one the consumer product currently uses. Check the vendor's
   documentation on the day of the change and write the model name and date in docs/DECISIONS.md.
3. The platform label is true. Do not label a result "Copilot" or "ChatGPT" unless it
   came from that product or from a vendor that captures that product's real answers.
4. Spot check. Run 10 prompts by hand in the real product and compare with the saved
   responses. Record the result in docs/DECISIONS.md.
5. Each prompt runs at least 5 times per platform per wave. Report a rate
   (named in X of 5), never a single yes or no.
6. A wave is complete only when every prompt has all its runs on every platform.
   Incomplete platforms are left out of the report and named as missing.

## Status on 2026-11-17 (from the code in src/api_clients/)

| Platform | Search on | Label true | Passes |
|---|---|---|---|
| Perplexity (sonar) | Yes | Yes | Checks 1 and 3. Runs per prompt: no |
| Gemini | Yes (added April 2026) | Yes | Checks 1 and 3. 798 of 964 calls completed for UniUni |
| Google AI Overviews (SerpAPI) | Yes | Yes | Checks 1 and 3. Rate-limit gaps |
| OpenAI / ChatGPT | No | No | Fails 1 and 3 |
| Anthropic / Claude | No | No | Fails 1 and 3. UniUni named in 0 of 964 responses |
| Copilot | No | No | Fails 1 and 3. It is a GPT mini model on Azure with no Bing search |

No platform passes check 5 yet. Every prompt has run once per wave.

## Report rules

- No projections, no "estimated monthly mentions", no hardcoded impact figures.
- No client's wording in another client's report (UniUni's report contained "luxury eyeshadow").
- Every number shows how many responses it is based on.

## Keys

API keys live in GCP Secret Manager only. No keys in config/config.json or any file in this folder.
