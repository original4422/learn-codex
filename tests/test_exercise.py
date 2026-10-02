from pathlib import Path
import subprocess
import sys
import unittest

from helpers import ROOT, temporary_directory


class ExerciseTests(unittest.TestCase):
    def test_reference_passes_blackbox_acceptance(self):
        result = subprocess.run([sys.executable, str(ROOT / "examples/taskboard/acceptance.py")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_starter_runs_but_feature_acceptance_fails(self):
        result = subprocess.run([sys.executable, str(ROOT / "examples/taskboard/acceptance.py"),
            "--script", str(ROOT / "examples/taskboard/starter.py")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("test_01_basic_roundtrip", result.stderr)
        self.assertIn("FAILED", result.stderr)

    def test_acceptance_rejects_missing_tag_validation(self):
        source = (ROOT / "examples/taskboard/taskboard.py").read_text()
        validation = ('    if len(result) > 20 or any(not t or len(t) > 40 for t in result):\n'
                      '        raise ValueError("provide at most 20 nonempty tags, each at most 40 characters")\n')
        self.assertIn(validation, source)
        self.assert_candidate_rejected(source.replace(validation, ""), "test_06_invalid_tags")

    def test_acceptance_rejects_unsorted_tags(self):
        source = (ROOT / "examples/taskboard/taskboard.py").read_text()
        normalization = "sorted(set(t.strip().lower() for t in tags))"
        self.assertIn(normalization, source)
        self.assert_candidate_rejected(source.replace(normalization,
            "list(dict.fromkeys(t.strip().lower() for t in tags))"), "test_02_tags")

    def assert_candidate_rejected(self, source, failing_check):
        with temporary_directory() as directory:
            candidate = Path(directory) / "taskboard.py"
            candidate.write_text(source)
            result = subprocess.run([sys.executable, str(ROOT / "examples/taskboard/acceptance.py"),
                "--script", str(candidate)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn(f"FAIL: {failing_check}", result.stderr)

    def test_exercise_copy_never_overwrites_work(self):
        with temporary_directory() as directory:
            destination = Path(directory) / "practice"
            command = [sys.executable, str(ROOT / "examples/taskboard/prepare_exercise.py"), str(destination)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            script = destination / "taskboard.py"
            self.assertEqual(script.read_bytes(), (ROOT / "examples/taskboard/starter.py").read_bytes())
            script.write_text("learner work")
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
            self.assertEqual(script.read_text(), "learner work")

    def test_acceptance_uses_target_local_cache_for_workspace_sandbox(self):
        with temporary_directory() as directory:
            target = Path(directory) / "taskboard.py"
            target.write_bytes((ROOT / "examples/taskboard/taskboard.py").read_bytes())
            result = subprocess.run([sys.executable, str(ROOT / "examples/taskboard/acceptance.py"),
                "--script", str(target)], cwd=target.parent, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((target.parent / ".cache/tmp").is_dir())


if __name__ == "__main__":
    unittest.main()
