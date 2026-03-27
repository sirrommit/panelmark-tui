"""DataclassForm widget — collect structured data from a dataclass template.

The widget inspects a dataclass instance and renders a form with one row
per field.  Each row shows a label (from ``metadata["label"]`` or the
field name), the current value or a ``[default]`` placeholder, and an
optional dim hint line (from ``metadata["hint"]`` or the type annotation).

Typing clears the ``[default]`` placeholder; deleting back to empty
restores it.  Typing ``\\None`` (a literal backslash followed by None)
returns Python ``None`` for that field; typing ``None`` (no backslash)
returns the string ``"None"``.

Usage
-----

    from dataclasses import dataclass, field
    from panelmark_tui.widgets import DataclassForm

    @dataclass
    class Contact:
        name:  str = field(default="",    metadata={"label": "Full name"})
        email: str = field(default="",    metadata={"label": "E-mail"})
        age:   int = field(default=0,     metadata={"label": "Age"})

    def collect(sh):
        def _save(shell, values):
            return values        # non-None → form closes
        def _cancel(shell, values):
            return False         # non-None → form closes (caller checks for False)

        result = DataclassForm(
            Contact(),
            title="New contact",
            actions=[
                {"shortcut": None, "show_button": True, "label": "Save",
                 "action": _save},
                {"shortcut": "KEY_ESCAPE", "show_button": True, "label": "Cancel",
                 "action": _cancel},
            ],
        ).show(parent_shell=sh)
"""

import dataclasses
import typing

from panelmark.interactions.base import Interaction
from panelmark.draw import DrawCommand, RenderContext, WriteCmd, FillCmd
from panelmark_tui import Shell
from panelmark_tui.widgets._utils import _ModalWidget


# User types this exact string to signal Python None for a field value.
# "\None" (backslash + None) → None; "None" (no backslash) → string "None".
_NONE_SENTINEL = "\\None"

_MAX_LABEL_WIDTH = 14   # characters reserved for the label column
_MAX_FORM_HEIGHT = 20   # cap on the shell region height to avoid giant popups


# ---------------------------------------------------------------------------
# Field-info extraction helpers
# ---------------------------------------------------------------------------

def _type_str(hint) -> str:
    """Convert a type hint to a concise readable string."""
    if hint is type(None):
        return "None"
    if hasattr(hint, "__name__"):
        return hint.__name__
    origin = getattr(hint, "__origin__", None)
    if origin is not None:
        args = getattr(hint, "__args__", ())
        origin_name = getattr(origin, "__name__", str(origin))
        if args:
            args_str = ", ".join(_type_str(a) for a in args)
            return f"{origin_name}[{args_str}]"
        return origin_name
    return str(hint)


def _extract_fields_info(dc_instance) -> list:
    """Return a list of field-descriptor dicts for *dc_instance*.

    Each descriptor has keys:
    ``name``, ``label``, ``hint``, ``has_default``,
    ``default_raw``, ``default_str``.
    """
    dc_type = type(dc_instance)
    try:
        type_hints = typing.get_type_hints(dc_type)
    except Exception:
        type_hints = {}

    infos = []
    for f in dataclasses.fields(dc_instance):
        name = f.name
        meta = f.metadata

        label = meta.get("label", name)

        if "hint" in meta:
            hint = str(meta["hint"])
        else:
            th = type_hints.get(name)
            hint = _type_str(th) if th is not None else None

        if "default" in meta:
            default_raw = meta["default"]
            has_default = True
        elif f.default is not dataclasses.MISSING:
            default_raw = f.default
            has_default = True
        elif f.default_factory is not dataclasses.MISSING:  # type: ignore[misc]
            try:
                default_raw = f.default_factory()  # type: ignore[misc]
            except Exception:
                default_raw = None
            has_default = True
        else:
            default_raw = None
            has_default = False

        # Human-readable default for the "[default]" placeholder
        if has_default:
            if default_raw is None:
                default_str = "None"
            elif isinstance(default_raw, str) and default_raw == _NONE_SENTINEL:
                default_str = _NONE_SENTINEL
            else:
                default_str = str(default_raw)
        else:
            default_str = ""

        infos.append(
            {
                "name": name,
                "label": label,
                "hint": hint,
                "has_default": has_default,
                "default_raw": default_raw,
                "default_str": default_str,
            }
        )
    return infos


# ---------------------------------------------------------------------------
# Internal interaction
# ---------------------------------------------------------------------------

