from pathlib import Path
from typing import Optional, Any
import json


class FileHandler:
    # These are not instance methods, will use like FileHandler.file_get(b"bekir", b"odev.txt")
    # No "__init__"
    # class variables defined like:
    master_path = Path("~/.peerdrive")
    pickle_path = master_path / ".storage" / "agents.pkl"

    # can use mypy backend.py for static type checking. These types are for this purpose.

    @staticmethod
    def server_overview_of(user: bytes) -> Optional[bytes]:
        # JSON encoding, so every key must be a string
        overview = {
            "user": user,
        }
        return json.dumps(overview).encode("ascii", "replace")
        # return None

    @staticmethod
    def server_file_get(user: bytes, filename: bytes) -> Optional[bytes]:
        return b"This is the contents of file " + filename + b" of user " + user + b"."
        # return None

    @staticmethod
    def server_file_put(user: bytes, filename: bytes, data: bytes) -> bool:
        print(f"PUT file {filename.decode()} for user {user.decode()}, contents: {data[:30].decode()}")
        return True

    @staticmethod
    def server_file_delete(user: bytes, filename: bytes) -> bool:
        print(f"DELETE file {filename.decode()} for user {user.decode()}")
        return True

    @staticmethod
    def server_file_rename(user: bytes, filename_old: bytes, filename_new: bytes) -> bool:
        print(f"RENAME file {filename_old.decode()} into {filename_new.decode()} for user {user.decode()}")
        return True

    @staticmethod
    def server_storage_status() -> Any:
        # TODO no idea about the output. Your choice.
        pass

    @staticmethod
    def client_file_read(path: Path) -> bytes:
        return b"This is the insides of the file at " + bytes(path) + b"\n"

    @staticmethod
    def client_file_write(path: Path, data: bytes) -> bool:
        print(f"WROTE path {path} with data: ", data[:30])
        return True
