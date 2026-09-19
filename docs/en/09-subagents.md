# 09 · Subagents: delegate work, retain verification

## Learning goals

Delegate two independent Taskboard reviews in parallel with explicit inputs, scope, and output contracts. Understand why a context fork does not isolate the filesystem. Verify every result before aggregation. Your artifact is a combined review traceable to code or data.

## Start with use: delegate independent questions

In an interactive Codex session in the Taskboard repository, send this task. It requests real model work and needs working authentication and a model; the offline alternative follows below.

```text
Use two subagents to review Taskboard in parallel. Both are read-only.
A: inspect JSON loading, validation, and save-failure paths; report at most
three risks supported by evidence.
B: inspect tag normalization and filtering; list existing tests and missing
boundary cases.
Each returns: file/function, reproducing input, observation versus inference,
and a suggested verification command.
Main agent: independently verify results, drop unsupported claims, merge
repeated findings, and run necessary tests.
A subagent saying "passed" is not evidence that tests passed.
```

Use `/agent` to inspect or switch child tasks. Check the main task for actual delegation, results, and aggregation. Current documentation describes parallel subagents with their own model and tool usage; the current trace establishes whether delegation occurred. [Official usage guide](https://learn.chatgpt.com/docs/agent-configuration/subagents)

Do not give both workers “modify the same save function.” Read-only exploration is easy to parallelize. For dependent edits, agree on interfaces, assign nonoverlapping files, and give one owner responsibility for integration checks.

## Observe: the handoff contract matters more than a role name

| Item | Useful handoff | Fragile handoff |
| --- | --- | --- |
| Input | Current commit, files, and question | “Look at the project” |
| Scope | Read-only; save failures only | “Optimize everything” |
| Output | Function, counterexample, evidence, command | “Looks fine” |
| Completion | Two failure paths checked | “Finish quickly” |
| Aggregation | Verify; retain unknowns as unknown | Vote on correctness |

A child summary compresses intermediate work. Separate “test executed” from “test recommended” so the parent cannot mistake advice for evidence. A file reference alone is insufficient: include the trigger and expected behavior.

## Mechanism and source: context boundaries and shared files

**Official implementation:** the pinned release contains multiple multi-agent implementation paths. This reading focuses on V2. [fork_mode in spawn.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/multi_agents_v2/spawn.rs#L291) accepts `fork_turns` as `none`, `all`, or a positive integer string, defaulting to `all`. “A child always starts without history” is therefore incorrect; inheritance depends on the interface and arguments.

[Session multi-agent instructions](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/multi_agents.rs#L60) describe the shared directory. Separate context does not automatically create a Git worktree or independent file copies. Independent edits require explicit isolated checkouts or nonoverlapping ownership.

Repeat essential constraints in each handoff: a partial history fork may miss an early decision, while a full fork may carry irrelevant noise. No context mode replaces a clear objective and acceptance contract.

## Runnable experiment: two workers, one validator

```sh
python3 scripts/course.py lab subagents
```

**Teaching simplification:** [mechanisms.py](../../src/codex_lab/mechanisms.py) uses two Python `ThreadPoolExecutor` workers with copied data. They are not Codex subagents, make no model calls, and do not simulate reasoning. The lab isolates dispatch → independent results → validation → aggregation.

Expect JSON with `verified_against_snapshot: true`. The `open-work` report lists unfinished task IDs `[2, 3]`; `coverage` lists the `test`-tagged ID `[3]`. Aggregation sorts scopes deterministically instead of relying on completion order. `aggregate_reviews()` checks schema, unique scopes, known IDs, and agreement with the source snapshot predicates.

Now make a report cite a nonexistent task:

```sh
PYTHONPATH=src python3 - <<'PY'
from codex_lab.mechanisms import SAMPLE_TASKS, audit_worker, aggregate_reviews
reports = [audit_worker(scope, SAMPLE_TASKS) for scope in ("open-work", "coverage")]
reports[0]["task_ids"].append(999)
try:
    aggregate_reviews(reports, SAMPLE_TASKS)
except ValueError as error:
    print(error)
else:
    raise SystemExit("invalid evidence was accepted")
PY
```

Expect `review cites an unknown task`. Next change `coverage` to the existing but incorrect ID `[1]`; expect `review evidence does not match the source snapshot`. Checking that a reference exists differs from checking that the conclusion is true.

## Verify real delegated results

Real code review is less mechanical than these predicates, but the structure transfers. Ask for an executable minimal reproduction or test. The parent reads the relevant implementation, runs verification, and records the result. If two reports disagree, compare inputs, versions, and commands, then reproduce in one working tree; do not take a majority vote.

Parallelism saves time only when enough independent work exists. Two agents inspecting a ten-line function may be slower than one. More agents cannot eliminate a shared dependency on an undecided interface. This lab claims no invented speedup ratio.

## Troubleshooting

| Symptom | First action |
| --- | --- |
| Duplicate child work | Narrow questions and make scopes disjoint |
| Lost child result | Standardize output and check every required scope arrived |
| Edits overwrite one another | Stop overlapping writes, assign files or isolated checkouts, then inspect differences |
| “Tests passed” without evidence | Mark unverified and run the relevant test |
| No subagent activity | Check version, features, and current capabilities; retain a single-agent route |

## Exercise and next step

Remove a scope, then duplicate one, and verify both reports are rejected. Design a third real review task: “Do CLI errors give actionable recovery advice?” Explain how it is independent of save correctness and who will aggregate it.

Next, connect these verification contracts to scripts in [10 · Automation and interfaces](10-automation.md).
