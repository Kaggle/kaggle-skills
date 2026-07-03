---
name: run-kaggle-tpu
description: Scaffold, push, poll, and pull Kaggle TPU kernels via the kaggle CLI. Use when asked to run something on a Kaggle TPU, check Kaggle TPU queue times, smoke-test torch_xla on Kaggle, debug the "Expected 8 worker addresses" multiprocessing bug, or set up a new Kaggle TPU experiment.
---

# Run Kaggle TPU

Drive Kaggle TPU experiments end-to-end with
`run-kaggle-tpu/scripts/driver.sh` (scaffold a kernel dir → push → poll
status → pull logs/results), instead of hand-writing
`kernel-metadata.json` and re-deriving the torch_xla multiprocessing fix each
time. Requires the `kaggle` CLI already authenticated (`~/.kaggle/kaggle.json`).

## Primer: how a Kaggle TPU kernel run actually works

A "kernel" here is a script/notebook Kaggle runs on a TPU VM. The workflow
is push-and-poll, not interactive:

1. You write a directory with `kernel-metadata.json` (id, title, code file,
   accelerator flags) + the code file itself.
2. `kaggle kernels push -p <dir>` uploads it and queues a run.
3. The kernel sits `QUEUED` until a TPU worker is free, then flips to
   `RUNNING`, then `COMPLETE` / `ERROR`.
4. `kaggle kernels output <ref> -p <out-dir>` downloads the log (as JSON
   lines with per-line timestamps) and any result files.

**Queue time is the real bottleneck**, not execution. Measured on 2026-07-01
(single-process `enable_tpu: true` script kernel, no dataset/model mounts)
across two separate pushes: push → RUNNING took **~11m17s** the first time
and **~3m10s** the second — queue time is variable, not a fixed constant, so
don't read one sample as the current wait. Either way the kernel itself
acquires a real TPU device (`xla:0`) and finishes in well under a minute once
running. Budget for a multi-minute queue wait per push and batch multiple
things into one kernel run rather than pushing many small ones.

## Run (agent path)

```bash
DRIVER=run-kaggle-tpu/scripts/driver.sh

# 1. Scaffold a new kernel dir (single-process smoke test by default)
$DRIVER scaffold /tmp/my-tpu-kernel my-tpu-kernel-slug single
# or for the 8-core multiprocessing pattern:
$DRIVER scaffold /tmp/my-tpu-kernel my-tpu-kernel-slug multicore

# 2. Push it
$DRIVER push /tmp/my-tpu-kernel

# 3. Poll until it's done (prints a line only when status changes;
#    exits 0=COMPLETE, 1=ERROR/CANCELLED, 2=timeout)
$DRIVER poll <kaggle-username>/my-tpu-kernel-slug 15 60

# 4. Pull the log + results
$DRIVER pull <kaggle-username>/my-tpu-kernel-slug /tmp/my-tpu-kernel/output
```

Or all in one shot (push, poll, pull):

```bash
$DRIVER run /tmp/my-tpu-kernel <kaggle-username>/my-tpu-kernel-slug 15 60
```

`poll`'s two numeric args are `interval_seconds max_iterations` — default
15s / 60 iterations (~15 min ceiling). Bump `max_iterations` for slower
queues; observed queue times so far are ~3-11 min, so 60×15s=15min has
margin.

The pulled log (`<out-dir>/<slug>.log`) is JSON-lines with a `time` field
(seconds since kernel start) per stdout/stderr chunk — grep it for your
print statements rather than trying to read Kaggle's HTML results page.

| driver.sh subcommand | what it does |
|---|---|
| `scaffold <dir> <slug> [single\|multicore]` | Writes `kernel-metadata.json` + `probe.py` from `scripts/templates/` into `<dir>`. Reads your kaggle username from `kaggle config view`. |
| `push <dir>` | `kaggle kernels push -p <dir>` |
| `status <ref>` | One-shot `kaggle kernels status <ref>`, last line only |
| `poll <ref> [interval] [max_iter]` | Loops `status`, prints only on change, stops at COMPLETE/ERROR/timeout |
| `pull <ref> [out_dir]` | `kaggle kernels output <ref> -p <out_dir>` |
| `run <dir> <ref> [interval] [max_iter]` | push + poll + pull |

To customize the probe past the template (real dataset/model mounts,
multi-file code), scaffold first, then edit `kernel-metadata.json` directly
— add to `dataset_sources` / `model_sources` / `kernel_sources` as needed
and edit `probe.py` (or swap in your own
`code_file`).

## Verified 2026-07-01

- Scaffolded a `single` kernel, pushed as `athviii/kaggle-tpu-skill-verify-20260701`,
  polled, and pulled its output with this exact driver — full push→poll→pull
  cycle exercised, not just written.
- Standalone probe pushed earlier the same session
  (`athviii/tpu-queue-time-probe-20260701`) confirmed the ~11m17s queue time
  and a clean `xla:0` device acquisition on completion.
- Other completed TPU kernels for reference (`kaggle kernels status <ref>`
  all report `COMPLETE`): `athviii/ldt-nonogram-real-tpu`,
  `athviii/tinystories-bpe-tst-sweep-tpu-v1`.

## Gotchas

- **"Expected 8 worker addresses, got 1"** — Kaggle's host process sets
  `TPU_PROCESS_ADDRESSES=local`. If that env var (and `CLOUD_TPU_TASK_ID`)
  leaks into the 8 processes `xmp.spawn` forks, each one thinks the
  topology has only one worker address and initialization fails. Fix:
  `os.environ.pop("TPU_PROCESS_ADDRESSES", None)` and
  `os.environ.pop("CLOUD_TPU_TASK_ID", None)` **before** calling
  `xmp.spawn(worker, start_method="fork")` — baked into
  `scripts/templates/multicore_probe.py`.
- **Never call `torch_xla.device()` in the parent process** — only inside
  the function passed to `xmp.spawn`. Calling it in the parent before
  spawning workers is what triggers the topology mismatch above.
- **`kernel_type: "script"` is enough for a plain `.py` file** — you don't
  need a notebook (`.ipynb`) + `kernel_type: "notebook"` just to run Python
  on a TPU. A bare script kernel (as scaffolded here) works and is simpler
  to template/diff.
- **Version warnings are usually harmless** — older `kaggle` CLI versions may
  print a warning on every call while still working for push/status/output;
  the driver doesn't try to suppress it.
- **Queue time dwarfs runtime for smoke tests** — don't poll with a short
  timeout expecting a fast turnaround; several minutes queued is normal, not
  a sign of failure.

## Troubleshooting

- **`Could not read kaggle username from 'kaggle config view'`** (from
  `scaffold`): `~/.kaggle/kaggle.json` isn't set up. Run
  `kaggle config view` yourself to see the actual error.
- **`Could not find SliceBuilder port 8471 in any of the 0 ports provided
  in tpu_process_addresses="local"`** in the pulled log: this is a benign
  warning from a *single-process* kernel (the metric server has nothing to
  bind to) — it still proceeds to acquire the TPU device fine. Only treat
  it as fatal if the kernel actually ends in `ERROR` status.
