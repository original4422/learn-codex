"""Opt-in native Codex coding exercise with an external black-box verdict."""

import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from . import adapters

TASK = """Implement tags in taskboard.py using only the Python standard library.
Read the starter first, edit it, then run your own CLI checks in this workspace.
Keep add/list/done compatible, deterministic IDs, and atomic saves. Requirements:
1. add accepts repeated --tag; strip whitespace, lowercase, deduplicate and sort.
2. list --tag normalizes its argument and matches a whole tag, never a substring;
   combine with existing --status all/open/done. done preserves all tags.
3. Old records without tags load with tags=[]; the next ID is max(existing IDs)+1.
4. Unknown IDs and malformed stores fail with exit 2 without changing the store.
5. At most 20 distinct normalized tags per task, each 1–40 characters inclusive.
6. Empty/whitespace/too-long tags and too many distinct tags fail with exit 2,
   including invalid list --tag arguments; failed operations never change store.
Successful commands print JSON as before. Do not access files outside this
workspace. The independent evaluator is not available to you. Finish with a
short description of changes and self-check commands, not a claimed verdict.
"""


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def permissions(workspace, codex_home):
    # A more specific workspace entry allows the temporary candidate under the
    # denied checkout. Native subprocesses cannot read answers or auth material.
    entries = {str(Path.home().resolve()): "deny", str(adapters.ROOT.resolve()): "deny",
               str(Path(codex_home).resolve()): "deny", str(Path(workspace).resolve()): "write"}
    filesystem = ",".join(f"{json.dumps(k)}={json.dumps(v)}" for k, v in entries.items())
    profile = 'permissions.exercise={extends=":workspace",filesystem={' + filesystem + '}}'
    return ["-c", profile, "-c", 'default_permissions="exercise"']


def candidate_prefix(workspace, codex_home):
    return [adapters.codex_binary(), "sandbox", "-P", "exercise", "-C", str(workspace),
            *permissions(workspace, codex_home), "--", sys.executable, "-I", "-B"]


def candidate_environment(workspace):
    # Candidate subprocesses need no login, provider key, or host shell secrets.
    return {"PATH": str(Path(sys.executable).parent) + os.pathsep + os.defpath,
            "HOME": str(workspace), "TMPDIR": str(workspace),
            "CODEX_HOME": str(adapters.ROOT / ".cache/codex-home")}


def probe_isolation(workspace, codex_home, env):
    protected = [adapters.ROOT / "examples/taskboard/taskboard.py",
                 adapters.ROOT / "examples/taskboard/acceptance.py", Path(codex_home)]
    code = """import pathlib, sys
p=pathlib.Path('isolation-probe.txt'); p.write_text('ok'); assert p.read_text()=='ok'; p.unlink()
for name in sys.argv[1:]:
    try:
        p=pathlib.Path(name)
        list(p.iterdir()) if p.is_dir() else p.read_bytes()
    except PermissionError:
        continue
    raise SystemExit('protected path was readable: '+name)
print('workspace read/write allowed; answer, oracle, auth directory denied')
"""
    completed = subprocess.run(candidate_prefix(workspace, codex_home) + ["-c", code, *map(str, protected)],
                               cwd=workspace, env=env, capture_output=True, text=True, timeout=15)
    if completed.returncode:
        raise RuntimeError("isolation probe failed: " + completed.stderr + completed.stdout)
    return completed.stdout.strip()


