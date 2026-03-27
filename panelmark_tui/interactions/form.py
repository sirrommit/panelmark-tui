import dataclasses
import typing

from panelmark.interactions.base import Interaction
from panelmark.draw import DrawCommand, RenderContext, WriteCmd, FillCmd


_VALID_TYPES = {"str", "int", "float", "bool", "choices"}


class FormInput(Interaction):
    """A structured data-entry form with multiple typed fields."""

    def __init__(self, fields: dict):
        """
        fields: dict[str, dict] mapping variable names to field definitions.
        Each field definition must have 'type' and 'descriptor'.
        """
        self._fields = {}  # ordered dict of field definitions
        self._field_keys = []
        self._field_states = {}  # key -> current text/value
        self._field_errors = {}  # key -> error message or None
        self._active_index = 0  # 0..len(fields) is fields, len(fields) is Submit
        self._wants_exit = False
        self._exit_value = None
        self._scroll_offset = 0

        for key, defn in fields.items():
            if 'type' not in defn:
                raise ValueError(f"field '{key}' missing required key 'type'")
            if 'descriptor' not in defn:
                raise ValueError(f"field '{key}' missing required key 'descriptor'")
            ftype = defn['type']
            if ftype not in _VALID_TYPES:
                raise ValueError(f"field '{key}' has unknown type '{ftype}'")
            if ftype == 'choices':
                if 'options' not in defn:
                    raise ValueError(f"field '{key}' type 'choices' requires 'options'")
                if not defn['options']:
                    raise ValueError(f"field '{key}' options must be a non-empty list")

            # Validate and set default
            default = defn.get('default')
            if default is not None:
                try:
                    _coerce(ftype, default)
                except (ValueError, TypeError):
                    raise ValueError(f"field '{key}' default value does not match type")

            self._fields[key] = dict(defn)
            self._field_keys.append(key)

            # Initialize state
            if ftype == 'bool':
                self._field_states[key] = _coerce('bool', default) if default is not None else False
            elif ftype == 'choices':
                options = defn['options']
                if default is not None and default in options:
                    self._field_states[key] = options.index(default)
                else:
                    self._field_states[key] = 0
            else:
                self._field_states[key] = str(default) if default is not None else ''

            self._field_errors[key] = None

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        num_fields = len(self._field_keys)

        # Build display rows as (text, style) tuples
        display_rows: list[tuple[str, dict | None]] = []
        for i, key in enumerate(self._field_keys):
            defn = self._fields[key]
            descriptor = defn['descriptor']
            ftype = defn['type']
            state = self._field_states[key]
            error = self._field_errors.get(key)

            # Format field value
            if ftype == 'bool':
                value_str = '< Yes >' if state else '< No  >'
            elif ftype == 'choices':
                options = defn['options']
                selected = options[state] if 0 <= state < len(options) else ''
                value_str = f'< {selected} >'
            else:
                placeholder = defn.get('placeholder', '')
                if state == '' and placeholder:
                    value_str = f'[{placeholder[:max(0, context.width - len(descriptor) - 5)]}]'
                else:
                    value_str = f'[{state}]'

            line = f'  {descriptor:<12}: {value_str}'
            line = line[:context.width].ljust(context.width)

            is_active = (i == self._active_index) and focused
            display_rows.append((line, {'reverse': True} if is_active else None))

            if error:
                err_line = f'  {"":12}  ! {error}'
                err_line = err_line[:context.width].ljust(context.width)
                display_rows.append((err_line, None))

        # Separator
        sep = '-' * min(context.width, 34)
        display_rows.append((sep.ljust(context.width), None))

        # Submit button
        submit_line = '  [ Submit ]'.ljust(context.width)
        is_submit_active = (self._active_index == num_fields) and focused
        display_rows.append((submit_line, {'reverse': True} if is_submit_active else None))

        # Compute which display row the active item is on
        active_display_row = 0
        if self._active_index == num_fields:
            active_display_row = len(display_rows) - 1
        else:
            row_cursor = 0
            for i, key in enumerate(self._field_keys):
                if i == self._active_index:
                    active_display_row = row_cursor
                    break
                row_cursor += 2 if self._field_errors.get(key) else 1

        # Scroll to keep active row visible
        total_rows = len(display_rows)
        if total_rows <= context.height:
            self._scroll_offset = 0
        else:
            if active_display_row < self._scroll_offset:
                self._scroll_offset = active_display_row
            elif active_display_row >= self._scroll_offset + context.height:
                self._scroll_offset = active_display_row - context.height + 1
            self._scroll_offset = max(0, min(self._scroll_offset, total_rows - context.height))

        # Build commands for visible rows
        cmds: list[DrawCommand] = []
        visible = display_rows[self._scroll_offset:self._scroll_offset + context.height]
        for i in range(context.height):
            if i < len(visible):
                text, style = visible[i]
                cmds.append(WriteCmd(row=i, col=0, text=text, style=style))
            else:
                cmds.append(WriteCmd(row=i, col=0, text=' ' * context.width))
        return cmds

    def handle_key(self, key) -> tuple:
        self._wants_exit = False
        num_fields = len(self._field_keys)

        if key.startswith("KEY_"):
            name = key
            if name == 'KEY_UP':
                self._active_index = max(0, self._active_index - 1)
                return False, self.get_value()
            elif name == 'KEY_DOWN':
                self._active_index = min(num_fields, self._active_index + 1)
                return False, self.get_value()
            elif name == 'KEY_ENTER':
                if self._active_index == num_fields:
                    return self._submit()
                else:
                    # For bool/choices, treat Enter as toggle/cycle
                    return self._interact_field()
            elif name == 'KEY_LEFT':
                return self._interact_field_left()
            elif name == 'KEY_RIGHT':
                return self._interact_field_right()
            elif name in ('KEY_BACKSPACE', 'KEY_DELETE'):
                return self._field_backspace()
        else:
            char = key
            if char == ' ':
                return self._interact_field()
            elif char.isprintable() and char not in ('\t',):
                return self._field_type_char(char)

        return False, self.get_value()

    def _current_key(self):
        if self._active_index < len(self._field_keys):
            return self._field_keys[self._active_index]
        return None

    def _interact_field(self):
        key = self._current_key()
        if key is None:
            return False, self.get_value()
        defn = self._fields[key]
        ftype = defn['type']
        if ftype == 'bool':
            self._field_states[key] = not self._field_states[key]
            return True, self.get_value()
        elif ftype == 'choices':
            options = defn['options']
            self._field_states[key] = (self._field_states[key] + 1) % len(options)
            return True, self.get_value()
        return False, self.get_value()

    def _interact_field_left(self):
        key = self._current_key()
        if key is None:
            return False, self.get_value()
        defn = self._fields[key]
        ftype = defn['type']
        if ftype == 'bool':
            self._field_states[key] = False
            return True, self.get_value()
        elif ftype == 'choices':
            options = defn['options']
            self._field_states[key] = (self._field_states[key] - 1) % len(options)
            return True, self.get_value()
        return False, self.get_value()

    def _interact_field_right(self):
        key = self._current_key()
        if key is None:
            return False, self.get_value()
        defn = self._fields[key]
        ftype = defn['type']
        if ftype == 'bool':
            self._field_states[key] = True
            return True, self.get_value()
        elif ftype == 'choices':
            options = defn['options']
            self._field_states[key] = (self._field_states[key] + 1) % len(options)
            return True, self.get_value()
        return False, self.get_value()

    def _field_backspace(self):
        key = self._current_key()
        if key is None:
            return False, self.get_value()
        defn = self._fields[key]
        ftype = defn['type']
        if ftype in ('str', 'int', 'float'):
            state = self._field_states[key]
            if state:
                self._field_states[key] = state[:-1]
                return True, self.get_value()
        return False, self.get_value()

    def _field_type_char(self, char: str):
        key = self._current_key()
        if key is None:
            return False, self.get_value()
        defn = self._fields[key]
        ftype = defn['type']
        state = self._field_states[key]

        if ftype == 'str':
            self._field_states[key] = state + char
            return True, self.get_value()
        elif ftype == 'int':
            if char.isdigit() or (char == '-' and not state):
                self._field_states[key] = state + char
                return True, self.get_value()
        elif ftype == 'float':
            if char.isdigit() or (char == '-' and not state) or (char == '.' and '.' not in state):
                self._field_states[key] = state + char
                return True, self.get_value()
        return False, self.get_value()

    def _validate_field(self, key) -> str | None:
        """Validate a field, return error message or None."""
        defn = self._fields[key]
        ftype = defn['type']
        state = self._field_states[key]

        if ftype in ('int', 'float'):
            if state:
                try:
                    parsed = _coerce(ftype, state)
                except (ValueError, TypeError):
                    return f'Must be a {"whole number" if ftype == "int" else "number"}'
                validator = defn.get('validator')
                if validator:
                    result = validator(parsed)
                    if result is not True and result:
                        return str(result)
            elif defn.get('required'):
                return 'This field is required'
        elif ftype == 'str':
            if state:
                validator = defn.get('validator')
                if validator:
                    result = validator(state)
                    if result is not True and result:
                        return str(result)
            elif defn.get('required'):
                return 'This field is required'

        return None

    def _submit(self):
        """Attempt to submit the form."""
        # Validate all fields
        has_errors = False
        first_error_index = None

        for i, key in enumerate(self._field_keys):
            error = self._validate_field(key)
            self._field_errors[key] = error
            if error:
                has_errors = True
                if first_error_index is None:
                    first_error_index = i

        if has_errors:
            self._active_index = first_error_index
            return False, self.get_value()

        # Build result dict
        result = {}
        for key in self._field_keys:
            defn = self._fields[key]
            ftype = defn['type']
            state = self._field_states[key]

            if ftype == 'str':
                result[key] = state if state else None
            elif ftype == 'int':
                result[key] = int(state) if state else None
            elif ftype == 'float':
                result[key] = float(state) if state else None
            elif ftype == 'bool':
                result[key] = state
            elif ftype == 'choices':
                options = defn['options']
                result[key] = options[state] if 0 <= state < len(options) else None

        self._exit_value = result
        self._wants_exit = True
        return True, result

    def get_value(self) -> dict:
        """Return current state as a dict."""
        result = {}
        for key in self._field_keys:
            defn = self._fields[key]
            ftype = defn['type']
            state = self._field_states[key]

            if ftype == 'choices':
                options = defn['options']
                result[key] = options[state] if 0 <= state < len(options) else None
            elif ftype == 'bool':
                result[key] = state
            else:
                result[key] = state
        return result

    def set_value(self, value) -> None:
        """Set field values from a dict."""
        for key, val in value.items():
            if key in self._fields:
                defn = self._fields[key]
                ftype = defn['type']
                if ftype == 'bool':
                    self._field_states[key] = bool(val)
                elif ftype == 'choices':
                    options = defn['options']
                    if val in options:
                        self._field_states[key] = options.index(val)
                else:
                    self._field_states[key] = str(val) if val is not None else ''

    def signal_return(self) -> tuple:
        if self._wants_exit:
            return True, self._exit_value
        return False, None


