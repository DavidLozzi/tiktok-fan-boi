# TikTok Fan Automation CLI

Automates the workflow of downloading the latest TikTok videos from multiple public creators, generating refreshed captions with LLM assistance, and uploading the processed clips to a destination TikTok account.

## Features
- Config-driven CLI compatible with Python 3.8+
- Parallel downloads with global de-duplication and rate-limit friendly fan-out
- Keyframe extraction (up to 50 frames) to ground caption generation
- LLM caption + hashtag authoring with retry/backoff and fallbacks
- TikTok Business API upload integration with privacy controls
- Append-only JSONL processing history, atomic writes, and rotation
- Structured logging with rotation and optional verbose console mode
- Unit tests (history, config, dedupe) plus mocked uploader/API interactions

## Quick Start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m tiktok_automation.cli init-config --path config.yaml
```

Edit the generated `config.yaml`, then set credentials:
```bash
export TIKTOK_ACCESS_TOKEN="your_upload_token"
export OPENAI_API_KEY="your_openai_key"
```

Execute a sync run:
```bash
python -m tiktok_automation.cli sync --config config.yaml --verbose
```

## Configuration
- `download`: source usernames, concurrency, watermark handling, storage paths
- `upload`: destination account, privacy (`public|friends|private`), retry policy
- `llm`: provider/model, temperature, hashtag caps, token limits
- `history`: JSONL location, max size, rotation count
- `logging`: log path, level, rotation
- `storage`: temp/keyframe directories

Use `configs/config.example.yaml` as a reference. Paths are relative to repository root unless absolute.

## Data & Storage
- Videos land under `data/downloads/`
- Keyframes live temporarily under `tmp/frames/`
- Processed ledger: `data/processed_videos.jsonl` (rotates by size)
- Logs: `logs/app.log` (rotates by size)

## Security Notes
- No credentials are written to config files; everything sensitive comes from environment variables
- Validate permissions on `config.yaml`, `data/`, and `logs/` when deploying
- TikTok and OpenAI tokens are pulled at runtime and never persisted

## Testing
```bash
pytest
```
Tests cover config loading, dedupe/index logic, caption rendering, and uploader request formation (via mocks).

## Troubleshooting
- **Missing dependencies**: reinstall from `requirements.txt`
- **TikTok API errors**: confirm `TIKTOK_ACCESS_TOKEN` scope and that the destination account is approved for uploads
- **LLM failures**: ensure `OPENAI_API_KEY` exists; failures fall back to original captions
- **Duplicate skips**: clear or rotate `data/processed_videos.jsonl` only if reprocessing is desired

## Limitations & Notes
- TikTok uploading requires Business API access; sandbox tokens will not publish publicly
- `TikTokApi` may need Playwright/Chromium setup depending on environment
- Long-running syncs should be wrapped with external scheduling/monitoring tooling
