# Quickstart: run it, then go deeper

First confirm that the course, experiments and case project work on your machine without model authentication. Then start a real Codex task. Run every command from the repository root.

## 1. Check the environment

You need Python 3.10 or newer and Git for reviewing changes. The site generator and offline experiments use only the Python standard library; no Node, database or third-party runtime dependency is required.

```sh
python3 --version
git --version
python3 scripts/course.py check
```

`check` runs behavior tests, builds both site languages and validates local links. Success ends with `OK` plus page and link counts. Test counts may change as the repository evolves; the [acceptance record](acceptance.md) contains the exact counts for this delivery.

## 2. Run your first loop

```sh
python3 scripts/course.py lab loop
python3 scripts/course.py lab loop --fail-tool
python3 scripts/course.py lab loop --max-tool-calls 0
```

Compare tool results, errors and budget termination. These commands use a fixed script in place of a model to make failure paths reproducible. Three successful command exits do not mean that three real model calls took place.

## 3. Run Taskboard

```sh
mkdir -p .cache
python3 examples/taskboard/taskboard.py --store .cache/quickstart.json add "Read the first lesson" --tag study
python3 examples/taskboard/taskboard.py --store .cache/quickstart.json list --tag study
python3 examples/taskboard/.agents/skills/taskboard-check/scripts/check.py
```

The first task in a new store has ID 1. Running `add` again appends a task rather than replacing earlier tasks. The last command checks tag matching, completion status and invalid input using a temporary store; it does not change your list. To start over, choose a new `--store` filename.

## 4. Open the bilingual site

```sh
python3 scripts/course.py serve --port 8765
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). The initial page and navigation are Chinese. Select `English` at the top right to switch the same page. Press `/` to search and `Esc` to close. On narrow screens, open chapter navigation with the menu button. Stop the server with Ctrl-C.

The server binds to loopback only. `dist/` is generated static output; Markdown sources live in `docs/`. Use the HTTP preview rather than double-clicking HTML files because search needs to load its local index.

## 5. Connect real Codex

This course targets `0.155.1`. Check an existing CLI version first. If you have not installed it, install the pinned npm package or choose a platform-appropriate method from the [official CLI guide](https://learn.chatgpt.com/docs/cli).

```sh
npm install -g @openai/codex@0.155.1
codex --version
python3 scripts/course.py lab probe
python3 scripts/course.py lab app-server
```

`probe` checks local CLI capabilities. `app-server` starts the real CLI and performs its protocol handshake. Neither calls a model. Installing the npm package needs working Node/npm and networking; these are not dependencies of the offline course itself.

Real calls require authentication. The following sets a project-local Codex home for a single command to isolate course state without changing your everyday setup. Authentication files are excluded from Git.

```sh
CODEX_HOME="$PWD/.cache/codex-home" codex login
CODEX_HOME="$PWD/.cache/codex-home" codex login status
python3 scripts/course.py lab exec --allow-model
```

Refer to the [official authentication documentation](https://learn.chatgpt.com/docs/auth) for login methods and account availability. Successful login does not guarantee network access, model entitlement or remaining quota. Model errors are recorded separately from offline results. Do not disable all execution isolation just to silence an error.

## Next steps and common failures

- `python3` missing: install a supported Python version and confirm that your terminal uses that interpreter.
- `codex` missing from PATH: the course and offline labs still work. Install the CLI, then rerun `probe`.
- Port already in use: choose a different port, such as `--port 8767`.
- No search results: use the HTTP preview and try a short keyword such as `MCP`, `approval` or `AGENTS`.
- Real call fails: preserve the exit code and error category, then follow the [lab guide](labs.md). Do not relabel a failure as a pass.

Continue to [chapter 1](01-first-task.md). Your first learning artifact should be a reviewable code change, not a message in which the model says it is done.
