"""Проверка записи канонического номера заказа."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crm_dedupe import apply_canonical_order_numbers


def test_apply_canonical_order_numbers_writes_digits_only():
    records = [
        {"Номер заказа": "A-00075", "№ строки": "1"},
        {"Номер заказа": " a-811", "№ строки": "2"},
    ]
    updated = apply_canonical_order_numbers(records)
    assert updated[0]["Номер заказа"] == "75"
    assert updated[1]["Номер заказа"] == "811"
    assert records[0]["Номер заказа"] == "A-00075"
