import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

from helpers import ROOT, temporary_directory
from codex_lab import adapters
from codex_lab.adapters import JsonProcess, exec_summary, local_environment, validate_summary


class AdapterTests(unittest.TestCase):
    def test_model_call_requires_explicit_flag(self):
        with self.assertRaisesRegex(ValueError, "--allow-model"):
            exec_summary()

    def test_environment_scopes_writes_inside_repository(self):
        env = local_environment()
        for key in ("CODEX_HOME", "TMPDIR", "XDG_CACHE_HOME"):
            self.assertTrue(env[key].startswith(str(ROOT / ".cache")))

    def test_summary_validates_meaning_not_only_json_shape(self):
        value = {"project": "taskboard", "total_tasks": 3, "open_tasks": 2, "summary": "Two tasks remain."}
        self.assertEqual(validate_summary(value), value)
        for bad in ({**value, "open_tasks": 3}, {**value, "total_tasks": True},
                    {**value, "project": "other"}, {**value, "summary": ""}, {**value, "extra": 1}):
            with self.assertRaises(ValueError):
                validate_summary(bad)

    def test_protocol_response_ignores_notifications(self):
        script = 'import json; print(json.dumps({"method":"notice"})); print(json.dumps({"id":7,"result":{"ok":True}}))'
        with JsonProcess([sys.executable, "-c", script]) as child:
            self.assertEqual(child.response(7, time.monotonic() + 3), {"ok": True})

    def test_protocol_error_and_malformed_output_fail(self):
        for script, expected in (("print('invalid')", ValueError),
                ('print(\'{"id":1,"error":{"code":-1,"message":"failure"}}\')', RuntimeError)):
            with JsonProcess([sys.executable, "-c", script]) as child:
                with self.assertRaises(expected):
                    child.response(1, time.monotonic() + 3)

    def test_timeout_reaps_process(self):
        with JsonProcess([sys.executable, "-c", "import time; time.sleep(20)"]) as child:
            with self.assertRaises(TimeoutError):
                child.receive(time.monotonic() + 0.05)
        self.assertIsNotNone(child.process.poll())

    def test_output_budget_fails_and_reaps_process(self):
        with JsonProcess([sys.executable, "-c", "print('x' * 4200000)"]) as child:
            with self.assertRaisesRegex(ValueError, "4 MiB"):
                child.receive(time.monotonic() + 5)
        self.assertIsNotNone(child.process.poll())

    def test_early_exit_is_not_success(self):
        with JsonProcess([sys.executable, "-c", "pass"]) as child:
            with self.assertRaises(RuntimeError):
                child.response(1, time.monotonic() + 3)

    @unittest.skipUnless(os.name == "posix", "POSIX process group behavior")
    def test_exited_launcher_does_not_leave_stdout_held_by_descendant(self):
        script = ("import subprocess,sys,json; "
                  "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
                  "print(json.dumps({'child':p.pid}),flush=True)")
        start = time.monotonic()
        with JsonProcess([sys.executable, "-c", script]) as child:
            self.assertIn("child", child.receive(time.monotonic() + 3))
            child.process.wait(timeout=3)
        self.assertFalse(child.reader.is_alive())
        self.assertLess(time.monotonic() - start, 5)

    def test_installed_layout_finds_checkout_instead_of_site_packages(self):
        with temporary_directory() as directory:
            installed = Path(directory) / "site-packages"
            shutil.copytree(ROOT / "src/codex_lab", installed / "codex_lab", ignore=shutil.ignore_patterns("__pycache__"))
            env = os.environ.copy()
            env["PYTHONPATH"] = str(installed)
            result = subprocess.run([sys.executable, "-c",
                "from codex_lab import adapters; print(adapters.ROOT); print(adapters.__file__)"],
                cwd=ROOT, env=env, capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = result.stdout.splitlines()
            self.assertEqual(lines[0], str(ROOT))
            self.assertTrue(lines[1].startswith(str(installed)))

    @unittest.skipUnless(os.name == "posix", "executable fixture uses a POSIX shebang")
    def test_synthetic_exec_timeout_replaces_stale_artifacts_with_partial_events(self):
        # A deterministic subprocess fixture exercises transport, not a model.
        with temporary_directory() as directory:
            root = Path(directory)
            executable = root / "fake-codex"
            executable.write_text(f"#!{sys.executable}\nimport json,time\n"
                                  "print(json.dumps({'type':'thread.started'}),flush=True)\ntime.sleep(10)\n")
            executable.chmod(0o755)
            output = root / ".cache/real-exec"
            output.mkdir(parents=True)
            (output / "events.jsonl").write_text("STALE_SUCCESS")
            (output / "last-message.json").write_text("STALE_SUCCESS")
            with patch.object(adapters, "ROOT", root), patch.object(adapters, "codex_binary", return_value=str(executable)):
                with self.assertRaises(TimeoutError):
                    exec_summary(allow_model=True, timeout=1.0)
            self.assertEqual(json.loads((output / "events.jsonl").read_text()), {"type": "thread.started"})
            self.assertFalse((output / "last-message.json").exists())


if __name__ == "__main__":
    unittest.main()
