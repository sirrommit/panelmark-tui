"""
TUI rendering for styled text — terminal escape sequence emission.

Parse-side functions (strip_comments, parse_styled, styled_plain_text,
styled_visual_len) live in panelmark.style (no terminal dependency).
This module adds the rendering layer that converts parsed style attrs
to blessed terminal escape sequences.
"""

from panelmark.style import parse_styled, styled_plain_text

# ── colour aliases ──────────────────────────────────────────────────────────

_COLOR_ALIASES: dict[str, str] = {
    'gray': 'bright_black',
    'grey': 'bright_black',
    'darkgray': 'bright_black',
    'darkgrey': 'bright_black',
    'lightgray': 'white',
    'lightgrey': 'white',
    'silver': 'white',
    'purple': 'magenta',
    'violet': 'magenta',
    'pink': 'bright_magenta',
    'orange': 'yellow',
    'lime': 'bright_green',
    'teal': 'cyan',
    'navy': 'blue',
    'maroon': 'red',
    'indigo': 'blue',
    'aqua': 'cyan',
    'olive': 'yellow',
    'fuchsia': 'bright_magenta',
}

# Attribute key groups
_FG_KEYS = frozenset({'color', 'fg', 'foreground', 'fg-color', 'fg_color',
                      'text-color', 'text_color'})
_BG_KEYS = frozenset({'bg', 'background', 'bg-color', 'bg_color', 'bgcolor',
                      'background-color', 'background_color'})

_STYLE_MAP = {
    'bold':           ('bold',),
    'dim':            ('dim',),
    'faint':          ('dim',),
    'italic':         ('italic',),
    'underline':      ('underline',),
    'ul':             ('underline',),
    'underlined':     ('underline',),
    'underline-text': ('underline',),
    'blink':          ('blink',),
    'flash':          ('blink',),
    'reverse':        ('reverse',),
    'invert':         ('reverse',),
    'reverse-video':  ('reverse',),
    'reverse_video':  ('reverse',),
    'standout':       ('standout',),
    'strike':         ('strikethru', 'strike', 'strikethrough'),
    'strikethrough':  ('strikethru', 'strike', 'strikethrough'),
    'strikeout':      ('strikethru', 'strike', 'strikethrough'),
    'line-through':   ('strikethru', 'strike', 'strikethrough'),
    'normal':         ('normal',),
    'reset':          ('normal',),
}


def _normalize_color(name: str) -> str:
    name = name.lower().replace('-', '_')
    if name in _COLOR_ALIASES:
        name = _COLOR_ALIASES[name]
    if name.startswith('bright') and not name.startswith('bright_'):
        name = 'bright_' + name[6:]
    return name


def _get_color_seq(value: str, bg: bool, term) -> str:
    try:
        n = int(value)
        fn = getattr(term, 'on_color' if bg else 'color', None)
        if callable(fn):
            seq = fn(n)
            return str(seq) if seq else ''
        return ''
    except (ValueError, TypeError):
        pass
    try:
        name = _normalize_color(value)
        attr = f'on_{name}' if bg else name
        seq = getattr(term, attr, None)
        return str(seq) if seq else ''
    except Exception:
        return ''


def _apply_attrs(attrs: dict, term) -> str:
    result = ''
    for key, val in attrs.items():
        try:
            if key in _FG_KEYS:
                result += _get_color_seq(str(val), bg=False, term=term)
            elif key in _BG_KEYS:
                result += _get_color_seq(str(val), bg=True, term=term)
            elif key in _STYLE_MAP:
                for prop in _STYLE_MAP[key]:
                    seq = getattr(term, prop, None)
                    if seq:
                        result += str(seq)
                        break
        except Exception:
            pass
    return result


def _truncate_segments(segments: list, max_len: int) -> list:
    result = []
    remaining = max_len
    for attrs, chunk in segments:
        if remaining <= 0:
            break
        if len(chunk) <= remaining:
            result.append((attrs, chunk))
            remaining -= len(chunk)
        else:
            result.append((attrs, chunk[:remaining]))
            remaining = 0
    return result


def render_styled(text: str, term, max_len: int = None) -> str:
    """
    Render *text* — which may contain style tags — using *term* escape sequences.

    *max_len*: if given, visible text is truncated to this many characters.
    """
    segments = parse_styled(text)
    if max_len is not None:
        segments = _truncate_segments(segments, max_len)

    result = ''
    for attrs, chunk in segments:
        if attrs:
            seq = _apply_attrs(attrs, term)
            if seq:
                try:
                    reset = str(term.normal) if term.normal else ''
                except Exception:
                    reset = ''
                result += seq + chunk + reset
            else:
                result += chunk
        else:
            result += chunk
    return result
