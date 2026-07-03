# Run Kaggle TPU Skill

This skill teaches AI coding agents how to scaffold, push, poll, and pull
Kaggle TPU script kernels through the `kaggle` CLI.

## What this skill enables

With this skill installed, an agent can create either a single-process TPU
smoke test or an 8-core `torch_xla` multiprocessing probe, upload it to Kaggle,
wait for the queued run to complete, and download the logs/results:

```bash
DRIVER=run-kaggle-tpu/scripts/driver.sh

$DRIVER scaffold /tmp/my-tpu-kernel my-tpu-kernel-slug single
$DRIVER push /tmp/my-tpu-kernel
$DRIVER poll <kaggle-username>/my-tpu-kernel-slug 15 60
$DRIVER pull <kaggle-username>/my-tpu-kernel-slug /tmp/my-tpu-kernel/output
```

## Prerequisites

- Python environment compatible with Kaggle TPU script kernels
- `kaggle` CLI installed (`pip install kaggle`)
- Valid Kaggle credentials (`~/.kaggle/kaggle.json`)

## Structure

```
run-kaggle-tpu/
|-- SKILL.md                    # Complete skill file and TPU runbook
|-- README.md                   # This file
`-- scripts/
    |-- driver.sh               # Scaffold, push, poll, pull, and run helper
    `-- templates/
        |-- kernel-metadata.multicore.json
        |-- kernel-metadata.single.json
        |-- multicore_probe.py
        `-- single_probe.py
```

## Installation

Point your AI coding agent to read `run-kaggle-tpu/SKILL.md`.

**Gemini CLI** — Copy to the auto-discovery location:

```bash
cp -r run-kaggle-tpu ~/.gemini/skills/run-kaggle-tpu
```

**Other tools** — Ask your agent to read `run-kaggle-tpu/SKILL.md`.

## Version

`0.1`
