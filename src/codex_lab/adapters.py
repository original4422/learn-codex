"""Real Codex CLI/App Server and MCP subprocess adapters, using stdlib only."""

import json
import os
from pathlib import Path
import queue
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

def find_project_root():
    """A wheel lives in site-packages; fixtures still belong to the checkout.

    Prefer a checkout enclosing cwd, then a source/editable checkout. Installed
    commands are documented to run from the repository; mechanisms without
    fixture dependencies also work elsewhere with cwd as their working root.
    """
    current = Path.cwd().resolve()
    candidates = [current, *current.parents, *Path(__file__).resolve().parents]
    for candidate in candidates:
        if (candidate / "PROJECT_BRIEF.md").is_file() and (candidate / "examples/taskboard/sample.json").is_file():
            return candidate
    return current


ROOT = find_project_root()
MAX_OUTPUT = 4 * 1024 * 1024
SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {"project": {"type": "string"}, "total_tasks": {"type": "integer"},
                   "open_tasks": {"type": "integer"}, "summary": {"type": "string"}},
    "required": ["project", "total_tasks", "open_tasks", "summary"],
    "additionalProperties": False,
}


def local_environment():
    """Keep CLI state and temporary artifacts inside this project."""
    env = os.environ.copy()
    cache = ROOT / ".cache"
    for key, directory in (("CODEX_HOME", cache / "codex-home"),
                           ("TMPDIR", cache / "tmp"), ("XDG_CACHE_HOME", cache / "xdg")):
        directory.mkdir(parents=True, exist_ok=True)
        env[key] = str(directory)
    env["PYTHONPATH"] = str(ROOT / "src")
    return env


def stop_process(process):
    # A launcher can exit while descendants keep stdout open. Signal its whole
    # process group even when the launcher itself has already been reaped.
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except PermissionError:
            # Some host sandboxes report EPERM for an already vanished group.
            # A live direct child can still be terminated through Popen.
            if process.poll() is None:
                process.terminate()
    elif process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except PermissionError:
                if process.poll() is None:
                    process.kill()
        else:
            process.kill()
        process.wait(timeout=2)


class JsonProcess:
    """Line framing + deadlines + bounded stdout; every child is reaped."""

    def __init__(self, command, *, env=None, cwd=None):
        (ROOT / ".cache/tmp").mkdir(parents=True, exist_ok=True)
        self.errors = tempfile.TemporaryFile(dir=ROOT / ".cache/tmp")
        try:
            self.process = subprocess.Popen(command, cwd=cwd or ROOT, env=env,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.errors,
                start_new_session=(os.name == "posix"))
        except BaseException:
            self.errors.close()
            raise
        self.messages = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        total = 0
        try:
            while True:
                line = self.process.stdout.readline(MAX_OUTPUT + 1)
                if not line:
                    self.messages.put(None)
                    return
                total += len(line)
                if total > MAX_OUTPUT:
                    raise ValueError("subprocess stdout exceeded 4 MiB")
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError("subprocess frame must be a JSON object")
                self.messages.put(value)
        except BaseException as error:
            self.messages.put(error)

    def send(self, message):
        self.process.stdin.write((json.dumps(message) + "\n").encode())
        self.process.stdin.flush()

    def receive(self, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("subprocess deadline exceeded")
        try:
            value = self.messages.get(timeout=remaining)
        except queue.Empty as error:
            raise TimeoutError("subprocess deadline exceeded") from error
        if isinstance(value, BaseException):
            raise ValueError(f"invalid subprocess stream: {value}") from value
        return value

    def response(self, identifier, deadline):
        while True:
            value = self.receive(deadline)
            if value is None:
                raise RuntimeError("subprocess closed before responding")
            if value.get("id") == identifier:
                if "error" in value:
                    raise RuntimeError(f"protocol error: {value['error']}")
                if "result" not in value:
                    raise ValueError("response lacks result")
                return value["result"]

    def close(self):
        stop_process(self.process)
        self.reader.join(timeout=2)
        if self.reader.is_alive() and os.name == "posix":
            # A descendant may ignore TERM after its launcher has exited.
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except PermissionError:
                if self.process.poll() is None:
                    self.process.kill()
            self.reader.join(timeout=2)
        for stream in (self.process.stdin, self.process.stdout):
            if stream:
                try:
                    stream.close()
                except BrokenPipeError:
                    pass
        self.errors.close()

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.close()


def codex_binary():
    binary = shutil.which("codex")
    if binary is None:
        raise RuntimeError("codex is not on PATH; install the official CLI and run probe again")
    return binary


def probe():
    binary = codex_binary()
    env = local_environment()
    checks = {}
    for label, arguments in (("version", ["--version"]), ("exec_help", ["exec", "--help"]),
                             ("app_server_help", ["app-server", "--help"])):
        completed = subprocess.run([binary, *arguments], cwd=ROOT, env=env,
            capture_output=True, text=True, timeout=15, check=True)
        checks[label] = completed.stdout
    return {"verification": "real installed CLI; no model call", "binary": binary,
            "version": checks["version"].strip(),
            "exec_flags": {flag: flag in checks["exec_help"] for flag in
                           ("--json", "--output-schema", "--ephemeral", "--ignore-user-config")},
            "app_server_stdio": "stdio://" in checks["app_server_help"]}


def app_server_handshake(timeout=15):
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    deadline = time.monotonic() + timeout
    with JsonProcess([codex_binary(), "app-server", "--listen", "stdio://"], env=local_environment()) as child:
        child.send({"id": 1, "method": "initialize", "params": {
            "clientInfo": {"name": "learn_codex_lab", "title": "Learn Codex Lab", "version": "1.0.0"}}})
        result = child.response(1, deadline)
        if not isinstance(result, dict) or not isinstance(result.get("userAgent"), str):
            raise ValueError("initialize result lacks the expected userAgent")
        child.send({"method": "initialized", "params": {}})
        # A loaded-list read proves the server accepted the completed handshake.
        # It does not read stored user history from the isolated CODEX_HOME.
        child.send({"id": 2, "method": "thread/loaded/list", "params": {}})
        loaded = child.response(2, deadline)
    return {"verification": "real Codex App Server; no thread/start or turn/start; no model",
            "initialize": result, "loaded_threads": loaded}


def mcp_demo(timeout=10):
    deadline = time.monotonic() + timeout
    with JsonProcess([sys.executable, "-m", "codex_lab", "mcp-server", "--root",
                      str(ROOT / "examples/mcp-data")], env=local_environment()) as child:
        child.send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-11-25", "capabilities": {},
            "clientInfo": {"name": "learn-codex-client", "version": "1.0.0"}}})
        initialized = child.response(1, deadline)
        child.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        child.send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tools = child.response(2, deadline)
        child.send({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "read_note", "arguments": {"path": "notes.md"}}})
        result = child.response(3, deadline)
        if result.get("isError"):
            raise RuntimeError("MCP read_note failed")
    return {"verification": "real Python subprocess and MCP stdio; no Codex model/client",
            "initialize": initialized, "tools": tools["tools"], "read_note": result}


