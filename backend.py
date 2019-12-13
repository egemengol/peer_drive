import socket
from threading import Thread
from typing import Tuple, NewType
import time
from pathlib import Path
import sys

Address = NewType("Address", Tuple[str, int])




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
                    #print("Received part:", part)
                    if not part:
                        break
                    parts.append(part)
                data = b"".join(parts)
                #print("Received:", data)
                self.f_tcp_recv(data)


class Backend:
    def __init__(self, listen_addr: Address):
        self.listener = ListenerTCP(listen_addr,self._f_tcp_recv)
        self.listener.start()
    
    def _f_tcp_recv(self, data: bytes):
        try:
            with open("recv", "wb") as f:
                f.write(data)
            #print(f"Wrote data: {data[:20].decode('ascii','replace')}...")
        except Exception as e:
            print('Failed to write data', file=sys.stderr)
    
    def _send_tcp(self, data: bytes, address: Address):
        TIMEOUT = 2
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)  # seconds
            try:
                s.connect(address)
            except Exception as e:
                print(e, file=sys.stderr)
            else:
                try:
                    s.sendall(data)
                except Exception as e:
                    print(e, file=sys.stderr)
    
    def _send_file(self, path, address: Address):
        with open(path, "rb") as f:
            filedata = f.read()
            #print("Read file", filedata)
            self._send_tcp(filedata, address)

if __name__=="__main__":
    addr = Address(("127.0.0.1",8888))
    b = Backend(addr)
    time.sleep(0.3)
    b._send_file(Path("./send"), addr)
    time.sleep(0.3)
