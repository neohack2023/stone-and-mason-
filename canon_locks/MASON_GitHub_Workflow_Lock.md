---
id: CANON_MASON_GITHUB_WORKFLOW_LOCK
title: MASON GitHub Workflow Lock
domain: stone_mason_github
type: canon_lock
status: canon
priority: high
decay_profile: none
trigger:
  - GitHub workflow
  - MASON
  - inbox
  - process memory
  - context packet
tags:
  - stone/canon-lock
  - mason/github
---

# MASON GitHub Workflow Lock

## Rule

MASON must preserve the STONE chain when processing repo inbox notes.

For any note that contains a useful observation, test, fix, workflow idea, prompt result, or reusable lesson, MASON should create:

1. episode summary
2. candidate memory card
3. trigger card
4. archived raw receipt
5. processing report

## Avoid

- archiving useful notes without extracting the lesson
- overwriting canon automatically
- generating unreviewed changes directly into main without a pull request
- treating raw receipts as clutter

## Human gate

Pull requests are the approval layer.

MASON drafts. Human merges.
