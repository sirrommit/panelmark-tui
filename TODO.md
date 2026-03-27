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
- [x] Keep `SubList` as compatibility-only unless there is a strong reason to keep investing in it separately from `TreeView`.

## Docs and demos

- [ ] Add a side-by-side README example that shows shell definition, Python wiring, and terminal output or screenshot.
- [ ] Promote the cleaned-up task manager example as the canonical showcase demo.
- [ ] Keep `KNOWN_LIMITATIONS.md`, `ISSUES.md`, and `CONTRIBUTING.md` aligned as implementation changes land.

## Consistent interaction API (PROPOSAL.md)

The goal: `get_value()` always means current logical state; `signal_return()`
always means explicit submit/accept.  See `PROPOSAL.md` for the full rationale
and the target interaction matrix.

### Phase 1 — Document the contract

- [ ] Add "Current logical state vs submitted result" definitions to `docs/interactions.md`.
- [ ] Add the interaction matrix table (from PROPOSAL.md) to `docs/interactions.md`.
- [ ] Mark `Function` as an escape hatch in its docstring and in `docs/interactions.md`.

### Phase 2 — Fix `MenuFunction`

- [ ] Change `MenuFunction.get_value()` to return the currently highlighted label
      (currently returns last activated label).
- [ ] Add `MenuFunction.last_activated` property to preserve the old behaviour for
      callers that need it.
- [ ] Update `examples/hello.py` and `examples/task_manager.py` if they rely on
      old `get_value()` semantics.
- [ ] Add / update tests: `get_value()` reflects current highlight; `last_activated`
      reflects last callback invocation; round-trip `get_value()` / `set_value()`.

### Phase 3 — `TextBox` submit mode

- [ ] Add `enter_mode` parameter to `TextBox`: `"newline"` (default), `"submit"`, `"ignore"`.
- [ ] Implement `TextBox.signal_return()`: signals with current text only in
      `enter_mode="submit"` after Enter is pressed.
- [ ] Update `InputPrompt` to use `enter_mode="submit"` if it simplifies its
      button/submit wiring.
- [ ] Add tests: submit mode signals return; newline mode does not; ignore mode does
      not; round-trip `get_value()` / `set_value()`.

### Phase 4 — Align selector family docs and tests

- [ ] Verify and document `MenuReturn`: `get_value()` = highlighted label,
      `signal_return()` = mapped payload.
- [ ] Verify and document `RadioList`: `get_value()` = selected value,
      `signal_return()` = same value on accept.
- [ ] Verify and document `CheckBox`: `get_value()` = full checked-state dict,
      no `signal_return()`.
- [ ] Verify and document `TreeView`: `get_value()` = highlighted path tuple,
      `signal_return()` = path on leaf accept.
- [ ] Verify and document `TableView`: `get_value()` = active row index,
      no `signal_return()` by default.
- [ ] Add round-trip `get_value()` / `set_value()` tests for each of the above.
- [ ] Add doc note that `RadioList` is the preferred single-select control;
      `CheckBox(mode="single")` is supported but not the recommended path.

### Phase 5 — Display interactions and escape-hatch clarification

- [ ] Verify `ListView`: `get_value()` = current items list, no `signal_return()`.
- [ ] Verify `StatusMessage`: `get_value()` = `(style, message)` or `None`,
      no `signal_return()`.
- [ ] Verify `FormInput` and `DataclassFormInteraction` current-state semantics
      match the matrix.
- [ ] Add a brief "Escape hatch" section to `docs/interactions.md` for `Function`.
- [ ] Add round-trip tests for `ListView`, `StatusMessage`, `FormInput`,
      `DataclassFormInteraction`.

## Later work

- [ ] Consider a `TextAreaPrompt` if there is a real use case that `InputPrompt` does not serve well.
- [ ] Consider `Tabs`, `CommandPalette`, or a multi-step `Wizard` only after the current widget and interaction APIs are cleaner.
