---
name: write-kaggle-benchmarks
description: Write, push, run, publish, and manage Kaggle Benchmark tasks using the kaggle CLI and the kaggle-benchmarks Python SDK. Use when the user wants to create or push a benchmark task (optionally with attached Kaggle datasets), run benchmarks against LLM models, check task/run status, stream or fetch execution logs, download results and source notebooks, publish a task to make it public, or troubleshoot benchmark workflows. 
---

# Write Kaggle Benchmarks

## Keywords
Kaggle benchmarks, write a benchmark, benchmark task, kbench, push task, run task.

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
    ├── download      — Download completed run outputs (and optionally source notebooks)
    ├── log (logs)    — Show execution logs for run(s) (streams live for RUNNING runs)
    ├── publish       — Make a task public (publishes the backing notebook by default)
    ├── models        — List available benchmark models
    └── delete        — Delete a task (not yet supported by server)
```

## Setup (one confirmation, then autonomous)

Before running setup, summarize the steps below in one short message and ask the user:
*"Run setup now? (installs/upgrades kaggle + kaggle-benchmarks, verifies auth, fetches Model Proxy creds)"*

If the user confirms, run all four steps below without further prompts. If the user declines,
stop and wait for direction. Re-run setup automatically (no re-confirmation) any time a later
step fails with an auth/import error — all steps are idempotent and safe.

### 1. Ensure latest CLI + SDK
```bash
pip install --upgrade kaggle kaggle-benchmarks
```
If `pip` is unavailable, fall back to `uv pip install --upgrade kaggle kaggle-benchmarks`.

### 2. Verify Kaggle auth
```bash
kaggle config view >/dev/null 2>&1 || kaggle auth login
```
If `kaggle auth login` is invoked, surface the OAuth URL to the user and wait for them
to complete the browser flow. This is the only setup step that may block on user action.

### 3. Fetch Model Proxy credentials + scaffolding
```bash
kaggle b init -y          # writes .env, example_task.py, kaggle_benchmarks_reference.md
# Creds-only refresh (use when MODEL_PROXY_API_KEY has expired):
kaggle b auth -y
```

### 4. Report and proceed
Print one line summarizing what changed (packages upgraded, auth status, env vars refreshed),
then continue to the workflow without waiting for further confirmation.

## Core workflow: Write → Validate → Push → Run → Status → Log → Download → Publish (optional)

### Pacing — check in at authoring & execution steps
Setup is confirmed once up front and then runs to completion. `list`, `status`, and `log` are
read-only — run them without asking. For Write / Validate / Push / Run / Download, treat
each as a checkpoint: state the command, run it, show output, stop, and ask before
advancing. Chain only if the user explicitly says so.

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
kaggle b t push my-task -f task.py -d owner/dataset1 -d owner/dataset2   # attach datasets
```
`--wait [TIMEOUT]` blocks until server-side creation finishes (no arg = indefinite). `--poll-interval <SECONDS>` caps the polling interval (default 60s; polling starts at 5s and grows adaptively). Repeat `-d`/`--kaggle-dataset` once per dataset (do **not** space-separate; see the Gotchas).

### 4. Run
```bash
# Interactive picker
kaggle b t run my-task

# Specific model
kaggle b t run my-task -m google/gemini-3.5-flash

# Multiple models (repeat -m, do NOT space-separate)
kaggle b t run my-task -m google/gemini-3.5-flash -m anthropic/claude-haiku-4-5

# Wait for completion
kaggle b t run my-task -m google/gemini-3.5-flash --wait
```
List available models: `kaggle b t models`.

### 5. Status
```bash
kaggle b t status my-task
kaggle b t status my-task -m google/gemini-3.5-flash
```
Prints task metadata (slug, version, state, created timestamp, public flag, task URL) and a per-model run table. Errored runs render their final exception line under an `Errors:` section.

