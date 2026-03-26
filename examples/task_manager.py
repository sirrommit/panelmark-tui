"""task_manager.py — panelmark-tui feature showcase.

A personal task manager that demonstrates most of the package:

  Shell layout   two-panel shell (task list | detail view)
  MenuFunction   action bar at the top
  MenuFunction   scrollable task list (selection drives the detail panel)
  ListView       read-only task detail view
  StatusMessage  feedback bar at the bottom
  on_change      detail panel auto-updates when task selection changes
  FormInput      add / edit tasks (title, priority, status, notes)
  DatePicker     pick a due date inside the add-task flow
  CheckBox       (via ListSelect multi) pick tags for a task
  ListSelect     single: sort-order picker; multi: filter and tag selection
  InputPrompt    quick-rename a task title
  Confirm        confirm before deleting or quitting
  Alert          show error / info messages
  Progress       simulated export with a cancellable progress bar
  FilePicker     choose where to export

Run:
    python examples/task_manager.py
"""

import datetime
import time

from panelmark_tui import Shell
from panelmark_tui.interactions import (
    FormInput,
    ListView,
    MenuFunction,
    MenuHybrid,
    StatusMessage,
)
from panelmark_tui.widgets import (
    Alert,
    Confirm,
    DatePicker,
    FilePicker,
    InputPrompt,
    ListSelect,
    Progress,
)

# ── Sample data ───────────────────────────────────────────────────────────────

PRIORITIES = ["High", "Medium", "Low"]
STATUSES   = ["To Do", "In Progress", "Done"]
ALL_TAGS   = ["work", "personal", "urgent", "idea", "blocked"]

def _make_task(title, priority="Medium", status="To Do",
               due=None, tags=None, notes=""):
    return {
        "title":    title,
        "priority": priority,
        "status":   status,
        "due":      due,          # datetime.date or None
        "tags":     tags or [],
        "notes":    notes,
    }

TASKS = [
    _make_task("Read panelmark-tui docs", "High",   "In Progress",
               due=datetime.date.today() + datetime.timedelta(days=1),
               tags=["work"], notes="Focus on interactions chapter."),
    _make_task("Write unit tests",        "High",   "To Do",
               due=datetime.date.today() + datetime.timedelta(days=3),
               tags=["work", "urgent"]),
    _make_task("Buy groceries",           "Low",    "To Do",
               tags=["personal"], notes="Milk, eggs, coffee."),
    _make_task("Plan weekend trip",       "Medium", "To Do",
               due=datetime.date.today() + datetime.timedelta(days=14),
               tags=["personal", "idea"]),
    _make_task("Fix login bug",           "High",   "In Progress",
               tags=["work", "urgent", "blocked"],
               notes="Waiting on infra team for DB access."),
    _make_task("Read sci-fi novel",       "Low",    "To Do",
               tags=["personal"]),
]

# Active filter / sort state (mutated by callbacks)
_filter_tags = set()       # empty = show all
_sort_key    = "priority"  # "priority" | "status" | "due" | "title"

# Currently-selected task (mutated by callbacks)
_state = {"current_task": None}

# ── Helpers ───────────────────────────────────────────────────────────────────

_PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}
_STATUS_ORDER   = {"In Progress": 0, "To Do": 1, "Done": 2}

def _sort_key_fn(task):
    if _sort_key == "priority":
        return (_PRIORITY_ORDER.get(task["priority"], 9), task["title"])
    if _sort_key == "status":
        return (_STATUS_ORDER.get(task["status"], 9), task["title"])
    if _sort_key == "due":
        due = task["due"] or datetime.date(9999, 12, 31)
        return (due, task["title"])
    return (task["title"],)


def _visible_tasks():
    tasks = [t for t in TASKS
             if not _filter_tags or _filter_tags & set(t["tags"])]
    return sorted(tasks, key=_sort_key_fn)


def _task_label(task):
    icons = {"High": "!", "Medium": "·", "Low": " "}
    icon  = icons.get(task["priority"], " ")
    done  = "✓" if task["status"] == "Done" else " "
    due_s = f"  [{task['due']}]" if task["due"] else ""
    return f"[{done}] {icon} {task['title']}{due_s}"


def _task_details(task):
    lines = [
        f"Title:    {task['title']}",
        f"Priority: {task['priority']}",
        f"Status:   {task['status']}",
        f"Due:      {task['due'] or '—'}",
        f"Tags:     {', '.join(task['tags']) or '—'}",
        "",
    ]
    if task["notes"]:
        lines.append("Notes:")
        for line in task["notes"].splitlines():
            lines.append(f"  {line}")
    else:
        lines.append("(no notes)")
    return lines


