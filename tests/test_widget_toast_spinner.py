"""Tests for Toast and Spinner widgets.

These tests avoid real terminal I/O by using MockTerminal.  They focus on
state management and render output rather than live terminal interaction.
"""

import io
import sys
import pytest

from panelmark_tui.testing import MockTerminal, make_key
from panelmark_tui.widgets.toast import Toast
from panelmark_tui.widgets.spinner import (
    Spinner,
    _SpinnerInteraction,
    _CancelInteraction,
    _FRAMES,
)
from panelmark.draw import RenderContext


def ctx(width=40, height=4):
    return RenderContext(width=width, height=height,
                        capabilities=frozenset({'color', 'cursor'}))


# ---------------------------------------------------------------------------
# _SpinnerInteraction unit tests (no I/O)
# ---------------------------------------------------------------------------

class TestSpinnerInteraction:
    def test_initial_frame_is_first(self):
        state = {"frame": 0, "message": ""}
        spin = _SpinnerInteraction(state)
        cmds = spin.render(ctx(), focused=False)
        texts = [c.text for c in cmds if hasattr(c, 'text')]
        assert _FRAMES[0] in texts[0]

    def test_frame_advances_in_text(self):
        state = {"frame": 3, "message": "hello"}
        spin = _SpinnerInteraction(state)
        cmds = spin.render(ctx(), focused=False)
        texts = [c.text for c in cmds if hasattr(c, 'text')]
        assert _FRAMES[3] in texts[0]
        assert 'hello' in texts[0]

    def test_message_empty_renders_frame_only(self):
        state = {"frame": 0, "message": ""}
        spin = _SpinnerInteraction(state)
        from panelmark.draw import WriteCmd
        cmds = spin.render(ctx(), focused=False)
        row0 = next(c for c in cmds if isinstance(c, WriteCmd) and c.row == 0)
        # Frame char should be present; no extra space before message
        assert _FRAMES[0] in row0.text

    def test_is_not_focusable(self):
        state = {"frame": 0, "message": ""}
        spin = _SpinnerInteraction(state)
        assert spin.is_focusable is False

    def test_set_value_updates_frame(self):
        state = {"frame": 0, "message": ""}
        spin = _SpinnerInteraction(state)
        spin.set_value(5)
        assert state["frame"] == 5

    def test_get_value_returns_frame(self):
        state = {"frame": 7, "message": ""}
        spin = _SpinnerInteraction(state)
        assert spin.get_value() == 7

    def test_frames_cycle(self):
        assert len(_FRAMES) > 0
        # All frames are distinct (good animation)
        assert len(set(_FRAMES)) == len(_FRAMES)


class TestCancelInteractionSpinner:
    def test_cancel_sets_flag(self):
        state = {"cancelled": False}
        ci = _CancelInteraction(state)
        ci.handle_key('KEY_ENTER')
        assert state["cancelled"] is True

    def test_no_cancel_without_enter(self):
        state = {"cancelled": False}
        ci = _CancelInteraction(state)
        ci.handle_key('KEY_DOWN')
        assert state["cancelled"] is False


# ---------------------------------------------------------------------------
# Spinner context manager (no real I/O)
# ---------------------------------------------------------------------------

class _FakeParent:
    def __init__(self, term):
        self.terminal = term
        self._renderer = None


def run_spinner(keys, cancellable=True, title="Test", width=50):
    term = MockTerminal(width=80, height=24)
    term.feed_keys(keys)
    parent = _FakeParent(term)
    buf = io.StringIO()
    old, sys.stdout = sys.stdout, buf
    handle_ref = []
    try:
        with Spinner(title=title, cancellable=cancellable,
                     width=width).show(parent_shell=parent) as handle:
            handle.tick("step 1")
            handle_ref.append(handle)
    finally:
        sys.stdout = old
    return handle_ref[0]


class TestSpinnerContextManager:
    def test_tick_advances_frame(self):
        handle = run_spinner(keys=[], cancellable=False)
        # After one tick, frame should be 1
        assert handle._state["frame"] == 1

    def test_tick_updates_message(self):
        handle = run_spinner(keys=[], cancellable=False)
        assert handle._state["message"] == "step 1"

    def test_escape_cancels(self):
        handle = run_spinner(keys=[chr(27)], cancellable=True)
        assert handle.cancelled is True

    def test_ctrl_q_cancels(self):
        handle = run_spinner(keys=[chr(17)], cancellable=True)
        assert handle.cancelled is True

    def test_not_cancelled_by_default(self):
        handle = run_spinner(keys=[], cancellable=True)
        assert handle.cancelled is False

    def test_non_cancellable_mode(self):
        handle = run_spinner(keys=[], cancellable=False)
        assert handle.cancelled is False


# ---------------------------------------------------------------------------
# Toast unit tests
# ---------------------------------------------------------------------------

class TestToastInstantiation:
    def test_default_attributes(self):
        t = Toast(message="Hello")
        assert t.message == "Hello"
        assert t.title == "Notice"
        assert t.duration == 2.0
        assert t.width == 40

    def test_custom_attributes(self):
        t = Toast(message="Saved!", title="Done", duration=1.0, width=30)
        assert t.message == "Saved!"
        assert t.title == "Done"
        assert t.duration == 1.0
        assert t.width == 30


class TestToastShow:
    def test_show_renders_message(self, capsys):
        term = MockTerminal(width=80, height=24)
        # MockTerminal.inkey returns a falsy key immediately (queue empty)
        parent = _FakeParent(term)
        Toast(message="File saved", title="OK", duration=0.0,
              width=40).show(parent_shell=parent)
        out = capsys.readouterr().out
        assert 'File saved' in out

    def test_show_renders_title(self, capsys):
        term = MockTerminal(width=80, height=24)
        parent = _FakeParent(term)
        Toast(message="x", title="MyTitle", duration=0.0,
              width=40).show(parent_shell=parent)
        out = capsys.readouterr().out
        assert 'MyTitle' in out
