"""Шаг 3 этапа 2: номер заказа из назначения."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bank_purpose import extract_order_number
from bank_statement import incoming_payments, read_bank_statement

DOCS_BANK = Path(__file__).resolve().parents[2] / "docs" / "02_bank_statement_rub.csv"


@pytest.mark.parametrize(
    ("purpose", "expected"),
    [
        ("A877 доплата", 877),
        ("A54 доплата", 54),
        ("Оплата заказа A-00243", 243),
        ("Предоплата заказ 775, тел. +7 964 847-86-23", 775),
        ("зак. 528", 528),
        ("по счету №828 от 13.12.2025", 828),
        ("Счёт № 00991 от 16.02.2026. НДС не облагается", 991),
        ("Оплата по договору", None),
        ("Перевод", None),
        ("за шубу", None),
        ("Пополнение", None),
    ],
)
def test_extract_order_number_examples(purpose: str, expected: int | None):
    assert extract_order_number(purpose) == expected


def test_phone_digits_are_not_taken_as_order():
    assert extract_order_number("Предоплата заказ 775, тел. +7 964 847-86-23") == 775


def test_conflicting_order_markers_return_none():
    assert extract_order_number("заказ 10 и заказ 20") is None


def test_current_statement_purposes_mostly_extract():
    incoming = incoming_payments(read_bank_statement(DOCS_BANK))
    extracted = [extract_order_number(r["Назначение платежа"]) for r in incoming]
    with_number = sum(1 for value in extracted if value is not None)
    without = sum(1 for value in extracted if value is None)
    assert with_number >= 1100
    assert without >= 1
