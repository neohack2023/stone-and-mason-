# ADR-0001: Runtime Folding and Recall Patterns for MASON

**Status:** Accepted  
**Date:** 2026-07-04  
**Accepted:** 2026-07-04 via PR #8  
**Owner:** Human developer  
**Related Issue/PR:** #7, #8, #9

## Context

STONE + MASON is a GitHub-native memory refinery. Its current repo contract turns raw inbox notes into reviewable artifacts: episode summaries, candidate memory cards, trigger cards, archived receipts, processing reports, and pull requests for human review.

That model protects durable memory, but long-running agent sessions also need a runtime pressure layer. Agent context can fill up before a durable MASON packet is ready. If the runtime layer uses loose LLM summaries, it can blur file paths, issue numbers, commit SHAs, branch names, workflow names, and other exact identifiers that future agents need.

The external Context Warp Drive project demonstrates a useful pattern family:

- deterministic rolling folds instead of repeated LLM summarization
- exact identifier conservation through a Coordinate Closet
- frozen folded prefixes for cache-hot reuse
- fold recall when touched paths or identifiers become relevant again
- hard-epoch rebirth seeds for bounded long-horizon sessions
- task rails to keep execution state outside the prompt
- register glyphs that distinguish transient work from durable verdicts or hazards

This ADR does not approve importing that package. It evaluates the pattern family and names the STONE + MASON equivalents.

## Decision

Adopt the following architecture terms as **MASON vNext doctrine**:

| External pattern | MASON term | Purpose |
|---|---|---|
| Coordinate Closet | Anchor Cabinet | Preserve exact paths, SHAs, issue refs, branch names, ports, model names, and workflow IDs. |
| Rolling fold | Deterministic Fold Card | Create repeatable structural skeletons from raw activity before any SLM enrichment. |
| Fold recall | Recall Triggers v2 | Page relevant folded material back in when a path, identifier, project, or error string reappears. |
| Hard-epoch rebirth seed | Re-entry Packet | Restart an agent cleanly with objective, active files, hazards, anchors, and next action. |
| Task Rail | Action Rail | Track execution state outside the prompt so folding does not erase the plan. |
| Register glyph grammar | Trust Register | Mark work as transient, executing, verdict, hazard, or blocked before harvesting durable memory. |

The first implementation step remains documentation-only. No dependency, workflow, or production script change is approved by this ADR.

Future implementation should be split into separate agent task packets, likely in this order:

1. Define Anchor Cabinet artifact shape.
2. Define deterministic fold-card rules.
3. Upgrade trigger-card matching to support paths, IDs, error strings, and workflow names.
4. Define Re-entry Packet shape for long-thread handoff.
5. Define Action Rail shape for execution state.
6. Decide whether a dependency or local implementation is justified.

## Consequences

### Benefits

- Keeps STONE + MASON aligned with its existing goal: smallest useful context packet, not full-history hoarding.
- Adds a runtime pressure layer without weakening repo-as-truth doctrine.
- Reduces identifier drift by making exact coordinate preservation explicit.
- Gives future agents cleaner restart packets.
- Separates temporary reasoning from durable memory candidates.

### Costs

- Adds new vocabulary that must be kept disciplined.
- Creates more artifact categories to govern if promoted later.
- Future implementation could increase script complexity.
- Any dependency import would require a separate review and dependency policy check.

### Risk Controls

- Do not modify `canon_locks/` as part of this ADR.
- Do not modify `.github/workflows/` as part of this ADR.
- Do not add package dependencies as part of this ADR.
- Require a new issue and PR before touching `scripts/`.
- Keep future artifact contracts reviewable before automation writes those artifacts.

## Alternatives Considered

### Option A: Import Context Warp Drive immediately

Rejected for this step. The package is promising, but immediate import would create dependency and integration risk before STONE + MASON has its own artifact contracts.

### Option B: Keep MASON only as durable memory, no runtime doctrine

Rejected as incomplete. Durable repo memory is necessary, but long sessions still need bounded runtime handoff and exact identifier preservation.

### Option C: Use LLM summaries for compaction

Rejected as the default strategy. LLM summaries can be useful for enrichment, but they should not be the only source of truth for exact paths, identifiers, and active task state.

## Reversal / Revisit Trigger

Revisit this ADR if:

- the proposed artifacts become too heavy for solo-dev workflow
- trigger-card recall becomes noisy or misleading
- deterministic folding fails to preserve enough useful context
- a future package import is proposed
- a simpler implementation achieves the same anti-drift goals

## Current Approval Boundary

Approved by this ADR:

- vocabulary and doctrine
- documentation of proposed artifact shapes
- future task sequencing

Not approved by this ADR:

- dependency additions
- workflow changes
- production script changes
- canon lock promotion
- automatic memory rewriting
