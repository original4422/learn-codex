# 06 · Approval and execution isolation are different controls

This chapter teaches you to interpret a denial: was the request not authorized, was the process blocked by isolation, or did the task itself fail? Compare controls in a side-effect-free policy experiment, then inspect the corresponding real CLI configuration.

## Why a small Taskboard change needs a boundary

Adding tags to `taskboard.py` normally needs project reads, writes inside the working directory, and Python tests. It does not need a production database, email credentials, or unrelated files. Permissions should match this actual work. A shell command can still start arbitrary programs even for a small task. “Only change one file” is an instruction, not an execution boundary.

An **approval policy** determines which actions need authorization; the reviewer can be the user or a configured automatic review service. An **OS sandbox** constrains the resources an executing process can access. **Git** records and displays changes to help recovery, but does not block reading files or sending network requests. These controls answer “is it authorized?”, “can it execute?”, and “what changed?” respectively.

```text
Tool request
     |
     v
Approval required? ---- required but absent ---> deny / request approval
     |
     v
Selected execution permissions and OS sandbox
     |
     +---- resource access forbidden ----------> failure / appropriate escalation
     |
     v
Command runs ----> exit code, output, changed files ----> acceptance
```

This diagram is a **teaching simplification**. Real behavior also involves execution rules, network policies, cached approvals, tool-specific handling, and managed restrictions. It is not a promise about the full order of every tool call.

## Compare four harmless cases

From the course root:

```bash
python3 scripts/course.py lab policy --approval ask --isolation read-only --action read
python3 scripts/course.py lab policy --approval never --isolation read-only --action write
python3 scripts/course.py lab policy --approval ask --isolation read-only --action write --approved
python3 scripts/course.py lab policy --approval ask --isolation workspace-write --action write --approved
```

Read the approval decision separately from permission to execute. A read can pass in a read-only environment. A write does not acquire permission merely because approval is set to `never`. In this lab, `--approved` alone does not alter isolation, so an approved write can still be rejected by read-only isolation. A workspace write can satisfy both controls.

The lab never performs the described file or network action. Its `ask` value is a teaching parameter, not an actual Codex CLI enum. The lab deliberately requires its approval condition for every write; ordinary in-workspace writes in real Codex may need no additional approval. It also does not implement real escalation: in a real system an approval can authorize the host to select broader execution permissions for a particular action under the applicable policy. Holding isolation fixed lets us distinguish authorizing a request from actually changing execution permissions.

Also run:

```bash
python3 scripts/course.py lab policy --approval ask --isolation workspace-write --action network --approved
```

Approval is satisfied here but `isolation_allows` remains false: a writable workspace does not imply network access. The lab assumes networking is disabled; actual configuration and organization policy may differ. A Python branch result does not establish that you tested macOS, Linux, or Windows OS isolation.

## Express the choices in the real CLI

These explicit launch commands apply to pinned version `0.155.1`:

```bash
codex --sandbox read-only --ask-for-approval on-request
codex --sandbox workspace-write --ask-for-approval on-request
codex --sandbox read-only --ask-for-approval never
```

The first supports investigation with approval requests when needed. The second supports edits within writable scope. The third retains read-only boundaries without asking interactively. `never` means no approval requests; it does not mean every action is allowed. Check the parameter values locally with `codex --help`.

Inside a session, use `/status` and `/permissions` to inspect effective configuration and available permission choices. The effective configuration governs this run; a command printed in a book cannot override organization policy. Nor does `workspace-write` make every nested path freely writable: the pinned version gives additional protection to locations including `.git` and existing `.agents` and `.codex` directories. [Official approvals and security guide](https://learn.chatgpt.com/docs/agent-approvals-security)

Use this bounded task:

```text
Read the Taskboard implementation and explain where tag filtering starts.
Do not change files. If a read fails, report the exact path and error;
do not change permissions to hide the failure.
```

A successful read-only task establishes that this request completed within the current boundary. It does not verify write blocking or network blocking. To inspect the actual OS sandbox directly, first read your local `codex sandbox --help`, then use harmless read/write probes in a disposable directory. Command forms differ across platforms and versions; this course does not present a guessed cross-platform command as a guarantee.

## Read how the official implementation handles denial

Pinned [tools/orchestrator.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/orchestrator.rs) centralizes approvals, sandbox selection, and retries. Follow it into [sandboxing](https://github.com/openai/codex/tree/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/sandboxing/src) for platform execution policies. The macOS [seatbelt.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/sandboxing/src/seatbelt.rs) is one concrete entry point.

The source models authorization and execution attempts separately, which motivates our lab's separation. The course does not recreate the complete security system or offer a homemade sandbox based on shell prefixes. A command starting with `python` can still have side effects; its arguments, script, working directory, and environment matter.

## Diagnose and preserve evidence

| Observation | Check first | Reasonable next action |
| --- | --- | --- |
| Missing or rejected approval | The request, scope, and denial reason | Narrow the action or explain the specific permission needed |
| `Permission denied` | Path, effective writable roots, OS error | Use an allowed location and retain the original error |
| Nonzero test exit | stderr, assertion, test input | Fix the implementation or an invalid test assumption |
| Failed download | Network policy, DNS, destination service | Continue independent work with installed dependencies and record the gap |

Do not classify every failed test as a permissions issue or broaden permissions merely to get green output. Taskboard needs no network dependency installation, so its offline logic checks remain runnable.

Exercise: explain one scenario that does not ask but remains read-only, and one that is approved but still fails. Submit policy commands, outputs, and your classification by control layer. If you run a real sandbox probe, record its OS, CLI version, and process exit status separately. Mark untested operating systems as unverified. Next: [sessions and context](07-context.md).
