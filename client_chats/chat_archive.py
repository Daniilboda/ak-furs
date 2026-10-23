"""Чтение чатов из архива (этап 4, шаг 1)."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

CHAT_NAME = re.compile(r"^chats/(C\d{4})\.txt$")


def list_chat_ids(path: Path | str) -> list[str]:
    """ID чатов из zip, отсортированные по номеру (C0001, C0002, …)."""
    file_path = Path(path)
    ids: list[str] = []
    with zipfile.ZipFile(file_path) as archive:
        for name in archive.namelist():
            match = CHAT_NAME.match(name.replace("\\", "/"))
            if match is None:
                continue
            ids.append(match.group(1))
    return sorted(ids, key=lambda chat_id: int(chat_id[1:]))


def read_chat_text(archive: zipfile.ZipFile, chat_id: str) -> str:
    """Прочитать один чат как UTF-8 (BOM допускается)."""
    member = f"chats/{chat_id}.txt"
    try:
        raw = archive.read(member)
    except KeyError as error:
        raise ValueError(f"в архиве нет файла {member}") from error
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError(f"{member} не в кодировке UTF-8") from error


def read_chats(path: Path | str) -> dict[str, str]:
    """Прочитать все txt-чаты из zip.

    Ключ — ID (C0001…), значение — полный текст файла.
    Исходный zip не изменяется.
    """
    file_path = Path(path)
    result: dict[str, str] = {}
    with zipfile.ZipFile(file_path) as archive:
        for chat_id in list_chat_ids(file_path):
            result[chat_id] = read_chat_text(archive, chat_id)
    return result
