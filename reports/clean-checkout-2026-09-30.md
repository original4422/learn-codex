# Clean checkout verification — 2026-09-30

The release candidate was copied into a fresh directory using only tracked
files and the new GitHub Actions workflow. No existing `.cache`, `.venv`,
`dist`, installed package or Codex authentication was copied.

Environment: macOS arm64, Python 3.14.7. All commands ran from the fresh
directory with the Python standard library and no package installation.

| Command or check | Result |
| --- | --- |
| `python3 scripts/course.py check` | Exit 0; 65 tests, 4 Skill checks, 39 pages and 1550 links/assets |
| `python3 scripts/course.py build` | Exit 0; bilingual site and link validation passed |
| `python3 scripts/course.py lab loop` | Exit 0 |
| `python3 scripts/course.py lab instructions` | Exit 0 |
| `python3 scripts/course.py lab policy` | Exit 0 |
| `python3 scripts/course.py lab context` | Exit 0 |
| `python3 scripts/course.py lab subagents` | Exit 0 |
| `python3 scripts/course.py lab mcp-demo` | Exit 0; real local MCP subprocess |
| `python3 examples/taskboard/acceptance.py` | Exit 0; 6 acceptance checks |
| Local HTTP preview | Chinese root, English index, search index and JavaScript returned HTTP 200 |
| `git diff --check` | Exit 0 |

The first clean run exposed an intermittent test failure: the synthetic CLI
timeout test sometimes exhausted its one-second deadline before receiving its
first event. The focused rerun passed. Its budget is now three seconds, below
the fixture's ten-second sleep; the final clean run still verifies timeout,
partial-event preservation and stale-output removal.

Before initial publication, all 96 existing historical blob versions were
checked for credential patterns, user-specific absolute paths and private or
cache file paths. No matches were found. The largest blob was approximately
20 KB. Tracked source and assets are the course implementation; upstream Codex
is referenced by pinned links and hashes, with downloaded source excluded.

GitHub Actions runs the offline check on Python 3.10 and 3.14. This local
verification made no model calls; historical CLI and App Server observations
remain in the original acceptance record.
