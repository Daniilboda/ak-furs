"""Проверка сведения источников к каноническим именам."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crm_dedupe import dedupe_order_lines, read_crm
from crm_normalize import (
    SOURCE_INSTAGRAM,
    SOURCE_REFERRAL,
    SOURCE_SITE,
    SOURCE_TELEGRAM,
    SOURCE_YANDEX_MAPS,
    normalize_source,
)
from run_crm_cleanup import run_cleanup

DOCS_CRM = Path(__file__).resolve().parents[2] / "docs" / "01_crm_orders_export.csv"
DOCS_CATALOG = Path(__file__).resolve().parents[2] / "docs" / "03_catalog_prices_reference.xlsx"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("IG", SOURCE_INSTAGRAM),
        ("Insta", SOURCE_INSTAGRAM),
        ("инстаграм", SOURCE_INSTAGRAM),
        ("Instagram", SOURCE_INSTAGRAM),
        ("Telegram", SOURCE_TELEGRAM),
        ("телеграм", SOURCE_TELEGRAM),
        ("TG", SOURCE_TELEGRAM),
        ("Рекомендация", SOURCE_REFERRAL),
        ("Реком.", SOURCE_REFERRAL),
        ("Сарафан", SOURCE_REFERRAL),
        ("Яндекс Карты", SOURCE_YANDEX_MAPS),
        ("Я.Карты", SOURCE_YANDEX_MAPS),
        ("yandex maps", SOURCE_YANDEX_MAPS),
        ("Сайт", SOURCE_SITE),
        ("Заявка с сайта", SOURCE_SITE),
        ("site", SOURCE_SITE),
    ],
)
def test_normalize_source_aliases(raw: str, expected: str):
    assert normalize_source(raw) == expected


def test_unknown_source_raises():
    with pytest.raises(ValueError, match="не найден"):
        normalize_source("ТикТок")


def test_cleanup_sources_are_five_canonical_values():
    records, _ = run_cleanup(DOCS_CRM, DOCS_CATALOG, only="all")
    sources = {record["Источник"] for record in records}
    assert sources == {
        SOURCE_INSTAGRAM,
        SOURCE_TELEGRAM,
        SOURCE_REFERRAL,
        SOURCE_YANDEX_MAPS,
        SOURCE_SITE,
    }
    # сырые варианты после очистки не остаются
    raw_variants = {record["Источник"] for record in dedupe_order_lines(read_crm(DOCS_CRM))}
    assert "Сарафан" in raw_variants
    assert "Сарафан" not in sources