def _rebuild_task_menu(sh, select_title=None):
    """Recreate the $tasks$ MenuFunction from the current data and filters."""
    visible = _visible_tasks()

    callbacks = {}
    for t in visible:
        def cb(shell, task=t):
            _show_detail(shell, task)
        callbacks[_task_label(t)] = cb

    if not callbacks:
        callbacks["(no tasks match filter)"] = lambda sh: None

    # Replace the interaction — unassign first, then re-assign.
    sh.unassign("tasks")
    sh.assign("tasks", MenuFunction(callbacks))

    # Re-select the task that was active before the rebuild.
    if select_title:
        for i, task in enumerate(visible):
            if task["title"] == select_title:
                sh.update("tasks", _task_label(task))
                break


def _show_detail(sh, task):
    sh.update("detail", _task_details(task))
    _state["current_task"] = task


def _current_task(sh):
    return _state["current_task"]


# ── Action callbacks ──────────────────────────────────────────────────────────

def _add_task(sh):
    """Open a FormInput to create a new task, then a DatePicker and tag picker."""
    form = FormInput({
        "title": {
            "type":       "str",
            "descriptor": "Title",
            "required":   True,
            "validator":  lambda v: True if v.strip() else "Title cannot be empty",
        },
        "priority": {
            "type":       "choices",
            "descriptor": "Priority",
            "options":    PRIORITIES,
            "default":    "Medium",
        },
        "status": {
            "type":       "choices",
            "descriptor": "Status",
            "options":    STATUSES,
            "default":    "To Do",
        },
        "notes": {
            "type":       "str",
            "descriptor": "Notes (optional)",
            "required":   False,
        },
    })

    # Embed the form in a small modal shell.
    form_def = """
|=== <bold>New Task</> ==|
|{8R $form$              }|
|=======================|
"""
    form_sh = Shell(form_def)
    form_sh.assign("form", form)
    result = form_sh.run_modal(parent_shell=sh, width=40)

    if result is None:
        sh.update("status", ("info", "Cancelled."))
        return

    # Optionally set a due date with DatePicker.
    due = DatePicker(title="Due date  (Esc to skip)").show(parent_shell=sh)

    # Optionally add tags with ListSelect in multi mode.
    selected = ListSelect(
        title       = "Tags  (Esc to skip)",
        prompt_lines= ["Select tags for this task:"],
        items       = {t: False for t in ALL_TAGS},
        multi       = True,
    ).show(parent_shell=sh)
    tags = [t for t, v in (selected or {}).items() if v]

    task = _make_task(
        title    = result["title"].strip(),
        priority = result["priority"],
        status   = result["status"],
        due      = due,
        tags     = tags,
        notes    = (result.get("notes") or "").strip(),
    )
    TASKS.append(task)
    _rebuild_task_menu(sh, select_title=task["title"])
    _show_detail(sh, task)
    sh.update("status", ("success", f"Added: {task['title']}"))


def _edit_task(sh):
    """Edit the selected task: rename, change priority/status, pick due date."""
    task = _current_task(sh)
    if task is None:
        Alert(title="No selection",
              message_lines=["Select a task first."]).show(parent_shell=sh)
        return

    # Quick-rename via InputPrompt.
    new_title = InputPrompt(
        title       = "Rename task",
        prompt_lines= ["Enter a new title:"],
        initial     = task["title"],
    ).show(parent_shell=sh)

    if new_title is None:
        return
    if not new_title.strip():
        Alert(title="Error",
              message_lines=["Title cannot be empty."]).show(parent_shell=sh)
        return

    # Change priority and status via ListSelect (single-pick).
    new_priority = ListSelect(
        title       = "Priority",
        prompt_lines= [f"Current: {task['priority']}"],
        items       = PRIORITIES,
    ).show(parent_shell=sh) or task["priority"]

    new_status = ListSelect(
        title       = "Status",
        prompt_lines= [f"Current: {task['status']}"],
        items       = STATUSES,
    ).show(parent_shell=sh) or task["status"]

    # Optionally update the due date with DatePicker.
    new_due = DatePicker(
        title   = "Due date  (Esc to keep current)",
        initial = task["due"] or datetime.date.today(),
    ).show(parent_shell=sh)
    if new_due is None:
        new_due = task["due"]

    task["title"]    = new_title.strip()
    task["priority"] = new_priority
    task["status"]   = new_status
    task["due"]      = new_due

    _rebuild_task_menu(sh, select_title=task["title"])
    _show_detail(sh, task)
    sh.update("status", ("success", f"Updated: {task['title']}"))


def _delete_task(sh):
    """Delete the selected task after a Confirm dialog."""
    task = _current_task(sh)
    if task is None:
        Alert(title="No selection",
              message_lines=["Select a task first."]).show(parent_shell=sh)
        return

    ok = Confirm(
        title         = "Delete task",
        message_lines = [f"Delete '{task['title']}'?", "This cannot be undone."],
        buttons       = {"Delete": True, "Cancel": False},
    ).show(parent_shell=sh)

    if ok:
        TASKS.remove(task)
        _state["current_task"] = None
        sh.update("detail", ["(select a task to see details)"])
        _rebuild_task_menu(sh)
        sh.update("status", ("success", "Task deleted."))
    else:
        sh.update("status", ("info", "Deletion cancelled."))


