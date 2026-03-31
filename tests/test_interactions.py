import pytest
from panelmark_tui.testing import MockTerminal, make_key
from panelmark_tui.interactions import (
    MenuFunction, MenuReturn,
    TextBox, ListView, CheckBox, Function, FormInput,
    RadioList, TreeView, TableView,
    StatusMessage, DataclassFormInteraction,
)
from panelmark.draw import RenderContext, WriteCmd, FillCmd, CursorCmd


def ctx(width=40, height=10):
    return RenderContext(width=width, height=height,
                        capabilities=frozenset({'color', 'cursor'}))


class TestMenuReturn:
    def test_initial_value(self):
        m = MenuReturn({'Option A': 'a', 'Option B': 'b'})
        assert m.get_value() == 'Option A'

    def test_navigate_down(self):
        m = MenuReturn({'A': 1, 'B': 2, 'C': 3})
        changed, val = m.handle_key('KEY_DOWN')
        assert changed is True
        assert val == 'B'

    def test_navigate_up(self):
        m = MenuReturn({'A': 1, 'B': 2, 'C': 3})
        m.handle_key('KEY_DOWN')
        changed, val = m.handle_key('KEY_UP')
        assert changed is True
        assert val == 'A'

    def test_navigate_clamp_at_top(self):
        m = MenuReturn({'A': 1, 'B': 2})
        m.handle_key('KEY_UP')
        assert m.get_value() == 'A'

    def test_navigate_clamp_at_bottom(self):
        m = MenuReturn({'A': 1, 'B': 2})
        m.handle_key('KEY_DOWN')
        m.handle_key('KEY_DOWN')
        assert m.get_value() == 'B'

    def test_enter_signals_exit(self):
        m = MenuReturn({'A': 1, 'B': 2})
        m.handle_key('KEY_ENTER')
        should_exit, rv = m.signal_return()
        assert should_exit is True
        assert rv == 1

    def test_enter_second_item(self):
        m = MenuReturn({'A': 1, 'B': 2})
        m.handle_key('KEY_DOWN')
        m.handle_key('KEY_ENTER')
        should_exit, rv = m.signal_return()
        assert should_exit is True
        assert rv == 2

    def test_signal_return_initially_false(self):
        m = MenuReturn({'A': 1})
        should_exit, rv = m.signal_return()
        assert should_exit is False

    def test_set_value(self):
        m = MenuReturn({'A': 1, 'B': 2, 'C': 3})
        m.set_value('C')
        assert m.get_value() == 'C'

    def test_round_trip_get_set_value(self):
        m = MenuReturn({'A': 1, 'B': 2, 'C': 3})
        m.handle_key('KEY_DOWN')
        label = m.get_value()
        m.set_value(label)
        assert m.get_value() == label

    def test_signal_return_returns_mapped_payload_not_label(self):
        m = MenuReturn({'Alpha': 'payload_a', 'Beta': 'payload_b'})
        m.handle_key('KEY_DOWN')
        m.handle_key('KEY_ENTER')
        fired, val = m.signal_return()
        assert fired is True
        assert val == 'payload_b'
        assert val != 'Beta'

    def test_render_returns_commands(self):
        m = MenuReturn({'Option A': 'a', 'Option B': 'b'})
        cmds = m.render(ctx(), focused=True)
        assert isinstance(cmds, list)
        assert any(isinstance(c, WriteCmd) for c in cmds)

    def test_render_active_row_reversed_when_focused(self):
        m = MenuReturn({'A': 1, 'B': 2})
        cmds = m.render(ctx(), focused=True)
        active = next(c for c in cmds if isinstance(c, WriteCmd) and c.row == 0)
        assert active.style == {'reverse': True}

    def test_render_active_row_marker_when_unfocused(self):
        m = MenuReturn({'A': 1, 'B': 2})
        cmds = m.render(ctx(), focused=False)
        active = next(c for c in cmds if isinstance(c, WriteCmd) and c.row == 0)
        assert '>' in active.text
        assert active.style is None