def validate_summary(value):
    if not isinstance(value, dict) or set(value) != set(SUMMARY_SCHEMA["required"]):
        raise ValueError("final summary must have exactly the schema's four fields")
    if value["project"] != "taskboard" or type(value["total_tasks"]) is not int or type(value["open_tasks"]) is not int:
        raise ValueError("invalid project or count types")
    if value["total_tasks"] != 3 or value["open_tasks"] != 2:
        raise ValueError("summary counts do not match the Taskboard sample")
    if not isinstance(value["summary"], str) or not value["summary"].strip():
        raise ValueError("summary must be a nonempty string")
    return value


def exec_summary(*, allow_model=False, model=None, timeout=120):
    if not allow_model:
        raise ValueError("real exec may incur model usage; explicitly pass --allow-model")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    output = ROOT / ".cache/real-exec"
    output.mkdir(parents=True, exist_ok=True)
    schema_path, last_path = output / "schema.json", output / "last-message.json"
    schema_path.write_text(json.dumps(SUMMARY_SCHEMA, indent=2) + "\n", encoding="utf-8")
    last_path.unlink(missing_ok=True)
    command = [codex_binary(), "exec", "--json", "--ephemeral", "--ignore-user-config",
               "--sandbox", "read-only", "--skip-git-repo-check", "--color", "never",
               "--output-schema", str(schema_path), "--output-last-message", str(last_path)]
    if model:
        command += ["--model", model]
    command += ["Read examples/taskboard/sample.json. Return project='taskboard', total_tasks, "
                "open_tasks, and a short summary. Count from the file. Do not modify any files."]
    deadline = time.monotonic() + timeout
    events = []
    # Truncate before launch and flush each event, so a timeout preserves this
    # attempt's partial evidence instead of leaving a previous successful run.
    with (output / "events.jsonl").open("w", encoding="utf-8") as transcript:
        with JsonProcess(command, env=local_environment()) as child:
            child.process.stdin.close()
            while True:
                message = child.receive(deadline)
                if message is None:
                    break
                events.append(message)
                transcript.write(json.dumps(message) + "\n")
                transcript.flush()
            child.process.wait(timeout=max(0.1, deadline - time.monotonic()))
            if child.process.returncode != 0:
                raise RuntimeError(f"codex exec exited {child.process.returncode}; inspect .cache/real-exec/events.jsonl (authentication may be required)")
    if not any(e.get("type") == "turn.completed" for e in events) or any(e.get("type") in {"error", "turn.failed"} for e in events):
        raise ValueError("event stream does not show a successful completed turn")
    value = validate_summary(json.loads(last_path.read_text(encoding="utf-8")))
    return {"verification": "real Codex model run; schema and sample counts checked",
            "event_types": [e.get("type") for e in events], "summary": value,
            "artifacts": str(output)}
