"""Factory for building a RenderContext from a blessed terminal and a Region."""

from panelmark.draw import RenderContext
from panelmark.layout import Region


def build_render_context(region: Region, term) -> RenderContext:
    """Build a ``RenderContext`` for *region* using *term* capability detection.

    Capability flags set by this factory:

    ``'color'``
        Set when the terminal reports at least 8 colours.
    ``'256color'``
        Set when the terminal reports at least 256 colours.
    ``'truecolor'``
        Set when the terminal reports at least 16 million colours (2^24).
    ``'unicode'``
        Always set — blessed targets Unicode-capable terminals.
    ``'cursor'``
        Always set — TUI renderers support a positioned text cursor.
    ``'italic'``
        Set when the terminal's italic sequence produces a non-empty string.

    Parameters
    ----------
    region:
        The layout region for which the context is being built. Supplies
        ``width`` and ``height``.
    term:
        A blessed ``Terminal`` instance (or compatible mock).
    """
    caps: set[str] = {'unicode', 'cursor'}

    try:
        n = term.number_of_colors
        if n >= 8:
            caps.add('color')
        if n >= 256:
            caps.add('256color')
        if n >= 2 ** 24:
            caps.add('truecolor')
    except Exception:
        pass

    try:
        if term.italic:
            caps.add('italic')
    except Exception:
        pass

    return RenderContext(
        width=region.width,
        height=region.height,
        capabilities=frozenset(caps),
    )
