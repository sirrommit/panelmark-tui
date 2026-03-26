# Response to ISSUES.md and SUGGESTIONS.md

This document responds to every item in `ISSUES.md` and `SUGGESTIONS.md`.
Each item is marked **Agree**, **Agree in principle**, or **Disagree**, followed by explanation
and (where applicable) what action should be taken.

---

## Responding to ISSUES.md

### panelmark issues

---

#### Comment syntax is documented incorrectly

**Agree.**

The shell-language docs say `#` line comments are stripped.  The parser only strips
`/* ... */` block comments.  A shell definition written with `# comment` will not behave
as documented — the `#` and everything after it on that row will be treated as literal
box-drawing content.

Action: either add `#` line-comment stripping to the parser, or update the docs to document
only `/* ... */` syntax.  Given that `#` is the more natural choice for a DSL, adding it to
the parser is the better fix.

---

#### Blank-line height semantics are documented incorrectly

**Agree.**

The docs contain a direct contradiction: they first say blank lines are ignored, then say
additional blank lines inside a multi-row panel expand its height.  The parser skips blank
lines entirely, so the second statement is false.

This is a documentation error.  The correct behaviour is: blank lines are ignored.  The docs
should remove the second statement.  If implicit height-expansion via blank lines is ever
desired, that is a new feature, not a doc fix.

---

#### Fill-only vertical splits do not behave as documented

**Agree.**

The docs promise equal distribution when all panels in a split are fill-width.  The layout
resolver does not implement this; the left branch effectively takes all remaining space and
the right branch can collapse to near-zero.  This is a material difference between the
documented and the actual behaviour.

This is a genuine layout bug.  Fix the resolver to divide remaining width equally among all
fill-only branches.

---

#### Vertical split validation is stricter in the docs than in the code

**Agree in principle.**

The docs say the structural divider must appear in the same structural position on every
content row.  The parser only checks that the first outer divider character is the same type
(`|` or `#`) across rows — it does not verify positional consistency.

However, calling this a "documentation error" undersells the situation.  The docs describe
a valid design contract; the parser just under-enforces it.  The right fix is to add a
validation pass that checks structural position consistency, not to weaken the docs to match
the parser's leniency.

---

#### Panel headings are documented as renderer-visible, but the shipped renderer ignores them

**Agree.**

`Panel.heading` is parsed and stored in the core model.  `panelmark-tui` does not render it
anywhere.  Users following the docs have no way to display headings through the only real
renderer.

Decision needed: either render headings in `panelmark-tui` (as a panel title drawn in the
border row), or explicitly mark the feature as "parsed but not yet rendered" in both READMEs.
Given the DSL uses `__text__` syntax that was clearly designed to be visible, rendering it
is the right long-term path.

---

### panelmark-tui issues

---

#### The getting-started guide miscounts the example regions

**Agree.**

The getting-started guide says the sample layout creates four regions; the sample defines
three named regions (`$tasks$`, `$entry$`, `$status$`).  This is a straightforward
documentation error that should be fixed immediately — it is the first thing a new user
reads.

---

#### Menu navigation docs overstate the implemented key bindings

**Agree.**

The interactions docs promise Page Up, Page Down, Home, and End for `MenuReturn`.
`MenuReturn`, `MenuFunction`, and `MenuHybrid` only implement up/down, `j`/`k`, and Enter.
The missing keys are not obscure edge cases; they are explicitly listed in the docs and
expected by users of menus with long item lists.

Either implement the missing keys or remove them from the docs.  Implementing them is
preferable since they are trivially available in any scrollable list.

---

#### `MenuHybrid` is documented as tuple-based, but implemented as callable-or-value

**Agree.**

The docs show `MenuHybrid(items)` with `(callback, return_value)` tuples.  The implementation
treats each item value as either a callable (invoke it) or a non-callable (exit with it as
the return value).  Tuples are not unpacked; the documented example would return the tuple
intact instead of invoking the callback.

The implementation's callable-or-value model is actually reasonable and consistent, but the
docs must match it.  Fix the docs to reflect the real API: callable values are called on
selection, non-callable values cause the shell to exit with that value as the return.

---

#### `TextBox` Home/End behavior is documented incorrectly

**Agree.**

The docs say Home/End jump to line start/end.  The implementation moves to the start or end
of the entire text buffer.  For single-line `TextBox` usage these are equivalent, but for
multiline usage (`wrap='extend'`) they diverge.

Fix the docs to say "moves to the start/end of the text buffer."  If per-line Home/End is
desired, that is a feature request, not a documentation clarification.

