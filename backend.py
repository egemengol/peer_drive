import socket
from threading import Thread
from typing import Optional, NamedTuple, Set
import sys


"""
Received port is TCP port which is not the listen port. To test on one machine, either
supply port in the header
create docker compose 
supplying port is easier.
"""


class Address(NamedTuple):
    ip: str
    port: int


class Agent(NamedTuple):
    name: bytes
    addr: Address

    @property
    def name_padded(self) -> bytes:
        return self.name.ljust(10, b"\0")[:10]

    def __str__(self) -> str:
        return f"{self.name.decode('ascii', 'replace')} - {self.addr.ip}"



class ListenerTCP(Thread):
    def __init__(self, address: Address, f_tcp_recv):
        super(ListenerTCP, self).__init__()
        self.daemon = True
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.bind(address)
            self.s.listen(5)
        except socket.error as e:
            print('Failed to create TCP socket', file=sys.stderr)
            print(e, file=sys.stderr)
            print(f"{address}", file=sys.stderr)
            sys.exit(1)
        self.f_tcp_recv = f_tcp_recv

    def run(self):
        while True:
            conn, addr = self.s.accept()
            with conn:
                parts = list()
                while True:
                    part = conn.recv(50)
                    if not part:
                        break
                    parts.append(part)
                data = b"".join(parts)
                addr = Address(ip=addr[0], port=addr[1])
                self.f_tcp_recv(data, addr)


class AgentHandler:
    def __init__(self):
        self._agents: Set[Agent] = set()

    def none_if_proper(self, agent: Agent) -> Optional[Agent]:
        if agent in self._agents:
            return None

        for ag in self._agents:
            if ag.name == agent.name:
                # address has changed
                return ag
            elif ag.addr.ip == agent.addr.ip:
                # different user from same ip
                return ag
        # User not found, add
        self._agents.add(agent)
        return None

    def replace(self, old_agent: Agent, new_agent: Agent) -> None:
        self._agents.discard(old_agent)
        self._agents.add(new_agent)


class Backend:
    def __init__(self, listen_addr: Address, username: bytes):
        self.listener = ListenerTCP(listen_addr, self._f_tcp_recv)
        self.listener.start()
        self.user_db = AgentHandler()
        self.username = username
        self.port_listen = listen_addr.port

    @property
    def _padded_name(self) -> bytes:
        return self.username.ljust(10, b"\0")[:10]

    @property
    def packet_header(self) -> bytes:
        return self._padded_name + self.port_listen.to_bytes(2, byteorder="big", signed=False)

    def _f_tcp_recv(self, data: bytes, addr: Address):
        """
        upload ex: bekir\0\0\0\0\0\x00\x00Ufilename.txt\0this is a file\n

        Bounded 10-byte \0 padded from right username at the beginning
        and big endian two bytes recv port number
        Then one char command type

        [S] Status    -
        [U] Upload    filename\0bytestring
        [D] Download  filename
        [R] Rename    oldfilename\0newfilename
        [X] Delete    filename
        [O] Overview  pickledDict
        [P] Payload   bytestring
        [F] Failure   failString\0pickledDict
        """
        if len(data) < 11:
            print(f"header is not whole {data.decode()}", file=sys.stderr)
            return

        user = data[:10].rstrip(b"\0")
        recv_port = int.from_bytes(data[10:12], byteorder="big", signed=False)
        agent = Agent(name=user, addr=Address(addr.ip, recv_port))
        agent_instead = self.user_db.none_if_proper(agent)
        if agent_instead is not None:
            # TODO handle error
            # call out_failure
            print(f"There is an agent like this: {agent_instead}", file=sys.stderr)
            return

        command = data[12]
        data = data[13:]
        if command == b'S':
            self._inc_status(agent)
            return
        else:
            tokens = data.split(b"\0", maxsplit=1)
            if command == b"U":
                pass
                
    def _inc_status(self, agent: Agent):
        """
        Creates overview for the user, sends it.
        """
        js = FileHandler.server_overview_of(agent.name)
        if js is None:
            return False
        data = b"O" + js
        return self._send_tcp(data, agent.addr)

    def out_status(self, agent: Agent) -> bool:
        # Sends STATUS command to agent.
        return self._send_tcp(b"S", agent.addr)
    
    def out_status_broadcast(self) -> None:
        # TODO DO BROADCAST OR MULTICAST
        # WHAT TO DO ON THE SAME MACHINE? MULTICAST WOULD WORK
        pass
    
    def _inc_upload(self, agent: Agent, filename: bytes, data: bytes) -> None:
        print(f"Incoming UPLOAD\nfilename: {filename.decode()}\ndata head: {data[:30].decode()}")
    
    def out_upload(self, agent: Agent, filename: bytes, data: bytes) -> bool:
        packet = self._padded_name + b"U" + filename + b"\0" + data
        return self._send_tcp(packet, agent.addr)

    def _send_tcp(self, data: bytes, address: Address) -> bool:
        socket_timeout = 2
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(socket_timeout)  # seconds
            try:
                s.connect(address)
            except Exception as e:
                print(e, file=sys.stderr)
                return False
            else:
                try:
                    s.sendall(self.packet_header + data)
                    return True
                except Exception as e:
                    print(e, file=sys.stderr)
                    return False


"""
    def _inc_download(self, user: bytes, filename: bytes):
        pass

    def _inc_rename(self, addr: Address, old_filename: bytes, new_filename: bytes):
        pass
    
    def _inc_delete(self, addr: Address, filename: bytes):
        pass

    def _inc_overview(self, addr: Address, pickled: bytes):
        pass
    
    def _inc_payload(self, addr: Address, data: bytes):
        pass

    def _inc_failure(self, addr: Address, fail_str: bytes, pickled: bytes):
        pass
"""

