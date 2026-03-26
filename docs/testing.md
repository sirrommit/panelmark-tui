# Testing

panelmark-tui provides testing utilities that let you test interactions and shells without
a real terminal. Import them from `panelmark_tui.testing`.

```python
from panelmark_tui.testing import MockTerminal, make_key
```

---

## Testing Interactions

Because `Interaction.render()` returns a plain `list[DrawCommand]`, you can test visual
output without any terminal dependency.

```python
from panelmark.draw import RenderContext, WriteCmd, FillCmd, CursorCmd

def ctx(width=40, height=10):
    """Helper: RenderContext with standard capabilities."""
    return RenderContext(
        width=width,
        height=height,
        capabilities=frozenset({'unicode', 'cursor', 'color'}),
    )
```

### Asserting on render output

```python
from panelmark_tui.interactions import MenuReturn

def test_menu_renders_items():
    menu = MenuReturn({"Alpha": 1, "Beta": 2, "Gamma": 3})
    cmds = menu.render(ctx(width=20, height=5), focused=False)
    texts = [c.text for c in cmds if isinstance(c, WriteCmd)]
    assert any("Alpha" in t for t in texts)
    assert any("Beta"  in t for t in texts)
    assert any("Gamma" in t for t in texts)

def test_menu_highlights_active_when_focused():
    menu = MenuReturn({"Alpha": 1, "Beta": 2})
    cmds = menu.render(ctx(), focused=True)
    # First item (active by default) should be reversed
    active_cmds = [c for c in cmds if isinstance(c, WriteCmd)
                   and c.style and c.style.get("reverse")]
    assert len(active_cmds) == 1
    assert "Alpha" in active_cmds[0].text

def test_textbox_places_cursor_when_focused():
    tb = TextBox("hello")
    cmds = tb.render(ctx(), focused=True)
    cursor_cmds = [c for c in cmds if isinstance(c, CursorCmd)]
    assert len(cursor_cmds) == 1
```

### Testing key handling

```python
def test_menu_navigates_down():
    menu = MenuReturn({"A": 1, "B": 2, "C": 3})
    changed, value = menu.handle_key("KEY_DOWN")
    assert menu._active_index == 1

def test_menu_returns_value_on_enter():
    menu = MenuReturn({"Yes": True, "No": False})
    changed, value = menu.handle_key("KEY_ENTER")
    assert value is True

def test_checkbox_toggles():
    cb = CheckBox({"opt1": False, "opt2": True})
    changed, state = cb.handle_key("KEY_ENTER")
    assert changed is True
    assert state["opt1"] is True   # toggled from False
```

### Testing scroll behaviour

`prime()` is a helper that forces a render so the interaction knows its viewport height
before navigation:

```python
def prime(interaction, height):
    interaction.render(RenderContext(width=40, height=height), focused=False)
    return interaction

def test_scroll_follows_active_item():
    menu = MenuReturn({f"Item {i}": i for i in range(20)})
    prime(menu, height=5)
    for _ in range(10):
        menu.handle_key("KEY_DOWN")
    # Active item must be within the viewport
    assert menu._active_index - menu._scroll_offset < 5
```

---

## MockTerminal

`MockTerminal` simulates a blessed terminal for tests that involve the renderer or the
full shell event loop.

```python
from panelmark_tui.testing import MockTerminal

term = MockTerminal(width=80, height=24)
```

`MockTerminal` supports:
- `term.width`, `term.height` — configurable terminal dimensions
- `term.move(row, col)` — returns a positioning string (or empty string in tests)
- `term.reverse`, `term.bold`, `term.normal` — style attributes (empty strings)
- `term.number_of_colors` — colour count (default: 8)
- `term.italic` — italic flag (default: `False`)

```python
from panelmark_tui.renderer import Renderer
from panelmark.layout import Region

def test_renderer_calls_interaction():
    from panelmark.draw import WriteCmd, RenderContext

    term = MockTerminal(width=80, height=24)
    renderer = Renderer(term)
    region = Region(name="test", row=0, col=0, width=20, height=5)
    called = []

    class MyInteraction:
        def render(self, context, focused=False):
            called.append((context, focused))
            return [WriteCmd(row=0, col=0, text=" " * context.width)]

    renderer.render_region(region, MyInteraction(), focused=True)
    assert len(called) == 1
    assert isinstance(called[0][0], RenderContext)
    assert called[0][1] is True
```

---

## make_key

`make_key` creates a fake blessed `Keystroke` object for use in tests that call code
expecting a blessed key event (rather than a plain string):

```python
from panelmark_tui.testing import make_key

key = make_key("KEY_ENTER")
key = make_key("a")           # printable character
key = make_key("\x1b")        # Escape
```

Most tests that call `handle_key()` directly pass plain strings like `"KEY_DOWN"` or
`"a"`. Use `make_key` only when the code under test inspects `key.is_sequence` or
`key.name` (i.e. blessed-specific attributes).

---

## Testing Widgets

Widgets run a full shell event loop internally. Test them by creating a `MockTerminal`,
attaching it to a parent shell, and calling `.show()` with that parent shell.

```python
from panelmark_tui import Shell
from panelmark_tui.testing import MockTerminal
from panelmark_tui.widgets import Alert

def make_parent(keys, width=80, height=24):
    """Return a minimal Shell whose terminal replays a fixed key sequence."""
    term = MockTerminal(width=width, height=height, keys=keys)
    sh = Shell("|{$dummy$}|")
    sh.terminal = term
    return sh

def test_alert_ok_returns_true():
    parent = make_parent(keys=["KEY_ENTER"])
    result = Alert(title="Hi", message_lines=["Hello"]).show(parent_shell=parent)
    assert result is True

def test_alert_escape_returns_none():
    parent = make_parent(keys=["\x1b"])
    result = Alert(title="Hi", message_lines=["Hello"]).show(parent_shell=parent)
    assert result is None
```

The key point: inject the terminal via `parent_shell.terminal`, **not** as a `_terminal`
kwarg to the widget constructor (that parameter does not exist on widget classes).

For more complete patterns see `tests/test_widgets.py` in the repository.

---

## Writing Tests without Terminals

The core rule: **interact via `handle_key()`, assert via `render()`**.

```python
def test_status_message_shows_error():
    status = StatusMessage()
    status.set_value(("error", "File not found"))
    ctx = RenderContext(width=40, height=1,
                       capabilities=frozenset({"color"}))
    cmds = status.render(ctx)
    write_cmds = [c for c in cmds if isinstance(c, WriteCmd)]
    assert any("File not found" in c.text for c in write_cmds)
    assert any(c.style and c.style.get("color") == "red" for c in write_cmds)

def test_status_message_clears():
    status = StatusMessage()
    status.set_value(("error", "Oops"))
    status.set_value(None)
    cmds = status.render(RenderContext(width=40, height=1))
    # Should produce only FillCmd (blank)
    assert all(isinstance(c, FillCmd) for c in cmds)
```
