# Contributing to panelmark-tui

---

## Repository layout

This is a two-package repository:

```
claude_play/
├── panelmark/          # core library (zero dependencies)
└── panelmark-tui/      # blessed-powered TUI renderer (this package)
```

`panelmark-tui` depends on `panelmark` at runtime and at test time.  The packages
are not installed as editable installs by default in this checkout — `PYTHONPATH`
must include both roots so Python can find them.

---

## Running the tests

### `panelmark` tests (core library)

```bash
cd panelmark
pytest -q
```

No `PYTHONPATH` manipulation needed — `panelmark` has no local dependencies.

### `panelmark-tui` tests

```bash
cd panelmark-tui
PYTHONPATH=/path/to/claude_play/panelmark-tui:/path/to/claude_play/panelmark pytest -q
```

Replace `/path/to/claude_play` with the absolute path to this checkout.  For example,
if the repo lives at `/home/sirrommit/claude_play`:

```bash
PYTHONPATH=/home/sirrommit/claude_play/panelmark-tui:/home/sirrommit/claude_play/panelmark pytest -q
```

**Why both paths?** `panelmark_tui` imports from `panelmark`; neither is installed as
a package in the venv, so both source roots must be on `PYTHONPATH`.

Both test suites should pass cleanly.  Use the `Makefile` targets in `panelmark-tui` for
convenience:

```bash
make test        # panelmark-tui tests only
make test-all    # panelmark-tui tests with full PYTHONPATH
```

### Running both together

```bash
PYTHONPATH=/home/sirrommit/claude_play/panelmark-tui:/home/sirrommit/claude_play/panelmark \
  pytest -q panelmark-tui/tests/ panelmark/tests/
```

(Run from `claude_play/`.)

---

## Running the examples

Examples live in `panelmark-tui/examples/` and require a real terminal (they use
blessed for fullscreen rendering).

```bash
cd panelmark-tui
PYTHONPATH=/home/sirrommit/claude_play/panelmark-tui:/home/sirrommit/claude_play/panelmark \
  python examples/hello.py

PYTHONPATH=/home/sirrommit/claude_play/panelmark-tui:/home/sirrommit/claude_play/panelmark \
  python examples/task_manager.py
```

Examples do not run correctly inside pytest or when stdout is redirected — blessed
requires a real tty.

---

## Architecture overview

See [Renderer Implementation](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/renderer-implementation.md) for how
`panelmark-tui` satisfies the `panelmark` renderer specification.

For the normative renderer contract and compatibility levels, see the
[Renderer Spec](https://github.com/sirrommit/panelmark-docs/blob/main/docs/renderer-spec/overview.md).

---

## Adding a new interaction type

Interactions are single-region, reusable UI behaviors.  Use an interaction when your
component lives inside one shell region and handles its own rendering and key events.

1. Create `panelmark_tui/interactions/<name>.py` — subclass `panelmark.Interaction`.
2. Implement `render(context, focused)` → `list[DrawCommand]`.
3. Implement `handle_key(key)` → `(changed, value)`.
4. Implement `get_value()`, `set_value(value)`, and `signal_return()`.
5. Set `is_focusable = True` if the interaction should receive keyboard focus.
6. Export from `panelmark_tui/interactions/__init__.py`.
7. Add tests in `tests/` and document in the [Interactions](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/interactions.md) page.

See [`../panelmark/docs/custom-interactions.md`](../panelmark/docs/custom-interactions.md)
for the full `Interaction` ABC contract and the interaction API semantics.

---

## Adding a shell-composed widget

Shell-composed widgets build a small `Shell` layout internally and run it as a modal
overlay.  Use this pattern for multi-region TUI flows: dialogs with a message area plus
buttons, forms with multiple fields, picker UIs with two panes, etc.

1. Subclass `_ModalWidget` from `panelmark_tui.widgets._utils`.
2. Implement `_build_popup(term)` — construct and wire a `Shell`, return it.
3. Set `self.width` in `__init__` so the base class can auto-centre the popup.
4. `.show(parent_shell=...)` is provided by the base class and calls `run_modal()`.
5. Export from `panelmark_tui/widgets/__init__.py`.
6. Add tests using `MockTerminal` — see [Testing](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/limitations.md).
7. Document in the [Widgets](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/widgets.md) page.

See `panelmark_tui/widgets/alert.py` or `panelmark_tui/widgets/confirm.py` as minimal
reference examples.

---

## Adding a renderer-managed utility widget

Renderer-managed utility widgets (`Progress`, `Toast`, `Spinner`) need their own render
cycle because they push updates synchronously or dismiss themselves on a timer.  Use this
pattern only when the standard modal-shell pattern genuinely cannot work — for example
when the widget must update between keypresses.

These widgets do not follow the `_ModalWidget` base class pattern.  Study the existing
`Progress` or `Spinner` implementation to understand the lifecycle before writing a new
one.

Guidelines:
- Keep the public API consistent with other widgets: a `.show()` method or context-manager.
- Document explicitly that the widget manages its own render cycle.
- Document return/cancellation semantics clearly.
- Export from `panelmark_tui/widgets/__init__.py`.
- Document in the [Widgets](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/widgets.md) page under the renderer-managed family.
