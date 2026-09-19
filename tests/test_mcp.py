import io
import json
from pathlib import Path
import unittest

from helpers import ROOT, temporary_directory
from codex_lab.adapters import mcp_demo
from codex_lab.mcp_server import MAX_FRAME, Server, bounded_read, serve


class McpTests(unittest.TestCase):
    def setUp(self):
        self.temporary = temporary_directory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "note.md").write_text("bounded note")
        (self.root / "tasks.json").write_text('[{"done":false},{"done":true}]')
        self.server = Server(self.root)

    def request(self, method, params=None, identifier=1):
        return self.server.dispatch({"jsonrpc": "2.0", "id": identifier,
                                     "method": method, "params": params or {}})

    def initialize(self):
        result = self.request("initialize", {"protocolVersion": "2025-11-25", "capabilities": {},
                                            "clientInfo": {"name": "test", "version": "1"}})
        self.assertEqual(result["result"]["protocolVersion"], "2025-11-25")
        self.assertIsNone(self.server.dispatch({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_initialization_required_and_duplicate_rejected(self):
        self.assertIn("error", self.request("tools/list"))
        self.initialize()
        self.assertIn("error", self.request("initialize"))

    def test_listing_read_and_stats(self):
        self.initialize()
        tools = self.request("tools/list")["result"]["tools"]
        self.assertEqual({t["name"] for t in tools}, {"read_note", "task_stats"})
        result = self.request("tools/call", {"name": "read_note", "arguments": {"path": "note.md"}})["result"]
        self.assertFalse(result["isError"])
        self.assertEqual(result["content"][0]["text"], "bounded note")
        result = self.request("tools/call", {"name": "task_stats", "arguments": {"path": "tasks.json"}})["result"]
        self.assertEqual(json.loads(result["content"][0]["text"]), {"total": 2, "open": 1, "done": 1})

    def test_bad_tool_arguments_are_protocol_errors(self):
        self.initialize()
        for params in ({"name": "unknown"}, {"name": "read_note", "arguments": []},
                       {"name": "read_note", "arguments": {"path": "note.md", "extra": True}},
                       {"name": "read_note", "arguments": {"path": 1}}):
            with self.subTest(params=params):
                self.assertEqual(self.request("tools/call", params)["error"]["code"], -32602)

    def test_failed_tool_is_result_with_iserror(self):
        self.initialize()
        for path in ("missing.md", "../note.md", "/etc/passwd"):
            result = self.request("tools/call", {"name": "read_note", "arguments": {"path": path}})
            self.assertTrue(result["result"]["isError"])
            self.assertNotIn(str(self.root), result["result"]["content"][0]["text"])

    def test_traversal_symlink_extension_and_size_bounds(self):
        (self.root / "alias.md").symlink_to(self.root / "note.md")
        (self.root / "large.txt").write_bytes(b"x" * 8193)
        (self.root / "script.py").write_text("pass")
        for name in ("../note.md", str(self.root / "note.md"), "alias.md", "large.txt", "script.py"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                bounded_read(self.root, name)

    def test_malformed_task_data_is_not_counted(self):
        (self.root / "tasks.json").write_text('[{"done":"false"}]')
        self.initialize()
        result = self.request("tools/call", {"name": "task_stats", "arguments": {"path": "tasks.json"}})
        self.assertTrue(result["result"]["isError"])

    def test_malformed_envelopes_and_unknown_method(self):
        for value in ([], None, {}, {"jsonrpc": "2.0", "id": True, "method": "ping"}):
            self.assertEqual(self.server.dispatch(value)["error"]["code"], -32600)
        self.initialize()
        self.assertEqual(self.request("missing")["error"]["code"], -32601)
        self.assertIsNone(self.server.dispatch({"jsonrpc": "2.0", "method": "ignored-notification"}))

    def test_stream_recovers_after_malformed_and_oversized_frame(self):
        ping = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "ping"}).encode() + b"\n"
        input_stream = io.BytesIO(b"not JSON\n" + b"x" * (MAX_FRAME + 1) + b"\n" + ping)
        output = io.StringIO()
        serve(self.root, input_stream, output)
        replies = [json.loads(x) for x in output.getvalue().splitlines()]
        self.assertEqual([r.get("error", {}).get("code") for r in replies], [-32700, -32700, None])
        self.assertEqual(replies[-1]["id"], 2)

    def test_real_subprocess_transport(self):
        result = mcp_demo()
        self.assertFalse(result["read_note"]["isError"])
        self.assertIn("real Python subprocess", result["verification"])

    def test_stream_recovers_from_deep_json_and_nonfinite_constants(self):
        deep = b"[" * 2000 + b"]" * 2000 + b"\n"
        nonfinite = b'{"jsonrpc":"2.0","id":NaN,"method":"ping"}\n'
        ping = b'{"jsonrpc":"2.0","id":3,"method":"ping"}\n'
        output = io.StringIO()
        serve(self.root, io.BytesIO(deep + nonfinite + ping), output)
        replies = [json.loads(line) for line in output.getvalue().splitlines()]
        # Python versions differ in JSON nesting limits; either rejection must
        # preserve framing so the following valid request succeeds.
        self.assertIn(replies[0]["error"]["code"], {-32700, -32600})
        self.assertEqual([r.get("error", {}).get("code") for r in replies[1:]], [-32700, None])

    def test_initialize_rejects_missing_client_identity(self):
        response = self.request("initialize", {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {}})
        self.assertEqual(response["error"]["code"], -32602)
        self.assertFalse(self.server.initialized)

    def test_deep_task_json_is_a_tool_error_not_server_crash(self):
        (self.root / "tasks.json").write_text("[" * 2000 + "]" * 2000)
        self.initialize()
        result = self.request("tools/call", {"name": "task_stats", "arguments": {"path": "tasks.json"}})
        self.assertTrue(result["result"]["isError"])
        self.assertEqual(self.request("ping")["result"], {})

    def test_malformed_tool_names_do_not_kill_stream_server(self):
        frames = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2025-11-25", "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
        ]
        for identifier, name in enumerate(([], {}, None, 42, True), start=2):
            frames.append({"jsonrpc": "2.0", "id": identifier, "method": "tools/call",
                           "params": {"name": name, "arguments": {"path": "note.md"}}})
        frames.append({"jsonrpc": "2.0", "id": 99, "method": "ping"})
        incoming = io.BytesIO("".join(json.dumps(frame) + "\n" for frame in frames).encode())
        outgoing = io.StringIO()
        serve(self.root, incoming, outgoing)
        replies = [json.loads(line) for line in outgoing.getvalue().splitlines()]
        self.assertEqual(len(replies), 7)
        self.assertTrue(all(reply["error"]["code"] == -32602 for reply in replies[1:-1]))
        self.assertEqual(replies[-1], {"jsonrpc": "2.0", "id": 99, "result": {}})


if __name__ == "__main__":
    unittest.main()
