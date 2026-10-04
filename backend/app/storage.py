import hashlib
from pathlib import Path

from .config import STORAGE_DIR


def calculate_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)

    return sha256.hexdigest()


def save_file(file_bytes: bytes, storage_key: str) -> Path:
    base_path = Path(STORAGE_DIR)
    file_path = base_path / storage_key

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(file_bytes)

    return file_path