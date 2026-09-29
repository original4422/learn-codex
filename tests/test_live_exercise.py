import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch, Mock

from helpers import ROOT, temporary_directory
from codex_lab import exercise


class ExerciseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = temporary_directory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.script = self.root / 'taskboard.py'
        self.reference = (ROOT / 'examples/taskboard/taskboard.py').read_text()

    def verdict(self, text):
        self.script.write_text(text)
        return exercise.verify_candidate(self.script)

    def test_reference_passes_six_external_checks(self):
        result = self.verdict(self.reference)
        self.assertTrue(result['passed'], result)
        self.assertEqual(len(result['checks']), 6)

    def test_starter_rejected(self):
        result = self.verdict((ROOT / 'examples/taskboard/starter.py').read_text())
        self.assertFalse(result['passed'])
        self.assertFalse(result['checks'][1]['passed'])

    def test_substring_filter_rejected(self):
        faulty = self.reference.replace('tag in t["tags"]', 'any(tag in item for item in t["tags"])')
        self.assertNotEqual(faulty, self.reference)
        self.assertFalse(self.verdict(faulty)['checks'][1]['passed'])

    def test_missing_length_limit_rejected(self):
        faulty = self.reference.replace('len(t) > 40', 'len(t) > 400')
        self.assertNotEqual(faulty, self.reference)
        self.assertFalse(self.verdict(faulty)['checks'][5]['passed'])

    def test_opt_in_before_auth_or_model_launch(self):
        with patch.object(exercise.adapters, 'codex_binary') as binary:
            with self.assertRaisesRegex(ValueError, '--allow-model'):
                exercise.run()
            binary.assert_not_called()

    def test_deadline_must_be_bounded(self):
        for timeout in (0, -1, 601):
            with self.assertRaises(ValueError):
                exercise.run(allow_model=True, timeout=timeout)

    def test_unauthenticated_selection_never_launches_model(self):
        with patch.object(exercise.adapters, 'codex_binary', return_value='codex'), \
             patch.object(exercise.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)) as run:
            with self.assertRaisesRegex(RuntimeError, 'not logged in'):
                exercise.run(allow_model=True, codex_home=self.root)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[0][-2:], ['login', 'status'])

    def test_timeout_preserves_failed_attempt_and_partial_events(self):
        child = Mock()
        child.process.stdin = io.BytesIO()
        child.errors = io.BytesIO(b"diagnostic")
        child.receive.side_effect = [{"type": "thread.started"}, TimeoutError("deadline")]
        child.__enter__ = Mock(return_value=child)
        child.__exit__ = Mock(return_value=False)
        with patch.object(exercise.adapters, "codex_binary", return_value="codex"), \
             patch.object(exercise.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)), \
             patch.object(exercise, "probe_isolation", return_value="fixture"), \
             patch.object(exercise.adapters, "JsonProcess", return_value=child):
            result = exercise.run(allow_model=True, codex_home=self.root)
        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["protected_unchanged"])
        output = Path(result["artifacts"])
        self.assertEqual(json.loads((output / "result.json").read_text())["status"], "failed")
        self.assertEqual(json.loads((output / "events.jsonl").read_text())["type"], "thread.started")
        self.assertEqual((output / "stderr.log").read_text(), "diagnostic")
        self.assertTrue((output / "candidate.diff").exists())

    def test_candidate_environment_has_no_host_secrets(self):
        with patch.dict(exercise.os.environ, {"PRIVATE_TOKEN": "do-not-inherit"}):
            env = exercise.candidate_environment(self.root)
        self.assertNotIn("PRIVATE_TOKEN", env)
        self.assertEqual(env["HOME"], str(self.root))

    def test_permission_override_is_one_toml_table(self):
        arguments = exercise.permissions(self.root, ROOT / '.cache/codex-home')
        self.assertIn('filesystem={', arguments[1])
        self.assertIn(json.dumps(str(ROOT))+'="deny"', arguments[1])
        self.assertIn(json.dumps(str(self.root))+'="write"', arguments[1])


if __name__ == '__main__':
    unittest.main()
