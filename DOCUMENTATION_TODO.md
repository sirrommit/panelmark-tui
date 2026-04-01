# Documentation TODO: panelmark-tui

All panelmark-docs links in this file use the base:
`https://github.com/sirrommit/panelmark-docs/blob/main/docs`

---

## README.md

### Fix interaction count inconsistency

- [x] On line 40, the "What it provides" table lists `12 built-in interactions`.
  The feature status table (lines 17–28) correctly lists 13. Change line 40 to:

  ```
  | 13 built-in interactions | `MenuFunction`, `MenuReturn`, `TextBox`, `ListView`, `CheckBox`, `Function`, `FormInput`, `DataclassFormInteraction`, `StatusMessage`, `TreeView`, `RadioList`, `TableView`, `NestedMenu` |
  ```

  (Add `NestedMenu` to the list — it is the 13th interaction present in the
  feature table but missing from the "What it provides" table.)

- [x] Also on line 40, update the label to clarify portable vs TUI-specific:
  change `12 built-in interactions` → `13 built-in interactions (8 portable, 5 TUI-specific)`

- [x] On line 41, update the widgets label:
  change `10 built-in widgets` → `10 built-in widgets (6 portable, 4 TUI-specific)`

### Replace portable interaction/widget reproduction with spec link

The README currently reproduces the full list of portable interactions and
widgets inline. Replace the inline portable lists with a single reference line
rather than a full enumeration. In the "What it provides" section, immediately
after the interactions and widgets rows, add:

```markdown
Portable interactions and widgets follow the
[portable library spec](https://github.com/sirrommit/panelmark-docs/blob/main/docs/renderer-spec/portable-library.md).
TUI-specific additions are documented in the links below.
```

- [x] Done — spec reference added after the table.

### Add explicit TUI-specific breakdowns

Immediately after the "What it provides" table, add two subsections listing only
the renderer-specific items (so a reader knows what they get beyond the portable
standard):

```markdown
### TUI-specific interactions (beyond portable standard)

| Interaction | Description |
|-------------|-------------|
| `MenuFunction` | Menu that calls a function on selection rather than returning |
| `Function` | Generic function-backed interaction |
| `ListView` | Scrollable read-only list |
| `TreeView` | Interactive collapsible tree; expand/collapse; full keyboard navigation |
| `TableView` | Multi-column display table; sticky header; scrollable |

### TUI-specific widgets (beyond portable standard)

| Widget | Description |
|--------|-------------|
| `DatePicker` | Date selection modal |
| `Progress` | Context-manager progress bar; renderer-managed update cycle |
| `Toast` | Transient overlay notification; auto-dismisses after timeout or keypress |
| `Spinner` | Indeterminate-progress popup; animated braille frames; cancellable |
```

- [x] Done — TUI-specific breakdowns added.

### Add portable-library-compatible status line

Immediately after the opening description paragraph, add:

```markdown
**Compatibility:** `portable-library-compatible` — implements all 8 required portable
interactions and all 6 required portable widgets as defined in the
[renderer spec](https://github.com/sirrommit/panelmark-docs/blob/main/docs/renderer-spec/overview.md).
```

- [x] Done — compatibility line added.

### Replace local Documentation table links with panelmark-docs links

The Documentation table (lines 139–145) links to local `docs/*.md` files which
duplicate content in panelmark-docs. Replace the entire Documentation section
with:

```markdown
## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/getting-started.md) | Step-by-step guide: building your first TUI with panelmark-tui |
| [Interactions](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/interactions.md) | All 13 built-in interactions with API reference and examples |
| [Widgets](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/widgets.md) | All 10 built-in widgets with full API reference |
| [Testing](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/limitations.md) | Testing interactions with `MockTerminal` and `make_key`; known limitations |
| [Renderer Implementation](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/renderer-implementation.md) | How panelmark-tui satisfies the renderer spec |
| [Portable Library Spec](https://github.com/sirrommit/panelmark-docs/blob/main/docs/renderer-spec/portable-library.md) | Normative spec for all 8 portable interactions and 6 portable widgets |
| [Shell Language](https://github.com/sirrommit/panelmark-docs/blob/main/docs/shell-language/overview.md) | ASCII-art layout syntax reference |
| [Draw Commands](https://github.com/sirrommit/panelmark-docs/blob/main/docs/renderer-spec/contract.md) | `DrawCommand` types, `RenderContext`, style dict |
| [Custom Interactions](https://github.com/sirrommit/panelmark-docs/blob/main/docs/shell-language/examples.md) | Implementing the `Interaction` ABC |
| [Renderer Spec](https://github.com/sirrommit/panelmark-docs/blob/main/docs/renderer-spec/overview.md) | Renderer compatibility contract; portable library; extension policy |
| [Contributing](CONTRIBUTING.md) | Test commands, PYTHONPATH setup, running examples, adding interactions/widgets |
```

