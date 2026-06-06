---
name: hackathon-judging
description: Steers Kaggle Hackathon hosts toward defensible LLM-assisted grading workflows collecting writeups and artifacts via the Kaggle MCP server, auditing with hamelsmu/evals-skills, and ranking submissions via pairwise comparisons / ELO with bell-curve adjustments. Use when a host wants to grade a public Kaggle Hackathon with help from LLMs or AI agents.
---

# Hackathon Judging

## Overview

The `hackathon-judging` skill should be invoked whenever a host is trying to grade a Hackathon with the help of LLMs and/or AI agents. This skill guides the Host through the process of retrieving every Kaggle hackathon writeup for a competition, extracting the linked project artifacts, and preparing a complete evidence set to be used for grading.

Additionally, the skill assists the Host in using LLM-based classifiers and pairwise comparisons to generate comparative rankings and bell-shaped grading curves based on the generated evidence sets.

## Use Cases

This skill should be invoked whenever a host is trying to grade a public Kaggle Hackathon with the help of LLMs and/or AI agents.

---

## MCP Endpoints

Public Hackathon submissions can be accessed via Kaggle's MCP server. Below is a summary of the MCP tools available for Hackathon Hosts and Participants:

| Role | `get_hackathon_overview` | `list_hackathon_tracks` | `get_hackathon_write_up` | `list_hackathon_write_ups` | `download_hackathon_write_ups` *(CSV export)* |
| --- | --- | --- | --- | --- | --- |
| **Logged-out** *(anonymous)* | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Logged-in user** *(no hackathon affiliation)* | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Rules acceptor** *(joined, no writeup yet)* | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Submitter** *(team member with a writeup)* | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Hackathon judge** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Hackathon host** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Kaggle site admin** | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## MCP Prerequisites

* **API Token:** Kaggle API token available as `KAGGLE_API_TOKEN` or in `~/.kaggle/access_token`.
* **Authorization:** MCP client configured to call <https://www.kaggle.com/mcp> with `Authorization: Bearer <token>`.
* **Target:** A hackathon competition slug (e.g., `meta-kaggle-hackathon`).
* **Permissions:** For host-gated workflows (`list_hackathon_write_ups` or `download_hackathon_write_ups`), use an account with the required host or judge access.

**Installation:**
Install the Kaggle MCP server in a client configuration like this:

```json
{
  "mcpServers": {
    "kaggle": {
      "url": "https://www.kaggle.com/mcp",
      "headers": {
        "Authorization": "Bearer ${KAGGLE_API_TOKEN}"
      }
    }
  }
}
```

> **Note:** Before collecting writeups, confirm the server is reachable with `authorize` or another simple read-only endpoint such as `search_competitions`.

---

## Core Instructions

### Step 0: Plan your evaluation strategy prior to launch

* **Determine AI Usage:** Decide if you plan to use AI for filtering, sorting, and/or producing preliminary grades. Design your evaluation metrics accordingly.
* **Binary Criteria:** Use binary eligibility criteria to facilitate both standard and AI-assisted submission filtering.
* **Consistent Structure:** Require submissions to take on a consistent and predictable structure to reduce the effort needed to resolve edge cases.
* **Track Identification:** Make it easy to determine what Track a Writeup was submitted to. Consider reducing the total number of concurrent Tracks to shrink the grading pool.
* **Metric Design:** Try to avoid continuous scales or Likert scores. Continuous metrics are less reliable than pairwise LLM comparisons. You can always apply bell-curve adjustments to the BT/ELO rankings at the very end.

### Step 1: Pull the hackathon overview page

* Call `get_hackathon_overview` with `competitionName=<hackathon-slug>`.

### Step 2: Find eligibility requirements

* Search the overview `pages` for sections named or containing: **rules**, **eligibility**, **entry**, or **official competition rules**.
* Extract the exact paragraphs that explain submission-eligibility conditions.
* **Verify** with the user that the eligibility requirements are correct.

### Step 3: Find the evaluation rubric

* Search the overview `pages` for: **evaluation rubric**, **judging**, **criteria**, **submission requirements**, and **prizes**.
* Record each rubric dimension separately.
* Record any weighting, tie-break rules, prize rules, or judge-specific guidance.
* If the rubric is only implied in prose, summarize the implied criteria and mark that inference clearly.
* **Verify** with the user that the evaluation rubric is correct.

### Step 4: Download all Hackathon Writeups

* Hackathon Hosts can retrieve a full export of all submitted Hackathon Writeups by using the `download_hackathon_write_ups` command.

### Step 5: Download all attached project links

