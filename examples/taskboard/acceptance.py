#!/usr/bin/env python3
"""Black-box acceptance checks for either a learner solution or the reference."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().with_name("taskboard.py")
ROOT = Path(__file__).resolve().parents[2]


class Acceptance(unittest.TestCase):
    def setUp(self):
        # --cd practice workspace-write must not need a write outside practice.
        cache = SCRIPT.parent / ".cache/tmp"
        cache.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=cache)
        self.addCleanup(self.temporary.cleanup)
        self.store = Path(self.temporary.name) / "tasks.json"

    def run_cli(self, *args, expected_code=0):
        result = subprocess.run([sys.executable, str(SCRIPT), "--store", str(self.store), *args],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, expected_code, result.stderr)
        return json.loads(result.stdout) if expected_code == 0 else result

    def test_01_basic_roundtrip(self):
        self.assertEqual(self.run_cli("add", "Read code")["id"], 1)
        self.assertTrue(self.run_cli("done", "1")["done"])
        self.assertEqual(self.run_cli("list", "--status", "open"), [])
        self.assertEqual(len(self.run_cli("list", "--status", "done")), 1)

    def test_02_tags_normalize_deduplicate_and_match_exactly(self):
        task = self.run_cli("add", "Study", "--tag", "TEST", "--tag", " Study ", "--tag", "study")
        self.assertEqual(task["tags"], ["study", "test"])
        self.run_cli("add", "Other", "--tag", "study-guide")
        self.assertEqual([t["id"] for t in self.run_cli("list", "--tag", " STUDY ")], [1])
        self.run_cli("done", "1")
        self.assertEqual(self.run_cli("list", "--tag", "study", "--status", "open"), [])

    def test_03_legacy_data_uses_empty_tags_and_next_max_id(self):
        self.store.write_text('[{"id":7,"title":"Legacy","done":false}]')
        self.assertEqual(self.run_cli("list")[0]["tags"], [])
        self.assertEqual(self.run_cli("add", "New", "--tag", "new")["id"], 8)

    def test_04_failed_operations_preserve_store(self):
        self.run_cli("add", "Original")
        before = self.store.read_bytes()
        self.run_cli("done", "999", expected_code=2)
        self.assertEqual(self.store.read_bytes(), before)
        self.store.write_text("invalid json")
        self.run_cli("add", "New", expected_code=2)
        self.assertEqual(self.store.read_text(), "invalid json")

    def test_05_tag_limits_accept_boundary_values_after_normalization(self):
        tags = ["x" * 40, *[f"tag-{i:02}" for i in range(19)]]
        arguments = [value for tag in [*tags, f" {tags[0].upper()} "] for value in ("--tag", tag)]
        task = self.run_cli("add", "Boundary", *arguments)
        self.assertEqual(task["tags"], sorted(tags))
        self.assertEqual([t["id"] for t in self.run_cli("list", "--tag", "x" * 40)], [task["id"]])

    def test_06_invalid_tags_fail_without_changing_store(self):
        self.run_cli("add", "Original", "--tag", "keep")
        before = self.store.read_bytes()
        invalid_tags = ([""], [" "], ["x" * 41], [f"tag-{i}" for i in range(21)])
        for tags in invalid_tags:
            with self.subTest(tags=tags):
                arguments = [value for tag in tags for value in ("--tag", tag)]
                self.run_cli("add", "Invalid", *arguments, expected_code=2)
                self.assertEqual(self.store.read_bytes(), before)
        for tag in ("", " ", "x" * 41):
            with self.subTest(filter=tag):
                self.run_cli("list", "--tag", tag, expected_code=2)
                self.assertEqual(self.store.read_bytes(), before)


def main(argv=None):
    global SCRIPT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", type=Path, default=SCRIPT)
    args = parser.parse_args(argv)
    SCRIPT = args.script.resolve(strict=True)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Acceptance))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
