# Built-in Interactions

panelmark-tui provides 12 built-in interaction types, all importable from
`panelmark_tui.interactions`.

```python
from panelmark_tui.interactions import (
    MenuFunction, MenuReturn,
    TextBox,
    ListView,
    CheckBox,
    Function,
    FormInput, DataclassFormInteraction,
    StatusMessage,
    TreeView,
    RadioList,
    TableView,
)
```

These interactions are `panelmark-tui`-specific.  They implement the
`panelmark.Interaction` ABC, which is defined in the core renderer contract:
[`../panelmark/docs/renderer-spec/contract.md`](../panelmark/docs/renderer-spec/contract.md).
For the full ABC interface and guidance on writing custom interactions, see
[`../panelmark/docs/custom-interactions.md`](../panelmark/docs/custom-interactions.md).

---

## API Contract

Every interaction follows a three-concept model.

### Current logical state

The value that best represents what this interaction currently contains or has
selected right now.  Always accessible via `get_value()` and restorable via
`set_value()`.

Examples: text in a text box; checked-state mapping in a checkbox list; active
row path in a tree; active radio value; current status payload.

### Submitted result

A value produced when the user explicitly accepts or submits — pressing Enter
on a menu item, activating a form's submit action, etc.  Returned through
`signal_return()`, not through `get_value()`.

Examples: the payload selected from a menu; the accepted result of a form
submission.

### Display model

The backing content of a display-only interaction.  Display-only interactions
expose their display model through `get_value()` when that is the only
meaningful current state.

Examples: the list of strings in `ListView`; the rows and columns in
`TableView`.

---

## Interaction matrix

| Interaction | `get_value()` | `set_value()` | `signal_return()` |
|---|---|---|---|
| `MenuFunction` | current highlighted label | highlight label | none |
| `MenuReturn` | current highlighted label | highlight label | mapped payload on accept |
| `CheckBox` | full checked-state dict | replace checked-state dict | none |
| `RadioList` | current selected value | select by value | selected value on accept |
| `TreeView` | current highlighted path tuple | highlight path | path on leaf accept |
| `TableView` | current active row index | set active row index | none |
| `TextBox` | current text | replace text | none (submit mode: text on accept) |
| `ListView` | current items list | replace items list | none |
| `StatusMessage` | current `(style, message)` or `None` | replace status payload | none |
| `FormInput` | current field-state dict | replace field-state dict | submitted dict on submit |
| `DataclassFormInteraction` | current field-state dict | replace field-state dict | action result on submit |
| `Function` | escape hatch — see below | escape hatch | escape hatch |

---

## MenuReturn

A scrollable menu that immediately returns a value when the user selects an item.

```python
MenuReturn(items: dict)
```

`items` maps display labels to return values. When the user presses Enter on a label, the
shell exits with the corresponding value.

```python
from panelmark_tui.interactions import MenuReturn

menu = MenuReturn({
    "New file":  "new",
    "Open...":   "open",
    "Save":      "save",
    "Quit":      "quit",
})
sh.assign("menu", menu)
result = sh.run()    # returns "new", "open", "save", or "quit"
```

**Keys:** `↑`/`↓` or `k`/`j` to navigate one item; `Page Up`/`Page Down` to jump by a
full page; `Home`/`End` to jump to the first/last item; `Enter` to select.

**Value:** the dict value mapped to the selected label (or the label itself if you pass a
list to convert via `{item: item for item in items}`).

---

## MenuFunction

A scrollable menu that calls a Python function when the user selects an item. Does not
exit the shell automatically — the callback decides what happens next.

```python
MenuFunction(items: dict)
```

`items` maps display labels to callables. Each callable receives the shell as its first
argument: `callback(shell)`.

```python
from panelmark_tui.interactions import MenuFunction

def open_file(sh):
    path = FilePicker().show(parent_shell=sh)
    if path:
        sh.update("status", ("success", f"Opened {path}"))

menu = MenuFunction({
    "Open file":  open_file,
    "Settings":   lambda sh: show_settings(sh),
    "Quit":       lambda sh: sh.handle_key("\x11"),   # Ctrl+Q
})
sh.assign("menu", menu)
```

**Keys:** same navigation as `MenuReturn` (including `Page Up`/`Page Down`/`Home`/`End`).

