# Built-in Interactions

panelmark-tui provides 12 built-in interaction types, all importable from
`panelmark_tui.interactions`.

```python
from panelmark_tui.interactions import (
    MenuFunction, MenuReturn, MenuHybrid,
    TextBox,
    ListView, SubList,
    CheckBox,
    Function,
    FormInput,
    StatusMessage,
    RadioList,
    TableView,
)
```

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

---

## MenuHybrid

A scrollable menu where each item is either a **callable** or a **plain value**.

```python
MenuHybrid(items: dict)
```

- If the selected item's value is **callable**, it is called as `callback(shell)` and the
  shell continues running. Use this for items with side effects.
- If the selected item's value is **not callable**, the shell exits and `shell.run()`
  returns that value. Use this for items that should close the shell.

```python
from panelmark_tui.interactions import MenuHybrid

def say_hello(sh):
    sh.update("status", ("success", "Hello!"))

menu = MenuHybrid({
    "Say Hello": say_hello,   # callable → runs, stays open
    "About":     show_about,  # callable → runs, stays open
    "Quit":      "quit",      # plain value → shell.run() returns "quit"
})
result = sh.run()   # returns "quit" when Quit is selected
```

**Keys:** same navigation as `MenuReturn` (including `Page Up`/`Page Down`/`Home`/`End`).

---

## TextBox

A multi-line (or single-line) text input with cursor navigation and optional word wrap.

```python
TextBox(
    initial: str = "",
    wrap: Literal["word", "anywhere", "extend"] = "word",
    readonly: bool = False,
)
```

**Wrap modes:**
- `"word"` — wrap at word boundaries (default)
- `"anywhere"` — wrap mid-word when the line is full
- `"extend"` — no wrap; newlines only on `Enter` (best for single-line inputs)

```python
from panelmark_tui.interactions import TextBox

# Single-line entry field
entry = TextBox(wrap="extend")
sh.assign("entry", entry)

# Read-only display
display = TextBox(initial="some text", readonly=True)
sh.assign("display", display)
```

**Keys:** printable characters to type; `Backspace`/`Delete` to erase; `←`/`→` to move
cursor; `Home`/`End` to jump to buffer start/end; `Enter` to insert newline (except
`readonly=True`).

**Value:** `str` — the full text content including any newlines.

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

## SubList

> **Deprecated.** `SubList` is a static indented display widget with no expand/collapse
> and no keyboard navigation. For interactive tree browsing use
> [`TreeView`](#treeview) instead.

A display-only indented list view. Items may be nested lists; nested items are rendered
with indentation to show hierarchy. Not focusable — updated programmatically via
`shell.update()`.

```python
SubList(items)
```

`items` is a `list` where any element may itself be a `list` to create an indented
sub-group. Nesting can go to any depth.

```python
from panelmark_tui.interactions import SubList

sections = SubList([
    "Documents",
    ["report.pdf", "notes.txt"],      # indented under Documents
    "Pictures",
    ["photo1.jpg", "photo2.jpg"],     # indented under Pictures
])
sh.assign("sections", sections)
```

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

An escape hatch for custom rendering and key handling. The handler function is called on
every render and every keypress.

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

`MenuReturn`, `MenuFunction`, `MenuHybrid`, and `CheckBox` all inherit from
`_ScrollableList`, which provides automatic scroll tracking.

**Navigation keys supported by all four:**

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
