# Known Limitations

> **Deprecated.** This file is superseded by the
> [panelmark-docs limitations page](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/limitations.md).
> It will be removed in a future release.

Real current limitations and intentionally non-obvious behaviour in panelmark-tui.
Items here are not bugs — they are the current reality that a contributor or user
needs to know about because the behaviour is surprising or differs from a reasonable
first expectation.

---

## Widgets

### `FilePicker` — directory panel navigates into directories, does not toggle expand/collapse

The tree panel on the left shows the contents of the currently selected directory.
Pressing `Enter` on a directory **navigates into it** — the panel contents change to
show that directory's children.  There is no collapsible tree view; the FilePicker
always shows a flat listing of the current directory.

---

## Testing

### Widget constructor does not accept a `_terminal` kwarg

Widget classes (`Confirm`, `Alert`, `FilePicker`, etc.) do not accept a `_terminal`
constructor argument.  To inject a mock terminal for testing, set
`parent_shell.terminal` before calling `widget.show(parent_shell=parent)`.

See [Testing](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/limitations.md) for the correct pattern and examples.

---

## Shell language

### Parser is permissive about split alignment

The shell-language reference implies that structural column dividers must appear at
exactly the same position in every content row of a block.  The parser enforces this
loosely — some irregular layouts are accepted silently rather than raising an error.
Valid layouts defined per the reference will always parse correctly; the edge cases
are layouts that the reference would reject but the parser accepts.
