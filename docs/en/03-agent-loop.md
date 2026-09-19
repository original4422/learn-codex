# 03 · Understand the agent loop through a tool call

The result of this chapter is an event record you can explain: who proposed an action, who executed it, how the result reached the model, and why a finished answer does not establish a correct change. Complete [the first task](01-first-task.md), then relate the file reads, commands, and edits in the interface to a feedback loop.

## Start with a failing Taskboard test

Suppose you request task tags. Codex reads `taskboard.py` and runs an acceptance test. The test reports that `--tag` is unknown. The model chooses to edit argument handling, a tool performs the edit and returns a result, and the model runs another test. Work continues until it has sufficient evidence or encounters a blocking condition.

Three roles matter. The model chooses the next action from its current context. The host registers tools, interprets arguments, controls execution, and records results. Python, the shell, and the filesystem produce external facts. “I will run the tests” is an intention. A tool's exit code is execution evidence. The assertions determine what that execution actually verified.

```text
User goal + project instructions + previous events
                       |
                       v
             Model chooses an action
                 /             \
          Tool request          Answer
               |                   |
       Permission / execution   Turn ends
               |
        Result or error event
               |
               +----> Update context and choose again
```

This is a **teaching simplification**. It deliberately omits streaming, concurrent calls, compaction, and cancellation. The diagram explains feedback; it does not claim that these few Python steps implement native Codex.

## Run a controlled miniature loop

From the course root:

```bash
python3 scripts/course.py lab loop
python3 scripts/course.py lab loop --fail-tool
python3 scripts/course.py lab loop --max-steps 1
```

The first invocation prints JSON events labeled as teaching output, including a tool request, result, and terminal state. The second deliberately fails a tool: its error must become inspectable feedback, not a fabricated success. Its final `status: completed` means the scripted loop ended with an error-reporting answer; the tool event's `ok: false` establishes that the business read failed. The third deliberately exhausts the step budget: the result must explain the limit instead of inventing completion. Consult the output and [lab guide](labs.md) for concrete fields.

The “model” in this experiment is a deterministic script. Fixed inputs produce fixed choices, allowing us to test feedback and stopping rules. It does not call OpenAI or establish that a real model can implement the tags requirement. Its value is that discarding an error or omitting a loop budget produces a reproducible control-layer defect.

When reading the lab, locate the function choosing the next action, the branch executing the tool, and the branch enforcing termination. Keeping those responsibilities distinct makes failures easier to diagnose. For example, replacing a read exception with an empty list in the tool adapter prevents the model from distinguishing “no tasks exist” from “reading failed.”

## Observe the real CLI's public events

This section requires authenticated Codex and working network access and may consume model usage. Run this read-only task from the course root:

```bash
mkdir -p .local
codex exec --sandbox read-only --json \
  'Read examples/taskboard/taskboard.py. Explain how list filtering works. Do not edit files.' \
  > .local/read-events.jsonl
```

Progress messages can go to standard error; the `--json` standard output consists of JSON lines. Do not merge these streams into one JSON file. Check the process exit status first, then inspect the events:

```bash
python3 - <<'PY'
import json
from pathlib import Path
for line in Path('.local/read-events.jsonl').read_text().splitlines():
    event = json.loads(line)
    item = event.get('item', {})
    print(event.get('type'), item.get('type', ''), item.get('status', ''))
PY
```

The official non-interactive interface reports thread, turn, and item lifecycles. Items can represent assistant messages or command execution. Do not require the model to choose the same tool every time or rely on a fixed ordering of fields. One run may read a small file differently from another; some requests need no tools. Ask whether the necessary evidence exists, rather than whether the sequence matches a screenshot. [Official non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)

For a Taskboard change, useful evidence is: relevant implementation read → target files changed → acceptance command executed → successful acceptance exit → diff consistent with requirements. A `turn.completed` event establishes that a turn ended. The model could still miss a test or misunderstand a requirement. A successful explanatory task is not a code acceptance test.

## Read the pinned source

This course pins public CLI `rust-v0.155.1`, commit `be2951ea34f0d295ed0becf97079f92fa5f6950e`. Follow turn processing in [core/session/turn.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/turn.rs), tool dispatch in the [tools directory](https://github.com/openai/codex/tree/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools), and non-interactive presentation in the [exec directory](https://github.com/openai/codex/tree/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/exec/src).

These are entry points into the **official implementation**. Client code does not disclose the server model's internal reasoning. Interface output, public events, and process results are the observable boundary. Our Python loop reproduces only the request–execute–feedback relationship, not the complete official protocol.

## Diagnose and practice

If the event file is empty, inspect CLI standard error, authentication, and network access before blaming the JSON parser. If some events exist before failure, retain the failed run and distinguish tool errors from authentication errors. For a long-running command, inspect its input and process state to distinguish waiting for stdin, a slow test, and a stuck process.

Exercise: compare the normal lab with `--fail-tool` and identify the first divergent event. Set the budget to 1 and explain why “not completed” is the correct outcome. Your acceptance check is to give separate examples of a model decision error, a tool execution error, and a host control error rather than calling everything “unreliable AI.” If you also run the real CLI, record its version, command, exit status, and evidence file separately from the offline experiment.

Next: [Put project instructions in the right place](04-instructions.md).
