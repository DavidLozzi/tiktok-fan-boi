# Repo name

TikTok Fan Automation CLI

brief desctiption of what it is

## details

- CLI app that downloads the latest TikTok videos from multiple public creators, deduplicates globally, and processes them end to end.
- Extracts keyframes (up to 50) from each downloaded video to give downstream caption generation visual context.
- Calls an LLM to produce refreshed captions + hashtags, enforces credit lines, performs retries/backoff, and falls back to source captions on failure.
- Uploads processed clips to a target TikTok account via the official API with privacy controls, logging, and error handling.
- Persists append-only JSONL history for de-duplication, rotates logs/history by size, and relies on config-driven settings plus environment-provided secrets.
- Includes tests (unit + integration with mocks), requirements file, and docs describing installation, configuration, troubleshooting, and limitations.

## coding requirements

### Python

- always use `httpx` over `requests`
- if performing multiple API calls, consider if it can be done in parallel and use `asyncio` to run multiple calls in parallel
- no credentials or secrets in source; rely on env vars or encrypted config
- default to atomic writes for logs/history/config outputs and guard against data races in concurrent workflows

## learnings

As you interact with the user and if you find anything that is out of the norm or an area where and the user went back-and-forth, or the user had to correct you, save your learnings below.

### learnings
Let your learnings in bullets below