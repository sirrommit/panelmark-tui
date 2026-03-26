"""TableView interaction — multi-column read-only display table.

Renders a sticky header row followed by scrollable data rows.  Column
values are padded or truncated to the specified width and separated by
single ``│`` dividers.

Example::

    from panelmark_tui.interactions import TableView

    shell.assign("results", TableView(
        columns=[("Name", 20), ("Status", 10), ("Score", 6)],
        rows=[
            ["Alice", "active", "95"],
            ["Bob",   "idle",   "72"],
        ],
    ))

The active row is highlighted when the interaction has focus.
``get_value()`` returns the 0-based index of the active (cursor) row.

Navigation
----------
``↑`` / ``k``   move up one row
``↓`` / ``j``   move down one row
``Page Up``     jump up one viewport
``Page Down``   jump down one viewport
``Home``        first row
``End``         last row
"""

from panelmark.interactions.base import Interaction
from panelmark.draw import DrawCommand, RenderContext, WriteCmd, FillCmd
from .scrollable import _Scrollable, _list_nav


class TableView(_Scrollable, Interaction):
    """Multi-column read-only display table.

    Parameters
    ----------
    columns : list[tuple[str, int]]
        Column definitions as ``[(header_label, width_in_chars), ...]``.
        Columns are rendered exactly ``width_in_chars`` characters wide
        and separated by a single ``│`` character.
    rows : list[list]
        Table data.  Each inner list should have the same number of
        elements as ``columns``.  Values are converted via ``str()``.
    """

    is_focusable = True

    def __init__(self, columns: list, rows: list):
        self._columns = list(columns)           # [(header, width), ...]
        self._rows = [list(r) for r in rows]
        self._active_index = 0
        self._scroll_offset = 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _cell(self, text: str, width: int) -> str:
        s = str(text)
        if len(s) >= width:
            return s[:width]
        return s.ljust(width)

    def _format_row(self, cells: list, total_width: int) -> str:
        parts = [self._cell(str(v), w) for v, (_, w) in zip(cells, self._columns)]
        return (' │ '.join(parts))[:total_width].ljust(total_width)

    def _format_header(self, total_width: int) -> str:
        parts = [self._cell(h, w) for h, w in self._columns]
        return (' │ '.join(parts))[:total_width].ljust(total_width)

    # ------------------------------------------------------------------
    # Interaction protocol
    # ------------------------------------------------------------------

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        # Store data-viewport height for correct page-up/down step
        self._last_height = max(1, context.height - 1)

        w = context.width
        cmds: list[DrawCommand] = []

        # Row 0: sticky header
        header_style = {'reverse': True} if focused else {'bold': True}
        cmds.append(WriteCmd(row=0, col=0, text=self._format_header(w),
                             style=header_style))

        if context.height <= 1:
            return cmds

        # Rows 1+: scrollable data
        data_height = context.height - 1
        viewport = self._rows[self._scroll_offset:self._scroll_offset + data_height]

        for screen_i, row_data in enumerate(viewport):
            item_idx = self._scroll_offset + screen_i
            line = self._format_row(row_data, w)
            if item_idx == self._active_index and focused:
                cmds.append(WriteCmd(row=screen_i + 1, col=0, text=line,
                                     style={'reverse': True}))
            else:
                cmds.append(WriteCmd(row=screen_i + 1, col=0, text=line))

        trailing = data_height - len(viewport)
        if trailing > 0:
            cmds.append(FillCmd(
                row=len(viewport) + 1, col=0,
                width=w, height=trailing,
            ))

        return cmds

    def handle_key(self, key) -> tuple:
        new_idx = _list_nav(key, self._active_index, len(self._rows),
                            self._last_height)
        if new_idx is not None:
            self._active_index = new_idx
            self._clamp_scroll_to(self._active_index)
            return True, self.get_value()
        return False, self.get_value()

    def get_value(self) -> int:
        """Return the active row index."""
        return self._active_index

    def set_value(self, value) -> None:
        """Set the active row by index."""
        if value is not None:
            n = len(self._rows)
            self._active_index = max(0, min(int(value), n - 1)) if n > 0 else 0
            self._clamp_scroll_to(self._active_index)
