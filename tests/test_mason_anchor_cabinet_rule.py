from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "mason_anchor_cabinet_rule.py"
SPEC = importlib.util.spec_from_file_location("mason_anchor_cabinet_rule", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
mason_anchor = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mason_anchor
SPEC.loader.exec_module(mason_anchor)


class AnchorCabinetRuleTests(unittest.TestCase):
    def test_extract_anchors_filters_secret_like_values(self) -> None:
        text = """
        # Runtime slice
        Repo neohack2023/stone-and-mason- uses scripts/mason_github_process.py.
        Issue #14 connects to PR #18 on branch: pr/14-anchor-cabinet-runner.
        provider=ollama model qwen2.5-coder:3b endpoint http://127.0.0.1:11434/api/chat
        MASON_PROVIDER=rule
        commit 6a8be62a70f74d3315b03fa6a6e61dee23619405
        API_KEY=sk-this-should-not-be-captured
        cookie=session-value
        Error: JSON validation failed
        """

        anchors = mason_anchor.extract_anchors(text)
        flattened = json.dumps(anchors)

        self.assertIn("neohack2023/stone-and-mason-", anchors["repos"])
        self.assertIn("scripts/mason_github_process.py", anchors["paths"])
        self.assertIn("scripts/mason_github_process.py", anchors["scripts"])
        self.assertIn("#14", anchors["issues"])
        self.assertIn("#18", anchors["prs"])
        self.assertIn("provider=ollama", anchors["providers"])
        self.assertIn("qwen2.5-coder:3b", anchors["models"])
        self.assertIn("port=11434", anchors["ports"])
        self.assertIn("MASON_PROVIDER=rule", anchors["environment_flags"])
        self.assertNotIn("sk-this-should-not-be-captured", flattened)
        self.assertNotIn("session-value", flattened)

    def test_rendered_candidate_contains_required_contract_sections(self) -> None:
        source = Path("inbox/runtime.md")
        text = "# Runtime Folding\nAnchor Cabinet should preserve scripts/mason_anchor_cabinet_rule.py for Issue #14."
        anchors = mason_anchor.extract_anchors(text)

        rendered = mason_anchor.build_anchor_cabinet(
            source,
            text,
            anchors,
            root=Path("."),
            created="2026-07-08",
        )

        self.assertIn("type: anchor_cabinet", rendered)
        self.assertIn("status: candidate", rendered)
        self.assertIn("## Scope", rendered)
        self.assertIn("## Source Trace", rendered)
        self.assertIn("## Anchors", rendered)
        self.assertIn("## Matching Rules", rendered)
        self.assertIn("## Exclusions", rendered)
        self.assertIn("## Review Notes", rendered)
        self.assertIn("Do not include secrets", rendered)
        self.assertIn("review_required: true", rendered)

    def test_preview_mode_does_not_write_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inbox = root / "inbox"
            inbox.mkdir()
            (inbox / "note.md").write_text(
                "# Note\nUse provider=rule with scripts/mason_github_process.py for Issue #14.\n",
                encoding="utf-8",
            )

            result = mason_anchor.process_notes(root=root, apply=False)

            self.assertTrue(result["ok"])
            self.assertEqual(result["count"], 1)
            self.assertFalse((root / "anchor_cabinets").exists())
            self.assertFalse((root / "reports").exists())
            self.assertIn("preview", result["results"][0])
            self.assertIn("## Anchors", result["results"][0]["preview"])

    def test_apply_mode_writes_candidate_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inbox = root / "inbox"
            inbox.mkdir()
            (inbox / "note.md").write_text(
                "# Apply Note\nUse provider=rule with scripts/mason_github_process.py for Issue #14.\n",
                encoding="utf-8",
            )

            result = mason_anchor.process_notes(root=root, apply=True)

            self.assertTrue(result["ok"])
            changed = result["results"][0]["changed"]
            self.assertEqual(len(changed), 2)
            self.assertTrue((root / changed[0]).exists())
            self.assertTrue((root / changed[1]).exists())
            self.assertIn("anchor_cabinets/", changed[0])
            self.assertIn("reports/", changed[1])


if __name__ == "__main__":
    unittest.main()
