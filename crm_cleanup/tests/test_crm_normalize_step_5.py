"""Проверка шага 5: сведение статусов."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crm_dedupe import dedupe_order_lines, read_crm
from crm_normalize import (
    STATUS_CANCELLED,
    STATUS_IN_PROGRESS,
    STATUS_PAID,
    STATUS_REFUND,
    apply_status_normalization,
    normalize_status,
)

DOCS_CRM = Path(__file__).resolve().parents[2] / "docs" / "01_crm_orders_export.csv"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("PAID", STATUS_PAID),
        ("оплачено", STATUS_PAID),
        ("Оплачен", STATUS_PAID),
        ("Оплачен ", STATUS_PAID),
        ("CANCELLED", STATUS_CANCELLED),
        ("отменен", STATUS_CANCELLED),
        ("Отменён", STATUS_CANCELLED),
        ("REFUND", STATUS_REFUND),
        ("возврат", STATUS_REFUND),
        ("Возврат", STATUS_REFUND),
        ("NEW", STATUS_IN_PROGRESS),
        ("Ждём оплату", STATUS_IN_PROGRESS),
        ("в работе", STATUS_IN_PROGRESS),
        ("В работе", STATUS_IN_PROGRESS),
        ("неизвестный статус", STATUS_IN_PROGRESS),
    ],
)
def test_normalize_status_examples(raw: str, expected: str):
    assert normalize_status(raw) == expected


def test_apply_status_normalization_does_not_mutate_input():
    original = [{"Статус": "PAID", "Номер заказа": "A-1"}]
    updated = apply_status_normalization(original)
    assert original[0]["Статус"] == "PAID"
    assert updated[0]["Статус"] == STATUS_PAID
    assert updated[0] is not original[0]


def test_current_export_statuses_become_four_values():
    records = apply_status_normalization(dedupe_order_lines(read_crm(DOCS_CRM)))
    statuses = {record["Статус"] for record in records}
    assert statuses <= {STATUS_PAID, STATUS_CANCELLED, STATUS_REFUND, STATUS_IN_PROGRESS}