---

#### `SubList` is documented as an expandable tree, but implemented as a static nested-list flattener

**Agree.**

This is the largest mismatch in the project.  The docs describe expandable/collapsible groups
with dict-based hierarchical input.  The implementation accepts nested lists (dicts are
accepted but the keys become labels and values are ignored beyond one level), flattens them
recursively, and has no expand/collapse state at all.

The current implementation is better described as `IndentedListView`.  Options:
1. Rename and re-document what it actually does.
2. Implement a real tree widget (the `TreeView` suggestion from SUGGESTIONS.md).

Option 1 is the immediate fix.  Option 2 is a future feature.

---

#### `CheckBox` docs omit real behavior and claim nonexistent behavior

**Agree.**

The docs omit `mode="single"` entirely, and describe Left/Right keys for setting
unchecked/checked that do not exist in the implementation.  Both errors should be fixed:
document `mode="single"`, remove the Left/Right key claims.

---

#### `InputPrompt` docs conflict with the implementation

**Agree.**

The central widgets guide says Enter in the entry box submits the prompt.  In fact, Enter
inserts a newline into the `TextBox(wrap='extend')` buffer; submission requires moving focus
to the button row.  The widget module docstring is correct.

Fix the central guide to match the module docstring and the actual UX: Tab to the button row,
then Enter to submit.

---

#### `FilePicker` docs describe a different widget than the one in the code

**Agree in principle.**

The ISSUES.md claim overstates the gap slightly.  Looking at the docs and code together: the
docs mention a "filename bar" and "Open/Cancel buttons," both of which exist in the
implementation (the `$filename$` region and the default `OK`/`Cancel` buttons).  The real
mismatches are: (a) the docs describe "expandable/collapsible tree behavior" when the
implementation navigates into directories on selection without any expand/collapse state;
(b) the docs omit the `$filter$` field and `$status$` bar that exist in the implementation.

Fix needed: update the docs to accurately describe what the FilePicker actually shows (path,
filter, tree panel, files panel, status bar, OK/Cancel), and clarify that selecting a directory
navigates into it rather than toggling a tree node.

---

#### Testing docs mention a widget `_terminal` override that does not exist

**Agree.**

The testing guide says most widgets accept a `_terminal` kwarg.  Widget `show()` methods
do not expose this; tests inject a terminal indirectly via `parent_shell.terminal`.  This
is the most likely documentation to mislead someone writing their first tests.

Fix: update the testing guide to show the correct pattern — create a mock terminal, assign
it to `parent_shell.terminal`, then call `widget.show(parent_shell=mock_shell)`.

---

### Cross-project issues

---

#### The examples are not all aligned with the current APIs

**Agree.**

The `hello.py` example passes `"quit"` (a non-callable string) as a `MenuFunction` item
value.  `MenuFunction._activate` unconditionally calls the selected value as
`callback(self._shell)`.  Selecting "Quit" will raise `TypeError: 'str' object is not
callable`.

This needs to be fixed in the example.  The correct pattern is to pass a callable that
either uses `MenuHybrid` (which handles non-callables as exit values by design) or sets
`_wants_exit = True` on the interaction directly.  Using `MenuHybrid` with `"quit"` as the
non-callable exit value is the cleanest fix that matches the documented API.

The comment in the example that says "plain value → shell.run() returns 'quit'" would then
also become accurate documentation for `MenuHybrid`'s behaviour.

---

#### The local test workflow is under-documented

**Agree.**

There is no repo-level instruction for running the full test suite from this multi-package
checkout.  The `panelmark-tui` tests require `PYTHONPATH` to include both package roots:

```
PYTHONPATH=/path/to/panelmark-tui:/path/to/panelmark pytest
```

This should be documented in a top-level `CONTRIBUTING.md` or `README.md` section in both
repos.  A `Makefile` target or shell script would make it even easier.

---

## Responding to SUGGESTIONS.md

### Product direction

---

#### Keep the current split: `panelmark` as core DSL, `panelmark-tui` as the first real renderer

**Agree.**

The split is clean.  The core has no terminal dependency; the renderer has all the
blessed-specific code.  This separation is the right foundation for future renderers and
should not be collapsed.

---

#### Tighten the message: renderer-agnostic UI shell DSL with one production renderer today

**Agree.**

"ASCII layouts for TUIs" undersells the architecture.  "Define your layout as a readable
ASCII shell; connect Python callbacks to regions; get a working terminal app" is both
accurate and more compelling.  The renderer-agnostic framing should be present but honest
about current state (one renderer shipped).

