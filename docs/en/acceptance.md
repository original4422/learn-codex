# v1 local acceptance record

Acceptance date: 2026-09-19. The objective is a complete local teaching project matching the [confirmed brief](../../PROJECT_BRIEF.md). Upstream is pinned to Codex CLI `0.155.1`, commit `be2951ea34f0d295ed0becf97079f92fa5f6950e`. This page and the [machine-readable record](../../reports/verification.json) describe verification scope; detailed output is in the [check log](../../reports/checks.log).

## Delivery coverage

| Brief requirement | Artifact and acceptance method |
| --- | --- |
| Independent local Git repository and bilingual entry points | Root README, README.en.md and commit history |
| Complete bilingual lessons and guides | 19 pages per language, including 11 chapters; page and body checks |
| A real continuous case | Taskboard reference, runnable starter, exercise generator and black-box acceptance |
| Mechanism explanations and runnable experiments | Tool loop, instruction discovery, policy, context and parallel aggregation with explicit simplification boundaries |
| Real interface integration | MCP stdio subprocess, Codex exec adapter and App Server client |
| Diagrams and bilingual site | Python-generated SVG, interactions, search, same-chapter language switch and responsive navigation |
| Verification, sources and contribution guidance | Automated checks, pinned source hashes, source map and bilingual contribution guide |

## Recorded results

| Check | Result |
| --- | --- |
| Automated tests | 63 passed, including bilingual coverage, failure paths and process cleanup |
| Taskboard black-box acceptance | Reference 4/4; starter correctly rejected |
| Independent Skill check | 4 behavior checks passed |
| Site build | 39 HTML pages and 1550 local links/assets validated |
| Installed entry point | Editable install in a fresh project-local virtual environment succeeded; `codex-lab loop` passed |
| Pinned source verification | All 28 recorded files matched their SHA-256 hashes |
| Real CLI and App Server | Both passed, with no model calls |
| Real model | Attempt timed out; unverified and excluded from pass claims |

## Verification layers

**Offline programs and protocols**: behavior tests cover normal results, deliberate failures, budget exhaustion, legacy compatibility, failed atomic writes, MCP input and path boundaries, malformed subprocess output and deadline cleanup. An independent Skill performs black-box checks. The runnable starter fails tag-feature acceptance while the reference passes the same checks, demonstrating rejection of a known defect.

**Real local Codex**: `codex --version` returned `codex-cli 0.155.1`; required exec flags were present. A real App Server completed `initialize → initialized → thread/loaded/list`, returning an empty loaded-thread list. It used an isolated project-local Codex home and made no model call.

**Real model**: `python3 scripts/course.py lab exec --allow-model --timeout 20` was attempted and exited 2 with `subprocess deadline exceeded`. No `OPENAI_API_KEY`, `CODEX_API_KEY` or `CODEX_ACCESS_TOKEN` was available to the process, and the isolated course home had no established login. Timeout alone does not establish a single root cause. No successful completion event and fact-checked model result were obtained. Real model editing, model-driven MCP use and real Codex subagent collaboration remain **unverified**.

**Website**: the requested OpenAI-inspired monochrome and clean sans-serif styling retains an independent learn-codex identity. The build generates every page in both languages; the root path directly displays Chinese. The builder checks internal links, anchors, downloadable source links and assets. Actual browser interaction and viewport results are listed in the browser entry of the machine record.

## Reproduce locally

From the repository root:

```sh
python3 scripts/course.py check
python3 examples/taskboard/acceptance.py
python3 scripts/course.py lab mcp-demo
python3 scripts/course.py lab probe
python3 scripts/course.py lab app-server
python3 scripts/course.py serve --port 8765
```

Open the [local preview](http://127.0.0.1:8765). Check the Chinese landing page and matching English chapter; search for `MCP`; inspect failure and budget termination in the playground; mark a chapter as learned and switch languages; open navigation on a narrow screen. Use the Markdown source link beside an article to inspect its source.

Regenerate execution evidence without model calls:

```sh
python3 scripts/verify.py --with-codex
```

Omit `--with-codex` if Codex is not installed; the record will explicitly show which integrations were not run. A real model run needs authentication and separate execution following the [lab guide](labs.md). This command cannot replace it.

## Known limitations

- Verification ran on macOS arm64 with Python 3.14.7. Code targets Python 3.10+, but no claim is made that every Python version, Linux or Windows was executed.
- Taskboard is a single-writer example. Atomic replacement prevents partial JSON files; it does not provide multi-writer transactions or prevent concurrent lost updates.
- The MCP service is a bounded teaching subset for a trusted local directory. Its path checks do not defend against malicious concurrent replacement and are not an OS sandbox.
- Python policy, compaction and subagent experiments are teaching models. They do not verify real cross-platform isolation, model compaction quality or model delegation quality.
- SDKs have a source walkthrough and purpose comparison. The runnable minimal integration uses App Server; TypeScript and Python SDK execution is not separately claimed.
- Official documentation is live. The pinned items are the source commit and verification date; future docs or CLI changes require rechecking.

## Publishing boundary

Artifacts stay inside `learn-codex`. Adjacent projects were not changed. No public repository was created, no remote was pushed, no site was publicly deployed and no social content was published. Preview binds only to `127.0.0.1`. The user can assess local v1 using this evidence and add real model evidence after authentication is available.
