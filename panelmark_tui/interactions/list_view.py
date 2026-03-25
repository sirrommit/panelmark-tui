from panelmark.interactions.base import Interaction
from panelmark.draw import DrawCommand, RenderContext, WriteCmd, FillCmd


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


class ListView(Interaction):
    """Display-only list of items with optional bullet styles."""

    is_focusable = False

    def __init__(self, items: list, bullet: str = '*'):
        self._items = list(items)
        self._bullet = bullet

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        cmds: list[DrawCommand] = []
        for i, item in enumerate(self._items):
            if i >= context.height:
                break
            bullet = _get_bullet(self._bullet, i)
            line = f'{bullet} {item}'
            display = line[:context.width].ljust(context.width)
            cmds.append(WriteCmd(row=i, col=0, text=display))

        trailing = context.height - min(len(self._items), context.height)
        if trailing > 0:
            cmds.append(FillCmd(
                row=context.height - trailing, col=0,
                width=context.width, height=trailing,
            ))
        return cmds

    def handle_key(self, key) -> tuple:
        return False, self.get_value()

    def get_value(self) -> list:
        return list(self._items)

    def set_value(self, value) -> None:
        self._items = list(value)


class SubList(Interaction):
    """Display-only list with support for nested sublists."""

    is_focusable = False

    def __init__(self, items: list, bullet: str = '*'):
        self._items = items
        self._bullet = bullet

    def _build_items(
        self, items: list, context: RenderContext,
        start_row: int, indent: int,
    ) -> tuple[list[DrawCommand], int]:
        """Recursively build draw commands. Returns (cmds, next_row)."""
        cmds: list[DrawCommand] = []
        row = start_row
        i = 0
        for item in items:
            if row >= context.height:
                break
            if isinstance(item, list):
                sub_cmds, row = self._build_items(item, context, row, indent + 2)
                cmds.extend(sub_cmds)
            else:
                bullet = _get_bullet(self._bullet, i)
                prefix = ' ' * indent
                line = f'{prefix}{bullet} {item}'
                display = line[:context.width].ljust(context.width)
                cmds.append(WriteCmd(row=row, col=0, text=display))
                row += 1
                i += 1
        return cmds, row

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        cmds, next_row = self._build_items(self._items, context, 0, 0)
        trailing = context.height - next_row
        if trailing > 0:
            cmds.append(FillCmd(row=next_row, col=0, width=context.width, height=trailing))
        return cmds

    def handle_key(self, key) -> tuple:
        return False, self.get_value()

    def get_value(self) -> list:
        return self._items

    def set_value(self, value) -> None:
        self._items = value
