"""Шаг 2 этапа 4: реплики менеджера и клиента."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chat_archive import read_chats
from chat_turns import (
    client_turns,
    load_and_parse_chats,
    manager_texts,
    manager_turns,
    parse_chat_turns,
)

DOCS_CHATS = Path(__file__).resolve().parents[2] / "docs" / "04_client_chats.zip"


SAMPLE = """\
Чат C9999 | клиент CL-1 | заказ A-1 | менеджер Тест
[01.01.2025 10:00] Клиент: Добрый день, это около 200 000 рублей?
[01.01.2025 10:05] Менеджер: Здравствуйте! Подскажите размер.
[01.01.2025 10:10] Клиент: 44
[01.01.2025 10:15] Менеджер: Хорошо, уточню.
"""


def test_parse_roles_and_order():
    turns = parse_chat_turns(SAMPLE)
    assert [t.role for t in turns] == ["Клиент", "Менеджер", "Клиент", "Менеджер"]
    assert turns[0].text.startswith("Добрый день")
    assert turns[0].index == 0
    assert turns[1].role == "Менеджер"


def test_client_amount_not_in_manager_texts():
    """Сумму клиента не считаем репликой менеджера (правило Q4)."""
    turns = parse_chat_turns(SAMPLE)
    mgr = manager_texts(turns)
    assert any("200 000" in t.text for t in client_turns(turns))
    assert all("200 000" not in text for text in mgr)
    assert len(manager_turns(turns)) == 2


def test_c0001_has_manager_price_line_and_client_without_it():
    chats = read_chats(DOCS_CHATS)
    turns = parse_chat_turns(chats["C0001"])
    assert manager_turns(turns)
    assert client_turns(turns)
    assert any("53 000" in text for text in manager_texts(turns))
    assert all("53 000" not in t.text for t in client_turns(turns))


def test_all_current_chats_parse():
    parsed = load_and_parse_chats(DOCS_CHATS)
    assert len(parsed) == 150
    for chat_id, turns in parsed.items():
        assert turns, chat_id
        assert all(t.role in {"Клиент", "Менеджер"} for t in turns)
