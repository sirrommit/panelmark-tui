"""DataclassForm widget — modal shell wrapper around DataclassFormInteraction.

Usage
-----

    from dataclasses import dataclass, field
    from panelmark_tui.widgets import DataclassForm

    @dataclass
    class Contact:
        name:  str = field(default="",  metadata={"label": "Full name"})
        email: str = field(default="",  metadata={"label": "E-mail"})
        age:   int = field(default=0,   metadata={"label": "Age"})

    def collect(sh):
        def _save(shell, values):
            return values   # non-None → form closes
        def _cancel(shell, values):
            return False    # non-None → form closes

        result = DataclassForm(
            Contact(),
            title="New contact",
            actions=[
                {"shortcut": None, "show_button": True, "label": "Save",
                 "action": _save},
                {"shortcut": None, "show_button": True, "label": "Cancel",
                 "action": _cancel},
            ],
        ).show(parent_shell=sh)

See ``DataclassFormInteraction`` in ``panelmark_tui.interactions`` to use
the form inline in your own shell without a modal wrapper.
"""

import dataclasses

from panelmark_tui import Shell
from panelmark_tui.interactions.form import DataclassFormInteraction, _extract_fields_info
from panelmark_tui.widgets._utils import _ModalWidget


_MAX_FORM_HEIGHT = 20


def _shell_def(title: str, form_height: int) -> str:
    return (
        f"|=== <bold>{title}</> ===|\n"
        f"|{{{form_height}R $form$           }}|\n"
        f"|========================|\n"
    )


class DataclassForm(_ModalWidget):
    """Modal form that collects structured data from a dataclass template.

    A thin modal wrapper around ``DataclassFormInteraction``.  The
    interaction handles all field rendering and key handling; this class
    builds the surrounding shell and runs it as a popup.

    For inline (non-modal) use, assign ``DataclassFormInteraction`` directly
    to a region in your own shell.

    Parameters
    ----------
    dataclass_instance :
        An instance of any ``@dataclass``.
    title : str
        Text shown in the popup title border.
    actions : list[dict] | None
        Passed directly to ``DataclassFormInteraction``.  Each dict may
        contain ``"shortcut"``, ``"show_button"``, ``"label"``,
        ``"action"`` (called as ``action(shell, values)``; return
        non-``None`` to close the form).
    on_change : callable | None
        Passed to ``DataclassFormInteraction``.  Called as
        ``on_change(field_name, values)`` when focus leaves a field.
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
        if any(a.get("show_button", False) for a in self.actions):
            rows += 2  # blank separator + button row
        return min(max(rows, 3), _MAX_FORM_HEIGHT)

    def _build_popup(self, term):
        form_height = self._compute_form_height()
        layout = _shell_def(self.title, form_height)
        popup = Shell(layout, _terminal=term)
        popup.assign(
            "form",
            DataclassFormInteraction(
                self._dc_instance,
                actions=self.actions,
                on_change=self.on_change,
            ),
        )
        return popup
