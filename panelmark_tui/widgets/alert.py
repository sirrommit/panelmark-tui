"""Alert widget — an informational or warning popup with a single OK button.

Shell layout
------------

    |=== <bold>Title</> ===|
    |{3R $message$         }|
    |----------------------|
    |{1R $ok$              }|
    |======================|

Height is always auto-detected from the explicit row declarations:
**7 rows** (1 title + 3 message + 1 divider + 1 ok + 1 bottom border).

Usage
-----

    from panelmark_tui.widgets.alert import Alert

    def warn_user(sh):
        Alert(
            title="Warning",
            message_lines=["No internet connection.", "Check your settings."],
        ).show(parent_shell=sh)
"""

from panelmark_tui import Shell
from panelmark_tui.interactions import ListView, MenuReturn
from panelmark_tui.widgets._utils import _ModalWidget


def _shell_def(title: str) -> str:
    return (
        f"|=== <bold>{title}</> ===|\n"
        "|{3R $message$           }|\n"
        "|------------------------|\n"
        "|{1R $ok$                }|\n"
        "|========================|\n"
    )


class Alert(_ModalWidget):
    """Informational or warning popup with a single OK button.

    Parameters
    ----------
    title : str
        Text displayed in the popup border (rendered bold).
    message_lines : list[str]
        Lines of text shown in the message area (3 rows visible).
    width : int
        Width of the popup in characters (including border walls).
        Height is always auto-detected from the row declarations.

    Returns
    -------
    ``True`` when OK is pressed, ``None`` on Escape / Ctrl+Q.
    """

    def __init__(
        self,
        title: str = "Alert",
        message_lines: list = None,
        width: int = 40,
    ):
        self.title = title
        self.message_lines = list(message_lines) if message_lines is not None else []
        self.width = width

    def _build_popup(self, term):
        popup = Shell(_shell_def(self.title), _terminal=term)
        popup.assign("message", ListView(self.message_lines, bullet=" "))
        popup.assign("ok", MenuReturn({"OK": True}))
        return popup