class _DataclassFormInteraction(Interaction):
    """Internal interaction that owns all form fields and button actions."""

    def __init__(self, fields_info: list, actions: list, on_change):
        self._fields_info = fields_info
        self._n_fields = len(fields_info)
        self._actions = list(actions) if actions else []
        self._button_actions = [a for a in self._actions if a.get("show_button", False)]
        self._n_buttons = len(self._button_actions)
        self._on_change = on_change

        # Per-field text state: None = showing default, str = user input
        self._field_text: dict = {}
        for fi in fields_info:
            self._field_text[fi["name"]] = None if fi["has_default"] else ""

        # Focus: 0..n_fields-1 are field rows; n_fields..n_fields+n_buttons-1 are buttons
        self._active_index = 0
        self._scroll_offset = 0
        self._last_height = 1
        self._shell = None  # injected by Shell.assign()

        self._wants_exit = False
        self._exit_value = None

    # ------------------------------------------------------------------
    # Interaction protocol
    # ------------------------------------------------------------------

    @property
    def is_focusable(self) -> bool:
        return True

    def render(self, context: RenderContext, focused: bool = False) -> list:
        self._last_height = context.height
        display_rows = self._build_display_rows(context, focused)

        active_row = self._active_display_row()
        total = len(display_rows)

        if total <= context.height:
            self._scroll_offset = 0
        else:
            if active_row < self._scroll_offset:
                self._scroll_offset = active_row
            elif active_row >= self._scroll_offset + context.height:
                self._scroll_offset = active_row - context.height + 1
            self._scroll_offset = max(0, min(self._scroll_offset, total - context.height))

        cmds: list[DrawCommand] = []
        visible = display_rows[self._scroll_offset : self._scroll_offset + context.height]
        for r, (text, style) in enumerate(visible):
            cmds.append(WriteCmd(row=r, col=0, text=text, style=style))
        for r in range(len(visible), context.height):
            cmds.append(WriteCmd(row=r, col=0, text=" " * context.width))
        return cmds

    def handle_key(self, key) -> tuple:
        self._wants_exit = False

        # Action shortcuts take priority
        for action_def in self._actions:
            sc = action_def.get("shortcut")
            if sc and key == sc:
                return self._activate_action(action_def)

        n_total = self._n_fields + self._n_buttons
        prev_index = self._active_index

        if key in ("KEY_UP", "k"):
            if self._active_index > 0:
                self._active_index -= 1
                self._fire_on_change(prev_index)
            return False, self.get_value()

        if key in ("KEY_DOWN", "j"):
            if self._active_index < n_total - 1:
                self._active_index += 1
                self._fire_on_change(prev_index)
            return False, self.get_value()

        if key in ("KEY_ENTER", "\n", "\r"):
            if self._active_index < self._n_fields:
                # Enter on a field moves to the next slot
                if self._active_index < n_total - 1:
                    self._active_index += 1
                    self._fire_on_change(prev_index)
                return False, self.get_value()
            else:
                # Enter on a button activates it
                btn_idx = self._active_index - self._n_fields
                if btn_idx < self._n_buttons:
                    return self._activate_action(self._button_actions[btn_idx])

        if key in ("KEY_BACKSPACE", "KEY_DELETE", "\x7f"):
            return self._field_backspace()

        # Printable characters type into the active field
        if self._active_index < self._n_fields:
            if len(key) == 1 and (key.isprintable() or key == " "):
                return self._type_char(key)

        return False, self.get_value()

    def get_value(self) -> dict:
        result = {}
        for fi in self._fields_info:
            name = fi["name"]
            text = self._field_text[name]
            if text is None:
                raw = fi["default_raw"]
                result[name] = (
                    None if isinstance(raw, str) and raw == _NONE_SENTINEL else raw
                )
            elif text == _NONE_SENTINEL:
                result[name] = None
            else:
                result[name] = text
        return result

    def set_value(self, value) -> None:
        if not isinstance(value, dict):
            return
        for name, val in value.items():
            for fi in self._fields_info:
                if fi["name"] == name:
                    if val is None:
                        self._field_text[name] = None if fi["has_default"] else ""
                    else:
                        self._field_text[name] = str(val)
                    break

    def signal_return(self) -> tuple:
        if self._wants_exit:
            return True, self._exit_value
        return False, None

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------

    def _build_display_rows(self, context: RenderContext, focused: bool) -> list:
        rows = []
        lw = min(_MAX_LABEL_WIDTH, max(4, context.width // 3))

        for i, fi in enumerate(self._fields_info):
            text = self._field_text[fi["name"]]
            is_default = text is None
            is_active = (i == self._active_index) and focused

            label = fi["label"][:lw]
            value_display = f"[{fi['default_str']}]" if is_default else (text or "")

            line = f"  {label:<{lw}}: {value_display}"
            line = line[: context.width].ljust(context.width)
            rows.append((line, {"reverse": True} if is_active else None))

            if fi["hint"]:
                indent = 2 + lw + 2
                hint_line = (" " * indent + fi["hint"])[: context.width].ljust(context.width)
                rows.append((hint_line, {"dim": True}))

        if self._button_actions:
            rows.append((" " * context.width, None))  # blank separator

            btn_parts = []
            for j, ba in enumerate(self._button_actions):
                is_active_btn = (
                    focused
                    and self._active_index >= self._n_fields
                    and (self._active_index - self._n_fields) == j
                )
                label_text = (
                    f"\u25c0 {ba['label']} \u25b6"
                    if is_active_btn
                    else f"[ {ba['label']} ]"
                )
                btn_parts.append(label_text)

            btn_line = ("  " + "  ".join(btn_parts))[: context.width].ljust(context.width)
            rows.append((btn_line, None))

        return rows

    def _active_display_row(self) -> int:
        """Return the display-row index of the currently active item."""
        row = 0
        for i, fi in enumerate(self._fields_info):
            if i == self._active_index:
                return row
            row += 1
            if fi["hint"]:
                row += 1
        # Active item is in the button area
        if self._button_actions:
            row += 1  # blank separator
        return row  # button row

    # ------------------------------------------------------------------
    # Key-handling helpers
    # ------------------------------------------------------------------

    def _fire_on_change(self, prev_index: int) -> None:
        if self._on_change and prev_index != self._active_index:
            if prev_index < self._n_fields:
                prev_name = self._fields_info[prev_index]["name"]
                self._on_change(prev_name, self.get_value())

    def _type_char(self, char: str) -> tuple:
        fi = self._fields_info[self._active_index]
        name = fi["name"]
        current = self._field_text[name]
        self._field_text[name] = char if current is None else current + char
        return True, self.get_value()

    def _field_backspace(self) -> tuple:
        if self._active_index >= self._n_fields:
            return False, self.get_value()
        fi = self._fields_info[self._active_index]
        name = fi["name"]
        current = self._field_text[name]
        if current is None:
            return False, self.get_value()  # already at default
        if len(current) <= 1:
            self._field_text[name] = None if fi["has_default"] else ""
        else:
            self._field_text[name] = current[:-1]
        return True, self.get_value()

    def _activate_action(self, action_def: dict) -> tuple:
        action = action_def.get("action")
        if action is None:
            return False, self.get_value()
        values = self.get_value()
        result = action(self._shell, values)
        if result is not None:
            self._wants_exit = True
            self._exit_value = result
            return True, values
        return False, self.get_value()


# ---------------------------------------------------------------------------
# Public widget
# ---------------------------------------------------------------------------

def _shell_def(title: str, form_height: int) -> str:
    return (
        f"|=== <bold>{title}</> ===|\n"
        f"|{{{form_height}R $form$           }}|\n"
        f"|========================|\n"
    )


class DataclassForm(_ModalWidget):
    """Modal form that collects structured data from a dataclass template.

    Inspects a dataclass instance and renders one row per field.  Each row
    shows a label (from ``metadata["label"]`` or the field name), the
    current value or a ``[default]`` placeholder, and an optional dim hint
    line derived from ``metadata["hint"]`` or the field's type annotation.

    Typing clears the ``[default]`` placeholder; deleting back to empty
    restores it.  Typing the literal string ``\\None`` (backslash + None)
    makes that field return Python ``None``; typing ``None`` (no backslash)
    returns the string ``"None"``.

    Parameters
    ----------
    dataclass_instance :
        An instance of any ``@dataclass``.  ``dataclasses.fields()`` and
        ``typing.get_type_hints()`` drive the form layout.
    title : str
        Text shown in the popup title border.
    actions : list[dict] | None
        Each dict defines one action and may contain:

        - ``"shortcut"`` : str | None — keyboard shortcut active from any field.
        - ``"show_button"`` : bool — render the action as a button in a button row.
        - ``"label"`` : str — text for the button.
        - ``"action"`` : callable — called as ``action(shell, values)``.
          Return any non-``None`` value to close the form with that result.
    on_change : callable | None
        Called as ``on_change(field_name, values)`` when keyboard focus
        leaves a field.
    width : int
        Popup width in characters (including border walls).

    Returns
    -------
    The non-``None`` value returned by the activated action, or ``None``
    on Escape / Ctrl+Q.
    """

    def __init__(
        self,
        dataclass_instance,
        title: str = "Form",
        actions: list = None,
        on_change=None,
        width: int = 60,
    ):
        if not dataclasses.is_dataclass(dataclass_instance) or isinstance(
            dataclass_instance, type
        ):
            raise TypeError("dataclass_instance must be a dataclass instance, not a class")
        self._dc_instance = dataclass_instance
        self.title = title
        self.actions = list(actions) if actions is not None else []
        self.on_change = on_change
        self.width = width
        self._fields_info = _extract_fields_info(dataclass_instance)

    def _compute_form_height(self) -> int:
        rows = 0
        for fi in self._fields_info:
            rows += 1
            if fi["hint"]:
                rows += 1
        button_actions = [a for a in self.actions if a.get("show_button", False)]
        if button_actions:
            rows += 2  # blank separator + button row
        return min(max(rows, 3), _MAX_FORM_HEIGHT)

    def _build_popup(self, term):
        form_height = self._compute_form_height()
        layout = _shell_def(self.title, form_height)
        popup = Shell(layout, _terminal=term)
        interaction = _DataclassFormInteraction(
            fields_info=self._fields_info,
            actions=self.actions,
            on_change=self.on_change,
        )
        popup.assign("form", interaction)
        return popup
