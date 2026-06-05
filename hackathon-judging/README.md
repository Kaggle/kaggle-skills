# Hackathon Judging Skill

This skill steers Kaggle Hackathon hosts toward defensible LLM-assisted grading. It documents the Kaggle MCP endpoints for retrieving hackathon writeups and attached artifacts, the prerequisites for setting up the MCP client, a 12-step grading workflow (collection → auditing → pairwise scoring → final ranking), and the anti-patterns to avoid.

## Structure

```
hackathon-judging/
├── SKILL.md    # Complete skill file — MCP endpoints, prereqs, workflow, anti-patterns
└── README.md   # This file
```

## Installation

Point your AI coding agent to read `SKILL.md`.

**Gemini CLI** — Copy to the auto-discovery location:
```bash
cp -r hackathon-judging ~/.gemini/skills/hackathon-judging
```

**Other tools** — Ask your agent to read `hackathon-judging/SKILL.md`.

## Related resources

- [hamelsmu/evals-skills](https://github.com/hamelsmu/evals-skills/tree/main) — the auditing toolkit referenced in Step 10.
- [Kaggle MCP server](https://www.kaggle.com/mcp) — endpoint for hackathon writeup retrieval.
