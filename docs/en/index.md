# From using Codex to understanding it

This is a practical Codex course for students and developers. Basic programming, terminal and Git knowledge is enough. Start with a task-list program, complete a small change with explicit acceptance criteria, then connect what you observe to public source code and minimal experiments.

## What you will take away

By the end, you should be able to write checkable requirements, have Codex read and modify an existing project, and judge the result using tests and a diff. You will explain the separate roles of instructions, tools, context and execution permissions, then connect repeatable steps to scripts and local tools.

The continuous case is **Taskboard**, a Python command-line task list backed by JSON. It is small enough to read completely, yet includes real constraints: persistence, compatibility, invalid input and atomic writes. The repository provides a finished reference implementation and a starter where you can implement tag filtering yourself.

## Three stages of learning

| Stage | Chapters | Learning artifact |
| --- | --- | --- |
| Complete something real | [First task](01-first-task.md), [development loop](02-workflow.md) | A change supported by tests and a reviewed diff |
| Understand what happened | [Tool loop](03-agent-loop.md), [instructions](04-instructions.md), [Skills](05-skills.md), [execution boundaries](06-safety.md), [context](07-context.md) | An explanation of success, failure and information loss |
| Build your workflow | [MCP](08-mcp.md), [subagents](09-subagents.md), [automation](10-automation.md), [desktop](11-desktop.md) | A bounded integration whose result can be checked |

Read in sequence on your first pass. If you already know the CLI, explore the important distinctions in the [mechanism playground](playground.md), then use the [source map](source-map.md).

## How to tell that you have learned it

“The command succeeded” is only the beginning. Each chapter asks for evidence: an acceptance contract, events, test output, a diff, a rejection reason or a structured result. Completion means being able to derive a conclusion from that evidence and identify what remains unverified.

Mark a chapter as learned at its end. Progress stays in this browser and is never uploaded. Switching language keeps the current chapter; both languages share progress.

## Three kinds of evidence

- **Official implementation**: public source pinned to Codex CLI `0.155.1` and official documentation. These establish product behavior and interfaces.
- **Observed behavior**: output from commands actually run locally. It applies to the environment and run in the report.
- **Teaching simplification**: the Python models and browser interactions in this repository. They isolate mechanisms; they are neither a Python rewrite of Codex nor an OS sandbox.

All offline experiments, the MCP protocol demo and the website run without a key. Real model experiments are enabled separately and need working authentication and connectivity. Passing offline tests does not establish a passing model run. See the [acceptance record](acceptance.md) for evidence.

## Start here

Run the commands in [quickstart](quickstart.md), then begin the first real task. Use the [lab guide](labs.md) to diagnose environment problems. Before contributing, read the [contribution guide](contributing.md) and [sources and versions](sources.md).

This independent educational project is not affiliated with OpenAI. The CLI is the main path; the desktop chapter discusses user-visible workflow correspondences only.
