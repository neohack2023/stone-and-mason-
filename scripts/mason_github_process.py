#!/usr/bin/env python3
"""
MASON GitHub Inbox Processor

GitHub-native processor for STONE + MASON repos.

Provider modes:
- rule: deterministic fallback that works anywhere in CI
- ollama: local SLM through a self-hosted runner on the same machine as Ollama
- codex: placeholder for future Codex CLI / GitHub agent integration

The script scans inbox/ and produces reviewable memory artifacts:
- raw_receipts/
- episodes/
- memory_cards/
- trigger_cards/
- reports/

All writes go through a JSON action plan and validation gate.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

INBOX = ROOT / "inbox"
RAW = ROOT / "raw_receipts"
EPISODES = ROOT / "episodes"
MEMORY = ROOT / "memory_cards"
TRIGGERS = ROOT / "trigger_cards"
CONTEXT = ROOT / "context_packets"
REPORTS = ROOT / "reports"

SUPPORTED = {".md", ".txt"}
ALLOWED_ACTIONS = {"create", "append", "move", "none"}
ALLOWED_CREATE_ROOTS = {"episodes", "memory_cards", "trigger_cards", "context_packets", "reports"}
ALLOWED_MOVE_FROM_ROOTS = {"inbox"}
ALLOWED_MOVE_TO_ROOTS = {"raw_receipts"}


class MasonValidationError(ValueError):
    """Raised when a model-proposed action plan is unsafe or malformed."""


@dataclass(frozen=True)
class MasonConfig:
    provider: str
    apply: bool
    ollama_endpoint: str
    ollama_model: str
    preview_output: Path | None
    max_note_chars: int
    max_rule_context_chars: int


def slugify(text: str, fallback: str = "untitled") -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    text = re.sub(r"_+", "_", text)
    return text[:90] or fallback


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip() or fallback
    return fallback


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    base = path.with_suffix("")
    suffix = path.suffix
    for i in range(2, 1000):
        candidate = base.with_name(f"{base.name}_{i}").with_suffix(suffix)
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not create unique path for {path}")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def safe_join(relative_path: str) -> Path:
    candidate = (ROOT / relative_path).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise MasonValidationError(f"Path escapes repo root: {relative_path}") from exc
    return candidate


def path_root(relative_path: str) -> str:
    return relative_path.replace("\\", "/").split("/", 1)[0]


def assert_safe_relative_path(relative_path: str) -> str:
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise MasonValidationError("Action path must be a non-empty string.")
    normalized = relative_path.replace("\\", "/").lstrip("/")
    if "\x00" in normalized:
        raise MasonValidationError(f"Null byte blocked in path: {relative_path}")
    if normalized.startswith("../") or "/../" in normalized or normalized == "..":
        raise MasonValidationError(f"Path traversal blocked: {relative_path}")
    if re.match(r"^[A-Za-z]:", normalized):
        raise MasonValidationError(f"Windows absolute path blocked: {relative_path}")
    safe_join(normalized)
    return normalized


def extract_json(text: str) -> dict[str, Any]:
    raw = text.strip()
    if not raw:
        raise MasonValidationError("Model returned empty response.")

    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, flags=re.IGNORECASE)
    if fenced:
        raw = fenced.group(1).strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end <= start:
            raise
        parsed = json.loads(raw[start : end + 1])

    if not isinstance(parsed, dict):
        raise MasonValidationError("Model JSON root must be an object.")
    return parsed


def extract_trigger_words(text: str) -> list[str]:
    triggers: list[str] = []

    patterns = [
        r"Suggested Trigger Words\s*:?\s*([\s\S]+?)(?:\n\n|$)",
        r"Trigger Words\s*:?\s*([\s\S]+?)(?:\n\n|$)",
        r"Suggested Triggers\s*:?\s*([\s\S]+?)(?:\n\n|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            raw = match.group(1)
            for part in re.split(r"[,\n]+", raw):
                item = part.strip(" -`\t")
                if 2 <= len(item) <= 80:
                    triggers.append(item)

    if not triggers:
        keywords = [
            "style prompt", "phonetic repair", "mispronunciation", "fast rap",
            "chopper flow", "lyrics box", "slider", "weirdness",
            "style influence", "audio influence", "context packet", "memory card",
            "trigger card", "canon lock", "Suno", "MASON", "STONE",
        ]
        lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in lower:
                triggers.append(keyword)

    return sorted(dict.fromkeys(triggers))[:12]


def extract_lesson(text: str) -> str:
    patterns = [
        r"Reusable Lesson\s*:?\s*([\s\S]+?)(?:\n\n|$)",
        r"Lesson\s*:?\s*([\s\S]+?)(?:\n\n|$)",
        r"Takeaway\s*:?\s*([\s\S]+?)(?:\n\n|$)",
        r"Fix\s*:?\s*([\s\S]+?)(?:\n\n|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            lesson = " ".join(match.group(1).split())
            if lesson:
                return lesson[:700]

    sentences = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    return " ".join(sentences[:3])[:700]


def classify(text: str) -> list[str]:
    labels = ["raw_receipt"]
    lower = text.lower()
    if any(x in lower for x in ["observed", "observation", "test", "result", "fix", "lesson"]):
        labels.append("episode")
    if any(x in lower for x in ["reusable lesson", "lesson", "rule", "should", "avoid", "fix"]):
        labels.append("memory_card")
    if any(x in lower for x in ["trigger", "retrieval", "keyword"]):
        labels.append("trigger_card")
    return sorted(dict.fromkeys(labels), key=labels.index)


def frontmatter(data: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def load_rule_context(max_chars: int) -> str:
    paths: list[Path] = [
        ROOT / "docs" / "STONE_Memory_Management_System.md",
        ROOT / "docs" / "MASON_SLM_Delivery_Layer.md",
        ROOT / "docs" / "GITHUB_WORKFLOW.md",
        ROOT / "AGENTS.md",
    ]
    paths.extend(sorted((ROOT / "canon_locks").glob("*.md")))

    pieces: list[str] = []
    for path in paths:
        if path.exists():
            pieces.append(f"\n\n--- FILE: {rel(path)} ---\n{read_text(path)}")

    joined = "".join(pieces)
    if len(joined) > max_chars:
        return joined[:max_chars] + "\n\n[TRUNCATED: rule context limit reached]"
    return joined


def build_rule_plan(path: Path) -> dict[str, Any]:
    text = read_text(path)
    title = first_heading(text, path.stem)
    slug = slugify(title)
    uid = hashlib.sha1(str(path).encode("utf-8") + text[:300].encode("utf-8")).hexdigest()[:10]
    today = dt.date.today().isoformat()
    triggers = extract_trigger_words(text)
    lesson = extract_lesson(text)
    labels = classify(text)

    episode_path = EPISODES / f"{slug}.md"
    memory_path = MEMORY / f"MEM_{slug}.md"
    trigger_path = TRIGGERS / f"TRG_{slug}.md"
    raw_path = RAW / path.name

    episode = f"""{frontmatter({
        'id': f'EP_{uid}',
        'title': title,
        'date': today,
        'domain': 'stone_mason_github',
        'source_type': 'inbox_note',
        'status': 'distilled',
        'tags': ['stone/episode', 'mason/github']
    })}

