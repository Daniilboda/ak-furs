"""Проверка шага 6: разбор скидки и цена за единицу после скидки."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crm_dedupe import dedupe_order_lines, read_crm
from crm_normalize import (
    apply_discount_fields,
    parse_discount,
    parse_money,
    unit_price_after_discount,
)

DOCS_CRM = Path(__file__).resolve().parents[2] / "docs" / "01_crm_orders_export.csv"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("50 000", 50_000),
        ("19,000.00", 19_000),
        ("2300,00", 2300),
        ("2,48 млн", 2_480_000),
        ("800", 800),
        ("1,600.00", 1600),
        ("2 100", 2100),
    ],
)
def test_parse_money(raw: str, expected: float):
    assert parse_money(raw) == expected


def test_parse_discount_percent():
    assert parse_discount("7%") == ("percent", 7.0)


def test_parse_discount_amount():
    assert parse_discount("800") == ("amount", 800.0)
    assert parse_discount("2 100") == ("amount", 2100.0)
    assert parse_discount("1,600.00") == ("amount", 1600.0)


def test_parse_discount_empty_is_zero_amount():
    assert parse_discount("") == ("amount", 0.0)
    assert parse_discount("   ") == ("amount", 0.0)


def test_unit_price_after_percent_discount():
    # заказ 512: 50 000 × 1, скидка 7% → 46 500
    assert unit_price_after_discount("50 000", "1", "7%") == 46_500


def test_unit_price_after_rub_discount_on_line():
    # заказ 671: 19 000 × 2 = 38 000, скидка 800 на строку → 37 200; за единицу 18 600
    assert unit_price_after_discount("19,000.00", "2", "800") == 18_600


def test_unit_price_without_discount():
    assert unit_price_after_discount("50 000", "1", "") == 50_000


def test_unit_price_with_million_price():
    assert unit_price_after_discount("2,48 млн", "1", "") == 2_480_000


def test_apply_discount_fields_does_not_mutate_input():
    original = [{"Цена за ед.": "50 000", "Кол-во": "1", "Скидка": "7%"}]
    updated = apply_discount_fields(original)
    assert "Цена за ед. после скидки" not in original[0]
    assert updated[0]["Цена за ед. после скидки"] == 46_500


def test_current_export_discounts_parse():
    records = dedupe_order_lines(read_crm(DOCS_CRM))
    for record in records:
        unit_price_after_discount(record["Цена за ед."], record["Кол-во"], record["Скидка"])
