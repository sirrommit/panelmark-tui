"""Tests for _ScrollableList scroll behaviour in menu and checkbox interactions,
and for ListView / SubList display-only scrolling."""

import pytest
from panelmark_tui.testing import make_key
from panelmark_tui.interactions import MenuFunction, MenuReturn, MenuHybrid, CheckBox
from panelmark_tui.interactions.list_view import ListView, SubList
from panelmark.draw import RenderContext, WriteCmd, FillCmd


def ctx(height):
    """RenderContext that shows only *height* rows at a time."""
    return RenderContext(width=40, height=height)


def make_labels(n):
    """Return a dict with n labelled items suitable for MenuReturn."""
    return {f'Item {i}': i for i in range(n)}


# ---------------------------------------------------------------------------
# Helper: force a render so _last_height is set
# ---------------------------------------------------------------------------

def prime(interaction, height):
    """Render into a small context so _last_height is stored."""
    interaction.render(ctx(height), focused=False)
    return interaction


# ---------------------------------------------------------------------------
# MenuReturn scrolling
# ---------------------------------------------------------------------------

class TestMenuReturnScroll:
    def test_scroll_offset_advances_when_active_passes_viewport(self):
        m = MenuReturn(make_labels(10))
        prime(m, 3)              # viewport = 3 rows
        for _ in range(4):       # move down 4 times
            m.handle_key('KEY_DOWN')
        # active = 4, viewport height = 3 → offset must be at least 2
        assert m._scroll_offset >= 2
        assert m._active_index - m._scroll_offset < 3

    def test_active_always_within_viewport(self):
        m = MenuReturn(make_labels(20))
        prime(m, 5)
        for _ in range(19):
            m.handle_key('KEY_DOWN')
        assert m._active_index == 19
        assert m._scroll_offset <= 19
        assert m._active_index - m._scroll_offset < 5

    def test_scroll_offset_decreases_when_scrolling_up(self):
        m = MenuReturn(make_labels(10))
        prime(m, 3)
        for _ in range(9):       # go to bottom
            m.handle_key('KEY_DOWN')
        for _ in range(9):       # go back to top
            m.handle_key('KEY_UP')
        assert m._active_index == 0
        assert m._scroll_offset == 0

    def test_scroll_offset_zero_for_short_list(self):
        m = MenuReturn(make_labels(3))
        prime(m, 5)              # viewport larger than list
        m.handle_key('KEY_DOWN')
        m.handle_key('KEY_DOWN')
        assert m._scroll_offset == 0

    def test_j_k_navigation_scrolls(self):
        m = MenuReturn(make_labels(10))
        prime(m, 3)
        for _ in range(5):
            m.handle_key('j')
        assert m._active_index == 5
        assert m._active_index - m._scroll_offset < 3
        for _ in range(5):
            m.handle_key('k')
        assert m._active_index == 0
        assert m._scroll_offset == 0


# ---------------------------------------------------------------------------
# MenuFunction scrolling
# ---------------------------------------------------------------------------

class TestMenuFunctionScroll:
    def test_scroll_offset_advances(self):
        calls = []
        items = {f'Action {i}': (lambda i=i: calls.append(i)) for i in range(10)}
        m = MenuFunction(items)
        prime(m, 3)
        for _ in range(6):
            m.handle_key('KEY_DOWN')
        assert m._active_index == 6
        assert m._active_index - m._scroll_offset < 3

    def test_scroll_stays_zero_for_small_list(self):
        m = MenuFunction({'A': lambda s: None, 'B': lambda s: None})
        prime(m, 5)
        m.handle_key('KEY_DOWN')
        assert m._scroll_offset == 0


# ---------------------------------------------------------------------------
# MenuHybrid scrolling
# ---------------------------------------------------------------------------

class TestMenuHybridScroll:
    def test_scroll_offset_advances(self):
        items = {f'Item {i}': i for i in range(10)}
        m = MenuHybrid(items)
        prime(m, 4)
        for _ in range(8):
            m.handle_key('KEY_DOWN')
        assert m._active_index == 8
        assert m._active_index - m._scroll_offset < 4


# ---------------------------------------------------------------------------
# CheckBox scrolling
# ---------------------------------------------------------------------------

class TestCheckBoxScroll:
    def test_scroll_offset_advances(self):
        items = {f'Option {i}': False for i in range(10)}
        c = CheckBox(items)
        prime(c, 3)
        for _ in range(6):
            c.handle_key('KEY_DOWN')
        assert c._active_index == 6
        assert c._active_index - c._scroll_offset < 3

    def test_toggle_out_of_viewport_does_not_crash(self):
        """Toggling an item that is off-screen should not raise."""
        items = {f'Opt {i}': False for i in range(10)}
        c = CheckBox(items)
        prime(c, 3)
        for _ in range(7):
            c.handle_key('KEY_DOWN')
        changed, val = c.handle_key('KEY_ENTER')
        assert changed is True
        assert val[f'Opt {c._active_index}'] is True

    def test_scroll_up_restores_offset_to_zero(self):
        items = {f'O{i}': False for i in range(8)}
        c = CheckBox(items)
        prime(c, 3)
        for _ in range(7):
            c.handle_key('KEY_DOWN')
        for _ in range(7):
            c.handle_key('KEY_UP')
        assert c._active_index == 0
        assert c._scroll_offset == 0


