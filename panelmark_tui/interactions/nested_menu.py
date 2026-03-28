"""NestedMenu interaction — hierarchical drill-down menu.

Data format
-----------
A nested dict where non-dict values are leaf return values and dict values are
branches::

    menu = NestedMenu({
        "File": {
            "New":  "file:new",
            "Open": "file:open",
            "Save": "file:save",
        },
        "Edit": {
            "Cut":   "edit:cut",
            "Copy":  "edit:copy",
            "Paste": "edit:paste",
        },
        "Quit": "quit",
    })
    sh.assign("menu", menu)
    result = sh.run()   # e.g. "file:save" or "quit"

Use ``Leaf(value)`` to make a dict the return value of a leaf item::

    NestedMenu({"Export": Leaf({"format": "csv", "delimiter": ","})})

Interaction protocol
--------------------
* ``get_value()`` — returns the **path tuple** of the currently highlighted
  item, e.g. ``('File', 'Save')`` when "Save" is highlighted inside the File
  submenu.
* ``set_value(path)`` — navigate to the item at the given path and highlight
  it.  Intermediate ancestors are entered automatically.
* ``signal_return()`` — returns ``(True, mapped_value)`` when the user accepts
  a leaf item; ``(False, None)`` otherwise.

Keys
----
``↑`` / ``k``          move up one item
``↓`` / ``j``          move down one item
``Page Up``            jump up one page
``Page Down``          jump down one page
``Home``               jump to first item
``End``                jump to last item
``Enter`` / ``Space``  descend into branch; accept leaf
``←`` / ``h``          go back to parent level

Malformed input
---------------
``ValueError`` is raised at construction time for:

- empty root dict
- empty branch dict
- duplicate sibling labels
- ``None`` as a leaf payload (bare)

``TypeError`` is raised for non-string labels or a non-dict top-level argument.

``Leaf(None)`` also raises ``ValueError`` at ``Leaf`` construction time.
"""

from panelmark.draw import DrawCommand, RenderContext, WriteCmd, FillCmd
from .scrollable import _ScrollableList, _list_nav


# ---------------------------------------------------------------------------
# Leaf sentinel
# ---------------------------------------------------------------------------

class Leaf:
    """Wraps a value so it is treated as a leaf payload rather than a branch.

    Use this when the desired return value is itself a dict::

        NestedMenu({"Export": Leaf({"format": "csv"})})
    """

    def __init__(self, value):
        if value is None:
            raise ValueError("Leaf payload must not be None")
        self.value = value

    def __repr__(self):
        return f"Leaf({self.value!r})"

    def __eq__(self, other):
        return isinstance(other, Leaf) and self.value == other.value


# ---------------------------------------------------------------------------
# NestedMenu interaction
# ---------------------------------------------------------------------------