**`get_value()`:** returns the currently **highlighted** label (not the last invoked one).

**`last_activated`:** read-only property that holds the label most recently invoked by the
user, or `None` before any item has been activated.  Use this when you need to know which
callback was last triggered without changing the menu's current state.

---

## TextBox

A multi-line (or single-line) text input with cursor navigation and optional word wrap.

```python
TextBox(
    initial: str = "",
    wrap: Literal["word", "anywhere", "extend"] = "word",
    readonly: bool = False,
    enter_mode: Literal["newline", "submit", "ignore"] = "newline",
)
```

**Wrap modes:**
- `"word"` — wrap at word boundaries (default)
- `"anywhere"` — wrap mid-word when the line is full
- `"extend"` — no wrap; newlines only on `Enter` (best for single-line inputs)

**Enter modes:**
- `"newline"` (default) — `Enter` inserts a newline character.
- `"submit"` — `Enter` does not insert a newline; instead `signal_return()` fires
  with the current text so the shell can exit.  Use this for single-line prompts
  where `Enter` should accept the input.
- `"ignore"` — `Enter` is silently discarded.

```python
from panelmark_tui.interactions import TextBox

# Single-line entry that submits on Enter
entry = TextBox(wrap="extend", enter_mode="submit")
sh.assign("entry", entry)
result = sh.run()   # returns the typed text when Enter is pressed

# Read-only display
display = TextBox(initial="some text", readonly=True)
sh.assign("display", display)
```

**Keys:** printable characters to type; `Backspace`/`Delete` to erase; `←`/`→` to move
cursor; `Home`/`End` to jump to buffer start/end; `Enter` behaviour depends on
`enter_mode` (see above).

**Value:** `str` — the full text content including any newlines.

**`signal_return()`:** fires with `(True, text)` when `Enter` is pressed and
`enter_mode="submit"`.  Resets after the first call so it fires exactly once per
press.  Always returns `(False, None)` in `"newline"` and `"ignore"` modes.

---

## ListView

A display-only scrollable list. Not focusable — used to show read-only content that the
user cannot interact with directly. Updated programmatically via `shell.update()`.

```python
ListView(items: list[str])
```

```python
from panelmark_tui.interactions import ListView

log = ListView(["Starting...", "Loading config...", "Ready"])
sh.assign("log", log)

# Append a line later:
current = sh.get("log")
sh.update("log", current + ["New log entry"])
```

**Value:** `list[str]` — the current list of display lines.

---

## TreeView

An interactive, keyboard-navigable tree with expand/collapse support.

```python
TreeView(tree: dict, *, initially_expanded: bool = False)
```

`tree` is a nested dict where `None` values are **leaves** and dict values are
**branches** with children:

```python
from panelmark_tui.interactions import TreeView

tree = TreeView({
    'Documents': {
        'report.pdf': None,
        'notes.txt':  None,
    },
    'Pictures': {
        'photo.jpg': None,
    },
    'README.md': None,
})
sh.assign('tree', tree)
result = sh.run()   # returns path tuple when a leaf is selected
                    # e.g. ('Documents', 'report.pdf')
```

Pass `initially_expanded=True` to start with all branches open.

**Keys:**

| Key | Action |
|-----|--------|
| `↑` / `k` | Move cursor up |
| `↓` / `j` | Move cursor down |
| `Page Up` | Jump up one page |
| `Page Down` | Jump down one page |
| `Home` | Jump to first item |
| `End` | Jump to last item |
| `Enter` / `Space` on branch | Toggle expand/collapse |
| `Enter` / `Space` on leaf | Select — shell exits with path tuple |

**Value:** `tuple[str, ...]` — the path of the currently highlighted item,
e.g. `('Documents', 'report.pdf')` or `('README.md',)`.  Returns `None` if
the tree is empty.

**signal_return:** fires with `(True, path_tuple)` when a leaf is activated.
Branch toggles do not exit the shell.

---

## CheckBox

A scrollable checkbox list. Supports **multi-select** (the default) and **single-select**
modes.

```python
CheckBox(items: dict[str, bool], mode: str = "multi")
```

`items` maps labels to initial checked states.

### Multi mode (`mode="multi"`, default)

Any number of items can be checked simultaneously. Checked items show `[X]`, unchecked
show `[ ]`.

