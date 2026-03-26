# TODO — panelmark / panelmark-tui

Phases are ordered by dependency and risk.  Complete each phase before starting the next.
Items marked ✅ are already done.

---

## Phase 0 — Already complete

- ✅ Draw-command API (`DrawCommand`, `RenderContext`, `WriteCmd`, `FillCmd`, `CursorCmd`)
- ✅ `_Scrollable` mixin split; `ListView` and `SubList` use it
- ✅ Tab / `KEY_TAB` focus fix in `panelmark/panelmark/shell.py`
- ✅ `examples/hello.py` and `examples/task_manager.py`
- ✅ `hello.py` quit bug fixed (`MenuFunction` → `MenuHybrid`)
- ✅ `RESPONSE.md` written (response to `ISSUES.md` and `SUGGESTIONS.md`)
- ✅ `#` line comments added to parser; `#` divider replaced by `||`

---

## Phase 1 — Doc / code alignment (no new features) ✅

- ✅ **getting-started.md**: fixed region count (four → three)
- ✅ **interactions.md**: removed Page Up/Down/Home/End from `MenuReturn` docs
- ✅ **interactions.md**: fixed `MenuHybrid` docs — callable-or-value model, removed tuple example
- ✅ **interactions.md**: fixed `TextBox` Home/End — "buffer start/end"
- ✅ **interactions.md**: fixed `CheckBox` — removed left/right key claim; added `mode="single"` docs
- ✅ **interactions.md**: fixed `SubList` — documented as static indented list, no expand/collapse
- ✅ **widgets.md**: fixed `InputPrompt` — Enter inserts newline; Tab then Enter to submit
- ✅ **widgets.md**: fixed `FilePicker` — accurate layout description; Enter navigates (no expand/collapse)
- ✅ **testing.md**: removed `_terminal` kwarg guidance; documented `parent_shell.terminal` pattern
- ✅ Both READMEs: added **"What is real today"** table
- ✅ Added **`KNOWN_LIMITATIONS.md`**

---

## Phase 2 — Core layout bug ✅

- ✅ **`panelmark/panelmark/layout.py`**: added `_is_all_fill()` helper; rewrote
      `_vsplit_left_width` to use equal column distribution for all-fill subtrees
- ✅ 12 new tests in `test_layout.py` (two-fill equal, three-fill equal, width-sweep
      differ-by-at-most-one, sum-to-available, `_is_all_fill` unit tests, regression
      for fixed+fill unchanged)
- ✅ Updated `shell-language.md` to guarantee equal distribution as a language-level rule
- ✅ Updated both READMEs and `KNOWN_LIMITATIONS.md`

---

## Phase 3 — Missing navigation keys

Goal: menus and lists behave as documented (after Phase 1 removes the false claims, Phase 3
adds the real behaviour).

- [ ] **`MenuReturn` / `MenuFunction` / `MenuHybrid`** (`interactions/menu.py`): add
      Page Up, Page Down, Home, End
- [ ] **`CheckBox`** (`interactions/checkbox.py`): add Page Up, Page Down, Home, End
- [ ] Extract shared keymap helper (`_scroll_delta(key)` or similar) so all list interactions
      use the same nav logic — see SUGGESTIONS.md "shared keymap helpers"
- [ ] Update interaction docs to document the now-real paging keys

---

## Phase 4 — `SubList` decision

Pick one:

**Option A — rename and re-document (smaller)**
- [ ] Rename `SubList` → `IndentedList` (or keep the name but update docs completely)
- [ ] Document it accurately: accepts nested lists, renders indented, no expand/collapse

**Option B — implement real `TreeView` (larger, replaces SubList story)**
- [ ] New `TreeView` interaction: dict-based input, expand/collapse state, keyboard toggle
- [ ] Deprecate `SubList` with a note pointing to `TreeView`
- [ ] Add tests for expand/collapse state and keyboard navigation

Phase 4 is self-contained; either option can proceed independently of Phase 5.

