"""RadioList interaction — single-select list with radio-button visuals.

Displays items as ``(●) Selected Item`` / ``( ) Other Item``.  The cursor
position *is* the selection; moving the cursor immediately moves the
highlighted radio marker.  Pressing ``Enter`` or ``Space`` signals the
shell to exit and return the selected value.

``get_value()`` returns the **value** (not the label) of the currently
selected item, making it a cleaner alternative to ``CheckBox(mode='single')``
which returns a dict of booleans.

Example::

    from panelmark_tui.interactions import RadioList

    shell.assign("size", RadioList({
        "Small":  "s",
        "Medium": "m",
        "Large":  "l",
    }))
    result = shell.run()   # returns "s", "m", or "l"

Navigation
----------
``↑`` / ``k``           move up one row
``↓`` / ``j``           move down one row
``Page Up``             jump up one viewport
``Page Down``           jump down one viewport
``Home``                first item
``End``                 last item
``Enter`` / ``Space``   accept current selection and return
"""

from panelmark.draw import DrawCommand, RenderContext
from .scrollable import _ScrollableList, _list_nav


class RadioList(_ScrollableList):
    """Single-select radio-button list.

    Parameters
    ----------
    items : dict[str, Any]
        ``{label: value}`` mapping.  The first item is pre-selected.
    """

    def __init__(self, items: dict):
        self._items = dict(items)
        self._labels = list(items.keys())
        self._active_index = 0
        self._scroll_offset = 0
        self._wants_exit = False
        self._exit_value = None

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        all_lines = []
        for i, label in enumerate(self._labels):
            marker = '(●)' if i == self._active_index else '( )'
            all_lines.append(f'{marker} {label}')

        viewport = all_lines[self._scroll_offset:self._scroll_offset + context.height]
        return self._build_rows(viewport, context, focused, active_marker=False)

    def handle_key(self, key) -> tuple:
        self._wants_exit = False
        new_idx = _list_nav(key, self._active_index, len(self._labels),
                            self._last_height)
        if new_idx is not None:
            self._active_index = new_idx
            self._clamp_scroll()
            return True, self.get_value()
        if key in ('KEY_ENTER', ' ') or key in ('\n', '\r'):
            return self._select()
        return False, self.get_value()

    def _select(self):
        if self._labels:
            self._exit_value = self._items[self._labels[self._active_index]]
            self._wants_exit = True
            return True, self.get_value()
        return False, self.get_value()

    def get_value(self):
        """Return the value of the currently selected item."""
        if self._labels:
            return self._items[self._labels[self._active_index]]
        return None

    def set_value(self, value) -> None:
        """Move the cursor to the item with the given value."""
        for i, label in enumerate(self._labels):
            if self._items[label] == value:
                self._active_index = i
                self._clamp_scroll()
                return

    def signal_return(self) -> tuple:
        if self._wants_exit:
            return True, self._exit_value
        return False, None