# {title}

## Observation

{(' '.join(text.split()))[:1200]}

## Why It Matters

This inbox note contains reusable workflow evidence for the STONE + MASON memory system.

## Reusable Lesson

{lesson}

## Source

- Raw receipt: `raw_receipts/{path.name}`
"""

    memory = f"""{frontmatter({
        'id': f'MEM_{uid}',
        'title': title,
        'domain': 'stone_mason_github',
        'type': 'workflow_rule',
        'status': 'candidate',
        'source': 'inbox_note',
        'confidence': '0.72',
        'decay_profile': 'medium',
        'trigger': triggers,
        'tags': ['stone/memory-card', 'mason/github']
    })}

# {title}

## Summary

{lesson}

## Trigger

Use this memory when the task mentions:

{chr(10).join(f'- {t}' for t in triggers) if triggers else '- related STONE/MASON workflow behavior'}

## Action

Apply the reusable lesson extracted from the source note.

## Avoid

Do not archive this kind of note without extracting the behavior it teaches.

## Source

- `raw_receipts/{path.name}`
"""

    trigger = f"""{frontmatter({
        'id': f'TRG_{uid}',
        'title': f'TRG {title}',
        'domain': 'stone_mason_github',
        'status': 'active',
        'trigger': triggers,
        'points_to': [f'MEM_{uid}'],
        'tags': ['stone/trigger-card', 'mason/github']
    })}

