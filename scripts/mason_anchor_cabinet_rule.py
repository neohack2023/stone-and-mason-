#!/usr/bin/env python3
"""
Standalone rule-mode Anchor Cabinet runner for STONE + MASON.

This helper scans inbox/ for .md and .txt notes, extracts exact recall
coordinates, and previews candidate Anchor Cabinet artifacts as JSON.
It writes files only when --apply is supplied.

No external dependencies are used.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "inbox"
ANCHOR_CABINETS = ROOT / "anchor_cabinets"
REPORTS = ROOT / "reports"

SUPPORTED_SUFFIXES = {".md", ".txt"}

ANCHOR_CATEGORIES = [
    "repos",
    "paths",
    "folders",
    "branches",
    "issues",
    "prs",
    "commits",
    "workflows",
    "scripts",
    "providers",
    "models",
    "ports",
    "environment_flags",
    "error_strings",
    "project_identifiers",
    "people_or_handles",
    "external_urls",
]

PROJECT_IDENTIFIERS = [
    "STONE + MASON",
    "STONE",
    "MASON",
    "Anchor Cabinet",
    "Deterministic Fold Card",
    "Recall Triggers v2",
    "Re-entry Packet",
    "Action Rail",
    "Trust Register",
    "Hermes Agent",
]

SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password|passwd|pwd|cookie|authorization|bearer)\b\s*[:=]\s*\S+"),
    re.compile(r"(?i)\b(ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]+"),
    re.compile(r"(?i)\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"(?i)\bxox[baprs]-[A-Za-z0-9-]+"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]


def slugify(text: str, fallback: str = "untitled") -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    text = re.sub(r"-+", "-", text)
    return text[:80] or fallback


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    base = path.with_suffix("")
    suffix = path.suffix
    for index in range(2, 1000):
        candidate = base.with_name(f"{base.name}_{index}").with_suffix(suffix)
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not create unique path for {path}")


def rel(path: Path, root: Path = ROOT) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def is_secret_like(value: str) -> bool:
    return any(pattern.search(value) for pattern in SECRET_PATTERNS)


def clean_candidate(value: str) -> str:
    return value.strip().strip("`'\"<>()[]{}.,;:")


def add_anchor(anchors: dict[str, list[str]], category: str, value: str) -> None:
    value = clean_candidate(value)
    if not value:
        return
    if is_secret_like(value):
        return
    anchors.setdefault(category, []).append(value)


def dedupe_anchors(anchors: dict[str, list[str]]) -> dict[str, list[str]]:
    compact: dict[str, list[str]] = {}
    for category in ANCHOR_CATEGORIES:
        seen: dict[str, None] = {}
        for value in anchors.get(category, []):
            if not value or is_secret_like(value):
                continue
            seen.setdefault(value, None)
        if seen:
            compact[category] = sorted(seen.keys())
    return compact


def extract_anchors(text: str) -> dict[str, list[str]]:
    anchors: dict[str, list[str]] = {category: [] for category in ANCHOR_CATEGORIES}

    for url in re.findall(r"https?://[^\s<>)\"']+", text):
        add_anchor(anchors, "external_urls", url)
        port_match = re.search(r":(\d{2,5})(?:/|$)", url)
        if port_match:
            add_anchor(anchors, "ports", f"port={port_match.group(1)}")

    for repo in re.findall(r"(?<![\w.-])([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)(?![\w-])", text):
        if "://" not in repo and "." not in repo.split("/", 1)[0] and "." not in repo.split("/", 1)[1]:
            add_anchor(anchors, "repos", repo)

    path_pattern = r"(?<![\w.-])([A-Za-z0-9_.-]+/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.(?:py|md|txt|yml|yaml|json|toml|ini|sh|js|ts|tsx|jsx|css|html))(?![\w-])"
    for path in re.findall(path_pattern, text):
        add_anchor(anchors, "paths", path)
        if path.startswith("scripts/"):
            add_anchor(anchors, "scripts", path)
        parts = path.split("/")[:-1]
        for index in range(1, len(parts) + 1):
            add_anchor(anchors, "folders", "/".join(parts[:index]) + "/")

    for folder in re.findall(r"(?<![\w.-])([A-Za-z0-9_.-]+/(?:[A-Za-z0-9_.-]+/)*)", text):
        if "." not in folder.rsplit("/", 2)[-2:-1]:
            add_anchor(anchors, "folders", folder)

    for branch in re.findall(r"(?i)\b(?:branch|head|base)\s*[:=]\s*`?([A-Za-z0-9._/-]+)`?", text):
        add_anchor(anchors, "branches", branch)

    for branch in re.findall(r"`((?:agent|mason|pr|feature|fix|docs)/[A-Za-z0-9._/-]+)`", text):
        add_anchor(anchors, "branches", branch)

    for issue in re.findall(r"(?i)\bissue\s+#?(\d+)", text):
        add_anchor(anchors, "issues", f"#{issue}")
    for pr in re.findall(r"(?i)\b(?:pr|pull request)\s+#?(\d+)", text):
        add_anchor(anchors, "prs", f"#{pr}")

    for commit in re.findall(r"\b[0-9a-f]{7,40}\b", text):
        add_anchor(anchors, "commits", commit)

    for workflow in re.findall(r"(?i)\bworkflow\s*[:=]\s*`?([^`\n\r]+?)`?(?:\n|$)", text):
        add_anchor(anchors, "workflows", workflow.strip())
    for known_workflow in ["MASON Inbox Processor", "MASON candidate review"]:
        if known_workflow.lower() in text.lower():
            add_anchor(anchors, "workflows", known_workflow)

    for provider in re.findall(r"\bprovider=(rule|ollama|codex|github-ai)\b", text, flags=re.IGNORECASE):
        add_anchor(anchors, "providers", f"provider={provider.lower()}")

    for model in re.findall(r"\b(?:qwen|gpt|llama|mistral|phi|codex)[A-Za-z0-9._:-]*\b", text, flags=re.IGNORECASE):
        add_anchor(anchors, "models", model)

    for port in re.findall(r"\bport\s*[:=]\s*(\d{2,5})\b", text, flags=re.IGNORECASE):
        add_anchor(anchors, "ports", f"port={port}")

    for flag in re.findall(r"\b[A-Z][A-Z0-9_]{2,}(?:=[^\s`'\"<>]+)?", text):
        if not is_secret_like(flag):
            add_anchor(anchors, "environment_flags", flag)

    for line in text.splitlines():
        if re.search(r"(?i)\b(error|failed|failure|exception|traceback)\b", line):
            cleaned = line.strip()
            if 5 <= len(cleaned) <= 220:
                add_anchor(anchors, "error_strings", cleaned)

    for identifier in PROJECT_IDENTIFIERS:
        if identifier.lower() in text.lower():
            add_anchor(anchors, "project_identifiers", identifier)

    for handle in re.findall(r"(?<![\w])@([A-Za-z0-9_-]{2,39})", text):
        add_anchor(anchors, "people_or_handles", handle)
    if "neohack2023" in text:
        add_anchor(anchors, "people_or_handles", "neohack2023")

    return dedupe_anchors(anchors)


def yaml_scalar(value: str) -> str:
    if value.startswith("#") or ":" in value or value in {"null", "true", "false"}:
        return json.dumps(value)
    return value


def yaml_block(title: str, items: list[str], indent: int = 2) -> list[str]:
    spaces = " " * indent
    lines = [f"{spaces}{title}:"]
    for item in items:
        lines.append(f"{spaces}  - {yaml_scalar(item)}")
    return lines


def anchors_yaml(anchors: dict[str, list[str]]) -> str:
    lines = ["anchors:"]
    for category in ANCHOR_CATEGORIES:
        items = anchors.get(category, [])
        if items:
            lines.extend(yaml_block(category, items, indent=2))
    return "\n".join(lines)


def build_matching_rules(anchors: dict[str, list[str]]) -> str:
    strong = []
    if anchors.get("paths"):
        strong.append("exact repository-relative path match")
    if anchors.get("issues"):
        strong.append("exact issue number match")
    if anchors.get("prs"):
        strong.append("exact PR number match")
    if anchors.get("branches"):
        strong.append("exact branch name match")
    if anchors.get("commits"):
        strong.append("exact commit SHA match")
    if anchors.get("project_identifiers"):
        strong.append("exact project identifier paired with a task boundary")
    if not strong:
        strong.append("same source file path appears again")

    weak = [
        "project phrase appears without a path, issue, PR, or script",
        "provider or model name appears without a MASON task boundary",
    ]

    do_not = [
        "memory alone",
        "context alone",
        "workflow alone",
        "agent alone",
        "generic docs reference without an exact path",
    ]

    lines = ["matching_rules:", "  strong_match:"]
    lines.extend(f"    - {item}" for item in strong)
    lines.append("  weak_match:")
    lines.extend(f"    - {item}" for item in weak)
    lines.append("  do_not_match:")
    lines.extend(f"    - {item}" for item in do_not)
    return "\n".join(lines)


def build_anchor_cabinet(
    source_path: Path,
    text: str,
    anchors: dict[str, list[str]],
    *,
    root: Path = ROOT,
    created: str | None = None,
) -> str:
    created = created or dt.date.today().isoformat()
    title = first_heading(text, source_path.stem)
    slug = slugify(title)
    digest = hashlib.sha1((rel(source_path, root) + text[:500]).encode("utf-8")).hexdigest()[:8]
    cabinet_id = f"anchor-cabinet-{created.replace('-', '')}-{slug}-{digest}"
    source_rel = rel(source_path, root)

    return f"""---
