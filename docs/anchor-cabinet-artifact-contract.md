# Anchor Cabinet Artifact Contract

**Status:** Proposed contract  
**Related ADR:** `decisions/ADR-0001-runtime-folding-and-recall-patterns.md`  
**Related Issue:** #9

## Purpose

The Anchor Cabinet preserves exact coordinates that future agents must not paraphrase, blur, or lose during folding, summarization, context-packet generation, or handoff.

It is the STONE + MASON runtime-pressure equivalent of an exact identifier register.

An Anchor Cabinet is not a memory card, not a canon lock, and not a summary. It is a compact coordinate list tied back to source evidence.

## Destination

Candidate Anchor Cabinet artifacts should live in a future reviewed artifact area only after the folder is explicitly approved.

Until then, Anchor Cabinet examples and contracts live in `docs/` only.

Recommended future destination if approved:

```text
anchor_cabinets/
```

Do not create that folder automatically unless a task packet explicitly allows it.

## When to Create One

Create or update an Anchor Cabinet candidate when a source note, raw receipt, issue, PR, or agent session contains coordinates likely to matter later.

Typical triggers:

- a file path is mentioned as active or risky
- a branch, issue, PR, or commit is part of the task boundary
- a workflow or script is referenced
- an error string may need exact matching later
- a provider, model, mode, port, or environment flag steers behavior
- a project identifier must remain stable across handoff
- a hazard depends on a precise path or name

## Required Frontmatter

```yaml
---
type: anchor_cabinet
status: candidate
id: anchor-cabinet-YYYYMMDD-short-slug
source_receipt: raw_receipts/path-or-null.md
scope: repo | issue | pr | session | task | project
created: YYYY-MM-DD
review_required: true
---
```

## Required Body Sections

Every Anchor Cabinet candidate must include these sections:

1. `## Scope`
2. `## Source Trace`
3. `## Anchors`
4. `## Matching Rules`
5. `## Exclusions`
6. `## Review Notes`

## Anchor Categories

Use these categories when present. Omit empty categories.

```yaml
anchors:
  repos: []
  paths: []
  folders: []
  branches: []
  issues: []
  prs: []
  commits: []
  workflows: []
  scripts: []
  providers: []
  models: []
  ports: []
  environment_flags: []
  error_strings: []
  project_identifiers: []
  people_or_handles: []
  external_urls: []
```

## Category Rules

### repos

Use `owner/name` form.

```yaml
repos:
  - neohack2023/stone-and-mason-
```

### paths

Use repository-relative file paths unless the absolute path is itself the important coordinate.

```yaml
paths:
  - scripts/mason_github_process.py
  - decisions/ADR-0001-runtime-folding-and-recall-patterns.md
```

### folders

Use trailing slash.

```yaml
folders:
  - context_packets/
  - trigger_cards/
```

### branches

Use exact branch names.

```yaml
branches:
  - agent/anchor-cabinet-contract
```

### issues and prs

Use quoted GitHub numbers so YAML does not treat `#` as a comment.

```yaml
issues:
  - "#9"
prs:
  - "#8"
```

### commits

Use full SHA when available. Use short SHA only when the source only provides short SHA.

```yaml
commits:
  - 6a8be62a70f74d3315b03fa6a6e61dee23619405
```

### workflows

Use exact visible workflow names.

```yaml
workflows:
  - MASON Inbox Processor
```

### scripts

Use repository-relative script entrypoints.

```yaml
scripts:
  - scripts/mason_github_process.py
```

### providers and models

Use exact provider modes, model names, or adapter labels.

```yaml
providers:
  - provider=rule
  - provider=ollama
models:
  - gpt-5.5
```

### ports

Use strings if the port is part of a larger exact expression.

```yaml
ports:
  - "port=3002"
```

### environment_flags

Use exact flag names and values when known.

```yaml
environment_flags:
  - WARP_CLAUDE_CLI_FOLD=dry-run
```

### error_strings

Preserve exact capitalization and punctuation.

```yaml
error_strings:
  - JSON validation failed
```

### project_identifiers

Use approved project names or domain-specific identifiers.

```yaml
project_identifiers:
  - STONE + MASON
  - Anchor Cabinet
```

### people_or_handles

Use only when the person or handle is operationally relevant to the task.

```yaml
people_or_handles:
  - neohack2023
```

### external_urls

Use only source or reference URLs needed for traceability.

```yaml
external_urls:
  - https://github.com/dogtorjonah/context-warp-drive
```

