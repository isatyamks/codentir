from dataclasses import dataclass


@dataclass
class AgentMessage:
    role: str
    content: str
