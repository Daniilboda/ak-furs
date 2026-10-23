"""Проверка подсчёта уникальных заказов и строк (Q1)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crm_dedupe import CRM_HEADER, count_q1, dedupe_order_lines, read_crm

DOCS_CRM = Path(__file__).resolve().parents[2] / "docs" / "01_crm_orders_export.csv"


def _record(order: str, line: str) -> dict[str, str]:
    record = {column: "" for column in CRM_HEADER}
    record["Номер заказа"] = order
    record["№ строки"] = line
    record["Выгружено"] = "2026-10-01 09:00"
    return record


def test_count_q1_on_small_fixture():
    records = [
        _record("A-00075", "1"),
        _record("a-75", "2"),
        _record("А-100", "1"),
        _record("A100", "1"),
    ]
    unique_orders, unique_lines = count_q1(records)
    assert unique_orders == 2
    assert unique_lines == 3


def test_count_q1_after_dedupe_matches_kept_rows():
    kept = dedupe_order_lines(read_crm(DOCS_CRM))
    unique_orders, unique_lines = count_q1(kept)
    assert unique_lines == len(kept)
    assert unique_orders <= unique_lines


def test_count_q1_on_current_export_after_cleanup():
    kept = dedupe_order_lines(read_crm(DOCS_CRM))
    unique_orders, unique_lines = count_q1(kept)
    assert unique_orders == 1000
    assert unique_lines == 1368
