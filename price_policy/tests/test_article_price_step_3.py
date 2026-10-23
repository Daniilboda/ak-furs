"""Шаг 3 этапа 3: артикул ↔ прайс с переименованиями."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from article_price import (
    min_allowed_price,
    old_to_new_article_map,
    price_lookup_article,
)
from catalog_prices import read_article_renames, read_price_history

DOCS_CATALOG = Path(__file__).resolve().parents[2] / "docs" / "03_catalog_prices_reference.xlsx"


@pytest.fixture(scope="module")
def tables():
    return read_price_history(DOCS_CATALOG), read_article_renames(DOCS_CATALOG)


def test_old_article_maps_to_new(tables):
    _, renames = tables
    assert price_lookup_article("SWK-PSH-01", renames) == "SWKPSH01N"
    assert price_lookup_article("SWKPSH01N", renames) == "SWKPSH01N"
    assert price_lookup_article("CHN-PAL-01", renames) == "CHN-PAL-01"


def test_min_price_for_new_and_old_article_same(tables):
    history, renames = tables
    on = date(2025, 11, 5)
    new_price = min_allowed_price("SWKPSH01N", on, history, renames)
    old_price = min_allowed_price("SWK-PSH-01", on, history, renames)
    assert new_price == old_price == 173000.0


def test_min_price_depends_on_date_period(tables):
    history, renames = tables
    assert min_allowed_price("CHN-PAL-01", date(2025, 3, 1), history, renames) == 60000.0
    assert min_allowed_price("CHN-PAL-01", date(2025, 11, 5), history, renames) == 62000.0
    assert min_allowed_price("CHN-PAL-01", "05.11.2025", history, renames) == 62000.0


def test_old_article_after_transition_date_still_resolves(tables):
    """Комментарий справочника: старый код может быть в заказах и после перехода."""
    history, renames = tables
    mapping = old_to_new_article_map(renames)
    assert mapping["SWK-PSH-01"] == "SWKPSH01N"
    # дата перехода 2025-05-10; заказ позже — всё равно ищем по новому коду в прайсе
    assert (
        min_allowed_price("SWK-PSH-01", date(2025, 12, 1), history, renames) == 173000.0
    )


def test_unknown_article_raises(tables):
    history, renames = tables
    with pytest.raises(ValueError, match="нет мин. цены"):
        min_allowed_price("NO-SUCH-ART", date(2025, 1, 1), history, renames)
