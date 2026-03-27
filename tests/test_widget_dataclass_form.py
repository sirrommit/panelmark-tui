"""Tests for DataclassForm widget and its internal _DataclassFormInteraction."""

import io
import sys
import dataclasses
from dataclasses import dataclass, field
import pytest

from panelmark.draw import RenderContext, WriteCmd
from panelmark_tui.testing import MockTerminal, make_key
from panelmark_tui.widgets.dataclass_form import DataclassForm
from panelmark_tui.interactions.form import (
    DataclassFormInteraction,
    _extract_fields_info,
    _type_str,
    _NONE_SENTINEL,
)


# ---------------------------------------------------------------------------
# Sample dataclasses used across tests
# ---------------------------------------------------------------------------

@dataclass
class Simple:
    name: str = field(default="Alice", metadata={"label": "Full name"})
    age:  int = field(default=30,      metadata={"label": "Age"})


@dataclass
class WithHint:
    score: float = field(
        default=0.0,
        metadata={"label": "Score", "hint": "0.0 – 100.0"},
    )


@dataclass
class NoDefaults:
    title: str
    count: int


@dataclass
class WithNoneDefault:
    value: str = field(default=None, metadata={"label": "Value"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ctx(width=40, height=10) -> RenderContext:
    return RenderContext(width=width, height=height)


def make_interaction(dc=None, actions=None, on_change=None):
    if dc is None:
        dc = Simple()
    return DataclassFormInteraction(dc, actions=actions, on_change=on_change)


class _FakeParent:
    def __init__(self, term):
        self.terminal = term
        self._renderer = None


def run_widget(widget, keys, width=60):
    term = MockTerminal(width=80, height=24)
    term.feed_keys(keys)
    parent = _FakeParent(term)
    buf = io.StringIO()
    old, sys.stdout = sys.stdout, buf
    try:
        return widget.show(parent_shell=parent)
    finally:
        sys.stdout = old


# ---------------------------------------------------------------------------
# _type_str
# ---------------------------------------------------------------------------

class TestTypeStr:
    def test_simple_type(self):
        assert _type_str(int) == "int"
        assert _type_str(str) == "str"

    def test_none_type(self):
        assert _type_str(type(None)) == "None"

    def test_generic_type(self):
        import typing
        result = _type_str(typing.Optional[int])
        # Must be a non-empty string; exact form varies by Python version
        assert isinstance(result, str)
        assert result


# ---------------------------------------------------------------------------
# _extract_fields_info
# ---------------------------------------------------------------------------

class TestExtractFieldsInfo:
    def test_label_from_metadata(self):
        infos = _extract_fields_info(Simple())
        assert infos[0]["label"] == "Full name"
        assert infos[1]["label"] == "Age"

    def test_label_fallback_to_name(self):
        infos = _extract_fields_info(NoDefaults(title="x", count=1))
        assert infos[0]["label"] == "title"
        assert infos[1]["label"] == "count"

    def test_hint_from_metadata(self):
        infos = _extract_fields_info(WithHint())
        assert infos[0]["hint"] == "0.0 – 100.0"

    def test_hint_from_type_annotation(self):
        infos = _extract_fields_info(Simple())
        assert infos[0]["hint"] == "str"
        assert infos[1]["hint"] == "int"

    def test_default_from_metadata(self):
        @dataclass
        class DC:
            x: str = field(default="fallback", metadata={"default": "override"})

        infos = _extract_fields_info(DC())
        assert infos[0]["has_default"] is True
        assert infos[0]["default_raw"] == "override"

    def test_default_from_field(self):
        infos = _extract_fields_info(Simple())
        assert infos[0]["has_default"] is True
        assert infos[0]["default_raw"] == "Alice"
        assert infos[0]["default_str"] == "Alice"

    def test_no_default(self):
        infos = _extract_fields_info(NoDefaults(title="x", count=1))
        assert infos[0]["has_default"] is False

    def test_none_default_display(self):
        infos = _extract_fields_info(WithNoneDefault())
        assert infos[0]["has_default"] is True
        assert infos[0]["default_raw"] is None
        assert infos[0]["default_str"] == "None"


# ---------------------------------------------------------------------------
# _DataclassFormInteraction — initial state
# ---------------------------------------------------------------------------

class TestInteractionInitialState:
    def test_field_with_default_starts_in_default_mode(self):
        inter = make_interaction(Simple())
        # default mode means _field_text[name] is None
        assert inter._field_text["name"] is None
        assert inter._field_text["age"] is None

    def test_field_without_default_starts_empty(self):
        inter = make_interaction(NoDefaults(title="x", count=1))
        assert inter._field_text["title"] == ""
        assert inter._field_text["count"] == ""

    def test_active_index_starts_at_zero(self):
        inter = make_interaction()
        assert inter._active_index == 0


# ---------------------------------------------------------------------------
# _DataclassFormInteraction — typing and backspace
# ---------------------------------------------------------------------------

class TestTypingAndBackspace:
    def test_typing_clears_default(self):
        inter = make_interaction(Simple())
        inter.handle_key("B")
        assert inter._field_text["name"] == "B"

    def test_typing_appends_to_existing_text(self):
        inter = make_interaction(Simple())
        inter.handle_key("H")
        inter.handle_key("i")
        assert inter._field_text["name"] == "Hi"

    def test_backspace_on_one_char_with_default_restores_default(self):
        inter = make_interaction(Simple())
        inter.handle_key("X")
        inter.handle_key("KEY_BACKSPACE")
        assert inter._field_text["name"] is None  # back to default mode

    def test_backspace_on_one_char_without_default_stays_empty(self):
        inter = make_interaction(NoDefaults(title="x", count=1))
        inter.handle_key("Z")
        inter.handle_key("KEY_BACKSPACE")
        assert inter._field_text["title"] == ""

    def test_backspace_removes_last_char(self):
        inter = make_interaction(Simple())
        inter.handle_key("H")
        inter.handle_key("i")
        inter.handle_key("KEY_BACKSPACE")
        assert inter._field_text["name"] == "H"

    def test_backspace_when_already_default_is_noop(self):
        inter = make_interaction(Simple())
        changed, _ = inter.handle_key("KEY_BACKSPACE")
        assert changed is False
        assert inter._field_text["name"] is None  # still in default mode

    def test_space_is_accepted(self):
        inter = make_interaction(NoDefaults(title="x", count=1))
        inter.handle_key(" ")
        assert inter._field_text["title"] == " "


# ---------------------------------------------------------------------------
# _DataclassFormInteraction — get_value
# ---------------------------------------------------------------------------

class TestGetValue:
    def test_default_mode_returns_default_raw(self):
        inter = make_interaction(Simple())
        vals = inter.get_value()
        assert vals["name"] == "Alice"
        assert vals["age"] == 30

    def test_typed_text_returned_as_string(self):
        inter = make_interaction(NoDefaults(title="x", count=1))
        inter.handle_key("H")
        inter.handle_key("i")
        vals = inter.get_value()
        assert vals["title"] == "Hi"

    def test_backslash_none_returns_python_none(self):
        inter = make_interaction(NoDefaults(title="x", count=1))
        for ch in _NONE_SENTINEL:
            inter.handle_key(ch)
        vals = inter.get_value()
        assert vals["title"] is None

    def test_string_none_returns_string(self):
        inter = make_interaction(NoDefaults(title="x", count=1))
        for ch in "None":
            inter.handle_key(ch)
        vals = inter.get_value()
        assert vals["title"] == "None"

    def test_none_default_raw_returns_none(self):
        inter = make_interaction(WithNoneDefault())
        vals = inter.get_value()
        assert vals["value"] is None


# ---------------------------------------------------------------------------
# _DataclassFormInteraction — navigation
# ---------------------------------------------------------------------------

class TestNavigation:
    def test_down_advances_active_index(self):
        inter = make_interaction(Simple())
        inter.handle_key("KEY_DOWN")
        assert inter._active_index == 1

    def test_up_retreats_active_index(self):
        inter = make_interaction(Simple())
        inter.handle_key("KEY_DOWN")
        inter.handle_key("KEY_UP")
        assert inter._active_index == 0

    def test_down_does_not_go_below_last(self):
        inter = make_interaction(Simple())  # 2 fields, no buttons → max index 1
        inter.handle_key("KEY_DOWN")
        inter.handle_key("KEY_DOWN")
        assert inter._active_index == 1

    def test_enter_on_field_moves_to_next(self):
        inter = make_interaction(Simple())
        inter.handle_key("KEY_ENTER")
        assert inter._active_index == 1

    def test_enter_on_last_field_with_button_moves_to_button(self):
        actions = [{"show_button": True, "label": "OK", "action": lambda s, v: None}]
        inter = make_interaction(Simple(), actions=actions)
        # advance to last field (index 1)
        inter.handle_key("KEY_DOWN")
        # Enter moves from last field to first button
        inter.handle_key("KEY_ENTER")
        assert inter._active_index == 2  # n_fields=2, first button at 2

    def test_j_k_navigation(self):
        inter = make_interaction(Simple())
        inter.handle_key("j")
        assert inter._active_index == 1
        inter.handle_key("k")
        assert inter._active_index == 0


# ---------------------------------------------------------------------------
# _DataclassFormInteraction — on_change callback
# ---------------------------------------------------------------------------

class TestOnChange:
    def test_on_change_fires_when_field_changes(self):
        events = []
        inter = make_interaction(Simple(), on_change=lambda name, v: events.append(name))
        inter.handle_key("KEY_DOWN")
        assert events == ["name"]

    def test_on_change_not_fired_when_clamped(self):
        events = []
        inter = make_interaction(Simple(), on_change=lambda name, v: events.append(name))
        inter.handle_key("KEY_UP")  # already at 0, can't go further up
        assert events == []

    def test_on_change_called_with_field_name_and_values(self):
        records = []
        inter = make_interaction(
            Simple(),
            on_change=lambda name, vals: records.append((name, vals)),
        )
        inter.handle_key("B")
        inter.handle_key("KEY_DOWN")
        assert records[0][0] == "name"
        assert records[0][1]["name"] == "B"


# ---------------------------------------------------------------------------
# _DataclassFormInteraction — actions
# ---------------------------------------------------------------------------

class TestActions:
    def test_shortcut_triggers_action(self):
        called = []
        actions = [
            {"shortcut": "KEY_F5", "show_button": False,
             "label": "Go", "action": lambda s, v: called.append(v) or None},
        ]
        inter = make_interaction(Simple(), actions=actions)
        inter.handle_key("KEY_F5")
        assert len(called) == 1

    def test_action_returning_none_does_not_exit(self):
        actions = [
            {"shortcut": "KEY_F5", "show_button": False,
             "label": "Go", "action": lambda s, v: None},
        ]
        inter = make_interaction(Simple(), actions=actions)
        inter.handle_key("KEY_F5")
        assert inter._wants_exit is False

    def test_action_returning_value_triggers_exit(self):
        actions = [
            {"shortcut": "KEY_F6", "show_button": False,
             "label": "Save", "action": lambda s, v: "saved"},
        ]
        inter = make_interaction(Simple(), actions=actions)
        inter.handle_key("KEY_F6")
        assert inter._wants_exit is True
        assert inter._exit_value == "saved"

    def test_signal_return_false_by_default(self):
        inter = make_interaction(Simple())
        ok, val = inter.signal_return()
        assert ok is False
        assert val is None

    def test_button_action_activated_by_enter(self):
        results = []
        actions = [
            {"shortcut": None, "show_button": True,
             "label": "Submit", "action": lambda s, v: results.append(v) or "done"},
        ]
        inter = make_interaction(Simple(), actions=actions)
        # Navigate to the button (past n_fields=2 fields)
        inter.handle_key("KEY_DOWN")
        inter.handle_key("KEY_DOWN")
        inter.handle_key("KEY_ENTER")
        assert len(results) == 1
        assert inter._wants_exit is True

    def test_action_receives_current_values(self):
        received = []
        actions = [
            {"shortcut": "KEY_F1", "show_button": False,
             "label": "Check", "action": lambda s, v: received.append(v) or None},
        ]
        inter = make_interaction(Simple(), actions=actions)
        inter.handle_key("B")   # type 'B' into first field
        inter.handle_key("KEY_F1")
        assert received[0]["name"] == "B"


# ---------------------------------------------------------------------------
# _DataclassFormInteraction — rendering
# ---------------------------------------------------------------------------

class TestRendering:
    def test_default_shown_in_brackets(self):
        inter = make_interaction(Simple())
        cmds = inter.render(ctx(), focused=False)
        texts = [c.text for c in cmds if isinstance(c, WriteCmd)]
        assert any("[Alice]" in t for t in texts)

    def test_user_text_shown_directly(self):
        inter = make_interaction(Simple())
        for ch in "Bob":
            inter.handle_key(ch)
        cmds = inter.render(ctx(), focused=False)
        texts = [c.text for c in cmds if isinstance(c, WriteCmd)]
        assert any("Bob" in t for t in texts)
        assert not any("[Alice]" in t for t in texts)

    def test_active_field_has_reverse_style(self):
        inter = make_interaction(Simple())
        cmds = inter.render(ctx(), focused=True)
        first_cmd = cmds[0]
        assert isinstance(first_cmd, WriteCmd)
        assert first_cmd.style is not None
        assert first_cmd.style.get("reverse") is True

    def test_hint_row_has_dim_style(self):
        inter = make_interaction(WithHint())
        cmds = inter.render(ctx(), focused=False)
        dim_cmds = [c for c in cmds if isinstance(c, WriteCmd) and c.style == {"dim": True}]
        assert len(dim_cmds) >= 1

    def test_hint_text_appears_in_dim_row(self):
        inter = make_interaction(WithHint())
        cmds = inter.render(ctx(), focused=False)
        dim_texts = [c.text for c in cmds if isinstance(c, WriteCmd) and c.style == {"dim": True}]
        assert any("0.0" in t for t in dim_texts)

    def test_no_hint_row_when_no_hint(self):
        """A field with an explicit hint='' should not render a hint row."""
        @dataclass
        class NoHintDC:
            x: str = field(default="hi", metadata={"hint": ""})

        inter = make_interaction(NoHintDC())
        cmds = inter.render(ctx(), focused=False)
        dim_cmds = [c for c in cmds if isinstance(c, WriteCmd) and c.style == {"dim": True}]
        assert len(dim_cmds) == 0

    def test_button_row_rendered(self):
        actions = [{"show_button": True, "label": "OK", "action": lambda s, v: None}]
        inter = make_interaction(Simple(), actions=actions)
        cmds = inter.render(ctx(), focused=False)
        texts = [c.text for c in cmds if isinstance(c, WriteCmd)]
        assert any("OK" in t for t in texts)

    def test_active_button_shown_with_arrow_markers(self):
        actions = [{"show_button": True, "label": "Save", "action": lambda s, v: None}]
        inter = make_interaction(Simple(), actions=actions)
        # Navigate to button (index 2 for 2-field form)
        inter.handle_key("KEY_DOWN")
        inter.handle_key("KEY_DOWN")
        cmds = inter.render(ctx(), focused=True)
        texts = [c.text for c in cmds if isinstance(c, WriteCmd)]
        assert any("◀ Save ▶" in t for t in texts)


# ---------------------------------------------------------------------------
# DataclassForm widget — construction
# ---------------------------------------------------------------------------

class TestDataclassFormConstruction:
    def test_requires_dataclass_instance(self):
        with pytest.raises(TypeError):
            DataclassForm("not a dataclass")

    def test_requires_instance_not_class(self):
        with pytest.raises(TypeError):
            DataclassForm(Simple)  # passing the class, not an instance

    def test_default_width(self):
        form = DataclassForm(Simple())
        assert form.width == 60

    def test_custom_width(self):
        form = DataclassForm(Simple(), width=80)
        assert form.width == 80


# ---------------------------------------------------------------------------
# DataclassForm widget — full integration via MockTerminal
# ---------------------------------------------------------------------------

class TestDataclassFormIntegration:
    def _make_save_cancel(self):
        def save(shell, values):
            return values   # non-None → close

        def cancel(shell, values):
            return False    # non-None → close (caller checks for False)

        return [
            {"shortcut": None, "show_button": True, "label": "Save",   "action": save},
            {"shortcut": None, "show_button": True, "label": "Cancel", "action": cancel},
        ]

    def test_escape_returns_none(self):
        result = run_widget(
            DataclassForm(Simple(), actions=self._make_save_cancel()),
            [make_key("\x11")],  # Ctrl+Q
        )
        assert result is None

    def test_save_button_returns_values(self):
        actions = self._make_save_cancel()
        # Navigate: Down × 2 to reach Save button, then Enter
        keys = [
            make_key("KEY_DOWN"),
            make_key("KEY_DOWN"),
            make_key("KEY_ENTER"),
        ]
        result = run_widget(DataclassForm(Simple(), actions=actions), keys)
        assert isinstance(result, dict)
        assert result["name"] == "Alice"
        assert result["age"] == 30

    def test_typed_value_returned(self):
        actions = self._make_save_cancel()
        # Type "Bob" in first field, then navigate to Save and press Enter
        keys = (
            [make_key(c) for c in "Bob"]
            + [make_key("KEY_DOWN"), make_key("KEY_DOWN"), make_key("KEY_ENTER")]
        )
        result = run_widget(DataclassForm(Simple(), actions=actions), keys)
        assert result["name"] == "Bob"

    def test_cancel_button_returns_false(self):
        actions = self._make_save_cancel()
        # Navigate to Cancel button (index 3 = 2 fields + button 1 "Save" + button 2 "Cancel")
        keys = [
            make_key("KEY_DOWN"),
            make_key("KEY_DOWN"),
            make_key("KEY_DOWN"),
            make_key("KEY_ENTER"),
        ]
        result = run_widget(DataclassForm(Simple(), actions=actions), keys)
        assert result is False

    def test_form_with_no_actions_stays_open_until_ctrl_q(self):
        keys = [make_key("KEY_DOWN"), make_key("\x11")]  # navigate + Ctrl+Q
        result = run_widget(DataclassForm(Simple()), keys)
        assert result is None
