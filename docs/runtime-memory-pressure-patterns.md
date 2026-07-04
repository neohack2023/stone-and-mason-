# Runtime Memory Pressure Patterns for MASON

**Status:** Proposed doctrine  
**Related ADR:** `decisions/ADR-0001-runtime-folding-and-recall-patterns.md`  
**Related Issue:** #7

## Purpose

STONE + MASON already handles durable memory: raw notes become reviewed episodes, memory cards, trigger cards, reports, and context packets.

This page defines a proposed runtime pressure layer for future MASON work. Its job is to keep long-running agent sessions bounded, exact, and recoverable without promoting loose chat residue into canon.

The core rule stays unchanged:

```text
MASON drafts. Humans merge.
```

## Layer Separation

| Layer | Owns | Must not do |
|---|---|---|
| Raw receipts | Source trace and audit trail | Disappear or be overwritten |
| Episodes | Compressed history of what happened | Pretend to be full source truth |
| Memory cards | Reusable lessons and behavioral rules | Become canon without review |
| Trigger cards | Retrieval hooks | Retrieve vague vibes without anchors |
| Context packets | Compact task input for an LLM | Hide conflicts or missing evidence |
| Runtime pressure layer | Fold, recall, restart, and execution state | Rewrite durable memory directly |

## Proposed MASON Terms

### Anchor Cabinet

The Anchor Cabinet is a deterministic list of exact coordinates extracted from raw activity.

Use it for values that must not be paraphrased:

- repository names
- file paths
- branch names
- issue and PR numbers
- commit SHAs
- workflow names
- script entrypoints
- model/provider names
- ports
- exact error strings
- user-approved project identifiers

Example:

```yaml
---
type: anchor_cabinet
status: candidate
source_receipt: raw_receipts/2026-07-04-example.md
---

anchors:
  repos:
    - neohack2023/stone-and-mason-
  paths:
    - scripts/mason_github_process.py
    - context_packets/
    - trigger_cards/
  issues:
    - "#7"
  workflows:
    - MASON Inbox Processor
  providers:
    - provider=rule
    - provider=ollama
```

### Deterministic Fold Card

A Deterministic Fold Card is a compact skeleton of older activity. It should be built by rules first, not by an LLM summary first.

It should preserve:

- what was touched
- what was decided
- what remains open
- exact anchors from the Anchor Cabinet
- source receipt links

Example:

```yaml
---
type: deterministic_fold_card
status: candidate
source_receipt: raw_receipts/2026-07-04-example.md
---

fold:
  objective: Add runtime memory pressure doctrine.
  touched:
    - decisions/ADR-0001-runtime-folding-and-recall-patterns.md
    - docs/runtime-memory-pressure-patterns.md
  settled:
    - No dependency import approved.
    - No workflow changes approved.
  open:
    - Human must decide whether to promote proposed doctrine.
  anchors:
    - "#7"
    - agent/context-warp-drive-doctrine
```

### Recall Triggers v2

Recall Triggers v2 are stronger trigger cards. They should match specific evidence, not fog.

Recommended trigger lanes:

| Lane | Example |
|---|---|
| Path | `scripts/mason_github_process.py` |
| Folder | `context_packets/` |
| Issue / PR | `#7`, `PR #8` |
| Error string | `JSON validation failed` |
| Provider | `provider=ollama` |
| Workflow | `MASON Inbox Processor` |
| Project phrase | `STONE + MASON`, `Anchor Cabinet` |
| Risk signal | `canon_locks/`, `.github/workflows/`, dependency files |

Trigger cards should point to memory cards, fold cards, and context packets only when the match is strong enough to help the next task.

### Re-entry Packet

A Re-entry Packet is a deterministic wake-up packet for long threads, agent restarts, or handoffs.

It should answer:

```text
What are we doing?
What repo and branch are active?
What issue or PR controls scope?
What files were touched?
What exact anchors must be preserved?
What hazards exist?
What checks ran?
What is the next safe action?
```

Suggested shape:

```yaml
---
type: reentry_packet
status: candidate
scope_issue: "#7"
branch: agent/context-warp-drive-doctrine
---

objective: Add proposed runtime memory pressure doctrine.
active_files:
  - decisions/ADR-0001-runtime-folding-and-recall-patterns.md
  - docs/runtime-memory-pressure-patterns.md
anchors:
  - neohack2023/stone-and-mason-
  - Context Warp Drive
  - Anchor Cabinet
hazards:
  - Do not add dependencies in this task.
  - Do not modify workflows in this task.
next_action: Open PR for human review.
```

### Action Rail

An Action Rail keeps execution state outside the prompt. It should not replace an issue. It is the agent's short-lived work spine.

Suggested shape:

```yaml
---
type: action_rail
status: active
scope_issue: "#7"
---

objective: Add documentation-only architecture proposal.
steps:
  - id: read-canon
    status: done
    evidence: AGENTS.md and README.md inspected.
  - id: create-branch
    status: done
    evidence: agent/context-warp-drive-doctrine
  - id: add-docs
    status: done
    evidence: ADR and runtime doctrine page created.
  - id: open-pr
    status: next
```

### Trust Register

A Trust Register marks whether a note is temporary, executing, settled, hazardous, or blocked before MASON harvests it.

Recommended plain-text values for MASON artifacts:

| Register | Meaning | Durable? |
|---|---|---:|
| `in_progress` | investigation or hypothesis | No |
| `executing` | tool/edit/test activity | No |
| `verdict` | verified conclusion | Yes |
| `hazard` | trap or invariant future agents need | Yes |
| `blocked` | needs human input or missing evidence | No |

MASON should prefer durable registers when creating memory cards and should avoid treating mid-investigation notes as settled truth.

## Retrieval Order

When building a context packet for a task, MASON should prefer this order:

1. Explicit task packet or issue.
2. `AGENTS.md` and repo-level contracts.
3. Relevant specs and decisions.
4. Canon locks only when explicitly relevant.
5. Anchor Cabinet entries matching the task.
6. Trigger cards matching exact paths, IDs, providers, workflow names, or error strings.
7. Recent episodes and memory cards.
8. Deterministic Fold Cards.
9. Raw receipts only when traceability or conflict review is needed.

## Non-goals

This proposal does not approve:

- importing Context Warp Drive as a dependency
- changing `.github/workflows/`
- changing `scripts/mason_github_process.py`
- promoting any new rule into `canon_locks/`
- automatically rewriting memory cards
- treating external project terminology as STONE + MASON canon without review

## Future Implementation Notes

A future implementation should start with rule-mode only:

```text
raw receipt
  -> extract anchors
  -> create deterministic fold card
  -> upgrade trigger matching
  -> create candidate re-entry packet
  -> generate report
  -> open PR
```

Only after the artifact shapes are stable should MASON consider SLM enrichment or third-party dependencies.