```python
from panelmark_tui.interactions import CheckBox

options = CheckBox({
    "Enable logging":   True,
    "Dark mode":        False,
    "Auto-save":        True,
    "Spell check":      False,
})
sh.assign("options", options)

result = sh.get("options")   # dict[str, bool]
```

### Single mode (`mode="single"`)

At most one item can be checked at a time. Checking a new item automatically unchecks the
previously checked one. Checked items show `(●)`, unchecked show `( )`.

```python
priority = CheckBox({
    "High":   True,
    "Medium": False,
    "Low":    False,
}, mode="single")
sh.assign("priority", priority)
```

**Keys:** `↑`/`↓` or `k`/`j` to navigate one item; `Page Up`/`Page Down` to jump by a
full page; `Home`/`End` to jump to the first/last item; `Space` or `Enter` to toggle.

**Value:** `dict[str, bool]` — label → checked state for all items.

> **Prefer `RadioList` for single-select.**  `CheckBox(mode="single")` is supported
> but returns a `dict[str, bool]`, which is harder to work with than the plain value
> that `RadioList.get_value()` and `signal_return()` return.  Use
> `CheckBox(mode="single")` only when you already have a checked-state dict as input
> or need the checkbox visual style specifically.

---

## RadioList

A single-select list with radio-button visuals (`(●)` / `( )`).  The cursor
position *is* the selection — moving the cursor immediately changes which item
shows `(●)`.  Pressing `Enter` or `Space` accepts the current selection and
causes the shell to exit with the selected **value** (not the label).

A cleaner alternative to `CheckBox(mode="single")` when the items map to
meaningful return values.

```python
RadioList(items: dict)
```

`items` maps display labels to return values.

```python
from panelmark_tui.interactions import RadioList

sh.assign("size", RadioList({
    "Small":  "s",
    "Medium": "m",
    "Large":  "l",
}))
result = sh.run()   # returns "s", "m", or "l"
```

**Keys:** `↑`/`↓` or `k`/`j` to navigate; `Page Up`/`Page Down` to jump by a
full page; `Home`/`End` to jump to the first/last item; `Enter` or `Space` to
accept.

**`get_value()`:** returns the **value** of the currently selected item.

**`set_value(value)`:** moves the cursor to the item with the given value.

**`signal_return()`:** returns `(True, value)` after `Enter` or `Space` is
pressed.

---

## TableView

A multi-column read-only display table.  Renders a sticky header row followed
by scrollable data rows.  Active row is highlighted when focused.

```python
TableView(columns: list, rows: list)
```

- `columns` — `[(header_label, width_in_chars), ...]`
- `rows` — list of rows; each row is a list of values (converted via `str()`)

Columns are rendered exactly `width_in_chars` characters wide and separated by
`│`.

```python
from panelmark_tui.interactions import TableView

sh.assign("results", TableView(
    columns=[("Name", 20), ("Status", 10), ("Score", 6)],
    rows=[
        ["Alice",   "active", "95"],
        ["Bob",     "idle",   "72"],
        ["Charlie", "active", "88"],
    ],
))
```

**Keys:** `↑`/`↓` or `k`/`j` to move the active row; `Page Up`/`Page Down` to
jump by one page; `Home`/`End` to jump to the first/last row.

**`get_value()`:** returns the 0-based active row index.

**`set_value(index)`:** moves the cursor to the given row index (clamped).

**Focusable:** `True` — assign to a region that can receive keyboard focus.

---

## Function

**Escape hatch.** `Function` does not follow the standard `get_value()` /
`set_value()` / `signal_return()` contract.  It exists for custom low-level
rendering and key handling where none of the built-in interactions fit.  Do not
use it as a model when designing new interactions.

`get_value()` returns an internal `_value` that the handler does not manage
through a first-class API.  `set_value()` sets that same private value.
`signal_return()` is not implemented — `Function` never causes the shell to
exit on its own.

```python
Function(handler: Callable)
```

The handler signature: `handler(shell, context, key)` where:
- `shell` — the `Shell` instance (or `None` before assignment)
- `context` — a `RenderContext` with `width`, `height`, `supports(...)`
- `key` — `None` on render calls, a key string on keypress

The handler should return `list[DrawCommand]` on render calls (key is `None`), or `None`
on key events.

