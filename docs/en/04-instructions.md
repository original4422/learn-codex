# 04 · AGENTS.md: put project instructions in the right place

After this chapter, you can predict instruction discovery order and write concise, executable working agreements for Taskboard. `AGENTS.md` holds enduring requirements such as the test entry point and data-format constraints. Keep a particular task's acceptance criteria in that task.

## Begin with the agreements we need

Taskboard uses the Python standard library and stores and prints JSON. An agent adding tags could introduce an ORM or print ordinary logs to stdout. The demonstration might still look fine while breaking reproducibility or the scripting interface. Concrete agreements are easier to check than “write high-quality code”:

```markdown
# Taskboard working agreements

- Keep runtime dependencies in the Python standard library.
- Preserve JSON output on stdout; send diagnostics to stderr.
- Preserve existing task IDs when adding fields.
- Run the documented acceptance check after changing CLI behavior.
- Report the command, exit status, and any unverified assumptions.
```

These are **project instructions**, not operating-system permissions. “Do not use the network” can guide the agent but cannot replace network isolation. Do not put API keys, passwords, or production data in an instruction file.

## Discovery depends on the directory path

**Official behavior:** startup chooses global guidance from Codex home, then walks from the project root to the current working directory. Each directory prefers `AGENTS.override.md`, then `AGENTS.md`, then configured fallback filenames. At most one file per directory enters the chain, ordered from root to working directory. The default project-document budget is 32 KiB. Closer directories provide more specific guidance. This is not a recursive load of every matching file in the repository. [Official AGENTS.md guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

```text
repo/AGENTS.md                 General guidance
repo/app/AGENTS.md             Replaced when a sibling override is selected
repo/app/AGENTS.override.md    App-specific guidance
repo/other/AGENTS.md           Outside the path when starting in app
```

Starting in `repo/app` includes the root and app directories. Starting in `repo` does not include app in the initial path. The agent may later read guidance when editing a subdirectory, but “might read later” does not mean “automatically injected at startup.” Choose an explicit working directory and ask it to inspect guidance for target files before making changes.

An override replaces candidates in the same directory; it does not erase every ancestor's instructions. A subdirectory saying “use another test command here” does not cancel a root-level data compatibility requirement. Instructions are natural-language context, not a type system that automatically resolves each sentence. For a real conflict, identify the sources and scopes instead of silently selecting a convenient interpretation.

## Check your prediction with fixtures

From the course root:

```bash
python3 scripts/course.py lab instructions
python3 scripts/course.py lab instructions --max-bytes 80
```

The lab uses `examples/instructions` fixtures, including a fixture global directory. It does not read or modify your personal settings. The default output lists selected files and their respective text in order; the small-budget run demonstrates information lost to truncation. Write your predicted path order first, then compare it with the JSON. Check that an override excludes the ordinary file at that level and that sibling branches are absent.

Change the scan's starting point with:

```bash
python3 scripts/course.py lab instructions \
  --root examples/instructions/repo \
  --cwd examples/instructions/repo \
  --home examples/instructions/home
```

Compared with the default app directory, starting at the root should omit app-level files. This Python implementation is a **teaching simplification**. You explicitly supply root, home, and byte budget. It does not reproduce all of Codex's configuration layering, worktree detection, platform path behavior, or fallback options. Its default 2048-byte budget is not the official default.

## Cross-check a real Codex session

From the course root, use a real read-only instance to explain the applicable project agreements:

```bash
codex --cd examples/taskboard --sandbox read-only --ask-for-approval on-request \
  'List the instruction files relevant to this working directory. Read and summarize their concrete test and data-format requirements. Do not change files.'
```

This invocation uses your actual personal configuration. Unlike the fixtures, its result may include personal guidance. Record paths and relevant project rules without publishing your entire configuration or session. A model's verbal summary is an observation, not proof of every injected byte. Cross-check files, the working directory, and local logs when necessary. [Official verification and troubleshooting guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

In the pinned [agents_md.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/agents_md.rs), find candidate ordering and directory traversal, then inspect byte limits and tests. Use a question such as “why was the sibling file excluded?” to bound source reading instead of reading all of core. This is the **official implementation**; fixture output is **observed lab behavior**.

One pinned-version edge case deserves an explicit check: project discovery chooses the first existing regular file before reading its contents. An empty `AGENTS.override.md` therefore shadows its sibling `AGENTS.md`; the empty content is then omitted. The global provider instead continues to the first non-empty file. Project trust is another precondition: this version skips project guidance for a project marked untrusted. Resolve discrepancies using the pinned source and actual trust configuration, not a general description alone.

## Diagnose and practice

If guidance appears missing, check `pwd`, the repository root, and launch arguments first. Then inspect overrides, empty files, and document limits. Start a new run after editing guidance so an older session's context is not mistaken for fresh configuration. If the model read but ignored a requirement, that is an execution-quality problem. Catch it with acceptance checks; adding many synonymous rules is unlikely to help.

Exercise: in a disposable practice copy, add an instruction file in a directory outside the current path and verify that discovery is unchanged. Move the working directory into that directory, predict the new chain, and check it. Finally, write one command-checkable Taskboard agreement, such as “invalid input must not overwrite existing JSON.” Passing this exercise requires a discovery order, an explanation of scope, and a verification command, not merely creating a file named `AGENTS.md`.

Next: [Package repeated work as a skill](05-skills.md).
