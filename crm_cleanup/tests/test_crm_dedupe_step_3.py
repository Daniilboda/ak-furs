"""Проверка поля «Выгружено» (шаг 3)."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crm_dedupe import exported_at, later_row, read_crm

DOCS_CRM = Path(__file__).resolve().parents[2] / "docs" / "01_crm_orders_export.csv"


def _row(exported: str, price: str) -> dict[str, str]:
    return {"Выгружено": exported, "Цена за ед.": price}


def test_exported_at_parses_crm_timestamp():
    assert exported_at("2026-10-01 09:28") == datetime(2026, 10, 1, 9, 28)


def test_exported_at_strips_edges():
    assert exported_at(" 2026-09-27 23:26 ") == datetime(2026, 9, 27, 23, 26)


def test_exported_at_rejects_other_formats():
    with pytest.raises(ValueError):
        exported_at("01.10.2026 09:28")


def test_later_row_keeps_the_newer_export():
    earlier = _row("2026-09-27 23:26", "125000,00")
    later = _row("2026-10-01 09:28", "159 000")
    assert later_row(earlier, later) is later
    assert later_row(later, earlier) is later


def test_later_row_does_not_choose_when_time_is_equal():
    with pytest.raises(ValueError, match="одинаковое"):
        later_row(_row("2026-10-01 09:28", "100"), _row("2026-10-01 09:28", "200"))


def test_current_export_timestamps_parse():
    for record in read_crm(DOCS_CRM):
        exported_at(record["Выгружено"])
