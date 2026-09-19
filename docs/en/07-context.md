# 07 · Sessions, context, and compaction

## Learning goals

Create a recoverable Taskboard handoff; distinguish the session log, the model's current context, and files on disk; run an explainable compaction experiment and compare it with the pinned Codex implementation. Your artifact is a handoff containing constraints, decisions, unresolved work, and verification commands.

## Start with use: resume the same task

Start `codex` in the repository root and ask: “Read the Taskboard save path. Analyze how an atomic replacement failure preserves the original file. Record the conclusion and next test; do not edit code.” After one completed turn, save the session ID, exit, and resume:

```sh
codex --version
codex resume
# Replace the ID below with the actual recorded session ID:
codex resume SESSION_ID
```

`codex resume --last` is convenient when a directory has one clear task. With concurrent tasks, an explicit ID is easier to audit. The interactive picker filters by working directory; `--all` broadens it. Non-interactive runs use `codex exec resume`. These options were checked against local `0.155.1` help output. [Pinned exec resume arguments](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/exec/src/cli.rs#L151)

After resuming, ask: “Check the previous conclusion against current files before continuing.” A remembered test result is not a fact about the current working tree. Another developer may have changed `save()` since the prior turn.

## Observe three different states

| State | Contents | Reliable check |
| --- | --- | --- |
| Persisted session | Historical events and recovery information | Save the session ID and use resume |
| Current model context | History, summaries, instructions, and tool results visible for this request | Inspect visible context/compaction activity and request file verification |
| Working tree | Current code, data, and Git differences | `git diff`, file reads, and fresh tests |

Resuming is not Git rollback; compaction does not delete project files. The model may receive a summary rather than the full log, so a handoff needs traceable files and commands. A useful Taskboard handoff could be:

```text
Goal: verify a failed save preserves existing data.
Constraints: change only Taskboard and its tests; never print credentials.
Decision: tags use exact normalized matching.
Evidence: tests/test_taskboard.py; fill in results after rerunning tests.
Open: simulate os.replace failure; compare file bytes before and after.
Next: run the save-failure test and inspect git diff.
```

Keep constraints separate from verified facts. “Needs rerun” must not become “passed” when the handoff is summarized.

## Mechanism and source: more than dropping old messages

**Official implementation:** [ContextManager](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/context_manager/history.rs#L72) distinguishes the model window from retained context state. [Recovery reconstruction](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/rollout_reconstruction.rs#L12) handles compaction checkpoints and subsequent records. Recovery therefore is not simply concatenating every chat message.

[CompactTask](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tasks/compact.rs#L29) selects a path using features and provider capabilities. One path [orchestrates summarization locally](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/compact.rs#L244) and replaces history; another uses [remote compaction](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/compact_remote_v2.rs#L223). “Local” describes client orchestration, not model-free summarization.

The course promises no fixed context size, automatic threshold, or identical summary text. These depend on version, model, configuration, and provider. Check your client's help for manual compaction controls. We do not fill a model context just to manufacture usage.

## Runnable experiment: preserve important facts

Run from the repository root:

```sh
python3 scripts/course.py lab context
```

**Teaching simplification:** `compact_context()` in `src/codex_lab/mechanisms.py` extracts content within a character budget. It preserves `constraint`, `decision`, and `open` entries, then keeps recent ordinary messages that fit. It calls no model, counts no actual tokens, and does not implement Codex's complete retained state.

Expect JSON with `after_chars` below `before_chars`, `dropped_messages` equal to `1`, and `memory` still containing “Never overwrite invalid JSON,” “Tags use exact normalized matching,” and the pending replace-failure test. The long success log disappears; the next instruction to read tests remains.

Now check the failure path:

```sh
PYTHONPATH=src python3 - <<'PY'
from codex_lab.mechanisms import compact_context
try:
    compact_context([{"kind": "constraint", "text": "must survive"}], max_chars=3)
except ValueError as error:
    print(error)
else:
    raise SystemExit("expected a budget error")
PY
```

Expect `protected facts exceed budget`. The program fails explicitly instead of silently discarding a constraint. This is our teaching contract, not a claim about every official compaction path.

## Troubleshooting and verification

| Symptom | First check |
| --- | --- |
| Empty resume picker | Working directory, account, Codex home, and whether the session used `--ephemeral` |
| Stale code description after resume | Read current files and Git differences; rerun tests |
| Shorter lab summary loses important work | Was the entry incorrectly labeled `message`? Is the budget reasonable? |
| Model compaction request fails | Record the actual error and provider settings; an offline pass does not prove recovery |

You should now explain why recoverability does not mean every original log line is sent to the model again. Files and tests establish file facts. See [acceptance](acceptance.md) for the execution status of actual resume and model-driven compaction.

## Exercise and next step

Add a “read-only review, do not edit code” constraint and five lengthy tool logs. Verify the constraint survives and the budget holds. Then exceed the budget with protected entries alone. Explain why explicitly narrowing scope is more auditable than silently trimming constraints.

Next, give the task a bounded tool in [08 · MCP](08-mcp.md).
