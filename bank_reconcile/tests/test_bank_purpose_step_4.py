"""Шаг 4 этапа 2: сопоставление платежа с заказом."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "crm_cleanup"))

from bank_purpose import is_payment_identified, matched_order_id, unidentified_incoming
from bank_statement import incoming_payments, read_bank_statement
from run_crm_cleanup import run_cleanup

DOCS_BANK = Path(__file__).resolve().parents[2] / "docs" / "02_bank_statement_rub.csv"
DOCS_CRM = Path(__file__).resolve().parents[2] / "docs" / "01_crm_orders_export.csv"


def _payment(purpose: str) -> dict[str, str]:
    return {
        "Дата операции": "01.01.2025",
        "Время": "12:00",
        "Сумма": "100,00",
        "Валюта": "RUR",
        "Тип": "Поступление",
        "Контрагент": "Тест",
        "Назначение платежа": purpose,
    }


def test_number_in_orders_is_identified():
    known = {54, 775, 828}
    assert matched_order_id("A54 доплата", known) == 54
    assert is_payment_identified(_payment("Предоплата заказ 775, тел. +7 964 847-86-23"), known)
    assert is_payment_identified(_payment("по счету №828 от 13.12.2025"), known)


def test_number_missing_or_unknown_is_not_identified():
    known = {54, 775}
    assert matched_order_id("Перевод", known) is None
    assert matched_order_id("A54 доплата", set()) is None
    assert matched_order_id("Оплата заказа A-01180", known) is None
    assert not is_payment_identified(_payment("за шубу"), known)
    assert not is_payment_identified(_payment("Оплата заказа A-01180"), known)


def test_unidentified_incoming_keeps_only_unmatched():
    known = {54}
    records = [
        _payment("A54 доплата"),
        _payment("Перевод"),
        _payment("A877 доплата"),
    ]
    unmatched = unidentified_incoming(records, known)
    assert [r["Назначение платежа"] for r in unmatched] == ["Перевод", "A877 доплата"]


def test_current_data_has_both_identified_and_unidentified():
    cleaned, _ = run_cleanup(DOCS_CRM)
    known = {int(row["Номер заказа"]) for row in cleaned}
    incoming = incoming_payments(read_bank_statement(DOCS_BANK))
    identified = [r for r in incoming if is_payment_identified(r, known)]
    unidentified = unidentified_incoming(incoming, known)
    assert identified
    assert unidentified
    assert len(identified) + len(unidentified) == len(incoming)
