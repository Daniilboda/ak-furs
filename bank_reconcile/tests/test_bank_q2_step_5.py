"""Шаг 5 этапа 2: список Q2a."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "crm_cleanup"))

from bank_q2 import q2a_paid_orders_without_payment
from bank_statement import read_bank_statement
from run_crm_cleanup import run_cleanup

DOCS_BANK = Path(__file__).resolve().parents[2] / "docs" / "02_bank_statement_rub.csv"
DOCS_CRM = Path(__file__).resolve().parents[2] / "docs" / "01_crm_orders_export.csv"


def _crm_row(order: str, status: str) -> dict[str, str]:
    return {
        "Номер заказа": order,
        "№ строки": "1",
        "Дата создания": "01.01.2025",
        "Клиент": "1",
        "Менеджер": "Ольга Смирнова",
        "Источник": "Сайт",
        "Артикул": "X",
        "Кол-во": "1",
        "Цена за ед.": "100.00",
        "Валюта": "руб.",
        "Скидка": "",
        "Статус": status,
        "Комментарий": "",
        "Выгружено": "2026-01-01 10:00",
    }


def _bank_row(purpose: str) -> dict[str, str]:
    return {
        "Дата операции": "01.01.2025",
        "Время": "12:00",
        "Сумма": "100,00",
        "Валюта": "RUR",
        "Тип": "Поступление",
        "Контрагент": "Тест",
        "Назначение платежа": purpose,
    }


def test_paid_without_incoming_enters_q2a():
    crm = [_crm_row("10", "Оплачен"), _crm_row("20", "Оплачен")]
    bank = [_bank_row("A20 доплата")]
    assert q2a_paid_orders_without_payment(crm, bank) == [10]


def test_paid_with_incoming_not_in_q2a():
    crm = [_crm_row("20", "Оплачен")]
    bank = [_bank_row("Оплата заказа A-00020")]
    assert q2a_paid_orders_without_payment(crm, bank) == []


def test_non_paid_not_in_q2a_even_without_payment():
    crm = [_crm_row("10", "В работе"), _crm_row("11", "Отменён")]
    bank: list[dict[str, str]] = []
    assert q2a_paid_orders_without_payment(crm, bank) == []


def test_q2a_sorted_numbers():
    crm = [_crm_row("30", "Оплачен"), _crm_row("5", "Оплачен"), _crm_row("12", "Оплачен")]
    bank = [_bank_row("заказ 12")]
    assert q2a_paid_orders_without_payment(crm, bank) == [5, 30]


def test_current_export_q2a_is_sorted_list_of_ints():
    crm, _ = run_cleanup(DOCS_CRM)
    bank = read_bank_statement(DOCS_BANK)
    result = q2a_paid_orders_without_payment(crm, bank)
    assert result == sorted(result)
    assert all(isinstance(value, int) for value in result)
    assert result  # на учебных данных список не пустой