class TestMenuFunction:
    def test_initial_value_is_first_label(self):
        m = MenuFunction({'Action': lambda s: None})
        assert m.get_value() == 'Action'

    def test_initial_value_empty_menu(self):
        m = MenuFunction({})
        assert m.get_value() is None

    def test_get_value_reflects_highlight(self):
        m = MenuFunction({'A': lambda s: None, 'B': lambda s: None})
        assert m.get_value() == 'A'
        m.handle_key('KEY_DOWN')
        assert m.get_value() == 'B'

    def test_navigate_down(self):
        m = MenuFunction({'A': lambda s: None, 'B': lambda s: None})
        m.handle_key('KEY_DOWN')

    def test_enter_calls_function(self):
        called = []
        m = MenuFunction({'Do it': lambda s: called.append(s)})
        m._shell = 'mock_shell'
        m.handle_key('KEY_ENTER')
        assert called == ['mock_shell']

    def test_enter_sets_last_activated(self):
        m = MenuFunction({'Action': lambda s: None})
        m.handle_key('KEY_ENTER')
        assert m.last_activated == 'Action'

    def test_get_value_stable_after_activation(self):
        """Activating an item should not change the highlight."""
        m = MenuFunction({'A': lambda s: None, 'B': lambda s: None})
        m.handle_key('KEY_DOWN')   # highlight B
        m.handle_key('KEY_ENTER')  # activate B
        assert m.get_value() == 'B'

    def test_last_activated_none_before_any_activation(self):
        m = MenuFunction({'A': lambda s: None})
        assert m.last_activated is None

    def test_last_activated_tracks_most_recent(self):
        m = MenuFunction({'A': lambda s: None, 'B': lambda s: None})
        m.handle_key('KEY_ENTER')   # activate A
        assert m.last_activated == 'A'
        m.handle_key('KEY_DOWN')
        m.handle_key('KEY_ENTER')   # activate B
        assert m.last_activated == 'B'

    def test_set_value_moves_highlight(self):
        m = MenuFunction({'A': lambda s: None, 'B': lambda s: None, 'C': lambda s: None})
        m.set_value('C')
        assert m.get_value() == 'C'

    def test_set_value_does_not_touch_last_activated(self):
        m = MenuFunction({'A': lambda s: None, 'B': lambda s: None})
        m.set_value('B')
        assert m.last_activated is None

    def test_round_trip_get_set_value(self):
        m = MenuFunction({'A': lambda s: None, 'B': lambda s: None, 'C': lambda s: None})
        m.handle_key('KEY_DOWN')
        val = m.get_value()
        m.handle_key('KEY_DOWN')   # move away
        m.set_value(val)           # restore
        assert m.get_value() == val

    def test_render_returns_commands(self):
        m = MenuFunction({'Option': lambda s: None})
        cmds = m.render(ctx(), focused=True)
        assert isinstance(cmds, list)
        assert any(isinstance(c, WriteCmd) for c in cmds)

    def test_signal_return_false_by_default(self):
        m = MenuFunction({'Action': lambda s: None})
        should_exit, _ = m.signal_return()
        assert should_exit is False

    def test_signal_return_true_after_callback_sets_wants_exit(self):
        sentinel = object()
        def _cb(sh):
            m._wants_exit = True
            m._exit_value = sentinel
        m = MenuFunction({'Go': _cb})
        m.handle_key('KEY_ENTER')
        should_exit, rv = m.signal_return()
        assert should_exit is True
        assert rv is sentinel

    def test_wants_exit_cleared_on_next_key(self):
        def _cb(sh):
            m._wants_exit = True
        m = MenuFunction({'Go': _cb})
        m.handle_key('KEY_ENTER')
        m.handle_key('KEY_DOWN')   # next navigation key clears it
        should_exit, _ = m.signal_return()
        assert should_exit is False


