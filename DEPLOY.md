# Deploying CareerOS on Render (Claude-powered)

This repository is [CareerOS AI](https://github.com/naeemhassan09/CareerOS-AI) (PolyForm Noncommercial licence, see `LICENSE` and `NOTICE`), set up for an **entry-level cybersecurity job search in Ireland**, running on **Claude only**.

## What changed from upstream

| Change | File |
|---|---|
| Every LLM task routes to Claude (Haiku for scoring/parsing, Sonnet for CV profile and cover letters); no OpenAI key needed | `app/llm/router.py` |
| Accepts Render's `postgres://` database URL | `app/config.py` |
| Cybersecurity profile: junior security, SOC, IAM/Entra, GRC titles; Irish cities; senior roles filtered out | `config/profile.cyber.yml` |
| CV template to fill in | `config/cv.md` |
| Container runs migrations on start and listens on `$PORT` | `Dockerfile` |
| One-click Render Blueprint (app and Postgres) | `render.yaml` |
| `mcp` pinned below 2.0 (the MCP server for Claude Desktop breaks on 2.x) | `pyproject.toml`, `Dockerfile` |

## Deploy (about 10 minutes)

1. Get a Claude API key at https://console.anthropic.com → **API Keys**. Add a few euro of credit; the app's budget cap is €10/month by default.
2. Sign in at https://render.com with GitHub.
3. **New → Blueprint** → choose this repository and the `claude/careeros-job-search-integration-56pkps` branch (or `main` after merging).
4. When Render asks for `ANTHROPIC_API_KEY`, paste your key. Leave the Adzuna and Reed fields blank for now.
5. Click **Apply**. The first build takes 5–8 minutes. Your link is `https://careeros-XXXX.onrender.com`.
6. Open the link and choose a username and password (setup mode, first visit only).

## Put it on your phone

- **iPhone (Safari):** open the link → Share → **Add to Home Screen**.
- **Android (Chrome):** open the link → ⋮ menu → **Add to Home screen**.

## Job sources

| Source | How it connects |
|---|---|
| **Adzuna** (aggregates Indeed-style listings in Ireland) | Free key at https://developer.adzuna.com → add `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` in Render or the app's Settings page → **Discover** in the app |
| **Reed** (UK and Ireland) | Free key at https://www.reed.co.uk/developers → `REED_API_KEY` |
| **LinkedIn** | LinkedIn offers no job-search API to personal apps. Use the Chrome extension in `extension/` on a laptop ("Send to CareerOS" on a LinkedIn job page), or paste the job description into the app's inbox from your phone. |
| **Indeed** | Same as LinkedIn: the Chrome extension or paste. Indeed's own search is available live in the Cyber Job Radar page (`web/cyber-job-radar.html`) through Claude's Indeed connector. |

The app never applies, emails or messages anyone on your behalf.

## Before you rely on it

- Fill in `config/cv.md` and the `EDIT` lines in `config/profile.cyber.yml`, then commit; Render redeploys automatically. Claude only uses facts written there.
- **Free-plan limits:** the web service sleeps after 15 minutes idle (first load then takes about a minute), and Render's free Postgres expires after 30 days. For daily use, switch both to the paid Starter plan in `render.yaml` or the dashboard.
- Keep the generated `PII_ENCRYPTION_KEY` unchanged. It decrypts your saved login and settings.
