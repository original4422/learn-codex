# Sources and versions: state what the evidence supports

This course checked official documentation on **2026-09-19** and pins source reading to the public release matching the local `codex-cli 0.155.1`. Commands first target this version. After installing a newer release, check `codex --version` and the relevant subcommand's `--help`.

## Pinned upstream

| Item | Verified value |
| --- | --- |
| Official repository | [openai/codex](https://github.com/openai/codex) |
| Release tag | [rust-v0.155.1](https://github.com/openai/codex/releases/tag/rust-v0.155.1) |
| Full commit | [be2951ea34f0d295ed0becf97079f92fa5f6950e](https://github.com/openai/codex/commit/be2951ea34f0d295ed0becf97079f92fa5f6950e) |
| Annotated tag object | `4e21628f9ec9ee656650cd2b62ef92225725b5ac` |
| Upstream license | Apache-2.0 |
| Machine-readable record | [references/upstream.json](../../references/upstream.json) |

**Observed behavior:** the installed binary reported `codex-cli 0.155.1`; `git ls-remote` returned the tag object and peeled commit above; the downloaded source's `codex-rs/Cargo.toml` also records `0.155.1`. The archive SHA-256 is `cd5a884836b53422052989479c6662f06e2ee8bb768c1a86a5ff7326b887d4d6`. This establishes the version correspondence. It does not mean the whole upstream was compiled or every feature tested.

```sh
git ls-remote https://github.com/openai/codex.git \
  refs/tags/rust-v0.155.1 'refs/tags/rust-v0.155.1^{}'
codex --version
```

## Keep three kinds of evidence separate

| Label | Supports | Does not support |
| --- | --- | --- |
| Official implementation | Types, branches, and transitions in the pinned source | Every account having access to a model |
| Observed behavior | The actual command, input, output, and exit code | Untested platforms or failure paths |
| Teaching simplification | Invariants and failures defined by a Python lab | Codex using the same algorithm, character budget, or worker model |

Labs use an original small Taskboard application. The offline planner is scripted; compaction is extractive; the subagent lab uses Python workers. These explain control flow without reproducing model reasoning or testing a Codex model. Real CLI execution, a real App Server handshake, and real model requests are recorded separately in [local acceptance](acceptance.md).

## Official entry points and documentation drift

During implementation we opened [open-source components](https://learn.chatgpt.com/docs/open-source), [non-interactive execution](https://learn.chatgpt.com/docs/non-interactive-mode), [MCP](https://learn.chatgpt.com/docs/extend/mcp), [subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [SDK](https://learn.chatgpt.com/docs/codex-sdk), [App Server](https://learn.chatgpt.com/docs/app-server), and [the desktop app](https://learn.chatgpt.com/docs/app). The former `developers.openai.com/codex/` entry point redirected to `learn.chatgpt.com/docs` on the verification date.

Product pages evolve; commit links remain fixed. Resolve disagreements by stating the version. For example, SDK source in this commit lives in `sdk/typescript/` and `sdk/python/`; a moving branch path in a web page is not proof of a historical file location. Current desktop documentation also uses the name ChatGPT desktop app. We use “desktop” as in the project brief and explain workflows without inferring private UI internals.

## The shortest source-reading route

Open the [source map](source-map.md), then read one entry point and one test for the behavior you are observing. Do not start by reading the whole Rust repository. Links share one commit, and `references/upstream.json` records content hashes for inspected files. `.cache/upstream/` is an ignored implementation-time download, not an installation requirement or a tracked course dependency. Offline labs do not need it.

Source retrieval initially hit an unavailable local proxy and sandbox DNS restrictions. An approved read-only network download then succeeded. We did not substitute guessed source paths or modify system proxy settings.

## Attribution and licenses

The course contains original explanations, experiments, and short source references rather than copies of entire documentation pages. Upstream code belongs to OpenAI and its contributors under Apache-2.0; the complete ignored download retains its original license. This is not official OpenAI training. Public CLI, SDK, and App Server code does not establish visibility into private desktop UI or hosted models. Contributions should record version changes, evidence, and remaining uncertainty; see [contributing](contributing.md).