class TestTextBox:
    def test_initial_value(self):
        t = TextBox(initial='hello')
        assert t.get_value() == 'hello'

    def test_type_chars(self):
        t = TextBox()
        t.handle_key('h')
        t.handle_key('i')
        assert t.get_value() == 'hi'

    def test_backspace(self):
        t = TextBox(initial='hello')
        t.handle_key('KEY_BACKSPACE')
        assert t.get_value() == 'hell'

    def test_set_value(self):
        t = TextBox()
        t.set_value('new text')
        assert t.get_value() == 'new text'

    def test_readonly_ignores_keys(self):
        t = TextBox(initial='fixed', readonly=True)
        t.handle_key('x')
        assert t.get_value() == 'fixed'

    def test_value_changed_flag(self):
        t = TextBox()
        changed, val = t.handle_key('a')
        assert changed is True
        assert val == 'a'

    def test_non_printable_not_added(self):
        t = TextBox()
        t.handle_key('KEY_UP')
        assert t.get_value() == ''

    def test_render_returns_commands(self):
        t = TextBox(initial='some text')
        cmds = t.render(ctx(), focused=True)
        assert isinstance(cmds, list)
        assert any(isinstance(c, WriteCmd) for c in cmds)

    def test_render_focused_has_cursor_cmd(self):
        t = TextBox(initial='hi')
        cmds = t.render(ctx(), focused=True)
        assert any(isinstance(c, CursorCmd) for c in cmds)

    def test_render_unfocused_no_cursor_cmd(self):
        t = TextBox(initial='hi')
        cmds = t.render(ctx(), focused=False)
        assert not any(isinstance(c, CursorCmd) for c in cmds)

    def test_render_text_appears_in_commands(self):
        t = TextBox(initial='hello')
        cmds = t.render(ctx(width=20, height=3), focused=False)
        text = ''.join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert 'hello' in text

    # --- enter_mode tests ---

    def test_newline_mode_enter_inserts_newline(self):
        t = TextBox(enter_mode='newline')
        changed, val = t.handle_key('KEY_ENTER')
        assert changed is True
        assert '\n' in val

    def test_newline_mode_signal_return_never_fires(self):
        t = TextBox(enter_mode='newline')
        t.handle_key('KEY_ENTER')
        fired, _ = t.signal_return()
        assert fired is False

    def test_submit_mode_enter_does_not_insert_newline(self):
        t = TextBox(initial='hello', enter_mode='submit')
        t.handle_key('KEY_ENTER')
        assert '\n' not in t.get_value()

    def test_submit_mode_signal_return_fires_after_enter(self):
        t = TextBox(initial='hello', enter_mode='submit')
        t.handle_key('KEY_ENTER')
        fired, val = t.signal_return()
        assert fired is True
        assert val == 'hello'

    def test_submit_mode_signal_return_resets_after_fire(self):
        t = TextBox(initial='hello', enter_mode='submit')
        t.handle_key('KEY_ENTER')
        t.signal_return()
        fired, _ = t.signal_return()
        assert fired is False

    def test_submit_mode_no_signal_before_enter(self):
        t = TextBox(initial='hello', enter_mode='submit')
        fired, _ = t.signal_return()
        assert fired is False

    def test_ignore_mode_enter_does_nothing(self):
        t = TextBox(initial='hello', enter_mode='ignore')
        changed, val = t.handle_key('KEY_ENTER')
        assert changed is False
        assert val == 'hello'

    def test_ignore_mode_signal_return_never_fires(self):
        t = TextBox(enter_mode='ignore')
        t.handle_key('KEY_ENTER')
        fired, _ = t.signal_return()
        assert fired is False

    def test_submit_mode_literal_newline_key(self):
        t = TextBox(initial='abc', enter_mode='submit')
        t.handle_key('\n')
        fired, val = t.signal_return()
        assert fired is True
        assert val == 'abc'

    def test_newline_mode_literal_newline_key_inserts(self):
        t = TextBox(enter_mode='newline')
        t.handle_key('\n')
        assert '\n' in t.get_value()

    def test_ignore_mode_literal_newline_key_does_nothing(self):
        t = TextBox(initial='x', enter_mode='ignore')
        t.handle_key('\n')
        assert t.get_value() == 'x'

    def test_set_value_resets_submitted_flag(self):
        t = TextBox(initial='hello', enter_mode='submit')
        t.handle_key('KEY_ENTER')
        t.set_value('new text')
        fired, _ = t.signal_return()
        assert fired is False

    def test_round_trip_get_set_value(self):
        t = TextBox(initial='foo', enter_mode='submit')
        t.set_value('bar')
        assert t.get_value() == 'bar'

    def test_default_enter_mode_is_newline(self):
        t = TextBox()
        t.handle_key('KEY_ENTER')
        assert '\n' in t.get_value()


