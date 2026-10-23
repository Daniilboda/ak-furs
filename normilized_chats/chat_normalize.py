"""Нормализация шапок чатов: клиент, заказ, менеджер — как в crm_cleanup."""

from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_CLIENT_CHATS = _ROOT / "client_chats"
_CRM = _ROOT / "crm_cleanup"
for _path in (_CLIENT_CHATS, _CRM):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from chat_archive import read_chats  # noqa: E402
from crm_dedupe import client_number, order_number  # noqa: E402
from crm_normalize import load_manager_aliases, normalize_manager  # noqa: E402

HEADER = re.compile(
    r"^Чат\s+(?P<chat_id>\S+)\s*\|\s*"
    r"клиент\s+(?P<client>.+?)\s*\|\s*"
    r"заказ\s+(?P<order>.+?)\s*\|\s*"
    r"менеджер\s+(?P<manager>.+?)\s*$",
    re.IGNORECASE,
)


def parse_chat_header(header_line: str) -> dict[str, str]:
    """Разобрать первую строку чата."""
    match = HEADER.match(header_line.strip())
    if match is None:
        raise ValueError(f"не удалось разобрать шапку чата: {header_line!r}")
    return match.groupdict()


def format_chat_header(chat_id: str, client: str, order: str, manager: str) -> str:
    """Каноническая шапка: клиент и заказ — числа без ведущих нулей."""
    return f"Чат {chat_id} | клиент {client} | заказ {order} | менеджер {manager}"


def normalize_chat_header_line(header_line: str, manager_aliases: dict[str, str]) -> str:
    """Клиент → число, заказ → число, менеджер → канон из справочника."""
    parts = parse_chat_header(header_line)
    client = str(client_number(parts["client"]))
    order = str(order_number(parts["order"]))
    manager = normalize_manager(parts["manager"], manager_aliases)
    return format_chat_header(parts["chat_id"], client, order, manager)


def normalize_chat_text(chat_text: str, manager_aliases: dict[str, str]) -> str:
    """Заменить только шапку; тело переписки не менять. Исходный текст не портить."""
    lines = chat_text.splitlines()
    if not lines:
        raise ValueError("пустой чат")
    new_header = normalize_chat_header_line(lines[0], manager_aliases)
    rest = lines[1:]
    body = "\n".join([new_header, *rest])
    if chat_text.endswith("\n"):
        body += "\n"
    return body


def read_chats_from_dir(path: Path | str) -> dict[str, str]:
    """Прочитать чаты из папки: либо chats/Cxxxx.txt, либо Cxxxx.txt в корне."""
    root = Path(path)
    nested = root / "chats"
    search_in = nested if nested.is_dir() else root
    result: dict[str, str] = {}
    for file_path in sorted(search_in.glob("C*.txt")):
        chat_id = file_path.stem
        if not re.fullmatch(r"C\d{4}", chat_id):
            continue
        result[chat_id] = file_path.read_text(encoding="utf-8-sig")
    if not result:
        raise ValueError(f"в {root} нет файлов Cxxxx.txt")
    return dict(sorted(result.items(), key=lambda item: int(item[0][1:])))


def normalize_chats(
    chats: dict[str, str],
    manager_aliases: dict[str, str],
) -> dict[str, str]:
    """Нормализовать шапки всех чатов."""
    return {
        chat_id: normalize_chat_text(text, manager_aliases)
        for chat_id, text in chats.items()
    }


def write_normalized_chats(chats: dict[str, str], out_dir: Path | str) -> Path:
    """Записать txt в out_dir/chats/Cxxxx.txt (как в архиве). Исходники не трогать."""
    base = Path(out_dir)
    chats_dir = base / "chats"
    chats_dir.mkdir(parents=True, exist_ok=True)
    for chat_id, text in chats.items():
        path = chats_dir / f"{chat_id}.txt"
        path.write_text(text, encoding="utf-8")
    return chats_dir


def normalize_from_zip(
    zip_path: Path | str,
    catalog_path: Path | str,
    out_dir: Path | str,
) -> dict[str, str]:
    aliases = load_manager_aliases(catalog_path)
    normalized = normalize_chats(read_chats(zip_path), aliases)
    write_normalized_chats(normalized, out_dir)
    return normalized


def normalize_from_dir(
    chats_dir: Path | str,
    catalog_path: Path | str,
    out_dir: Path | str,
) -> dict[str, str]:
    aliases = load_manager_aliases(catalog_path)
    normalized = normalize_chats(read_chats_from_dir(chats_dir), aliases)
    write_normalized_chats(normalized, out_dir)
    return normalized
