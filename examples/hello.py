"""hello.py — minimal panelmark-tui example.

A three-option menu that greets you, shows an about box, and quits.
Demonstrates how little code it takes to get a working TUI.

Run:
    python examples/hello.py
"""

from panelmark_tui import Shell
from panelmark_tui.interactions import MenuFunction, StatusMessage
from panelmark_tui.widgets import Alert

# ── Layout ────────────────────────────────────────────────────────────────────

LAYOUT = """
|=== <bold>Hello, panelmark-tui!</> ===|
|{3R  $menu$                           }|
|--------------------------------------|
|{1R  $status$                         }|
|======================================|
"""

# ── Callbacks ─────────────────────────────────────────────────────────────────

def say_hello(sh):
    Alert(title="Hello!", message_lines=["Hello, World!"]).show(parent_shell=sh)
    sh.update("status", ("success", "Said hello!"))


def show_about(sh):
    Alert(
        title="About",
        message_lines=[
            "panelmark-tui minimal example.",
            "",
            "Three menu items.  Five lines of layout.",
            "That's all it takes.",
        ],
        width=50,
    ).show(parent_shell=sh)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    sh = Shell(LAYOUT)

    # A non-callable value ("quit") causes MenuFunction to exit the shell.
    sh.assign("menu", MenuFunction({
        "Say Hello": say_hello,
        "About":     show_about,
        "Quit":      "quit",      # plain value → shell.run() returns "quit"
    }))

    sh.assign("status", StatusMessage())
    sh.update("status", ("info", "Use ↑ ↓ to navigate, Enter to select."))

    sh.run()
    print("Goodbye!")


if __name__ == "__main__":
    main()
