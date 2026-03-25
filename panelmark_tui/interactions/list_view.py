from panelmark.interactions.base import Interaction
from panelmark.draw import DrawCommand, RenderContext, WriteCmd, FillCmd
from .scrollable import _Scrollable


def _to_roman(n: int, upper: bool = True) -> str:
    """Convert integer to Roman numeral."""
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
    result = ''
    for i in range(len(val)):
        while n >= val[i]:
            result += syms[i]
            n -= val[i]
    if not upper:
        result = result.lower()
    return result


def _get_bullet(bullet: str, index: int) -> str:
    """Get the bullet/prefix for an item at the given index (0-based)."""
    if bullet in ('*', '-', '•'):
        return bullet
    elif bullet == '1':
        return str(index + 1) + '.'
    elif bullet == 'A':
        return chr(ord('A') + index) + '.'
    elif bullet == 'a':
        return chr(ord('a') + index) + '.'
    elif bullet == 'I':
        return _to_roman(index + 1, upper=True) + '.'
    elif bullet == 'i':
        return _to_roman(index + 1, upper=False) + '.'
    return bullet


class ListView(_Scrollable, Interaction):
    """Scrollable display-only list with optional bullet styles.

    Not focusable by default so that display-only regions are skipped by
    the shell's focus cycle.  Set ``is_focusable = True`` on a subclass
    to enable keyboard scrolling.

    Scroll state (``_scroll_offset``) can always be driven
    programmatically via ``_scroll_by`` / ``_clamp_scroll_to`` from the
    ``_Scrollable`` mixin regardless of focusability.

    Navigation keys (when focusable)
    ---------------------------------
    ``↑`` / ``k``          scroll up one row
    ``↓`` / ``j``          scroll down one row
    ``Page Up``            scroll up one viewport
    ``Page Down``          scroll down one viewport
    ``Home``               jump to top
    ``End``                jump to bottom
    """

    is_focusable = False

    def __init__(self, items: list, bullet: str = '*'):
        self._items = list(items)
        self._bullet = bullet

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        self._last_height = context.height
        cmds: list[DrawCommand] = []

        visible = self._items[self._scroll_offset:self._scroll_offset + context.height]
        for i, item in enumerate(visible):
            abs_i = self._scroll_offset + i
            bullet = _get_bullet(self._bullet, abs_i)
            line = f'{bullet} {item}'
            display = line[:context.width].ljust(context.width)
            cmds.append(WriteCmd(row=i, col=0, text=display))

        trailing = context.height - len(visible)
        if trailing > 0:
            cmds.append(FillCmd(
                row=len(visible), col=0,
                width=context.width, height=trailing,
            ))
        return cmds

    def handle_key(self, key) -> tuple:
        n = len(self._items)
        if key in ('KEY_UP', 'k'):
            self._scroll_by(-1, n)
        elif key in ('KEY_DOWN', 'j'):
            self._scroll_by(1, n)
        elif key == 'KEY_PPAGE':
            self._scroll_by(-max(1, self._last_height - 1), n)
        elif key == 'KEY_NPAGE':
            self._scroll_by(max(1, self._last_height - 1), n)
        elif key == 'KEY_HOME':
            self._scroll_offset = 0
        elif key == 'KEY_END':
            self._scroll_by(n, n)
        return False, self.get_value()

    def get_value(self) -> list:
        return list(self._items)

    def set_value(self, value) -> None:
        self._items = list(value)
        # Clamp in case the list shrank
        self._scroll_by(0, len(self._items))


class SubList(_Scrollable, Interaction):
    """Scrollable display-only list with support for nested sublists.

    Items can be plain strings or nested lists for sub-groups::

        SubList(['top', ['child1', 'child2'], 'bottom'])

    Sub-group items are indented by two spaces per nesting level.

    Scroll offset is supported for programmatic control.  The interaction
    is not focusable by default; make it focusable in a subclass if keyboard
    scrolling is needed.
    """

    is_focusable = False

    def __init__(self, items: list, bullet: str = '*'):
        self._items = items
        self._bullet = bullet

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _flatten_items(self, items: list, indent: int = 0) -> list[str]:
        """Recursively flatten *items* into a list of display strings."""
        lines: list[str] = []
        i = 0
        for item in items:
            if isinstance(item, list):
                lines.extend(self._flatten_items(item, indent + 2))
            else:
                bullet = _get_bullet(self._bullet, i)
                lines.append(' ' * indent + bullet + ' ' + str(item))
                i += 1
        return lines

    # ------------------------------------------------------------------
    # Interaction protocol
    # ------------------------------------------------------------------

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        self._last_height = context.height
        lines = self._flatten_items(self._items)

        visible = lines[self._scroll_offset:self._scroll_offset + context.height]
        cmds: list[DrawCommand] = []
        for i, line in enumerate(visible):
            cmds.append(WriteCmd(row=i, col=0,
                                 text=line[:context.width].ljust(context.width)))

        trailing = context.height - len(visible)
        if trailing > 0:
            cmds.append(FillCmd(row=len(visible), col=0,
                                width=context.width, height=trailing))
        return cmds

    def handle_key(self, key) -> tuple:
        return False, self.get_value()

    def get_value(self) -> list:
        return self._items

    def set_value(self, value) -> None:
        self._items = value
