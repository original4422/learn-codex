# Concepts and source map

Trace one behavior to one entry point, then verify one invariant. Every link below pins `rust-v0.155.1` at commit `be2951ea34f0d295ed0becf97079f92fa5f6950e`, not the moving main branch. See [sources and versions](sources.md) for evidence.

## Find code by question

| Observed question | Pinned entry point | Symbol or responsibility | Lesson |
| --- | --- | --- | --- |
| First run | [main.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/cli/src/main.rs#L1) | CLI command dispatch | [01](01-first-task.md) |
| Why one request calls several tools | [turn.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/turn.rs#L163) | run_turn → run_sampling_request | [03](03-agent-loop.md) |
| Tool routing | [router.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/router.rs#L74) | ToolRouter | [03](03-agent-loop.md) |
| Instructions for the working directory | [agents_md.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/agents_md.rs#L55) | load_project_instructions → agents_md_paths | [04](04-instructions.md) |
| Global instructions | [mod.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/codex-home/src/instructions/mod.rs#L24) | load_from_codex_home | [04](04-instructions.md) |
| Skill discovery | [discovery.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/ext/skills/src/loader/discovery.rs#L1) | Sources and search roots | [05](05-skills.md) |
| Skill content | [render.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/ext/skills/src/render.rs#L1) | Rendering skill information for the model | [05](05-skills.md) |
| Execution and approvals | [orchestrator.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/orchestrator.rs#L1) | Tool execution orchestration | [06](06-safety.md) |
| Approval is not sandboxing | [sandboxing.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/sandboxing.rs#L194) | default_exec_approval_requirement | [06](06-safety.md) |
| Resume a session | [rollout_reconstruction.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/rollout_reconstruction.rs#L12) | RolloutReconstruction | [07](07-context.md) |
| Compaction dispatch | [compact.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tasks/compact.rs#L29) | Path selection by capabilities and features | [07](07-context.md) |
| Model window after compaction | [history.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/context_manager/history.rs#L72) | ContextManager | [07](07-context.md) |
| MCP connection | [rmcp_client.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/rmcp-client/src/rmcp_client.rs#L609) | initialize → list_tools → call_tool | [08](08-mcp.md) |
| MCP dispatch | [mcp.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/mcp.rs#L176) | handle_call | [08](08-mcp.md) |
| Subagent context | [spawn.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/multi_agents_v2/spawn.rs#L291) | fork_mode | [09](09-subagents.md) |
| Shared directory boundary | [multi_agents.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/multi_agents.rs#L60) | Shared filesystem and context instructions | [09](09-subagents.md) |
| JSONL events | [exec_events.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/exec/src/exec_events.rs#L11) | ThreadEvent | [10](10-automation.md) |
| Events to output | [event_processor_with_jsonl_output.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/exec/src/event_processor_with_jsonl_output.rs#L1) | JSONL output processor | [10](10-automation.md) |
| App Server handshake | [initialize_processor.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/app-server/src/request_processors/initialize_processor.rs#L49) | initialize | [10](10-automation.md) |
| TypeScript SDK | [exec.ts](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/sdk/typescript/src/exec.ts#L91) | CodexExec.run launches the CLI | [10](10-automation.md) |
| Python SDK | [client.py](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/sdk/python/src/openai_codex/client.py#L215) | JSON-RPC client | [10](10-automation.md) |

## What a source-reading session should produce

For session recovery, start with “Why can work continue after closing the terminal?” Locate recovery types and history reconstruction, then distinguish the on-disk log, the model's input window, and the current working tree. These are different data. You should identify the function that reconstructs history and design a local check for “resuming a conversation does not undo file edits.”

In a large function, follow only the relevant inputs, branches, and outputs. In `tasks/compact.rs`, observe the feature branch followed by provider compaction capability matching. That disproves “every model uses the same summarization algorithm.” It does not establish when a particular account automatically compacts; that also needs runtime configuration, model information, and real events.

## Which files are teaching code

| Course code | Demonstrates | Deliberately omits |
| --- | --- | --- |
| `src/codex_lab/mechanisms.py` | Loops, instruction discovery, approvals versus isolation, compaction, aggregation checks | Network models, complete configuration layers, actual OS sandboxing |
| `src/codex_lab/mcp_server.py` | stdio MCP lifecycle and bounded file tools | Remote authentication, complete protocol capabilities, production deployment |
| `src/codex_lab/adapters.py` | CLI JSONL, structured output, App Server handshake | Production retries and a complete UI client |
| `examples/taskboard/taskboard.py` | A real application that can be tested and reviewed | Multi-writer database transactions and deployment |

These are not a Python rewrite of Codex. Preserve the boundaries of native Rust, TypeScript, and the Python SDK when reading upstream. The desktop lesson has no private UI source links; the public App Server protocol establishes only the service integration boundary.

## Exercise: inspect an evidence chain

Choose one row and record five things: claim, pinned source, runnable command, observable result, and what remains unproven. If you have only a filename and cannot describe inputs and outputs, narrow the question. If your installed version differs, record the difference before choosing experiments to rerun; do not silently replace commit links with main.