class NestedMenu(_ScrollableList):
    """Hierarchical drill-down menu interaction.

    See module docstring for data format, interaction protocol, and keys.
    """

    def __init__(self, items: dict):
        self._tree = _normalize(items)
        self._current_path: tuple = ()
        # Each entry: (path_at_that_level, active_index, scroll_offset)
        self._nav_stack: list = []
        self._active_index: int = 0
        self._scroll_offset: int = 0
        self._wants_exit: bool = False
        self._exit_value = None

    # ------------------------------------------------------------------
    # Internal navigation helpers
    # ------------------------------------------------------------------

    def _items_at(self, path: tuple) -> dict:
        """Return the branch dict at *path* in the normalized tree."""
        node = self._tree
        for label in path:
            node = node[label]
        return node

    def _current_items(self) -> dict:
        return self._items_at(self._current_path)

    def _current_labels(self) -> list:
        return list(self._current_items().keys())

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        cmds: list[DrawCommand] = []
        header_rows = 0

        # Breadcrumb header when inside a submenu
        if self._current_path:
            crumb = '\u2190 ' + ' \u203a '.join(self._current_path)
            cmds.append(WriteCmd(row=0, col=0,
                                 text=crumb[:context.width].ljust(context.width)))
            header_rows = 1

        # Effective item viewport height (reduced by breadcrumb if present)
        self._last_height = max(1, context.height - header_rows)

        labels = self._current_labels()
        items = self._current_items()
        viewport = labels[self._scroll_offset: self._scroll_offset + self._last_height]

        for screen_i, label in enumerate(viewport):
            row = screen_i + header_rows
            item_idx = self._scroll_offset + screen_i
            is_branch = isinstance(items[label], dict)
            display = (label + ' \u25b6') if is_branch else label
            clipped = display[:context.width].ljust(context.width)

            if item_idx == self._active_index and focused:
                cmds.append(WriteCmd(row=row, col=0, text=clipped,
                                     style={'reverse': True}))
            elif item_idx == self._active_index:
                marker = f'> {display}'[:context.width].ljust(context.width)
                cmds.append(WriteCmd(row=row, col=0, text=marker))
            else:
                cmds.append(WriteCmd(row=row, col=0, text=clipped))

        # Fill trailing rows
        rendered = len(viewport) + header_rows
        trailing = context.height - rendered
        if trailing > 0:
            cmds.append(FillCmd(row=rendered, col=0,
                                width=context.width, height=trailing))

        return cmds

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def handle_key(self, key: str) -> tuple:
        self._wants_exit = False
        labels = self._current_labels()

        new_idx = _list_nav(key, self._active_index, len(labels), self._last_height)
        if new_idx is not None:
            self._active_index = new_idx
            self._clamp_scroll()
            return True, self.get_value()

        if key in ('KEY_ENTER', ' ', '\n', '\r'):
            return self._accept()

        if key in ('KEY_LEFT', 'h'):
            return self._go_back()

        return False, self.get_value()

    def _accept(self) -> tuple:
        labels = self._current_labels()
        if not labels:
            return False, self.get_value()
        label = labels[self._active_index]
        item = self._current_items()[label]
        if isinstance(item, dict):
            # Branch: descend into it
            self._nav_stack.append(
                (self._current_path, self._active_index, self._scroll_offset)
            )
            self._current_path = self._current_path + (label,)
            self._active_index = 0
            self._scroll_offset = 0
            return True, self.get_value()
        else:
            # Leaf: signal shell exit with mapped payload
            self._exit_value = item.value
            self._wants_exit = True
            return True, self.get_value()

    def _go_back(self) -> tuple:
        if not self._nav_stack:
            return False, self.get_value()
        path, active_index, scroll_offset = self._nav_stack.pop()
        self._current_path = path
        self._active_index = active_index
        self._scroll_offset = scroll_offset
        return True, self.get_value()

    # ------------------------------------------------------------------
    # Interaction protocol
    # ------------------------------------------------------------------

    def get_value(self) -> tuple:
        """Return the path tuple to the currently highlighted item.

        Returns ``()`` only if the current level has no items, which cannot
        occur with valid input (construction raises on empty branches).
        """
        labels = self._current_labels()
        if not labels:
            return ()
        return self._current_path + (labels[self._active_index],)

    def set_value(self, path) -> None:
        """Navigate to the item at *path* and highlight it.

        *path* is a tuple of string labels from the root to the target item.
        Intermediate ancestors are descended into automatically.  Invalid or
        nonexistent paths are silently ignored.
        """
        if not isinstance(path, tuple) or not path:
            return
        # Validate the full path exists
        try:
            node = self._tree
            for label in path[:-1]:
                node = node[label]
                if not isinstance(node, dict):
                    return
            if path[-1] not in node:
                return
        except (KeyError, TypeError):
            return
        # Rebuild navigation state from scratch
        self._nav_stack = []
        self._current_path = ()
        self._active_index = 0
        self._scroll_offset = 0
        for label in path[:-1]:
            labels = self._current_labels()
            idx = labels.index(label)
            self._nav_stack.append((self._current_path, idx, self._scroll_offset))
            self._current_path = self._current_path + (label,)
            self._active_index = 0
            self._scroll_offset = 0
        # Highlight the final label at the current level
        labels = self._current_labels()
        if path[-1] in labels:
            self._active_index = labels.index(path[-1])
            self._clamp_scroll()

    def signal_return(self) -> tuple:
        """Return ``(True, mapped_value)`` when a leaf has been accepted."""
        if self._wants_exit:
            return True, self._exit_value
        return False, None


# ---------------------------------------------------------------------------
# Input normalization
# ---------------------------------------------------------------------------

def _normalize(items: dict, _path: str = '') -> dict:
    """Recursively validate and normalize a NestedMenu items dict.

    Returns a new dict where every leaf value is wrapped in ``Leaf`` and every
    branch value is a recursively normalized dict.  Raises ``ValueError`` or
    ``TypeError`` on malformed input.
    """
    if not isinstance(items, dict):
        raise TypeError(
            f'NestedMenu items must be a dict, got {type(items).__name__!r}'
        )
    if not items:
        loc = 'root' if not _path else repr(_path)
        raise ValueError(f'NestedMenu {loc} must not be empty')

    result: dict = {}
    for label, value in items.items():
        if not isinstance(label, str):
            raise TypeError(
                f'NestedMenu labels must be strings, got {type(label).__name__!r}'
            )
        if label in result:
            raise ValueError(f'Duplicate sibling label {label!r}')
        child_path = f'{_path} \u203a {label}' if _path else label
        if isinstance(value, Leaf):
            result[label] = value
        elif isinstance(value, dict):
            result[label] = _normalize(value, child_path)
        elif value is None:
            raise ValueError(
                f'None is not a valid leaf payload at {child_path!r}'
            )
        else:
            result[label] = Leaf(value)
    return result
