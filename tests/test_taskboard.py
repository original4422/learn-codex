import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from helpers import ROOT, temporary_directory
import taskboard


class TaskboardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = temporary_directory()
        self.addCleanup(self.temporary.cleanup)
        self.store = Path(self.temporary.name) / "tasks.json"

    def test_add_list_done_and_deterministic_ids(self):
        first = taskboard.add(self.store, " First ", [" Study ", "study", "TEST"])
        second = taskboard.add(self.store, "Second", ["study-guide"])
        self.assertEqual([first["id"], second["id"]], [1, 2])
        self.assertEqual(first["tags"], ["study", "test"])
        self.assertEqual(first["title"], "First")
        self.assertEqual([t["id"] for t in taskboard.list_tasks(self.store, "STUDY")], [1])
        self.assertTrue(taskboard.done(self.store, 1)["done"])
        self.assertEqual(len(taskboard.list_tasks(self.store, status="done")), 1)
        self.assertEqual(len(taskboard.list_tasks(self.store, status="open")), 1)
        self.assertEqual(taskboard.done(self.store, 1)["id"], 1)

    def test_ids_follow_max_not_array_length(self):
        taskboard.save(self.store, [{"id": 10, "title": "Migrated", "done": False}])
        self.assertEqual(taskboard.add(self.store, "Next")["id"], 11)

    def test_old_store_without_tags_is_readable(self):
        self.store.write_text('[{"id":1,"title":"legacy","done":false}]')
        self.assertEqual(taskboard.load(self.store)[0]["tags"], [])

    def test_bad_json_is_never_overwritten(self):
        self.store.write_text("broken [")
        with self.assertRaises(ValueError):
            taskboard.add(self.store, "Valid title")
        self.assertEqual(self.store.read_text(), "broken [")

    def test_atomic_replace_failure_preserves_original_and_cleans_temp(self):
        taskboard.add(self.store, "Original")
        before = self.store.read_bytes()
        with patch.object(taskboard.os, "replace", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                taskboard.add(self.store, "Should not persist")
        self.assertEqual(self.store.read_bytes(), before)
        self.assertEqual(list(self.store.parent.glob(".taskboard-*")), [])

    def test_unknown_id_preserves_original(self):
        taskboard.add(self.store, "Original")
        before = self.store.read_bytes()
        with self.assertRaises(ValueError):
            taskboard.done(self.store, 99)
        self.assertEqual(self.store.read_bytes(), before)

    def test_reject_invalid_data(self):
        invalid = [None, {}, [{"id": True, "title": "x", "done": False}],
                   [{"id": 1, "title": "x", "done": "false"}],
                   [{"id": 1, "title": "", "done": False}],
                   [{"id": 1, "title": "x", "done": False, "tags": [3]}],
                   [{"id": 1, "title": "x", "done": False}] * 2]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                taskboard.validate(value)

    def test_reject_bad_title_tag_and_oversized_store(self):
        for title in (" ", "x" * 201):
            with self.assertRaises(ValueError):
                taskboard.add(self.store, title)
        with self.assertRaises(ValueError):
            taskboard.add(self.store, "x", [" "])
        self.store.write_bytes(b" " * (taskboard.MAX_BYTES + 1))
        with self.assertRaises(ValueError):
            taskboard.load(self.store)

    def test_cli_roundtrip_and_error_exit(self):
        command = [sys.executable, str(ROOT / "examples/taskboard/taskboard.py"), "--store", str(self.store)]
        result = subprocess.run(command + ["add", "中文 task", "--tag", "study"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["title"], "中文 task")
        result = subprocess.run(command + ["done", "999"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("does not exist", result.stderr)

    def test_deep_json_fails_without_traceback_or_overwrite(self):
        raw = "[" * 2000 + "]" * 2000
        self.store.write_text(raw)
        result = subprocess.run([sys.executable, str(ROOT / "examples/taskboard/taskboard.py"),
            "--store", str(self.store), "add", "New"], capture_output=True, text=True, timeout=3)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(self.store.read_text(), raw)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires a named pipe")
    def test_fifo_store_is_rejected_without_blocking(self):
        os.mkfifo(self.store)
        result = subprocess.run([sys.executable, str(ROOT / "examples/taskboard/taskboard.py"),
            "--store", str(self.store), "list"], capture_output=True, text=True, timeout=3)
        self.assertEqual(result.returncode, 2)
        self.assertIn("regular file", result.stderr)


if __name__ == "__main__":
    unittest.main()
