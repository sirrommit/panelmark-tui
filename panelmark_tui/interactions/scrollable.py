"""Scroll-state mixin and scrollable-list base for panelmark-tui interactions.

Two classes are exported:

``_Scrollable``
    A pure mixin (no ``Interaction`` inheritance) providing scroll state and
    helpers.  Combine with ``Interaction`` to build any scrollable interaction::

        class MyView(_Scrollable, Interaction):
            ...

    Members:

    * ``_scroll_offset``    — first visible row index (updated by helpers)
    * ``_last_height``      — viewport height from the most recent render call
    * ``_clamp_scroll_to(target_row)`` — ensure *target_row* is visible
    * ``_scroll_by(delta, total_items)`` — shift offset by *delta* rows,
      clamped to ``[0, total_items − height]``

``_ScrollableList``
    Abstract base for **interactive** scrollable lists (menus, checkboxes).
    Extends ``_Scrollable`` and adds:

    * ``_active_index``    — currently highlighted item (0-based)
    * ``_clamp_scroll()``  — convenience wrapper: ``_clamp_scroll_to(_active_index)``
    * ``_build_rows(display_lines, context, focused, active_marker)``
      — returns ``list[DrawCommand]`` for the visible viewport slice with
      focus/active highlighting and trailing ``FillCmd``

Usage in a ``_ScrollableList`` subclass ``render()``::

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        viewport = self._labels[self._scroll_offset:
                                 self._scroll_offset + context.height]
        return self._build_rows(viewport, context, focused)

Usage after moving ``_active_index`` in ``handle_key()``::

    self._active_index = max(0, self._active_index - 1)
    self._clamp_scroll()

Future extraction note
----------------------
``_Scrollable`` is already the clean base class for Phase 9.  ``ListView``
and ``SubList`` extend it directly so that display-only interactions can
inherit scroll state without inheriting the list-selection machinery.
``_ScrollableList`` uses ``_active_index``-based clamping on top of the same
scroll primitives.
"""

from panelmark.interactions.base import Interaction
from panelmark.draw import DrawCommand, RenderContext, WriteCmd, FillCmd


# ---------------------------------------------------------------------------
# Shared navigation helper
# ---------------------------------------------------------------------------

def _list_nav(key: str, active: int, total: int, page_size: int):
    """Map a navigation key to a new active index.

    Handles up/down (arrow keys and vi keys), page up/down, home, and end.
    Returns the new index (clamped to ``[0, total-1]``), or ``None`` if the
    key is not a navigation key.

    Parameters
    ----------
    key:        The raw key string from ``handle_key``.
    active:     Current active (cursor) index.
    total:      Total number of items in the list.
    page_size:  Viewport height — used as the page-up/down step size.
    """
    if total == 0:
        return None
    if key in ('KEY_UP', 'KEY_SUP') or key == 'k':
        return max(0, active - 1)
    if key in ('KEY_DOWN', 'KEY_SDOWN') or key == 'j':
        return min(total - 1, active + 1)
    if key == 'KEY_PPAGE':                          # Page Up
        return max(0, active - max(1, page_size))
    if key == 'KEY_NPAGE':                          # Page Down
        return min(total - 1, active + max(1, page_size))
    if key == 'KEY_HOME':
        return 0
    if key == 'KEY_END':
        return total - 1
    return None


# ---------------------------------------------------------------------------
# _Scrollable — pure scroll-state mixin
# ---------------------------------------------------------------------------

class _Scrollable:
    """Pure mixin providing scroll state and helpers.

    Do not extend ``Interaction`` directly — combine with it::

        class MyView(_Scrollable, Interaction): ...
    """

    _scroll_offset: int = 0
    _last_height: int = 10   # updated on every render call

    def _clamp_scroll_to(self, target_row: int) -> None:
        """Adjust ``_scroll_offset`` so *target_row* is within the viewport.

        Uses ``_last_height`` from the most recent ``render()`` call.
        Safe to call before the first render (falls back to ``_last_height=10``).
        """
        h = max(1, self._last_height)
        if target_row < self._scroll_offset:
            self._scroll_offset = target_row
        elif target_row >= self._scroll_offset + h:
            self._scroll_offset = target_row - h + 1

    def _scroll_by(self, delta: int, total_items: int) -> None:
        """Shift ``_scroll_offset`` by *delta* rows.

        The result is clamped to ``[0, max(0, total_items − height)]`` so
        the offset never goes out of range.
        """
        h = max(1, self._last_height)
        max_offset = max(0, total_items - h)
        self._scroll_offset = max(0, min(self._scroll_offset + delta, max_offset))


# ---------------------------------------------------------------------------
# _ScrollableList — interactive list base (menus, checkboxes)
# ---------------------------------------------------------------------------

class _ScrollableList(_Scrollable, Interaction):
    """Abstract base for list-like interactions that support scroll offset."""

    _active_index: int = 0

    def _clamp_scroll(self) -> None:
        """Adjust ``_scroll_offset`` so ``_active_index`` is within the viewport.

        Convenience wrapper around ``_clamp_scroll_to``; call this after
        changing ``_active_index`` in ``handle_key()``.
        """
        self._clamp_scroll_to(self._active_index)

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
