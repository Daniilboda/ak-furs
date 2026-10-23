"""Шаг 3 этапа 4: первая цена менеджера (правила, без LLM)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chat_archive import read_chats
from chat_turns import parse_chat_turns
from manager_price import (
    first_manager_price_index,
    first_manager_price_turn,
    is_manager_price_utterance,
)

DOCS_CHATS = Path(__file__).resolve().parents[2] / "docs" / "04_client_chats.zip"


@pytest.mark.parametrize(
    "text",
    [
        "Цена с учётом всех работ: 53 000 ₽.",
        "Изначальная стоимость 2,404 млн.",
        "Стоимость этой модели — 138 тыс..",
        "Для вас итоговая — 2.094.000 руб, это лучшее, что могу сделать.",
        "Цена с учётом всех работ: сто пятьдесят восемь тысяч рублей.",
        "Для вас итоговая — два миллиона двести тысяч рублей, это лучшее, что могу сделать.",
    ],
)
def test_price_utterances_detected(text: str):
    assert is_manager_price_utterance(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "Можем оплатить в 2-3 платежа.",
        "Возможна предоплата 30%, остальное при получении.",
        "Наш шоурум находится у метро Фрунзенская, работаем ежедневно с 10 до 21.",
        "Давайте я запишу вас на встречу в шоурум, там и подберём. Завтра в 15:00 удобно?",
        "Здравствуйте! Меня зовут Полина, рада помочь.",
    ],
)
def test_non_price_manager_lines_rejected(text: str):
    assert is_manager_price_utterance(text) is False


def test_client_amount_is_not_manager_price():
    text = """\
Чат C9999 | клиент CL-1 | заказ A-1 | менеджер Тест
[01.01.2025 10:00] Клиент: Это около 200 000 рублей?
[01.01.2025 10:05] Менеджер: Подскажите размер.
"""
    turns = parse_chat_turns(text)
    assert first_manager_price_turn(turns) is None


def test_first_price_is_earliest_manager_price_line():
    text = """\
Чат C9999 | клиент CL-1 | заказ A-1 | менеджер Тест
[01.01.2025 10:00] Менеджер: Здравствуйте!
[01.01.2025 10:05] Менеджер: Цена с учётом всех работ: 53 000 ₽.
[01.01.2025 10:10] Менеджер: Могу предложить специальную цену — 50 000 ₽.
"""
    turns = parse_chat_turns(text)
    first = first_manager_price_turn(turns)
    assert first is not None
    assert "53 000" in first.text
    assert first_manager_price_index(turns) == 1


def test_c0001_first_price_and_c0010_has_none():
    chats = read_chats(DOCS_CHATS)
    t1 = parse_chat_turns(chats["C0001"])
    first = first_manager_price_turn(t1)
    assert first is not None
    assert "53 000" in first.text
    assert first_manager_price_turn(parse_chat_turns(chats["C0010"])) is None


def test_almost_all_current_chats_have_manager_price():
    chats = read_chats(DOCS_CHATS)
    missing = [
        cid
        for cid, text in chats.items()
        if first_manager_price_turn(parse_chat_turns(text)) is None
    ]
    # C0010 обрывается до цены (Q5)
    assert missing == ["C0010"]
