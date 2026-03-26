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


# ---------------------------------------------------------------------------
# hello.py
# ---------------------------------------------------------------------------

class TestHelloSmoke:
    def test_import(self):
        """examples.hello can be imported without error."""
        import examples.hello  # noqa: F401

    def test_layout_and_wiring(self):
        """Shell parses LAYOUT and assign() calls succeed without errors."""
        from examples.hello import LAYOUT, say_hello, show_about
        from panelmark_tui import Shell
        from panelmark_tui.interactions import MenuHybrid, StatusMessage

        term = MockTerminal(width=80, height=24)
        sh = Shell(LAYOUT, _terminal=term)
        sh.assign("menu", MenuHybrid({
            "Say Hello": say_hello,
            "About":     show_about,
            "Quit":      "quit",
        }))
        sh.assign("status", StatusMessage())

    def test_quit_exits_cleanly(self):
        """Selecting Quit (third item) causes sh.run() to return 'quit'."""
        from examples.hello import LAYOUT, say_hello, show_about
        from panelmark_tui import Shell
        from panelmark_tui.interactions import MenuHybrid, StatusMessage

        term = MockTerminal(width=80, height=24)
        sh = Shell(LAYOUT, _terminal=term)
        sh.assign("menu", MenuHybrid({
            "Say Hello": say_hello,
            "About":     show_about,
            "Quit":      "quit",
        }))
        sh.assign("status", StatusMessage())

        # Navigate down twice to "Quit", then Enter
        result = _run_headless(sh, term, ["KEY_DOWN", "KEY_DOWN", "KEY_ENTER"])
        assert result == "quit"

    def test_escape_exits(self):
        """Pressing Escape causes sh.run() to return without error."""
        from examples.hello import LAYOUT, say_hello, show_about
        from panelmark_tui import Shell
        from panelmark_tui.interactions import MenuHybrid, StatusMessage

        term = MockTerminal(width=80, height=24)
        sh = Shell(LAYOUT, _terminal=term)
        sh.assign("menu", MenuHybrid({
            "Say Hello": say_hello,
            "About":     show_about,
            "Quit":      "quit",
        }))
        sh.assign("status", StatusMessage())

        result = _run_headless(sh, term, ["\x1b"])
        assert result is None


# ---------------------------------------------------------------------------
# task_manager.py
# ---------------------------------------------------------------------------

class TestTaskManagerSmoke:
    def test_import(self):
        """examples.task_manager can be imported without error."""
        import examples.task_manager  # noqa: F401

    def test_layout_and_wiring(self, monkeypatch):
        """Shell parses LAYOUT and all assign() calls succeed without errors."""
        import examples.task_manager as tm
        from panelmark_tui import Shell
        from panelmark_tui.interactions import ListView, MenuHybrid, StatusMessage

        term = MockTerminal(width=80, height=24)
        sh = Shell(tm.LAYOUT, _terminal=term)

        actions_menu = MenuHybrid({
            "Add": tm._add_task, "Edit": tm._edit_task,
            "Delete": tm._delete_task, "Filter": tm._filter_tasks,
            "Sort": tm._sort_tasks, "Export": tm._export_tasks,
            "Quit": lambda s: None,
        })
        sh.assign("actions", actions_menu)
        tm._rebuild_task_menu(sh)
        sh.assign("detail", ListView(["(select a task to see details)"]))
        sh.assign("status", StatusMessage())

    def test_escape_exits(self, monkeypatch):
        """Pressing Escape causes sh.run() to return without error."""
        import examples.task_manager as tm
        from panelmark_tui import Shell
        from panelmark_tui.interactions import ListView, MenuHybrid, StatusMessage

        term = MockTerminal(width=80, height=24)
        sh = Shell(tm.LAYOUT, _terminal=term)

        actions_menu = MenuHybrid({
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
        from panelmark_tui.interactions import ListView, StatusMessage
        from panelmark_tui.interactions import MenuHybrid

        # Reset shared module state so this test is independent
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

        actions_menu = MenuHybrid({
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
