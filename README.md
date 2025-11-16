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

## Getting a TikTok Access Token
- **Create/verify a TikTok for Developers account** at <https://developers.tiktok.com> and enroll the TikTok Business “Content Posting” product for your app.
- **Register an application** in the developer portal, note the `client_key`, `client_secret`, and configure an OAuth redirect URL that you control (must match your `upload.callback_url` if you plan to use it).
- **Add the destination TikTok Business account** (or Business Center) as an authorized account for the app so it can request the `video.upload`, `user.info.basic`, and `business.account.info` scopes.
- **Run the OAuth flow**: send the user to `https://www.tiktok.com/v2/auth/authorize/?client_key=...&scope=video.upload,user.info.basic&redirect_uri=...&state=...&response_type=code`. After login/approval TikTok calls your redirect with `code=...`.
- **Exchange the code for a token** by POSTing to `https://open.tiktokapis.com/v2/oauth/token/` with `client_key`, `client_secret`, `code`, and `grant_type=authorization_code`. The JSON response contains `access_token` and `refresh_token`.
- **Refresh when needed** using the same endpoint with `grant_type=refresh_token` before expiry (typically every 24 hours unless you requested longer-lived tokens).
- **Export the active token** into the environment where this CLI runs: `export TIKTOK_ACCESS_TOKEN="paste_access_token_here"`. Never commit the token to Git; rotate immediately if exposed.

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
