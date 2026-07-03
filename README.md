# STONE + MASON

**STONE** = Selective, Tagged, Optimized, Navigable, Evolving  
**MASON** = Memory Assembly System for Optimized Navigation

This repo turns the STONE + MASON memory workflow into a GitHub-native system.

The goal is not to store everything. The goal is to turn raw notes into the smallest useful context packet for the next task.

## Core flow

```text
inbox/ note
  ↓
MASON GitHub Action
  ↓
classify → summarize → tag → rank → merge → flag conflicts
  ↓
episodes/ + memory_cards/ + trigger_cards/ + context_packets/
  ↓
pull request for human review
```

## Repo folders

```text
inbox/              raw notes, prompt tests, tool outputs, lab receipts
raw_receipts/       archived source notes after processing
episodes/           compressed summaries of what happened
memory_cards/       reusable rules and lessons
trigger_cards/      retrieval hooks for memory cards
canon_locks/        high-priority rules that steer MASON
docs/               doctrine and workflow documentation
context_packets/    compact packets to feed an LLM
scripts/            MASON processing scripts
.github/workflows/  automation entrypoints
```

## First use

1. Add one markdown or text note to `inbox/`.
2. Run the **MASON Inbox Processor** workflow manually from the Actions tab.
3. Review the generated pull request.
4. Merge only if the generated memory cards are useful.

## Local SLM note

GitHub-hosted runners cannot reach your PC's local Ollama server. To use Ollama directly, run this workflow on a self-hosted runner installed on the same machine as Ollama.

Use the GitHub-hosted runner for deterministic rule-mode tests. Use a self-hosted runner for real local SLM curation.
