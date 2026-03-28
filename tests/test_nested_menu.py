"""Tests for the NestedMenu interaction and Leaf sentinel."""

import pytest
from panelmark_tui.interactions import NestedMenu, Leaf
from panelmark.draw import RenderContext, WriteCmd, FillCmd


def ctx(height=10, width=40):
    return RenderContext(width=width, height=height)


def prime(nm, height=5):
    """Render once so _last_height is set."""
    nm.render(ctx(height), focused=False)
    return nm


# ---------------------------------------------------------------------------
# Sample menus used across tests
# ---------------------------------------------------------------------------

SIMPLE = {
    "File": {
        "New":  "file:new",
        "Save": "file:save",
    },
    "Edit": {
        "Cut":  "edit:cut",
        "Copy": "edit:copy",
    },
    "Quit": "quit",
}

FLAT = {
    "Alpha": "a",
    "Beta":  "b",
    "Gamma": "g",
}

DEEP = {
    "A": {
        "B": {
            "C": "deep:c",
        },
    },
}

MIXED = {
    "Top":  "top:val",
    "Sub":  {
        "Child": "sub:child",
    },
}


# ---------------------------------------------------------------------------
# 1. Input normalization — shorthand nested dict
# ---------------------------------------------------------------------------

class TestNormalization:
    def test_string_leaf_wrapped_in_leaf(self):
        nm = NestedMenu(FLAT)
        assert isinstance(nm._tree["Alpha"], Leaf)
        assert nm._tree["Alpha"].value == "a"

    def test_int_leaf_wrapped_in_leaf(self):
        nm = NestedMenu({"X": 42})
        assert nm._tree["X"].value == 42

    def test_branch_stays_as_dict(self):
        nm = NestedMenu(SIMPLE)
        assert isinstance(nm._tree["File"], dict)

    def test_nested_branch_normalized_recursively(self):
        nm = NestedMenu(SIMPLE)
        assert isinstance(nm._tree["File"]["New"], Leaf)
        assert nm._tree["File"]["New"].value == "file:new"

    def test_order_preserved(self):
        nm = NestedMenu(SIMPLE)
        assert list(nm._tree.keys()) == ["File", "Edit", "Quit"]

    def test_leaf_wrapping_dict_payload(self):
        payload = {"format": "csv"}
        nm = NestedMenu({"Export": Leaf(payload)})
        assert nm._tree["Export"].value == payload

    def test_leaf_wrapping_dict_payload_not_treated_as_branch(self):
        nm = NestedMenu({"Export": Leaf({"k": "v"})})
        assert isinstance(nm._tree["Export"], Leaf)
        assert not isinstance(nm._tree["Export"], dict)


# ---------------------------------------------------------------------------
# 2. Malformed input detection
# ---------------------------------------------------------------------------

class TestMalformedInput:
    def test_empty_root_raises(self):
        with pytest.raises(ValueError, match="root"):
            NestedMenu({})

    def test_empty_branch_raises(self):
        with pytest.raises(ValueError):
            NestedMenu({"File": {}})

    def test_duplicate_sibling_labels_raises(self):
        # Python dicts can't have duplicate keys at the language level, so
        # test via _normalize directly with a contrived scenario — the check
        # also protects against subclasses or alternative dict types.
        from panelmark_tui.interactions.nested_menu import _normalize
        # Simulate by calling _normalize with a normal dict (no dups possible
        # at syntax level); instead verify the guard exists by patching items()
        # to yield duplicates.
        class DupDict(dict):
            def items(self):
                yield "A", "x"
                yield "A", "y"
        with pytest.raises(ValueError, match="Duplicate"):
            _normalize(DupDict({"A": "x"}))

    def test_none_leaf_raises(self):
        with pytest.raises(ValueError):
            NestedMenu({"X": None})

    def test_leaf_none_raises_at_construction(self):
        with pytest.raises(ValueError):
            Leaf(None)

    def test_non_dict_root_raises(self):
        with pytest.raises(TypeError):
            NestedMenu(["a", "b"])

    def test_non_string_label_raises(self):
        from panelmark_tui.interactions.nested_menu import _normalize
        with pytest.raises(TypeError, match="strings"):
            _normalize({1: "value"})


# ---------------------------------------------------------------------------
# 3. Initial state
# ---------------------------------------------------------------------------

