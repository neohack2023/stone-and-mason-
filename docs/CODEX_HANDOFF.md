# Codex Handoff

Use this when you want Codex to work on the repo.

## Setup checklist

1. Connect ChatGPT/Codex to GitHub.
2. Open the `stone-and-mason-` repo in Codex.
3. Make sure Codex reads `AGENTS.md`.
4. Give Codex one scoped task at a time.
5. Review the pull request before merging.

## Default prompt

```text
Read AGENTS.md first.
Work inside the STONE + MASON architecture.
Do not bypass the PR review gate.
Modify only the files needed for this task.
Keep provider=rule working as the safe fallback.
If adding model-based behavior, validate JSON actions before writing files.
Every generated memory card must link back to a raw receipt.
```

## Good Codex tasks

- Add `provider=ollama` to `scripts/mason_github_process.py`.
- Add `provider=codex` once Codex CLI/GitHub Action access is confirmed.
- Add tests for markdown artifact generation.
- Improve conflict detection.
- Add a context packet builder.
- Add a dry-run preview artifact.

## Bad Codex tasks

- Process the entire vault without review.
- Promote canon automatically.
- Rewrite all memory cards at once.
- Remove raw receipts.

## Working model

```text
Codex = repo mechanic and optional high-power MASON operator
CI = repeatable memory conveyor belt
Pull request = human review gate
```
