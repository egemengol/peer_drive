import json
from enum import Enum, auto
from pathlib import Path
from typing import NamedTuple, Optional, Set, List

import attr
import cattr


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


@attr.s(auto_attribs=True)
class BytesDataclass:
    def to_bjson(self) -> bytes:
        d = cattr.unstructure(self)
        s = json.dumps(d)
        return s.encode("ascii", "replace")

    @classmethod
    def from_bjson(cls, data: bytes):
        s = data.decode("ascii", "replace")
        d = json.loads(s)
        try:
            o = cattr.structure(d, cls)
            return o
        except:
            return None


@attr.s(auto_attribs=True, frozen=True)
class Command(BytesDataclass):
    agent: Agent
    filename: Optional[str]
    path: Optional[Path]

# TODO make this use dict, path as value.
# Use it to check in front_end.

class DownloadHandler:
    _pendings: Set[Command] = set()
    
    @classmethod
    def add_download(cls, command: Command) -> bool:
        if command in cls._pendings:
            return False
        cls._pendings.add(command)
        return True

    @classmethod
    def _find_path(cls, agent: Agent, filename: str) -> Optional[Path]:
        for comm in cls._pendings:
            if comm.agent == agent and comm.filename == filename:
                return comm.path
        return None

    @classmethod
    def resolve_download(cls, agent: Agent, filename: str) -> Optional[Path]:
        for comm in cls._pendings:
            if comm.agent == agent and comm.filename == filename:
                path = comm.path
                cls._pendings.discard(comm)
                return path
        return None

    @classmethod
    def is_pending(cls, agent: Agent, filename: str) -> bool:
        for comm in cls._pendings:
            if comm.agent == agent and comm.filename == filename:
                return True
        return False


class ErrorType(Enum):
    PARSE = auto()
    PUT = auto()
    OVERVIEW = auto()
    GET = auto()
    DOWNLOAD = auto()


@attr.s(auto_attribs=True)
class Fail(BytesDataclass):
    error: ErrorType
    filename: Optional[str]


@attr.s(auto_attribs=True)
class FileInfo(BytesDataclass):
    name: str
    length_KB: int


@attr.s(auto_attribs=True)
class Overview(BytesDataclass):
    space_KB_total: int
    space_KB_free: int
    files: List[FileInfo]

