"""Spinner widget — indeterminate-progress popup.

Displays an animated spinner alongside a status message while the caller
performs background work.  Unlike :class:`~panelmark_tui.widgets.Progress`,
the Spinner has no known total — it just animates until ``tick()`` is
called or the context manager exits.

Shell layout
------------

    |=== <bold>Title</> ===|
    |{1R $spin$            }|   ← spinner frame + message on one row
    |----------------------|
    |{1R $buttons$         }|   ← omitted when cancellable=False
    |======================|

- **4 rows** when ``cancellable=False``  (1+1+1+1)
- **6 rows** when ``cancellable=True``   (1+1+1+1+1+1)

Usage
-----

    from panelmark_tui.widgets import Spinner

    def do_work(sh):
        with Spinner(title="Scanning…").show(parent_shell=sh) as spin:
            for path in paths:
                scan(path)
                spin.tick(f"Scanning {path}")
                if spin.cancelled:
                    break
"""

import sys
import contextlib

from panelmark.interactions.base import Interaction
from panelmark.draw import DrawCommand, RenderContext, WriteCmd, FillCmd
from panelmark_tui import Shell
from panelmark_tui.interactions import MenuReturn
from panelmark_tui.renderer import Renderer
from panelmark_tui.events import EventLoop


# ---------------------------------------------------------------------------
# Animation frames
# ---------------------------------------------------------------------------

_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']


# ---------------------------------------------------------------------------
# Shell definitions
# ---------------------------------------------------------------------------

def _shell_with_buttons(title: str) -> str:
    return (
        f"|=== <bold>{title}</> ===|\n"
        "|{1R $spin$              }|\n"
        "|------------------------|\n"
        "|{1R $buttons$           }|\n"
        "|========================|\n"
    )


def _shell_no_buttons(title: str) -> str:
    return (
        f"|=== <bold>{title}</> ===|\n"
        "|{1R $spin$              }|\n"
        "|========================|\n"
    )


# ---------------------------------------------------------------------------
# _SpinnerInteraction
# ---------------------------------------------------------------------------

class _SpinnerInteraction(Interaction):
    """Draws a ``⠋ message`` line that advances its animation frame on each
    ``tick()`` call."""

    def __init__(self, state: dict):
        self._state = state

    @property
    def is_focusable(self):
        return False

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        frame = _FRAMES[self._state.get("frame", 0) % len(_FRAMES)]
        msg = self._state.get("message", "")
        line = f"{frame} {msg}" if msg else frame
        line = line[:context.width].ljust(context.width)
        cmds: list[DrawCommand] = [WriteCmd(row=0, col=0, text=line)]
        if context.height > 1:
            cmds.append(FillCmd(row=1, col=0,
                                width=context.width, height=context.height - 1))
        return cmds

    def handle_key(self, key) -> tuple:
        return False, self.get_value()

    def get_value(self):
        return self._state.get("frame", 0)

    def set_value(self, value) -> None:
        if value is not None:
            self._state["frame"] = int(value)


# ---------------------------------------------------------------------------
# _CancelInteraction
# ---------------------------------------------------------------------------

class _CancelInteraction(MenuReturn):
    """MenuReturn that sets state["cancelled"] when Cancel is selected."""

    def __init__(self, state: dict):
        self._state = state
        super().__init__({"Cancel": None})

    def handle_key(self, key) -> tuple:
        changed, value = super().handle_key(key)
        should_exit, _ = super().signal_return()
        if should_exit:
            self._state["cancelled"] = True
        return changed, value


# ---------------------------------------------------------------------------
# _SpinnerHandle — yielded to the caller
# ---------------------------------------------------------------------------

