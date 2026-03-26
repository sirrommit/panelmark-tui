"""Tests for RadioList interaction."""

import pytest
from panelmark_tui.interactions import RadioList
from panelmark.draw import RenderContext, WriteCmd, FillCmd


def ctx(width=40, height=10):
    return RenderContext(width=width, height=height,
                        capabilities=frozenset({'color', 'cursor'}))


class TestRadioListValue:
    def test_initial_value_is_first(self):
        r = RadioList({'Small': 's', 'Medium': 'm', 'Large': 'l'})
        assert r.get_value() == 's'

    def test_navigate_down_updates_value(self):
        r = RadioList({'A': 1, 'B': 2, 'C': 3})
        changed, val = r.handle_key('KEY_DOWN')
        assert changed is True
        assert val == 2

    def test_navigate_up_at_top_clamps(self):
        r = RadioList({'A': 1, 'B': 2})
        r.handle_key('KEY_UP')
        assert r.get_value() == 1

    def test_navigate_down_at_bottom_clamps(self):
        r = RadioList({'A': 1, 'B': 2})
        r.handle_key('KEY_DOWN')
        r.handle_key('KEY_DOWN')
        assert r.get_value() == 2

    def test_vi_keys(self):
        r = RadioList({'A': 1, 'B': 2, 'C': 3})
        r.handle_key('j')
        assert r.get_value() == 2
        r.handle_key('k')
        assert r.get_value() == 1

    def test_home_end(self):
        r = RadioList({'A': 1, 'B': 2, 'C': 3})
        r.handle_key('KEY_END')
        assert r.get_value() == 3
        r.handle_key('KEY_HOME')
        assert r.get_value() == 1

    def test_page_up_down(self):
        items = {str(i): i for i in range(20)}
        r = RadioList(items)
        r.handle_key('KEY_NPAGE')
        # Should jump by page_size (default _last_height=10)
        assert r.get_value() == 10
        r.handle_key('KEY_PPAGE')
        assert r.get_value() == 0


class TestRadioListSignalReturn:
    def test_no_exit_on_navigation(self):
        r = RadioList({'A': 1, 'B': 2})
        r.handle_key('KEY_DOWN')
        should_exit, rv = r.signal_return()
        assert should_exit is False

    def test_enter_signals_exit_with_value(self):
        r = RadioList({'A': 1, 'B': 2})
        r.handle_key('KEY_ENTER')
        should_exit, rv = r.signal_return()
        assert should_exit is True
        assert rv == 1

    def test_enter_after_navigation(self):
        r = RadioList({'A': 1, 'B': 2, 'C': 3})
        r.handle_key('KEY_DOWN')
        r.handle_key('KEY_DOWN')
        r.handle_key('KEY_ENTER')
        should_exit, rv = r.signal_return()
        assert should_exit is True
        assert rv == 3

    def test_space_signals_exit(self):
        r = RadioList({'A': 1, 'B': 2})
        r.handle_key(' ')
        should_exit, rv = r.signal_return()
        assert should_exit is True
        assert rv == 1

    def test_signal_return_cleared_on_next_key(self):
        r = RadioList({'A': 1, 'B': 2})
        r.handle_key('KEY_ENTER')
        r.handle_key('KEY_DOWN')
        should_exit, _ = r.signal_return()
        assert should_exit is False

    def test_initial_signal_return_false(self):
        r = RadioList({'A': 1})
        should_exit, rv = r.signal_return()
        assert should_exit is False


class TestRadioListSetValue:
    def test_set_value_moves_cursor(self):
        r = RadioList({'A': 1, 'B': 2, 'C': 3})
        r.set_value(3)
        assert r.get_value() == 3

    def test_set_value_unknown_noop(self):
        r = RadioList({'A': 1, 'B': 2})
        r.set_value(99)
        assert r.get_value() == 1   # unchanged

    def test_set_value_then_enter_returns_correct(self):
        r = RadioList({'A': 1, 'B': 2, 'C': 3})
        r.set_value(2)
        r.handle_key('KEY_ENTER')
        _, rv = r.signal_return()
        assert rv == 2


class TestRadioListRender:
    def test_render_returns_commands(self):
        r = RadioList({'A': 1, 'B': 2})
        cmds = r.render(ctx(), focused=True)
        assert isinstance(cmds, list)
        assert any(isinstance(c, WriteCmd) for c in cmds)

    def test_selected_item_has_filled_marker(self):
        r = RadioList({'A': 1, 'B': 2})
        cmds = r.render(ctx(), focused=False)
        texts = [c.text for c in cmds if isinstance(c, WriteCmd)]
        assert any('(●)' in t for t in texts)

    def test_unselected_items_have_empty_marker(self):
        r = RadioList({'A': 1, 'B': 2, 'C': 3})
        cmds = r.render(ctx(), focused=False)
        texts = [c.text for c in cmds if isinstance(c, WriteCmd)]
        assert sum('( )' in t for t in texts) == 2

    def test_focused_active_row_reversed(self):
        r = RadioList({'A': 1, 'B': 2})
        cmds = r.render(ctx(), focused=True)
        active = next(c for c in cmds if isinstance(c, WriteCmd) and c.row == 0)
        assert active.style == {'reverse': True}

    def test_trailing_fill_when_fewer_items_than_height(self):
        r = RadioList({'A': 1})
        cmds = r.render(ctx(height=5), focused=False)
        assert any(isinstance(c, FillCmd) for c in cmds)

    def test_render_clips_to_width(self):
        long_label = 'X' * 100
        r = RadioList({long_label: 1})
        cmds = r.render(ctx(width=20), focused=False)
        for c in cmds:
            if isinstance(c, WriteCmd):
                assert len(c.text) <= 20

    def test_is_focusable(self):
        r = RadioList({'A': 1})
        assert r.is_focusable is True


class TestRadioListScroll:
    def test_scroll_follows_cursor(self):
        items = {str(i): i for i in range(20)}
        r = RadioList(items)
        # Render with small height to set _last_height
        r.render(ctx(height=5), focused=True)
        for _ in range(10):
            r.handle_key('KEY_DOWN')
        # scroll_offset should have advanced so active index is visible
        assert r._scroll_offset <= r._active_index
        assert r._active_index < r._scroll_offset + 5