---

#### Ship around one crisp story first: terminal admin tools and internal dashboards

**Agree.**

This is the right wedge.  Internal dashboards and admin tools have a clear need for rapid
keyboard-navigable UIs without heavy frontend infrastructure.  Leading with this story avoids
the "why not just use Rich/Textual?" question by targeting a slightly different use case:
declarative layout-first tooling.

---

### Architecture

---

#### Make the contract between `panelmark` and renderers explicit

**Agree.**

The renderer interface is currently implicit — if you want to write a renderer, you have to
read the TUI renderer's source and infer the contract.  A short `RENDERER_CONTRACT.md`
documenting `Shell`, `DrawCommand`, `RenderContext`, what methods a renderer must call, and
what it receives in return would make the architecture credible before adding more renderers.

---

#### Decide whether `Panel.heading` is real or dead

**Agree.**

This is the same issue as ISSUES.md item 5.  The heading feature cannot stay in a "parsed
but not rendered, mentioned in docs" limbo.  Either render it (in the border row, as a
centred title) or deprecate and remove it from the language.  The current state actively
misleads users.

---

#### Fix fill-only `VSplit` resolution in `panelmark`

**Agree.**

Same as ISSUES.md item 3.  This is a real layout bug affecting any layout where two or more
fill-width panels share a row.

---

#### Add a shell-definition validation layer separate from parsing

**Agree in principle.**

A separate validator that catches inconsistent divider placement cleanly is architecturally
sound.  However, the execution order matters: fixing the existing layout bug (fill splits)
and doc/code mismatches should come first.  Adding a validator is a quality-of-life
improvement for shell authors and can be added incrementally.

---

#### Reduce implementation drift by giving interactions/widgets shared keymap helpers

**Agree.**

Several interactions hand-roll their own navigation logic independently.  A small shared
`_nav_keys` function or mixin that handles up/down/j/k/Page Up/Page Down/Home/End and maps
them to a delta would eliminate duplicated code and make the key bindings consistent across
all list-like interactions.

---

#### Add a small public "widget base" or modal helper API

**Agree in principle.**

Several widgets reimplement the same shell construction pattern (`Shell(layout)`, `assign`,
`run_modal`).  A `_ModalWidget` base class that handles the boilerplate — taking a layout
string, assigning interactions, and running modal with the right width — would cut the code
in each widget file significantly.  This should come after the doc/code alignment work, not
before.

---

### Shell language

---

#### Keep the shell language small

**Agree.**

The DSL's value is that it is readable and writable by inspection.  Every added semantic
makes the language harder to learn and the renderer contract harder to specify.  Resist
adding new keywords until a second renderer has been written and the contract is locked.

---

#### Clarify comment syntax and choose one form

**Agree.**

`#` is the natural choice for a line-oriented DSL.  If `/* ... */` is kept for block
comments, both forms should be documented.  If only `/* ... */` is supported, that should
be the only documented form.  The current mismatch (docs say `#`, code strips `/* */`) is
actively harmful.

---

#### Add explicit syntax or rules for equal fill columns

**Agree.**

If all-fill equal distribution is the intended behaviour (and it should be — it is what
users will expect), it needs to be in the language spec as a guaranteed rule, not an implied
side effect.  Once the resolver bug is fixed, document it explicitly.

---

#### Consider a lightweight include/section mechanism only after the current single-shell format is stable

**Agree.**

A multi-shell artifact format is useful but premature.  Stabilise the single-shell format
first.  An include mechanism is at least two milestones away.

---

#### Decide whether headings should be structural or purely decorative

**Agree.**

This is the same issue as ISSUES.md item 5 and SUGGESTIONS.md Architecture item 2.  Recommend
making them structural: parse the heading, pass it to the renderer, render it as a centred
title in the top border row of the panel.  This is the most natural reading of `__text__`
syntax and gives the feature actual utility.

---

### Interaction layer

---

#### Split the built-ins into clearer categories

**Agree.**

The current inventory (`MenuFunction`, `MenuReturn`, `MenuHybrid`, `TextBox`, `ListView`,
`SubList`, `CheckBox`, `FormInput`, `StatusMessage`) mixes selection widgets, text-entry
widgets, display widgets, and a multi-field form widget without obvious grouping.  Organising
the docs and the module layout into selection / text-entry / status-display / forms would
make the package easier to survey.

---

#### Replace or redesign `MenuHybrid`

**Agree in principle.**