```python
from panelmark_tui.interactions import Function
from panelmark.draw import WriteCmd

def clock_handler(shell, context, key):
    if key is None:   # render
        import datetime
        now = datetime.datetime.now().strftime("%H:%M:%S")
        return [WriteCmd(row=0, col=0, text=now.ljust(context.width))]
    # key events: do nothing

sh.assign("clock", Function(clock_handler))
```

### When to use `Function`

Use `Function` only when no built-in interaction fits and you need full control over
drawing and key handling.  Good candidates:

- Custom visualisations (graphs, progress bars, ASCII art) that don't map to any
  standard widget
- One-off display regions that read external state on every render call
- Wrappers around third-party drawing code

**When not to use `Function`:**  if you find yourself re-implementing navigation,
selection, or text editing inside a handler, consider whether a built-in interaction
or a new subclass of `_ScrollableList` would be a better fit.  `Function` is a
last resort, not a default choice.

---

## FormInput

A structured data-entry form with multiple typed fields, validation, and a Submit button.

```python
FormInput(fields: dict)
```

Each entry in `fields` maps a variable name to a field definition dict:

```python
fields = {
    "name": {
        "type":        "str",          # 'str', 'int', 'float', 'bool', 'choices'
        "descriptor":  "Your name",    # label shown in the form
        "default":     "",             # optional initial value
        "placeholder": "Enter name",   # hint shown when empty
        "required":    True,           # fail validation if empty
        "validator":   lambda v: True if len(v) >= 2 else "Too short",
    },
    "age": {
        "type":       "int",
        "descriptor": "Age",
        "required":   True,
        "validator":  lambda v: True if 0 < v < 150 else "Must be 1–149",
    },
    "role": {
        "type":    "choices",
        "descriptor": "Role",
        "options": ["Admin", "User", "Guest"],
        "default": "User",
    },
    "active": {
        "type":       "bool",
        "descriptor": "Active",
        "default":    True,
    },
}

form = FormInput(fields)
sh.assign("form", form)
result = sh.run()   # dict with field values, or None on cancel
```

**Field types:**

| Type | Input method | Value |
|------|--------------|-------|
| `str` | Type freely | `str` or `None` if empty |
| `int` | Digits and leading `-` only | `int` or `None` if empty |
| `float` | Digits, `-`, and one `.` | `float` or `None` if empty |
| `bool` | `←`/`→` or Space to toggle | `bool` |
| `choices` | `←`/`→` or Space to cycle | selected option `str` |

**Validator:** a callable that receives the coerced value and returns `True` (pass) or
an error message string.

**Keys:** `↑`/`↓` to move between fields; field-specific keys for editing; `Enter` on
Submit (or on a `bool`/`choices` field) to activate; `Tab`/`Shift+Tab` for focus.

**Value:** `dict[str, value]` on successful submit (coerced to the declared type);
`None` on cancel.

---

## StatusMessage

A display-only single-line status / validation feedback area. Not focusable.

```python
StatusMessage()
```

Update via `shell.update(name, value)` where value is:
- `None` or `""` — clear (show blank)
- `("error", "message")` — red `✗ message`
- `("success", "message")` — green `✓ message`
- `("info", "message")` — default colour `ℹ message`
- A plain `str` — treated as `("info", str)`

```python
status = StatusMessage()
sh.assign("status", status)

sh.update("status", ("error",   "File not found"))
sh.update("status", ("success", "Saved successfully"))
sh.update("status", ("info",    "3 items selected"))
sh.update("status", None)   # clear
```

**Value:** `(style, message)` tuple, or `None` if blank.

---

## Scrolling behaviour

`MenuReturn`, `MenuFunction`, and `CheckBox` all inherit from
`_ScrollableList`, which provides automatic scroll tracking.

**Navigation keys supported by all three:**

| Key | Action |
|-----|--------|
| `↑` / `k` | Move up one item |
| `↓` / `j` | Move down one item |
| `Page Up` | Jump up by one full page (viewport height) |
| `Page Down` | Jump down by one full page |
| `Home` | Jump to the first item |
| `End` | Jump to the last item |

The scroll offset is kept in sync automatically: the viewport always contains the active
item. It is updated on every `render()` call, so the interaction correctly tracks the
viewport even if the terminal is resized.
