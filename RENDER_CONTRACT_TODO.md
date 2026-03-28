# Renderer Contract TODO

The `panelmark` core repo now contains a renderer specification in
`docs/renderer-spec/`, including a portable standard library definition in
`docs/renderer-spec/portable-library.md`.

`panelmark-tui` implements all required interactions and widgets named in that
spec, but its documentation has not been aligned with it yet.  This file
describes what needs to be done.

No implementation changes are required by any of these items.  All work is
documentation and self-declaration.

---

## 1. Add a dedicated section for `DataclassFormInteraction` in `docs/interactions.md`

`DataclassFormInteraction` currently appears only as a single row in the
interaction matrix.  The portable spec defines its constructor and API contract
based on what could be inferred from the `DataclassForm` widget wrapper.  That
inferred signature needs to be verified against the actual implementation and
documented properly.

The inferred constructor is:

```python
DataclassFormInteraction(
    dc_instance,
    actions: list | None = None,
    on_change: callable | None = None,
)
```

**What to do:**

- Verify this matches the actual `DataclassFormInteraction.__init__` signature.
- Add a dedicated section to `docs/interactions.md` (after `FormInput`) that
  documents:
  - the constructor and its parameters
  - what `actions` entries look like (`{"label": ..., "shortcut": ..., "action": ...}`)
  - what `on_change` receives
  - `get_value()` → current field-state dict
  - `set_value(mapping)` → replace field-state dict
  - `signal_return()` → `(True, action_result)` when an action fires
  - a usage example
  - a note pointing to `DataclassForm` for modal popup use

If the actual constructor differs from the inferred signature, update the
portable spec at `docs/renderer-spec/portable-library.md` in `panelmark` to
match.

---

## 2. Mark interactions and widgets as portable in their docs

`docs/interactions.md` and `docs/widgets.md` do not currently indicate which
interactions/widgets are part of the portable standard library contract.

**What to do:**

Add a note at the top of each relevant section in both docs.  A short inline
tag works well:

> **Portable:** This interaction is part of the `panelmark` portable standard
> library.  See `docs/renderer-spec/portable-library.md` in the core repo.

Apply it to these interactions: `MenuReturn`, `RadioList`, `CheckBox`,
`TextBox`, `FormInput`, `DataclassFormInteraction`, `StatusMessage`.

Apply it to these widgets: `Alert`, `Confirm`, `InputPrompt`, `ListSelect`,
`FilePicker`, `DataclassForm`.

For the frequently-implemented interactions and widgets (`MenuFunction`,
`ListView`, `TreeView`, `TableView`, `DatePicker`, `Progress`, `Spinner`,
`Toast`), use a lighter note:

> **Frequently implemented:** This interaction follows the `panelmark` portable
> standard library's recommended API for this type.

---

## 3. Upgrade the compatibility claim in `docs/renderer-implementation.md`

`docs/renderer-implementation.md` currently says:

> `panelmark-tui` claims **`core-compatible`** status.  It does not currently
> claim `portable-library-compatible` — its widget set covers similar ground
> but has not been formally aligned against the portable standard library
> contract.

Now that the portable spec exists and panelmark-tui implements all required
interactions and widgets, this claim should be upgraded — but only after items
1 and 2 above are done, because those are what constitute "formally aligned."

**What to do:**

After completing items 1 and 2, update the compatibility claim to:

> `panelmark-tui` claims **`portable-library-compatible`** status.  It
> implements all required interactions and widgets defined in the portable
> standard library.  It also provides the frequently-implemented interactions
> and widgets listed in that spec.  All renderer-specific additions beyond the
> portable contract are documented as such.

---

## Order of operations

1. Add `DataclassFormInteraction` section to `interactions.md` (and fix
   portable-library.md in panelmark if the constructor differs)
2. Add portable/frequently-implemented tags to `interactions.md` and
   `widgets.md`
3. Upgrade the compatibility claim in `renderer-implementation.md`
4. Commit and push
