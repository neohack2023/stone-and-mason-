#!/usr/bin/env python3
"""
MASON GitHub Inbox Processor

Rule-mode processor for STONE + MASON repos.

It scans inbox/, creates:
- raw_receipts/
- episodes/
- memory_cards/
- trigger_cards/
- context_packets/ when requested later
- reports/

This v0 intentionally works without model access so the GitHub pipeline can be tested first.
Later, a self-hosted runner can call a local Ollama endpoint for full SLM curation.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INBOX = ROOT / "inbox"
RAW = ROOT / "raw_receipts"
EPISODES = ROOT / "episodes"
MEMORY = ROOT / "memory_cards"
TRIGGERS = ROOT / "trigger_cards"
CONTEXT = ROOT / "context_packets"
REPORTS = ROOT / "reports"

SUPPORTED = {".md", ".txt"}


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
            "trigger card", "canon lock", "Suno", "MASON", "STONE"
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


def frontmatter(data: dict) -> str:
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


def process_file(path: Path, apply: bool) -> dict:
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
    report_path = REPORTS / f"MASON_Report_{slug}.md"

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

    report = {
        "source": str(path.relative_to(ROOT)),
        "classification": labels,
        "created": [
            str(episode_path.relative_to(ROOT)),
            str(memory_path.relative_to(ROOT)),
            str(trigger_path.relative_to(ROOT)),
            str(report_path.relative_to(ROOT)),
        ],
        "moved_to": str(raw_path.relative_to(ROOT)),
        "triggers": triggers,
        "lesson": lesson,
    }

    if apply:
        write_text(episode_path, episode)
        write_text(memory_path, memory)
        write_text(trigger_path, trigger)
        write_text(report_path, "```json\n" + json.dumps(report, indent=2) + "\n```")
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        if raw_path.exists():
            raw_path = RAW / f"{slug}_{uid}{path.suffix}"
        shutil.move(str(path), str(raw_path))

    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write generated files and move inbox notes")
    args = parser.parse_args()

    INBOX.mkdir(exist_ok=True)
    files = [p for p in INBOX.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED and not p.name.startswith(".")]

    reports = []
    for file in files:
        reports.append(process_file(file, apply=args.apply))

    print(json.dumps({"count": len(reports), "reports": reports}, indent=2))


if __name__ == "__main__":
    main()
