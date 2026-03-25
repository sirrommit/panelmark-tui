from panelmark.interactions.base import Interaction
from panelmark.draw import DrawCommand, RenderContext


class Function(Interaction):
    """Custom interaction that delegates to a user-provided handler.

    The handler is called with ``(shell, context, key)`` where *context* is a
    ``RenderContext`` on render calls (``key=None``) and on key events.

    The handler may return a ``list[DrawCommand]`` to draw content, or
    ``None`` to produce no output.  Handlers written before the draw command
    migration that performed side-effect drawing can return ``None`` and
    continue to work, though they will produce no visible output under the new
    renderer.  See ``DRAW_MIGRATION.md`` for the upgrade path.
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
