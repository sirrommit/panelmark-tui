# Documentation vs Implementation Issues

## What the projects currently are

- `panelmark` is the renderer-agnostic core: it parses the ASCII shell DSL, resolves regions, defines `DrawCommand`/`RenderContext`, and provides the `Shell` state machine with focus, dirty tracking, `update`, `bind`, and `on_change`.
- `panelmark-tui` is the blessed-backed terminal layer: it subclasses `panelmark.Shell` with `run()` and `run_modal()`, renders borders and regions, ships built-in interactions, modal widgets, and headless test helpers.

## panelmark

### Comment syntax is documented incorrectly

- `panelmark/docs/shell-language.md` says comments beginning with `#` are stripped.
- The implementation only strips C-style `/* ... */` comments in [`panelmark/panelmark/style.py`](/home/sirrommit/claude_play/panelmark/panelmark/style.py).
- Effect: shell definitions written per the docs with `# comment` will fail or be parsed as literal content.

### Blank-line height semantics are documented incorrectly

- `panelmark/docs/shell-language.md` says blank lines are ignored, then later says additional blank lines inside a multi-row panel expand its height.
- The parser skips blank lines entirely in [`panelmark/panelmark/parser.py`](/home/sirrommit/claude_play/panelmark/panelmark/parser.py), so blank lines never contribute height.
- Effect: the implicit-height example in the docs is not achievable as written.

### Fill-only vertical splits do not behave as documented

- `panelmark/docs/shell-language.md` says if all panels in a split are fill, they share space equally.
- The resolver in [`panelmark/panelmark/layout.py`](/home/sirrommit/claude_play/panelmark/panelmark/layout.py) does not implement equal distribution for fill-only splits; the left branch takes almost all width and the right branch can collapse.
- Effect: documented layout behavior is materially different from runtime behavior.

### Vertical split validation is stricter in the docs than in the code

- The docs say the structural divider must appear in the same structural position on every content row.
- The parser only requires the first outer divider character to exist and be the same type (`|` or `#`) across rows in [`panelmark/panelmark/parser.py`](/home/sirrommit/claude_play/panelmark/panelmark/parser.py).
- Effect: some irregular layouts are accepted even though the reference says they are invalid.

### Panel headings are documented as renderer-visible, but the shipped renderer ignores them

- `panelmark/docs/shell-language.md` says `__text__` headings are passed to the renderer and may be displayed.
- `Panel.heading` is parsed and stored, but `panelmark-tui` does not render panel headings anywhere.
- Effect: the feature exists in the core model but not in the only real renderer.

## panelmark-tui

### The getting-started guide miscounts the example regions

- `panelmark-tui/docs/getting-started.md` says the sample layout creates four regions.
- The sample defines three named regions: `$tasks$`, `$entry$`, and `$status$`.

### Menu navigation docs overstate the implemented key bindings

- `panelmark-tui/docs/interactions.md` says `MenuReturn` supports Page Up, Page Down, Home, and End.
- `MenuReturn`, `MenuFunction`, and `MenuHybrid` only implement up/down, `j`/`k`, and Enter in [`panelmark-tui/panelmark_tui/interactions/menu.py`](/home/sirrommit/claude_play/panelmark-tui/panelmark_tui/interactions/menu.py).
- Effect: users following the docs will expect navigation features that do not exist.

### `MenuHybrid` is documented as tuple-based, but implemented as callable-or-value

- The docs say `MenuHybrid(items)` maps labels to `(callback, return_value)` tuples.
- The implementation treats each item value as either a callable or a terminal return value; tuples are not unpacked in [`panelmark-tui/panelmark_tui/interactions/menu.py`](/home/sirrommit/claude_play/panelmark-tui/panelmark_tui/interactions/menu.py).
- Effect: the documented example would return the tuple instead of invoking the callback.

### `TextBox` Home/End behavior is documented incorrectly

- `panelmark-tui/docs/interactions.md` says Home/End jump to line start/end.
- `TextBox` moves to the start or end of the entire text buffer in [`panelmark-tui/panelmark_tui/interactions/textbox.py`](/home/sirrommit/claude_play/panelmark-tui/panelmark_tui/interactions/textbox.py).

### `SubList` is documented as an expandable tree, but implemented as a static nested-list flattener

- The docs describe expandable/collapsible groups and dict-based hierarchical input.
- The implementation only accepts nested lists meaningfully, flattens them recursively, and has no expand/collapse state or navigation in [`panelmark-tui/panelmark_tui/interactions/list_view.py`](/home/sirrommit/claude_play/panelmark-tui/panelmark_tui/interactions/list_view.py).
- Effect: this is a major mismatch between API expectations and the real feature set.

### `CheckBox` docs omit real behavior and claim nonexistent behavior

- The docs describe only multi-select checkboxes and say left/right explicitly set unchecked/checked.
- The implementation supports both `mode="multi"` and `mode="single"` but does not handle left/right at all in [`panelmark-tui/panelmark_tui/interactions/checkbox.py`](/home/sirrommit/claude_play/panelmark-tui/panelmark_tui/interactions/checkbox.py).

### `InputPrompt` docs conflict with the implementation

- `panelmark-tui/docs/widgets.md` says Enter in the entry box submits.
- The implementation uses `TextBox(wrap="extend")`, where Enter inserts a newline; submission requires moving focus to the button row in [`panelmark-tui/panelmark_tui/widgets/input_prompt.py`](/home/sirrommit/claude_play/panelmark-tui/panelmark_tui/widgets/input_prompt.py).
- The widget module docstring is correct; the central widgets guide is not.

### `FilePicker` docs describe a different widget than the one in the code

- The docs say there is a filename bar, Open/Cancel buttons, and expandable/collapsible tree behavior.
- The implementation has a path field, filter field, tree panel, files panel, status bar, and default `OK`/`Cancel` buttons in [`panelmark-tui/panelmark_tui/widgets/file_picker.py`](/home/sirrommit/claude_play/panelmark-tui/panelmark_tui/widgets/file_picker.py).
- Enter on a directory navigates into it; there is no expand/collapse state.

### Testing docs mention a widget `_terminal` override that does not exist

- `panelmark-tui/docs/testing.md` says most widgets accept a `_terminal` kwarg.
- The widget `show()` methods do not expose `_terminal`; tests inject a terminal indirectly through `parent_shell.terminal`.
- Effect: the recommended testing pattern in the docs is misleading.

## Cross-project inconsistencies worth fixing

### The examples are not all aligned with the current APIs

- [`panelmark-tui/examples/hello.py`](/home/sirrommit/claude_play/panelmark-tui/examples/hello.py) claims a non-callable `MenuFunction` item causes the shell to exit.
- The current `MenuFunction` implementation unconditionally calls the selected value as a callback, so that example is inconsistent with the code.

### The local test workflow is under-documented

- `panelmark-tui` tests passed only after setting `PYTHONPATH` explicitly from the repository root.
- The docs describe testing helpers, but there is no clear repo-level instruction for running the package test suite from this checkout layout.

## Verification

- `panelmark` tests: `116 passed`
- `panelmark-tui` tests: `225 passed` when run with `PYTHONPATH=/home/sirrommit/claude_play/panelmark-tui:/home/sirrommit/claude_play/panelmark`