class TestInitialState:
    def test_starts_at_root(self):
        nm = NestedMenu(SIMPLE)
        assert nm._current_path == ()

    def test_active_index_zero(self):
        nm = NestedMenu(SIMPLE)
        assert nm._active_index == 0

    def test_get_value_returns_first_label_tuple(self):
        nm = NestedMenu(SIMPLE)
        assert nm.get_value() == ("File",)

    def test_signal_return_initially_false(self):
        nm = NestedMenu(SIMPLE)
        ok, val = nm.signal_return()
        assert ok is False
        assert val is None

    def test_is_focusable(self):
        nm = NestedMenu(SIMPLE)
        assert nm.is_focusable is True


# ---------------------------------------------------------------------------
# 4. Navigation within a level
# ---------------------------------------------------------------------------

class TestNavigation:
    def test_down_moves_cursor(self):
        nm = NestedMenu(SIMPLE)
        prime(nm)
        nm.handle_key('KEY_DOWN')
        assert nm._active_index == 1

    def test_up_from_zero_clamps(self):
        nm = NestedMenu(SIMPLE)
        prime(nm)
        nm.handle_key('KEY_UP')
        assert nm._active_index == 0

    def test_down_clamps_at_last(self):
        nm = NestedMenu(FLAT)
        prime(nm)
        for _ in range(10):
            nm.handle_key('KEY_DOWN')
        assert nm._active_index == len(FLAT) - 1

    def test_home_jumps_to_first(self):
        nm = NestedMenu(FLAT)
        prime(nm)
        nm.handle_key('KEY_DOWN')
        nm.handle_key('KEY_DOWN')
        nm.handle_key('KEY_HOME')
        assert nm._active_index == 0

    def test_end_jumps_to_last(self):
        nm = NestedMenu(FLAT)
        prime(nm)
        nm.handle_key('KEY_END')
        assert nm._active_index == len(FLAT) - 1

    def test_j_k_vi_keys(self):
        nm = NestedMenu(FLAT)
        prime(nm)
        nm.handle_key('j')
        assert nm._active_index == 1
        nm.handle_key('k')
        assert nm._active_index == 0

    def test_get_value_tracks_cursor(self):
        nm = NestedMenu(FLAT)
        prime(nm)
        nm.handle_key('KEY_DOWN')
        assert nm.get_value() == ("Beta",)

    def test_unhandled_key_returns_false(self):
        nm = NestedMenu(FLAT)
        changed, _ = nm.handle_key('x')
        assert changed is False


# ---------------------------------------------------------------------------
# 5. Descending into branches
# ---------------------------------------------------------------------------

class TestDescend:
    def test_enter_on_branch_descends(self):
        nm = NestedMenu(SIMPLE)
        prime(nm)
        nm._active_index = 0   # "File"
        nm.handle_key('KEY_ENTER')
        assert nm._current_path == ("File",)

    def test_space_on_branch_descends(self):
        nm = NestedMenu(SIMPLE)
        prime(nm)
        nm._active_index = 0
        nm.handle_key(' ')
        assert nm._current_path == ("File",)

    def test_descend_resets_active_index(self):
        nm = NestedMenu(SIMPLE)
        prime(nm)
        nm._active_index = 1   # "Edit"
        nm.handle_key('KEY_ENTER')
        assert nm._active_index == 0

    def test_descend_does_not_signal_return(self):
        nm = NestedMenu(SIMPLE)
        prime(nm)
        nm._active_index = 0
        nm.handle_key('KEY_ENTER')
        ok, _ = nm.signal_return()
        assert ok is False

    def test_get_value_inside_branch(self):
        nm = NestedMenu(SIMPLE)
        prime(nm)
        nm._active_index = 0   # "File"
        nm.handle_key('KEY_ENTER')
        # Now inside File, first item is "New"
        assert nm.get_value() == ("File", "New")

    def test_descend_into_deep_branch(self):
        nm = NestedMenu(DEEP)
        prime(nm)
        nm.handle_key('KEY_ENTER')   # into A
        nm.handle_key('KEY_ENTER')   # into A > B
        assert nm._current_path == ("A", "B")
        assert nm.get_value() == ("A", "B", "C")


# ---------------------------------------------------------------------------
# 6. Leaf acceptance
# ---------------------------------------------------------------------------