---

## Phase 5 — Panel headings

- [ ] Decide rendering: centred title in the top border row of the panel (recommended)
- [ ] Implement in `panelmark_tui/renderer.py` (or wherever border rendering lives)
- [ ] Add tests confirming the heading text appears in the rendered output
- [ ] Update `shell-language.md` and `KNOWN_LIMITATIONS.md` to reflect headings are now
      rendered

---

## Phase 6 — New widgets

Add in this order (each is independent):

- [ ] **`RadioList`**: single-select, cleaner API than `CheckBox(mode="single")`.
      `CheckBox(mode="single")` may stay as an alias or be deprecated.
- [ ] **`TableView`**: multi-column read-only display.  Column definitions, aligned
      rendering, scrollable.
- [ ] **`Toast`**: transient overlay notification, auto-dismiss after N seconds.
      Useful complement to `StatusMessage` when there is no status region.
- [ ] **`Spinner`**: indeterminate progress.  Variant of `Progress` without a known total.

Defer to a later phase:
- `TextAreaPrompt` — multiline input modal (needs design)
- `Tabs` — switch between panes (needs shell architecture design)
- `CommandPalette` — fuzzy command selector (nice-to-have, low priority)
- `KeyValueForm` / `Wizard` — multi-step forms (complex, design first)

---

## Phase 7 — Developer experience

- [ ] **`CONTRIBUTING.md`** at repo root: document `PYTHONPATH` requirement for tests,
      how to run `panelmark` tests alone vs both together, how to run examples
- [ ] **`Makefile`** (or `justfile`): `make test`, `make test-all`, `make run-hello`,
      `make run-task-manager`
- [ ] **CI smoke tests**: import each example and verify it does not crash at import time;
      run a short headless key sequence through `hello.py` to confirm it exits cleanly
- [ ] **`_ModalWidget` base class**: extract shared `Shell` construction + `run_modal` pattern
      from `Confirm`, `Alert`, `InputPrompt`, etc.

---

## Phase 8 — Renderer contract + future renderers

Only start this phase after Phase 2 (layout bug) is fixed and Phase 4 (SubList decision) is
resolved — those are the two things most likely to affect a renderer's contract.

- [ ] Write **`RENDERER_CONTRACT.md`**: what a renderer must call, what it receives, how
      dirty tracking works, how to drive `run()` and `run_modal()`
- [ ] Review `panelmark_tui` against the contract document; fix any deviation
- [ ] (Future) `panelmark-html` — only begin after the contract doc is published and at
      least one other person has read it

---

## Phase 9 — Marketing / README polish

Do last; there is no point polishing docs that may still change.

- [ ] Both READMEs: lead with visual differentiator ("define UI layout as readable ASCII
      shells"), not "zero dependency"
- [ ] Add side-by-side example to README: shell string | Python wiring | terminal screenshot
- [ ] Promote `task_manager.py` as the canonical showcase demo
- [ ] Review ecosystem claims — "renderers planned" is fine; "render anywhere" is not
- [ ] Confirm package naming (`panelmark` + `panelmark-tui` family) before any PyPI
      publishing

---

## Quick-reference: cross-cutting issues to keep in mind

| Issue | Where to fix | Phase |
|-------|-------------|-------|
| Fill-only VSplit collapses right column | `panelmark/layout.py` | 2 |
| Panel headings parsed but not rendered | `panelmark_tui/renderer.py` | 5 |
| `SubList` not a real tree | `interactions/list_view.py` + docs | 4 |
| Paging keys missing from menus | `interactions/menu.py` + checkbox | 3 |
| `MenuHybrid` docs wrong | `docs/interactions.md` | 1 |
| `FilePicker` docs wrong | `docs/widgets.md` | 1 |
| `_terminal` kwarg doesn't exist | `docs/testing.md` | 1 |
| No PYTHONPATH instructions | new `CONTRIBUTING.md` | 7 |