class TestListView:
    def test_initial_value(self):
        lv = ListView(['apple', 'banana', 'cherry'])
        assert lv.get_value() == ['apple', 'banana', 'cherry']

    def test_handle_key_returns_no_change(self):
        lv = ListView(['a', 'b'])
        changed, val = lv.handle_key('KEY_DOWN')
        assert changed is False

    def test_set_value(self):
        lv = ListView(['a'])
        lv.set_value(['x', 'y', 'z'])
        assert lv.get_value() == ['x', 'y', 'z']

    def test_render_returns_commands(self):
        lv = ListView(['item 1', 'item 2'])
        cmds = lv.render(ctx())
        assert isinstance(cmds, list)
        assert any(isinstance(c, WriteCmd) for c in cmds)

    def test_render_items_appear_in_commands(self):
        lv = ListView(['alpha', 'beta'])
        cmds = lv.render(ctx(width=20, height=5))
        text = ''.join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert 'alpha' in text
        assert 'beta' in text

    def test_render_trailing_fill_when_short(self):
        lv = ListView(['only one'])
        cmds = lv.render(ctx(width=20, height=5))
        assert any(isinstance(c, FillCmd) for c in cmds)

    def test_bullet_numeric(self):
        lv = ListView(['a', 'b', 'c'], bullet='1')
        assert lv._bullet == '1'

    def test_bullet_alpha_upper(self):
        lv = ListView(['a', 'b'], bullet='A')
        assert lv._bullet == 'A'

    def test_round_trip_get_set_value(self):
        lv = ListView(['x', 'y', 'z'])
        items = lv.get_value()
        lv.set_value(items)
        assert lv.get_value() == items

    def test_signal_return_never_fires(self):
        lv = ListView(['a', 'b'])
        lv.handle_key('KEY_DOWN')
        fired, _ = lv.signal_return()
        assert fired is False


class TestStatusMessage:
    def test_initial_value_is_none(self):
        s = StatusMessage()
        assert s.get_value() is None

    def test_set_value_tuple(self):
        s = StatusMessage()
        s.set_value(('error', 'File not found'))
        assert s.get_value() == ('error', 'File not found')

    def test_set_value_success(self):
        s = StatusMessage()
        s.set_value(('success', 'Saved'))
        assert s.get_value() == ('success', 'Saved')

    def test_set_value_none_clears(self):
        s = StatusMessage()
        s.set_value(('info', 'hello'))
        s.set_value(None)
        assert s.get_value() is None

    def test_set_value_empty_string_clears(self):
        s = StatusMessage()
        s.set_value(('info', 'hello'))
        s.set_value('')
        assert s.get_value() is None

    def test_set_value_plain_string(self):
        s = StatusMessage()
        s.set_value('plain message')
        val = s.get_value()
        assert val is not None
        assert 'plain message' in val[1]

    def test_round_trip_get_set_value(self):
        s = StatusMessage()
        s.set_value(('info', 'status text'))
        val = s.get_value()
        s.set_value(val)
        assert s.get_value() == val

    def test_signal_return_never_fires(self):
        s = StatusMessage()
        s.set_value(('error', 'oops'))
        fired, _ = s.signal_return()
        assert fired is False

    def test_render_returns_commands(self):
        s = StatusMessage()
        s.set_value(('info', 'hello'))
        cmds = s.render(ctx())
        assert isinstance(cmds, list)
        assert any(isinstance(c, WriteCmd) for c in cmds)

    def test_render_blank_when_no_message(self):
        s = StatusMessage()
        cmds = s.render(ctx())
        assert not any(isinstance(c, WriteCmd) for c in cmds)