### 6. Log
*"Use this to confirm the run actually succeeded — status alone can show COMPLETED for a run that errored mid-stream."*
```bash
kaggle b t log my-task                            # logs for every run of the task
kaggle b t log my-task -m google/gemini-3.5-flash # filter to one model
kaggle b t log my-task -m model-a -m model-b      # multiple models, sequential
```
`RUNNING` runs stream live via SSE; `COMPLETED`/`ERRORED` runs print the persisted log in one shot; `QUEUED` runs print `(No logs available — server returned 404)` and continue.

### 7. Download
```bash
kaggle b t download my-task                       # all terminal runs
kaggle b t download my-task -o ./results          # custom directory
kaggle b t download my-task -m google/gemini-3.5-flash
kaggle b t download my-task -s                    # also fetch source notebooks
kaggle b t download my-task -f                    # force re-download (overwrite)
```
Output layout: `<output>/<task>/<version>/<model>/<run_id>/....` Already-downloaded runs are skipped unless `--force`/`-f` is passed. With `--include-source`/`-s`, each run's directory also contains `__notebook__.ipynb` and `__notebook_source__.ipynb` alongside the regular outputs (useful for debugging the kernel session).

### 8. Publish (optional)
*"Optional. Tasks can stay private indefinitely — only publish when you want the task and its backing notebook to be visible to other Kaggle users."*
```bash
kaggle b t publish my-task                              # publish task + backing notebook (default)
kaggle b t publish my-task --no-publish-backing-notebook  # publish task only, keep notebook private
```
Publishes both the task and the backing notebook by default. If the task is already public the command is a no-op for the task itself but will still publish the notebook unless `--no-publish-backing-notebook` is passed.

## Quick Recipes
**Reminder**: these are reference snippets, not invocations to chain automatically. Per the "Pacing" section above, run them one at a time with user confirmation between each, unless the user explicitly asks you to chain them.

```bash
# Push → run → download (run one command at a time, confirm between)
kaggle b t push my-task -f task.py --wait
kaggle b t run my-task -m google/gemini-3.5-flash --wait
kaggle b t download my-task -o ./results

# List tasks, filtered
kaggle b t list --name-regex "^math" --status errored

# Debug an errored run: pull logs first, then download source notebook
kaggle b t log my-task -m google/gemini-3.5-flash
kaggle b t download my-task -m google/gemini-3.5-flash -s -f
```

## Gotchas
Most of these are silent failures the agent will not detect on its own — review before generating any task file or CLI invocation.
- **No `.run()` call → silent no-op**. The push will succeed even if the file has no `.run()` (push validation only checks for `@task` decorators). The task will then execute on the server and produce no `.run.json`, so nothing is recorded. Every task function must end with `task_fn.run(kbench.llm)` (or `.evaluate(...)`).
- **`MODEL_PROXY_API_KEY` is short-lived**. If `python task.py` fails with an auth error, re-run `kaggle b auth -y` (or `kaggle b init -y`) to refresh.
- **`init` / `auth` append to the env file**. Loaded via `dotenv` so last-wins makes re-running safe, but the file accumulates duplicate entries over time.
- **Task slug must match a `@task` decorator**. `kaggle b t push <SLUG> -f file.py` fails if `<SLUG>` doesn't match the slugified name of some `@kbench.task(name=...)` (or function name) in the file. Names are normalized: `My Task` → `my-task`, `my_task` → `my-task`.
- **Server returns model slugs with `@default` suffix sometimes** (e.g. `google/gemini-3.5-flash@default`). The CLI normalizes `@` → `-` for matching; user-facing commands should use the plain `owner/model` form.
- **`delete` is not implemented server-side**. The command exists but currently prints `Delete is not supported by the server yet.`
- **Repeated flags, not space-separated**. For multi-value flags (`-m`, `-d`/`--kaggle-dataset`), pass the flag once per value: `-m a -m b`, not `-m a b`. Space-separated form is **not** supported and will error.
- **CLI scope is tasks only, not benchmarks**. A *benchmark* is a curated collection of tasks. The CLI lets you create, push, and run individual tasks, but creating or managing benchmarks (collections) must be done on the Kaggle web UI.
