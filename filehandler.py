import json
import sys
import os
import os.path
from pathlib import Path

from containers import *

path_storage: Path = Path("./storage")
if not path_storage.is_dir():
    path_storage.mkdir()

# TODO BIG! handle file open exceptions! None handled right now!
# TODO tests!


class FileHandler:
    # These are not instance methods, will use like FileHandler.file_get(b"bekir", b"odev.txt")
    # No "__init__"

    # can use mypy backend.py for static type checking. These types are for this purpose.

    @staticmethod
    def get_size(path: Path) -> int:
        """
        total_size = 0
        seen = {}
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    stat = os.stat(fp)
                except OSError:
                    continue
                try:
                    seen[stat.st_ino]
                except KeyError:
                    seen[stat.st_ino] = True
                else:
                    continue
                total_size += stat.st_size
        return total_size
        """
        return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file() )

    @staticmethod
    def server_overview_of(user: str) -> Overview:
        # JSON encoding, so every key must be a string
        # noinspection PyTypeChecker
        space_total = 200000
        space_free = space_total-FileHandler.get_size(path_storage) 
        all_files_user = []
        path: Path = path_storage / user
        for (dirpath, dirnames, filenames) in os.walk(path):
            for f in filenames:
                all_files_user.append(FileInfo(f, os.path.getsize(path / f)))
        
        overview = Overview(
            space_KB_total=space_total,
            space_KB_free=space_free,
            files=all_files_user
        )
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
        filepath: Path= path_storage / user / filename
        if os.path.isfile(filepath):
            os.remove(filepath)
            print(f"DELETE file {filename} for user {user}")
            return True
        else:
            return False

    @staticmethod
    def server_file_rename(user: str, filename_old: str, filename_new: str) -> bool:
        filepath1: Path = path_storage / user / filename_old
        filepath2: Path = path_storage / user / filename_old
        if os.path.isfile(filepath1):
            os.rename(r'{}'.format(filepath1),r'{}'.format(filepath2))
            print(f"RENAME file {filename_old} into {filename_new} for user {user}")
            return True
        else:
            return False

    @staticmethod
    def server_storage_status() -> str:
        users: List[Tuple[str, int]] = list()

        for user in path_storage.iterdir():
            if not user.is_dir():
                continue
            size = user.stat().st_size
            users.append((user.name, size))
        return "(User, used space):\n" + str(users)
        """
        space_total = FileHandler.get_size(path_storage)
        list_of_dirnames = []
        list_of_filenames = []
        for (dirpath, dirnames, filenames) in os.walk(path_storage):

            list_of_dirnames.append(Path(dirpath).name)
            for f in filenames:
                list_of_filenames.append(f)
        status = {
            "total size": str(space_total),
            "directories" : str(list_of_dirnames),
            "# of file" : str(len(list_of_filenames))
        }
        status = {

        }
        return str(status)
        """

    @staticmethod
    def client_file_read(path: Path) -> Optional[bytes]:
        try:
            with path.open("rb") as f:
                return f.read()
        except:
            return None

    @staticmethod
    def client_file_write(path: Path, data: bytes) -> bool:
        try:
            with path.open("wb") as f:
                f.write(data)
                return True
        except:
            return False