class TestLeafAccept:
    def test_enter_on_leaf_signals_return(self):
        nm = NestedMenu(FLAT)
        prime(nm)
        nm._active_index = 0   # "Alpha" -> "a"
        nm.handle_key('KEY_ENTER')
        ok, val = nm.signal_return()
        assert ok is True
        assert val == "a"

    def test_space_on_leaf_signals_return(self):
        nm = NestedMenu(FLAT)
        prime(nm)
        nm.handle_key(' ')
        ok, val = nm.signal_return()
        assert ok is True

    def test_leaf_inside_branch_signals_return(self):
        nm = NestedMenu(SIMPLE)
        prime(nm)
        nm._active_index = 0   # "File"
        nm.handle_key('KEY_ENTER')   # descend into File
        nm._active_index = 1         # "Save"
        nm.handle_key('KEY_ENTER')
        ok, val = nm.signal_return()
        assert ok is True
        assert val == "file:save"

    def test_leaf_payload_is_mapped_value_not_label(self):
        nm = NestedMenu({"Go": "go:action"})
        prime(nm)
        nm.handle_key('KEY_ENTER')
        _, val = nm.signal_return()
        assert val == "go:action"

    def test_leaf_dict_payload_via_leaf_wrapper(self):
        payload = {"fmt": "csv"}
        nm = NestedMenu({"Export": Leaf(payload)})
        prime(nm)
        nm.handle_key('KEY_ENTER')
        ok, val = nm.signal_return()
        assert ok is True
        assert val == payload

    def test_signal_return_cleared_on_next_key(self):
        nm = NestedMenu(FLAT)
        prime(nm)
        nm.handle_key('KEY_ENTER')
        nm.handle_key('KEY_DOWN')
        ok, _ = nm.signal_return()
        assert ok is False


# ---------------------------------------------------------------------------
# 7. Going back / backtracking
# ---------------------------------------------------------------------------

class TestGoBack:
    def test_left_goes_back_to_parent(self):
        nm = NestedMenu(SIMPLE)
        prime(nm)
        nm._active_index = 0
        nm.handle_key('KEY_ENTER')   # into File
        nm.handle_key('KEY_LEFT')    # back to root
        assert nm._current_path == ()

    def test_h_goes_back(self):
        nm = NestedMenu(SIMPLE)
        prime(nm)
        nm.handle_key('KEY_ENTER')
        nm.handle_key('h')
        assert nm._current_path == ()

    def test_back_restores_parent_active_index(self):
        nm = NestedMenu(SIMPLE)
        prime(nm)
        nm._active_index = 1   # "Edit"
        nm.handle_key('KEY_ENTER')
        nm.handle_key('KEY_LEFT')
        assert nm._active_index == 1

    def test_back_restores_parent_scroll_offset(self):
        nm = NestedMenu(SIMPLE)
        prime(nm, height=2)
        nm._active_index = 2   # "Quit" — may have scrolled
        nm._scroll_offset = 1
        nm.handle_key('KEY_ENTER')   # Quit is a leaf, will signal exit
        # Reset for back test: descend into Edit instead
        nm2 = NestedMenu(SIMPLE)
        prime(nm2, height=2)
        nm2._active_index = 1        # "Edit"
        nm2._scroll_offset = 1
        nm2.handle_key('KEY_ENTER')
        nm2.handle_key('KEY_LEFT')
        assert nm2._scroll_offset == 1

    def test_back_from_root_does_nothing(self):
        nm = NestedMenu(SIMPLE)
        prime(nm)
        changed, _ = nm.handle_key('KEY_LEFT')
        assert changed is False
        assert nm._current_path == ()

    def test_back_does_not_signal_return(self):
        nm = NestedMenu(SIMPLE)
        prime(nm)
        nm.handle_key('KEY_ENTER')
        nm.handle_key('KEY_LEFT')
        ok, _ = nm.signal_return()
        assert ok is False

    def test_back_from_deep_nesting(self):
        nm = NestedMenu(DEEP)
        prime(nm)
        nm.handle_key('KEY_ENTER')   # into A
        nm.handle_key('KEY_ENTER')   # into A > B
        nm.handle_key('KEY_LEFT')    # back to A
        assert nm._current_path == ("A",)
        nm.handle_key('KEY_LEFT')    # back to root
        assert nm._current_path == ()


# ---------------------------------------------------------------------------
# 8. Root cancel
# ---------------------------------------------------------------------------

class TestRootCancel:
    def test_back_at_root_returns_changed_false(self):
        nm = NestedMenu(SIMPLE)
        changed, _ = nm.handle_key('KEY_LEFT')
        assert changed is False

    def test_signal_return_never_fires_from_back_at_root(self):
        nm = NestedMenu(SIMPLE)
        nm.handle_key('KEY_LEFT')
        ok, val = nm.signal_return()
        assert ok is False
        assert val is None


# ---------------------------------------------------------------------------
# 9. get_value / set_value round-trip
# ---------------------------------------------------------------------------

