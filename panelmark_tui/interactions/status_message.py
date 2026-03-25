"""StatusMessage interaction — inline status/validation feedback region.

Displays a single-line message with one of three severity styles:

  - ``"error"``   — prefixed with ``✗ ``, rendered in red (or plain if no colour)
  - ``"success"`` — prefixed with ``✓ ``, rendered in green
  - ``"info"``    — prefixed with ``ℹ ``, rendered in the terminal default colour

Not focusable; receives updates via ``shell.update(name, value)`` where
*value* is one of:

  - ``None`` or ``""``          — clears the region (shows blank)
  - ``(style, message)`` tuple  — style is ``"error"``, ``"success"``, or ``"info"``
  - A plain ``str``             — treated as ``("info", str)``

Example::

    from panelmark_tui.interactions import StatusMessage

    shell.assign("status", StatusMessage())
    shell.update("status", ("error", "File not found"))
    shell.update("status", ("success", "Saved"))
    shell.update("status", None)          # clear
"""

from panelmark.interactions.base import Interaction
from panelmark.draw import DrawCommand, RenderContext, WriteCmd, FillCmd


_PREFIXES = {
    "error":   "✗ ",
    "success": "✓ ",
    "info":    "ℹ ",
}

_COLORS = {
    "error":   "red",
    "success": "green",
}


class StatusMessage(Interaction):
    """Inline status / validation feedback region.

    Not focusable.  Updated programmatically via ``shell.update()``.
    """

    def __init__(self):
        self._style   = "info"
        self._message = ""

    @property
    def is_focusable(self) -> bool:
        return False

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        cmds: list[DrawCommand] = []

        if not self._message:
            cmds.append(FillCmd(row=0, col=0, width=context.width, height=context.height))
            return cmds

        prefix  = _PREFIXES.get(self._style, "")
        text    = f"{prefix}{self._message}"
        clipped = text[:context.width].ljust(context.width)

        color = _COLORS.get(self._style)
        style = {'color': color} if color and context.supports('color') else None
        cmds.append(WriteCmd(row=0, col=0, text=clipped, style=style))

        if context.height > 1:
            cmds.append(FillCmd(row=1, col=0, width=context.width, height=context.height - 1))

        return cmds

    # ------------------------------------------------------------------
    # Interaction protocol (display-only)
    # ------------------------------------------------------------------

    def handle_key(self, key) -> tuple:
        return False, self.get_value()

    def get_value(self):
        if not self._message:
            return None
        return (self._style, self._message)

    def set_value(self, value) -> None:
        if value is None or value == "":
            self._style   = "info"
            self._message = ""
        elif isinstance(value, tuple) and len(value) == 2:
            style, message = value
            self._style   = style if style in _PREFIXES else "info"
            self._message = str(message) if message else ""
        else:
            self._style   = "info"
            self._message = str(value)
