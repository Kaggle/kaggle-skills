# Write Kaggle Benchmarks Skill

This skill teaches AI coding agents how to write, push, run, and manage Kaggle Benchmark tasks using the `kaggle` CLI and the `kaggle-benchmarks` Python SDK.

## Structure

```
write-kaggle-benchmarks/
├── SKILL.md    # Skill instructions: CLI workflow, setup, gotchas, and reference pointers
└── README.md   # This file
```

## Installation

Point your AI coding agent to read `SKILL.md`.

**Gemini CLI** — Copy to the auto-discovery location:
```bash
cp -r write-kaggle-benchmarks ~/.gemini/skills/write-kaggle-benchmarks
```

**Other tools** — Ask your agent to read `write-kaggle-benchmarks/SKILL.md`.

## Related

- **`kaggle-benchmarks`** — sibling skill in this repo focused on writing benchmark task code with the `kaggle_benchmarks` Python library (decorators, assertions, judges, tools).
