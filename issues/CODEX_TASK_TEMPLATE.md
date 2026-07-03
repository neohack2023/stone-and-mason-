# Codex Task Template

Use this text when creating an issue for Codex.

```markdown
## Goal

[Describe the exact change.]

## Context

Read `AGENTS.md`, `docs/STONE_Memory_Management_System.md`, and `docs/MASON_SLM_Delivery_Layer.md` first.

## Scope

Only modify:

- [file or folder]

## Requirements

- Preserve provider=rule as fallback.
- Keep pull requests as the review gate.
- Validate model-proposed JSON before writing files.
- Every memory card must link to a source receipt.
- Do not promote canon without explicit instruction.

## Acceptance criteria

- [ ] Tests or dry run pass
- [ ] Generated markdown has frontmatter
- [ ] No unrelated files changed
- [ ] README/docs updated if behavior changed
```
