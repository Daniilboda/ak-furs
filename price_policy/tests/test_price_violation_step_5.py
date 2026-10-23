"""Шаг 5 этапа 3: сравнение с минимальной ценой."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from catalog_prices import read_article_renames, read_price_history
from price_violation import is_below_minimum, line_price_check
from unit_after_discount import unit_price_after_discount

DOCS_CATALOG = Path(__file__).resolve().parents[2] / "docs" / "03_catalog_prices_reference.xlsx"


@pytest.fixture(scope="module")
def tables():
    return read_price_history(DOCS_CATALOG), read_article_renames(DOCS_CATALOG)


def test_below_minimum_is_violation():
    assert is_below_minimum(61999.0, 62000.0) is True


def test_equal_minimum_is_not_violation():
    assert is_below_minimum(62000.0, 62000.0) is False


def test_above_minimum_is_not_violation():
    assert is_below_minimum(62001.0, 62000.0) is False


def test_line_below_min_marked(tables):
    history, renames = tables
    # CHN-PAL-01 на 05.11.2025 → мин. 62000; после скидки ниже
    unit_after, minimum, violated = line_price_check(
        article="CHN-PAL-01",
        creation_date=date(2025, 11, 5),
        price="70000",
        quantity="1",
        discount="20%",
        price_history=history,
        renames=renames,
    )
    assert unit_after == 56000.0
    assert minimum == 62000.0
    assert violated is True


def test_line_equal_min_not_marked(tables):
    history, renames = tables
    unit_after, minimum, violated = line_price_check(
        article="CHN-PAL-01",
        creation_date="05.11.2025",
        price="62000",
        quantity="1",
        discount="",
        price_history=history,
        renames=renames,
    )
    assert unit_after == minimum == 62000.0
    assert violated is False


def test_old_article_rename_used_in_check(tables):
    history, renames = tables
    # SWK-PSH-01 → SWKPSH01N, на 2025-11-05 мин. 173000
    _, minimum, violated = line_price_check(
        article="SWK-PSH-01",
        creation_date=date(2025, 11, 5),
        price="200000",
        quantity="1",
        discount="20%",  # 160000 < 173000
        price_history=history,
        renames=renames,
    )
    assert minimum == 173000.0
    assert violated is True
    assert unit_price_after_discount("200000", "1", "20%") == 160000.0
