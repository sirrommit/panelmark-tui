# panelmark-tui

**panelmark-tui** is the blessed-powered terminal renderer for
[panelmark](https://github.com/sirrommit/panelmark) shells. It turns a panelmark layout
definition and a set of interaction assignments into a live, keyboard-driven TUI application.

**Compatibility:** `portable-library-compatible` — implements all 8 required portable
interactions and all 6 required portable widgets as defined in the
[renderer spec](https://github.com/sirrommit/panelmark-docs/blob/main/docs/renderer-spec/overview.md).

---

## What is real today

| Category | Status |
|----------|--------|
| Shell layout (ASCII-art DSL) | ✅ Fully working |
| Fullscreen event loop (`Shell.run()`) | ✅ Fully working |
| Modal overlay (`Shell.run_modal()`) | ✅ Fully working |
| Tab / Shift+Tab focus movement | ✅ Fully working |
| `MenuReturn`, `MenuFunction` | ✅ Working — up/down/j/k/Enter/Page Up/Page Down/Home/End navigation |
| `TextBox`, `ListView`, `CheckBox`, `Function`, `FormInput`, `StatusMessage` | ✅ Working |
| `TreeView` | ✅ Interactive collapsible tree — expand/collapse, full keyboard navigation |
| Paging keys (Page Up/Down, Home/End) in menus | ✅ Implemented in all list interactions |
| `RadioList` interaction | ✅ Single-select with `(●)` / `( )` visuals; returns value on Enter/Space |
| `TableView` interaction | ✅ Multi-column display table; sticky header; scrollable; focusable |
| `DataclassFormInteraction`, `DataclassForm` | ✅ Dataclass-driven form interaction and modal widget |
| Standard modal widgets (`Confirm`, `Alert`, `InputPrompt`, `ListSelect`, `FilePicker`, `DatePicker`) | ✅ Working |
| `Progress` widget | ✅ Context-manager progress bar; renderer-managed update cycle |
| `Toast` widget | ✅ Transient overlay notification; auto-dismisses after timeout or keypress |
| `Spinner` widget | ✅ Indeterminate-progress popup; animated braille frames; cancellable |
| Panel headings (`__text__` syntax) | ✅ Rendered as `├─── Heading ───┤` at top of panel content area |
| Equal-width fill splits (all fill-width columns) | ✅ Columns share space equally (differ by at most 1 char) |

See [Known Limitations](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/limitations.md) for the full list.

---

## What it provides

| Component | Description |
|-----------|-------------|
| `Shell` | Full terminal event loop (fullscreen and modal) |
| 13 built-in interactions (8 portable, 5 TUI-specific) | `MenuFunction`, `MenuReturn`, `TextBox`, `ListView`, `CheckBox`, `Function`, `FormInput`, `DataclassFormInteraction`, `StatusMessage`, `TreeView`, `RadioList`, `TableView`, `NestedMenu` |
| 10 built-in widgets (6 portable, 4 TUI-specific) | `Confirm`, `Alert`, `InputPrompt`, `ListSelect`, `FilePicker`, `DatePicker`, `Progress`, `Toast`, `Spinner`, `DataclassForm` |
| Testing utilities | `MockTerminal`, `make_key` for test suites that don't need a real terminal |

Portable interactions and widgets follow the
[portable library spec](https://github.com/sirrommit/panelmark-docs/blob/main/docs/renderer-spec/portable-library.md).
TUI-specific additions are documented in the links below.

### TUI-specific interactions (beyond portable standard)

| Interaction | Description |
|-------------|-------------|
| `MenuFunction` | Menu that calls a function on selection rather than returning |
| `Function` | Generic function-backed interaction |
| `ListView` | Scrollable read-only list |
| `TreeView` | Interactive collapsible tree; expand/collapse; full keyboard navigation |
| `TableView` | Multi-column display table; sticky header; scrollable |

### TUI-specific widgets (beyond portable standard)

| Widget | Description |
|--------|-------------|
| `DatePicker` | Date selection modal |
| `Progress` | Context-manager progress bar; renderer-managed update cycle |
| `Toast` | Transient overlay notification; auto-dismisses after timeout or keypress |
| `Spinner` | Indeterminate-progress popup; animated braille frames; cancellable |

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

## Using widgets

Most widgets follow the modal pattern:

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

Some widgets — `Progress` and `Spinner` — use a context-manager pattern with a
renderer-managed update cycle rather than the simple modal return:

```python
from panelmark_tui.widgets import Progress

with Progress(title="Processing", total=len(items)).show(sh) as prog:
    for i, item in enumerate(items, 1):
        process(item)
        prog.set_progress(i)
        if prog.cancelled:
            break
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/getting-started.md) | Step-by-step guide: building your first TUI with panelmark-tui |
| [Interactions](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/interactions.md) | All 13 built-in interactions with API reference and examples |
| [Widgets](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/widgets.md) | All 10 built-in widgets with full API reference |
| [Testing](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/limitations.md) | Testing interactions with `MockTerminal` and `make_key`; known limitations |
| [Renderer Implementation](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/renderer-implementation.md) | How panelmark-tui satisfies the renderer spec |
| [Portable Library Spec](https://github.com/sirrommit/panelmark-docs/blob/main/docs/renderer-spec/portable-library.md) | Normative spec for all 8 portable interactions and 6 portable widgets |
| [Shell Language](https://github.com/sirrommit/panelmark-docs/blob/main/docs/shell-language/overview.md) | ASCII-art layout syntax reference |
| [Draw Commands](https://github.com/sirrommit/panelmark-docs/blob/main/docs/renderer-spec/contract.md) | `DrawCommand` types, `RenderContext`, style dict |
| [Custom Interactions](https://github.com/sirrommit/panelmark-docs/blob/main/docs/shell-language/examples.md) | Implementing the `Interaction` ABC |
| [Renderer Spec](https://github.com/sirrommit/panelmark-docs/blob/main/docs/renderer-spec/overview.md) | Renderer compatibility contract; portable library; extension policy |
| [Contributing](CONTRIBUTING.md) | Test commands, PYTHONPATH setup, running examples, adding interactions/widgets |

---

## License

MIT
