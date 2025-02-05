import pytest

from registry.tool import main


def test_tools():
    assert len(main.tools()) > 0


def test_tool():
    assert main.tool("test_tool_1")
    assert main.tool("test_tool_2")
