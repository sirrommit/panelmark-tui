"""_ScrollableList — shared base for vertically scrollable list interactions.

Subclasses inherit:
  - ``_active_index``  / ``_scroll_offset`` scroll state
  - ``_clamp_scroll()`` — adjusts offset so the active item is always visible
  - ``_build_rows()``  — builds a ``list[DrawCommand]`` for the visible
                         viewport slice with focus/active highlighting and
                         trailing-row fill commands

Usage in a subclass render()::

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        viewport = self._labels[self._scroll_offset:
                                 self._scroll_offset + context.height]
        return self._build_rows(viewport, context, focused)

Usage after moving _active_index in handle_key()::

    self._active_index = max(0, self._active_index - 1)
    self._clamp_scroll()

Future extraction note
----------------------
The scroll state block (``_active_index``, ``_scroll_offset``, ``_last_height``,
``_clamp_scroll``) is intentionally kept separate from ``_build_rows``.  A
future ``_Scrollable`` base class (Phase 9) will lift exactly that block out,
allowing display-only scrollable interactions to inherit scroll state without
inheriting the list-selection machinery.
"""

from panelmark.interactions.base import Interaction
from panelmark.draw import DrawCommand, RenderContext, WriteCmd, FillCmd


class _ScrollableList(Interaction):
    """Abstract base for list-like interactions that support scroll offset."""

    # ------------------------------------------------------------------
    # Scroll state  (future _Scrollable base class extracts this block)
    # ------------------------------------------------------------------

    _active_index: int = 0
    _scroll_offset: int = 0
    _last_height: int = 10   # updated on every render call

    def _clamp_scroll(self) -> None:
        """Adjust _scroll_offset so _active_index is within the viewport.

        Uses the height recorded on the last render() call.  Safe to call
        before the first render (falls back to _last_height = 10).
        """
        h = max(1, self._last_height)
        if self._active_index < self._scroll_offset:
            self._scroll_offset = self._active_index
        elif self._active_index >= self._scroll_offset + h:
            self._scroll_offset = self._active_index - h + 1

    # ------------------------------------------------------------------
    # Row building
    # ------------------------------------------------------------------

    def _build_rows(
        self,
        display_lines: list,
        context: RenderContext,
        focused: bool,
        active_marker: bool = True,
    ) -> list[DrawCommand]:
        """Return draw commands for *display_lines* (the visible viewport slice).

        Parameters
        ----------
        display_lines:
            Pre-sliced list of strings — one per visible row, starting at
            ``_scroll_offset``.  Each string is the full display text for
            that item (e.g. ``'label'`` or ``'[X] label'``).
        context:
            Render context supplying region dimensions and capabilities.
        focused:
            Whether this interaction has keyboard focus.
        active_marker:
            If True (default), the active row gets a ``>`` prefix when the
            interaction is not focused.  Set to False for interactions
            (e.g. CheckBox) that only highlight when focused.
        """
        self._last_height = context.height
        cmds: list[DrawCommand] = []

        for screen_i, line in enumerate(display_lines):
            item_idx = self._scroll_offset + screen_i
            clipped = line[:context.width].ljust(context.width)

            if item_idx == self._active_index and focused:
                cmds.append(WriteCmd(row=screen_i, col=0, text=clipped,
                                     style={'reverse': True}))
            elif item_idx == self._active_index and active_marker:
                text = f'> {line}'[:context.width].ljust(context.width)
                cmds.append(WriteCmd(row=screen_i, col=0, text=text))
            else:
                cmds.append(WriteCmd(row=screen_i, col=0, text=clipped))

        # Fill any rows below the rendered items
        trailing = context.height - len(display_lines)
        if trailing > 0:
            cmds.append(FillCmd(
                row=len(display_lines), col=0,
                width=context.width, height=trailing,
            ))

        return cmds

