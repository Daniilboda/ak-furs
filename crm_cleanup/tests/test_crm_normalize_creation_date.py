"""Проверка канонической даты создания ДД.ММ.ГГГГ."""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crm_dedupe import dedupe_order_lines, read_crm
from crm_normalize import (
    apply_canonical_creation_dates,
    format_creation_date,
    parse_creation_date,
)

DOCS_CRM = Path(__file__).resolve().parents[2] / "docs" / "01_crm_orders_export.csv"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2026-03-03", "03.03.2026"),
        ("03.03.2026", "03.03.2026"),
        ("11/02/2025", "11.02.2025"),
        ("45752", "05.04.2025"),
        ("23 сен 2026", "23.09.2026"),
        ("7 фев 2025", "07.02.2025"),
        ("24 мая 2026", "24.05.2026"),
    ],
)
def test_format_creation_date_examples(raw: str, expected: str):
    assert format_creation_date(raw) == expected


def test_parse_creation_date_excel_serial():
    assert parse_creation_date("45819") == date(2025, 6, 11)


def test_apply_canonical_creation_dates_does_not_mutate_input():
    original = [{"Дата создания": "2026-03-03"}]
    updated = apply_canonical_creation_dates(original)
    assert original[0]["Дата создания"] == "2026-03-03"
    assert updated[0]["Дата создания"] == "03.03.2026"


def test_current_export_dates_all_parse_to_dotted_format():
    for record in dedupe_order_lines(read_crm(DOCS_CRM)):
        formatted = format_creation_date(record["Дата создания"])
        assert re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", formatted)
