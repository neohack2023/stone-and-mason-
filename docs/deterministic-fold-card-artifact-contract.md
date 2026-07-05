# Deterministic Fold Card Artifact Contract

**Status:** Proposed contract  
**Related ADR:** `decisions/ADR-0001-runtime-folding-and-recall-patterns.md`  
**Related Issue:** #11

## Purpose

A Deterministic Fold Card is a compact, repeatable skeleton of older activity.

Its job is to preserve task continuity under context pressure without replacing raw receipts, episodes, memory cards, trigger cards, or human review.

A Deterministic Fold Card must be rule-first. It may later be enriched by an SLM, but the source-of-truth skeleton must be computable from explicit inputs and exact anchors.

## Non-negotiable Rule

```text
Raw receipts remain the source trace.
Deterministic Fold Cards are compact views.
Loose summaries are not canonical source truth.
```

## Destination

Candidate Deterministic Fold Card artifacts should live in a future reviewed artifact area only after the folder is explicitly approved.

Until then, examples and contracts live in `docs/` only.

Recommended future destination if approved:

```text
fold_cards/
```

Do not create that folder automatically unless a task packet explicitly allows it.

## When to Create One

Create a Deterministic Fold Card candidate when older activity needs to be compressed for handoff, retrieval, or context-packet generation.

Typical triggers:

- a long issue/PR/task thread needs compact handoff
- several raw receipts refer to the same task boundary
- an agent session touched multiple files and needs a stable restart skeleton
- older work should be recallable by exact anchors
- a context packet needs compact history without rereading every receipt
- a conflict or hazard depends on preserving what was touched and decided

## Required Frontmatter

```yaml
---
type: deterministic_fold_card
status: candidate
id: fold-card-YYYYMMDD-short-slug
source_receipts:
  - raw_receipts/path-or-null.md
scope: repo | issue | pr | session | task | project
created: YYYY-MM-DD
review_required: true
anchor_cabinet: path-or-null
---
```

## Required Body Sections

Every Deterministic Fold Card candidate must include these sections:

1. `## Scope`
2. `## Source Trace`
3. `## Fold Summary`
4. `## Touched Surfaces`
5. `## Settled Outcomes`
6. `## Open Threads`
7. `## Hazards`
8. `## Anchors Preserved`
9. `## Exclusions`
10. `## Review Notes`

## Fold Lanes

Use these lanes in the `Fold Summary` section.

```yaml
fold:
  objective: ""
  time_window: ""
  mode: documentation | architecture | development | review | maintenance | research | prompt_lab | local_slm
  status: in_progress | blocked | completed | abandoned | superseded
  source_count: 0
  confidence: low | medium | high
```

### objective

One sentence describing the bounded task.

### time_window

Use an exact date or range when known. Do not use vague phrasing like "recently" unless the source itself lacks dates.

### mode

Use the active repo-governor mode.

### status

Use the state of the folded work, not the desired future state.

### source_count

Count source receipts or source references used to build the card.

### confidence

Use:

- `high` when all major claims have source trace and exact anchors
- `medium` when source trace exists but some context is incomplete
- `low` when the fold is mostly a handoff clue and must be verified before use

## Touched Surfaces

List concrete files, folders, workflows, issues, PRs, and branches touched or discussed.

Recommended shape:

```yaml
touched_surfaces:
  files: []
  folders: []
  workflows: []
  issues: []
  prs: []
  branches: []
  external_refs: []
```

Rules:

- Use repo-relative file paths.
- Use trailing slash for folders.
- Quote issue and PR numbers.
- Do not include generic nouns.
- If a surface was only mentioned but not changed, add a note in `Review Notes`.

## Settled Outcomes

Settled outcomes are verified results or explicit decisions.

Use short bullets, each tied to source trace.

Good:

```text
- ADR-0001 was accepted after PR #10 merged.
- Anchor Cabinet contract was defined as documentation-only.
```

Bad:

```text
- The system is much better now.
- We basically solved memory.
```

Settled outcomes must not include speculation.

## Open Threads

Open threads are unfinished next steps, unresolved questions, or future task candidates.

