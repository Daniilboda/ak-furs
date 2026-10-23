"""Разбор реплик менеджера и клиента (этап 4, шаг 2)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from chat_archive import read_chats

Role = Literal["Клиент", "Менеджер"]

_TURN = re.compile(
    r"^\[(?P<when>[^\]]+)\]\s*(?P<role>Клиент|Менеджер):\s*(?P<text>.*)$"
)


@dataclass(frozen=True)
class Turn:
    when: str
    role: Role
    text: str
    index: int  # порядок в чате, 0 — первая реплика после заголовка


def parse_chat_turns(chat_text: str) -> list[Turn]:
    """Разобрать текст чата на реплики. Первая строка — заголовок, пропускается."""
    lines = chat_text.splitlines()
    if not lines:
        return []
    turns: list[Turn] = []
    for line in lines[1:]:
        if not line.strip():
            continue
        match = _TURN.match(line)
        if match is None:
            raise ValueError(f"не удалось разобрать реплику: {line!r}")
        turns.append(
            Turn(
                when=match.group("when").strip(),
                role=match.group("role"),  # type: ignore[arg-type]
                text=match.group("text"),
                index=len(turns),
            )
        )
    return turns


def manager_turns(turns: list[Turn]) -> list[Turn]:
    """Только реплики менеджера (для поиска цены и приглашения)."""
    return [turn for turn in turns if turn.role == "Менеджер"]


def client_turns(turns: list[Turn]) -> list[Turn]:
    """Только реплики клиента."""
    return [turn for turn in turns if turn.role == "Клиент"]


def manager_texts(turns: list[Turn]) -> list[str]:
    """Тексты менеджера по порядку — суммы клиента сюда не попадают."""
    return [turn.text for turn in manager_turns(turns)]


def parse_all_chats(chats: dict[str, str]) -> dict[str, list[Turn]]:
    """Разобрать все чаты: ID → список реплик."""
    return {chat_id: parse_chat_turns(text) for chat_id, text in chats.items()}


def load_and_parse_chats(path: Path | str) -> dict[str, list[Turn]]:
    """Прочитать zip и разобрать реплики."""
    return parse_all_chats(read_chats(path))