class TestCheckBox:
    def test_initial_value(self):
        cb = CheckBox({'a': True, 'b': False, 'c': True})
        assert cb.get_value() == {'a': True, 'b': False, 'c': True}

    def test_toggle_with_space(self):
        cb = CheckBox({'a': False, 'b': False})
        changed, val = cb.handle_key(' ')
        assert changed is True
        assert val['a'] is True

    def test_navigate_down_then_toggle(self):
        cb = CheckBox({'a': False, 'b': False})
        cb.handle_key('KEY_DOWN')
        cb.handle_key(' ')
        val = cb.get_value()
        assert val['b'] is True
        assert val['a'] is False

    def test_single_mode_deselects_others(self):
        cb = CheckBox({'a': True, 'b': False}, mode='single')
        cb.handle_key('KEY_DOWN')
        cb.handle_key(' ')
        val = cb.get_value()
        assert val['b'] is True
        assert val['a'] is False

    def test_multi_mode_allows_multiple(self):
        cb = CheckBox({'a': True, 'b': False}, mode='multi')
        cb.handle_key('KEY_DOWN')
        cb.handle_key(' ')
        val = cb.get_value()
        assert val['a'] is True
        assert val['b'] is True

    def test_set_value(self):
        cb = CheckBox({'a': False})
        cb.set_value({'a': True})
        assert cb.get_value() == {'a': True}

    def test_round_trip_get_set_value(self):
        cb = CheckBox({'x': True, 'y': False, 'z': True})
        state = cb.get_value()
        cb.set_value(state)
        assert cb.get_value() == state

    def test_signal_return_never_fires(self):
        cb = CheckBox({'a': False, 'b': False})
        cb.handle_key(' ')
        fired, _ = cb.signal_return()
        assert fired is False

    def test_render_returns_commands(self):
        cb = CheckBox({'opt1': True, 'opt2': False})
        cmds = cb.render(ctx(), focused=True)
        assert isinstance(cmds, list)
        assert any(isinstance(c, WriteCmd) for c in cmds)

    def test_render_checked_items_appear(self):
        cb = CheckBox({'yes': True, 'no': False})
        cmds = cb.render(ctx(width=30, height=5), focused=False)
        text = ''.join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert '[X]' in text
        assert '[ ]' in text


class TestFunction:
    def test_render_calls_handler(self):
        calls = []
        def handler(shell, context, key):
            calls.append((shell, context, key))
            return []
        f = Function(handler)
        c = ctx()
        f.render(c)
        assert len(calls) == 1
        assert calls[0][1] is c
        assert calls[0][2] is None  # key=None on render

    def test_render_returns_handler_commands(self):
        cmds_out = [WriteCmd(row=0, col=0, text='hi')]
        f = Function(lambda s, c, k: cmds_out)
        result = f.render(ctx())
        assert result == cmds_out

    def test_render_none_handler_returns_empty(self):
        f = Function(lambda s, c, k: None)
        result = f.render(ctx())
        assert result == []

    def test_handle_key_calls_handler(self):
        calls = []
        def handler(shell, context, key):
            calls.append(key)
        f = Function(handler)
        f._context = ctx()
        f.handle_key('x')
        assert 'x' in calls

    def test_initial_value_none(self):
        f = Function(lambda s, c, k: None)
        assert f.get_value() is None

    def test_set_value(self):
        f = Function(lambda s, c, k: None)
        f.set_value(42)
        assert f.get_value() == 42


