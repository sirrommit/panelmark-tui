"""Internal utilities shared across widget modules.  Not part of the public API."""

from panelmark_tui.interactions.menu import MenuFunction


class _ModalWidget:
    """Base class for modal popup widgets that delegate to Shell.run_modal().

    Subclasses implement ``_build_popup(term)`` to construct and wire a Shell.
    ``show()`` handles terminal extraction and the ``run_modal()`` call.

    Subclasses must set ``self.width`` in their ``__init__``.
    """

    def _build_popup(self, term):
        """Build and return a fully-wired Shell for this popup.

        Parameters
        ----------
        term :
            Terminal object (``blessed.Terminal`` or ``MockTerminal``), or
            ``None`` to let Shell create its own.

        Returns
        -------
        Shell
        """
        raise NotImplementedError

    def show(self, parent_shell=None, **run_modal_kwargs):
        """Display the popup and block until the user makes a choice.

        Parameters
        ----------
        parent_shell : Shell | None
            If provided, the parent's display is fully restored when the popup
            closes.  Pass the ``sh`` argument received inside a callback.
        **run_modal_kwargs
            Forwarded to ``Shell.run_modal()``.  Use ``row``/``col`` to
            override auto-centering.

        Returns
        -------
        The value returned by the focused interaction on selection, or
        ``None`` on Escape / Ctrl+Q.
        """
        term = parent_shell.terminal if parent_shell is not None else None
        popup = self._build_popup(term)
        return popup.run_modal(
            width=self.width,
            parent_shell=parent_shell,
            **run_modal_kwargs,
        )


class _SubmittingMenu(MenuFunction):
    """A MenuFunction with OK / Cancel that signals run_modal() to exit.

    On OK, reads ``shell.get(value_region)`` and signals exit with that value.
    On Cancel, signals exit with ``None``.

    Parameters
    ----------
    value_region : str
        The region name whose value OK should capture and return.
    ok_label : str
        Label for the submit button (default ``"OK"``).
    cancel_label : str
        Label for the cancel button (default ``"Cancel"``).
    """

    def __init__(
        self,
        value_region: str,
        ok_label: str = "OK",
        cancel_label: str = "Cancel",
    ):
        self._value_region = value_region
        self._submitted = False
        self._result = None
        super().__init__({
            ok_label: self._handle_ok,
            cancel_label: self._handle_cancel,
        })

    def _handle_ok(self, sh):
        self._result = sh.get(self._value_region)
        self._submitted = True

    def _handle_cancel(self, sh):
        self._result = None
        self._submitted = True

    def signal_return(self) -> tuple:
        if self._submitted:
            return True, self._result
        return False, None
