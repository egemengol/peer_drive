from typing import NamedTuple, Optional, Set

from filehandler import FileHandler


class Agent(NamedTuple):
    name: bytes
    ip: str

    @property
    def name_padded(self) -> bytes:
        return self.name.ljust(10, b"\0")[:10]

    def __str__(self) -> str:
        return f"{self.name.decode('ascii', 'replace')} - {self.ip}"


class AgentHandler:
    # TODO implement pickle!
    pickle_path = FileHandler.pickle_path

    def __init__(self):
        self._agents: Set[Agent] = set()

    def none_if_proper(self, agent: Agent) -> Optional[Agent]:
        if agent in self._agents:
            return None

        for ag in self._agents:
            if ag.name == agent.name:
                # address has changed
                return ag
            elif ag.ip == agent.ip:
                # different user from same ip
                return ag
        # User not found, add
        self._agents.add(agent)
        return None

    def replace(self, old_agent: Agent, new_agent: Agent) -> None:
        self._agents.discard(old_agent)
        self._agents.add(new_agent)

