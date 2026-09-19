# 11 · Desktop: the same development loop in a visual workspace

## Learning goals

Map requirements, files, tools, tests, differences, and recovery from CLI to desktop. Complete the same Taskboard acceptance contract without memorizing button positions. Desktop is an additional route; code and checks still come from the local repository.

## Start with use: prepare a clean exercise copy

Run in the course root:

```sh
python3 examples/taskboard/prepare_exercise.py .local/taskboard-desktop
python3 examples/taskboard/acceptance.py --script .local/taskboard-desktop/taskboard.py
```

The preparation script refuses to overwrite a directory. If you already ran it, choose a new name and update subsequent paths. The starter supports add/list/done and status filtering but lacks tags. Expect two basic checks to pass and two tag checks to fail. Those failures represent the feature contract, not installation problems.

Select or open `learn-codex` in the desktop app, create a local task, and verify its working directory points to this course copy. Current official documentation uses “ChatGPT desktop app”; labels may differ by host version. Locate operations by their result. [Official desktop entry point](https://learn.chatgpt.com/docs/app)

Send:

```text
Modify only .local/taskboard-desktop/taskboard.py and necessary tests beside it.
Add repeated --tag arguments and full-tag filtering to Taskboard.
Trim whitespace, lowercase and deduplicate tags; legacy data without tags
must behave as an empty tag list.
Read the program and examples/taskboard/acceptance.py, explain the plan,
then implement it.
Run: python3 examples/taskboard/acceptance.py --script .local/taskboard-desktop/taskboard.py
Inspect the changes and report verification. Do not push, deploy, or publish.
```

This is a ready-to-use desktop procedure. The project does not count the written procedure as an executed desktop model task. Record your own client version, working directory, and results when you run it.

## Observe: where each client shows evidence

| Step | CLI | Desktop object to find |
| --- | --- | --- |
| Choose scope | `cd`, `codex -C` | Project directory and execution environment |
| State requirements | Prompt or prompt file | Message, attachments, referenced files |
| Observe execution | Terminal tool output, JSONL | Tool records, terminal, task activity |
| Read files | Editor, `cat`, `rg` | File preview or editor panel |
| Inspect differences | `git diff` | Diff panel and comparison base |
| Verify | Acceptance command and exit code | The same command's output and status |
| Resume | Resume with a session ID | Reopen the task and recheck current files |

Do not stop at the assistant's “done.” Find the actual command, exit status, and current file. The practice copy lives in `.local/`, ignored by the course repository, so its edits will not automatically appear in root Git diff. The next section gives a suitable comparison.

## Make directories and comparison bases explicit

“Local” generally works in the selected directory; a worktree is another Git working tree. Check the path before starting and validate in the same path afterward. If the user tests the original directory while the agent edits a worktree, they are testing different code. [Official worktree workflow](https://learn.chatgpt.com/docs/environments/git-worktrees)

Compare your exercise with a freshly generated baseline:

```sh
python3 examples/taskboard/prepare_exercise.py .local/taskboard-desktop-baseline
git diff --no-index -- .local/taskboard-desktop-baseline/taskboard.py .local/taskboard-desktop/taskboard.py
```

`git diff --no-index` exits 1 when differences exist; this is not a failed application test. Baseline creation also refuses overwrite, so use new names for repeated practice. The completed reference is `examples/taskboard/taskboard.py`, but review against requirements and tests before reading it; copying the reference is not your implementation exercise.

If using an isolated worktree, generate its `.local` copy there. Ignored files are not automatically copied into a new worktree. Course files, code, data, and task history have different lifecycles; do not assume they always move together.

## Mechanism and source: the public service boundary

**Official implementation:** public App Server supports initialization, threads, turns, and events; its [initialization handler](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/app-server/src/request_processors/initialize_processor.rs#L49) is a source entry point. This does not reveal which private method every desktop button invokes, establish that all desktop components are open source, or prove identical features across clients. See the official [component scope](https://learn.chatgpt.com/docs/open-source).

**Teaching correspondence:** this diagram maps workflows, not private desktop architecture.

```text
One requirements and acceptance contract
        │
        ├── CLI: prompt → tool output → files/tests/diff
        │
        └── Desktop: task message → activity → files/tests/diff panels
                                                 │
                                         Same Taskboard acceptance
```

Tool permissions do not disappear in a visual interface. Inspect the specific command and scope in an approval request. The distinction between approvals and isolation from [lesson 06](06-safety.md) still applies. This course does not require unrestricted execution.

## Runnable checks and expected results

After the desktop task, run in its actual working directory:

```sh
python3 examples/taskboard/acceptance.py --script .local/taskboard-desktop/taskboard.py
python3 scripts/course.py lab app-server
```

The first command should pass all four acceptance checks and verifies your code. The second should initialize real App Server and read its loaded-thread list; it verifies a public protocol. These checks are independent. The latter cannot replace the former or prove that a desktop model task ran.

Keep six items in your desktop acceptance note: client version, actual working directory, initial failures, final passing output, code differences, and remaining limits. If the model reports completion but the file is unchanged, inspect activity for a blocker or directory mismatch.

## Troubleshooting

| Symptom | Check and action |
| --- | --- |
| Task says fixed, terminal sees old code | Compare local/worktree paths and enter the actual edited directory |
| Git diff omits practice changes | `.local/` is ignored; use `--no-index` with an explicit baseline |
| Preview and terminal disagree | Refresh preview and compare absolute paths; inspect files on disk |
| Execution fails after approval | Check the failed command, OS boundary, and dependencies; approval is not a success guarantee |
| A button is missing | Consult current official guidance and retain the CLI verification route |

## Exercise and course wrap-up

Ask the desktop task for a read-only review of the final implementation, requiring a real counterexample or a clear statement that none was found. Run its suggested verification yourself. Write a handoff of at most ten lines, separating constraints, decisions, evidence, and remaining work as in [lesson 07](07-context.md).

You can now follow one contract across clients: requirements → reading → edits → verification → diff → retrospective. Pick another practice activity in [labs](labs.md); see [acceptance](acceptance.md) for the actual local v1 status.
