# Contributing

Improve explanations, add meaningful failure cases, correct version mappings or refine translations. Each change should answer a specific question and make results easier to reproduce or evaluate.

## Repository responsibilities

| Path | Contents |
| --- | --- |
| `docs/zh/`, `docs/en/` | Matching Chinese and English text |
| `src/codex_lab/` | Mechanism experiments, MCP service and real CLI adapter |
| `examples/` | Taskboard, exercises, instruction tree and read-only MCP data |
| `tests/` | Normal and failure behavior verification |
| `scripts/`, `site/assets/` | Shared entry point, static build, editable SVG sources and interactions |
| `references/`, `reports/` | Pinned sources, versions and acceptance evidence |
| `.cache/`, `dist/` | Ignored temporary files and reproducible site output |

## Editing the course

Update both languages and preserve the same chapters and experiment coverage. A translation can reorder sentences for natural expression, but must not omit failure conditions, limitations or verification steps. Link product claims to the appropriate official document or source at a fixed commit.

Each lesson needs a goal, runnable steps, expected observations, troubleshooting and an exercise. A short definition alone is not coverage of a topic. Register new chapters in the page list in `scripts/build_site.py` and provide both languages.

The site uses a small in-repository Markdown renderer supporting headings, paragraphs, fenced code, links, images, emphasis, flat lists, quotes and tables. Raw HTML is escaped. MDX, nested lists, footnotes and raw pipe characters in table cells are unsupported. Turn complex hierarchies into subsections and put commands containing pipes in fenced code blocks.

## Editing experiments

State the behavior being verified first. “A failed write preserves the original file” is a better test goal than “a function gets called.” Failure tests should check persistent state and exit codes, not merely match an error message.

Keep teaching models explicitly bounded. Sharing a function name with a product does not make a model the official implementation. Real integrations must use the official CLI or protocol and state authentication, usage, timeout and output limits. Default tests must not call a model.

```sh
python3 scripts/course.py check
python3 examples/taskboard/.agents/skills/taskboard-check/scripts/check.py
python3 scripts/draw_diagrams.py
python3 scripts/course.py build
```

## Editing the site or diagrams

Edit and regenerate SVG through Python, retaining both source and export. After a site change, check the Chinese default page, same-chapter English switching, search, narrow-screen navigation, copy buttons and keyboard access. Progress and theme stay in browser storage. Do not add trackers, remote fonts or unsolicited analytics services.

## Upgrading the upstream version

First verify an available tag and commit in a dedicated change. Then update `references/upstream.json`, the source map, affected commands and verification records. Live documentation continues to change: pinned source does not pin the website. Explain which versions differ rather than only replacing the version number.

This repository does not copy assets from adjacent courses. Its original teaching code, prose and diagrams use the MIT license. Retain links and upstream Apache-2.0 attribution when referencing OpenAI source. Contributions must have compatible distribution rights.
