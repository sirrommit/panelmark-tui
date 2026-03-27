# Claude Instructions for panelmark-tui

This repository is `panelmark-tui`, the terminal renderer for `panelmark`.

## Scope

- Work inside `/home/sirrommit/claude_play/panelmark-tui`.
- You may read `/home/sirrommit/claude_play/panelmark` when needed for core contract,
  shell-language, draw-command, or renderer-boundary context.
- Do not edit `/home/sirrommit/claude_play/panelmark` unless the user explicitly asks for a
  coordinated cross-repo change.

## Dependency direction

- `panelmark-tui` depends on `panelmark`; the reverse is not true.
- Prefer local fixes in `panelmark-tui` when possible.
- If the task requires checking how `panelmark-tui` should interact with the core, read only
  the smallest relevant files in `../panelmark`.

## Context-efficiency rules

- Minimize context usage.
- Start with the smallest useful file set:
  1. User request
  2. `README.md`, `CONTRIBUTING.md`, `ISSUES.md`, and the relevant docs page
  3. The specific implementation file being changed
  4. The smallest relevant test file
- Do not read the whole repo by default.
- Do not read large sections of `../panelmark` unless the current task requires it.
- Prefer targeted `rg` searches and partial file reads.

Useful `../panelmark` files when needed:

- `../panelmark/README.md`
- `../panelmark/docs/shell-language.md`
- `../panelmark/docs/draw-commands.md`
- `../panelmark/docs/custom-interactions.md`
- `../panelmark/docs/renderer-boundary.md`

## Validation

Every change must be tested before completion.

- Run the narrowest relevant test first.
- If the change is broader, run:
  - `cd /home/sirrommit/claude_play/panelmark-tui && PYTHONPATH=/home/sirrommit/claude_play/panelmark-tui:/home/sirrommit/claude_play/panelmark pytest -q`
- For doc-only changes, run the nearest relevant check if one exists; otherwise say that no
  automated doc check exists.

## Git

Each completed update should be committed and pushed unless the user says not to.

- Remote: `origin git@github.com:sirrommit/panelmark-tui.git`
- Default branch: `main`

Before pushing:

- Check `git status --short`
- Confirm only intended files changed
- Use a clear scoped commit message

## Working style

- Make the smallest change that fully solves the task.
- Keep docs, tests, and implementation aligned when tightly coupled.
- Do not perform speculative cleanup outside the requested scope.
- Preserve unrelated user changes.
- If a task appears to require edits in `../panelmark`, stop and ask unless the user has
  already explicitly approved a cross-repo change.
