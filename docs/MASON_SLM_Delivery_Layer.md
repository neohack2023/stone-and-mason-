# MASON SLM Delivery Layer

**MASON** = Memory Assembly System for Optimized Navigation

MASON is the memory operator.

In GitHub mode, MASON reads repo files, processes `inbox/`, creates markdown memory artifacts, and opens a reviewable pull request.

## Tool-chain process

```text
intake
→ classify
→ summarize
→ tag
→ rank
→ merge
→ flag conflicts
→ create memory card
→ create trigger card
→ build context packet
```

## Responsibilities

MASON should:

- classify inbox notes
- summarize raw receipts
- extract reusable rules
- create memory cards
- create trigger cards
- build context packets
- flag stale or conflicting memory
- preserve raw evidence
- open reviewable pull requests

MASON should not:

- silently overwrite canon
- delete source notes
- promote everything to canon
- dump the whole repo into an LLM
- treat summaries as source truth without a receipt

## GitHub-native behavior

A MASON run should produce a branch and pull request with:

- archived raw receipt
- episode summary
- candidate memory card
- trigger card
- optional context packet
- processing report

Human review remains the final gate.
