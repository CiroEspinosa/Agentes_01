import pytest

from registry.agent import main


def test_agents():
    assert len(main.agents()) > 0


def test_agent():
    assert main.agent("test_agent_1")
    assert main.agent("test_agent_2")


def test_swarms():
    assert len(main.swarms()) > 0


def test_swarm():
    assert main.swarm("test_swarm_1")