## Matching Rules

Each cabinet must describe how its anchors should trigger recall.

Use this shape:

```yaml
matching_rules:
  strong_match:
    - exact path match
    - exact issue or PR number match
    - exact branch name match
  weak_match:
    - project phrase appears without a path or issue
    - provider name appears without a task boundary
  do_not_match:
    - generic words like memory, context, agent, docs, or workflow by themselves
```

## Exclusions

Anchor Cabinets must explicitly exclude vague or unsafe recall triggers.

Good exclusions:

```text
Do not trigger recall from the word "memory" alone.
Do not trigger recall from "docs" alone.
Do not trigger recall from generic model-family names unless paired with a task boundary.
Do not preserve secrets, tokens, passwords, cookies, or `.env` values.
```

## Source Trace

Every cabinet must point back to evidence.

Preferred order:

1. raw receipt path
2. issue number
3. PR number
4. commit SHA
5. source URL
6. local note reference when no better source exists

If no source receipt exists yet, write:

```text
Source receipt: not yet available; derived from reviewed issue/PR context.
```

## Review Notes

Review notes should call out:

- ambiguous anchors
- anchors intentionally omitted
- conflicts with canon locks or memory cards
- whether future automation may create this artifact
- whether the candidate is safe for durable storage

## Complete Example

```yaml
---
type: anchor_cabinet
status: candidate
id: anchor-cabinet-20260704-runtime-folding-doctrine
source_receipt: null
scope: issue
created: 2026-07-04
review_required: true
---
```

## Scope

Runtime folding and recall doctrine for STONE + MASON.

## Source Trace

- Issue: `#9`
- Prior PR: `#8`
- ADR: `decisions/ADR-0001-runtime-folding-and-recall-patterns.md`

## Anchors

```yaml
anchors:
  repos:
    - neohack2023/stone-and-mason-
  paths:
    - decisions/ADR-0001-runtime-folding-and-recall-patterns.md
    - docs/runtime-memory-pressure-patterns.md
    - docs/anchor-cabinet-artifact-contract.md
  folders:
    - docs/
    - decisions/
  branches:
    - agent/anchor-cabinet-contract
  issues:
    - "#9"
  prs:
    - "#8"
  commits:
    - 6a8be62a70f74d3315b03fa6a6e61dee23619405
  workflows:
    - MASON Inbox Processor
  scripts:
    - scripts/mason_github_process.py
  providers:
    - provider=rule
    - provider=ollama
  project_identifiers:
    - STONE + MASON
    - Anchor Cabinet
    - Deterministic Fold Card
    - Recall Triggers v2
    - Re-entry Packet
    - Action Rail
    - Trust Register
  external_urls:
    - https://github.com/dogtorjonah/context-warp-drive
```

## Matching Rules

```yaml
matching_rules:
  strong_match:
    - exact issue match: "#9"
    - exact PR match: "#8"
    - exact path match inside docs/ or decisions/
    - exact project identifier match: Anchor Cabinet
  weak_match:
    - STONE + MASON appears without artifact or path context
    - provider=rule appears without MASON context
  do_not_match:
    - memory alone
    - context alone
    - workflow alone
```

## Exclusions

- Do not include secrets, tokens, cookies, or `.env` values.
- Do not trigger recall from generic words alone.
- Do not treat this cabinet as a canon lock.

## Review Notes

This contract is documentation-only. Future automation must not write Anchor Cabinet artifacts until a separate implementation PR approves the destination folder, validation rules, and report behavior.

## Validation Checklist

Before accepting an Anchor Cabinet candidate:

- [ ] Frontmatter is present.
- [ ] `type` is `anchor_cabinet`.
- [ ] `status` is `candidate` unless explicitly promoted by review.
- [ ] Source trace exists.
- [ ] Anchors are exact, not paraphrased.
- [ ] Issue and PR numbers are quoted.
- [ ] File paths are repository-relative.
- [ ] Folders use trailing slash.
- [ ] Empty categories are omitted.
- [ ] Matching rules include strong, weak, and do-not-match lanes.
- [ ] Exclusions forbid secrets and vague recall triggers.
- [ ] Review notes identify ambiguity or confirm none found.

## Non-goals

This contract does not approve:

- a new `anchor_cabinets/` folder
- script changes
- workflow changes
- automatic extraction
- dependency additions
- canon lock promotion

Those require separate task packets and human-reviewed PRs.
