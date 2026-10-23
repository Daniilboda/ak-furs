"""Шаг 7 этапа 3: итог Q3 по менеджерам."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from catalog_prices import read_article_renames, read_price_history
from q3_summary import compute_q3, compute_q3_from_cleaned

DOCS_CATALOG = Path(__file__).resolve().parents[2] / "docs" / "03_catalog_prices_reference.xlsx"
CLEANED_CRM = (
    Path(__file__).resolve().parents[2]
    / "crm_cleanup"
    / "normalized_crm"
    / "01_crm_orders_export_cleaned.csv"
)


def _row(
    *,
    manager: str,
    status: str = "Оплачен",
    price: str = "70000",
    discount: str = "20%",
) -> dict[str, str]:
    return {
        "Номер заказа": "1",
        "№ строки": "1",
        "Дата создания": "05.11.2025",
        "Артикул": "CHN-PAL-01",
        "Кол-во": "1",
        "Цена за ед.": price,
        "Скидка": discount,
        "Статус": status,
        "Менеджер": manager,
    }


def test_total_equals_sum_by_manager():
    history = read_price_history(DOCS_CATALOG)
    renames = read_article_renames(DOCS_CATALOG)
    records = [
        _row(manager="Вероника Белова"),  # violation
        _row(manager="Вероника Белова"),  # violation
        _row(manager="Алина Сергеева"),  # violation
        _row(manager="Алина Сергеева", status="Отменён"),  # skip
        _row(manager="Полина Орлова", price="62000", discount=""),  # equal min — ok
    ]
    result = compute_q3(records, history, renames)
    by_manager = result["q3_price_violation_lines_by_manager"]
    assert result["q3_price_violation_lines_total"] == sum(by_manager.values())
    assert result["q3_price_violation_lines_total"] == 3
    assert by_manager == {"Алина Сергеева": 1, "Вероника Белова": 2}


def test_current_cleaned_q3_total_matches_manager_sum():
    result = compute_q3_from_cleaned(CLEANED_CRM, DOCS_CATALOG)
    total = result["q3_price_violation_lines_total"]
    by_manager = result["q3_price_violation_lines_by_manager"]
    assert total == sum(by_manager.values())
    assert total > 0
    assert all(isinstance(name, str) and name for name in by_manager)
    assert all(isinstance(count, int) and count > 0 for count in by_manager.values())