class _SpinnerHandle:
    """Live handle to an active Spinner popup.

    Returned by the context manager created by ``Spinner.show()``.
    """

    def __init__(self, popup: Shell, state: dict, term, renderer: Renderer):
        self._popup = popup
        self._state = state
        self._term = term
        self._renderer = renderer

    def tick(self, message: str = "") -> None:
        """Advance the spinner frame and optionally update the message."""
        self._state["frame"] = (self._state.get("frame", 0) + 1) % len(_FRAMES)
        self._state["message"] = message

        popup = self._popup
        popup.update("spin", self._state["frame"])
        self._flush_dirty()
        self._poll_cancel()

    @property
    def cancelled(self) -> bool:
        return self._state.get("cancelled", False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _flush_dirty(self) -> None:
        popup = self._popup
        renderer = self._renderer
        for name in list(popup._dirty):
            if name in popup._interactions and name in popup._regions:
                renderer.render_region(
                    popup._regions[name],
                    popup._interactions[name],
                    name == popup._focused,
                )
        popup._dirty.clear()
        sys.stdout.flush()

    def _poll_cancel(self) -> None:
        if self._state.get("cancelled"):
            return
        term = self._term
        key = term.inkey(timeout=0)
        if not key:
            return
        key_str = str(key)
        if key_str in (chr(27), chr(17)):
            self._state["cancelled"] = True
            return
        if key_str == "\t":
            self._popup._move_focus(1)
            self._flush_dirty()
        elif key.is_sequence and key.name == "KEY_BTAB":
            self._popup._move_focus(-1)
            self._flush_dirty()
        elif self._popup._focused and self._popup._focused in self._popup._interactions:
            interaction = self._popup._interactions[self._popup._focused]
            interaction.handle_key(key.name if key.is_sequence else str(key))
            self._popup._dirty.add(self._popup._focused)
            should_exit, _ = interaction.signal_return()
            if should_exit:
                self._state["cancelled"] = True
            self._flush_dirty()


# ---------------------------------------------------------------------------
# Public widget class
# ---------------------------------------------------------------------------

class Spinner:
    """Indeterminate-progress popup.

    Parameters
    ----------
    title : str
        Text displayed in the popup border (rendered bold).
    cancellable : bool
        If ``True`` (default), a Cancel button is shown.
    width : int
        Width of the popup in characters (including border walls).

    Usage
    -----

    Call ``show()`` as a context manager::

        with Spinner(title="Working…").show(parent_shell=sh) as spin:
            for item in items:
                process(item)
                spin.tick(f"Processing {item}")
                if spin.cancelled:
                    break
    """

    def __init__(
        self,
        title: str = "Working…",
        cancellable: bool = True,
        width: int = 50,
    ):
        self.title = title
        self.cancellable = cancellable
        self.width = width

    @contextlib.contextmanager
    def show(self, parent_shell=None, row=None, col=None):
        """Display the spinner popup as a context manager.

        Parameters
        ----------
        parent_shell : Shell | None
            If provided, the parent's display is restored when the popup
            closes.
        row, col : int | None
            Override automatic centering.

        Yields
        ------
        _SpinnerHandle
            Object with ``tick(message)`` method and ``cancelled`` attribute.
        """
        term = parent_shell.terminal if parent_shell is not None else None
        if term is None:
            import blessed
            term = blessed.Terminal()

        state = {"frame": 0, "message": "", "cancelled": False}

        shell_def = (
            _shell_with_buttons(self.title)
            if self.cancellable
            else _shell_no_buttons(self.title)
        )
        popup = Shell(shell_def, _terminal=term)
        popup.assign("spin", _SpinnerInteraction(state))
        if self.cancellable:
            popup.assign("buttons", _CancelInteraction(state))

        tw = term.width or 80
        th = term.height or 24

        from panelmark.layout import _fixed_height
        fh = _fixed_height(popup._layout.root)
        height = fh if fh is not None else max(1, int(th * 0.4))

        if row is None:
            row = max(0, (th - height) // 2)
        if col is None:
            col = max(0, (tw - self.width) // 2)

        popup._resolve_layout(self.width, height,
                              offset_row=row, offset_col=col)

        for name in popup._focus_order:
            if name in popup._interactions and popup._interactions[name].is_focusable:
                popup._focused = name
                break

        renderer = Renderer(term)
        popup._renderer = renderer
        renderer.full_render(
            popup._layout, popup._regions, popup._interactions,
            popup._focused, self.width, height,
            offset_row=row, offset_col=col,
        )
        sys.stdout.flush()

        handle = _SpinnerHandle(popup, state, term, renderer)

        try:
            yield handle
        finally:
            if parent_shell is not None and parent_shell._renderer is not None:
                tw = term.width or 80
                th = term.height or 24
                parent_shell._renderer.full_render(
                    parent_shell._layout, parent_shell._regions,
                    parent_shell._interactions, parent_shell._focused,
                    tw, th,
                )
                sys.stdout.flush()