Each open thread should include:

```yaml
open_threads:
  - item: "Define Recall Triggers v2 contract."
    reason: "ADR-0001 implementation sequence lists it after fold-card rules."
    next_safe_action: "Create a documentation-only issue and draft PR."
```

## Hazards

Hazards are durable warnings future agents should not miss.

Examples:

```yaml
hazards:
  - "Do not create `fold_cards/` until a separate task packet approves the folder."
  - "Do not treat LLM-generated summaries as source truth."
  - "Do not modify `.github/workflows/` while defining artifact contracts."
```

## Anchors Preserved

Deterministic Fold Cards should reference an Anchor Cabinet when one exists.

They may inline anchors only when no Anchor Cabinet exists yet.

Recommended shape:

```yaml
anchors_preserved:
  anchor_cabinet: docs/anchor-cabinet-artifact-contract.md
  repos: []
  paths: []
  issues: []
  prs: []
  commits: []
  branches: []
  workflows: []
  project_identifiers: []
```

## Source Trace

Every fold card must point back to evidence.

Preferred order:

1. raw receipt path
2. issue number
3. PR number
4. commit SHA
5. ADR or docs path
6. source URL
7. local note reference when no better source exists

If no raw receipt exists yet, write:

```text
Raw receipt: not yet available; derived from reviewed issue/PR context.
```

## Deterministic Build Rules

A fold card should be reproducible from the same inputs.

Minimum deterministic rules:

1. Sort paths alphabetically unless chronology matters.
2. Preserve exact casing and punctuation for paths, branches, errors, and identifiers.
3. Quote issue and PR numbers.
4. Omit empty anchor categories.
5. Keep settled outcomes separate from open threads.
6. Keep hazards separate from ordinary notes.
7. Keep speculation out of settled outcomes.
8. Never collapse multiple distinct files into vague folder prose unless the folder itself is the anchor.
9. Prefer source references over narrative explanation.
10. If an SLM enrichment disagrees with the rule-built skeleton, the rule-built skeleton wins until human review.

## SLM Enrichment Boundary

An SLM may help polish language or suggest classifications only after the deterministic skeleton exists.

Allowed SLM enrichment:

- improve readability
- suggest missing open threads
- suggest possible hazards
- suggest confidence level
- suggest trigger terms for a future trigger card

Forbidden SLM enrichment:

- inventing touched files
- replacing exact anchors with paraphrases
- promoting speculation into settled outcomes
- deleting source trace
- changing issue/PR/commit/path values
- hiding uncertainty

## Matching Behavior

Deterministic Fold Cards should be recallable by exact anchors, not generic phrasing.

Recommended matching lanes:

```yaml
matching:
  strong_match:
    - exact file path
    - exact branch name
    - exact issue or PR number
    - exact commit SHA
    - exact project identifier
  weak_match:
    - related artifact name without issue or path
    - mode name plus project phrase
  do_not_match:
    - memory alone
    - context alone
    - docs alone
    - agent alone
```

## Exclusions

Every fold card must exclude unsafe or noisy recall.

Required exclusions:

```text
Do not include secrets, tokens, passwords, cookies, or `.env` values.
Do not trigger recall from generic words alone.
Do not treat this fold as a replacement for raw receipts.
Do not treat this fold as a canon lock.
Do not treat unreviewed SLM prose as settled fact.
```

## Complete Example

```yaml
---
type: deterministic_fold_card
status: candidate
id: fold-card-20260705-anchor-cabinet-contract
source_receipts:
  - null
scope: pr
created: 2026-07-05
review_required: true
anchor_cabinet: docs/anchor-cabinet-artifact-contract.md
---
```

## Scope

Follow-up documentation work after accepting ADR-0001 and defining the Anchor Cabinet artifact contract.

## Source Trace

- PR: `#10`
- Issue: `#9`
- Merge commit: `8ebff6213b4230601662c1bba4b55093cc4fb042`
- ADR: `decisions/ADR-0001-runtime-folding-and-recall-patterns.md`
- Contract: `docs/anchor-cabinet-artifact-contract.md`