type: anchor_cabinet
status: candidate
id: {cabinet_id}
source_receipt: null
scope: task
created: {created}
review_required: true
---

# {title}

## Scope

Rule-mode Anchor Cabinet candidate generated from `{source_rel}`.

## Source Trace

- Source note: `{source_rel}`
- Source receipt: not yet available; derived from inbox note before archival.

## Anchors

```yaml
{anchors_yaml(anchors)}
```

## Matching Rules

```yaml
{build_matching_rules(anchors)}
```

## Exclusions

- Do not include secrets, tokens, cookies, passwords, authorization headers, or `.env` values.
- Do not trigger recall from generic words alone.
- Do not treat this cabinet as a canon lock.
- Do not promote this candidate without human review.

## Review Notes

This file was generated by standalone rule-mode extraction. Review exact anchors before accepting durable storage.
"""


def report_for(source_path: Path, cabinet_path: Path | None, anchors: dict[str, list[str]], *, root: Path) -> dict[str, Any]:
    return {
        "source": rel(source_path, root),
        "candidate": rel(cabinet_path, root) if cabinet_path else None,
        "anchor_counts": {category: len(values) for category, values in anchors.items()},
        "anchors": anchors,
        "review_required": True,
    }


def scan_inbox(root: Path = ROOT) -> list[Path]:
    inbox = root / "inbox"
    if not inbox.exists():
        return []
    return sorted(
        path
        for path in inbox.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES and not path.name.startswith(".")
    )


def process_notes(root: Path = ROOT, apply: bool = False) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    output_root = root / "anchor_cabinets"
    report_root = root / "reports"

    for source_path in scan_inbox(root):
        text = read_text(source_path)
        anchors = extract_anchors(text)
        cabinet = build_anchor_cabinet(source_path, text, anchors, root=root)
        title = first_heading(text, source_path.stem)
        slug = slugify(title)
        cabinet_path = output_root / f"{slug}.md"
        report_path = report_root / f"MASON_Anchor_Cabinet_Report_{slug}_{dt.datetime.now(dt.UTC).strftime('%Y%m%d_%H%M%S')}.json"

        changed: list[str] = []
        if apply:
            cabinet_path = unique_path(cabinet_path)
            write_text(cabinet_path, cabinet)
            report = report_for(source_path, cabinet_path, anchors, root=root)
            write_text(report_path, json.dumps(report, indent=2))
            changed.extend([rel(cabinet_path, root), rel(report_path, root)])

        results.append(
            {
                "source": rel(source_path, root),
                "candidate_path": rel(cabinet_path, root),
                "anchor_count": sum(len(values) for values in anchors.values()),
                "anchor_counts": {category: len(values) for category, values in anchors.items()},
                "anchors": anchors,
                "changed": changed,
                "preview": cabinet if not apply else None,
            }
        )

    return {"ok": True, "apply": apply, "count": len(results), "results": results}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview or write rule-mode Anchor Cabinet candidates.")
    parser.add_argument("--apply", action="store_true", help="write candidate Anchor Cabinets and reports")
    parser.add_argument("--root", default=str(ROOT), help="repository root to scan; defaults to this repo")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    result = process_notes(root=root, apply=args.apply)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