# TRG {title}

## Match Condition

Retrieve the linked memory when a future issue, note, or task matches these triggers:

{chr(10).join(f'- {t}' for t in triggers) if triggers else '- related STONE/MASON workflow behavior'}

## Linked Memory

- `MEM_{uid}`
"""

    return {
        "provider": "rule",
        "summary": f"Rule-mode processing plan for {path.name}.",
        "classification": labels,
        "confidence": 0.72,
        "conflict_warnings": [],
        "needs_human_review": True,
        "actions": [
            {"type": "create", "path": rel(episode_path), "content": episode},
            {"type": "create", "path": rel(memory_path), "content": memory},
            {"type": "create", "path": rel(trigger_path), "content": trigger},
            {"type": "move", "from": rel(path), "to": rel(raw_path)},
        ],
        "report": {
            "source": rel(path),
            "classification": labels,
            "created": [rel(episode_path), rel(memory_path), rel(trigger_path)],
            "moved_to": rel(raw_path),
            "triggers": triggers,
            "lesson": lesson,
        },
    }


def build_mason_system_prompt() -> str:
    return """
You are MASON, a GitHub-native memory operator for a STONE + MASON repository.

STONE = Selective, Tagged, Optimized, Navigable, Evolving.
MASON = Memory Assembly System for Optimized Navigation.

Return strict JSON only. No markdown fence. No commentary.

Required schema:
{
  "summary": "short summary",
  "classification": ["raw_receipt", "episode", "memory_card", "trigger_card"],
  "confidence": 0.0,
  "conflict_warnings": [],
  "needs_human_review": true,
  "actions": [],
  "report": {}
}

Allowed actions:
- create: {"type":"create", "path":"episodes/file.md", "content":"markdown"}
- append: {"type":"append", "path":"reports/file.md", "content":"markdown"}
- move: {"type":"move", "from":"inbox/source.md", "to":"raw_receipts/source.md"}
- none: {"type":"none", "reason":"why"}

