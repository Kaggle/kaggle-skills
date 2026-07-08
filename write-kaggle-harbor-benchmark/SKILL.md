---
name: write-kaggle-harbor-benchmark
description: Use when creating, running, validating, or documenting a Kaggle benchmark repository that uses Harbor task specifications, custom autonomous agents, or Kaggle model proxy routing.
---

# Write Kaggle Harbor Benchmarks

Kaggle supports agentic benchmarks written using the [Harbor](https://github.com/harbor-framework/harbor) specification by executing individual tasks inside Docker containers with `harbor run`.

This enables a clear, local-first workflow:

1. **Route via Model Proxy:** All language model calls must pass through Kaggle's Model Proxy (`MODEL_PROXY_URL`). This ensures execution traces are automatically logged for benchmark scoring and evaluation reports, while keeping provider API keys secure and managed by Kaggle without embedding private credentials in agent code.
2. **Iterate Locally with Harbor:** Start by running your oracle solution or verification script directly to confirm environment correctness, then run a lightweight built-in agent (such as `mini-swe-agent`) with `harbor run` to iterate on your instructions and tests.
3. **Verify in Kaggle Runner:** Use the packaged Kaggle runner image to verify everything works and then ping Kaggle team to verify.

## Model Proxy

**Note:** `MODEL_PROXY_API_KEY` expires after a short duration. Re-run `kaggle benchmarks auth -y --env-file .env` when it expires

Kaggle provides free inference credits to verified accounts and logs language model calls via a OpenAI Chat Competions/ Anthropic Messages API compatible Model Proxy.

To get started:

1. **Request a quota increase** : Email your Kaggle username to Ivan at __ileo@google.com__ and we'll bump your quota and grant access to more models.

2. **Configure CLI**: You'll then need to install the CLI and then generate your local credentials.

```bash
uv tool install kaggle
kaggle auth login
kaggle benchmarks auth -y --env-file .env
```

3. **Test model access**: Verify model access with a quick `curl` request (OpenAI-compatible or Anthropic-compatible):

   **OpenAI-Compatible Endpoint:**
   ```bash
   source .env

   curl "${MODEL_PROXY_URL%/}/openapi/v1/chat/completions" \
     -H "Authorization: Bearer ${MODEL_PROXY_API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{"model":"google/gemini-3.5-flash","messages":[{"role":"user","content":"Reply with exactly: ok"}]}'
   ```

   **Anthropic-Compatible Endpoint:**
   ```bash
   source .env

   curl "${MODEL_PROXY_URL%/}/anthropic/v1/messages" \
     -H "x-api-key: ${MODEL_PROXY_API_KEY}" \
     -H "anthropic-version: 2023-06-01" \
     -H "Content-Type: application/json" \
     -d '{"model":"google/gemini-3.5-flash","messages":[{"role":"user","content":"Reply with exactly: ok"}],"max_tokens":20}'
   ```

<---- [ add this divider for old stuff for now we'll work through section by section ] ---

## Creating Your First Task

Harbor provides a scaffolding tool to generate a standard task directory structure. 

Initialize a new task by running:
```bash
harbor init -t my-org/my-task -o tasks/my-task
```

This generates:
```text
tasks/my-task/
├── task.toml            # Task metadata, timeouts, resource limits
├── instruction.md       # Prompt/problem statement given to the agent
├── environment/
│   └── Dockerfile       # Container sandbox definition
├── tests/
│   ├── test.sh          # Verifier entrypoint script
│   └── test_outputs.py  # Pytest verification tests
└── solution/            # Optional oracle reference solution
```

*Tip: Keep your first task small and deterministic (e.g., creating a single file with specific contents) to verify the pipeline.*

## Running Your Task Locally

Once your task is scaffolded, you can test it locally using a lightweight built-in agent (such as `mini-swe-agent`) routed through the Kaggle Model Proxy:

```bash
source .env

harbor run \
  -p tasks/my-task \
  -a mini-swe-agent \
  -m openai/google/gemini-3.5-flash \
  --ae OPENAI_API_KEY="${MODEL_PROXY_API_KEY}" \
  --ae OPENAI_BASE_URL="${MODEL_PROXY_URL%/}/openapi/v1"
```

## Verifying in Kaggle Runner Image

Once local validation passes, verify your repository inside the official Kaggle runner image (`us-west1-docker.pkg.dev/kaggle-playground-170215/kaggle-benchmarks/harbor-test:latest`), which supports both **amd64** and **arm64** architectures.

The runner performs repository cloning and Docker-in-Docker execution. Run a smoke test by passing your repository URL, task path, and agent:

```bash
source .env

docker run --privileged --rm \
  -e MODEL_PROXY_URL="${MODEL_PROXY_URL}" \
  -e MODEL_PROXY_API_KEY="${MODEL_PROXY_API_KEY}" \
  -e KAGGLE_TASK_REPO_URL="https://github.com/my-org/my-repo" \
  -e KAGGLE_TASK_PATH="tasks/my-task" \
  -e KAGGLE_HARBOR_AGENT="mini-swe-agent" \
  -e KAGGLE_HARBOR_MODEL="openai/google/gemini-3.5-flash" \
  -e DOCKERD_STORAGE_DRIVER="vfs" \
  us-west1-docker.pkg.dev/kaggle-playground-170215/kaggle-benchmarks/harbor-test:latest
```

*Note: `-e DOCKERD_STORAGE_DRIVER="vfs"` is required when running on macOS Docker Desktop because the container runs Docker-in-Docker. For private GitHub repositories, also pass `-e KAGGLE_GIT_TOKEN="$(gh auth token)"`.*

## Custom Agents & Next Steps

If you are evaluating a custom autonomous agent rather than a built-in agent, implement a Harbor agent adapter. Refer to the [Harbor Agents Documentation](https://www.harborframework.com/docs/agents) for full details on building custom SDK and CLI agent adapters.

Once verified locally and in the runner image, email **ileo@google.com** to review and publish your benchmark on Kaggle!
