"""Tests for the TreeView interaction."""

import pytest
from panelmark_tui.interactions import TreeView
from panelmark.draw import RenderContext, WriteCmd, FillCmd


def ctx(height=10, width=40):
    return RenderContext(width=width, height=height)


def prime(tv, height=5):
    """Render once so _last_height is set."""
    tv.render(ctx(height), focused=False)
    return tv


# ---------------------------------------------------------------------------
# Sample trees used across tests
# ---------------------------------------------------------------------------

SIMPLE = {
    'Documents': {
        'report.pdf': None,
        'notes.txt':  None,
    },
    'Pictures': {
        'photo.jpg': None,
    },
    'README.md': None,
}

FLAT = {
    'alpha': None,
    'beta':  None,
    'gamma': None,
}

DEEP = {
    'A': {
        'B': {
            'C': None,
        },
    },
}


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

class TestInitialState:
    def test_all_branches_collapsed_by_default(self):
        tv = TreeView(SIMPLE)
        items = tv._visible_items()
        labels = [item[1][-1] for item in items]
        # Only top-level items visible (branches collapsed)
        assert 'report.pdf' not in labels
        assert 'photo.jpg' not in labels

    def test_top_level_items_visible(self):
        tv = TreeView(SIMPLE)
        items = tv._visible_items()
        labels = [item[1][-1] for item in items]
        assert 'Documents' in labels
        assert 'Pictures' in labels
        assert 'README.md' in labels

    def test_initially_expanded_shows_all(self):
        tv = TreeView(SIMPLE, initially_expanded=True)
        items = tv._visible_items()
        labels = [item[1][-1] for item in items]
        assert 'report.pdf' in labels
        assert 'notes.txt' in labels
        assert 'photo.jpg' in labels

    def test_active_index_starts_at_zero(self):
        tv = TreeView(SIMPLE)
        assert tv._active_index == 0

    def test_get_value_returns_first_path(self):
        tv = TreeView(SIMPLE)
        val = tv.get_value()
        assert isinstance(val, tuple)
        assert len(val) == 1

    def test_signal_return_initially_false(self):
        tv = TreeView(SIMPLE)
        should_exit, _ = tv.signal_return()
        assert should_exit is False


# ---------------------------------------------------------------------------
# Branch / leaf identification
# ---------------------------------------------------------------------------

class TestItemTypes:
    def test_branch_is_branch(self):
        tv = TreeView(SIMPLE)
        items = tv._visible_items()
        docs = next(item for item in items if item[1] == ('Documents',))
        assert docs[2] is True  # is_branch

    def test_leaf_is_not_branch(self):
        tv = TreeView(SIMPLE)
        items = tv._visible_items()
        readme = next(item for item in items if item[1] == ('README.md',))
        assert readme[2] is False

    def test_nested_leaf_visible_when_expanded(self):
        tv = TreeView(SIMPLE)
        tv._expanded.add(('Documents',))
        items = tv._visible_items()
        paths = [item[1] for item in items]
        assert ('Documents', 'report.pdf') in paths
        assert ('Documents', 'notes.txt') in paths


# ---------------------------------------------------------------------------
# Display text
# ---------------------------------------------------------------------------

class TestDisplayText:
    def test_collapsed_branch_shows_close_marker(self):
        tv = TreeView(SIMPLE)
        items = tv._visible_items()
        docs = next(item for item in items if item[1] == ('Documents',))
        assert '▶' in docs[0]

    def test_expanded_branch_shows_open_marker(self):
        tv = TreeView(SIMPLE)
        tv._expanded.add(('Documents',))
        items = tv._visible_items()
        docs = next(item for item in items if item[1] == ('Documents',))
        assert '▼' in docs[0]

    def test_leaf_no_marker(self):
        tv = TreeView(SIMPLE)
        items = tv._visible_items()
        readme = next(item for item in items if item[1] == ('README.md',))
        assert '▶' not in readme[0]
        assert '▼' not in readme[0]

    def test_nested_item_indented(self):
        tv = TreeView(SIMPLE)
        tv._expanded.add(('Documents',))
        items = tv._visible_items()
        nested = next(item for item in items if item[1] == ('Documents', 'report.pdf'))
        assert nested[0].startswith(' ')  # has leading indent


# ---------------------------------------------------------------------------
# Expand / collapse via Enter
# ---------------------------------------------------------------------------

