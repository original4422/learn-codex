"""Small MCP stdio server, implementing a documented bounded subset.

This is real JSON-RPC/MCP transport, not a fake MCP-shaped function call.
It does not implement HTTP, auth, resources, prompts, or subscriptions.
Use only with a trusted local root: path checks are not an OS sandbox and do
not defend against a concurrent process replacing directories during a read.
"""

import json
from pathlib import Path
import sys

PROTOCOL = "2025-11-25"
SUPPORTED = {PROTOCOL, "2025-03-26", "2024-11-05"}
MAX_FRAME = 65536
MAX_FILE = 8192


def reject_nonfinite(value):
    raise ValueError(f"non-finite constant {value} is not valid JSON")


def bounded_read(root, relative):
    if not isinstance(relative, str) or not relative or "\x00" in relative:
        raise ValueError("path must be a nonempty relative string")
    name = Path(relative)
    if name.is_absolute() or ".." in name.parts:
        raise ValueError("absolute paths and parent traversal are forbidden")
    root = Path(root).resolve(strict=True)
    candidate = root / name
    # Reject all symlink components, even ones currently resolving inside root.
    current = root
    for part in name.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("symbolic links are forbidden")
    path = candidate.resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("path must identify a regular file inside root")
    if path.suffix.lower() not in {".md", ".txt", ".json"}:
        raise ValueError("only .md, .txt, and .json files are allowed")
    with path.open("rb") as handle:
        raw = handle.read(MAX_FILE + 1)
    if len(raw) > MAX_FILE:
        raise ValueError("file exceeds the 8192-byte tool limit")
    return raw.decode("utf-8")


def tool_definitions():
    return [{"name": name, "description": description,
             "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}},
                             "required": ["path"], "additionalProperties": False},
             "annotations": {"readOnlyHint": True, "destructiveHint": False,
                             "idempotentHint": True, "openWorldHint": False}}
            for name, description in (
                ("read_note", "Read one UTF-8 .md/.txt/.json file under the configured root; max 8192 bytes."),
                ("task_stats", "Count total/open/done tasks from one JSON task array under the configured root."))]


class Server:
    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError("root must be a directory")
        self.initialized = False
        self.ready = False

    @staticmethod
    def error(identifier, code, message):
        return {"jsonrpc": "2.0", "id": identifier, "error": {"code": code, "message": message}}

    def dispatch(self, message):
        valid_id = isinstance(message, dict) and ("id" not in message or
                    type(message["id"]) in (str, int))
        if not valid_id or message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
            return self.error(None, -32600, "Invalid Request")
        identifier = message.get("id")
        method = message["method"]
        params = message.get("params", {})
        if "id" not in message:
            if method == "notifications/initialized" and self.initialized and isinstance(params, dict):
                self.ready = True
            return None
        if not isinstance(params, dict):
            return self.error(identifier, -32602, "params must be an object")
        if method == "initialize":
            if self.initialized:
                return self.error(identifier, -32600, "Already initialized")
            if not isinstance(params.get("protocolVersion"), str) or not isinstance(params.get("capabilities"), dict) or not isinstance(params.get("clientInfo"), dict):
                return self.error(identifier, -32602, "initialize requires protocolVersion, capabilities, clientInfo")
            if any(not isinstance(params["clientInfo"].get(key), str) for key in ("name", "version")):
                return self.error(identifier, -32602, "clientInfo requires string name and version")
            self.initialized = True
            requested = params["protocolVersion"]
            result = {"protocolVersion": requested if requested in SUPPORTED else PROTOCOL,
                      "capabilities": {"tools": {"listChanged": False}},
                      "serverInfo": {"name": "learn-codex-bounded-notes", "version": "1.0.0"}}
        elif method == "ping":
            result = {}
        elif not self.ready:
            return self.error(identifier, -32002, "Complete initialize and notifications/initialized first")
        elif method == "tools/list":
            result = {"tools": tool_definitions()}
        elif method == "tools/call":
            name, arguments = params.get("name"), params.get("arguments", {})
            if not isinstance(name, str) or name not in {"read_note", "task_stats"}:
                return self.error(identifier, -32602, "Unknown tool")
            if not isinstance(arguments, dict) or set(arguments) != {"path"} or not isinstance(arguments["path"], str):
                return self.error(identifier, -32602, "arguments must contain exactly one string path")
            try:
                text = bounded_read(self.root, arguments["path"])
                if name == "task_stats":
                    try:
                        tasks = json.loads(text, parse_constant=reject_nonfinite)
                    except RecursionError as error:
                        raise ValueError("task JSON nesting is too deep") from error
                    if not isinstance(tasks, list) or any(not isinstance(t, dict) or type(t.get("done")) is not bool for t in tasks):
                        raise ValueError("task file must be an array of objects with boolean done")
                    total, done = len(tasks), sum(t["done"] for t in tasks)
                    text = json.dumps({"total": total, "open": total - done, "done": done})
                result = {"content": [{"type": "text", "text": text}], "isError": False}
            except (OSError, ValueError) as error:
                # Do not disclose absolute host paths from OS error strings.
                reason = str(error) if isinstance(error, ValueError) else "file could not be read"
                result = {"content": [{"type": "text", "text": reason}], "isError": True}
        else:
            return self.error(identifier, -32601, "Method not found")
        return {"jsonrpc": "2.0", "id": identifier, "result": result}


def serve(root, input_stream=None, output_stream=None):
    server = Server(root)
    input_stream = input_stream or sys.stdin.buffer
    output_stream = output_stream or sys.stdout
    while True:
        line = input_stream.readline(MAX_FRAME + 1)
        if not line:
            return
        if len(line) > MAX_FRAME:
            # Consume the rest of the oversized frame before handling another.
            while line and not line.endswith(b"\n"):
                line = input_stream.readline(MAX_FRAME + 1)
            reply = server.error(None, -32700, "Frame exceeds 65536 bytes")
        else:
            try:
                message = json.loads(line, parse_constant=reject_nonfinite)
            except (ValueError, UnicodeDecodeError, RecursionError):
                reply = server.error(None, -32700, "Parse error")
            else:
                reply = server.dispatch(message)
        if reply is not None:
            output_stream.write(json.dumps(reply, ensure_ascii=False) + "\n")
            output_stream.flush()
