# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.2.0] — 2026-04-05

### Added

- `NestedMenu` interaction with `Leaf` sentinel for hierarchical navigation.
- `RadioList` interaction (portable-library-compatible selector).
- `TableView` interaction for tabular display.
- `TreeView` interaction; `SubList` deprecated in its favour.
- `Toast` and `Spinner` display interactions.
- `DataclassFormInteraction` — form driven by a dataclass definition.
- `DataclassForm` widget — modal wrapper around `DataclassFormInteraction`.
- `_ModalWidget` base class extracting the shared `Shell` construction and
  `run_modal()` pattern for all modal widgets.
- `TextBox.enter_mode` and `TextBox.signal_return()` for controlled submission.
- Page Up / Page Down / Home / End navigation in all list interactions.
- Panel heading rendering: when a region carries a `heading` string (set via
  `__text__` in the shell definition), the renderer draws a
  `├─── Heading ───┤` sub-border at the top of the panel and shifts content
  down by one row.
- `TUICommandExecutor` — translates `list[DrawCommand]` to blessed terminal
  output, handling row/col offset mapping from region coordinates.
- `build_render_context()` — builds a `RenderContext` from a `Region` and
  blessed terminal, detecting colour depth and capability flags.
- `docs/renderer-implementation.md` — describes the TUI rendering pipeline.
- Examples directory with `hello.py` and `task_manager.py`.
- Smoke tests for example scripts.
- `Makefile` with `test`, `test-all`, `run-hello`, and `run-task-manager`
  targets.

### Changed

- All built-in interactions migrated to the draw-command API: `render()` now
  accepts `RenderContext` and returns `list[DrawCommand]` instead of writing
  to the terminal directly.
- `_ScrollableList` split into `_Scrollable` (scroll-offset state only) and
  `_ScrollableList` (adds active-index and `_build_rows()`). `ListView` now
  inherits `_Scrollable`.
- `MenuFunction` gains `signal_return()`; `MenuHybrid` removed.
- `SubList` removed; use `ListView` for flat display or `TreeView` for
  hierarchy.
- Brought all portable interactions and widgets into conformance with the
  panelmark portable-library contract (constructor shape, semantic contract,
  return values).
- `task_manager.py` example rewritten to use only the public shell API.

### Fixed

- `MenuFunction.get_value()` now returns the current highlight rather than a
  stale value.
- Three bugs found during example testing (key handling, focus, rendering).
- Fill-split equal distribution: two or more fill-width columns now correctly
  share available width (documentation aligned with the core fix).

---

## [0.1.0] — 2026-03-24

Initial release.

### Added

- TUI renderer (`Renderer`) driving blessed terminal output from a
  `panelmark.Shell`.
- Full structural border rendering: `|=====|` frame lines, `|-----|` and
  `|=====|` separator lines, titled borders (`|--- Label ---|`), and
  box-drawing corner/junction characters matching the nested layout structure.
- `render_region()` executing draw commands against the terminal for each
  assigned interaction.
- Built-in interactions: `MenuFunction`, `MenuReturn`, `CheckBox`, `FormInput`,
  `TextBox`, `ListView`, `StatusMessage`, `Function`.
- Modal widgets: `Alert`, `Confirm`, `InputPrompt`, `ListSelect`, `FilePicker`,
  `DatePicker`, `Progress`.
- `MockTerminal` and `make_key()` test helpers.
- `testing.py` module for interaction unit tests.
- Shell event loop integration via `panelmark_tui.run()`.

[Unreleased]: https://github.com/sirrommit/panelmark-tui/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/sirrommit/panelmark-tui/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/sirrommit/panelmark-tui/releases/tag/v0.1.0