class TestFormInput:
    def test_construction_valid(self):
        form = FormInput({
            'name': {'type': 'str', 'descriptor': 'Name'},
        })
        assert form is not None

    def test_construction_missing_type_raises(self):
        with pytest.raises(ValueError, match="missing required key 'type'"):
            FormInput({'x': {'descriptor': 'X'}})

    def test_construction_missing_descriptor_raises(self):
        with pytest.raises(ValueError, match="missing required key 'descriptor'"):
            FormInput({'x': {'type': 'str'}})

    def test_construction_choices_missing_options_raises(self):
        with pytest.raises(ValueError, match="requires 'options'"):
            FormInput({'x': {'type': 'choices', 'descriptor': 'X'}})

    def test_construction_choices_empty_options_raises(self):
        with pytest.raises(ValueError, match="non-empty list"):
            FormInput({'x': {'type': 'choices', 'descriptor': 'X', 'options': []}})

    def test_initial_str_value(self):
        form = FormInput({'name': {'type': 'str', 'descriptor': 'Name', 'default': 'Alice'}})
        val = form.get_value()
        assert val['name'] == 'Alice'

    def test_initial_bool_value(self):
        form = FormInput({'flag': {'type': 'bool', 'descriptor': 'Flag', 'default': True}})
        val = form.get_value()
        assert val['flag'] is True

    def test_initial_choices_value(self):
        form = FormInput({
            'role': {'type': 'choices', 'descriptor': 'Role',
                     'options': ['Admin', 'User'], 'default': 'User'}
        })
        val = form.get_value()
        assert val['role'] == 'User'

    def test_type_str_character(self):
        form = FormInput({'name': {'type': 'str', 'descriptor': 'Name'}})
        form.handle_key('a')
        assert form.get_value()['name'] == 'a'

    def test_type_int_allows_digits(self):
        form = FormInput({'age': {'type': 'int', 'descriptor': 'Age'}})
        form.handle_key('2')
        form.handle_key('5')
        assert form.get_value()['age'] == 25

    def test_type_int_rejects_letters(self):
        form = FormInput({'age': {'type': 'int', 'descriptor': 'Age'}})
        form.handle_key('a')
        assert form.get_value()['age'] is None

    def test_get_value_int_empty_returns_none(self):
        form = FormInput({'age': {'type': 'int', 'descriptor': 'Age'}})
        assert form.get_value()['age'] is None

    def test_get_value_float_valid_returns_float(self):
        form = FormInput({'ratio': {'type': 'float', 'descriptor': 'Ratio'}})
        form.handle_key('3')
        form.handle_key('.')
        form.handle_key('1')
        form.handle_key('4')
        assert form.get_value()['ratio'] == 3.14

    def test_get_value_float_empty_returns_none(self):
        form = FormInput({'ratio': {'type': 'float', 'descriptor': 'Ratio'}})
        assert form.get_value()['ratio'] is None

    def test_get_value_float_incomplete_returns_none(self):
        # "12." is a valid Python float string but _coerce would succeed; "-" alone is invalid
        form = FormInput({'ratio': {'type': 'float', 'descriptor': 'Ratio'}})
        form.handle_key('-')
        assert form.get_value()['ratio'] is None

    def test_get_value_int_returns_int_type(self):
        form = FormInput({'n': {'type': 'int', 'descriptor': 'N', 'default': '7'}})
        # default is stored as string '7', get_value must coerce to int
        assert form.get_value()['n'] == 7
        assert isinstance(form.get_value()['n'], int)

    def test_round_trip_set_get_int(self):
        form = FormInput({'age': {'type': 'int', 'descriptor': 'Age'}})
        form.set_value({'age': 42})
        assert form.get_value()['age'] == 42

    def test_bool_toggle_with_space(self):
        form = FormInput({'flag': {'type': 'bool', 'descriptor': 'Flag', 'default': False}})
        form.handle_key(' ')
        assert form.get_value()['flag'] is True

    def test_bool_default_ambiguous_string_raises(self):
        for bad in ('1', '0', 'yes', 'no', 'on', 'off', ''):
            with pytest.raises(ValueError):
                FormInput({'f': {'type': 'bool', 'descriptor': 'F', 'default': bad}})

    def test_bool_default_false_capital_accepted(self):
        form = FormInput({'f': {'type': 'bool', 'descriptor': 'F', 'default': 'False'}})
        assert form.get_value()['f'] is False

    def test_bool_default_true_string_accepted(self):
        form = FormInput({'f': {'type': 'bool', 'descriptor': 'F', 'default': 'true'}})
        assert form.get_value()['f'] is True

    def test_bool_default_false_lower_string_accepted(self):
        form = FormInput({'f': {'type': 'bool', 'descriptor': 'F', 'default': 'false'}})
        assert form.get_value()['f'] is False

    def test_bool_default_true_mixed_case_accepted(self):
        form = FormInput({'f': {'type': 'bool', 'descriptor': 'F', 'default': 'True'}})
        assert form.get_value()['f'] is True

    def test_bool_default_python_true_accepted(self):
        form = FormInput({'f': {'type': 'bool', 'descriptor': 'F', 'default': True}})
        assert form.get_value()['f'] is True

    def test_bool_default_python_false_accepted(self):
        form = FormInput({'f': {'type': 'bool', 'descriptor': 'F', 'default': False}})
        assert form.get_value()['f'] is False

    def test_choices_cycle_with_space(self):
        form = FormInput({
            'role': {'type': 'choices', 'descriptor': 'Role', 'options': ['A', 'B', 'C']}
        })
        form.handle_key(' ')
        assert form.get_value()['role'] == 'B'

    def test_navigate_down(self):
        form = FormInput({
            'a': {'type': 'str', 'descriptor': 'A'},
            'b': {'type': 'str', 'descriptor': 'B'},
        })
        form.handle_key('KEY_DOWN')
        assert form._active_index == 1

    def test_signal_return_initially_false(self):
        form = FormInput({'name': {'type': 'str', 'descriptor': 'Name'}})
        fired, _ = form.signal_return()
        assert fired is False

    def test_submit_valid_form(self):
        form = FormInput({'name': {'type': 'str', 'descriptor': 'Name'}})
        form.handle_key('h')
        form.handle_key('i')
        form.handle_key('KEY_DOWN')
        form.handle_key('KEY_ENTER')
        should_exit, rv = form.signal_return()
        assert should_exit is True
        assert rv['name'] == 'hi'

    def test_round_trip_get_set_value(self):
        form = FormInput({
            'name': {'type': 'str', 'descriptor': 'Name', 'default': 'Alice'},
            'flag': {'type': 'bool', 'descriptor': 'Flag', 'default': True},
        })
        state = form.get_value()
        form.set_value(state)
        assert form.get_value() == state

    def test_submit_required_field_empty(self):
        form = FormInput({'name': {'type': 'str', 'descriptor': 'Name', 'required': True}})
        form.handle_key('KEY_DOWN')
        form.handle_key('KEY_ENTER')
        should_exit, _ = form.signal_return()
        assert should_exit is False
        assert form._field_errors.get('name') is not None

    def test_render_returns_commands(self):
        form = FormInput({
            'name': {'type': 'str', 'descriptor': 'Name'},
            'active': {'type': 'bool', 'descriptor': 'Active'},
        })
        cmds = form.render(ctx(), focused=True)
        assert isinstance(cmds, list)
        assert any(isinstance(c, WriteCmd) for c in cmds)

    def test_render_active_row_reversed(self):
        form = FormInput({'name': {'type': 'str', 'descriptor': 'Name'}})
        cmds = form.render(ctx(), focused=True)
        reversed_cmds = [c for c in cmds if isinstance(c, WriteCmd) and c.style == {'reverse': True}]
        assert len(reversed_cmds) >= 1

    def test_set_value(self):
        form = FormInput({'name': {'type': 'str', 'descriptor': 'Name'}})
        form.set_value({'name': 'Bob'})
        assert form.get_value()['name'] == 'Bob'


