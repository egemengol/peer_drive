from typing import NamedTuple, Optional, Set, Dict, Any, NewType
import json
from pprint import pformat

import dataclasses

Jsonable = NewType("Jsonable", Dict[str, Any])


class Address(NamedTuple):
    ip: str
    port: int


class Agent(NamedTuple):
    name: bytes
    ip: str

    @property
    def name_padded(self) -> bytes:
        return self.name.ljust(10, b"\0")[:10]

    def __str__(self) -> str:
        return f"{self.name.decode('ascii', 'replace')} - {self.ip}"


class AgentHandler:
    _agents: Set[Agent] = set()

    @classmethod
    def none_if_proper(cls, agent: Agent) -> Optional[Agent]:
        if agent in cls._agents:
            return None

        for ag in cls._agents:
            if ag.name == agent.name:
                # address has changed
                return ag
            elif ag.ip == agent.ip:
                # different user from same ip
                return ag
        # User not found, add
        cls._agents.add(agent)
        return None

    @classmethod
    def replace(cls, old_agent: Agent, new_agent: Agent) -> None:
        cls._agents.discard(old_agent)
        cls._agents.add(new_agent)

    @classmethod
    def get_agent(cls, name: bytes) -> Optional[Agent]:
        for ag in cls._agents:
            if ag.name == name:
                return ag
        return None


class FailJsonEnc(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
