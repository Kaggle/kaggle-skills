---
name: kaggle-admin-api-auth
description: Authenticate an agent to the Kaggle Agents/Benchmarks admin API using a KGAT_ access token over the public www.kaggle.com endpoint.
---

# Authenticating to the Kaggle API

This skill lets an agent call the
**public API on `www.kaggle.com`** with a Kaggle access token (`KGAT_...`).

> **Do NOT use the legacy method.** Legacy = HTTP Basic auth
> (`Authorization: Basic base64(username:key)`) from a downloaded `kaggle.json`.
> It only works on `/api/v1` legacy endpoints. Always use a `KGAT_` bearer.

---

## Step 1 — Get a `KGAT_` access token

Two supported paths. Prefer the CLI; the settings-page paste is the zero-setup
fallback.

### Path A — Kaggle CLI (recommended)

The agent can install and drive the CLI itself; the only human step is a
one-time browser sign-in.

**1a. Set up an isolated Python env and install the CLI (needs ≥ 1.8.0):**

```bash
python3 -m venv ~/.kaggle-cli-venv
~/.kaggle-cli-venv/bin/pip install --quiet --upgrade "kaggle>=1.8.0"
KAGGLE=~/.kaggle-cli-venv/bin/kaggle
```

If the user says the CLI is already installed, still resolve a concrete binary
and check the version — older CLIs cannot mint access tokens:

```bash
KAGGLE=$(command -v kaggle || echo ~/.kaggle-cli-venv/bin/kaggle)
"$KAGGLE" --version   # must be >= 1.8.0; if lower, fall back to the venv install above
```

**1b. Probe first, log in only if needed** (handles "installed but logged out"):

```bash
if TOKEN=$("$KAGGLE" auth print-access-token --expiration 6h 2>/dev/null) && [ -n "$TOKEN" ]; then
  echo "Already logged in."
else
  "$KAGGLE" auth login          # human: sign in + Approve. Cloudtop: add --no-launch-browser to get a pasteable URL
  TOKEN=$("$KAGGLE" auth print-access-token --expiration 6h)
fi
```

- `kaggle auth login` requests scope `resources.admin:*`.
- Token TTL: 30 min default, **16 h max**
  ([`Constants.cs#L114-115`](https://github.com/Kaggle/kaggleazure/blob/aeb253835a01fa44e8e90a39e36d2721cd9ffd06/Kaggle.Framework/Configuration/Constants.cs#L114-L115)).
  Re-run `print-access-token` to refresh; no need to log in again.

### Path B — Settings page paste (zero-setup fallback)

Ask the human to visit **https://www.kaggle.com/settings/api**, click
**"Generate New Token"** under *API Tokens (Recommended)* (Type: **Access
token**), copy the `KGAT_...` value, and provide it. Then:

```bash
TOKEN="KGAT_...paste..."
```

This is a legitimate V2 bearer — **not** the legacy key. The legacy key is the
separate "Create Legacy API Key" button that downloads `kaggle.json`; don't use
that.

---

## Step 2 — Call the API

One header. Base URL is the public site.

```bash
BASE=https://www.kaggle.com

# Smoke test: list harnesses (requires the agentic-candidates flag)
curl -sSL "$BASE/api/v1/agents/harnesses/list" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Use the RPC paths/bodies documented on each `*_api_service.proto`.
Each proto method carries a `curl` example in its comment.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | Missing/expired bearer | Re-run `print-access-token`, or re-paste a fresh token |
| `403` / not-found on a valid RPC | Account lacks a feature flag | Have an admin grant access to appropriate flag |
| CLI can't mint token | CLI < 1.8.0 | `pip install --upgrade "kaggle>=1.8.0"` in the venv |
| `kaggle auth login` opens nothing on Cloudtop | Headless box | `kaggle auth login --no-launch-browser` and open the printed URL |

---

## References

- Bearer vs `/api/v1` vs `/api/i` gate:
  [`ApiTokenAuthenticationHandler.cs#L100-118`](https://github.com/Kaggle/kaggleazure/blob/aeb253835a01fa44e8e90a39e36d2721cd9ffd06/Kaggle.Web/Helpers/ApiTokenAuthenticationHandler.cs#L100-L118)
- Token TTL:
  [`Constants.cs#L114-115`](https://github.com/Kaggle/kaggleazure/blob/aeb253835a01fa44e8e90a39e36d2721cd9ffd06/Kaggle.Framework/Configuration/Constants.cs#L114-L115)
- CLI auth commands:
  [`kaggle-cli/skills/references/auth.md`](https://github.com/Kaggle/kaggle-cli/blob/main/skills/references/auth.md)
