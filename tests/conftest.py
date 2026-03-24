import io
import sys
import pytest
from panelmark_tui.testing import MockTerminal, make_key
from panelmark_tui import Shell


@pytest.fixture
def mock_term():
    """Provide a MockTerminal for testing."""
    return MockTerminal(width=80, height=24)


@pytest.fixture
def shell_factory(mock_term, monkeypatch):
    """Factory fixture that creates Shell instances with a MockTerminal."""
    # Redirect stdout to a buffer so renderer output is captured
    def _make_shell(definition: str):
        return Shell(definition, _terminal=mock_term)
    return _make_shell


@pytest.fixture
def capture_output(monkeypatch):
    """Capture stdout for renderer tests."""
    buf = io.StringIO()
    monkeypatch.setattr(sys, 'stdout', buf)
    return buf
