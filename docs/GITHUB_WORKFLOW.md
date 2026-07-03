# GitHub Workflow

This repo moves STONE + MASON from a local Obsidian-only workflow into GitHub.

## Why GitHub

GitHub gives the system:

- versioned memory
- reviewable changes
- pull requests as human approval gates
- issues as structured inbox forms
- Actions as automation runners
- a clean audit trail

## Two operating modes

### 1. Rule mode

Runs on GitHub-hosted runners.

It uses deterministic extraction logic from `scripts/mason_github_process.py`.

Use this for:
- pipeline tests
- safe scaffolding
- confirming folder behavior

### 2. Local SLM mode

Runs on a self-hosted GitHub runner installed on the same PC as Ollama.

Use this when you want GitHub Actions to call the Ollama chat API on that same machine.

A GitHub-hosted runner cannot call your local Ollama because it runs on GitHub's servers, not your machine.

## Recommended flow

```text
1. Add one note to inbox/
2. Run MASON Inbox Processor
3. Inspect the generated branch / PR
4. Confirm episode, memory card, trigger card, and raw receipt archive
5. Merge if clean
```

## Permission model

Auto:
- create draft episode summaries
- create candidate memory cards
- create trigger cards
- archive raw receipts
- write reports

Human review:
- merge pull requests
- promote canon locks
- resolve conflicts
- retire memory