class TestExpandCollapse:
    def test_enter_on_branch_expands(self):
        tv = TreeView(SIMPLE)
        # First item is 'Documents' (a branch)
        tv._active_index = 0
        changed, val = tv.handle_key('KEY_ENTER')
        assert ('Documents',) in tv._expanded

    def test_enter_on_expanded_branch_collapses(self):
        tv = TreeView(SIMPLE)
        tv._expanded.add(('Documents',))
        tv._active_index = 0
        tv.handle_key('KEY_ENTER')
        assert ('Documents',) not in tv._expanded

    def test_space_toggles_branch(self):
        tv = TreeView(SIMPLE)
        tv._active_index = 0
        tv.handle_key(' ')
        assert ('Documents',) in tv._expanded
        tv.handle_key(' ')
        assert ('Documents',) not in tv._expanded

    def test_collapse_also_collapses_descendants(self):
        tv = TreeView(DEEP)
        tv._expanded.add(('A',))
        tv._expanded.add(('A', 'B'))
        tv._active_index = 0
        tv.handle_key('KEY_ENTER')  # collapse A
        assert ('A',) not in tv._expanded
        assert ('A', 'B') not in tv._expanded

    def test_expand_does_not_signal_exit(self):
        tv = TreeView(SIMPLE)
        tv._active_index = 0
        tv.handle_key('KEY_ENTER')
        should_exit, _ = tv.signal_return()
        assert should_exit is False

    def test_expand_returns_changed_true(self):
        tv = TreeView(SIMPLE)
        tv._active_index = 0
        changed, _ = tv.handle_key('KEY_ENTER')
        assert changed is True

    def test_cursor_clamped_after_collapse(self):
        tv = TreeView(SIMPLE)
        tv._expanded.add(('Documents',))
        items = tv._visible_items()
        tv._active_index = len(items) - 1   # move to last visible item
        tv._active_index = 0                # back to Documents
        tv.handle_key('KEY_ENTER')          # expand
        # Now collapse
        tv.handle_key('KEY_ENTER')
        new_items = tv._visible_items()
        assert tv._active_index < len(new_items)


# ---------------------------------------------------------------------------
# Leaf selection
# ---------------------------------------------------------------------------

class TestLeafSelection:
    def test_enter_on_leaf_signals_exit(self):
        tv = TreeView(SIMPLE)
        tv._expanded.add(('Documents',))
        items = tv._visible_items()
        # Find the index of 'report.pdf'
        idx = next(i for i, item in enumerate(items) if item[1] == ('Documents', 'report.pdf'))
        tv._active_index = idx
        tv.handle_key('KEY_ENTER')
        should_exit, val = tv.signal_return()
        assert should_exit is True
        assert val == ('Documents', 'report.pdf')

    def test_enter_on_leaf_returns_changed_true(self):
        tv = TreeView(FLAT)
        tv._active_index = 0
        changed, val = tv.handle_key('KEY_ENTER')
        assert changed is True

    def test_space_on_leaf_signals_exit(self):
        tv = TreeView(FLAT)
        tv._active_index = 0
        tv.handle_key(' ')
        should_exit, val = tv.signal_return()
        assert should_exit is True

    def test_exit_value_is_path_tuple(self):
        tv = TreeView(FLAT)
        tv._active_index = 0
        tv.handle_key('KEY_ENTER')
        _, val = tv.signal_return()
        assert isinstance(val, tuple)
        assert len(val) == 1

    def test_signal_return_cleared_on_next_key(self):
        tv = TreeView(FLAT)
        tv._active_index = 0
        tv.handle_key('KEY_ENTER')
        tv.handle_key('KEY_DOWN')
        should_exit, _ = tv.signal_return()
        assert should_exit is False


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

class TestNavigation:
    def test_down_moves_cursor(self):
        tv = TreeView(SIMPLE)
        prime(tv)
        initial = tv._active_index
        tv.handle_key('KEY_DOWN')
        assert tv._active_index == initial + 1

    def test_up_moves_cursor(self):
        tv = TreeView(SIMPLE)
        prime(tv)
        tv.handle_key('KEY_DOWN')
        tv.handle_key('KEY_UP')
        assert tv._active_index == 0

    def test_down_clamps_at_last(self):
        tv = TreeView(FLAT)
        prime(tv)
        for _ in range(10):
            tv.handle_key('KEY_DOWN')
        assert tv._active_index == len(FLAT) - 1

    def test_home_jumps_to_first(self):
        tv = TreeView(SIMPLE)
        prime(tv)
        tv.handle_key('KEY_DOWN')
        tv.handle_key('KEY_DOWN')
        tv.handle_key('KEY_HOME')
        assert tv._active_index == 0

    def test_end_jumps_to_last(self):
        tv = TreeView(SIMPLE)
        prime(tv)
        tv.handle_key('KEY_END')
        items = tv._visible_items()
        assert tv._active_index == len(items) - 1

    def test_page_down_jumps_forward(self):
        tv = TreeView(SIMPLE, initially_expanded=True)
        prime(tv, height=3)
        tv.handle_key('KEY_NPAGE')
        assert tv._active_index == 3

    def test_navigation_through_expanded_tree(self):
        tv = TreeView(SIMPLE)
        prime(tv, height=10)
        # Expand Documents
        tv._active_index = 0
        tv.handle_key('KEY_ENTER')
        items = tv._visible_items()
        # Move through all items
        for _ in range(len(items) - 1):
            tv.handle_key('KEY_DOWN')
        assert tv._active_index == len(items) - 1

    def test_get_value_tracks_cursor(self):
        tv = TreeView(SIMPLE)
        prime(tv)
        tv.handle_key('KEY_DOWN')
        val = tv.get_value()
        items = tv._visible_items()
        assert val == items[tv._active_index][1]

    def test_j_k_vi_keys(self):
        tv = TreeView(FLAT)
        prime(tv)
        tv.handle_key('j')
        assert tv._active_index == 1
        tv.handle_key('k')
        assert tv._active_index == 0

    def test_unhandled_key_returns_false(self):
        tv = TreeView(FLAT)
        changed, _ = tv.handle_key('x')
        assert changed is False


