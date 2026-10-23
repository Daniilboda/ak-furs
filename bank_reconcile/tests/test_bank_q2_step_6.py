"""Шаг 6 этапа 2: Q2b — неопознанные поступления."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "crm_cleanup"))

from bank_q2 import q2b_unidentified_payments
from bank_statement import read_bank_statement
from run_crm_cleanup import run_cleanup

DOCS_BANK = Path(__file__).resolve().parents[2] / "docs" / "02_bank_statement_rub.csv"
DOCS_CRM = Path(__file__).resolve().parents[2] / "docs" / "01_crm_orders_export.csv"


def _crm_row(order: str) -> dict[str, str]:
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
        "Статус": "Оплачен",
        "Комментарий": "",
        "Выгружено": "2026-01-01 10:00",
    }


def _bank_row(amount: str, purpose: str, *, op_type: str = "Поступление") -> dict[str, str]:
    return {
        "Дата операции": "01.01.2025",
        "Время": "12:00",
        "Сумма": amount,
        "Валюта": "RUR",
        "Тип": op_type,
        "Контрагент": "Тест",
        "Назначение платежа": purpose,
    }


def test_q2b_counts_and_sums_unidentified_only():
    crm = [_crm_row("10")]
    bank = [
        _bank_row("100,00", "A10 доплата"),  # опознан
        _bank_row("200,00", "Перевод"),  # нет номера
        _bank_row("50,00", "заказ 999"),  # номера нет в CRM
        _bank_row("300,00", "без номера", op_type="Списание"),  # не поступление
    ]
    count, total = q2b_unidentified_payments(crm, bank)
    assert count == 2
    assert total == 250.0


def test_q2b_empty_when_all_matched():
    crm = [_crm_row("10"), _crm_row("20")]
    bank = [_bank_row("1 000,00", "A10"), _bank_row("2 000,00", "заказ 20")]
    assert q2b_unidentified_payments(crm, bank) == (0, 0.0)


def test_current_export_q2b_matches_unidentified_list_size():
    crm, _ = run_cleanup(DOCS_CRM)
    bank = read_bank_statement(DOCS_BANK)
    count, total = q2b_unidentified_payments(crm, bank)
    assert count == 16
    assert total == 3_437_100.0
