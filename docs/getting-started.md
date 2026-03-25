# Getting Started with panelmark-tui

This guide walks you through building a complete TUI application with panelmark-tui, from
layout definition to a working interactive program.

---

## Step 1 — Define the layout

Write a shell definition string using panelmark's ASCII-art syntax. Every line must start
and end with `|`. Use `=` lines for double-line borders, `-` lines for single-line borders.

```python
LAYOUT = """
|=== <bold>Task Manager</> ========|
|{18R $tasks$                      }|
|------------------------------------|
|{2R  $entry$                       }|
|{2R  $status$                      }|
|====================================|
"""
```

This creates four regions:
- `$tasks$` — 18 rows tall, for the task list
- `$entry$` — 2 rows, for typing new tasks
- `$status$` — 2 rows, for status messages

For a full syntax reference see [Shell Language](../../panelmark/docs/shell-language.md).

---

## Step 2 — Create the Shell

```python
from panelmark_tui import Shell

sh = Shell(LAYOUT)
```

`Shell` parses the definition and sets up the layout model. The terminal dimensions are
auto-detected from the actual terminal when `run()` is called.

---

## Step 3 — Assign interactions

Import the interaction types you need and assign one to each named region.

```python
from panelmark_tui.interactions import (
    ListView, TextBox, MenuReturn, StatusMessage
)

task_list = ListView(["Buy groceries", "Write docs", "Ship release"])
entry     = TextBox(wrap="extend")
status    = StatusMessage()

sh.assign("tasks",  task_list)
sh.assign("entry",  entry)
sh.assign("status", status)
```

`assign()` raises `RegionNotFoundError` if the name does not match a region in the layout,
so typos are caught immediately.

---

## Step 4 — Set initial state

Use `shell.update()` to pre-populate regions before the event loop starts:

```python
sh.update("status", ("info", "Tab to move focus · Enter to add task · Ctrl+Q to quit"))
```

---

## Step 5 — Wire up interactions

Use `shell.on_change()` to react to value changes, and `shell.bind()` to mirror one region
into another:

```python
# When the entry TextBox changes, update the status
def on_entry_change(value):
    if value.strip():
        sh.update("status", ("info", f"Press Enter to add: {value.strip()!r}"))
    else:
        sh.update("status", None)

sh.on_change("entry", on_entry_change)
```

Or use `MenuFunction` to attach callbacks directly to menu items (see
[Interactions](interactions.md)).

---

## Step 6 — Run the event loop

```python
result = sh.run()
```

`run()` takes over the terminal in fullscreen mode:
- Clears and redraws the screen on start
- Automatically handles terminal resize events
- Returns when the user presses Escape or Ctrl+Q, or when an interaction signals exit

The return value is whatever the exiting interaction's `signal_return()` provides (usually
the selected item, submitted form, or `None` on cancel).

---

## Step 7 — Handle the result

```python
if result is not None:
    print(f"Result: {result}")
```

---

## Complete example

```python
from panelmark_tui import Shell
from panelmark_tui.interactions import ListView, TextBox, StatusMessage

LAYOUT = """
|=== <bold>Task Manager</> ===|
|{15R $tasks$                 }|
|-----------------------------|
|{2R  $entry$                 }|
|{1R  $status$                }|
|=============================|
"""

def main():
    tasks = ["Buy groceries", "Write docs"]
    sh = Shell(LAYOUT)

    task_view = ListView(tasks[:])
    entry_box = TextBox(wrap="extend")
    status    = StatusMessage()

    sh.assign("tasks",  task_view)
    sh.assign("entry",  entry_box)
    sh.assign("status", status)
    sh.update("status", ("info", "Tab · Enter to add · Ctrl+Q to quit"))

    # Add a task when Enter is pressed in the entry box
    def on_change(value):
        if '\n' in value:
            text = value.replace('\n', '').strip()
            if text:
                tasks.append(text)
                sh.update("tasks", tasks[:])
            sh.update("entry", "")

    sh.on_change("entry", on_change)

    sh.run()
    print("Goodbye!")

if __name__ == "__main__":
    main()
```

---

## Modal popups

To display a modal dialog from inside a running shell — for example from a `MenuFunction`
callback — pass `parent_shell=sh` to the widget's `.show()` method. This ensures the parent
shell's display is restored when the modal closes.

```python
from panelmark_tui.widgets import Confirm

def delete_task(sh, task_name):
    ok = Confirm(
        title="Delete task",
        message_lines=[f"Delete '{task_name}'?"],
    ).show(parent_shell=sh)
    if ok:
        tasks.remove(task_name)
        sh.update("tasks", tasks[:])
```

See [Widgets](widgets.md) for the full widget API.

---

## Advanced: manual event loop

If you need to control the event loop yourself (for example to integrate with asyncio or
another framework), drive the shell manually:

```python
from panelmark_tui.renderer import Renderer
from panelmark_tui.context import build_render_context
from panelmark_tui.executor import TUICommandExecutor

renderer = Renderer(term)
renderer.full_render(sh.layout, sh.regions, sh.interactions, sh.focus, w, h)

while True:
    key = your_key_source()
    status, value = sh.handle_key(key)
    if status == 'exit':
        break
    # Re-render dirty regions
    for name in sh.dirty_regions:
        region = sh.regions[name]
        interaction = sh.interactions.get(name)
        if interaction:
            renderer.render_region(region, interaction, name == sh.focus)
    sh.mark_all_clean()
```

See [Draw Commands](../../panelmark/docs/draw-commands.md) for the `RenderContext` and
command types used internally.
