# 05 · Skills: turn repeated acceptance work into an executable workflow

This chapter produces a real run of the `taskboard-check` skill check. You will distinguish discovering a skill, loading its instructions, executing its script, and accepting the task. We use a project-local teaching skill without installing or changing personal skills.

## When to extract a skill

The first chapters repeatedly check Taskboard's JSON output, tag filtering, and test evidence. Re-explaining the workflow invites omissions, especially on failure paths. A narrowly scoped skill lets its description match the task, its body organize the steps, and its script perform reproducible mechanical checks.

Use `AGENTS.md` for continuing project agreements. Use a skill for a workflow invoked by a particular class of task. A skill is not a new model or a background service. Its scripts run through ordinary execution tools under current permissions. An instruction to run tests is not evidence that tests ran.

## Inspect the provided example

```text
examples/taskboard/
  taskboard.py
  .agents/skills/taskboard-check/
    SKILL.md
    scripts/check.py
```

The [skill source](../../examples/taskboard/.agents/skills/taskboard-check/SKILL.md) includes frontmatter `name` and `description`. Its name is `taskboard-check`; its description limits it to this course's CLI acceptance. The body organizes reading, execution, result inspection, and reporting limits. It does not try to handle every Python question.

The **official mechanism** uses progressive loading: metadata such as name and description comes first; the full instructions are read when selected. You can explicitly mention `$taskboard-check`, or the agent can match a task to its description. Common repository discovery covers `.agents/skills` along the path from the working directory to the repository root. Starting at the course root therefore does not imply discovery of a skill in a child directory. We start from Taskboard here. [Official skills guide](https://learn.chatgpt.com/docs/build-skills)

Description quality affects selection after discovery. “Helps with all development work” claims unrelated tasks; an overly narrow description without clear triggers is easy to miss. Ours says to verify Taskboard after changes to add, list, tags, or completion, which gives a reader a concrete applicability test.

## Verify the script before involving a model

From the course root:

```bash
python3 examples/taskboard/.agents/skills/taskboard-check/scripts/check.py
```

Expect exit code 0, JSON `status: passed`, and four checks:

| Check | Counterexample it targets |
| --- | --- |
| `normalized_add` | Whitespace and duplicate input tags must normalize to one `study` |
| `exact_tag_filter` | With both `study` and `studying`, only the former should match |
| `completion_and_status` | Completing a task preserves tags and removes it from open results |
| `rejection_preserves_store` | An empty title is rejected without changing existing file bytes |

The script creates a temporary store, calls the actual `taskboard.py` through subprocesses, and cleans up afterward. It does not mock the CLI or call a model. It establishes these concrete local application behaviors. It does not establish real Codex skill selection or replace the full regression suite.

The script resolves its default target from its own location, so changing the shell directory does not silently test a different same-named program. To check a practice copy, provide an explicit target:

```bash
python3 examples/taskboard/.agents/skills/taskboard-check/scripts/check.py \
  --target .local/taskboard-practice/taskboard.py
```

The starter without tag support should fail. A completed implementation should pass. Preserve the failure exit, message, and target path; do not weaken assertions to make a demonstration succeed.

## Have Codex perform the full workflow

Launch from the course root:

```bash
codex --cd examples/taskboard --sandbox workspace-write --ask-for-approval on-request
```

Enter the following inside Codex. The `$` is a skill mention in session input, not a shell variable:

```text
Use $taskboard-check to verify the current Taskboard.
Identify the skill's source path, run its script, and report the exact checks
and uncovered areas. Do not edit the implementation. If it fails,
preserve the failed evidence and explain the cause.
```

Use `/skills` first if you want to inspect the available list. Look for the agent reading the body and executing the script, not merely repeating its name. Compare the actual command and exit status in tool records with the script output. A menu entry proves discovery only; a final “checks completed” claim still needs execution evidence. [Official explicit invocation guidance](https://learn.chatgpt.com/docs/build-skills)

A comparison task for implicit matching is “Check whether Taskboard's tags and completion state meet the project agreements.” It may activate the skill, but selection also depends on other instructions, installed skills, and model choices. Record observations without turning a single run into a universal rule. Prefer explicit invocation when you want a stable experimental entry point.

## Source reading and troubleshooting

The pinned [skill discoverer](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/ext/skills/src/loader/discovery.rs) scans files. The [skill parsing crate](https://github.com/openai/codex/tree/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/skills/src) handles metadata. [render.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/ext/skills/src/render.rs) presents available skills to the model. These entry points distinguish “not found,” “invalid format,” and “found but not selected.” They are the **official implementation**; the course supplies an application-level skill example.

If the skill is absent, check the launch directory, path, and frontmatter, then start a fresh session. If it is listed but its script cannot be found, inspect relative-path resolution. If the script fails, run it directly to distinguish a requirement failure, unavailable Python, and execution restrictions. Editing the description does not repair application defects.

Exercise: deliberately change tag matching to substring matching in a practice copy, then run the skill script. When `study` incorrectly selects `studying`, it should fail. Restore the implementation and rerun. Explain which assertion detects the defect and why “all output is valid JSON” would miss this semantic error.

Next: [Approval and execution isolation](06-safety.md).