Raw receipt: not yet available; derived from reviewed issue/PR context.

## Fold Summary

```yaml
fold:
  objective: "Accept ADR-0001 and define the Anchor Cabinet contract."
  time_window: "2026-07-04 to 2026-07-05"
  mode: architecture
  status: completed
  source_count: 4
  confidence: high
```

## Touched Surfaces

```yaml
touched_surfaces:
  files:
    - decisions/ADR-0001-runtime-folding-and-recall-patterns.md
    - docs/anchor-cabinet-artifact-contract.md
  folders:
    - decisions/
    - docs/
  workflows: []
  issues:
    - "#9"
  prs:
    - "#10"
  branches:
    - agent/anchor-cabinet-contract
  external_refs:
    - https://github.com/dogtorjonah/context-warp-drive
```

## Settled Outcomes

- ADR-0001 was marked Accepted after PR #8 merged.
- The Anchor Cabinet contract was defined as documentation-only.
- No `anchor_cabinets/` folder was created.
- No scripts, workflows, dependencies, or runtime behavior were changed.

## Open Threads

```yaml
open_threads:
  - item: "Define Deterministic Fold Card contract."
    reason: "ADR-0001 lists deterministic fold-card rules after Anchor Cabinet shape."
    next_safe_action: "Create docs-only issue and draft PR."
  - item: "Define Recall Triggers v2 contract."
    reason: "Recall requires exact trigger lanes after fold-card rules are stable."
    next_safe_action: "Wait until fold-card contract is reviewed."
```

## Hazards

```yaml
hazards:
  - "Do not create `anchor_cabinets/` without a separate task packet."
  - "Do not modify `scripts/` while defining artifact contracts."
  - "Do not use loose summaries as canonical source truth."
```

## Anchors Preserved

```yaml
anchors_preserved:
  anchor_cabinet: docs/anchor-cabinet-artifact-contract.md
  repos:
    - neohack2023/stone-and-mason-
  paths:
    - decisions/ADR-0001-runtime-folding-and-recall-patterns.md
    - docs/anchor-cabinet-artifact-contract.md
  issues:
    - "#9"
  prs:
    - "#10"
  commits:
    - 8ebff6213b4230601662c1bba4b55093cc4fb042
  branches:
    - agent/anchor-cabinet-contract
  workflows: []
  project_identifiers:
    - STONE + MASON
    - Anchor Cabinet
    - Deterministic Fold Card
```

## Exclusions

- Do not include secrets, tokens, cookies, passwords, or `.env` values.
- Do not trigger recall from `memory`, `context`, `docs`, or `agent` alone.
- Do not treat this fold card as a canon lock.
- Do not treat this fold card as a replacement for raw receipts.

## Review Notes

This example is documentation-only. Future automation must not write Deterministic Fold Cards until a separate implementation PR approves the destination folder, validation rules, and processing-report behavior.

## Validation Checklist

Before accepting a Deterministic Fold Card candidate:

- [ ] Frontmatter is present.
- [ ] `type` is `deterministic_fold_card`.
- [ ] `status` is `candidate` unless explicitly promoted by review.
- [ ] Source trace exists.
- [ ] Raw receipts are referenced when available.
- [ ] Fold summary uses the required lanes.
- [ ] Touched surfaces use exact paths and quoted issue/PR numbers.
- [ ] Settled outcomes are verified and non-speculative.
- [ ] Open threads include a reason and next safe action.
- [ ] Hazards are separated from ordinary notes.
- [ ] Anchors are exact and preferably linked to an Anchor Cabinet.
- [ ] Empty anchor categories are omitted unless shown in examples for clarity.
- [ ] Matching rules include strong, weak, and do-not-match lanes.
- [ ] Exclusions forbid secrets and vague recall triggers.
- [ ] Review notes identify ambiguity or confirm none found.

## Non-goals

This contract does not approve:

- a new `fold_cards/` folder
- script changes
- workflow changes
- automatic extraction
- dependency additions
- canon lock promotion
- using SLM summaries as source truth

Those require separate task packets and human-reviewed PRs.
