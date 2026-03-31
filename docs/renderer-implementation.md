# Renderer Implementation: panelmark-tui

This document describes how `panelmark-tui` satisfies the `panelmark` renderer
specification.

For the normative specification, see the renderer-spec docs in the `panelmark` core repo:

- [overview.md](../panelmark/docs/renderer-spec/overview.md) — spec structure and rationale
- [contract.md](../panelmark/docs/renderer-spec/contract.md) — required renderer behavior
- [extensions.md](../panelmark/docs/renderer-spec/extensions.md) — compatibility labels and extension policy
- [portable-library.md](../panelmark/docs/renderer-spec/portable-library.md) — optional portable widget layer
- [readiness.md](../panelmark/docs/renderer-spec/readiness.md) — readiness checklist

`panelmark-tui` claims **`portable-library-compatible`** status.  It implements all
required interactions and widgets defined in the portable standard library.  It also
provides the frequently-implemented interactions and widgets listed in that spec.  All
renderer-specific additions beyond the portable contract are documented as such.


## Module Layout

```
panelmark_tui/
├── shell.py          Shell subclass — event loop, terminal setup/teardown, dirty/redraw
├── renderer.py       Draws structural chrome; calls render_region() per interaction
├── context.py        build_render_context() — constructs RenderContext from blessed term
├── executor.py       TUICommandExecutor — translates DrawCommand list to terminal output
├── style.py          render_styled() — applies <bold>/<red>/… tags via blessed
├── testing.py        MockTerminal, make_key — test utilities
├── interactions/     Concrete Interaction subclasses
└── widgets/          Renderer-side convenience widgets
```


## How Each Contract Requirement Is Met

### Shell Hosting

`shell.py` provides a `Shell` subclass with `run()` and `run_modal()` methods.  `run()`
initializes the `blessed` terminal, enters fullscreen mode, drives the event loop, and
tears down the terminal on exit.


### Region Rendering

`renderer.py` walks the `LayoutModel` tree to draw structural chrome (borders, headings,
dividers), then calls `render_region(region, interaction, focused)` for each named region.

`render_region` builds a `RenderContext` via `context.py`, calls
`interaction.render(context, focused)`, and passes the resulting command list to
`TUICommandExecutor`.


### Draw Command Execution

`executor.py` provides `TUICommandExecutor`, which translates each `DrawCommand` into
terminal escape sequences via `blessed`.  It maps region-relative coordinates to
screen-absolute coordinates.


### Input Dispatch

The event loop in `shell.py` reads key events from `blessed` and passes them to
`shell.handle_key(key)`.  On `('exit', value)`, the loop terminates and returns `value`.
On `('continue', None)`, it redraws dirty regions and waits for the next event.


### Focus Handling

`renderer.py` passes `focused=True` to `render_region` for the region whose name matches
the shell's current focus.


### Dirty / Redraw

`shell.py` tracks dirty region names in its own `_dirty` set.  After each `handle_key()`
call, the Shell subclass's `_redraw_dirty(renderer, term)` method iterates the dirty set,
re-renders each affected region, and then clears the set.  This satisfies the spec's
requirement that dirty regions are redrawn and tracking state is reset after redraw.


### Shell Return Semantics

The event loop returns the value from `('exit', value)` to the caller of `run()`.
Interaction `signal_return()` behavior is routed through the shell's key dispatch and
results in an exit signal when the interaction signals accept.


## Shell API Surface

These are the `panelmark.Shell` attributes that `panelmark-tui` accesses directly.
All other interaction goes through the public API.

| Attribute | Type | Purpose |
|-----------|------|---------|
| `shell.regions` | `dict[str, Region]` | Populated after `Shell.__init__` |
| `shell.interactions` | `dict[str, Interaction]` | Populated by `assign()` |
| `shell.focus` | `str \| None` | Name of the currently focused region |
| `shell._dirty` | `set[str]` | Region names needing re-render |
| `shell.handle_key(key)` | method | Returns `('exit', value)` or `('continue', None)` |
| `shell.layout` | `LayoutModel` | The parsed layout tree |


## Testing Utilities

`testing.py` provides:

- `MockTerminal` — a fake terminal surface that records output without requiring a real TTY
- `make_key` — constructs fake key objects for use in interaction and shell tests

These allow tests to run without a real terminal.


## Renderer-Specific Additions

The following are `panelmark-tui`-specific and are not part of the portable core contract.

### Built-in interactions

The following interactions satisfy the **portable standard library** semantic contract
defined in `panelmark/docs/renderer-spec/portable-library.md`.  They are TUI-specific
class implementations, but their `get_value()` / `set_value()` / `signal_return()`
semantics are portable across renderers that implement the same spec:

- `MenuReturn` — single-select scrollable list that returns a mapped value
- `NestedMenu` — hierarchical action menu with `Leaf` sentinel
- `RadioList` — single-select list with radio-button visuals
- `CheckBox` — checkbox list (multi and single-select modes)
- `TextBox` — multi-line text editor with word-wrap and submit-mode options
- `FormInput` — structured data-entry form with typed fields and validation
- `DataclassFormInteraction` — dataclass-introspecting form interaction
- `StatusMessage` — display-only inline status/feedback region

The following interactions are TUI-specific additions with no portable equivalent:

- `MenuFunction` — scrollable menu that invokes callbacks without exiting the shell
- `ListView` — display-only scrollable list
- `TreeView` — interactive collapsible tree
- `TableView` — multi-column display table with sticky header
- `Function` — escape-hatch for fully custom rendering and key handling

All interactions implement the `panelmark.Interaction` ABC and are implemented against
the blessed TUI surface.


### Built-in widgets

The following widgets satisfy the **portable standard library** semantic contract:

- `Alert`, `Confirm`, `InputPrompt`, `ListSelect`, `FilePicker`, `DataclassForm` — required
  portable modal widgets

The following widgets are TUI-specific additions with no portable equivalent:

- `DatePicker` — calendar date selection
- `Progress`, `Toast`, `Spinner` — renderer-managed utility overlays with their own
  render cycles

What makes a widget or interaction portable is semantic contract compatibility, not
renderer-neutral code.  A TUI-specific class implementation can still satisfy the portable
contract if its constructor, `get_value()`, `set_value()`, and `signal_return()` semantics
match the spec.


## Portability Boundaries

| Layer | Source of truth | Portable? |
|-------|----------------|-----------|
| Shell language (DSL syntax) | `panelmark` core | Yes |
| Shell state machine, focus, dirty tracking | `panelmark` core | Yes |
| Interaction ABC (`render`, `handle_key`, `get_value`, `set_value`, `signal_return`) | `panelmark` core | Yes |
| Draw command types (`WriteCmd`, `FillCmd`, `CursorCmd`, `RenderContext`) | `panelmark` core | Yes |
| Required portable interaction implementations | `panelmark-tui` | Yes — semantic contract matches portable spec |
| TUI-specific interaction implementations | `panelmark-tui` | No — TUI-specific |
| Required portable widget implementations | `panelmark-tui` | Yes — semantic contract matches portable spec |
| TUI-specific widget implementations | `panelmark-tui` | No — TUI-specific |
| Blessed terminal integration | `panelmark-tui` | No |
| `MockTerminal`, test utilities | `panelmark-tui` | No |

Application code that uses only the portable standard library API (interactions and widgets
listed as portable above) is portable across any renderer that claims
`portable-library-compatible` status.  Application code that uses TUI-specific interactions
or widgets is coupled to the TUI renderer.
