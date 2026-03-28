# Built-in Widgets

panelmark-tui ships 10 built-in widgets. Widgets are renderer-side convenience components
for common TUI tasks. They are not part of the portable `panelmark` core contract — they
are specific to the `panelmark-tui` blessed renderer.

---

## Widget families

### Standard modal dialogs

`Confirm`, `Alert`, `InputPrompt`, `ListSelect`, `FilePicker`, `DatePicker`, `DataclassForm`

These are shell-composed widgets. Each builds a small `Shell` internally and runs it as a
modal overlay. They block until the user makes a choice and return a value (or `None` on
cancel).

```python
result = Widget(options...).show(parent_shell=sh)
```

All modal dialog widgets:
- Are auto-centred on screen by default
- Restore the parent shell's display after closing
- Return `None` on Escape or Ctrl+Q (unless noted otherwise)
- Accept `parent_shell=sh` to integrate with a running TUI

### Renderer-managed utility overlays

`Progress`, `Toast`, `Spinner`

These widgets manage their own render cycle. `Toast` displays briefly then removes itself;
`Progress` and `Spinner` use a context-manager pattern where the caller drives updates
synchronously.

```python
# Context-manager pattern
with Progress(title="...", total=n).show(sh) as prog:
    ...
```

These widgets always return `None` — cancellation is checked via `.cancelled`.

---

## Import

```python
from panelmark_tui.widgets import (
    Confirm, Alert, InputPrompt,
    ListSelect, FilePicker, DatePicker,
    DataclassForm,
    Progress, Toast, Spinner,
)
```

---

## Confirm

Asks the user to confirm or deny an action. A message area and caller-defined buttons.

```python
Confirm(
    title: str = "Confirm",
    message_lines: list[str] = [],
    buttons: dict = {"OK": True, "Cancel": False},
    width: int = 40,
)
```

```python
result = Confirm(
    title="Delete account",
    message_lines=[
        "This will permanently delete your account.",
        "All data will be lost.",
    ],
    buttons={"Delete": "delete", "Keep": "keep", "Cancel": None},
).show(parent_shell=sh)

if result == "delete":
    do_delete()
```

**Returns:** the dict value for the selected button, or `None` on Escape/Ctrl+Q.

**Layout:** 2-row message area, separator, button row.
**Height:** auto-detected (~7 rows).

---

## Alert

Informational or warning popup with a single OK button. Blocks until dismissed.

```python
Alert(
    title: str = "Alert",
    message_lines: list[str] = [],
    width: int = 40,
)
```

```python
Alert(
    title="Error",
    message_lines=["Could not read file:", "  /etc/myconfig.conf"],
).show(parent_shell=sh)
```

**Returns:** `True` when OK is pressed, `None` on Escape/Ctrl+Q.

**Layout:** 3-row message area, separator, OK button.
**Height:** auto-detected (~7 rows).

---

## InputPrompt

Asks the user to type a single line of text.

```python
InputPrompt(
    title: str = "Input",
    prompt_lines: list[str] = [],
    initial: str = "",
    width: int = 50,
)
```

```python
name = InputPrompt(
    title="Rename",
    prompt_lines=["Enter a new name for this item:"],
    initial="old_name.txt",
).show(parent_shell=sh)

if name is not None:
    rename(name)
```

**Returns:** the entered text string on OK or Enter (may be empty `""`), `None` on
Cancel/Escape/Ctrl+Q.

**Layout:** 2-row prompt, separator, 2-row text entry, separator, OK/Cancel buttons.
**Height:** auto-detected (~9 rows).

**Notes:**
- Focus opens on the text entry box.
- `Enter` in the entry box **submits immediately** (the box uses `enter_mode="submit"`).
- `Tab` also moves focus to the button row if you prefer to use the OK button.

---

## ListSelect

Lets the user pick one item (single mode) or multiple items (multi mode) from a scrollable
list.

```python
ListSelect(
    title: str = "Select",
    prompt_lines: list[str] = [],
    items: list | dict = [],
    multi: bool = False,
    width: int = 40,
)
```

### Single mode (`multi=False`)

Selecting an item immediately returns its value. The dialog closes on selection.

