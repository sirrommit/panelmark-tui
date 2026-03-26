# Suggestions and Next Steps

## Product direction

- Keep the current split. `panelmark` is a solid core DSL/state package, and `panelmark-tui` is the first real renderer.
- Tighten the message: this is not just “ASCII layouts for TUIs”; it is “a renderer-agnostic UI shell DSL with one production renderer today.”
- Ship around one crisp story first: “build terminal admin tools and internal dashboards quickly.” That is a clearer wedge than promising future web/desktop renderers too early.

## Architecture

- Make the contract between `panelmark` and renderers explicit. A small renderer interface document would help before adding `panelmark-html` or desktop backends.
- Decide whether `Panel.heading` is real or dead. Either render it in `panelmark-tui`, or remove/deprecate it from the documented language.
- Fix fill-only `VSplit` resolution in `panelmark`. Equal distribution for unconstrained columns should be deterministic and tested.
- Add a shell-definition validation layer separate from parsing. Right now the parser accepts some shapes the docs say are invalid; a validator could catch inconsistent divider placement cleanly.
- Reduce implementation drift inside `panelmark-tui` by giving interactions/widgets shared keymap helpers instead of each class hand-rolling its own navigation logic.
- Add a small public “widget base” or modal helper API. Several widgets reimplement the same shell construction pattern.

## Shell language

- Keep the shell language small. Resist adding too many semantics into the DSL before a second renderer exists.
- Clarify comment syntax and choose one form. `#` line comments are the most obvious for this kind of DSL; if you keep `/* ... */`, document only that.
- Add explicit syntax or rules for equal fill columns if that behavior is intended. It should be guaranteed, not implied.
- Consider a lightweight include/section mechanism only after the current single-shell format is stable. A multi-shell artifact format could be useful, but it is a larger design step than the current docs suggest.
- Decide whether headings should be structural or purely decorative. If structural, renderers need a standard treatment. If decorative, say so clearly.

## Interaction layer

- Split the built-ins into clearer categories: selection, text entry, status/display, forms, and escape hatches. The current inventory is useful but conceptually mixed.
- Replace or redesign `MenuHybrid`. The callable-or-value behavior is compact but ambiguous; a clearer API would be separate `MenuAction` and `MenuReturn`, or an explicit action object.
- Turn `SubList` into a real tree widget or rename it. The current behavior is closer to `IndentedListView`.
- Document `CheckBox(mode="single")` and consider renaming that mode to a dedicated `RadioList` widget if you want a cleaner public surface.
- Add standard paging keys to menus and checkbox lists if the docs keep promising them.

## Additional widgets that should exist

- `RadioList` or `ChoiceList`: single-select alternative to `CheckBox(mode="single")`.
- `TableView`: multi-column read-only data display.
- `TreeView`: actual expandable/collapsible hierarchy, which would replace the current `SubList` story.
- `Tabs`: switch between named panes without rebuilding shells.
- `CommandPalette`: quick fuzzy selector for commands/items.
- `Toast` or transient notification widget: less intrusive than modal alerts.
- `Spinner` or indeterminate progress widget: useful when total work is unknown.
- `TextAreaPrompt`: multiline text-entry modal instead of repurposing `InputPrompt`.
- `KeyValueForm` or `Wizard`: multi-step data entry on top of `FormInput`.

## Documentation

- Make the docs match the code before adding more docs. Right now the main problem is drift, not lack of material.
- Put a short “What is real today” section at the top of both READMEs.
- Normalize the interaction docs against the actual key bindings and constructor signatures.
- Add a single “known limitations” page. That is better than silently implying features like tree expansion, equal fill splits, or line-relative cursor movement.
- Add a repo-root contributor note for running tests in this multi-package checkout, including the required `PYTHONPATH`.
- Keep examples executable. Add CI checks that run every example or at least import them and smoke-test the main flows.

## Marketing

- Stop leading with “zero dependency” alone. That matters, but it is not the reason someone adopts the project.
- Lead with the visual differentiator: “define UI layout as readable ASCII shells.”
- Show side-by-side examples: shell definition, Python interaction wiring, and resulting terminal screenshot.
- Publish one serious demo app. The task manager is close; turn it into the canonical showcase.
- Be careful with ecosystem claims. “Web and desktop renderers planned” is fine. “Render anywhere” should be framed as direction, not current capability.
- Pick a stable package naming story early. `panelmark-tui` is fine if you optimize for developer discoverability; if you want a surface-based family later, rename now rather than later.

## Recommended execution order

1. Fix doc/code mismatches in the current README and docs.
2. Fix the core layout bug for fill-only vertical splits.
3. Audit examples and align them with current interaction behavior.
4. Decide whether `SubList` becomes a true tree or gets renamed and re-documented.
5. Standardize navigation behavior across menu-like interactions.
6. Add one or two high-value widgets: `TreeView` and `TableView`.
7. Only then start serious design work on `panelmark-html`.
