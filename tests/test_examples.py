"""Smoke tests for examples/ — catch import errors, layout-parse failures,
region mismatches, and render crashes without requiring a real terminal."""
import sys
import pytest
from panelmark_tui.testing import MockTerminal


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _run_headless(sh, term, keys=("\x1b",)):
    """Feed *keys* then call sh.run(); return the exit value."""
    term.feed_keys(list(keys))
    return sh.run()


def _make_hello_shell(term):
    """Build the hello.py shell with MockTerminal, mirroring main()."""
    from examples.hello import LAYOUT, say_hello, show_about
    from panelmark_tui import Shell
    from panelmark_tui.interactions import MenuFunction, StatusMessage

    sh = Shell(LAYOUT, _terminal=term)

    def _quit(sh_inner):
        menu._wants_exit = True
        menu._exit_value = None

    menu = MenuFunction({
        "Say Hello": say_hello,
        "About":     show_about,
        "Quit":      _quit,
    })
    sh.assign("menu", menu)
    sh.assign("status", StatusMessage())
    return sh


# ---------------------------------------------------------------------------
# hello.py
# ---------------------------------------------------------------------------

class TestHelloSmoke:
    def test_import(self):
        """examples.hello can be imported without error."""
        import examples.hello  # noqa: F401

    def test_layout_and_wiring(self):
        """Shell parses LAYOUT and assign() calls succeed without errors."""
        term = MockTerminal(width=80, height=24)
        _make_hello_shell(term)

    def test_quit_exits_cleanly(self):
        """Selecting Quit (third item) causes sh.run() to return."""
        term = MockTerminal(width=80, height=24)
        sh = _make_hello_shell(term)
        # Navigate down twice to "Quit", then Enter
        result = _run_headless(sh, term, ["KEY_DOWN", "KEY_DOWN", "KEY_ENTER"])
        assert result is None

    def test_escape_exits(self):
        """Pressing Escape causes sh.run() to return without error."""
        term = MockTerminal(width=80, height=24)
        sh = _make_hello_shell(term)
        result = _run_headless(sh, term, ["\x1b"])
        assert result is None


# ---------------------------------------------------------------------------
# task_manager.py
# ---------------------------------------------------------------------------

class TestTaskManagerSmoke:
    def test_import(self):
        """examples.task_manager can be imported without error."""
        import examples.task_manager  # noqa: F401

    def test_layout_and_wiring(self):
        """Shell parses LAYOUT and all assign() calls succeed without errors."""
        import examples.task_manager as tm
        from panelmark_tui import Shell
        from panelmark_tui.interactions import ListView, MenuFunction, StatusMessage

        term = MockTerminal(width=80, height=24)
        sh = Shell(tm.LAYOUT, _terminal=term)

        actions_menu = MenuFunction({
            "Add": tm._add_task, "Edit": tm._edit_task,
            "Delete": tm._delete_task, "Filter": tm._filter_tasks,
            "Sort": tm._sort_tasks, "Export": tm._export_tasks,
            "Quit": lambda s: None,
        })
        sh.assign("actions", actions_menu)
        tm._rebuild_task_menu(sh)
        sh.assign("detail", ListView(["(select a task to see details)"]))
        sh.assign("status", tm.StatusMessage())

    def test_escape_exits(self):
        """Pressing Escape causes sh.run() to return without error."""
        import examples.task_manager as tm
        from panelmark_tui import Shell
        from panelmark_tui.interactions import ListView, MenuFunction, StatusMessage

        term = MockTerminal(width=80, height=24)
        sh = Shell(tm.LAYOUT, _terminal=term)

        actions_menu = MenuFunction({
            "Add": tm._add_task, "Edit": tm._edit_task,
            "Delete": tm._delete_task, "Filter": tm._filter_tasks,
            "Sort": tm._sort_tasks, "Export": tm._export_tasks,
            "Quit": lambda s: None,
        })
        sh.assign("actions", actions_menu)
        tm._rebuild_task_menu(sh)
        sh.assign("detail", ListView(["(select a task to see details)"]))
        sh.assign("status", StatusMessage())

        result = _run_headless(sh, term, ["\x1b"])
        assert result is None

    def test_quit_with_confirm(self, monkeypatch):
        """Selecting Quit → confirming causes sh.run() to exit cleanly."""
        import examples.task_manager as tm
        from panelmark_tui import Shell
        from panelmark_tui.interactions import ListView, MenuFunction, StatusMessage

        monkeypatch.setattr(tm, "_state", {"current_task": None})

        term = MockTerminal(width=80, height=24)
        sh = Shell(tm.LAYOUT, _terminal=term)

        def _quit(sh_inner):
            from panelmark_tui.widgets import Confirm
            ok = Confirm(
                title="Quit",
                message_lines=["Exit Task Manager?"],
                buttons={"Quit": True, "Cancel": False},
            ).show(parent_shell=sh_inner)
            if ok:
                actions_menu._wants_exit = True
                actions_menu._exit_value = None

        actions_menu = MenuFunction({
            "Add": tm._add_task, "Edit": tm._edit_task,
            "Delete": tm._delete_task, "Filter": tm._filter_tasks,
            "Sort": tm._sort_tasks, "Export": tm._export_tasks,
            "Quit": _quit,
        })
        sh.assign("actions", actions_menu)
        tm._rebuild_task_menu(sh)
        sh.assign("detail", ListView(["(select a task to see details)"]))
        sh.assign("status", StatusMessage())

        # Navigate to Quit (6 downs), Enter to open dialog, Enter to confirm
        result = _run_headless(
            sh, term,
            ["KEY_DOWN"] * 6 + ["KEY_ENTER", "KEY_ENTER"],
        )
        assert result is None