def _coerce(ftype: str, value):
    """Coerce a value to the given type, raising ValueError if not possible."""
    if ftype == 'str':
        return str(value)
    elif ftype == 'int':
        return int(value)
    elif ftype == 'float':
        return float(value)
    elif ftype == 'bool':
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        raise ValueError(
            f"Boolean field requires True/False or the strings 'true'/'false', got {value!r}"
        )
    return value


# ---------------------------------------------------------------------------
# DataclassFormInteraction
# ---------------------------------------------------------------------------

# Typing \None in a field returns Python None; typing None returns "None".
_NONE_SENTINEL = "\\None"

_MAX_LABEL_WIDTH = 14   # characters reserved for the label column


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


class DataclassFormInteraction(Interaction):
    """A form interaction driven by a dataclass instance.

    Renders one row per field with an optional dim hint line.  Fields with
    defaults show a ``[default]`` placeholder; typing clears it and
    deleting back to empty restores it.

    Typing the literal string ``\\None`` (backslash + None) makes a field
    return Python ``None``; typing ``None`` (no backslash) returns the
    string ``"None"``.

    Parameters
    ----------
    dataclass_instance :
        An instance of any ``@dataclass``.
    actions : list[dict] | None
        Each dict may contain:

        - ``"shortcut"`` : str | None
        - ``"show_button"`` : bool — render as a button in the button row
        - ``"label"`` : str
        - ``"action"`` : callable ``(shell, values) -> result``
          Return non-``None`` to signal shell exit with that result.
    on_change : callable | None
        Called as ``on_change(field_name, values)`` when focus leaves a field.
    """

    def __init__(self, dataclass_instance, actions: list = None, on_change=None):
        if not dataclasses.is_dataclass(dataclass_instance) or isinstance(
            dataclass_instance, type
        ):
            raise TypeError(
                "dataclass_instance must be a dataclass instance, not a class"
            )
        self._fields_info = _extract_fields_info(dataclass_instance)
        self._n_fields = len(self._fields_info)
        self._actions = list(actions) if actions else []
        self._button_actions = [a for a in self._actions if a.get("show_button", False)]
        self._n_buttons = len(self._button_actions)
        self._on_change = on_change

        self._field_text: dict = {}
        for fi in self._fields_info:
            self._field_text[fi["name"]] = None if fi["has_default"] else ""

        self._active_index = 0
        self._scroll_offset = 0
        self._last_height = 1
        self._shell = None  # injected by Shell.assign()

        self._wants_exit = False
        self._exit_value = None

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
                if self._active_index < n_total - 1:
                    self._active_index += 1
                    self._fire_on_change(prev_index)
                return False, self.get_value()
            else:
                btn_idx = self._active_index - self._n_fields
                if btn_idx < self._n_buttons:
                    return self._activate_action(self._button_actions[btn_idx])

        if key in ("KEY_BACKSPACE", "KEY_DELETE", "\x7f"):
            return self._field_backspace()

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
                    elif fi["has_default"] and val == fi["default_raw"]:
                        # Restore to default mode so get_value() round-trips cleanly
                        self._field_text[name] = None
                    else:
                        self._field_text[name] = str(val)
                    break

    def signal_return(self) -> tuple:
        if self._wants_exit:
            return True, self._exit_value
        return False, None

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
            rows.append((" " * context.width, None))

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
        row = 0
        for i, fi in enumerate(self._fields_info):
            if i == self._active_index:
                return row
            row += 1
            if fi["hint"]:
                row += 1
        if self._button_actions:
            row += 1
        return row

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
            return False, self.get_value()
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
