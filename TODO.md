# TODO — panelmark-tui

This file tracks work that should be done in `panelmark-tui` itself. It should not include
core `panelmark` work except where a `panelmark` change has already landed and `panelmark-tui`
needs a follow-up adaptation.

## Current priorities

- [x] Rewrite [examples/task_manager.py](/home/sirrommit/claude_play/panelmark-tui/examples/task_manager.py) to avoid private shell internals such as `_interactions` and ad hoc shell state like `_current_task`.
- [x] Add smoke coverage for examples so README/demo drift is caught automatically.
- [x] Add a `Makefile` or `justfile` for common `panelmark-tui` workflows:
  - `test`
  - `test-all` or equivalent with the required `PYTHONPATH`
  - `run-hello`
  - `run-task-manager`
- [x] Extract a shared modal/widget helper for repeated `Shell` construction and `run_modal()` patterns used across widgets.

## API cleanup

- [x] Decide whether `MenuHybrid` stays as-is, is renamed, or is replaced by a clearer action/value API.
- [x] If `MenuHybrid` stays, tighten its public documentation and examples so the callable-or-value rule is immediately obvious.
- [ ] Keep `SubList` as compatibility-only unless there is a strong reason to keep investing in it separately from `TreeView`.

## Docs and demos

- [ ] Add a side-by-side README example that shows shell definition, Python wiring, and terminal output or screenshot.
- [ ] Promote the cleaned-up task manager example as the canonical showcase demo.
- [ ] Keep `KNOWN_LIMITATIONS.md`, `ISSUES.md`, and `CONTRIBUTING.md` aligned as implementation changes land.

## Later work

- [ ] Consider a `TextAreaPrompt` if there is a real use case that `InputPrompt` does not serve well.
- [ ] Consider `Tabs`, `CommandPalette`, or a multi-step `Wizard` only after the current widget and interaction APIs are cleaner.
