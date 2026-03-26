import sys
from panelmark.layout import (LayoutModel, Region, BorderRow, HSplit, VSplit,
                               Panel, _declared_width, _declared_height,
                               _num_vsplit_cols, _vsplit_left_width)
from .style import render_styled, styled_plain_text
from .executor import TUICommandExecutor
from .context import build_render_context

# ---------------------------------------------------------------------------
# Box-drawing character tables
# ---------------------------------------------------------------------------
_SS = dict(h='─', v='│', tl='┌', tr='┐', bl='└', br='┘',
           lt='├', rt='┤', tt='┬', bt='┴', cr='┼')
_DD = dict(h='═', v='║', tl='╔', tr='╗', bl='╚', br='╝',
           lt='╠', rt='╣', tt='╦', bt='╩', cr='╬')
_DS = dict(h='═', v='│', tl='╒', tr='╕', bl='╘', br='╛',
           lt='╞', rt='╡', tt='╤', bt='╧', cr='╪')
_SD = dict(h='─', v='║', tl='╓', tr='╖', bl='╙', br='╜',
           lt='╟', rt='╢', tt='╥', bt='╨', cr='╫')


def _box(h_style: str, v_style: str) -> dict:
    if h_style == 'double' and v_style == 'double':
        return _DD
    if h_style == 'single' and v_style == 'single':
        return _SS
    if h_style == 'double' and v_style == 'single':
        return _DS
    return _SD


def _border_end_char(h_style, v_above, v_below, side):
    v = v_above or v_below or 'single'
    tbl = _box(h_style, v)
    if v_above is None:
        return tbl['tl'] if side == 'l' else tbl['tr']
    if v_below is None:
        return tbl['bl'] if side == 'l' else tbl['br']
    return tbl['lt'] if side == 'l' else tbl['rt']


def _border_cross_char(h_style, v_above, v_below):
    v = v_above or v_below or 'single'
    tbl = _box(h_style, v)
    if v_above is None:
        return tbl['tt']
    if v_below is None:
        return tbl['bt']
    return tbl['cr']


def _bottom_face_dividers(node, col: int, width: int, pct_base) -> dict:
    if node is None or isinstance(node, Panel):
        return {}
    if isinstance(node, VSplit):
        if pct_base is None:
            pct_base = width - (_num_vsplit_cols(node) - 1)
        left_width = _vsplit_left_width(node, width, pct_base)
        div_col = col + left_width
        result = {div_col: node.divider}
        result.update(_bottom_face_dividers(node.left, col, left_width, pct_base))
        result.update(_bottom_face_dividers(
            node.right, col + left_width + 1, width - left_width - 1, pct_base))
        return result
    if isinstance(node, HSplit):
        child = node.bottom if node.bottom is not None else node.top
        return _bottom_face_dividers(child, col, width, None)
    return {}


def _top_face_dividers(node, col: int, width: int, pct_base) -> dict:
    if node is None or isinstance(node, Panel):
        return {}
    if isinstance(node, VSplit):
        if pct_base is None:
            pct_base = width - (_num_vsplit_cols(node) - 1)
        left_width = _vsplit_left_width(node, width, pct_base)
        div_col = col + left_width
        result = {div_col: node.divider}
        result.update(_top_face_dividers(node.left, col, left_width, pct_base))
        result.update(_top_face_dividers(
            node.right, col + left_width + 1, width - left_width - 1, pct_base))
        return result
    if isinstance(node, HSplit):
        child = node.top if node.top is not None else node.bottom
        return _top_face_dividers(child, col, width, None)
    return {}


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

