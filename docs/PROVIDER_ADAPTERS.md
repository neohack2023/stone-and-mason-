# MASON Provider Adapters

MASON now uses a provider layer so the same GitHub workflow can run with different backends.

## Providers

### `provider=rule`

Deterministic fallback.

Use for:
- safe CI tests
- GitHub-hosted runners
- dry-run previews
- confirming file routing

This provider does not call an AI model. It extracts titles, lessons, triggers, and memory artifacts with rule-based logic.

### `provider=ollama`

Local SLM mode.

Use for:
- self-hosted GitHub runners
- local Ollama processing
- richer classification and summarization

Required:

```text
Ollama running on the same machine as the self-hosted runner
```

Default endpoint:

```text
http://127.0.0.1:11434/api/chat
```

Default model:

```text
qwen2.5-coder:3b
```

A GitHub-hosted runner cannot reach your PC's localhost.

### `provider=codex`

Placeholder mode.

Use Codex today as the repo mechanic:
- patch scripts
- improve workflows
- add tests
- implement new providers
- review and modify the MASON system

The `provider=codex` backend is a safe no-op placeholder until a Codex CLI or GitHub Action runtime is confirmed inside the workflow environment.

## JSON action validation

All provider outputs go through a validation gate before writing files.

Allowed actions:

```json
{ "type": "create", "path": "episodes/file.md", "content": "markdown" }
{ "type": "append", "path": "reports/file.md", "content": "markdown" }
{ "type": "move", "from": "inbox/source.md", "to": "raw_receipts/source.md" }
{ "type": "none", "reason": "no write needed" }
```

Allowed create and append roots:

```text
episodes/
memory_cards/
trigger_cards/
context_packets/
reports/
```

Allowed move route:

```text
inbox/ → raw_receipts/
```

Blocked:
- path traversal
- absolute paths
- drive-letter paths
- delete actions
- canon lock writes from model providers

## Dry-run preview

Every run writes a preview JSON artifact named:

```text
mason-preview
```

Use this to inspect what MASON planned before trusting batch runs.

## Review gate

When files change, the workflow opens a pull request.

MASON drafts. Humans merge.
