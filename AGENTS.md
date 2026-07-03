# AGENTS.md

## Project

This repo is the GitHub-native STONE + MASON memory system.

STONE = Selective, Tagged, Optimized, Navigable, Evolving.
MASON = Memory Assembly System for Optimized Navigation.

The system turns raw notes into reviewable memory artifacts.

## Core workflow

```text
inbox note
→ classify
→ summarize
→ tag
→ rank
→ merge or flag duplicate
→ flag conflicts
→ create episode summary
→ create candidate memory card
→ create trigger card
→ archive raw receipt
→ create processing report
→ open or update PR for human review
```

## Folder contract

```text
inbox/              raw notes and tests waiting for processing
raw_receipts/       archived source notes after processing
episodes/           summaries of what happened and why it mattered
memory_cards/       reusable rules and lessons
trigger_cards/      retrieval hooks pointing to memory cards
canon_locks/        high-priority rules; do not modify casually
context_packets/    compact packets to feed a larger LLM
reports/            processing reports and audit traces
docs/               doctrine and architecture
scripts/            automation scripts
.github/workflows/  CI entrypoints
```

## Agent behavior rules

1. Preserve source traceability. Every memory card should point back to a raw receipt or source note.
2. Do not delete raw receipts.
3. Do not promote a rule to `canon_locks/` unless the user explicitly asks or the issue says canon promotion is the task.
4. Prefer pull requests over direct changes to `main` for generated memory artifacts.
5. Keep generated notes compact, readable, and frontmatter-compatible.
6. If a note contains a reusable lesson, do not only archive it. Extract the behavior.
7. If new evidence conflicts with an existing memory card or canon lock, create a conflict warning instead of overwriting.
8. Keep rule-mode processing available as a deterministic fallback.

## Required artifact shapes

### Episode summary

Destination: `episodes/`

Must include:
- frontmatter
- observation
- why it mattered
- reusable lesson
- source receipt link

### Candidate memory card

Destination: `memory_cards/`

Must include:
- frontmatter
- summary
- trigger
- action
- avoid
- source receipt link

### Trigger card

Destination: `trigger_cards/`

Must include:
- frontmatter
- match condition
- linked memory id
- trigger words

### Processing report

Destination: `reports/`

Must include:
- source file
- classification
- artifacts created
- conflicts found
- review notes

## Codex role

Codex should act as the repo mechanic and optional MASON operator.

Use Codex for:
- implementing provider adapters
- improving scripts
- adding tests
- validating markdown output
- improving GitHub Actions
- processing small inbox batches when explicitly requested

Do not use Codex to silently rewrite the memory vault without review.

## Preferred implementation path

1. Keep `scripts/mason_github_process.py` as the core entrypoint.
2. Add provider modes behind flags.
3. Preserve `provider=rule` as the fallback.
4. Add `provider=ollama` for self-hosted local SLM mode.
5. Add `provider=codex` only if Codex CLI or Codex GitHub Action is available in the execution environment.
6. Validate all model-proposed JSON before writing files.

## Safety gate

MASON drafts. Humans merge.