class Renderer:
    def __init__(self, term):
        self._term = term

    def full_render(self, layout_model, regions, interactions,
                    focused_name, term_width, term_height,
                    offset_row: int = 0, offset_col: int = 0):
        term = self._term
        is_full_screen = (offset_row == 0 and offset_col == 0)

        if is_full_screen:
            print(term.clear, end='', flush=False)

        layout_height = (
            _declared_height(layout_model.root, term_height)
            if layout_model.root is not None else 0
        )
        blank_inner = ' ' * (term_width - 2)
        blank_full  = ' ' * term_width
        for r in range(term_height):
            abs_row = offset_row + r
            if r < layout_height:
                print(term.move(abs_row, offset_col) + '│' + blank_inner + '│',
                      end='', flush=False)
            elif is_full_screen:
                print(term.move(abs_row, offset_col) + blank_full, end='', flush=False)

        if layout_model.root is not None:
            self._render_structure(
                layout_model.root,
                row=offset_row, col=offset_col + 1,
                width=term_width - 2, height=term_height,
                pct_base=None,
                left_div='single',
                right_div='single',
                term_width=term_width,
            )

        for name, region in regions.items():
            interaction = interactions.get(name)
            focused = (name == focused_name)
            if interaction:
                self.render_region(region, interaction, focused)
            else:
                self._render_empty_region(region, focused)

        sys.stdout.flush()

    def _render_structure(self, node, row: int, col: int, width: int,
                          height: int, pct_base, left_div: str,
                          right_div: str, term_width: int) -> None:
        if node is None or isinstance(node, Panel):
            return

        if isinstance(node, VSplit):
            if pct_base is None:
                pct_base = width - (_num_vsplit_cols(node) - 1)
            left_width = _vsplit_left_width(node, width, pct_base)
            div_col = col + left_width
            div_char = '║' if node.divider == 'double' else '│'
            for r in range(height):
                print(self._term.move(row + r, div_col) + div_char,
                      end='', flush=False)
            self._render_structure(
                node.left, row, col, left_width, height,
                pct_base, left_div, node.divider, term_width)
            self._render_structure(
                node.right, row, col + left_width + 1,
                width - left_width - 1, height,
                pct_base, node.divider, right_div, term_width)
            return

        if isinstance(node, HSplit):
            top_height = (_declared_height(node.top, height)
                          if node.top is not None else 0)
            border_rows = 1 if node.border is not None else 0
            bottom_height = max(0, height - top_height - border_rows)

            if node.top is not None:
                self._render_structure(
                    node.top, row, col, width, top_height,
                    None, left_div, right_div, term_width)

            if node.border is not None:
                border_row = row + top_height
                start_col = col - 1
                end_col = col + width

                prev_dividers = {}
                if node.top is not None:
                    prev_dividers[start_col] = left_div
                    prev_dividers[end_col] = right_div
                    prev_dividers.update(
                        _bottom_face_dividers(node.top, col, width, None))

                next_dividers = {}
                if node.bottom is not None:
                    next_dividers[start_col] = left_div
                    next_dividers[end_col] = right_div
                    next_dividers.update(
                        _top_face_dividers(node.bottom, col, width, None))

                self.draw_border(
                    border_row, term_width, node.border.style,
                    node.border.title,
                    prev_dividers=prev_dividers,
                    next_dividers=next_dividers,
                    start_col=start_col, end_col=end_col,
                )

            if node.bottom is not None:
                self._render_structure(
                    node.bottom,
                    row + top_height + border_rows,
                    col, width, bottom_height,
                    None, left_div, right_div, term_width)

    def render_region(self, region: Region, interaction, focused: bool):
        content_region = self._content_region(region)
        context = build_render_context(content_region, self._term)
        commands = interaction.render(context, focused)
        executor = TUICommandExecutor(self._term)
        executor.execute(commands, content_region)

    def _render_empty_region(self, region: Region, focused: bool):
        term = self._term
        content_region = self._content_region(region)
        for row_offset in range(content_region.height):
            row = content_region.row + row_offset
            print(term.move(row, content_region.col) + ' ' * content_region.width,
                  end='', flush=False)

    def _content_region(self, region: Region) -> Region:
        """Return the region to use for content rendering.

        When the region has a heading, draw the heading border on the top row
        and return a Region that starts one row lower with height decremented by 1.
        """
        if not region.heading:
            return region
        self._render_panel_heading(region)
        return Region(
            name=region.name,
            row=region.row + 1,
            col=region.col,
            width=region.width,
            height=max(0, region.height - 1),
        )

    def _render_panel_heading(self, region: Region) -> None:
        """Draw a ├─── Heading ───┤ line at the top row of *region*."""
        start_col = region.col - 1
        end_col = region.col + region.width
        v_dividers = {start_col: 'single', end_col: 'single'}
        self.draw_border(
            row=region.row,
            term_width=None,
            style='single',
            title=region.heading,
            prev_dividers=v_dividers,
            next_dividers=v_dividers,
            start_col=start_col,
            end_col=end_col,
        )

    def draw_border(self, row: int, term_width, style: str, title=None,
                    prev_dividers: dict | None = None,
                    next_dividers: dict | None = None,
                    start_col: int | None = None,
                    end_col: int | None = None) -> None:
        term = self._term
        fill = '═' if style == 'double' else '─'
        prev = prev_dividers or {}
        nxt = next_dividers or {}

        if start_col is None:
            start_col = 0
        if end_col is None:
            end_col = (term_width - 1) if term_width is not None else start_col

        border_width = end_col - start_col + 1
        chars = [fill] * border_width

        v_up = prev.get(start_col)
        v_dn = nxt.get(start_col)
        chars[0] = _border_end_char(style, v_up, v_dn, 'l')

        v_up = prev.get(end_col)
        v_dn = nxt.get(end_col)
        chars[border_width - 1] = _border_end_char(style, v_up, v_dn, 'r')

        all_positions = set(prev.keys()) | set(nxt.keys())
        for pos in all_positions:
            if start_col < pos < end_col:
                v_up = prev.get(pos)
                v_dn = nxt.get(pos)
                chars[pos - start_col] = _border_cross_char(style, v_up, v_dn)

        line = ''.join(chars)
        print(term.move(row, start_col) + line, end='', flush=False)

        if title:
            plain_title = f' {styled_plain_text(title)} '
            title_len = len(plain_title)
            inner_width = end_col - start_col - 1
            if title_len <= inner_width:
                left_fill = (inner_width - title_len) // 2
                title_start = start_col + 1 + left_fill
                rendered = render_styled(f' {title} ', term)
                try:
                    reset = str(term.normal) if term.normal else ''
                except Exception:
                    reset = ''
                print(term.move(row, title_start) + rendered + reset,
                      end='', flush=False)
