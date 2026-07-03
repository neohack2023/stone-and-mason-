# Codex Mode for MASON

Codex can participate in STONE + MASON in two ways.

## 1. Repo mechanic mode

Best use:

- patch scripts
- improve workflows
- add provider adapters
- write tests
- improve JSON validation
- update docs

This is the safest and most natural Codex role.

```text
GitHub issue
→ Codex reads repo and AGENTS.md
→ Codex changes code/docs
→ Codex opens PR
→ human review
```

## 2. MASON operator mode

Possible use:

- process small inbox batches
- create memory cards
- create trigger cards
- build context packets

This should only happen through reviewable branches or pull requests.

```text
inbox note
→ Codex/MASON prompt
→ generated artifacts
→ PR review
```

## Why Codex is not the same as the local SLM

The local SLM is cheap, private, and good for routine curation.

Codex is stronger for codebase-aware repo work. It is better used as the builder and repair agent for the MASON system.

## Recommended provider stack

```text
provider=rule
  deterministic fallback for CI tests

provider=ollama
  local SLM through self-hosted runner

provider=codex
  optional higher-power repo-aware agent mode
```

## Guardrails

- Keep PRs as the approval gate.
- Keep raw receipts traceable.
- Do not auto-promote canon locks.
- Do not process large inbox batches without review.
- Do not remove rule mode.

## Codex handoff prompt

Use this when asking Codex to work on the repo:

```text
Read AGENTS.md first.
Work inside the STONE + MASON architecture.
Do not bypass the PR review gate.
Add or modify only the files needed for this issue.
Keep provider=rule working as the safe fallback.
If adding model-based behavior, validate JSON actions before writing files.
Every generated memory card must link back to a raw receipt.
```
