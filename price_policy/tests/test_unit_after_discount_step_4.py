"""Шаг 4 этапа 3: цена за единицу после скидки."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from unit_after_discount import unit_price_after_discount, unit_price_after_discount_from_row


def test_percent_discount_from_line_sum():
    # 50_000 × 1, скидка 7% → 46_500
    assert unit_price_after_discount("50000.00", "1", "7%") == 46500.0


def test_ruble_discount_on_whole_line():
    # 19_000 × 2 = 38_000, скидка 800 на строку → 37_200 → за ед. 18_600
    assert unit_price_after_discount("19000", "2", "800") == 18600.0


def test_empty_discount_keeps_unit_price():
    assert unit_price_after_discount("100000.00", "1", "") == 100000.0


def test_from_row_uses_crm_fields():
    row = {
        "Цена за ед.": "40000.00",
        "Кол-во": "1",
        "Скидка": "10%",
    }
    assert unit_price_after_discount_from_row(row) == 36000.0
