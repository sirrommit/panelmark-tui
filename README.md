# panelmark-tui

**panelmark-tui** is the blessed-powered terminal renderer for
[panelmark](https://github.com/sirrommit/panelmark) shells. It turns a panelmark layout
definition and a set of interaction assignments into a live, keyboard-driven TUI application.

---

## What is real today

| Category | Status |
|----------|--------|
| Shell layout (ASCII-art DSL) | ✅ Fully working |
| Fullscreen event loop (`Shell.run()`) | ✅ Fully working |
| Modal overlay (`Shell.run_modal()`) | ✅ Fully working |
| Tab / Shift+Tab focus movement | ✅ Fully working |
| `MenuReturn`, `MenuFunction`, `MenuHybrid` | ✅ Working — up/down/j/k/Enter navigation |
| `TextBox`, `ListView`, `CheckBox`, `Function`, `FormInput`, `StatusMessage` | ✅ Working |
| `SubList` | ⚠️ Works as a **static indented list** — no expand/collapse, no tree navigation |
| Paging keys (Page Up/Down, Home/End) in menus | ✅ Implemented in all list interactions |
| 7 modal widgets (`Confirm`, `Alert`, `InputPrompt`, `ListSelect`, `FilePicker`, `DatePicker`, `Progress`) | ✅ Working |
| Panel headings (`__text__` syntax) | ⚠️ Parsed and stored, **not rendered** by this package |
| Equal-width fill splits (all fill-width columns) | ✅ Columns share space equally (differ by at most 1 char) |

See [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) for the full list.

---

## What it provides

| Component | Description |
|-----------|-------------|
| `Shell` | Full terminal event loop (fullscreen and modal) |
| 10 interaction types | `MenuFunction`, `MenuReturn`, `MenuHybrid`, `TextBox`, `ListView`, `SubList`, `CheckBox`, `Function`, `FormInput`, `StatusMessage` |
| 7 modal widgets | `Confirm`, `Alert`, `InputPrompt`, `ListSelect`, `FilePicker`, `DatePicker`, `Progress` |
| Testing utilities | `MockTerminal`, `make_key` for test suites that don't need a real terminal |

---

## Installation

```
pip install panelmark-tui
```

Dependencies: `panelmark`, `blessed`

---

## Quick start

```python
from panelmark_tui import Shell
from panelmark_tui.interactions import MenuReturn, StatusMessage

LAYOUT = """
|=== <bold>Pick a colour</> ===|
|{10R $menu$                   }|
|------------------------------|
|{2R  $status$                 }|
|==============================|
"""

def main():
    sh = Shell(LAYOUT)
    sh.assign("menu", MenuReturn({
        "Red":   "red",
        "Green": "green",
        "Blue":  "blue",
    }))
    sh.assign("status", StatusMessage())
    sh.update("status", ("info", "Arrow keys to navigate, Enter to select"))

    result = sh.run()
    print(f"You chose: {result}")

if __name__ == "__main__":
    main()
```

Run it:
```
python myapp.py
```

---

## Using modal widgets

All widgets follow the same pattern:

```python
Widget(options...).show(parent_shell=sh) -> result
```

```python
from panelmark_tui.widgets import Confirm, Alert, InputPrompt

# Inside a running shell event handler:
def handle_delete(sh):
    confirmed = Confirm(
        title="Delete file",
        message_lines=["Are you sure you want to delete this file?",
                       "This cannot be undone."],
    ).show(parent_shell=sh)

    if confirmed:
        do_delete()
        Alert(title="Done", message_lines=["File deleted."]).show(parent_shell=sh)
    else:
        sh.update("status", ("info", "Cancelled"))
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](docs/getting-started.md) | Step-by-step guide: building your first TUI |
| [Interactions](docs/interactions.md) | All 10 built-in interaction types with examples |
| [Widgets](docs/widgets.md) | All 7 modal widgets with full API reference |
| [Testing](docs/testing.md) | Testing interactions and shells without a real terminal |

Also see the panelmark core docs for the layout language and custom interaction protocol:

| Document | Description |
|----------|-------------|
| [Shell Language](../panelmark/docs/shell-language.md) | ASCII-art layout syntax reference |
| [Draw Commands](../panelmark/docs/draw-commands.md) | `DrawCommand`, `RenderContext`, style dict |
| [Custom Interactions](../panelmark/docs/custom-interactions.md) | Implementing the `Interaction` ABC |

---

## License

MIT
