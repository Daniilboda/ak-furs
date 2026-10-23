"""Проверка сведения валюты к «руб.»."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crm_normalize import CURRENCY_RUB, normalize_currency
from run_crm_cleanup import run_cleanup

DOCS_CRM = Path(__file__).resolve().parents[2] / "docs" / "01_crm_orders_export.csv"
DOCS_CATALOG = Path(__file__).resolve().parents[2] / "docs" / "03_catalog_prices_reference.xlsx"


@pytest.mark.parametrize(
    "raw",
    ["RUB", "RUR", "руб", "руб.", "₽", " Rub "],
)
def test_normalize_currency_to_rub(raw: str):
    assert normalize_currency(raw) == CURRENCY_RUB


def test_unknown_currency_raises():
    with pytest.raises(ValueError, match="не найдена"):
        normalize_currency("USD")


def test_cleanup_currency_is_only_rub():
    records, _ = run_cleanup(DOCS_CRM, DOCS_CATALOG, only="all")
    assert {record["Валюта"] for record in records} == {CURRENCY_RUB}
