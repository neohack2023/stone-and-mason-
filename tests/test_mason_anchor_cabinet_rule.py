from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "mason_anchor_cabinet_rule.py"
SPEC = importlib.util.spec_from_file_location("mason_anchor_cabinet_rule", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
anchor = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = anchor
SPEC.loader.exec_module(anchor)


class AnchorCabinetRuleScriptTests(unittest.TestCase):
    def test_extract_anchors_preserves_coordinates_and_filters_secretish_values(self) -> None:
        text = """
        Work in neohack2023/stone-and-mason- on branch agent/rule-anchor-cabinet-mvp.
        Touch scripts/mason_github_process.py and docs/anchor-cabinet-artifact-contract.md.
        Related PR #10, issue #13, commit 8ebff6213b4230601662c1bba4b55093cc4fb042.
        Use provider=rule, qwen2.5-coder:3b, port=3002, and MASON Inbox Processor.
        Keep https://github.com/dogtorjonah/context-warp-drive as an external reference.
        SECRET_TOKEN=do-not-store should not become an anchor.
        """

        anchors = anchor.extract_anchors(text)

        self.assertIn("neohack2023/stone-and-mason-", anchors["repos"])
        self.assertIn("agent/rule-anchor-cabinet-mvp", anchors["branches"])
        self.assertIn("scripts/mason_github_process.py", anchors["paths"])
        self.assertIn("docs/anchor-cabinet-artifact-contract.md", anchors["paths"])
        self.assertIn("#10", anchors["prs"])
        self.assertIn("#13", anchors["issues"])
        self.assertIn("8ebff6213b4230601662c1bba4b55093cc4fb042", anchors["commits"])
        self.assertIn("provider=rule", anchors["providers"])
        self.assertIn("qwen2.5-coder:3b", anchors["models"])
        self.assertIn("port=3002", anchors["ports"])
        self.assertIn("MASON Inbox Processor", anchors["workflows"])
        self.assertIn("https://github.com/dogtorjonah/context-warp-drive", anchors["external_urls"])
        self.assertNotIn("SECRET_TOKEN=do-not-store", anchors.get("environment_flags", []))

    def test_render_anchor_cabinet_has_required_contract_sections(self) -> None:
        source = anchor.INBOX / "anchor_mvp_test.md"
        source.parent.mkdir(exist_ok=True)
        source.write_text(
            "# Anchor MVP Test\n\n"
            "Preserve scripts/mason_github_process.py for issue #13 and provider=rule.\n",
            encoding="utf-8",
        )
        try:
            plan = anchor.build_plan(source)
        finally:
            source.unlink(missing_ok=True)

        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan.target, "anchor_cabinets/ANCHOR_Anchor_MVP_Test.md")
        self.assertIn("type: anchor_cabinet", plan.content)
        self.assertIn("## Scope", plan.content)
        self.assertIn("## Source Trace", plan.content)
        self.assertIn("## Anchors", plan.content)
        self.assertIn("## Matching Rules", plan.content)
        self.assertIn("## Exclusions", plan.content)
        self.assertIn("## Review Notes", plan.content)
        self.assertIn("scripts/mason_github_process.py", plan.content)
        self.assertIn('"#13"', plan.content)


if __name__ == "__main__":
    unittest.main()
