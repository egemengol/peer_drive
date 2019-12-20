import socket
from threading import Thread
from typing import Optional, NamedTuple, Set
import sys

from filehandler import FileHandler
from agent import Agent, AgentHandler


class Address(NamedTuple):
    ip: str
    port: int


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
                self.f_tcp_recv(data, addr[0])


class ListenerUDP(Thread):
    def __init__(self, address: Address, f_udp_recv):
        super(ListenerUDP, self).__init__()
        self.daemon = True
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.s.bind(address)
            self.s.setblocking(0)
        except socket.error as e:
            print('Failed to create UDP socket', file=sys.stderr)
            print(e, file=sys.stderr)
            print(f"{address}", file=sys.stderr)
            sys.exit(1)
        self.f_udp_recv = f_udp_recv

    def run(self):
        while True:
            conn, addr = self.s.accept()
            with conn:
                parts = list()
                while True:
                    part = conn.recv(11)
                    if not part:
                        break
                    parts.append(part)
                data = b"".join(parts)
                self.f_udp_recv(data, addr[0])


class Backend:
    PORT_TCP = 8888
    PORT_UDP = 9999

    def __init__(self, username: bytes):
        self.listener_tcp = ListenerTCP(Address(self.get_ip(), self.PORT_TCP), self._f_tcp_recv)
        self.listener_tcp.start()
        self.listener_udp = ListenerUDP(Address('', self.PORT_UDP), self._f_tcp_recv)

        self.user_db = AgentHandler()
        self.username = username

    @staticmethod
    def get_ip() -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            try:
                # doesn't even have to be reachable
                s.connect(('10.255.255.255', 1))
                ip = s.getsockname()[0]
            except:
                ip = '127.0.0.1'
        return ip

    @property
    def _padded_name(self) -> bytes:
        return self.username.ljust(10, b"\0")[:10]

    def _f_tcp_recv(self, data: bytes, ip: str):
        """
        upload ex: bekir\0\0\0\0\0\x00\x00Ufilename.txt\0this is a file\n

        Bounded 10-byte \0 padded from right username at the beginning
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
        agent = Agent(name=user, ip=ip)
        agent_instead = self.user_db.none_if_proper(agent)
        if agent_instead is not None:
            # TODO handle error
            # call out_failure
            print(f"There is an agent like this: {agent_instead}", file=sys.stderr)
            return

        command = data[10]
        data = data[11:]
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
        return self._send_tcp(data, agent.ip)

    def out_status(self, agent: Agent) -> bool:
        # Sends STATUS command to agent.
        return self._send_tcp(b"S", agent.ip)
    
    def out_status_broadcast(self) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('', 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            try:
                s.sendto(b"S", ("<broadcast>", self.PORT_UDP))
                return True
            except:
                return False

    def _inc_upload(self, agent: Agent, filename: bytes, data: bytes) -> None:
        print(f"Incoming UPLOAD\nfilename: {filename.decode()}\ndata head: {data[:30].decode()}")
    
    def out_upload(self, agent: Agent, filename: bytes, data: bytes) -> bool:
        packet = self._padded_name + b"U" + filename + b"\0" + data
        return self._send_tcp(packet, agent.ip)

    def _send_tcp(self, data: bytes, ip: str) -> bool:
        socket_timeout = 2
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(socket_timeout)  # seconds
            try:
                s.connect((ip, self.PORT_TCP))
            except Exception as e:
                print(e, file=sys.stderr)
                return False
            else:
                try:
                    s.sendall(self._padded_name + data)
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
