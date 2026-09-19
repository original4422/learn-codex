# 10 · Automation: from terminal output to verifiable interfaces

## Learning goals

Generate a structured Taskboard summary with non-interactive CLI execution; separate events from final JSON; perform a real App Server handshake; choose between CLI, SDK, and App Server. A deliverable needs process evidence, final output, and semantic validation, not merely JSON-shaped text.

## Choose an interface first

| Need | Interface | Your responsibility |
| --- | --- | --- |
| One script task or CI step | `codex exec` | Input, deadlines, exit status, result validation |
| Consecutive tasks in application code | Codex SDK | Session lifecycle, errors, business rules |
| A custom client, approval UI, or event panel | `codex app-server` | Initialization, correlation, notifications, approvals, cancellation |
| External capabilities for Codex | MCP server | Tool contracts and server boundaries; see the previous lesson |

MCP supplies tools to an agent; App Server lets your client drive Codex. Sharing a JSON transport does not make them interchangeable. Official guides describe [SDK](https://learn.chatgpt.com/docs/codex-sdk) and [App Server](https://learn.chatgpt.com/docs/app-server) use cases.

## Actual use: a structured Taskboard summary

First check the installed interfaces without a model:

```sh
python3 scripts/course.py lab probe
```

Expect the version, recognized flags such as `--json`, `--output-schema`, and `--ephemeral`, and App Server stdio support. This runs help commands only.

Then explicitly request a model experiment:

```sh
python3 scripts/course.py lab exec --allow-model --timeout 120
# To select a model supported by your account:
python3 scripts/course.py lab exec --allow-model --model YOUR_AVAILABLE_MODEL
```

Replace the model name in the second command with one actually available to your account. No shared default availability is promised. The experiment runs real `codex exec --json --output-schema ... --sandbox read-only`, asking it to read `examples/taskboard/sample.json` without editing files. The course launches Codex instead of directly calling the Responses API.

**Authentication boundary:** the adapter stores CLI state in this project's ignored `.cache/codex-home`. It does not automatically use a login in your global Codex home. Supply `CODEX_API_KEY` only to this process through an existing secure credential mechanism, or log in interactively in this isolated environment:

```sh
PYTHONPATH=src python3 - <<'PY'
import subprocess
from codex_lab.adapters import codex_binary, local_environment
subprocess.run([codex_binary(), "login"], env=local_environment(), check=True)
PY
```

Login requires normal user authentication in a browser. Do not copy auth files or keys into tutorials, Git, or reports. The model run may incur usage. Without credentials, record the failure and still complete the handshake and offline checks below.

## Observe: events and answers are different outputs

[Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode) supports JSONL events and structured final responses. The course stores them separately in ignored `.cache/real-exec/`:

| File | Purpose | Check |
| --- | --- | --- |
| `schema.json` | Requested final shape | Four required fields, no additional fields |
| `events.jsonl` | Line-by-line process events | Completion and no fatal failure |
| `last-message.json` | Final answer | Parseable, correctly typed, counts match input |

Expect `project="taskboard"`, `total_tasks=3`, `open_tasks=2`, and a nonempty `summary`. Wording may vary; the three data values must match the sample. `--output-schema` constrains shape, not truth, so `validate_summary()` also checks semantics.

JSONL is one object per line, not one large JSON array. `item.completed` ends an item, not necessarily a successful turn; a tool item can itself fail. The model lab reports success only after a successful process, `turn.completed`, no fatal event, and validated final data. See the pinned [ThreadEvent](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/exec/src/exec_events.rs#L11) definitions.

## Minimal real integration: App Server without inference

```sh
python3 scripts/course.py lab app-server --timeout 15
```

The [adapter](../../src/codex_lab/adapters.py) launches real `codex app-server --listen stdio://` and performs:

```text
initialize(id=1, clientInfo) → result(userAgent, ...)
initialized notification
thread/loaded/list(id=2) → result(data, ...)
terminate child process
```

Expect `initialize.userAgent` and `loaded_threads`. A newly started isolated server normally has no loaded sessions. This demonstrates actual startup, bidirectional communication, and a post-initialization read. No `thread/start` or `turn/start` is sent, so it performs no inference or model-driven tool execution.

App Server uses `initialized`; MCP in the previous lesson uses `notifications/initialized`. Send each protocol's actual method even though both carry newline-delimited JSON. Match responses by ID rather than assuming the next line is the reply: notifications may interleave. The adapter bounds stdout, enforces deadlines, and reaps the child process so the demo does not leave a permanent server. [Pinned initialization handler](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/app-server/src/request_processors/initialize_processor.rs#L49)

A full client also needs `thread/start`, `turn/start`, notifications, user approvals, cancellation, and disconnect handling. A handshake alone is not a production client.

## What SDKs actually wrap

**Official implementation:** pinned [TypeScript CodexExec.run](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/sdk/typescript/src/exec.ts#L91) launches the CLI and consumes events; [Thread.run](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/sdk/typescript/src/thread.ts#L118) gathers items and the final answer. In contrast, [Python CodexClient](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/sdk/python/src/openai_codex/client.py#L215) uses App Server stdio JSON-RPC. An SDK does not necessarily call the model API directly.

This TypeScript interface example follows the official API. Installing the npm package and executing this snippet are not counted as completed course verification:

```typescript
import { Codex } from "@openai/codex-sdk";
const codex = new Codex();
const thread = codex.startThread({
  sandboxMode: "read-only",
  workingDirectory: process.cwd(),
});
const result = await thread.run("Read examples/taskboard/sample.json and count open tasks.");
console.log(result.finalResponse);
```

If you pursue this route, install the SDK in a separate directory following official documentation, record the actual package version, and add the same business validation. The repository's development package version is not necessarily an installable npm release number.

## Runnable result-rejection experiment

```sh
PYTHONPATH=src python3 - <<'PY'
from codex_lab.adapters import validate_summary
for wrong in (True, 99):
    try:
        validate_summary({"project":"taskboard","total_tasks":3,
                          "open_tasks":wrong,"summary":"Looks valid."})
    except ValueError as error:
        print(error)
    else:
        raise SystemExit("bad count was accepted")
PY
```

Python booleans subclass int, so validation uses exact type checks. It rejects `True` and also rejects integer `99` because it disagrees with the sample. No model is involved: this checks that the consumer does not blindly trust shape or prose.

## Troubleshooting and exercise

| Symptom | Meaning and next step |
| --- | --- |
| `codex` missing from PATH | Install the official CLI, then rerun probe |
| Authentication or network error | Preserve the actual failure category; isolated home does not inherit global login |
| Timeout | Incomplete run; do not consume an old answer; inspect model/network and retry explicitly |
| Correct schema but wrong count | Business validation failed; inspect the input instead of weakening the check |
| App Server handshake passes | Only protocol-layer evidence; check model-run status separately |

Exercise: add a fourth Taskboard task and predict why the current `validate_summary()` rejects the new count. Change validation to compute expected values from the actual input snapshot, then add a wrong-snapshot failure test. Do not merely change the constant 3 to 4.

Next, map the same loop to [desktop](11-desktop.md). See [acceptance](acceptance.md) for actual execution records.
