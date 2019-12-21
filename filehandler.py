from pathlib import Path

from containers import *

path_storage: Path = Path("./.storage")
if not path_storage.is_dir():
    path_storage.mkdir()


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
    def server_file_get(user: bytes, filename: bytes) -> Optional[bytes]:
        return b"This is the contents of file " + filename + b" of user " + user + b"."
        # return None

    @staticmethod
    def server_file_put(user: bytes, filename: bytes, data: bytes) -> bool:
        path: Path = path_storage / user.decode("ascii", "replace")
        if not path.is_dir():
            path.mkdir()
        filepath: Path = path / filename.decode("ascii", "replace")
        with open(filepath, "wb") as f:
            f.write(data)
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
            with open(path, "rb") as f:
                return f.read()
        except:
            return None

    @staticmethod
    def client_file_write(path: Path, data: bytes) -> bool:
        print(f"WROTE path {path} with data: ", data[:30])
        return True
