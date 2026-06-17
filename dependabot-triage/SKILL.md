---
name: dependabot-triage
description: Triage Dependabot PRs on Kaggle repos (e.g. Kaggle/competitions, Kaggle/competitions-prep, Kaggle/kaggle-environments) by checking whether the proposed package version is already shipped in Kaggle/docker-python, allowed by hearth's uv exclude-newer cutoff, and not a semver major bump. Use whenever a maintainer asks to triage, sweep, or auto-approve Dependabot PRs.
---

# Dependabot Triage

A Dependabot bump is almost always safe when the proposed version is already
shipped in Kaggle's `docker-python` image. This skill checks that (plus hearth's
`exclude-newer` cutoff and major-version bumps) and prints a verdict.

## Run it

Triages every open Dependabot PR on the repo (Docker runs once for the batch):

```bash
python3 dependabot-triage/check_dependabot_pr.py --repo Kaggle/competitions
```

Requirements (the script itself is stdlib only — no pip install):

- `gh` CLI authenticated with read access to the target repo.
- `docker`, plus GCR auth to pull `gcr.io/kaggle-images/python:latest`
  (`gcloud auth configure-docker gcr.io`). The script runs `pip list` inside that
  image to get the full installed-package set, so the first run pulls the image.

## Output

A JSON list with one dict per open PR: `{ "verdict", "package", "version", "reason" }`.

- `auto-approve` — docker-python ships this version or newer, no major bump, and
  (for `competitions/hearth`) within the `exclude-newer` cutoff. Safe to approve:
  `gh pr review <pr> -R <repo> --approve --body "<reason>"`. Do not merge — leave
  that to branch protection.
- `needs-attention` — read `reason`. Common blockers: package not installed in
  docker-python, proposed version newer than docker-python ships, a major bump,
  or blocked by hearth's `exclude-newer`. Review manually before approving.
- `skip-js` — a JS/npm package with no docker-python baseline; review manually.
- `skip-obsolete` — a `Kaggle/competitions-prep` PR targeting a `closed/` or
  `never_launched/` directory; the work is obsolete, so the PR is safe to close.

Review the list and only approve the `auto-approve` rows after confirming.
