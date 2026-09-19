# 08 · MCP: give the agent a bounded tool

## Learning goals

Expose Taskboard reference material through local stdio tools; observe initialization, discovery, and invocation; reject escaped paths, symbolic links, and oversized files. Distinguish evidence that a model selected a tool, a protocol carried a request, and a tool performed an operation.

## Start with use: run a separate tool process

From the repository root:

```sh
python3 scripts/course.py lab mcp-demo
```

This starts the course's Python MCP server as a child process, completes `initialize` → `notifications/initialized` → `tools/list` → `tools/call`, reads `examples/mcp-data/notes.md`, and ends the process. No Codex login or model request is needed.

**What to observe:** output should contain server information, tools named `read_note` and `task_stats`, and a successful text result. This is actual interprocess protocol communication. The client chooses the invocation directly, so it does not demonstrate a model selecting a tool.

## Observe the protocol: messages have different roles

```text
Client                         Local server
  initialize (id=1)     ───→   Negotiate version/capabilities
                        ←───   result (id=1)
  notifications/initialized → Enter callable state
  tools/list (id=2)     ───→   Return definitions/inputSchema
                        ←───   result (id=2)
  tools/call (id=3)     ───→   Validate, then perform bounded read
                        ←───   content / isError
```

Requests have IDs and responses match them. Notifications have no ID or expected response. A tool operation can fail with `result.isError=true`, while an invalid JSON-RPC request returns an `error` object. Labeling both “model failures” obscures where to investigate.

**Teaching implementation:** [mcp_server.py](../../src/codex_lab/mcp_server.py) implements the bounded subset required here: newline-delimited JSON, initialization, ping, tool listing, and invocation. It does not implement HTTP, OAuth, resource subscriptions, or production concurrency. stdout contains protocol JSON only; diagnostics belong on stderr.

## Tool contracts: enforce boundaries in code

| Tool | Input | Success | Rejection boundaries |
| --- | --- | --- | --- |
| `read_note` | `{"path":"notes.md"}` | UTF-8 text | Absolute paths, `..`, symlinks, disallowed extensions, more than 8192 bytes |
| `task_stats` | Relative path to a JSON task array | total/open/done | Read boundaries plus non-array data and non-boolean done |

The server root is chosen at startup, not selected by the model per call. Annotations such as `readOnlyHint` describe a tool; they do not enforce safety. `bounded_read()` performs actual checks. A request to read outside the root must still fail even if the model says it is necessary.

Path validation is not an OS sandbox. This lab assumes a trusted local data directory and does not defend against a hostile concurrent process replacing directories between validation and reading. Untrusted concurrent writes require a different isolation and file-access design; this teaching service is not a security gateway.

## Connect real Codex with one-run configuration

The [official MCP documentation](https://learn.chatgpt.com/docs/extend/mcp) describes local stdio and HTTP connections. Use one-run `-c` overrides rather than changing global user configuration. Start in the repository root:

```sh
codex \
  -c 'mcp_servers.course.command="python3"' \
  -c "mcp_servers.course.args=[\"$PWD/scripts/course.py\",\"lab\",\"mcp-server\",\"--root\",\"$PWD/examples/mcp-data\"]" \
  -c 'mcp_servers.course.required=true'
```

This command assumes the project path contains no double quotes or backslashes. For such paths, use correctly TOML-escaped absolute paths in configuration. In the session, inspect `/mcp` and ask: “Use course's read_note to read notes.md and summarize the returned content. Do not substitute a shell read.” Check the tool name, arguments, and result in the trace. Without a tool invocation, the answer alone is not evidence of tool use.

This step needs working Codex authentication, a model, and MCP tool availability, and may incur model usage. `required=true` exposes connection failures; it does not guarantee every invocation succeeds. The acceptance report separates the standalone protocol demonstration from actual model-driven tool use.

## Mechanism and source: discovery, routing, execution

**Official implementation:** the pinned [RmcpClient](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/rmcp-client/src/rmcp_client.rs#L609) exposes initialization, discovery, and invocation. The [MCP handler](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/mcp.rs#L176) connects an agent tool call to execution. Our Python server is an external tool provider, not a translation of the Rust client.

Start with the schema from `tools/list`, then follow the name and arguments in `tools/call`. Descriptions help a model choose a tool, but the server still validates types, fields, and boundaries. MCP grants no automatic permission to arbitrary tools and does not turn external text into trusted instructions.

## Runnable failure experiment

Verify an escaped path produces a tool error while the server remains responsive:

```sh
PYTHONPATH=src python3 - <<'PY'
from codex_lab.mcp_server import Server
s = Server("examples/mcp-data")
s.dispatch({"jsonrpc":"2.0","id":1,"method":"initialize","params":{
    "protocolVersion":"2025-11-25","capabilities":{},
    "clientInfo":{"name":"course-check","version":"1"}}})
s.dispatch({"jsonrpc":"2.0","method":"notifications/initialized"})
r = s.dispatch({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{
    "name":"read_note","arguments":{"path":"../taskboard/sample.json"}}})
assert r["result"]["isError"] is True
assert "result" in s.dispatch({"jsonrpc":"2.0","id":3,"method":"ping"})
print(r["result"]["content"][0]["text"])
PY
```

Expect `parent traversal are forbidden`. This direct Python dispatcher call isolates the rejection branch. The earlier `mcp-demo` checks real child-process transport. Both are useful, different checks.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Empty tool list or failed initialization | Python path, working directory, existing root, and initialized notification |
| JSON parse errors | Logs contaminating stdout, or more than one JSON object per line |
| Existing file rejected | Symlinks, extension, root escape, or size limit |
| Tools listed but model did not call one | Task and tool request, actual invocation events; discovery is not invocation |

## Exercise and next step

Place a `tasks.json` in an experimental copy of `examples/mcp-data/`, with one completed and two open tasks. Call `task_stats`; expect `total=3, open=2, done=1`. Change one `done` to the string `"false"`; expect a tool error instead of treating a nonempty string as true. Keep the input and failure evidence.

Next, delegate independent review tasks in [09 · Subagents](09-subagents.md).