# ---------------------------------------------------------------------------
# Scroll behaviour
# ---------------------------------------------------------------------------

class TestScrolling:
    def test_active_item_stays_in_viewport_after_down(self):
        tv = TreeView(SIMPLE, initially_expanded=True)
        prime(tv, height=3)
        items = tv._visible_items()
        for _ in range(len(items) - 1):
            tv.handle_key('KEY_DOWN')
        assert tv._active_index - tv._scroll_offset < 3

    def test_scroll_offset_zero_for_short_list(self):
        tv = TreeView(FLAT)
        prime(tv, height=10)
        for _ in range(2):
            tv.handle_key('KEY_DOWN')
        assert tv._scroll_offset == 0


# ---------------------------------------------------------------------------
# set_value
# ---------------------------------------------------------------------------

class TestSetValue:
    def test_set_value_jumps_to_visible_item(self):
        tv = TreeView(FLAT)
        prime(tv)
        tv.set_value(('gamma',))
        assert tv.get_value() == ('gamma',)

    def test_set_value_expands_ancestors(self):
        tv = TreeView(SIMPLE)
        prime(tv)
        tv.set_value(('Documents', 'notes.txt'))
        assert ('Documents',) in tv._expanded
        assert tv.get_value() == ('Documents', 'notes.txt')

    def test_set_value_deeply_nested_expands_all_ancestors(self):
        tv = TreeView(DEEP)
        prime(tv)
        tv.set_value(('A', 'B', 'C'))
        assert ('A',) in tv._expanded
        assert ('A', 'B') in tv._expanded
        assert tv.get_value() == ('A', 'B', 'C')

    def test_set_value_invalid_does_not_crash(self):
        tv = TreeView(FLAT)
        tv.set_value(None)  # should be silently ignored
        tv.set_value(())    # empty tuple ignored


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

class TestRender:
    def test_render_returns_draw_commands(self):
        tv = TreeView(SIMPLE)
        cmds = tv.render(ctx(), focused=False)
        assert isinstance(cmds, list)
        assert any(isinstance(c, WriteCmd) for c in cmds)

    def test_render_active_row_reversed_when_focused(self):
        tv = TreeView(FLAT)
        cmds = tv.render(ctx(), focused=True)
        reversed_cmds = [c for c in cmds if isinstance(c, WriteCmd) and c.style == {'reverse': True}]
        assert len(reversed_cmds) == 1

    def test_render_fill_for_short_tree(self):
        tv = TreeView(FLAT)
        cmds = tv.render(ctx(height=10), focused=False)
        assert any(isinstance(c, FillCmd) for c in cmds)

    def test_render_shows_branch_marker(self):
        tv = TreeView(SIMPLE)
        cmds = tv.render(ctx(), focused=False)
        texts = ''.join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert '▶' in texts

    def test_render_shows_open_marker_after_expand(self):
        tv = TreeView(SIMPLE)
        tv._expanded.add(('Documents',))
        cmds = tv.render(ctx(), focused=False)
        texts = ''.join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert '▼' in texts

    def test_render_children_visible_after_expand(self):
        tv = TreeView(SIMPLE)
        tv._expanded.add(('Documents',))
        cmds = tv.render(ctx(height=10), focused=False)
        texts = ''.join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert 'report.pdf' in texts
        assert 'notes.txt' in texts

    def test_render_children_hidden_when_collapsed(self):
        tv = TreeView(SIMPLE, initially_expanded=True)
        tv._expanded.clear()
        cmds = tv.render(ctx(height=10), focused=False)
        texts = ''.join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert 'report.pdf' not in texts

    def test_initially_expanded_render(self):
        tv = TreeView(SIMPLE, initially_expanded=True)
        cmds = tv.render(ctx(height=20), focused=False)
        texts = ''.join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert 'photo.jpg' in texts


# ---------------------------------------------------------------------------
# is_focusable
# ---------------------------------------------------------------------------

class TestFocusable:
    def test_is_focusable_true(self):
        tv = TreeView(FLAT)
        assert tv.is_focusable is True


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_tree(self):
        tv = TreeView({})
        items = tv._visible_items()
        assert items == []
        assert tv.get_value() is None

    def test_enter_on_empty_tree(self):
        tv = TreeView({})
        changed, val = tv.handle_key('KEY_ENTER')
        assert changed is False
        assert val is None

    def test_flat_tree_no_branches(self):
        tv = TreeView(FLAT)
        items = tv._visible_items()
        assert all(not item[2] for item in items)

    def test_all_branches_tree(self):
        tv = TreeView({'A': {'B': {'C': {}}}, })
        items = tv._visible_items()
        assert len(items) == 1  # only 'A' visible (collapsed)
