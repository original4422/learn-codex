# Runnable experiments

[中文](README.md)

Run commands from the learn-codex repository root with Python 3.10 or newer. Runtime experiments use only the standard library. The common entry point is `python3 scripts/course.py lab <name>`; `PYTHONPATH=src python3 -m codex_lab <name>` is equivalent. For an installed command, run `python3 -m pip install -e .` in your own virtual environment, then use `codex-lab`. Offline environments without setuptools can use the common entry point without installation.

## Continuing case: Taskboard

The completed reference is `examples/taskboard/taskboard.py`. This single-writer JSON CLI adds, lists, and completes tasks and filters by tags. Atomic replacement prevents a partially written JSON file. It does not prevent lost updates from concurrent writers.

```sh
python3 examples/taskboard/taskboard.py --store .local/demo-tasks.json add "Add regression tests" --tag Study --tag test
python3 examples/taskboard/taskboard.py --store .local/demo-tasks.json list --tag study --status open
python3 examples/taskboard/taskboard.py --store .local/demo-tasks.json done 1
python3 examples/taskboard/acceptance.py
```

The first ID in a fresh store is 1; subsequent IDs are the maximum existing ID plus one. Repeating a command does not reset data. Tags are trimmed, lowercased, deduplicated, and sorted; filtering matches whole tags. Legacy tasks without `tags` receive an empty list. Titles contain 1–200 characters; there may be up to 20 tags of 1–40 characters each. Errors exit with code 2. Place `--store` before the subcommand.

Prepare a real editing exercise:

```sh
python3 examples/taskboard/prepare_exercise.py .local/taskboard-practice
python3 .local/taskboard-practice/taskboard.py --store .local/practice-data.json add "Read the code"
python3 examples/taskboard/acceptance.py --script .local/taskboard-practice/taskboard.py
```

Preparation refuses to overwrite an existing directory. Acceptance data goes to `.cache/tmp` beside the target script, so it stays inside the practice directory's workspace-write boundary. The baseline supports add/list/done and status filtering but lacks tags: two basic acceptance checks pass and two tag checks fail by design. Ask Codex to implement the feature in the practice copy, then rerun the same acceptance script. The default reference passes all four checks. Atomic failure, malformed data, and ID validation tests are in `tests/test_taskboard.py`.

## Mechanism experiments and expected observations

```sh
python3 scripts/course.py lab loop
python3 scripts/course.py lab loop --fail-tool
python3 scripts/course.py lab loop --max-steps 1
python3 scripts/course.py lab instructions
python3 scripts/course.py lab policy --action write --approved --isolation read-only
python3 scripts/course.py lab context
python3 scripts/course.py lab subagents
```

| Experiment | Observation | Explicit boundary |
| --- | --- | --- |
| loop | Tool starts, tool returns, final message counts two open tasks | Scripted mock; does not evaluate a model |
| loop --fail-tool | Tool error becomes an observation; final reports the failure | Does not disguise errors as successful data |
| loop --max-steps 1 | status is budget_exhausted | Separate step and tool-call limits |
| instructions | Ordered global, root, and nested override text | Explicit root; no Git discovery, config parsing, or full trust model |
| policy | approval_satisfied is true; isolation_allows is false | Decision table only, no OS sandbox; ask/never are teaching enums |
| context | Long tool output removed; constraints, decisions, open work, and recent message retained | Extractive character budget, not Codex token/model compaction |
| subagents | Two scoped reports checked against the source snapshot | Independent Python workers; no real Codex child agents |

For project instruction discovery, an empty `AGENTS.override.md` shadows the same directory's `AGENTS.md`; global discovery skips empty files. The total byte budget may truncate text without splitting UTF-8 characters. This model composes text rather than resolving semantic conflicts between instructions.

## Real MCP stdio experiment

```sh
python3 scripts/course.py lab mcp-demo
python3 scripts/course.py lab mcp-server --root examples/mcp-data
```

`mcp-demo` starts a real Python child process and performs initialize, notifications/initialized, tools/list, and tools/call, returning notes.md. The second command runs the server, which waits for client input and normally prints nothing by itself; stop with Ctrl-C. Each protocol message is a JSON line. Reserve stdout for protocol output, never logs.

`read_note` reads only `.md/.txt/.json` files inside the root, up to 8192 bytes each. It rejects absolute paths, `..`, symlinks, and escaped paths. `task_stats` applies the same bounds and validates a JSON array with boolean `done` values before counting. Protocol errors use JSON-RPC error responses; failures while executing valid tool calls use `isError: true`. This server does not implement HTTP, resource subscriptions, or authentication. Use a trusted local root: path validation is not an OS sandbox and cannot defend against another process concurrently replacing directories.

To connect the server to real Codex, add it as a stdio MCP server in temporary CLI configuration. Use absolute paths: Python arguments are `-m codex_lab mcp-server --root <absolute-root>`, with environment `PYTHONPATH=<absolute-project>/src`. See the MCP chapter for complete configuration. Passing this experiment does not prove a real Codex model selected or called the tool.

## Real CLI and model verification boundaries

```sh
python3 scripts/course.py lab probe
python3 scripts/course.py lab app-server
```

The first reads the installed version and help. The second launches real `codex app-server` and performs initialize → initialized → thread/loaded/list. Neither calls a model. App Server messages differ from MCP; do not transfer its methods or lifecycle to MCP. CLI state stays in this project's `.cache/codex-home`; temporary files stay in `.cache/tmp`.

A real model run requires explicit selection and may consume model usage:

```sh
CODEX_HOME="$PWD/.cache/codex-home" codex login
python3 scripts/course.py lab exec --allow-model --timeout 120
```

Alternatively, supply an existing `CODEX_API_KEY` to this process; never put keys in the repository or logs. The experiment neither reads nor copies the host's auth.json. Use `--model <available-model>` for a model your account actually supports. The integration invokes `codex exec --json --ephemeral --ignore-user-config --sandbox read-only --output-schema ...`, asks the model to read the sample, and then verifies completion events, the four-field final JSON, total count 3, and open count 2. JSONL and the final message are written to `.cache/real-exec`. Inspect artifacts before sharing because events may include local machine information.

Missing `--allow-model`, absent authentication, timeouts, failure events, invalid JSON, and wrong counts all fail. Mock tests and synthetic subprocess tests never count as real model verification. Consult the repository acceptance report for the actual recorded verification status.

## Verification and troubleshooting

```sh
python3 -m unittest discover -s tests -v
python3 examples/taskboard/acceptance.py
```

If codex is missing, install the official CLI and rerun probe. For an App Server timeout, check the probe version and stdio flags; disabling sandboxing does not fix a protocol problem. If the practice directory exists, choose another path. Preserve malformed Taskboard JSON and repair it manually or use a fresh store; the CLI never silently resets it. For MCP path failures, check extension, size, root, and symlinks. Failures go to stderr with nonzero exit codes; automation must check those codes.
