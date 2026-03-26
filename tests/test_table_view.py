"""Tests for TableView interaction."""

import pytest
from panelmark_tui.interactions import TableView
from panelmark.draw import RenderContext, WriteCmd, FillCmd


COLS = [("Name", 10), ("Status", 8), ("Score", 5)]
ROWS = [
    ["Alice",   "active", "95"],
    ["Bob",     "idle",   "72"],
    ["Charlie", "active", "88"],
]


def ctx(width=40, height=8):
    return RenderContext(width=width, height=height,
                        capabilities=frozenset({'color', 'cursor', 'bold'}))


class TestTableViewRender:
    def test_render_returns_commands(self):
        t = TableView(COLS, ROWS)
        cmds = t.render(ctx(), focused=False)
        assert isinstance(cmds, list)
        assert len(cmds) > 0

    def test_header_at_row_0(self):
        t = TableView(COLS, ROWS)
        cmds = t.render(ctx(), focused=False)
        row0 = next(c for c in cmds if isinstance(c, WriteCmd) and c.row == 0)
        assert 'Name' in row0.text
        assert 'Status' in row0.text
        assert 'Score' in row0.text

    def test_data_rows_start_at_row_1(self):
        t = TableView(COLS, ROWS)
        cmds = t.render(ctx(), focused=False)
        data_rows = [c for c in cmds if isinstance(c, WriteCmd) and c.row > 0]
        assert len(data_rows) == len(ROWS)

    def test_cell_content_appears(self):
        t = TableView(COLS, ROWS)
        cmds = t.render(ctx(), focused=False)
        all_text = ' '.join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert 'Alice' in all_text
        assert 'Bob' in all_text

    def test_active_row_reversed_when_focused(self):
        t = TableView(COLS, ROWS)
        cmds = t.render(ctx(), focused=True)
        # Row 1 (data row index 0) should be reversed
        active = next(c for c in cmds if isinstance(c, WriteCmd) and c.row == 1)
        assert active.style == {'reverse': True}

    def test_header_bold_when_unfocused(self):
        t = TableView(COLS, ROWS)
        cmds = t.render(ctx(), focused=False)
        header = next(c for c in cmds if isinstance(c, WriteCmd) and c.row == 0)
        assert header.style == {'bold': True}

    def test_header_reversed_when_focused(self):
        t = TableView(COLS, ROWS)
        cmds = t.render(ctx(), focused=True)
        header = next(c for c in cmds if isinstance(c, WriteCmd) and c.row == 0)
        assert header.style == {'reverse': True}

    def test_trailing_fill_when_fewer_rows(self):
        t = TableView(COLS, [['A', 'B', 'C']])
        cmds = t.render(ctx(height=8), focused=False)
        assert any(isinstance(c, FillCmd) for c in cmds)

    def test_column_separator_present(self):
        t = TableView(COLS, ROWS)
        cmds = t.render(ctx(), focused=False)
        data_row = next(c for c in cmds if isinstance(c, WriteCmd) and c.row == 1)
        assert '│' in data_row.text

    def test_height_1_shows_only_header(self):
        t = TableView(COLS, ROWS)
        cmds = t.render(ctx(height=1), focused=False)
        write_cmds = [c for c in cmds if isinstance(c, WriteCmd)]
        assert len(write_cmds) == 1
        assert write_cmds[0].row == 0

    def test_is_focusable(self):
        t = TableView(COLS, ROWS)
        assert t.is_focusable is True

    def test_empty_rows(self):
        t = TableView(COLS, [])
        cmds = t.render(ctx(), focused=False)
        assert any(isinstance(c, WriteCmd) and c.row == 0 for c in cmds)


class TestTableViewNavigation:
    def test_initial_value_is_zero(self):
        t = TableView(COLS, ROWS)
        assert t.get_value() == 0

    def test_down_increments_active(self):
        t = TableView(COLS, ROWS)
        t.render(ctx(), focused=True)
        changed, val = t.handle_key('KEY_DOWN')
        assert changed is True
        assert val == 1

    def test_up_at_top_clamps(self):
        t = TableView(COLS, ROWS)
        t.handle_key('KEY_UP')
        assert t.get_value() == 0

    def test_down_at_bottom_clamps(self):
        t = TableView(COLS, ROWS)
        t.render(ctx(), focused=True)
        t.handle_key('KEY_END')
        t.handle_key('KEY_DOWN')
        assert t.get_value() == len(ROWS) - 1

    def test_home_end(self):
        t = TableView(COLS, ROWS)
        t.render(ctx(), focused=True)
        t.handle_key('KEY_END')
        assert t.get_value() == 2
        t.handle_key('KEY_HOME')
        assert t.get_value() == 0

    def test_vi_keys(self):
        t = TableView(COLS, ROWS)
        t.render(ctx(), focused=True)
        t.handle_key('j')
        assert t.get_value() == 1
        t.handle_key('k')
        assert t.get_value() == 0

    def test_empty_table_navigation_is_noop(self):
        t = TableView(COLS, [])
        changed, val = t.handle_key('KEY_DOWN')
        assert changed is False
        assert val == 0

    def test_irrelevant_key_returns_false(self):
        t = TableView(COLS, ROWS)
        changed, _ = t.handle_key('a')
        assert changed is False


class TestTableViewSetValue:
    def test_set_value_moves_cursor(self):
        t = TableView(COLS, ROWS)
        t.set_value(2)
        assert t.get_value() == 2

    def test_set_value_clamps_above_range(self):
        t = TableView(COLS, ROWS)
        t.set_value(100)
        assert t.get_value() == len(ROWS) - 1

    def test_set_value_clamps_below_zero(self):
        t = TableView(COLS, ROWS)
        t.set_value(1)
        t.set_value(-1)
        assert t.get_value() == 0

    def test_set_value_empty_table(self):
        t = TableView(COLS, [])
        t.set_value(5)   # should not raise
        assert t.get_value() == 0


class TestTableViewScroll:
    def test_scroll_follows_active_row(self):
        many_rows = [[str(i), 'x', str(i)] for i in range(30)]
        t = TableView(COLS, many_rows)
        t.render(ctx(height=5), focused=True)
        t.handle_key('KEY_END')
        assert t._scroll_offset <= t._active_index
        assert t._active_index < t._scroll_offset + t._last_height

    def test_last_height_is_data_height(self):
        t = TableView(COLS, ROWS)
        t.render(ctx(height=6), focused=False)
        # _last_height should be height - 1 (excluding header)
        assert t._last_height == 5
