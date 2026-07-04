from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "mason_github_process.py"
SPEC = importlib.util.spec_from_file_location("mason_github_process", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
mason = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mason)


class MasonMoveValidationTests(unittest.TestCase):
    def test_move_action_from_is_forced_to_current_source(self) -> None:
        source_path = mason.ROOT / "inbox" / "a.md"
        plan = {
            "actions": [
                {
                    "type": "move",
                    "from": "inbox/b.md",
                    "to": "raw_receipts/a.md",
                }
            ],
            "conflict_warnings": [],
        }

        validated = mason.validate_action_plan(plan, source_path)
        move_action = validated["actions"][0]

        self.assertEqual(move_action["from"], "inbox/a.md")
        self.assertEqual(move_action["to"], "raw_receipts/a.md")
        self.assertTrue(
            any(
                "inbox/b.md" in warning and "inbox/a.md" in warning
                for warning in validated["conflict_warnings"]
            )
        )


if __name__ == "__main__":
    unittest.main()
