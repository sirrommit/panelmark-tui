from panelmark.interactions.base import Interaction
from panelmark.draw import DrawCommand, RenderContext


class Function(Interaction):
    """Escape-hatch interaction for custom rendering and key handling.

    ``Function`` does **not** follow the standard ``get_value()`` /
    ``set_value()`` / ``signal_return()`` contract that the built-in
    interactions share.  It is intended for low-level, one-off behaviour where
    none of the built-in interactions fit.  Do not use it as a model when
    designing new interactions.

    ``get_value()`` returns an internal ``_value`` that the handler does not
    manage through a first-class API.  ``signal_return()`` is not implemented —
    ``Function`` never causes the shell to exit on its own.

    The handler is called with ``(shell, context, key)`` where *context* is a
    ``RenderContext`` on render calls (``key=None``) and on key events.

    The handler may return a ``list[DrawCommand]`` to draw content, or
    ``None`` to produce no output.
    """

    def __init__(self, handler):
        """
        handler: Callable[[Shell, RenderContext, key | None], list[DrawCommand] | None]
        Called with key=None on render, with the key string on each keypress.
        """
        self._handler = handler
        self._value = None
        self._context = None
        self._shell = None

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        self._context = context
        result = self._handler(self._shell, context, None)
        if isinstance(result, list):
            return result
        return []

    def handle_key(self, key) -> tuple:
        self._handler(self._shell, self._context, key)
        return False, self.get_value()

    def get_value(self):
        return self._value

    def set_value(self, value) -> None:
        self._value = value
