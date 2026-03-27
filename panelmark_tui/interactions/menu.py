from panelmark.draw import DrawCommand, RenderContext
from .scrollable import _ScrollableList, _list_nav


class MenuFunction(_ScrollableList):
    """Menu where each item calls a function when selected.

    ``get_value()`` returns the currently highlighted label (current logical
    state).  Use ``last_activated`` to read which label was most recently
    invoked.
    """

    def __init__(self, items: dict):
        """
        items: dict[str, Callable[[Shell], None]]
        """
        self._items = items
        self._labels = list(items.keys())
        self._active_index = 0
        self._scroll_offset = 0
        self._wants_exit = False
        self._exit_value = None
        self._last_activated = None
        self._shell = None

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        viewport = self._labels[
            self._scroll_offset: self._scroll_offset + context.height
        ]
        return self._build_rows(viewport, context, focused)

    def handle_key(self, key) -> tuple:
        self._wants_exit = False
        new_idx = _list_nav(key, self._active_index, len(self._labels),
                            self._last_height)
        if new_idx is not None:
            self._active_index = new_idx
            self._clamp_scroll()
            return True, self.get_value()
        if key == 'KEY_ENTER' or key in ('\n', '\r'):
            return self._activate()
        return False, self.get_value()

    def _activate(self):
        if self._labels:
            label = self._labels[self._active_index]
            self._last_activated = label
            callback = self._items[label]
            if self._shell is not None:
                callback(self._shell)
            else:
                callback(None)
            return True, self.get_value()
        return False, self.get_value()

    def get_value(self):
        """Return the currently highlighted label (current logical state)."""
        if self._labels:
            return self._labels[self._active_index]
        return None

    @property
    def last_activated(self):
        """The label most recently invoked by the user, or ``None``."""
        return self._last_activated

    def set_value(self, value) -> None:
        """Highlight the item with the given label."""
        if value is not None and value in self._labels:
            self._active_index = self._labels.index(value)
            self._clamp_scroll()

    def signal_return(self) -> tuple:
        if self._wants_exit:
            return True, self._exit_value
        return False, None


class MenuReturn(_ScrollableList):
    """Menu where each item returns a value when selected."""

    def __init__(self, items: dict):
        """
        items: dict[str, Any]
        """
        self._items = items
        self._labels = list(items.keys())
        self._active_index = 0
        self._scroll_offset = 0
        self._wants_exit = False
        self._exit_value = None

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        viewport = self._labels[
            self._scroll_offset: self._scroll_offset + context.height
        ]
        return self._build_rows(viewport, context, focused)

    def handle_key(self, key) -> tuple:
        self._wants_exit = False
        new_idx = _list_nav(key, self._active_index, len(self._labels),
                            self._last_height)
        if new_idx is not None:
            self._active_index = new_idx
            self._clamp_scroll()
            return True, self.get_value()
        if key == 'KEY_ENTER' or key in ('\n', '\r'):
            return self._select()
        return False, self.get_value()

    def _select(self):
        if self._labels:
            label = self._labels[self._active_index]
            self._exit_value = self._items[label]
            self._wants_exit = True
            return True, self.get_value()
        return False, self.get_value()

    def get_value(self):
        if self._labels:
            return self._labels[self._active_index]
        return None

    def set_value(self, value) -> None:
        if value in self._labels:
            self._active_index = self._labels.index(value)
            self._clamp_scroll()

    def signal_return(self) -> tuple:
        if self._wants_exit:
            return True, self._exit_value
        return False, None


