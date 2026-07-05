# Anchor Cabinet Runner Quickstart

**Status:** Runtime helper note  
**Related issue:** #14

## Purpose

`scripts/mason_anchor_cabinet_rule.py` is the first runnable STONE + MASON runtime-pressure helper.

It scans `inbox/` notes for exact coordinates and prepares reviewable Anchor Cabinet candidates. It does not use an LLM, does not import Context Warp Drive, and does not modify the existing MASON inbox processor.

## Preview mode

Preview mode is the default. It prints JSON and writes nothing.

```bash
python scripts/mason_anchor_cabinet_rule.py
```

Optional preview file:

```bash
python scripts/mason_anchor_cabinet_rule.py --preview-output reports/anchor_preview.json
```

## Apply mode

Apply mode writes candidate artifacts.

```bash
python scripts/mason_anchor_cabinet_rule.py --apply
```

When anchors are found, it writes:

```text
anchor_cabinets/ANCHOR_<note-title>.md
reports/Anchor_Cabinet_Report_<timestamp>.json
```

## What it extracts

The runner preserves exact anchors such as:

- repository names
- file paths
- folders
- branches
- issue and PR numbers
- commit SHAs
- workflow names
- provider modes
- model names
- ports
- environment flags, except secret-like values
- error strings
- project identifiers
- handles
- external URLs

## Safety behavior

The runner filters secret-like values containing terms such as:

```text
SECRET
TOKEN
PASSWORD
PASSWD
COOKIE
PRIVATE_KEY
API_KEY
ACCESS_KEY
.env
```

It also keeps generic words out of matching rules so `memory`, `context`, `docs`, `workflow`, or `agent` alone do not become recall triggers.

## Current boundary

This helper is intentionally standalone. A later PR may integrate Anchor Cabinet generation into `scripts/mason_github_process.py` after this runnable slice is reviewed.
