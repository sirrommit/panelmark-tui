# Current Issues and Drift

This file tracks known gaps between documentation, code, and contributor workflow.
Update it when issues are fixed or discovered.

---

## What is no longer an issue

These gaps are closed — implemented, tested, and documented:

- `#` line comments in `panelmark`
- Equal distribution for fill-only vertical splits
- Panel heading rendering in `panelmark-tui`
- Paging keys in menus and other list-style interactions
- `TreeView`
- `RadioList`
- `TableView`
- `Toast`
- `Spinner`
- The old `hello.py` `MenuFunction` example bug
- README stale counts (10 interactions / 7 widgets → 13 / 9)
- README menu navigation description missing Page Up/Down/Home/End
- interactions doc opening count (12 → 13)
- `KNOWN_LIMITATIONS.md` framing (reworked to list current non-obvious behaviours only)
- Missing contributor guide — added as `CONTRIBUTING.md`
- Missing renderer boundary doc — added as `panelmark/docs/renderer-boundary.md`

---

## Remaining issues

### Example code uses private shell internals

- `examples/task_manager.py` reaches into `sh._interactions` and stores ad hoc state
  on the shell object via `sh._current_task`.
- The example works but demonstrates private implementation details rather than the
  stable public API.
- **Effect:** the flagship demo may encourage maintenance-liability patterns.
- **Fix requires:** rewriting the example to use only public API — no doc change needed.

### Parser is permissive about split alignment

- The shell-language reference implies structural column dividers must be consistent
  across all content rows of a block.  The parser enforces this loosely — some
  irregular layouts are accepted silently.
- See `KNOWN_LIMITATIONS.md` for the user-facing note.
- **Fix requires:** code change to the parser — validation pass after parsing.

---

## Verification

- `panelmark` tests: `136 passed`
- `panelmark-tui` tests: `388 passed`
- Run commands: see [`CONTRIBUTING.md`](CONTRIBUTING.md)