Rules:
- Write only to episodes/, memory_cards/, trigger_cards/, context_packets/, reports/.
- Move originals only from inbox/ to raw_receipts/.
- Do not write canon_locks/.
- Do not delete files.
- If a note teaches a reusable behavior, create a candidate memory card and trigger card.
- Every memory card must link back to the raw receipt.
""".strip()


def call_ollama(path: Path, config: MasonConfig) -> dict[str, Any]:
    text = read_text(path)[: config.max_note_chars]
    rule_context = load_rule_context(config.max_rule_context_chars)
    payload = {
        "model": config.ollama_model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": build_mason_system_prompt()},
            {
                "role": "user",
                "content": (
                    f"RULE CONTEXT:\n{rule_context}\n\n"
                    f"SOURCE FILE: {rel(path)}\n\n"
                    f"NOTE TO PROCESS:\n{text}\n\n"
                    "Create a reviewable MASON action plan."
                ),
            },
        ],
        "options": {"temperature": 0.1},
    }

    request = urllib.request.Request(
        config.ollama_endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Ollama provider failed. This mode requires a self-hosted runner with Ollama reachable at {config.ollama_endpoint}."
        ) from exc

    content = body.get("message", {}).get("content", "")
    plan = extract_json(content)
    plan["provider"] = "ollama"
    return plan


def build_codex_placeholder_plan(path: Path) -> dict[str, Any]:
    return {
        "provider": "codex",
        "summary": "Codex provider placeholder. No Codex CLI or Codex GitHub Action backend is wired yet.",
        "classification": ["raw_receipt"],
        "confidence": 0.0,
        "conflict_warnings": [
            "provider=codex is a placeholder. Use Codex through GitHub issues/PRs for repo changes until a runtime backend is confirmed."
        ],
        "needs_human_review": True,
        "actions": [
            {
                "type": "none",
                "reason": f"Codex placeholder did not process {rel(path)}. Use provider=rule or provider=ollama for processing.",
            }
        ],
        "report": {"source": rel(path), "status": "codex_placeholder"},
    }


def build_plan(path: Path, config: MasonConfig) -> dict[str, Any]:
    if config.provider == "rule":
        return build_rule_plan(path)
    if config.provider == "ollama":
        return call_ollama(path, config)
    if config.provider == "codex":
        return build_codex_placeholder_plan(path)
    raise ValueError(f"Unsupported provider: {config.provider}")


def validate_action_plan(plan: dict[str, Any], source_path: Path) -> dict[str, Any]:
    if not isinstance(plan, dict):
        raise MasonValidationError("Plan must be an object.")
    actions = plan.get("actions")
    if not isinstance(actions, list):
        raise MasonValidationError("Plan must contain actions list.")

    plan.setdefault("conflict_warnings", [])
    expected_from = assert_safe_relative_path(rel(source_path))
    if path_root(expected_from) not in ALLOWED_MOVE_FROM_ROOTS:
        raise MasonValidationError(f"Move source root is not allowed: {expected_from}")

    for action in actions:
        if not isinstance(action, dict):
            raise MasonValidationError("Each action must be an object.")
        action_type = action.get("type")
        if action_type not in ALLOWED_ACTIONS:
            raise MasonValidationError(f"Unsupported action type: {action_type}")

        if action_type in {"create", "append"}:
            action_path = assert_safe_relative_path(action.get("path", ""))
            if path_root(action_path) not in ALLOWED_CREATE_ROOTS:
                raise MasonValidationError(f"Create/append root is not allowed: {action_path}")
            if not action_path.endswith(".md") and not action_path.endswith(".json"):
                raise MasonValidationError(f"Create/append path must be .md or .json: {action_path}")
            if not isinstance(action.get("content"), str):
                raise MasonValidationError(f"Create/append content must be a string: {action_path}")
            action["path"] = action_path

        if action_type == "move":
            supplied_from = action.get("from") or expected_from
            try:
                supplied_from = assert_safe_relative_path(supplied_from)
            except MasonValidationError as exc:
                plan["conflict_warnings"].append(
                    f"Move source overridden for {expected_from}: provider supplied unsafe from={action.get('from')!r} ({exc})."
                )
                supplied_from = expected_from

            to_path = assert_safe_relative_path(action.get("to", ""))
            if supplied_from != expected_from:
                plan["conflict_warnings"].append(
                    f"Move source overridden for {expected_from}: provider requested {supplied_from}."
                )
            if path_root(to_path) not in ALLOWED_MOVE_TO_ROOTS:
                raise MasonValidationError(f"Move destination root is not allowed: {to_path}")
            action["from"] = expected_from
            action["to"] = to_path

        if action_type == "none" and not action.get("reason"):
            action["reason"] = "No write needed."

    plan.setdefault("summary", "MASON action plan")
    plan.setdefault("classification", ["raw_receipt"])
    plan.setdefault("confidence", 0.0)
    plan.setdefault("needs_human_review", True)
    plan.setdefault("report", {})
    return plan


def apply_action_plan(plan: dict[str, Any], source_path: Path) -> list[str]:
    changed: list[str] = []

    for action in plan["actions"]:
        action_type = action["type"]

        if action_type == "none":
            continue

        if action_type == "create":
            target = unique_path(safe_join(action["path"]))
            write_text(target, action["content"])
            changed.append(rel(target))
            continue

        if action_type == "append":
            target = safe_join(action["path"])
            old = read_text(target) if target.exists() else ""
            write_text(target, old.rstrip() + "\n\n" + action["content"])
            changed.append(rel(target))
            continue

        if action_type == "move":
            source = safe_join(action["from"])
            if not source.exists() and source_path.exists():
                source = source_path
            if not source.exists():
                raise FileNotFoundError(f"Move source not found: {action['from']}")
            destination = unique_path(safe_join(action["to"]))
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            changed.append(rel(destination))

    return changed


def write_processing_report(source_path: Path, plan: dict[str, Any], changed: list[str], apply: bool) -> str:
    slug = slugify(source_path.stem)
    stamp = dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS / f"MASON_Report_{slug}_{stamp}.json"
    report = {
        "source": rel(source_path) if source_path.exists() else str(source_path).replace("\\", "/"),
        "provider": plan.get("provider"),
        "summary": plan.get("summary"),
        "classification": plan.get("classification"),
        "confidence": plan.get("confidence"),
        "conflict_warnings": plan.get("conflict_warnings", []),
        "needs_human_review": plan.get("needs_human_review", True),
        "apply": apply,
        "changed": changed,
        "model_report": plan.get("report", {}),
    }
    write_text(report_path, json.dumps(report, indent=2))
    return rel(report_path)


def process_file(path: Path, config: MasonConfig) -> dict[str, Any]:
    plan = build_plan(path, config)
    plan = validate_action_plan(plan, path)
    changed: list[str] = []

    if config.apply:
        changed = apply_action_plan(plan, path)
        report_path = write_processing_report(path, plan, changed, apply=True)
        changed.append(report_path)
    else:
        report_path = None

    return {
        "source": rel(path),
        "provider": config.provider,
        "summary": plan.get("summary"),
        "classification": plan.get("classification"),
        "confidence": plan.get("confidence"),
        "conflict_warnings": plan.get("conflict_warnings", []),
        "needs_human_review": plan.get("needs_human_review", True),
        "actions": [
            {k: v for k, v in action.items() if k != "content"} for action in plan.get("actions", [])
        ],
        "changed": changed,
        "processing_report": report_path,
    }


def parse_args() -> MasonConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write generated files and move inbox notes")
    parser.add_argument("--provider", choices=["rule", "ollama", "codex"], default=os.environ.get("MASON_PROVIDER", "rule"))
    parser.add_argument("--ollama-endpoint", default=os.environ.get("OLLAMA_ENDPOINT", "http://127.0.0.1:11434/api/chat"))
    parser.add_argument("--ollama-model", default=os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:3b"))
    parser.add_argument("--preview-output", default=os.environ.get("MASON_PREVIEW_OUTPUT"))
    parser.add_argument("--max-note-chars", type=int, default=int(os.environ.get("MASON_MAX_NOTE_CHARS", "8000")))
    parser.add_argument("--max-rule-context-chars", type=int, default=int(os.environ.get("MASON_MAX_RULE_CONTEXT_CHARS", "18000")))
    args = parser.parse_args()

    return MasonConfig(
        provider=args.provider,
        apply=args.apply,
        ollama_endpoint=args.ollama_endpoint,
        ollama_model=args.ollama_model,
        preview_output=Path(args.preview_output) if args.preview_output else None,
        max_note_chars=args.max_note_chars,
        max_rule_context_chars=args.max_rule_context_chars,
    )


def main() -> None:
    config = parse_args()
    INBOX.mkdir(exist_ok=True)
    files = [
        p
        for p in INBOX.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED and not p.name.startswith(".")
    ]

    results = []
    try:
        for file in files:
            results.append(process_file(file, config))
    except (MasonValidationError, RuntimeError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc), "provider": config.provider}, indent=2), file=sys.stderr)
        raise SystemExit(1) from exc

    preview = {"ok": True, "provider": config.provider, "apply": config.apply, "count": len(results), "results": results}
    rendered = json.dumps(preview, indent=2)
    print(rendered)

    if config.preview_output:
        config.preview_output.parent.mkdir(parents=True, exist_ok=True)
        config.preview_output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