def _filter_tasks(sh):
    """Filter the visible task list by tag (multi-select CheckBox via ListSelect)."""
    global _filter_tags

    current = {t: (t in _filter_tags) for t in ALL_TAGS}
    result = ListSelect(
        title       = "Filter by tag",
        prompt_lines= ["Check tags to show  (empty = show all):"],
        items       = current,
        multi       = True,
    ).show(parent_shell=sh)

    if result is None:
        return

    _filter_tags = {t for t, v in result.items() if v}
    _rebuild_task_menu(sh)

    if _filter_tags:
        sh.update("status", ("info",
                             f"Filtered to: {', '.join(sorted(_filter_tags))}"))
    else:
        sh.update("status", ("info", "Showing all tasks."))


def _sort_tasks(sh):
    """Pick a sort order for the task list via ListSelect."""
    global _sort_key

    choice = ListSelect(
        title       = "Sort tasks by",
        prompt_lines= [f"Current sort: {_sort_key}"],
        items       = {
            "priority": "priority",
            "status":   "status",
            "due date": "due",
            "title":    "title",
        },
    ).show(parent_shell=sh)

    if choice is None:
        return

    _sort_key = choice
    _rebuild_task_menu(sh)
    sh.update("status", ("info", f"Sorted by {choice}."))



def _export_tasks(sh):
    """Pick an output file with FilePicker, then write tasks with a Progress bar."""
    path = FilePicker(
        title  = "Export tasks to…",
        filter = "*.txt",
    ).show(parent_shell=sh)

    if path is None:
        sh.update("status", ("info", "Export cancelled."))
        return

    if not path.endswith(".txt"):
        path += ".txt"

    lines = []
    for t in TASKS:
        lines.append(f"# {t['title']}")
        lines.append(f"  Priority : {t['priority']}")
        lines.append(f"  Status   : {t['status']}")
        lines.append(f"  Due      : {t['due'] or '—'}")
        lines.append(f"  Tags     : {', '.join(t['tags']) or '—'}")
        if t["notes"]:
            lines.append(f"  Notes    : {t['notes']}")
        lines.append("")

    with Progress(
        title      = "Exporting tasks…",
        total      = len(lines),
        cancellable= True,
    ).show(sh) as prog:
        written = []
        for i, line in enumerate(lines, 1):
            written.append(line)
            prog.set_progress(i, f"Writing line {i} of {len(lines)}")
            time.sleep(0.02)
            if prog.cancelled:
                sh.update("status", ("info", "Export cancelled."))
                return

    try:
        with open(path, "w") as f:
            f.write("\n".join(written))
        sh.update("status", ("success",
                             f"Exported {len(TASKS)} task(s) → {path}"))
    except OSError as exc:
        Alert(title="Export failed",
              message_lines=[str(exc)]).show(parent_shell=sh)


# ── Layout ────────────────────────────────────────────────────────────────────

LAYOUT = """
|=== <bold>Task Manager</> ===============================|
|{1R  $actions$                                           }|
|---------------------------------------------------------|
|{38% 14R $tasks$         }|{14R $detail$                 }|
|---------------------------------------------------------|
|{1R  $status$                                            }|
|=========================================================|
"""

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    sh = Shell(LAYOUT)

    # _quit is defined here so it can capture actions_menu by closure.
    # MenuHybrid.signal_return() checks _wants_exit after each callback
    # returns, so setting it inside the callback exits the shell cleanly.
    def _quit(sh):
        """Show a confirmation dialog; if confirmed, signal the shell to exit."""
        ok = Confirm(
            title         = "Quit",
            message_lines = ["Exit Task Manager?"],
            buttons       = {"Quit": True, "Cancel": False},
        ).show(parent_shell=sh)
        if ok:
            actions_menu._wants_exit = True
            actions_menu._exit_value = None

    actions_menu = MenuHybrid({
        "Add":    _add_task,
        "Edit":   _edit_task,
        "Delete": _delete_task,
        "Filter": _filter_tasks,
        "Sort":   _sort_tasks,
        "Export": _export_tasks,
        "Quit":   _quit,
    })
    sh.assign("actions", actions_menu)

    # Task list.
    _rebuild_task_menu(sh)

    # Detail panel.
    sh.assign("detail", ListView(["(select a task to see details)"]))

    # Status bar.
    sh.assign("status", StatusMessage())
    sh.update("status", ("info",
        "Tab / Shift-Tab to switch panels  ·  ↑↓ to navigate  ·  Enter to select"))

    sh.run()
    print("Task Manager closed.")


if __name__ == "__main__":
    main()