The callable-or-value model is not inherently confusing — once you understand it, it is
quite compact.  But the docs do not explain it clearly, and the name `MenuHybrid` gives no
hint of the behaviour.

Recommended path: keep the implementation, rename or alias to something more self-describing
(e.g. `MenuMixed` or `Menu` if `MenuFunction` and `MenuReturn` were consolidated), and
document the callable-or-value contract explicitly.  Creating separate `MenuAction` and
`MenuReturn` classes is cleaner but is a breaking API change for a feature that is currently
working correctly.

---

#### Turn `SubList` into a real tree widget or rename it

**Agree.**

This is ISSUES.md item 9 again.  Renaming is the immediate fix.  A real `TreeView` widget
is a future feature.

---

#### Document `CheckBox(mode="single")` and consider renaming that mode to `RadioList`

**Agree.**

`mode="single"` behaves like a radio button group — only one item can be selected.  Calling
it `CheckBox(mode="single")` is confusing because checkboxes are conventionally multi-select.
A dedicated `RadioList` widget with a cleaner API would be better.  In the meantime, document
`mode="single"` clearly in the existing `CheckBox` docs.

---

#### Add standard paging keys to menus and checkbox lists

**Agree.**

Page Up / Page Down / Home / End are standard in any scrollable list.  They are already
promised in the docs.  Implement them.

---

### Additional widgets that should exist

---

#### `RadioList` or `ChoiceList`

**Agree.**

A dedicated single-select list widget is more intuitive than `CheckBox(mode="single")`.
This should replace or wrap the existing mode once the widget surface is cleaned up.

---

#### `TableView`

**Agree.**

Multi-column read-only data display is a common need for admin/dashboard tools.  The current
workaround (a `ListView` with manually padded strings) is fragile.  A proper `TableView`
with column definitions and aligned rendering would be a high-value addition.

---

#### `TreeView`

**Agree.**

`SubList` advertises tree behaviour but delivers a flat indented list.  A real `TreeView`
with expand/collapse state, dict-based input, and keyboard navigation is the right long-term
replacement.

---

#### `Tabs`

**Agree in principle.**

`Tabs` would allow switching between named content panes without rebuilding shells.  This is
useful but requires the shell to support a "swap interaction in region" pattern cleanly.  It
is a larger design step than it appears and should be deferred until the simpler widgets are
solid.

---

#### `CommandPalette`

**Agree in principle.**

A fuzzy selector over a list of commands/items is useful for power users.  It could be built
on top of a filtered `MenuFunction` without deep changes to the core.  Low priority but a
good demo vehicle.

---

#### `Toast` or transient notification widget

**Agree.**

A non-modal brief notification that auto-dismisses is more user-friendly than `Alert` for
non-critical messages.  `StatusMessage` covers some of this use case but requires the shell
to have a status region.  A `Toast` overlay that appears at a fixed position and disappears
after a timeout would be more flexible.

---

#### `Spinner` or indeterminate progress widget

**Agree.**

The existing `Progress` widget requires a known total.  An indeterminate spinner for
operations with unknown duration is a separate need.  This is straightforward to implement
as a variant of `Progress`.

---

#### `TextAreaPrompt`

**Agree.**

Reusing `InputPrompt` for multiline text entry is awkward because `InputPrompt` uses a
`TextBox(wrap='extend')` internally but documents itself as a single-line widget.  A
dedicated `TextAreaPrompt` with explicit multiline semantics, proper height, and
submit-via-button UX would be cleaner.

---

#### `KeyValueForm` or `Wizard`

**Agree in principle.**

Multi-step data entry on top of `FormInput` is a real use case.  The current `FormInput`
handles single-step forms well.  A `Wizard` that chains multiple `FormInput` steps with
back/next navigation is a natural extension.  This is complex enough to warrant careful
design before implementation.

---

### Documentation

---

#### Make the docs match the code before adding more docs

**Agree.**

This is the single most important documentation priority.  A new user reading the current
docs will encounter multiple features that behave differently from what is described.  Every
doc-code mismatch erodes trust and costs debugging time.  No new documentation should be
added until the existing docs accurately reflect the implementation.

---

#### Put a short "What is real today" section at the top of both READMEs

**Agree.**

A brief "What works today / what is planned" section would set expectations correctly and
prevent users from spending time on features that do not yet exist (tree expansion, equal
fill splits, etc.).

---

#### Normalize the interaction docs against the actual key bindings and constructor signatures

**Agree.**