```python
colour = ListSelect(
    title="Pick colour",
    prompt_lines=["Choose a background colour:"],
    items=["Red", "Green", "Blue", "Yellow"],
).show(parent_shell=sh)
```

Pass a `dict` to return values other than the label:

```python
colour = ListSelect(
    items={"Red": "#FF0000", "Green": "#00FF00", "Blue": "#0000FF"},
).show(parent_shell=sh)
```

**Returns:** the selected item (label string for a list; dict value for a dict), or
`None` on Escape/Ctrl+Q.

### Multi mode (`multi=True`)

Shows checkboxes. The user checks items and presses OK to confirm.

```python
tags = ListSelect(
    title="Add tags",
    items={"urgent": True, "bug": False, "feature": False, "docs": False},
    multi=True,
).show(parent_shell=sh)

if tags:
    apply_tags({k for k, v in tags.items() if v})
```

Pass a `list` to start with all unchecked; pass a `dict[str, bool]` to set initial states.

**Returns:** `dict[str, bool]` of all items and their final checked states on OK,
`None` on Cancel/Escape/Ctrl+Q.

**Height:** auto-detected (~14 rows single / ~16 rows multi).

---

## FilePicker

Browse the filesystem and select a file or directory.

```python
FilePicker(
    start_dir: str | None = None,     # defaults to os.getcwd()
    title: str = "Select File",
    dirs_only: bool = False,          # hide files, show only directories
    filter: str = "*",                # initial glob pattern
    width: int = 70,
)
```

```python
path = FilePicker(
    start_dir="/home/user/projects",
    title="Open project",
    filter="*.py",
).show(parent_shell=sh)

if path:
    open_project(path)
```

```python
# Directory picker mode
dest = FilePicker(
    title="Choose destination",
    dirs_only=True,
).show(parent_shell=sh)
```

**Returns:** absolute path string on OK, `None` on Cancel/Escape/Ctrl+Q.

**Layout:** two-column panel (directory tree left, file list right), filter field
(glob pattern), filename field, status bar, OK/Cancel buttons.

**Interaction:**
- Navigate either panel with `↑`/`↓`; `Enter` on a directory **navigates into it**
- The file list is filtered live by the glob pattern typed in the filter field
- Selecting a file copies its path into the filename field
- The filename field can also be typed in directly
- `Tab` moves focus between panels and fields

---

## DatePicker

Presents a monthly calendar for date selection.

```python
DatePicker(
    initial: datetime.date | None = None,   # defaults to today
    title: str = "Select Date",
    width: int = 30,
)
```

```python
import datetime

due_date = DatePicker(
    title="Set due date",
    initial=datetime.date.today() + datetime.timedelta(days=7),
).show(parent_shell=sh)

if due_date:
    set_due_date(due_date)
```

**Returns:** `datetime.date` on OK, `None` on Cancel/Escape/Ctrl+Q.

**Layout:** month/year navigation row, calendar grid (8 rows), OK/Cancel buttons.
**Height:** auto-detected (~14 rows).

**Keys:**
- `↑`/`↓`/`←`/`→` — move the highlighted date one day/week at a time
- `←`/`→` in the nav row — previous/next month
- `Enter` — select the highlighted date
- Calendar wraps across month boundaries when navigating days

**Visual states:**
- Selected (cursor) date: bold + reverse
- Today's date: bold
- Other dates: plain

---

## DataclassForm

