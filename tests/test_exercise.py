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
