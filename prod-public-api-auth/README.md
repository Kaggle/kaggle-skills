# Kaggle API Auth — Skill README

Teaches an agent to authenticate to the public Kaggle API.

## Prereqs

- For the CLI path: Python 3.11+, browser access for a one-time sign-in.

## Flow

1. **Get a `KGAT_` token** — either:
   - CLI: `python -m venv` → `pip install "kaggle>=1.8.0"` →
     `kaggle auth print-access-token` (fall back to `kaggle auth login` if
     logged out), or
   - Settings page: **kaggle.com/settings/api → Generate New Token** → paste.
2. **Call** `https://www.kaggle.com/api/v1/...` with
   `Authorization: Bearer $TOKEN`.

## Don't

- Don't use **legacy Basic auth** (`kaggle.json` username/key) — `/api/v1`
  legacy only, can't reach these RPCs.
- Don't build the IAP layer — it's not required for this API.

See `SKILL.md` for the full copy-paste procedure and troubleshooting.
