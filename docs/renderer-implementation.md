# Renderer Implementation: panelmark-tui

This document describes how `panelmark-tui` implements the `panelmark` renderer contract.

For the normative contract, see `docs/renderer-spec/` in the `panelmark` core repo,
starting with [overview.md](https://github.com/sirrommit/panelmark/blob/main/docs/renderer-spec/overview.md).

`panelmark-tui` claims **`core-compatible`** status.


## Module Layout

```
panelmark_tui/
├── shell.py          Shell subclass — event loop, terminal setup/teardown
├── renderer.py       Draws structural chrome; calls render_region() per interaction
├── context.py        build_render_context() — constructs RenderContext from blessed term
├── executor.py       TUICommandExecutor — translates DrawCommand list to terminal output
├── style.py          render_styled() — applies <bold>/<red>/… tags via blessed
├── testing.py        MockTerminal, make_key — test utilities
├── interactions/     Concrete Interaction subclasses
└── widgets/          Pre-built modal Shell instances
```


## How Each Contract Requirement Is Met

### Shell Hosting

`shell.py` provides a `Shell` subclass with a `run()` method.  `run()` initializes the
`blessed` terminal, enters fullscreen mode, runs the event loop, and tears down the
terminal on exit.


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
`shell.focus`.


### Dirty / Redraw

After each `handle_key()` call, `renderer.py` redraws any region in `shell.dirty_regions`
and calls `shell.mark_all_clean()`.


### Shell Return Semantics

The event loop returns the value from `('exit', value)` to the caller of `run()`.
Interaction `signal_return()` is routed through the shell's key dispatch and results in an
exit signal when the shell is configured to exit on return.


## Shell API Surface

These are the only `panelmark.Shell` attributes that `panelmark-tui` accesses directly.
All other interaction goes through the public API.

| Attribute | Type | Purpose |
|-----------|------|---------|
| `shell.regions` | `dict[str, Region]` | Populated after `Shell.__init__` |
| `shell.interactions` | `dict[str, Interaction]` | Populated by `assign()` |
| `shell.focus` | `str \| None` | Name of the currently focused region |
| `shell.dirty_regions` | `set[str]` | Region names needing re-render |
| `shell.mark_all_clean()` | method | Clears `dirty_regions` after redraw |
| `shell.handle_key(key)` | method | Returns `('exit', value)` or `('continue', None)` |
| `shell.layout` | `LayoutModel` | The parsed layout tree |


## Testing Utilities

`testing.py` provides:

- `MockTerminal` — a fake terminal surface that records output without requiring a real TTY
- `make_key` — constructs fake key objects for use in interaction and shell tests

These allow tests to run without a real terminal.


## Renderer-Specific Additions

The following are `panelmark-tui`-specific and are not part of the portable contract:

- `widgets/` — pre-built modal Shell instances (e.g. confirm dialogs, input prompts)
  specific to the TUI surface
- Any `interactions/` subclasses that use `blessed`-specific capabilities

These are documented within their respective modules and are not expected to be portable
to other renderers.