This is part of the doc-code alignment work.  Each interaction's doc page should list only
the keys that are actually handled in the implementation, and the constructor signatures
should be verified against the source.

---

#### Add a single "known limitations" page

**Agree.**

A `KNOWN_LIMITATIONS.md` or a section in the README that honestly lists current constraints
(no equal fill splits, no heading rendering, no tree expansion, no paging keys in menus)
is better than implying features work when they do not.

---

#### Add a repo-root contributor note for running tests

**Agree.**

Same as ISSUES.md cross-project item 2.  The `PYTHONPATH` requirement for tests in this
multi-package checkout must be documented prominently.

---

#### Keep examples executable; add CI checks

**Agree.**

Examples that import-crash or behave incorrectly are worse than no examples.  Every example
should be smoke-tested in CI (at minimum: import the module and run `main()` with a headless
terminal).  The `hello.py` bug (non-callable in `MenuFunction`) is a direct consequence of
having no automated example validation.

---

### Marketing

---

#### Stop leading with "zero dependency" alone

**Agree.**

Zero dependency is a nice property but not a reason to adopt.  The visual differentiator —
define layout as readable ASCII art — is what makes the project distinctive.  Lead with that.

---

#### Lead with the visual differentiator: "define UI layout as readable ASCII shells"

**Agree.**

This is the correct hook.  ASCII-defined layout is immediately understandable and memorable.
It is what makes `panelmark` different from every other Python TUI library.

---

#### Show side-by-side examples: shell definition, Python interaction wiring, terminal screenshot

**Agree.**

A three-panel "before and after" showing the shell string, the five lines of Python, and the
rendered terminal output would make the project's value proposition obvious in 30 seconds.

---

#### Publish one serious demo app

**Agree.**

The `task_manager.py` example is close to being the canonical showcase.  It exercises most
of the widget surface and is realistic enough to be convincing.  Fixing its rough edges and
promoting it prominently would be more valuable than writing ten small examples.

---

#### Be careful with ecosystem claims

**Agree.**

"Web and desktop renderers planned" is honest forward-looking communication.  "Render
anywhere" should not be used until at least two renderers exist and the renderer contract is
published.  Overpromising on future renderers risks the project's credibility.

---

#### Pick a stable package naming story early

**Agree.**

`panelmark-tui` is the right name if renderer-per-package is the model.  If a
`panelmark-html` or `panelmark-desktop` is coming, the naming convention is already
established.  Rename now rather than after users have pinned to the old name.

---

### Recommended execution order

**Agree with the order as written, with one addition.**

The proposed sequence:
1. Fix doc/code mismatches in the current README and docs.
2. Fix the core layout bug for fill-only vertical splits.
3. Audit examples and align them with current interaction behaviour.
4. Decide whether `SubList` becomes a true tree or gets renamed and re-documented.
5. Standardise navigation behaviour across menu-like interactions.
6. Add one or two high-value widgets: `TreeView` and `TableView`.
7. Only then start serious design work on `panelmark-html`.

Addition: step 3 should include fixing the `hello.py` `MenuFunction` non-callable bug
(change to `MenuHybrid`) and adding CI smoke-tests for all examples so the bug cannot
regress.

---

## Summary

**ISSUES.md:** All 15 items are confirmed correct.  Two deserve a nuance note:

- The FilePicker gap is slightly overstated (the docs do describe a filename bar and
  Open/Cancel buttons, both of which exist), but the description of expand/collapse tree
  behaviour is genuinely wrong.
- The divider validation gap is real, but the fix is to strengthen the parser's validation
  to match the docs, not to weaken the docs.

**SUGGESTIONS.md:** All major recommendations are sound.  A few are deferred or nuanced:

- `MenuHybrid` should be kept but better documented and potentially renamed, rather than
  replaced with `MenuAction`/`MenuReturn`.
- `Tabs` and `Wizard` are good long-term ideas but require design work before implementation.
- The recommended execution order is correct as written.

**Highest-priority actions (in order):**

1. Fix `hello.py` — replace `"Quit": "quit"` in `MenuFunction` with `MenuHybrid` or a
   callable wrapper.
2. Fix the fill-only VSplit layout bug in `panelmark`.
3. Fix the getting-started region count (4 → 3).
4. Update interaction docs to remove non-existent key bindings (paging in menus,
   Left/Right in CheckBox, Enter-submits in InputPrompt).
5. Rename or re-document `SubList`.
6. Fix the comment syntax mismatch (add `#` support or update docs to say `/* */` only).
7. Document the correct test workflow with `PYTHONPATH`.