def verify_candidate(script, prefix=None, env=None):
    """Reuse the six existing checks; only the candidate enters the sandbox."""
    path = adapters.ROOT / "examples/taskboard/acceptance.py"
    spec = importlib.util.spec_from_file_location("taskboard_external_acceptance", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SCRIPT = Path(script)

    class ExternalAcceptance(module.Acceptance):
        def run_cli(self, *args, expected_code=0):
            command = [*(prefix or [sys.executable, "-I", "-B"]), str(script), "--store", str(self.store), *args]
            completed = subprocess.run(command, cwd=Path(script).parent, env=env,
                                       capture_output=True, text=True, timeout=10)
            self.assertEqual(completed.returncode, expected_code, completed.stderr)
            return json.loads(completed.stdout) if expected_code == 0 else completed

    outcomes = []
    for name in unittest.defaultTestLoader.getTestCaseNames(ExternalAcceptance):
        result = unittest.TestResult()
        ExternalAcceptance(name).run(result)
        outcomes.append({"check": name, "passed": result.wasSuccessful(),
                         "failures": len(result.failures), "errors": len(result.errors)})
    return {"passed": all(item["passed"] for item in outcomes), "checks": outcomes}


def run(*, allow_model=False, codex_home=None, model="gpt-6-sol", timeout=240):
    if not allow_model:
        raise ValueError("exercise calls a real model; explicitly pass --allow-model")
    if not 0 < timeout <= 600:
        raise ValueError("exercise timeout must be between 0 and 600 seconds")
    env = adapters.local_environment()
    selected_home = Path(codex_home).expanduser().resolve(strict=True) if codex_home else Path(env["CODEX_HOME"])
    env["CODEX_HOME"] = str(selected_home)
    env.pop("OPENAI_API_KEY", None)
    auth = subprocess.run([adapters.codex_binary(), "login", "status"], env=env,
                          capture_output=True, text=True, timeout=15)
    if auth.returncode:
        raise RuntimeError("selected CODEX_HOME is not logged in; choose an existing logged-in home with --codex-home")
    cache = adapters.ROOT / ".cache/exercises"
    cache.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="taskboard-", dir=cache))
    output.chmod(0o700)
    workspace = output / "workspace"
    workspace.mkdir()
    source = adapters.ROOT / "examples/taskboard"
    original = (source / "starter.py").read_text()
    candidate = workspace / "taskboard.py"
    candidate.write_text(original)
    protected = {name: digest(source / name) for name in ("starter.py", "taskboard.py", "acceptance.py")}
    started = time.monotonic()
    result = {"verification": "real Codex coding task; external black-box acceptance",
              "status": "failed", "model": model, "artifacts": str(output),
              "protected_sha256": protected, "max_tool_calls": 20, "timeout_seconds": timeout}
    events = []
    phases = (output / "phases.jsonl").open("w")

    def phase(name, **fields):
        phases.write(json.dumps({"phase": name, "elapsed_seconds": round(time.monotonic()-started, 3), **fields}) + "\n")
        phases.flush()

    try:
        phase("prepared")
        candidate_env = candidate_environment(workspace)
        result["isolation"] = probe_isolation(workspace, selected_home, candidate_env)
        phase("isolation_checked")
        command = [adapters.codex_binary(), "exec", "--json", "--ephemeral", "--ignore-user-config",
                   "--ignore-rules", "--skip-git-repo-check", "--color", "never", "-C", str(workspace),
                   "--model", model, *permissions(workspace, selected_home),
                   "--output-last-message", str(output / "last-message.txt")]
        settings = {"approval_policy": "never", "web_search": "disabled", "project_doc_max_bytes": 0,
                    "features.multi_agent": False, "model_reasoning_effort": "low",
                    "shell_environment_policy.inherit": "none",
                    "shell_environment_policy.set.PATH": candidate_env["PATH"],
                    "shell_environment_policy.set.HOME": candidate_env["HOME"],
                    "shell_environment_policy.set.TMPDIR": candidate_env["TMPDIR"]}
        for key, value in settings.items():
            command += ["-c", f"{key}={json.dumps(value)}"]
        command += [TASK]
        deadline = time.monotonic() + timeout
        tool_calls = 0
        phase("model_started")
        with (output / "events.jsonl").open("w") as transcript:
            with adapters.JsonProcess(command, env=env, cwd=workspace) as child:
                try:
                    child.process.stdin.close()
                    while True:
                        event = child.receive(deadline)
                        if event is None:
                            break
                        events.append(event)
                        transcript.write(json.dumps(event) + "\n")
                        transcript.flush()
                        if event.get("type") == "item.completed" and event.get("item", {}).get("type") in {"command_execution", "file_change", "mcp_tool_call"}:
                            tool_calls += 1
                            if tool_calls > 20:
                                raise RuntimeError("exercise exceeded 20 tool calls")
                    child.process.wait(timeout=max(0.1, deadline-time.monotonic()))
                    result["model_exit_code"] = child.process.returncode
                finally:
                    child.errors.seek(0)
                    (output / "stderr.log").write_bytes(child.errors.read(4 * 1024 * 1024))
        phase("model_finished", tool_calls=tool_calls)
        completed = [e for e in events if e.get("type") == "turn.completed"]
        result["usage"] = [e.get("usage") for e in completed]
        if result["model_exit_code"] or not completed or any(e.get("type") in {"error", "turn.failed"} for e in events):
            raise RuntimeError("model did not complete successfully; private events preserved")
        if candidate.is_symlink() or not candidate.is_file():
            raise RuntimeError("candidate must remain a regular taskboard.py file")
        verdict = verify_candidate(candidate, candidate_prefix(workspace, selected_home), candidate_env)
        result["acceptance"] = verdict
        result["status"] = "passed" if verdict["passed"] else "failed"
        phase("independent_acceptance", passed=verdict["passed"])
    except (ValueError, OSError, RuntimeError, TimeoutError, subprocess.SubprocessError) as error:
        result["error"] = str(error)
        phase("failed", error=type(error).__name__)
    finally:
        result["protected_unchanged"] = all(digest(source / name) == value for name, value in protected.items())
        if not result["protected_unchanged"]:
            result["status"] = "failed"
        if candidate.is_symlink() or not candidate.is_file():
            result["status"] = "failed"
            result["error"] = "candidate must remain a regular taskboard.py file"
        else:
            final_source = candidate.read_text(errors="replace")
            (output / "candidate.diff").write_text("".join(difflib.unified_diff(original.splitlines(True), final_source.splitlines(True), fromfile="starter.py", tofile="taskboard.py")))
            result["candidate_sha256"] = digest(candidate)
        result["elapsed_seconds"] = round(time.monotonic()-started, 3)
        result["event_types"] = sorted({e.get("type", "unknown") for e in events})
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        phases.close()
    return result
