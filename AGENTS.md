# learn-codex contributor instructions

- This is an independent local teaching repository. Write only inside this repository.
- Course material in `docs/zh` and `docs/en` must remain structurally equivalent. Chinese is the default site language.
- Label official implementation, observed behavior, and teaching simplification explicitly.
- Use pinned primary sources from `references/upstream.json`. Do not invent model execution evidence.
- Keep labs bounded and dependency-light. A scripted model is an offline fixture, never a real model verification.
- Preserve `.cache/` as ignored local material. Do not include credentials, personal session logs, or host configuration in reports.
- Build and validate with `python3 scripts/course.py check`. Changes to the site also require `python3 scripts/course.py build`.
- No remote push, public deployment, or social publishing is authorized for v1.
