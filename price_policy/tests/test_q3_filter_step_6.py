"""Шаг 6 этапа 3: исключить статус «Отменён»."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from catalog_prices import read_article_renames, read_price_history
from q3_filter import counts_for_q3, is_cancelled, line_is_q3_violation

DOCS_CATALOG = Path(__file__).resolve().parents[2] / "docs" / "03_catalog_prices_reference.xlsx"


@pytest.fixture(scope="module")
def tables():
    return read_price_history(DOCS_CATALOG), read_article_renames(DOCS_CATALOG)


def _row(*, status: str, price: str = "70000", discount: str = "20%") -> dict[str, str]:
    # CHN-PAL-01 на 05.11.2025: мин. 62000; 70000−20% = 56000 → ниже минимума
    return {
        "Номер заказа": "1",
        "№ строки": "1",
        "Дата создания": "05.11.2025",
        "Артикул": "CHN-PAL-01",
        "Кол-во": "1",
        "Цена за ед.": price,
        "Скидка": discount,
        "Статус": status,
        "Менеджер": "Ольга Смирнова",
    }


def test_cancelled_detected():
    assert is_cancelled(_row(status="Отменён")) is True
    assert is_cancelled(_row(status="Оплачен")) is False
    assert is_cancelled(_row(status="В работе")) is False


def test_cancelled_does_not_count_for_q3():
    assert counts_for_q3(_row(status="Отменён")) is False
    assert counts_for_q3(_row(status="В работе")) is True
    assert counts_for_q3(_row(status="Возврат")) is True


def test_cancelled_below_min_not_q3_violation(tables):
    history, renames = tables
    row = _row(status="Отменён")
    assert line_is_q3_violation(row, history, renames) is False


def test_in_progress_below_min_is_q3_violation(tables):
    history, renames = tables
    row = _row(status="В работе")
    assert line_is_q3_violation(row, history, renames) is True


def test_paid_equal_min_not_violation(tables):
    history, renames = tables
    row = _row(status="Оплачен", price="62000", discount="")
    assert line_is_q3_violation(row, history, renames) is False
