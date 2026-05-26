---
name: write-kaggle-benchmarks
description: Write, push, run, and manage Kaggle Benchmark tasks using the kaggle CLI and the kaggle-benchmarks Python SDK. Use when the user wants to create or push a benchmark task, run benchmarks against LLM models, check task/run status, download results, or troubleshoot benchmark workflows. Keywords: kaggle benchmarks, benchmark task, kbench, model proxy, push task, run task.
---

# Write Kaggle Benchmarks

## Official Resources
- **SDK source & API** — https://github.com/Kaggle/kaggle-benchmarks
- **SDK auto-generated docs** — https://deepwiki.com/Kaggle/kaggle-benchmarks
- **CLI docs** — https://github.com/Kaggle/kaggle-cli/blob/main/docs/benchmarks.md

## Command Hierarchy
```
kaggle benchmarks (alias: kaggle b)
├── auth              — Fetch Model Proxy credentials
├── init              — Fetch credentials + setup local dev environment
└── tasks (alias: t)  — Manage benchmark tasks
    ├── push          — Upload a task from a .py file
    ├── run           — Run a task against model(s)
    ├── list          — List your benchmark tasks
    ├── status        — Show task details and per-model run status
    ├── download      — Download completed run outputs
    ├── models        — List available benchmark models
    └── delete        — Delete a task (not yet supported by server)
```

## Setup
```bash
# Full setup: credentials + .env + example_task.py + kaggle_benchmarks_reference.md
kaggle b init -y

# Credentials only (refresh MODEL_PROXY_* in .env)
kaggle b auth -y
```

Custom paths: `--env-file <FILE>` and `--example-file <FILE>` for init.

### Env vars written by init:
- `MODEL_PROXY_URL`
- `MODEL_PROXY_API_KEY`
- `MODEL_PROXY_EXPIRY_TIME`
- `LLM_DEFAULT`
- `LLM_DEFAULT_EVAL`
- `LLMS_AVAILABLE`

## Core workflow: Init → Write → Validate → Push → Run → Status → Download

### 0. Init (once per environment, re-run when creds expire)

`init` fetches Model Proxy credentials, writes `.env`, and drops an
`example_task.py` + `kaggle_benchmarks_reference.md` next to it. Every
later step depends on the `MODEL_PROXY_*` vars it writes, so run it
before anything else — and re-run it any time `python task.py` or
`kaggle b t run` fails with an auth error (the API key is short-lived).

```bash
kaggle b init -y                      # first-time setup
kaggle b auth -y                      # creds-only refresh (no scaffolding)
```

### 1. Write a task file
A task file must:
- Import `kaggle_benchmarks as kbench`
- Define at least one function decorated with `@kbench.task(...)`
- Call `.run(kbench.llm)` (or `.evaluate(...)`) on the task function — see Gotchas
- Use `# %%` cell markers (jupytext percent format)

#### Minimal example:
```python
# %%
import kaggle_benchmarks as kbench

# %%
@kbench.task(name="my-test-task")
def my_test_task(llm):
    response = llm.prompt("What is 2 + 2?")
    kbench.assertions.assert_in("4", response, expectation="Should contain 4")

my_test_task.run(kbench.llm)
```

#### LLM resolution precedence (highest → lowest):
1. **Explicit model in code**: `task.run(llm=kbench.llms["google/gemini-3.5-flash"])`
2. **Default in code**: `task.run(llm=kbench.llm)` (resolves to `LLM_DEFAULT`)
3. **Env vars from .env** (`LLM_DEFAULT`, `LLMS_AVAILABLE`, `MODEL_PROXY_*`)

### 2. Validate locally
Run the task end-to-end before pushing. This catches the silent-no-op gotcha and broken prompts before the push → run → wait → download round-trip.

```bash
kaggle b init -y                     # ensure .env is current
python task.py                       # run the task directly
ls -1 *.run.json                     # confirm a run file was produced
```
If `python task.py` exits cleanly and `*.run.json` appears, the task is safe to push. If validation fails, fix and re-run before proceeding to Step 3.

### 3. Push
```bash
kaggle b t push my-task -f task.py --wait
```
`--wait [TIMEOUT]` blocks until server-side creation finishes (no arg = indefinite). `--poll-interval <SECONDS>` controls polling (default 10s).

### 4. Run
```bash
# Interactive picker
kaggle b t run my-task

# Specific model
kaggle b t run my-task -m google/gemini-3.5-flash

# Wait for completion
kaggle b t run my-task -m google/gemini-3.5-flash --wait
```
List available models: `kaggle b t models`.

### 5. Status
```bash
kaggle b t status my-task
kaggle b t status my-task -m google/gemini-3.5-flash
```
For the full output format and error-section layout, see `references/command-reference.md`.

### 6. Download
```bash
kaggle b t download my-task                       # all terminal runs
kaggle b t download my-task -o ./results          # custom directory
kaggle b t download my-task -m google/gemini-3.5-flash
```
Output layout: `<output>/<task>/<version>/<model>/<run_id>/....` Already-downloaded runs are skipped.

## Quick Recipes
```bash
# Push → run → download in one shot
kaggle b t push my-task -f task.py --wait && \
kaggle b t run my-task -m google/gemini-3.5-flash --wait && \
kaggle b t download my-task -o ./results

# List tasks, filtered
kaggle b t list --name-regex "^math" --status errored
```

## Gotchas
Most of these are silent failures the agent will not detect on its own — review before generating any task file or CLI invocation.
- **No `.run()` call → silent no-op**. The push will succeed even if the file has no `.run()` (push validation only checks for `@task` decorators). The task will then execute on the server and produce no `.run.json`, so nothing is recorded. Every task function must end with `task_fn.run(kbench.llm)` (or `.evaluate(...)`).
- **`MODEL_PROXY_API_KEY` is short-lived**. If `python task.py` fails with an auth error, re-run `kaggle b auth -y` (or `kaggle b init -y`) to refresh.
- **`init` / `auth` append to the env file**. Loaded via `dotenv` so last-wins makes re-running safe, but the file accumulates duplicate entries over time.
- **Task slug must match a `@task` decorator**. `kaggle b t push <SLUG> -f file.py` fails if `<SLUG>` doesn't match the slugified name of some `@kbench.task(name=...)` (or function name) in the file. Names are normalized: `My Task` → `my-task`, `my_task` → `my-task`.
- **Server returns model slugs with `@default` suffix sometimes** (e.g. `google/gemini-3.5-flash@default`). The CLI normalizes `@` → `-` for matching; user-facing commands should use the plain `owner/model` form.
- **`delete` is not implemented server-side**. The command exists but currently prints `Delete is not supported by the server yet.`
