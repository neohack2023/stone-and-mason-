#!/usr/bin/env python3
"""Rule-mode Anchor Cabinet generator for STONE + MASON.

This is the first runnable runtime-pressure slice. It scans inbox notes for
exact coordinates and writes reviewable Anchor Cabinet candidates without using
LLM summarization or external dependencies.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "inbox"
ANCHOR_CABINETS = ROOT / "anchor_cabinets"
REPORTS = ROOT / "reports"
SUPPORTED = {".md", ".txt"}

PROJECT_IDENTIFIERS = [
    "STONE + MASON",
    "Anchor Cabinet",
    "Deterministic Fold Card",
    "Recall Triggers v2",
    "Re-entry Packet",
    "Action Rail",
    "Trust Register",
    "Context Warp Drive",
]

SECRETISH_RE = re.compile(
    r"(SECRET|TOKEN|PASSWORD|PASSWD|COOKIE|PRIVATE[_-]?KEY|API[_-]?KEY|ACCESS[_-]?KEY|\.env)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AnchorPlan:
    source: str
    target: str
    anchors: dict[str, list[str]]
    content: str


def slugify(text: str, fallback: str = "untitled") -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    text = re.sub(r"_+", "_", text)
    return text[:90] or fallback


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip() or fallback
    return fallback


def clean_anchor(value: str) -> str:
    return value.strip().strip("`'\".,;)({}[]")


def not_secretish(value: str) -> bool:
    return not SECRETISH_RE.search(value)


def uniq(values: list[str]) -> list[str]:
    cleaned = [clean_anchor(v) for v in values if clean_anchor(v) and not_secretish(clean_anchor(v))]
    return sorted(dict.fromkeys(cleaned))


def extract_anchors(text: str) -> dict[str, list[str]]:
    anchors: dict[str, list[str]] = {}

    external_urls = uniq(re.findall(r"https?://[^\s)`\]<>\"]+", text))
    if external_urls:
        anchors["external_urls"] = external_urls

    commits = uniq(re.findall(r"\b[a-f0-9]{7,40}\b", text, flags=re.IGNORECASE))
    commits = [c for c in commits if re.search(r"[a-f]", c, flags=re.IGNORECASE)]
    if commits:
        anchors["commits"] = commits

    repos = []
    for match in re.findall(r"(?<![\w.-])([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)(?![\w.-])", text):
        left, right = match.split("/", 1)
        if "." not in right and left.lower() not in {"docs", "scripts", "tests", "anchor_cabinets"}:
            repos.append(match)
    repos = uniq(repos)
    if repos:
        anchors["repos"] = repos

    paths = uniq(
        re.findall(
            r"(?<![\w.-])((?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.(?:md|txt|json|yml|yaml|py|toml|js|ts|tsx|jsx|sh))(?![\w/])",
            text,
        )
    )
    if paths:
        anchors["paths"] = paths

    folders = uniq(re.findall(r"(?<![\w.-])((?:[A-Za-z0-9_.-]+/)+)(?![\w.-])", text))
    folders = [folder for folder in folders if not any(url.startswith(f"https://{folder}") or url.startswith(f"http://{folder}") for url in external_urls)]
    if folders:
        anchors["folders"] = folders

    scripts = [path for path in paths if path.startswith("scripts/")]
    if scripts:
        anchors["scripts"] = scripts

    prs = [f"#{n}" for n in uniq(re.findall(r"\b(?:PR|pull request)\s*#(\d+)\b", text, flags=re.IGNORECASE))]
    if prs:
        anchors["prs"] = prs

    pr_numbers = {pr.lstrip("#") for pr in prs}
    issues = [f"#{n}" for n in re.findall(r"(?<![A-Za-z])#(\d+)\b", text) if n not in pr_numbers]
    issues = uniq(issues)
    if issues:
        anchors["issues"] = issues

    branches = uniq(re.findall(r"\b((?:agent|feature|fix|docs|chore|release|hotfix)/[A-Za-z0-9._/-]+)\b", text))
    if branches:
        anchors["branches"] = branches

    workflows = []
    if "mason inbox processor" in text.lower():
        workflows.append("MASON Inbox Processor")
    workflows.extend(re.findall(r"workflow(?: name)?[:=]\s*['\"]?([^'\"\n]+)", text, flags=re.IGNORECASE))
    workflows = uniq(workflows)
    if workflows:
        anchors["workflows"] = workflows

    for key, pattern in {
        "providers": r"\bprovider=[A-Za-z0-9_.:-]+\b",
        "models": r"\b(?:gpt-[A-Za-z0-9_.:-]+|claude-[A-Za-z0-9_.:-]+|gemini-[A-Za-z0-9_.:-]+|qwen[A-Za-z0-9_.:-]+|llama[A-Za-z0-9_.:-]+)\b",
        "ports": r"\bport=\d{2,5}\b|(?<!\w):\d{2,5}\b",
        "environment_flags": r"\b[A-Z][A-Z0-9_]{2,}=[^\s`'\"]+",
    }.items():
        values = uniq(re.findall(pattern, text, flags=re.IGNORECASE))
        if values:
            anchors[key] = values

    errors = uniq(re.findall(r"(?:error|exception|failed|failure)[:=]\s*['\"]?([^'\"\n]{4,160})", text, flags=re.IGNORECASE))
    if errors:
        anchors["error_strings"] = errors

    project_identifiers = [identifier for identifier in PROJECT_IDENTIFIERS if identifier.lower() in text.lower()]
    if project_identifiers:
        anchors["project_identifiers"] = project_identifiers

    handles = uniq(re.findall(r"(?<!\w)@[A-Za-z0-9_-]{2,39}\b", text))
    if handles:
        anchors["people_or_handles"] = handles

    return {key: values for key, values in anchors.items() if values}


def yaml_list(values: list[str], indent: int = 4) -> str:
    pad = " " * indent
    lines = []
    for value in values:
        if value.startswith("#") or ":" in value:
            lines.append(f'{pad}- "{value}"')
        else:
            lines.append(f"{pad}- {value}")
    return "\n".join(lines)


def render_anchor_yaml(anchors: dict[str, list[str]]) -> str:
    order = [
        "repos", "paths", "folders", "branches", "issues", "prs", "commits", "workflows",
        "scripts", "providers", "models", "ports", "environment_flags", "error_strings",
        "project_identifiers", "people_or_handles", "external_urls",
    ]
    lines = ["anchors:"]
    for category in order:
        values = anchors.get(category, [])
        if values:
            lines.append(f"  {category}:")
            lines.append(yaml_list(values))
    return "\n".join(lines)


def render_matching_rules(anchors: dict[str, list[str]]) -> str:
    strong = []
    if anchors.get("paths") or anchors.get("scripts"):
        strong.append("exact path match")
    if anchors.get("issues") or anchors.get("prs"):
        strong.append("exact issue or PR number match")
    if anchors.get("branches"):
        strong.append("exact branch name match")
    if anchors.get("commits"):
        strong.append("exact commit SHA match")
    if anchors.get("error_strings"):
        strong.append("exact error string match")
    if anchors.get("providers") or anchors.get("workflows"):
        strong.append("exact provider or workflow match with STONE + MASON context")
    if not strong:
        strong.append("exact project identifier match with source trace")

    return "\n".join([
        "matching_rules:",
        "  strong_match:",
        *(f"    - {item}" for item in strong),
        "  weak_match:",
        "    - project phrase appears without a path, issue, branch, or source trace",
        "    - provider name appears without a task boundary",
        "  do_not_match:",
        "    - memory alone",
        "    - context alone",
        "    - docs alone",
        "    - workflow alone",
        "    - agent alone",
    ])


def render_anchor_cabinet(path: Path, text: str, anchors: dict[str, list[str]]) -> str:
    today = dt.date.today().isoformat()
    title = first_heading(text, path.stem)
    slug = slugify(title)
    digest = hashlib.sha1((rel(path) + text[:300]).encode("utf-8")).hexdigest()[:10]
    return f"""---