class TestRadioList:
    def _items(self):
        return {'Small': 's', 'Medium': 'm', 'Large': 'l'}

    def test_initial_value_is_first_item_value(self):
        r = RadioList(self._items())
        assert r.get_value() == 's'

    def test_navigate_down_changes_value(self):
        r = RadioList(self._items())
        changed, val = r.handle_key('KEY_DOWN')
        assert changed is True
        assert val == 'm'

    def test_navigate_up_clamps_at_top(self):
        r = RadioList(self._items())
        r.handle_key('KEY_UP')
        assert r.get_value() == 's'

    def test_enter_fires_signal_return(self):
        r = RadioList(self._items())
        r.handle_key('KEY_DOWN')
        r.handle_key('KEY_ENTER')
        fired, val = r.signal_return()
        assert fired is True
        assert val == 'm'

    def test_space_fires_signal_return(self):
        r = RadioList(self._items())
        r.handle_key(' ')
        fired, val = r.signal_return()
        assert fired is True
        assert val == 's'

    def test_signal_return_initially_false(self):
        r = RadioList(self._items())
        fired, _ = r.signal_return()
        assert fired is False

    def test_signal_return_returns_value_not_label(self):
        r = RadioList({'Alpha': 'payload_a', 'Beta': 'payload_b'})
        r.handle_key('KEY_DOWN')
        r.handle_key('KEY_ENTER')
        fired, val = r.signal_return()
        assert fired is True
        assert val == 'payload_b'
        assert val != 'Beta'

    def test_set_value_moves_cursor(self):
        r = RadioList(self._items())
        r.set_value('l')
        assert r.get_value() == 'l'

    def test_round_trip_get_set_value(self):
        r = RadioList(self._items())
        r.handle_key('KEY_DOWN')
        val = r.get_value()
        r.set_value(val)
        assert r.get_value() == val

    def test_render_returns_commands(self):
        r = RadioList(self._items())
        cmds = r.render(ctx(), focused=True)
        assert isinstance(cmds, list)
        assert any(isinstance(c, WriteCmd) for c in cmds)

    def test_render_shows_radio_markers(self):
        r = RadioList(self._items())
        cmds = r.render(ctx(width=30, height=5), focused=False)
        text = ''.join(c.text for c in cmds if isinstance(c, WriteCmd))
        assert '(●)' in text
        assert '( )' in text


