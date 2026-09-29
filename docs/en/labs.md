# Lab guide and verification layers

This is both an experiment index and a reproduction guide. From the repository root, run `python3 scripts/course.py lab --help`; append `--help` to an experiment for its options. No dependency installation is required: the shared entry point adds `src/` to the module path.

## Experiment index

| Command (prefix each with `python3 scripts/course.py lab`) | What to observe | Verification type |
| --- | --- | --- |
| `loop` | Causal order of tool start, result and final answer | Scripted model |
| `loop --fail-tool` | Error as an observation, never a fabricated success | Offline fault injection |
| `loop --max-tool-calls 0` | Stop when tool budget is exhausted | Offline budget check |
| `instructions` | Candidate files and order from home and root to cwd | Simplified discovery |
| `policy --isolation workspace-write --approved` | Approval and execution boundary both satisfied | Decision simulation; no OS sandbox |
| `context` | Preserve constraints, decisions and unfinished work | Extractive character-budget compaction |
| `subagents` | Independent snapshots, concurrent delegation and evidence aggregation | Python workers, not Codex subagents |
| `mcp-demo` | Initialize, list tools and call a bounded reader | Real stdio MCP subprocess |
| `probe` | Installed version and required flags | Real CLI, no model |
| `app-server` | initialize → initialized → thread/loaded/list | Real App Server, no model |
| `exec --allow-model` | JSONL events, structured output and factual checks | Real model; authentication required |

## Run and interpret output

```sh
python3 scripts/course.py lab instructions
python3 scripts/course.py lab context
python3 scripts/course.py lab subagents
python3 scripts/course.py lab mcp-demo
```

Each result includes `implementation` or `verification`. Read that field before interpreting the result. `loop --fail-tool` may finish with `completed`, meaning that the loop ended and reported the error. It does not mean the business tool succeeded. Inspect the event's `ok` field for tool success.

The subagent simulation's `verified_against_snapshot: true` means only that a local aggregator recomputed results against fixed data. It does not mean a model reviewed code. The MCP demo uses actual interprocess protocol traffic, but does not establish that a model autonomously selected the tool.

## Case project and exercise starter

The [reference implementation](../../examples/taskboard/taskboard.py) provides `add`, `list`, `done` and tag filtering. A nonexistent store means an empty list; corrupt JSON is an explicit failure and is never silently replaced with an empty store. Tests cover legacy data, empty titles, missing tasks, exact tag matching, store validation and failed atomic replacement.

Chapter 1 creates an exercise copy where you implement filtering while preserving the existing interface. Chapter 2 checks failure and regression paths. Chapter 5 packages acceptance in a callable Skill. Keep the starter and final diff for a useful retrospective instead of editing the reference merely to manufacture a passing exercise.

Run `python3 examples/taskboard/acceptance.py --script .local/taskboard-practice/taskboard.py` to check your exercise. Its six checks cover the basic CLI, tag normalization and sorting, exact filtering, legacy records, and data preservation. Boundary checks accept 40-character tags and 20 distinct normalized tags, including repeated input values. Empty tags, 41-character tags and 21 distinct tags must exit with code 2 and preserve the store byte for byte. The course tests also verify that the checker rejects implementations with tag validation or sorting removed.

```sh
python3 scripts/course.py test
python3 examples/taskboard/.agents/skills/taskboard-check/scripts/check.py
```

The Skill script performs independent black-box CLI checks. It provides cross-checking evidence rather than replacing the full test suite.

## Optional installation

Running from the checkout needs no installation. If you want the `codex-lab` command inside a virtual environment, install the local package. Build tooling may need access to a package index.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/codex-lab loop
```

If networking prevents installation of build dependencies, continue using `python3 scripts/course.py lab ...`. Both paths call the same code.

## Real CLI and model paths

The real CLI adapter keeps course state under `.cache/` and does not read your everyday Codex home history. It applies an output limit and deadline to the stream and reaps its child process on exit. See [adapters.py](../../src/codex_lab/adapters.py).

```sh
python3 scripts/course.py lab probe
python3 scripts/course.py lab app-server --timeout 15
python3 scripts/course.py lab exec --allow-model --timeout 120
```

The model experiment asks Codex to read a fixed sample and return `project`, `total_tasks`, `open_tasks` and `summary`. The adapter checks the exit code, `turn.completed`, error events, JSON fields and counts against the actual sample. Valid JSON alone does not establish a correct answer.

The sample has three tasks, two open. Its JSON Schema is written to `.cache/real-exec/schema.json`. Each run clears earlier output and flushes incoming events to `events.jsonl`; the final message is in `last-message.json`. A timeout preserves the partial events received during this run. A partial stream is not success: check the CLI error, completion event and validated result together. Do not commit real logs containing personal context.

## Troubleshooting order

1. Confirm the working directory, Python version and offline tests. Offline failures usually concern code or input, not a model.
2. Run `probe` to check that the CLI exists and supports the parameters. If the version differs, compare the [source record](sources.md).
3. Run `app-server`. A failed protocol handshake is different from failed authentication; inspect deadlines, protocol fields and local process state.
4. Check login inside the isolated Codex home, then run the model experiment. Authentication, networking, quota and model access can fail independently.
5. If the structure is valid but counts are wrong, record a factual verification failure. Do not weaken the validator to produce a pass.

## Verification boundaries

This project does not implement a production MCP framework, an operating-system sandbox, Codex's tokenizer or a full Agent scheduler. Source walkthroughs retain the implementation's native languages. Tests establish the explicitly listed behavior of this repository; separate observations support real product behavior. See the [acceptance record](acceptance.md) for commands actually run and delivery limitations.
