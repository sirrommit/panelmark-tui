"""TreeView interaction — interactive collapsible tree with keyboard navigation.

Tree data format
----------------
A nested dict where ``None`` values are leaves and dict values are branches::

    tree = {
        'Documents': {
            'report.pdf': None,
            'notes.txt':  None,
        },
        'Pictures': {
            'photo1.jpg': None,
        },
        'README.md': None,
    }

    tv = TreeView(tree)
    sh.assign('tree', tv)

Interaction protocol
--------------------
* ``get_value()`` — returns the **path tuple** of the currently highlighted
  item, e.g. ``('Documents', 'report.pdf')`` or ``('README.md',)``.
* ``signal_return()`` — returns ``(True, path_tuple)`` after Enter/Space
  is pressed on a **leaf** node.  Branch nodes toggle expand/collapse
  instead.

Keys
----
``↑`` / ``k``        move up one item
``↓`` / ``j``        move down one item
``Page Up``          jump up one page
``Page Down``        jump down one page
``Home``             jump to first visible item
``End``              jump to last visible item
``Enter`` / ``Space``  expand/collapse branch; select leaf (signals return)
"""

from panelmark.draw import DrawCommand, RenderContext
from .scrollable import _ScrollableList, _list_nav

_BRANCH_OPEN  = '▼ '
_BRANCH_CLOSE = '▶ '
_LEAF_INDENT  = '  '   # same width as a branch marker so labels align


class TreeView(_ScrollableList):
    """Interactive tree view with expand/collapse support.

    See module docstring for data format and interaction protocol.
    """

    def __init__(self, tree: dict, *, initially_expanded: bool = False):
        """
        Parameters
        ----------
        tree:
            Nested dict describing the tree.  ``None`` values are leaves;
            dict values are branches with children.
        initially_expanded:
            If True all branches start expanded.  Defaults to False
            (all branches start collapsed).
        """
        self._tree = tree
        self._expanded: set = set()        # set of path tuples for open branches
        self._active_index = 0
        self._scroll_offset = 0
        self._wants_exit = False
        self._exit_value = None

        if initially_expanded:
            self._expand_all(tree, ())

    # ------------------------------------------------------------------
    # Tree traversal helpers
    # ------------------------------------------------------------------

    def _expand_all(self, tree: dict, path: tuple) -> None:
        """Recursively expand every branch in *tree* rooted at *path*."""
        for label, children in tree.items():
            if isinstance(children, dict):
                cur_path = path + (label,)
                self._expanded.add(cur_path)
                self._expand_all(children, cur_path)

    def _visible_items(self) -> list:
        """Return the flat list of currently visible items.

        Each element is a ``(display_text, path_tuple, is_branch)`` triple.
        Only items within expanded branches are included; collapsed branches
        hide all their descendants.
        """
        result: list = []
        self._build_visible(self._tree, (), 0, result)
        return result

    def _build_visible(self, tree: dict, path: tuple, indent: int,
                       result: list) -> None:
        for label, children in tree.items():
            cur_path = path + (label,)
            is_branch = isinstance(children, dict)
            if is_branch:
                marker = _BRANCH_OPEN if cur_path in self._expanded else _BRANCH_CLOSE
                display = ' ' * indent + marker + label
                result.append((display, cur_path, True))
                if cur_path in self._expanded:
                    self._build_visible(children, cur_path, indent + 2, result)
            else:
                display = ' ' * indent + _LEAF_INDENT + label
                result.append((display, cur_path, False))

    # ------------------------------------------------------------------
    # Interaction protocol
    # ------------------------------------------------------------------

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        items = self._visible_items()
        display_lines = [item[0] for item in items]
        viewport = display_lines[self._scroll_offset:self._scroll_offset + context.height]
        return self._build_rows(viewport, context, focused)

    def handle_key(self, key) -> tuple:
        self._wants_exit = False
        items = self._visible_items()
        new_idx = _list_nav(key, self._active_index, len(items), self._last_height)
        if new_idx is not None:
            self._active_index = new_idx
            self._clamp_scroll()
            return True, self.get_value()
        if key in ('KEY_ENTER', ' ', '\n', '\r'):
            return self._activate(items)
        return False, self.get_value()

    def _activate(self, items: list) -> tuple:
        """Toggle expand/collapse (branch) or select (leaf)."""
        if not items:
            return False, self.get_value()
        _, path, is_branch = items[self._active_index]
        if is_branch:
            if path in self._expanded:
                # Collapse: also collapse all descendants so re-expanding is clean
                self._expanded = {
                    p for p in self._expanded
                    if p[:len(path)] != path
                }
            else:
                self._expanded.add(path)
            # Clamp cursor to new visible list (collapsing may shrink it)
            new_items = self._visible_items()
            if self._active_index >= len(new_items):
                self._active_index = max(0, len(new_items) - 1)
            self._clamp_scroll()
            return True, self.get_value()
        else:
            # Leaf selected — signal shell exit
            self._exit_value = path
            self._wants_exit = True
            return True, self.get_value()

    def get_value(self):
        """Return the path tuple of the currently highlighted item, or None."""
        items = self._visible_items()
        if items and 0 <= self._active_index < len(items):
            return items[self._active_index][1]
        return None

    def set_value(self, value) -> None:
        """Highlight the item at *value* (a path tuple).

        If the path is not currently visible, the intermediate branches are
        expanded first so the item can be found and navigated to.
        """
        if not isinstance(value, tuple) or not value:
            return
        # Ensure all ancestors are expanded
        for depth in range(1, len(value)):
            self._expanded.add(value[:depth])
        items = self._visible_items()
        for i, (_, path, _) in enumerate(items):
            if path == value:
                self._active_index = i
                self._clamp_scroll()
                return

    def signal_return(self) -> tuple:
        if self._wants_exit:
            return True, self._exit_value
        return False, None
