# Self-Hosted Ollama Runner

GitHub-hosted runners cannot reach a local Ollama server on your PC.

To use the real local SLM through GitHub, run a GitHub self-hosted runner on the same machine as Ollama.

## Architecture

```text
GitHub Actions UI
  ↓
self-hosted runner on your PC
  ↓
Ollama localhost API
  ↓
local SLM
  ↓
repo branch and pull request
```

## Why this matters

GitHub becomes the control panel and audit trail. Your local machine supplies the model. The repo remains the source of truth.

## Required local pieces

- GitHub self-hosted runner
- Ollama running locally
- a small model such as `qwen2.5-coder:3b` or `llama3.2:3b`

## Recommended local model

For markdown filing, JSON, and action plans, start with:

```text
qwen2.5-coder:3b
```

## Safety rule

The SLM drafts memory changes. Pull requests remain the approval gate.