Remove the old secondary "Also see the panelmark core docs..." table entirely
(lines 147–154) — the links above replace it.

- [x] Done — Documentation section replaced with panelmark-docs links; old secondary table removed.

---

## Local docs/ folder

The local `docs/` tree duplicates content now canonical in panelmark-docs.
Process each file:

- [x] `docs/getting-started.md` — confirmed panelmark-docs version is complete; local file deleted.

- [x] `docs/interactions.md` — confirmed panelmark-docs version covers all 13 interactions; local file deleted.

- [x] `docs/widgets.md` — confirmed panelmark-docs version covers all 10 widgets; local file deleted.

- [x] `docs/testing.md` — confirmed content covered by panelmark-docs limitations page; local file deleted.

- [x] `docs/renderer-implementation.md` — confirmed panelmark-docs version is complete; local file deleted.

- [x] After deleting the docs/ files, confirmed no remaining file links to any deleted path in README.md.
  Updated CONTRIBUTING.md and ISSUES.md to remove/replace remaining references.
  Run:
  `grep -rn "docs/getting-started\|docs/interactions\|docs/widgets\|docs/testing\|docs/renderer-implementation" . --include="*.md" -l`
  Remaining references are in internal planning files only (PORTABLE_TODO.md, DOCUMENTATION_TODO.md, TODO.md) — these are historical references in planning notes, not user-facing links.

### Other root-level planning files

The following root-level files are internal working notes not needed after the
documentation is updated:

- [x] `KNOWN_LIMITATIONS.md` — updated link on line 31 of README to point to the panelmark-docs URL.
  Added deprecation header to the file.

- [ ] `PORTABLE_TODO.md` — **BLOCKED**: file has open code-level items (FormInput semantic
  conformance, DataclassFormInteraction action semantics). These are implementation tasks,
  not docs items. Cannot transfer to panelmark-docs issues from this repo. Needs separate
  engineering pass. Do not delete until items are resolved or filed as GitHub issues.

- [ ] `PROPOSAL.md`, `RESPONSE.md` — **NEEDS VERIFICATION**: both files contain implementation
  checklists and action items. Cannot confirm all are complete without code inspection.
  Needs a separate pass to verify against current code before deletion.

---

## Validation

- [x] Grep for any remaining relative cross-repo links:
  `grep -n "\.\./panelmark\b" README.md`
  Result: empty. ✓

- [x] Grep for any remaining links to deleted local docs:
  `grep -n "docs/getting-started\|docs/interactions\|docs/widgets\|docs/testing\|docs/renderer-implementation" README.md`
  Result: empty. ✓

- [x] Confirm interaction count reads "13" (not "12") everywhere in README.md:
  `grep -n "built-in interaction" README.md`
  Result: both occurrences show 13. ✓

- [x] Confirm `NestedMenu` appears in the interactions list in the "What it provides" table. ✓

- [x] Run tests (doc-only change — no automated check exists for README content):
  `PYTHONPATH=... .venv/bin/pytest -q`
  Result: 591 passed. ✓

- [x] Review `git diff` — only `README.md`, `KNOWN_LIMITATIONS.md`, `CONTRIBUTING.md`,
  `ISSUES.md`, deleted `docs/*.md` files, and `DOCUMENTATION_TODO.md` changed.
  No Python source changes.

- [ ] Commit:
  ```
  docs: fix interaction count (12→13), replace local docs/ with panelmark-docs links
  ```

- [ ] Push to `origin main`.
