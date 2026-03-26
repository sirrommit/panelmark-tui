# Known Limitations

This document lists the known gaps between what the documentation describes and what is
currently implemented.  Each item notes which package is affected, what the current
behaviour is, and when a fix is planned.

---

## Layout

### Equal-width fill splits are not guaranteed

**Package:** `panelmark`
**Current behaviour:** When all columns in a vertical split are fill-width (no fixed or
percentage width specified), the left column takes almost all available space and the right
column may collapse to near-zero width.
**Expected behaviour (per docs):** Fill columns share remaining space equally.
**Planned fix:** Phase 2 of the project roadmap (`panelmark/panelmark/layout.py`).

---

## Shell language

### Panel headings are not rendered by `panelmark-tui`

**Package:** `panelmark-tui`
**Current behaviour:** The `__text__` heading syntax is parsed by the core parser and stored
in `Panel.heading`, but `panelmark-tui` does not render headings anywhere — they are silently
ignored at display time.
**Planned fix:** Phase 5 of the roadmap (render as centred title in the panel's top border
row).

---

## Interactions

### Paging keys are not implemented in menu interactions

**Package:** `panelmark-tui`
**Affected interactions:** `MenuReturn`, `MenuFunction`, `MenuHybrid`, `CheckBox`
**Current behaviour:** Only `↑`/`↓` (and `k`/`j`) and `Enter` are handled.
Page Up, Page Down, Home, and End do nothing.
**Planned fix:** Phase 3 of the roadmap.

### `SubList` is a static indented list, not a tree

**Package:** `panelmark-tui`
**Current behaviour:** `SubList` accepts nested lists and renders them with indentation.
It has no expand/collapse state, no keyboard navigation, and is not focusable.
Dict input is accepted but dict keys are used only as labels; the hierarchical structure
implied by key→children mapping is flattened.
**Planned fix:** Phase 4 of the roadmap — either rename to `IndentedList` and document
accurately, or replace with a real `TreeView` widget.

---

## Widgets

### `InputPrompt` — Enter inserts a newline, not submits

**Package:** `panelmark-tui`
**Current behaviour:** The entry box uses `TextBox(wrap="extend")`.  Pressing `Enter` inside
the box inserts a newline character.  To submit, press `Tab` to move focus to the button
row, then `Enter` on OK.
**Note:** This is intentional behaviour, not a bug.  The widget docstring describes it
correctly.  The central `widgets.md` guide previously described it incorrectly and has been
fixed.

### `FilePicker` — no expand/collapse tree navigation

**Package:** `panelmark-tui`
**Current behaviour:** The tree panel on the left shows the directory structure.  Pressing
`Enter` on a directory **navigates into it** — it does not toggle an expand/collapse state.
There is no collapsible tree; the panel always shows the contents of the currently selected
directory.

---

## Testing

### Widget `_terminal` kwarg does not exist

**Package:** `panelmark-tui`
**Current behaviour:** Widget classes (`Confirm`, `Alert`, etc.) do not accept a `_terminal`
constructor argument.  To inject a mock terminal for testing, set `parent_shell.terminal`
before calling `widget.show(parent_shell=parent_shell)`.
See [docs/testing.md](docs/testing.md) for the correct pattern.
