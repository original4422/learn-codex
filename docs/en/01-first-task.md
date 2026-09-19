# 01 · Your first task: add tags to Taskboard

This chapter delivers a real small change: store tags in a command-line task board and filter tasks by tag. Run a baseline, define acceptance, let Codex read, edit, and test, then inspect the diff yourself. Without model credentials, you can still run the reference implementation and acceptance checker; these paths establish different things.

## Prepare the CLI and authentication

The course needs Python 3.10+ and Git. Read-only labs, the website, and Taskboard need no third-party Python packages. The real agent path additionally needs Codex CLI, usable authentication, and network access. Record your environment first:

```bash
python3 --version
git --version
codex --version
```

Our source baseline is `rust-v0.155.1`, public commit `be2951ea34f0d295ed0becf97079f92fa5f6950e`. If the CLI is not installed, you can install the pinned package using an existing npm installation:

```bash
npm install -g @openai/codex@0.155.1
codex --version
```

Without npm, download the matching OS and CPU binary from the [pinned official release](https://github.com/openai/codex/releases/tag/rust-v0.155.1). Official standalone installers and Homebrew are also described in the [CLI installation guide](https://learn.chatgpt.com/docs/cli). Those generally follow the latest version. If you use another version, record the difference instead of treating this pinned source as a guarantee about that version.

Plain `codex` commands in this chapter use your everyday Codex home; the quickstart integration lab uses isolated `.cache/codex-home`. Their login states can differ. To reuse isolated authentication, prefix each Codex command executed from the course root with `CODEX_HOME="$PWD/.cache/codex-home"`, including the later `--cd` launch, so the home remains consistent.

Do not sign in again if valid authentication already exists. Check status, then choose an authentication method if needed:

```bash
codex login status
codex login
```

`codex login` uses the ChatGPT browser sign-in flow. If you choose API key authentication, provide `OPENAI_API_KEY` through your own secure environment, then run:

```bash
printenv OPENAI_API_KEY | codex login --with-api-key
```

Do not paste a key literal into course files or shell history. ChatGPT and API key authentication have different billing and access paths; actual availability depends on your account and workspace. API key usage is not the same as included subscription usage. [Official authentication guide](https://learn.chatgpt.com/docs/auth)

Version and login status are local evidence. They do not establish working network access, model calls, or available account usage. The first real task checks those; a failure still leaves the offline path available.

## Run the reference implementation first

Run all following commands from the course root. With a new store, the first task should receive `id: 1`:

```bash
python3 examples/taskboard/taskboard.py --store .local/first-task.json add 'Learn the workflow' --tag study
python3 examples/taskboard/taskboard.py --store .local/first-task.json list --tag study
python3 examples/taskboard/taskboard.py --store .local/first-task.json done 1
```

The first prints a JSON object containing `id`, `title`, `done: false`, and `tags: ["study"]`. The second prints an array containing that task; the third changes it to `done: true`. Repeated runs preserve previous tasks, so IDs can increase. Use another fresh filename instead of deleting your data just to match the printed example.

This completed version demonstrates the target behavior. We will edit a separate practice copy instead of asking a model to reimplement an existing feature.

## Create a recoverable practice baseline

```bash
python3 examples/taskboard/prepare_exercise.py .local/taskboard-practice
git -C .local/taskboard-practice init
git -C .local/taskboard-practice add taskboard.py AGENTS.md
git -C .local/taskboard-practice -c user.name='Course Learner' -c user.email='learner@example.invalid' commit -m 'Start Taskboard tag exercise'
python3 .local/taskboard-practice/taskboard.py --help
```

`prepare_exercise.py` copies the working starter as `taskboard.py`. It supports adding, listing, completing, and status filtering, but no tags. The commit records a local practice baseline. Command-specific author settings do not change your global Git configuration.

Run acceptance before editing to establish that it detects the missing feature:

```bash
python3 examples/taskboard/acceptance.py --script .local/taskboard-practice/taskboard.py
```

A nonzero exit is expected here, caused by missing `--tag` support and the `tags` field. Missing Python, a missing file, or a syntax error is an environment problem to resolve first, not the intended feature gap. Check that the completed implementation satisfies the same requirements:

```bash
python3 examples/taskboard/acceptance.py --script examples/taskboard/taskboard.py
```

This gives us a useful checker: it accepts reference behavior and rejects a known defect. A test we have only ever seen pass provides weaker evidence that it detects errors.

## Give Codex the acceptance criteria

Launch the CLI in the practice directory:

```bash
codex --cd .local/taskboard-practice --sandbox workspace-write --ask-for-approval on-request
```

Enter this task inside the session:

```text
Add tags to the current Taskboard. Acceptance criteria are already defined.
Read AGENTS.md and taskboard.py first, identify the necessary changes,
then implement, test, and review the diff.

1. add accepts repeated --tag values; trim, lowercase, deduplicate, and sort.
2. Each tag has 1–40 characters, with at most 20 tags. Reject invalid values
   without corrupting existing data.
3. list --tag uses normalized exact matching and composes with
   --status open/done/all.
4. Legacy JSON tasks without tags remain readable and have no tags.
5. Preserve existing IDs, add/list/done behavior, and the JSON stdout interface.
6. Use only the Python standard library. Do not modify the course reference
   implementation or acceptance checker.

Run acceptance from this practice directory:
python3 ../../examples/taskboard/acceptance.py --script taskboard.py

Report what changed, the checks actually executed and their exit statuses,
and behavior that remains unverified.
```

“Tags” includes a data format, input rules, and composable filtering. Defining all three gives Codex a concrete boundary. “Add useful tags” leaves case handling, duplicates, and legacy compatibility unspecified.

Defining acceptance before editing does not require repeated permission for an already authorized small change. If a real permission request appears, inspect its exact command and scope. [Chapter six](06-safety.md) explains that mechanism.

## Collect completion evidence yourself

After leaving or pausing the CLI, run these from the course root:

```bash
python3 examples/taskboard/acceptance.py --script .local/taskboard-practice/taskboard.py
git -C .local/taskboard-practice diff --check
git -C .local/taskboard-practice diff -- taskboard.py
git -C .local/taskboard-practice status --short
```

Acceptance establishes the covered behaviors. `diff --check` catches patch whitespace issues. The regular diff supports reasoning about the change, and status reveals untracked files. Read the implementation too: rule out hardcoded acceptance inputs, deleted failure handling, and unrelated edits.

Deliver the changed `taskboard.py`, an explainable diff, acceptance output, and a brief retrospective. The model saying “done” is insufficient. If you ran only the reference and checker, record “local application checks passed; real model editing not verified.”

## Mechanism and failure paths

In the **official implementation**, [TUI arguments](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/tui/src/cli.rs) carry launch options into the interactive client, while the [login crate](https://github.com/openai/codex/tree/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/login/src) supplies authentication functionality. Taskboard and its checker are course applications, not built-in Codex capabilities.

If `codex` is absent from PATH, resolve installation paths instead of accumulating versions. If login works but a call fails, retain the error type and exit status and inspect account, service, and network conditions. If the model edits the reference instead of the practice copy, inspect `--cd` and the diff; do not accept the scope error. When acceptance fails, ask the agent to explain the first failing input, expected value, and actual result before fixing it.

Exercise: create tasks tagged `study` and `studying` in the successful version and confirm that selecting the former excludes the latter. Explain why this is stronger than checking whether output contains “study.” Next: [Build a complete development workflow](02-workflow.md).