Modal form widget driven by a dataclass instance. Presents the dataclass's fields as
editable form rows with optional action buttons. A thin modal wrapper around
[`DataclassFormInteraction`](interactions.md#dataclassforminteraction).

```python
DataclassForm(
    dc_instance,
    title: str = "Edit",
    actions: list | None = None,
    on_change: callable | None = None,
    width: int = 60,
)
```

```python
import dataclasses
from panelmark_tui.widgets import DataclassForm

@dataclasses.dataclass
class Config:
    host: str = "localhost"
    port: int = 8080
    debug: bool = False

cfg = Config()
result = DataclassForm(
    cfg,
    title="Server Settings",
    actions=[
        {"label": "Save", "shortcut": "s",
         "action": lambda vals: {**vals, "_saved": True}},
        {"label": "Cancel", "shortcut": "q", "action": lambda vals: None},
    ],
).show(parent_shell=sh)

if result and result.get("_saved"):
    apply_config(result)
```

**Returns:** a dict of field values on submit, or `None`/`False` depending on the action
that triggered exit.  Each action's return value becomes the shell exit value.

**When to use the interaction directly:** if you need the form embedded in a larger shell
(alongside other regions) rather than as a standalone popup, assign
`DataclassFormInteraction` to a region directly.

---

## Progress

Displays a progress bar during a long operation. Driven programmatically from the
caller's loop.

```python
Progress(
    title: str = "Progress",
    total: int = 100,
    cancellable: bool = True,
    width: int = 50,
)
```

**Usage — context manager (recommended):**

```python
with Progress(title="Importing data", total=len(records)).show(sh) as prog:
    for i, record in enumerate(records, 1):
        process(record)
        prog.set_progress(i, f"Processing record {i}/{len(records)}")
        if prog.cancelled:
            break
```

**`_ProgressHandle` API** (the object yielded by the context manager):

| Method / Property | Description |
|-------------------|-------------|
| `prog.set_progress(n, message="")` | Advance bar to step `n` and update the message text |
| `prog.cancelled` | `True` if the user clicked Cancel |

**Returns:** `None` always (use `prog.cancelled` to check for cancellation).

**Layout:** 2-row message area, separator, 2-row progress bar, separator, Cancel button.
**Height:** 9 rows (cancellable) or 7 rows (non-cancellable).

**Notes:**
- `Progress` manages its own render cycle — `set_progress()` pushes updates
  synchronously without waiting for a keypress.
- The bar renders as `[████████░░░░░░] 55%` using Unicode block characters.

---

## Toast

Transient overlay notification that auto-dismisses after a configurable timeout
or on any keypress.  Useful when there is no `$status$` region in the current
shell.

```python
Toast(
    message: str,
    title: str = "Notice",
    duration: float = 2.0,
    width: int = 40,
)
```

```python
from panelmark_tui.widgets import Toast

def handle_save(sh):
    save_file()
    Toast(message="File saved!", duration=1.5).show(parent_shell=sh)
```

**Returns:** `None` always.

**Layout:** title border, 1-row message, bottom border.
**Height:** 3 rows (fixed).

**Notes:**
- Dismisses after `duration` seconds **or** on the first keypress, whichever
  comes first.
- Does not wait for any specific key — any key press dismisses.

---

## Spinner

Indeterminate-progress popup for operations with no known total.  Like
`Progress` but shows an animated spinner instead of a fill bar.

```python
Spinner(
    title: str = "Working…",
    cancellable: bool = True,
    width: int = 50,
)
```

**Usage — context manager:**

```python
from panelmark_tui.widgets import Spinner

def do_work(sh):
    with Spinner(title="Scanning…").show(parent_shell=sh) as spin:
        for path in paths:
            scan(path)
            spin.tick(f"Scanning {path}")
            if spin.cancelled:
                break
```

**`_SpinnerHandle` API** (the object yielded by the context manager):

| Method / Property | Description |
|-------------------|-------------|
| `spin.tick(message="")` | Advance animation frame; optionally update status text |
| `spin.cancelled` | `True` if the user pressed Escape, Ctrl+Q, or Cancel |

**Returns:** `None` always (use `spin.cancelled` to check for cancellation).

**Layout:** spinner row, separator, Cancel button (if `cancellable=True`).
**Height:** 4 rows (non-cancellable) or 6 rows (cancellable).

**Animation:** Braille spinner frames (`⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`), 10 distinct frames.

---

## Positioning

By default, modal dialog widgets are centred on screen. Pass explicit `row`, `col`, or
`width` to `.show()` to override position:

```python
Alert(message_lines=["Done"]).show(
    parent_shell=sh,
    row=5,
    col=10,
    width=30,
)
```

Position overrides are handled by each widget's `.show()` implementation. Modal
shell-based widgets forward them to their internal `Shell.run_modal()` call.
Renderer-managed utility widgets (`Progress`, `Toast`, `Spinner`) handle positioning
in their own render cycle.
