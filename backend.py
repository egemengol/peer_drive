import socket
from pathlib import Path
from threading import Thread
import sys
from typing import List

from filehandler import FileHandler
from containers import *


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
                    part = conn.recv(500)
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
        except socket.error as e:
            print('Failed to create UDP socket', file=sys.stderr)
            print(e, file=sys.stderr)
            print(f"{address}", file=sys.stderr)
            sys.exit(1)
        self.f_udp_recv = f_udp_recv

    def run(self):
        while True:
            data, addr = self.s.recvfrom(30)
            self.f_udp_recv(data, addr[0])


class Backend:
    PORT_TCP = 8888
    PORT_UDP = 9999

    def __init__(self, username: str, debug: bool):
        self.debug = debug
        self.listener_tcp = ListenerTCP(Address(self.get_ip(), self.PORT_TCP), self._f_tcp_recv)
        self.listener_tcp.start()
        self.listener_udp = ListenerUDP(Address('', self.PORT_UDP), self._f_tcp_recv)
        self.listener_udp.start()

        self.username = username.encode("ascii", "replace")[:10]
        self.out_status_broadcast()

        self.overviews_since_request: List[Jsonable] = list()

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
        return self.username.ljust(10, b"\0")

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
        [O] Overview  json
        [P] Payload   filename\0bytestring
        [F] Failure   bjson
        """
        if len(data) < 11:
            print(f"header is not whole {data.decode()}", file=sys.stderr)
            return

        user = data[:10].rstrip(b"\0")
        if user == self.username:
            return
        agent = Agent(name=user, ip=ip)
        agent_instead = AgentHandler.none_if_proper(agent)
        """
        if agent_instead is not None:
            # TODO handle error
            # call out_failure
            print(f"There is an agent like this: {agent_instead}", file=sys.stderr)
            return
        """
        command = data[10:11]
        payload = data[11:]
        if command == b'S':
            self._inc_status(agent)
            return
        else:
            tokens = payload.split(b"\0", maxsplit=1)
            if command == b"U":
                if len(tokens) != 2:
                    return
                self._inc_upload(agent, *tokens)
            elif command == b"F":
                if len(tokens) != 1:
                    return
                self._inc_failure(agent, tokens[0])
            elif command == b"O":
                if len(tokens) != 1:
                    return
                self._inc_overview(agent, tokens[0])
            elif command == b"D":
                if len(tokens) != 1:
                    return
                self._inc_download(agent, tokens[0])
            else:
                print("Unknown command:", data)

    def _inc_status(self, agent: Agent) -> bool:
        """
        Creates overview for the user, sends it.
        """
        d = FileHandler.server_overview_of(agent.name)
        if d is None:
            return False
        data = b"O" + json.dumps(d).encode("ascii", "replace")
        return self._send_tcp(data, agent.ip)

    def out_status(self, agent: Agent) -> bool:
        # Sends STATUS command to agent.
        self.overviews_since_request = list()
        return self._send_tcp(b"S", agent.ip)
    
    def out_status_broadcast(self) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('', 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            try:
                packet = self._padded_name + b"S"
                s.sendto(packet, ("<broadcast>", self.PORT_UDP))
                self.overviews_since_request = list()
                return True
            except:
                return False

    def _inc_upload(self, agent: Agent, filename: bytes, data: bytes) -> None:
        success = FileHandler.server_file_put(agent.name, filename, data)
        if not success:
            self.out_failure(agent, b"PUT_ERROR", None)

    def out_upload(self, agent: Agent, filepath: Path, filename: Optional[bytes] = None) -> bool:
        data = FileHandler.client_file_read(filepath)
        if data is None:
            return False
        if filename is None:
            filename = filepath.name.encode("ascii", "replace")
        packet = b"U" + filename + b"\0" + data
        return self._send_tcp(packet, agent.ip)

    def _inc_overview(self, agent: Agent, bjson: bytes) -> None:
        try:
            overview = Jsonable(json.loads(bjson.decode("ascii", "replace")))
            overview["from_user"] = agent.name
            self.overviews_since_request.append(Jsonable(overview))
        except:
            self.out_failure(agent, b"PARSE_ERROR", None)

    def out_overview(self, agent: Agent, overview: Jsonable) -> bool:
        return self._send_tcp(b"O" + json.dumps(overview).encode("ascii", "replace"), agent.ip)

    def get_overviews(self) -> List[Jsonable]:
        return self.overviews_since_request

    def _inc_failure(self, agent: Agent, bjson: bytes) -> None:
        try:
            fail_obj = json.loads(bjson.decode("ascii", "replace"))
            print(f"FAIL from {agent.name.decode('ascii', 'replace')}", file=sys.stderr)
            print(fail_obj, file=sys.stderr)
        except:
            return

    def out_failure(self, agent: Agent, fail_message: bytes, fail_dict: Optional[Jsonable]) -> bool:
        serialized = b""
        if fail_dict is not None:
            try:
                serialized = json.dumps(fail_dict).encode("ascii", "replace")
            except:
                pass
        return self._send_tcp(b"F"+fail_message+b"\0"+serialized, agent.ip)

    def _inc_download(self, agent: Agent, filename: bytes) -> None:
        data = FileHandler.server_file_get(agent.name, filename)
        if data is not None:
            self.out_payload(agent, filename, data)

    def out_download(self, agent: Agent, filename: bytes) -> bool:
        return self._send_tcp(b"D" + filename, agent.ip)

    def _inc_payload(self, agent: Agent, filename: bytes, payload: bytes) -> None:
        pass

    def out_payload(self, agent: Agent, filename: bytes, payload: bytes) -> bool:


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
                    packet = self._padded_name + data
                    s.sendall(packet)
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
