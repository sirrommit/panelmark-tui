"""TUI command executor — translates DrawCommand lists to terminal output.

The executor is the only place in ``panelmark-tui`` that calls ``term.move()``
or emits style escape sequences on behalf of an interaction. Interactions
themselves produce renderer-agnostic ``DrawCommand`` lists; this module
converts them to blessed terminal output.

Usage (inside Renderer.render_region)::

    executor = TUICommandExecutor(term)
    commands = interaction.render(context, focused)
    executor.execute(commands, region)
    sys.stdout.flush()   # caller flushes after all regions are done
"""

import sys
from panelmark.draw import WriteCmd, FillCmd, CursorCmd, DrawCommand
from panelmark.layout import Region
from .style import _apply_attrs


class TUICommandExecutor:
    """Executes a ``list[DrawCommand]`` against a blessed terminal.

    Coordinates in each command are region-relative (``(0, 0)`` = top-left
    of the region). The executor adds ``region.row`` and ``region.col`` to
    map them to screen-absolute positions before printing.

    ``CursorCmd`` is handled last — the terminal cursor is positioned at the
    last ``CursorCmd`` in the list after all draw operations complete. This
    ensures the visible blinking cursor ends up at the correct spot regardless
    of the order commands are appended by the interaction.

    The executor does **not** call ``sys.stdout.flush()``. The caller
    (``Renderer.full_render``) flushes once after all regions are rendered,
    matching the existing batched-flush behaviour.
    """

    def __init__(self, term):
        self._term = term

    def execute(self, commands: list[DrawCommand], region: Region) -> None:
        """Execute *commands* offset by *region* position.

        Parameters
        ----------
        commands:
            List returned by ``Interaction.render()``.
        region:
            The layout region for this interaction. Supplies the absolute
            row/col offset applied to all region-relative coordinates.
        """
        cursor_cmd: CursorCmd | None = None

        for cmd in commands:
            if isinstance(cmd, WriteCmd):
                self._write(cmd, region)
            elif isinstance(cmd, FillCmd):
                self._fill(cmd, region)
            elif isinstance(cmd, CursorCmd):
                cursor_cmd = cmd  # last one wins

        if cursor_cmd is not None:
            self._cursor(cursor_cmd, region)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _apply_style(self, style: dict | None) -> tuple[str, str]:
        """Return (prefix, reset) escape strings for *style*.

        Returns ('', '') when style is None or produces no sequences.
        """
        if not style:
            return '', ''
        prefix = _apply_attrs(style, self._term)
        if not prefix:
            return '', ''
        try:
            reset = str(self._term.normal) if self._term.normal else ''
        except Exception:
            reset = ''
        return prefix, reset

    def _write(self, cmd: WriteCmd, region: Region) -> None:
        abs_row = region.row + cmd.row
        abs_col = region.col + cmd.col
        prefix, reset = self._apply_style(cmd.style)
        print(
            self._term.move(abs_row, abs_col) + prefix + cmd.text + reset,
            end='', flush=False,
        )

    def _fill(self, cmd: FillCmd, region: Region) -> None:
        prefix, reset = self._apply_style(cmd.style)
        line = (cmd.char * cmd.width)[:cmd.width]
        for r in range(cmd.height):
            abs_row = region.row + cmd.row + r
            abs_col = region.col + cmd.col
            print(
                self._term.move(abs_row, abs_col) + prefix + line + reset,
                end='', flush=False,
            )

    def _cursor(self, cmd: CursorCmd, region: Region) -> None:
        abs_row = region.row + cmd.row
        abs_col = region.col + cmd.col
        print(self._term.move(abs_row, abs_col), end='', flush=False)
