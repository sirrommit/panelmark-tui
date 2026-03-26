"""Toast widget — transient overlay notification that auto-dismisses.

Displays a short message in a small popup overlay.  The popup disappears
after ``duration`` seconds **or** as soon as the user presses any key,
whichever comes first.  Useful when there is no ``$status$`` region in the
current shell.

Shell layout
------------

    |=== <bold>Title</> ===|
    |{1R $msg$             }|
    |======================|

Height is always **3 rows** (1 border + 1 message + 1 border).

Usage
-----

    from panelmark_tui.widgets import Toast

    # Inside a running shell event handler:
    def handle_save(sh):
        save_file()
        Toast(message="Saved!", duration=1.5).show(parent_shell=sh)
"""

import sys

from panelmark_tui import Shell
from panelmark_tui.interactions import StatusMessage
from panelmark_tui.renderer import Renderer


class Toast:
    """Transient overlay notification.

    Parameters
    ----------
    message : str
        Text to display.
    title : str
        Text in the popup border (default ``"Notice"``).
    duration : float
        Seconds to wait before auto-dismissing (default ``2.0``).
        Press any key to dismiss early.
    width : int
        Width of the popup in characters (including border walls).
    """

    def __init__(
        self,
        message: str,
        title: str = "Notice",
        duration: float = 2.0,
        width: int = 40,
    ):
        self.message = message
        self.title = title
        self.duration = duration
        self.width = width

    def show(self, parent_shell=None, row=None, col=None) -> None:
        """Display the toast and return after it is dismissed.

        Parameters
        ----------
        parent_shell : Shell | None
            If provided, the parent's display is restored after the toast
            dismisses.
        row, col : int | None
            Override automatic centering.
        """
        term = parent_shell.terminal if parent_shell is not None else None
        if term is None:
            import blessed
            term = blessed.Terminal()

        shell_def = (
            f"|=== <bold>{self.title}</> ===|\n"
            "|{1R $msg$ }|\n"
            "|=============|\n"
        )
        popup = Shell(shell_def, _terminal=term)
        popup.assign("msg", StatusMessage())
        popup.update("msg", ("info", self.message))

        tw = term.width or 80
        th = term.height or 24
        height = 3   # fixed: top border + 1 content row + bottom border

        if row is None:
            row = max(0, (th - height) // 2)
        if col is None:
            col = max(0, (tw - self.width) // 2)

        popup._resolve_layout(self.width, height, offset_row=row, offset_col=col)

        renderer = Renderer(term)
        renderer.full_render(
            popup._layout, popup._regions, popup._interactions,
            None, self.width, height,
            offset_row=row, offset_col=col,
        )
        sys.stdout.flush()

        # Block until keypress or timeout
        term.inkey(timeout=self.duration)

        # Restore parent display
        if parent_shell is not None and parent_shell._renderer is not None:
            tw = term.width or 80
            th = term.height or 24
            parent_shell._renderer.full_render(
                parent_shell._layout, parent_shell._regions,
                parent_shell._interactions, parent_shell._focused, tw, th,
            )
            sys.stdout.flush()
