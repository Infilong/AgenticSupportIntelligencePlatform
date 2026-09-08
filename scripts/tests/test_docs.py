import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("check_docs", Path(__file__).parents[1] / "check_docs.py")
docs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(docs)


class DocumentationChecks(unittest.TestCase):
    def test_repository_checks_missing_guides_and_broken_subsystem_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in docs.CONTROL_DOCS:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# Guide\n", encoding="utf-8")
            for state in ("active", "completed"):
                (root / "docs" / "exec-plans" / state).mkdir(parents=True)
            self.assertEqual(docs.check_repository(root), [])
            guide = root / "backend" / "app" / "services" / "README.md"
            guide.write_text("[Contract](missing-contract.md)\n", encoding="utf-8")
            self.assertIn("broken local link missing-contract.md",
                          "\n".join(docs.check_repository(root)))
            guide.unlink()
            self.assertIn("missing document", "\n".join(docs.check_repository(root)))

    def test_local_links_are_checked_but_examples_and_remote_links_are_not(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "guide.md"
            (path.parent / "target.md").write_text("# Target", encoding="utf-8")
            path.write_text("[OK](target.md) [web](https://example.com)\n"
                            "```text\n[example](absent.md)\n```", encoding="utf-8")
            self.assertEqual(docs.check_file(path), [])
            (path.parent / "target.md").unlink()
            self.assertIn("broken local link target.md", docs.check_file(path)[0])

    def test_instruction_size_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AGENTS.md"
            path.write_text("instruction\n" * 199, encoding="utf-8")
            self.assertEqual(docs.check_file(path), [])
            path.write_text("instruction\n" * 200, encoding="utf-8")
            self.assertIn("under 200 lines", docs.check_file(path)[0])

    def test_plans_need_sections_and_missing_files_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.md"
            self.assertIn("missing document", docs.check_file(path)[0])
            path.write_text("## Goal\n", encoding="utf-8")
            self.assertIn("missing plan section Verification", "\n".join(docs.check_file(path, plan=True)))
            path.write_text("\n".join(f"## {heading}" for heading in docs.PLAN_SECTIONS), encoding="utf-8")
            self.assertEqual(docs.check_file(path, plan=True), [])


if __name__ == "__main__":
    unittest.main()
