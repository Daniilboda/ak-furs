"""Шаг 5 этапа 4: отбор чатов, где приглашение раньше цены."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from q4_select import (
    chat_is_q4,
    q4_from_chat_text,
    q4_ids_from_annotations,
)

HEADER = "Чат C9999 | клиент CL-1 | заказ A-1 | менеджер Тест"


def _chat(*lines: str) -> str:
    body = "\n".join(lines)
    return f"{HEADER}\n{body}\n"


def test_invite_before_price_is_q4():
    text = _chat(
        "[01.01.2025 10:00] Менеджер: Лучше приезжайте к нам в ателье на примерку!",
        "[01.01.2025 10:05] Клиент: Хорошо, а сколько стоит?",
        "[01.01.2025 10:10] Менеджер: Стоимость этой модели — 208.000 руб.",
    )
    assert q4_from_chat_text(text) is True


def test_price_before_invite_is_not_q4():
    text = _chat(
        "[01.01.2025 10:00] Менеджер: Цена с учётом всех работ: 53 000 ₽.",
        "[01.01.2025 10:05] Менеджер: Приглашаю на примерку в ателье — когда вам удобно?",
    )
    assert q4_from_chat_text(text) is False


def test_no_price_is_not_q4():
    text = _chat(
        "[01.01.2025 10:00] Менеджер: Лучше приезжайте к нам в ателье на примерку!",
        "[01.01.2025 10:05] Клиент: А цена?",
        "[01.01.2025 10:10] Менеджер: Подскажите размер, уточню.",
    )
    assert q4_from_chat_text(text) is False


def test_no_invite_is_not_q4():
    text = _chat(
        "[01.01.2025 10:00] Менеджер: Стоимость этой модели — 107 000 ₽.",
        "[01.01.2025 10:05] Менеджер: Наш шоурум находится у метро Фрунзенская, работаем ежедневно.",
    )
    assert q4_from_chat_text(text) is False


def test_q4_ids_sorted_from_annotations():
    payload = {
        "chats": [
            {"chat_id": "C0010", "meeting_before_price": False},
            {"chat_id": "C0024", "meeting_before_price": True},
            {"chat_id": "C0003", "meeting_before_price": True},
            {"chat_id": "C0090", "meeting_before_price": True},
        ]
    }
    assert q4_ids_from_annotations(payload) == ["C0003", "C0024", "C0090"]
    assert chat_is_q4(payload["chats"][0]) is False