class TestGetSetRoundTrip:
    def test_round_trip_root_leaf(self):
        nm = NestedMenu(FLAT)
        prime(nm)
        nm.handle_key('KEY_DOWN')
        original = nm.get_value()
        nm.set_value(original)
        assert nm.get_value() == original

    def test_round_trip_nested_leaf(self):
        nm = NestedMenu(SIMPLE)
        prime(nm)
        nm.handle_key('KEY_ENTER')   # into File
        nm.handle_key('KEY_DOWN')    # "Save"
        original = nm.get_value()
        assert original == ("File", "Save")
        nm2 = NestedMenu(SIMPLE)
        nm2.set_value(original)
        assert nm2.get_value() == original

    def test_set_value_descends_into_correct_level(self):
        nm = NestedMenu(SIMPLE)
        nm.set_value(("Edit", "Copy"))
        assert nm._current_path == ("Edit",)
        assert nm.get_value() == ("Edit", "Copy")

    def test_set_value_deep_path(self):
        nm = NestedMenu(DEEP)
        nm.set_value(("A", "B", "C"))
        assert nm._current_path == ("A", "B")
        assert nm.get_value() == ("A", "B", "C")

    def test_set_value_invalid_path_ignored(self):
        nm = NestedMenu(FLAT)
        original = nm.get_value()
        nm.set_value(("NonExistent",))
        assert nm.get_value() == original

    def test_set_value_none_ignored(self):
        nm = NestedMenu(FLAT)
        original = nm.get_value()
        nm.set_value(None)
        assert nm.get_value() == original

    def test_set_value_empty_tuple_ignored(self):
        nm = NestedMenu(FLAT)
        original = nm.get_value()
        nm.set_value(())
        assert nm.get_value() == original

    def test_set_value_path_through_leaf_ignored(self):
        # "Quit" is a leaf in SIMPLE — can't descend through it
        nm = NestedMenu(SIMPLE)
        nm.set_value(("Quit", "Something"))
        # Should be silently ignored; state unchanged
        assert nm._current_path == ()

    def test_set_value_root_item(self):
        nm = NestedMenu(SIMPLE)
        nm.handle_key('KEY_DOWN')
        nm.set_value(("Quit",))
        assert nm._current_path == ()
        assert nm.get_value() == ("Quit",)


# ---------------------------------------------------------------------------
# 10. Render
# ---------------------------------------------------------------------------

class TestRender:
    def test_render_returns_draw_commands(self):
        nm = NestedMenu(SIMPLE)
        cmds = nm.render(ctx(), focused=False)
        assert isinstance(cmds, list)
        assert any(isinstance(c, WriteCmd) for c in cmds)

    def test_render_shows_all_root_labels(self):
        nm = NestedMenu(SIMPLE)
        cmds = nm.render(ctx(height=10), focused=False)
        texts = ''.join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert 'File' in texts
        assert 'Edit' in texts
        assert 'Quit' in texts

    def test_render_branch_shows_arrow_marker(self):
        nm = NestedMenu(SIMPLE)
        cmds = nm.render(ctx(), focused=False)
        texts = ''.join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert '\u25b6' in texts   # ▶

    def test_render_leaf_no_arrow_marker(self):
        nm = NestedMenu({"Go": "go"})
        cmds = nm.render(ctx(), focused=False)
        texts = ''.join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert '\u25b6' not in texts

    def test_render_focused_active_row_reversed(self):
        nm = NestedMenu(FLAT)
        cmds = nm.render(ctx(), focused=True)
        reversed_cmds = [c for c in cmds if isinstance(c, WriteCmd)
                         and c.style == {'reverse': True}]
        assert len(reversed_cmds) == 1

    def test_render_fill_for_short_list(self):
        nm = NestedMenu(FLAT)
        cmds = nm.render(ctx(height=10), focused=False)
        assert any(isinstance(c, FillCmd) for c in cmds)

    def test_render_shows_breadcrumb_inside_submenu(self):
        nm = NestedMenu(SIMPLE)
        nm.handle_key('KEY_ENTER')   # into File (index 0)
        cmds = nm.render(ctx(), focused=False)
        texts = ''.join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert '\u2190' in texts   # ←
        assert 'File' in texts

    def test_render_no_breadcrumb_at_root(self):
        nm = NestedMenu(SIMPLE)
        cmds = nm.render(ctx(), focused=False)
        texts = ''.join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert '\u2190' not in texts

    def test_render_submenu_shows_children_not_siblings(self):
        nm = NestedMenu(SIMPLE)
        nm.handle_key('KEY_ENTER')   # into File
        cmds = nm.render(ctx(height=10), focused=False)
        texts = ''.join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert 'New' in texts
        assert 'Save' in texts
        assert 'Edit' not in texts
        assert 'Quit' not in texts
