import sys
import blessed
try:
    import termios as _termios
    _HAS_TERMIOS = True
except ImportError:
    _HAS_TERMIOS = False

from panelmark.shell import Shell as _CoreShell
from panelmark.layout import _fixed_width, _fixed_height
from .renderer import Renderer
from .events import EventLoop


def _key_str(key) -> str:
    """Translate a blessed Keystroke to a plain string key name."""
    if key.is_sequence:
        return key.name   # e.g. 'KEY_UP', 'KEY_ENTER', 'KEY_BTAB'
    return str(key)       # printable char or control char


class Shell(_CoreShell):
    """
    TUI shell — extends panelmark.Shell with a blessed-powered event loop.

    Usage::

        sh = Shell(definition)
        sh.assign('menu', MenuFunction({...}))
        result = sh.run()

    For modal popups call ``run_modal(parent_shell=sh)`` instead of ``run()``.
    The caller is responsible for being inside the parent's terminal context.
    """

    def __init__(self, definition: str, _terminal=None):
        super().__init__(definition)
        self._term = _terminal or blessed.Terminal()
        self._renderer = None   # Set by run() / run_modal()

    @property
    def terminal(self):
        return self._term

    # ------------------------------------------------------------------
    # Event loop helpers
    # ------------------------------------------------------------------

    def _auto_focus(self):
        """Set focus to the first focusable region if focus is None."""
        if self._focused is None:
            for name in self._focus_order:
                if name in self._interactions and self._interactions[name].is_focusable:
                    self._focused = name
                    break

    def _redraw_dirty(self, renderer, term):
        for dirty_name in list(self._dirty):
            if dirty_name in self._interactions and dirty_name in self._regions:
                region = self._regions[dirty_name]
                interaction = self._interactions[dirty_name]
                renderer.render_region(region, interaction,
                                       dirty_name == self._focused)
        self._dirty.clear()
        sys.stdout.flush()

    # ------------------------------------------------------------------
    # run()
    # ------------------------------------------------------------------

    def run(self):
        """Start the TUI event loop in fullscreen. Returns the exit value."""
        term = self._term
        renderer = Renderer(term)
        self._renderer = renderer
        event_loop = EventLoop(term)

        self._auto_focus()
        w = term.width or 80
        h = term.height or 24
        self._resolve_layout(w, h)

        with term.fullscreen(), term.cbreak(), term.hidden_cursor():
            _saved_attrs = None
            if _HAS_TERMIOS and hasattr(term, '_keyboard_fd'):
                try:
                    _saved_attrs = _termios.tcgetattr(term._keyboard_fd)
                    attrs = list(_saved_attrs)
                    attrs[0] &= ~_termios.IXON
                    _termios.tcsetattr(term._keyboard_fd, _termios.TCSANOW, attrs)
                except Exception:
                    _saved_attrs = None

            try:
                renderer.full_render(
                    self._layout, self._regions, self._interactions,
                    self._focused, w, h)
                self._dirty.clear()
                sys.stdout.flush()

                while True:
                    key = event_loop.next_key()
                    if key is None or not key:
                        continue

                    # Resize: re-resolve layout and full re-render
                    if key.is_sequence and key.name == 'KEY_RESIZE':
                        w = term.width or 80
                        h = term.height or 24
                        self._resolve_layout(w, h)
                        renderer.full_render(
                            self._layout, self._regions, self._interactions,
                            self._focused, w, h)
                        self._dirty.clear()
                        sys.stdout.flush()
                        continue

                    status, value = self.handle_key(_key_str(key))
                    if status == 'exit':
                        return value

                    self._redraw_dirty(renderer, term)

            finally:
                if _saved_attrs is not None and _HAS_TERMIOS and hasattr(term, '_keyboard_fd'):
                    try:
                        _termios.tcsetattr(
                            term._keyboard_fd, _termios.TCSADRAIN, _saved_attrs)
                    except Exception:
                        pass

        return None

    # ------------------------------------------------------------------
    # run_modal()
    # ------------------------------------------------------------------

    def run_modal(self, row=None, col=None, width=None, height=None,
                  parent_shell=None):
        """Run as a modal popup. Must be called inside a parent terminal context."""
        term = self._term
        tw = term.width  or 80
        th = term.height or 24
        root = self._layout.root

        if width is None:
            fw = _fixed_width(root)
            width = (fw + 2) if fw is not None else max(1, int(tw * 0.6))

        if height is None:
            fh = _fixed_height(root)
            height = fh if fh is not None else max(1, int(th * 0.6))

        if row is None:
            row = max(0, (th - height) // 2)

        if col is None:
            col = max(0, (tw - width) // 2)

        self._resolve_layout(width, height, offset_row=row, offset_col=col)
        self._auto_focus()

        renderer = Renderer(term)
        self._renderer = renderer
        event_loop = EventLoop(term)

        renderer.full_render(self._layout, self._regions, self._interactions,
                             self._focused, width, height,
                             offset_row=row, offset_col=col)
        self._dirty.clear()
        sys.stdout.flush()

        result = None
        while True:
            key = event_loop.next_key()
            if key is None or not key:
                continue

            if key.is_sequence and key.name == 'KEY_RESIZE':
                self._resolve_layout(width, height, offset_row=row, offset_col=col)
                renderer.full_render(self._layout, self._regions, self._interactions,
                                     self._focused, width, height,
                                     offset_row=row, offset_col=col)
                self._dirty.clear()
                sys.stdout.flush()
                continue

            status, value = self.handle_key(_key_str(key))
            if status == 'exit':
                result = value
                break

            self._redraw_dirty(renderer, term)

        # Restore parent display
        if parent_shell is not None and parent_shell._renderer is not None:
            tw = term.width or 80
            th = term.height or 24
            parent_shell._renderer.full_render(
                parent_shell._layout, parent_shell._regions,
                parent_shell._interactions, parent_shell._focused, tw, th)
            sys.stdout.flush()

        return result
