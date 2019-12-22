import sys
from pathlib import Path

from containers import *

path_storage: Path = Path("./.storage")
if not path_storage.is_dir():
    path_storage.mkdir()

# TODO BIG! handle file open exceptions! None handled right now!


class FileHandler:
    # These are not instance methods, will use like FileHandler.file_get(b"bekir", b"odev.txt")
    # No "__init__"
    # class variables defined like:
    master_path = Path("~/.peerdrive")

    # can use mypy backend.py for static type checking. These types are for this purpose.

    @staticmethod
    def server_overview_of(user: bytes) -> Optional[Jsonable]:
        # JSON encoding, so every key must be a string
        # noinspection PyTypeChecker
        overview = Jsonable({
            "user": user.decode('ascii', 'replace'),
            "total_space_KB": 200000,
            "used_space_KB": 50000,
        })
        return overview
        # return None

    @staticmethod
    def server_file_get(user: str, filename: str) -> Optional[bytes]:
        path: Path = path_storage / user
        if not path.is_dir():
            print(f"NOT FOUND file {filename} for user {user}", file=sys.stderr)
            return None
        filepath = path / filename
        with filepath.open("rb") as f:
            data = f.read()
        print(f"SERVED file {filename} for user {user}, contents:")
        print(f"{data[:40].decode('ascii', 'replace')}")
        return data

    @staticmethod
    def server_file_put(user: str, filename: str, data: bytes) -> bool:
        path: Path = path_storage / user
        if not path.is_dir():
            path.mkdir()
        filepath: Path = path / filename
        with filepath.open("wb") as f:
            f.write(data)
        print(f"PUT file {filename} for user {user}, contents: {data[:30].decode()}")
        return True

    @staticmethod
    def server_file_delete(user: str, filename: str) -> bool:
        print(f"DELETE file {filename} for user {user}")
        return True

    @staticmethod
    def server_file_rename(user: str, filename_old: str, filename_new: str) -> bool:
        print(f"RENAME file {filename_old} into {filename_new} for user {user}")
        return True

    @staticmethod
    def server_storage_status() -> str:
        # TODO no idea about the output. Your choice.
        # JSON for now.
        status = {
            "total": "laksjd"
        }
        return json.dumps(status)

    @staticmethod
    def client_file_read(path: Path) -> Optional[bytes]:
        try:
            with path.open("rb") as f:
                return f.read()
        except:
            return None

    @staticmethod
    def client_file_write(path: Path, data: bytes) -> bool:
        print(f"WROTE path {path} with data: ", data[:30])
        return True