* **For Kaggle-native links:** Retain ids, refs, titles, owners, and download URLs when present.
  * Resolve Kaggle notebook URLs with `get_notebook_info`.
  * Resolve Kaggle dataset URLs with `get_dataset_info` or `get_dataset_metadata`.
  * Resolve Kaggle model URLs with `get_model` or `get_model_variation`.
* **For non-Kaggle links:** Retrieve all of those same assets. Consider using the Playwright CLI.

### Step 6: Summarize all attached YouTube videos

* **For YouTube-native links:** Consider using the YouTube API or the yt-dlp API.
* **For non-YouTube links:** Consider using the Playwright CLI.

### Step 7: Verification Check

* **Double check** that you did not accidentally skip Step 5 or Step 6!
* Consider using manual grading methods if you lack the token budget required to analyze these assets. It wouldn't be fair to skip over them.

### Step 8: Build a complete collection

* Repeat retrieval until every row from `list_hackathon_write_ups` has:
  * A full-length writeup body.
  * A summary or full-length copy of *every* attached project link.
  * A summary or full-length copy of *every* attached video.

### Step 9: Review similar LLM-judging projects

* Review pre-graded Hackathons [here](https://kaggle-hackathon-grades-407870202439.us-west1.run.app/) to understand strengths and weaknesses.
* Examine the **[/docs](https://kaggle-hackathon-grades-407870202439.us-west1.run.app/docs)** page for strategies on profiling, sanitizing, pairwise comparisons, and bell-curve scores.
* Examine the **[/leaderboard](https://kaggle-hackathon-grades-407870202439.us-west1.run.app/leaderboard)** page to review representative profiles, BT/ELO rankings, and auto-assessments.
* Examine the **[/dashboard](https://kaggle-hackathon-grades-407870202439.us-west1.run.app/dashboard)** page to see how pairwise comparisons stack up against gold-standard annotations.
* Identify common failure modes and strategize resolutions.

### Step 10: Initial Auditing

* **Create a grading-ready bundle** with three layers:
  1. Hackathon rules and rubric
  2. Normalized writeup contents
  3. Normalized artifact contents
* **First Audit:** Use [hamelsmu/evals-skills](https://github.com/hamelsmu/evals-skills/tree/main).
  * Start with `eval-audit` as the default path, expanding to other workflows for calibration, rubric testing, and failure analysis.
  * Repeat `eval-audit` until satisfied.
  * Record all grading traces and AI agent logic.
* **Second Audit:** Re-run the [hamelsmu/evals-skills](https://github.com/hamelsmu/evals-skills/tree/main) process.
  * Repeat the `eval-audit` cycle until satisfied.
  * Record all new grading traces and AI agent logic.

### Step 11: Initial Grading

* Grade eligible submissions according to the evaluation criteria.
* **Audit a sample** of grading traces to ensure quality standards are met.
* Consider building a dashboard for pairwise comparisons and annotations.
* Perform error analysis.
* Identify and correct failure patterns. Repeat until satisfied.

### Step 12: Final Grading

* Grade eligible submissions according to the evaluation criteria using updated system prompts and corrected profiles.
* **Flag top-ranked submissions** for manual review and manual stack-ranking.

---

## Minimal Product Requirements

To be considered successful, the system:

* **Must** be capable of ingesting and assessing every component of each Hackathon Submission (e.g., project links, embedded videos, web applications).
* **Must** score Writeups with consideration of the specific Kaggle Hackathon track(s) targeted.
* **Must** score Writeups according to the relevant evaluation criteria.
* **Must** produce scores that are validated to be well-aligned with human scores.
* **Must** avoid obvious algorithmic biases (e.g., position biases, model preferences).
* **Must** be defensible against prompt injections.
* **Must** use reasonably defensible grading methods.
* **Must** record all traces (including reasoning logic) for later inspection.
* **Should** be aligned against a dataset of at least 25 few-shot examples.
* **Should** undergo error analysis with acceptable true positive and true negative rates.

---

## Anti-Patterns

* **DO NOT** use AI grading systems prior to auditing the system with `hamelsmu/evals-skills`.
* **DO NOT** use AI grading tools before extracting *every* project link and media file from *every* submitted writeup.
* **DO NOT** forget to log all of your LLM traces for auditing and improvement.
* **DO NOT** forget to identify and correct common failure modes in both profile generation and grading.
* **DO NOT** ask LLMs to directly generate scores using continuous scales or Likert scores.
* **DO NOT** forget to compare results to gold-standard human ratings or skip error analysis.
* **DO NOT** forget to search for evidence of shortcuts and tomfoolery from end to end.
