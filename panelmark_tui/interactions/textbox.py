from typing import Literal
from panelmark.interactions.base import Interaction
from panelmark.draw import DrawCommand, RenderContext, WriteCmd, FillCmd, CursorCmd


class TextBox(Interaction):
    """A text input box with optional word-wrap modes.

    ``enter_mode`` controls what happens when the user presses Enter:

    - ``"newline"`` (default) — inserts a newline character.
    - ``"submit"`` — records a submit intent; ``signal_return()`` will then
      return ``(True, text)`` so the shell exits with the current text.
    - ``"ignore"`` — Enter is silently ignored.

    ``get_value()`` always returns the current text regardless of
    ``enter_mode``.  ``signal_return()`` only fires once per submit press
    and only when ``enter_mode="submit"``.
    """

    def __init__(
        self,
        initial: str = "",
        wrap: Literal["word", "anywhere", "extend"] = "word",
        readonly: bool = False,
        enter_mode: Literal["newline", "submit", "ignore"] = "newline",
    ):
        self._text = initial
        self._wrap = wrap
        self._readonly = readonly
        self._enter_mode = enter_mode
        self._submitted = False
        self._cursor_pos = len(initial)  # position in text
        self._scroll_offset = 0  # row scroll offset

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        lines = self._get_display_lines(context.width)

        # Adjust scroll to show cursor
        if focused:
            cursor_line = self._get_cursor_line(context.width)
            if cursor_line < self._scroll_offset:
                self._scroll_offset = cursor_line
            elif cursor_line >= self._scroll_offset + context.height:
                self._scroll_offset = cursor_line - context.height + 1

        visible_lines = lines[self._scroll_offset:self._scroll_offset + context.height]

        cmds: list[DrawCommand] = []
        for i in range(context.height):
            if i < len(visible_lines):
                text = visible_lines[i][:context.width].ljust(context.width)
            else:
                text = ' ' * context.width
            cmds.append(WriteCmd(row=i, col=0, text=text))

        # Draw cursor if focused
        if focused and not self._readonly:
            cursor_line = self._get_cursor_line(context.width)
            cursor_col_in_line = self._get_cursor_col_in_line(context.width)
            visible_cursor_row = cursor_line - self._scroll_offset
            if 0 <= visible_cursor_row < context.height:
                col = min(cursor_col_in_line, context.width - 1)
                lines_at_cursor = lines[cursor_line] if cursor_line < len(lines) else ''
                char_at = lines_at_cursor[cursor_col_in_line:cursor_col_in_line + 1] or ' '
                cmds.append(WriteCmd(
                    row=visible_cursor_row, col=col,
                    text=char_at, style={'reverse': True},
                ))
                cmds.append(CursorCmd(row=visible_cursor_row, col=col))

        return cmds

    def _get_display_lines(self, width: int) -> list:
        """Split text into display lines based on wrap mode."""
        if self._wrap == 'extend':
            return self._text.split('\n') if self._text else ['']

        if not self._text:
            return ['']

        result = []
        for paragraph in self._text.split('\n'):
            if not paragraph:
                result.append('')
                continue
            if self._wrap == 'anywhere':
                while len(paragraph) > width:
                    result.append(paragraph[:width])
                    paragraph = paragraph[width:]
                result.append(paragraph)
            else:  # word wrap
                words = paragraph.split(' ')
                current_line = ''
                for word in words:
                    if not current_line:
                        current_line = word
                    elif len(current_line) + 1 + len(word) <= width:
                        current_line += ' ' + word
                    else:
                        result.append(current_line)
                        current_line = word
                result.append(current_line)

        return result if result else ['']

    def _get_cursor_line(self, width: int) -> int:
        """Get the display line number the cursor is on."""
        lines = self._get_display_lines(width)
        char_count = 0
        for i, line in enumerate(lines):
            line_len = len(line)
            if char_count + line_len >= self._cursor_pos:
                return i
            char_count += line_len + 1
        return max(0, len(lines) - 1)

    def _get_cursor_col_in_line(self, width: int) -> int:
        """Get the column within the display line where the cursor is."""
        lines = self._get_display_lines(width)
        char_count = 0
        for line in lines:
            line_len = len(line)
            if char_count + line_len >= self._cursor_pos:
                return self._cursor_pos - char_count
            char_count += line_len + 1
        return 0

    def handle_key(self, key) -> tuple:
        if self._readonly:
            return False, self.get_value()

        if key.startswith("KEY_"):
            name = key
            if name == 'KEY_BACKSPACE' or name == 'KEY_DELETE':
                if self._cursor_pos > 0:
                    self._text = self._text[:self._cursor_pos-1] + self._text[self._cursor_pos:]
                    self._cursor_pos -= 1
                    return True, self.get_value()
            elif name == 'KEY_DC':
                if self._cursor_pos < len(self._text):
                    self._text = self._text[:self._cursor_pos] + self._text[self._cursor_pos+1:]
                    return True, self.get_value()
            elif name == 'KEY_LEFT':
                if self._cursor_pos > 0:
                    self._cursor_pos -= 1
            elif name == 'KEY_RIGHT':
                if self._cursor_pos < len(self._text):
                    self._cursor_pos += 1
            elif name == 'KEY_HOME':
                self._cursor_pos = 0
            elif name == 'KEY_END':
                self._cursor_pos = len(self._text)
            elif name == 'KEY_ENTER':
                if self._enter_mode == 'newline':
                    self._text = self._text[:self._cursor_pos] + '\n' + self._text[self._cursor_pos:]
                    self._cursor_pos += 1
                    return True, self.get_value()
                elif self._enter_mode == 'submit':
                    self._submitted = True
                    return True, self.get_value()
                # 'ignore': fall through
        else:
            char = key
            if char in ('\n', '\r'):
                if self._enter_mode == 'newline':
                    self._text = self._text[:self._cursor_pos] + '\n' + self._text[self._cursor_pos:]
                    self._cursor_pos += 1
                    return True, self.get_value()
                elif self._enter_mode == 'submit':
                    self._submitted = True
                    return True, self.get_value()
                # 'ignore': fall through
            elif char and char.isprintable():
                self._text = self._text[:self._cursor_pos] + char + self._text[self._cursor_pos:]
                self._cursor_pos += 1
                return True, self.get_value()

        return False, self.get_value()

    def get_value(self) -> str:
        return self._text

    def set_value(self, value) -> None:
        self._text = str(value)
        self._cursor_pos = len(self._text)
        self._submitted = False

    def signal_return(self) -> tuple:
        """Return ``(True, text)`` after Enter is pressed in ``enter_mode="submit"``.

        Resets the submit flag after firing so a second call returns
        ``(False, None)`` until Enter is pressed again.
        """
        if self._submitted:
            self._submitted = False
            return True, self._text
        return False, None