# ---------------------------------------------------------------------------
# Render output — active item is inside the rendered commands
# ---------------------------------------------------------------------------

class TestScrollRender:
    def test_active_item_rendered_after_scroll(self):
        m = MenuReturn(make_labels(10))
        prime(m, 3)
        for _ in range(5):
            m.handle_key('KEY_DOWN')
        cmds = m.render(ctx(3), focused=True)
        texts = [c.text for c in cmds if isinstance(c, WriteCmd)]
        assert any('Item 5' in t for t in texts)

    def test_first_item_not_rendered_after_scroll(self):
        m = MenuReturn(make_labels(10))
        prime(m, 3)
        for _ in range(5):
            m.handle_key('KEY_DOWN')
        cmds = m.render(ctx(3), focused=False)
        texts = [c.text for c in cmds if isinstance(c, WriteCmd)]
        assert not any('Item 0' in t for t in texts)


# ---------------------------------------------------------------------------
# ListView scroll behaviour
# ---------------------------------------------------------------------------

class TestListViewScroll:
    def test_not_focusable_by_default(self):
        lv = ListView(['a', 'b', 'c'])
        assert lv.is_focusable is False

    def test_scroll_offset_zero_initially(self):
        lv = ListView(list(range(20)))
        assert lv._scroll_offset == 0

    def test_render_shows_first_n_items(self):
        lv = ListView(['alpha', 'beta', 'gamma', 'delta'])
        cmds = lv.render(ctx(2), focused=False)
        texts = [c.text for c in cmds if isinstance(c, WriteCmd)]
        assert any('alpha' in t for t in texts)
        assert any('beta' in t  for t in texts)
        assert not any('gamma' in t for t in texts)

    def test_scroll_by_shifts_visible_window(self):
        lv = ListView(list(f'Item {i}' for i in range(10)))
        prime(lv, 3)
        lv._scroll_by(3, 10)
        cmds = lv.render(ctx(3), focused=False)
        texts = [c.text for c in cmds if isinstance(c, WriteCmd)]
        assert any('Item 3' in t for t in texts)
        assert not any('Item 0' in t for t in texts)

    def test_fill_cmd_added_for_short_list(self):
        lv = ListView(['only'])
        cmds = lv.render(ctx(5), focused=False)
        assert any(isinstance(c, FillCmd) for c in cmds)

    def test_handle_key_up_scrolls(self):
        lv = ListView(list(f'R{i}' for i in range(10)))
        prime(lv, 3)
        lv._scroll_by(5, 10)
        lv.handle_key('KEY_UP')
        assert lv._scroll_offset == 4

    def test_handle_key_down_scrolls(self):
        lv = ListView(list(f'R{i}' for i in range(10)))
        prime(lv, 3)
        lv.handle_key('KEY_DOWN')
        assert lv._scroll_offset == 1

    def test_handle_key_home_resets_offset(self):
        lv = ListView(list(f'R{i}' for i in range(10)))
        prime(lv, 3)
        lv._scroll_by(5, 10)
        lv.handle_key('KEY_HOME')
        assert lv._scroll_offset == 0

    def test_handle_key_end_jumps_to_bottom(self):
        lv = ListView(list(f'R{i}' for i in range(10)))
        prime(lv, 3)
        lv.handle_key('KEY_END')
        assert lv._scroll_offset == 7  # 10 items - 3 height

    def test_handle_key_returns_false_and_items(self):
        items = ['x', 'y', 'z']
        lv = ListView(items)
        changed, value = lv.handle_key('KEY_DOWN')
        assert changed is False
        assert value == items

    def test_set_value_clamps_offset(self):
        lv = ListView(list(range(20)))
        prime(lv, 5)
        lv._scroll_by(15, 20)   # offset = 15
        lv.set_value(list(range(3)))  # shrink list to 3 items
        assert lv._scroll_offset == 0


# ---------------------------------------------------------------------------
# SubList scroll behaviour
# ---------------------------------------------------------------------------

class TestSubListScroll:
    def test_not_focusable(self):
        sl = SubList(['a', 'b'])
        assert sl.is_focusable is False

    def test_flat_items_rendered(self):
        sl = SubList(['foo', 'bar', 'baz'])
        cmds = sl.render(ctx(3), focused=False)
        texts = [c.text for c in cmds if isinstance(c, WriteCmd)]
        assert any('foo' in t for t in texts)
        assert any('bar' in t for t in texts)

    def test_nested_items_indented(self):
        sl = SubList(['top', ['child1', 'child2'], 'bottom'])
        cmds = sl.render(ctx(10), focused=False)
        texts = [c.text for c in cmds if isinstance(c, WriteCmd)]
        child_lines = [t for t in texts if 'child' in t]
        assert all(t.startswith('  ') for t in child_lines)

    def test_scroll_hides_top_items(self):
        sl = SubList(list(f'Item {i}' for i in range(10)))
        prime(sl, 3)
        sl._scroll_by(3, 10)
        cmds = sl.render(ctx(3), focused=False)
        texts = [c.text for c in cmds if isinstance(c, WriteCmd)]
        assert not any('Item 0' in t for t in texts)
        assert any('Item 3' in t for t in texts)
