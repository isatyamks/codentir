"""
LLM provider contract — kept separate to avoid circular imports with contracts.py.
"""

from dataclasses import dataclass


@dataclass
class AgentMessage:
    role: str
    content: str


class llmProvider:
    """Base protocol for LLM providers. Subclass and implement generate()."""

    def generate(self, messages: list) -> "GroqResponse":
        raise NotImplementedError


@dataclass
class GroqResponse:
    content: str
