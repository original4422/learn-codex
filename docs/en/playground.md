# Mechanism playground

The interactions below turn control flow into events you can inspect one step at a time. They run in the browser without networking, shell execution or real model calls. Editable source is in [app.js](../../site/assets/app.js); command-line counterparts are in [mechanisms.py](../../src/codex_lab/mechanisms.py).

## Observe loop termination

Choose success, tool failure or budget exhaustion, then click “Next step.” Notice that deciding to execute a tool and the tool actually succeeding are different moments. An error is an observation too; it must not be disguised as an empty result.

After the interaction, answer: at which step did external evidence become available? When can you conclude that the task is complete? If the budget runs out first, should you provide a complete answer, partial findings, or an explicit incomplete status?

```sh
python3 scripts/course.py lab loop
python3 scripts/course.py lab loop --fail-tool
python3 scripts/course.py lab loop --max-tool-calls 0
```

The browser demonstrates state changes. The Python version emits events and has tests for budgets and failures. Both are **teaching simplifications**. See [chapter 3](03-agent-loop.md) and [chapter 10](10-automation.md) for observing real Codex events.

## Separate approval from isolation

The second interaction independently toggles whether the target is inside an allowed directory and whether approval has been granted. Of the four combinations, the simplified policy allows execution only when both checks pass. Approval does not make an out-of-bounds path writable; an allowed path does not replace required approval.

```sh
python3 scripts/course.py lab policy --action write --isolation read-only --approved
python3 scripts/course.py lab policy --action write --isolation workspace-write
python3 scripts/course.py lab policy --action write --isolation workspace-write --approved
```

This is only a decision function. It creates no OS isolation. Real systems may also impose platform restrictions, network policies and organizational settings. The experiment helps you avoid mistaking one policy check for a complete security boundary. [Chapter 6](06-safety.md) maps this distinction to the official implementation.

## Predict, then verify

Before clicking, write your expected outcome for each permission combination. Toggle each combination and explain any difference between prediction and observation. Apply your explanation to Taskboard: what path capability does writing the task store require, and what does reviewing a diff require?

If the buttons do not work, check that JavaScript is enabled. The Python commands above provide an equivalent runnable entry point. Course text remains readable without JavaScript.
