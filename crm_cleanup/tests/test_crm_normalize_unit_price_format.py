"""Проверка формата цены за единицу с копейками."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crm_dedupe import dedupe_order_lines, read_crm
from crm_normalize import apply_canonical_unit_prices, format_money
from run_crm_cleanup import run_cleanup

DOCS_CRM = Path(__file__).resolve().parents[2] / "docs" / "01_crm_orders_export.csv"
DOCS_CATALOG = Path(__file__).resolve().parents[2] / "docs" / "03_catalog_prices_reference.xlsx"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("50 000", "50000.00"),
        ("19,000.00", "19000.00"),
        ("2300,00", "2300.00"),
        ("2,48 млн", "2480000.00"),
        (46500, "46500.00"),
        (18600.0, "18600.00"),
    ],
)
def test_format_money_with_kopecks(raw: object, expected: str):
    assert format_money(raw) == expected  # type: ignore[arg-type]


def test_apply_canonical_unit_prices_formats_both_fields():
    records = [
        {
            "Цена за ед.": "50 000",
            "Цена за ед. после скидки": 46500.0,
        }
    ]
    updated = apply_canonical_unit_prices(records)
    assert updated[0]["Цена за ед."] == "50000.00"
    assert updated[0]["Цена за ед. после скидки"] == "46500.00"
    assert records[0]["Цена за ед."] == "50 000"


def test_cleanup_writes_unit_prices_with_kopecks():
    records, _ = run_cleanup(DOCS_CRM, DOCS_CATALOG, only="all")
    money = re.compile(r"^\d+\.\d{2}$")
    for record in records:
        assert money.fullmatch(str(record["Цена за ед."]))
        assert money.fullmatch(str(record["Цена за ед. после скидки"]))
