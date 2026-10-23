"""Шаг 2 этапа 3: дата создания заказа → одна календарная дата."""

from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from order_date import order_creation_date

DOCS_CRM = Path(__file__).resolve().parents[2] / "docs" / "01_crm_orders_export.csv"
CLEANED_CRM = (
    Path(__file__).resolve().parents[2]
    / "crm_cleanup"
    / "normalized_crm"
    / "01_crm_orders_export_cleaned.csv"
)


@pytest.mark.parametrize(
    "raw",
    [
        "2025-11-05",
        "05.11.2025",
        "05/11/2025",
        "5 ноя 2025",
    ],
)
def test_different_writings_same_calendar_date(raw: str):
    """Пример строки CHN-PAL-01 / заказ A00846: все записи → 2025-11-05."""
    assert order_creation_date(raw) == date(2025, 11, 5)


def test_excel_serial_and_iso_become_dates():
    assert order_creation_date("45752") == date(2025, 4, 5)
    assert order_creation_date("2026-03-03") == date(2026, 3, 3)


def test_date_object_passes_through():
    assert order_creation_date(date(2025, 11, 5)) == date(2025, 11, 5)


def test_cleaned_crm_dates_all_parse():
    with CLEANED_CRM.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
    assert rows
    for row in rows:
        parsed = order_creation_date(row["Дата создания"])
        assert isinstance(parsed, date)


def test_raw_export_sample_matches_cleaned():
    """Сырая и cleaned дата одной строки дают один день."""
    with DOCS_CRM.open(encoding="utf-8-sig", newline="") as handle:
        raw_rows = list(csv.DictReader(handle, delimiter=";"))
    with CLEANED_CRM.open(encoding="utf-8-sig", newline="") as handle:
        clean_rows = list(csv.DictReader(handle, delimiter=";"))

    raw = next(r for r in raw_rows if r["Артикул"] == "CHN-PAL-01")
    clean = next(
        r
        for r in clean_rows
        if r["Артикул"] == "CHN-PAL-01" and r["Дата создания"] == "05.11.2025"
    )
    assert order_creation_date(raw["Дата создания"]) == order_creation_date(
        clean["Дата создания"]
    )
    assert order_creation_date(raw["Дата создания"]) == date(2025, 11, 5)
