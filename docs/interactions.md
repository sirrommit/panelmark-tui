# Built-in Interactions

panelmark-tui provides 10 built-in interaction types, all importable from
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

**Keys:** `↑`/`↓` or `k`/`j` to navigate, `Enter` to select, `Page Up`/`Page Down`
for larger jumps, `Home`/`End` to jump to first/last item.

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

**Keys:** same navigation as `MenuReturn`.

---

## MenuHybrid

A scrollable menu that **both** calls a callback **and** returns a value. Useful when you
need side effects (like updating another region) and also want the shell to exit on
selection.

```python
MenuHybrid(items: dict)
```

`items` maps labels to `(callback, return_value)` tuples.

```python
from panelmark_tui.interactions import MenuHybrid

menu = MenuHybrid({
    "Yes": (lambda sh: sh.update("status", ("success", "Confirmed")), True),
    "No":  (lambda sh: sh.update("status", ("info",    "Cancelled")), False),
})
```

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
cursor; `Home`/`End` to jump to line start/end; `Enter` to insert newline (except
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

A hierarchical list view with expandable/collapsible groups. Items can be plain strings or
nested dicts for sub-groups.

```python
SubList(items)
```

`items` can be:
- A `list[str]` — flat list (same as `ListView`)
- A `dict[str, list]` — top-level groups mapping label → children
- Nested combinations for deeper hierarchies

```python
from panelmark_tui.interactions import SubList

tree = SubList({
    "Documents": ["report.pdf", "notes.txt"],
    "Pictures":  ["photo1.jpg", "photo2.jpg"],
})
sh.assign("tree", tree)
```

---

## CheckBox

A scrollable list of checkboxes for multi-selection.

```python
CheckBox(items: dict[str, bool])
```

`items` maps labels to initial checked states.

```python
from panelmark_tui.interactions import CheckBox

options = CheckBox({
    "Enable logging":   True,
    "Dark mode":        False,
    "Auto-save":        True,
    "Spell check":      False,
})
sh.assign("options", options)

# Read the result
result = sh.get("options")   # dict[str, bool]
```

**Keys:** `↑`/`↓` to navigate; `Space` or `Enter` to toggle; `←`/`→` to explicitly
set unchecked/checked.

**Value:** `dict[str, bool]` — label → checked state for all items.

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
`_ScrollableList`, which provides automatic scroll tracking:

- The scroll offset advances when the active item moves below the visible viewport
- The scroll offset decreases when the active item moves above the visible viewport
- Scroll offset is adjusted on every `render()` call

The scroll state uses the height from the most recent `render()` call, so interactions
correctly track the viewport even if the terminal is resized.
