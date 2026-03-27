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

**Expected:** 136 passed.

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

**Expected:** 388 passed.

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

See [`panelmark/docs/renderer-boundary.md`](../panelmark/docs/renderer-boundary.md)
for a concise description of what `panelmark` owns, what `panelmark-tui` owns, and
how the two packages interact.

---

## Adding a new interaction type

1. Create `panelmark_tui/interactions/<name>.py` — subclass `panelmark.Interaction`.
2. Implement `render(context, focused)` → `list[DrawCommand]`.
3. Implement `handle_key(key)` → `(changed, value)`.
4. Implement `get_value()`, `set_value(value)`, and `is_focusable`.
5. Export from `panelmark_tui/interactions/__init__.py`.
6. Add tests in `tests/` and document in `docs/interactions.md`.

See [`panelmark/docs/custom-interactions.md`](../panelmark/docs/custom-interactions.md)
for the full `Interaction` ABC contract.

---

## Adding a new modal widget

Widgets are pre-built `Shell` instances.  Follow the pattern in any existing widget
(e.g. `panelmark_tui/widgets/alert.py`):

1. Build a layout string and assign interactions in `__init__`.
2. Expose a `.show(parent_shell=None, ...)` method that calls `Shell.run_modal()`.
3. Return a meaningful value (or `None` on cancel).
4. Export from `panelmark_tui/widgets/__init__.py`.
5. Add tests in `tests/test_widgets.py` using `MockTerminal` and the pattern in
   [`docs/testing.md`](docs/testing.md).
6. Document in `docs/widgets.md`.