class TestTreeView:
    def _tree(self):
        return {
            'docs': {'readme.txt': None, 'guide.txt': None},
            'src': {'main.py': None},
            'LICENSE': None,
        }

    def test_initial_value_is_first_visible_item(self):
        tv = TreeView(self._tree())
        # Top-level items are all branches/leaves; first is 'docs' branch
        val = tv.get_value()
        assert val == ('docs',)

    def test_navigate_down_changes_value(self):
        tv = TreeView(self._tree())
        changed, val = tv.handle_key('KEY_DOWN')
        assert changed is True
        assert val == ('src',)

    def test_branch_toggle_no_signal_return(self):
        tv = TreeView(self._tree())
        tv.handle_key('KEY_ENTER')   # expand 'docs'
        fired, _ = tv.signal_return()
        assert fired is False

    def test_leaf_select_fires_signal_return(self):
        tv = TreeView(self._tree(), initially_expanded=True)
        # Navigate to first leaf under 'docs'
        tv.handle_key('KEY_DOWN')   # -> docs/readme.txt
        tv.handle_key('KEY_ENTER')
        fired, val = tv.signal_return()
        assert fired is True
        assert val == ('docs', 'readme.txt')

    def test_signal_return_initially_false(self):
        tv = TreeView(self._tree())
        fired, _ = tv.signal_return()
        assert fired is False

    def test_set_value_expands_ancestors(self):
        tv = TreeView(self._tree())
        tv.set_value(('docs', 'guide.txt'))
        assert tv.get_value() == ('docs', 'guide.txt')

    def test_round_trip_get_set_value(self):
        tv = TreeView(self._tree(), initially_expanded=True)
        tv.handle_key('KEY_DOWN')
        val = tv.get_value()
        tv.set_value(val)
        assert tv.get_value() == val

    def test_empty_tree_get_value_is_none(self):
        tv = TreeView({})
        assert tv.get_value() is None

    def test_render_returns_commands(self):
        tv = TreeView(self._tree())
        cmds = tv.render(ctx(), focused=True)
        assert isinstance(cmds, list)
        assert any(isinstance(c, WriteCmd) for c in cmds)


class TestTableView:
    def _table(self):
        return TableView(
            columns=[('Name', 10), ('Score', 6)],
            rows=[['Alice', '95'], ['Bob', '72'], ['Carol', '88']],
        )

    def test_initial_value_is_zero(self):
        t = self._table()
        assert t.get_value() == 0

    def test_navigate_down_changes_value(self):
        t = self._table()
        changed, val = t.handle_key('KEY_DOWN')
        assert changed is True
        assert val == 1

    def test_navigate_up_clamps_at_zero(self):
        t = self._table()
        t.handle_key('KEY_UP')
        assert t.get_value() == 0

    def test_navigate_clamps_at_last_row(self):
        t = self._table()
        for _ in range(10):
            t.handle_key('KEY_DOWN')
        assert t.get_value() == 2

    def test_signal_return_never_fires(self):
        t = self._table()
        t.handle_key('KEY_DOWN')
        fired, _ = t.signal_return()
        assert fired is False

    def test_set_value_moves_cursor(self):
        t = self._table()
        t.set_value(2)
        assert t.get_value() == 2

    def test_set_value_clamps_high(self):
        t = self._table()
        t.set_value(999)
        assert t.get_value() == 2

    def test_set_value_clamps_low(self):
        t = self._table()
        t.handle_key('KEY_DOWN')
        t.set_value(-5)
        assert t.get_value() == 0

    def test_round_trip_get_set_value(self):
        t = self._table()
        t.handle_key('KEY_DOWN')
        idx = t.get_value()
        t.set_value(idx)
        assert t.get_value() == idx

    def test_render_returns_commands(self):
        t = self._table()
        cmds = t.render(ctx(), focused=True)
        assert isinstance(cmds, list)
        assert any(isinstance(c, WriteCmd) for c in cmds)

    def test_render_header_appears(self):
        t = self._table()
        cmds = t.render(ctx(width=30, height=5), focused=False)
        text = ''.join(c.text for c in cmds if isinstance(c, WriteCmd) and c.row == 0)
        assert 'Name' in text
        assert 'Score' in text