type: anchor_cabinet
status: candidate
id: anchor-cabinet-{today.replace('-', '')}-{slug}-{digest}
source_receipt: null
scope: task
created: {today}
review_required: true
tags:
  - stone/anchor-cabinet
  - mason/runtime-pressure
---

# Anchor Cabinet: {title}

## Scope

Exact-coordinate preservation for `{rel(path)}`.

## Source Trace

- Source note: `{rel(path)}`
- Raw receipt: not yet available; generated before archival.

## Anchors

```yaml
{render_anchor_yaml(anchors)}
```

## Matching Rules

```yaml
{render_matching_rules(anchors)}
```

## Exclusions

- Do not include secrets, tokens, cookies, passwords, private keys, API keys, or `.env` values.
- Do not trigger recall from generic words alone.
- Do not treat this cabinet as a canon lock.
- Do not treat this cabinet as a summary or memory card.

## Review Notes

Generated by deterministic rule-mode Anchor Cabinet processing. Human review is required before treating these anchors as durable retrieval coordinates.
"""


def build_plan(path: Path) -> AnchorPlan | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    anchors = extract_anchors(text)
    if not anchors:
        return None
    title = first_heading(text, path.stem)
    target = ANCHOR_CABINETS / f"ANCHOR_{slugify(title)}.md"
    return AnchorPlan(source=rel(path), target=rel(target), anchors=anchors, content=render_anchor_cabinet(path, text, anchors))


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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def discover_inbox_files() -> list[Path]:
    INBOX.mkdir(exist_ok=True)
    return sorted(
        path for path in INBOX.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED and not path.name.startswith(".")
    )


def run(apply: bool) -> dict[str, Any]:
    plans = [plan for path in discover_inbox_files() if (plan := build_plan(path))]
    changed: list[str] = []

    if apply:
        for plan in plans:
            target = unique_path(ROOT / plan.target)
            write_text(target, plan.content)
            changed.append(rel(target))

        stamp = dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_path = REPORTS / f"Anchor_Cabinet_Report_{stamp}.json"
        write_text(report_path, json.dumps({"count": len(plans), "changed": changed}, indent=2))
        changed.append(rel(report_path))

    return {
        "ok": True,
        "processor": "mason_anchor_cabinet_rule",
        "apply": apply,
        "count": len(plans),
        "changed": changed,
        "plans": [
            {"source": plan.source, "target": plan.target, "anchors": plan.anchors}
            for plan in plans
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write Anchor Cabinet candidates")
    parser.add_argument("--preview-output", default=os.environ.get("ANCHOR_CABINET_PREVIEW_OUTPUT"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run(apply=args.apply)
    rendered = json.dumps(result, indent=2)
    print(rendered)
    if args.preview_output:
        output = Path(args.preview_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - CLI safety surface
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(1) from exc
