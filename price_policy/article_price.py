"""Сопоставление артикула с прайсом с учётом переименований (этап 3, шаг 3)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from catalog_prices import read_article_renames, read_price_history
from order_date import order_creation_date


def old_to_new_article_map(renames: list[dict]) -> dict[str, str]:
    """Старый артикул → новый (из листа «Переименования»)."""
    mapping: dict[str, str] = {}
    for row in renames:
        old = str(row["Старый артикул"]).strip()
        new = str(row["Новый артикул"]).strip()
        if old in mapping and mapping[old] != new:
            raise ValueError(f"конфликт переименования для {old!r}")
        mapping[old] = new
    return mapping


def price_lookup_article(article: str, renames: list[dict]) -> str:
    """Артикул, под которым ищем цену в «Прайс_история».

    Старый код всегда сводим к новому: в прайсе лежат новые артикулы,
    а старый может встречаться в заказах и после даты перехода.
    """
    text = article.strip()
    return old_to_new_article_map(renames).get(text, text)


def period_covers(on_date: date, start: date | None, end: date | None) -> bool:
    """True, если дата попадает в [start, end]; end=None — без верхней границы."""
    if start is None:
        raise ValueError("у периода прайса пустое «Действует с»")
    if on_date < start:
        return False
    if end is not None and on_date > end:
        return False
    return True


def min_allowed_price(
    article: str,
    on_date: date | str,
    price_history: list[dict],
    renames: list[dict],
) -> float:
    """Минимально допустимая цена артикула на дату создания заказа."""
    day = order_creation_date(on_date)
    lookup = price_lookup_article(article, renames)
    matches = [
        row
        for row in price_history
        if str(row["Артикул"]).strip() == lookup
        and period_covers(day, row["Действует с"], row["Действует по"])
    ]
    if not matches:
        raise ValueError(
            f"нет мин. цены для артикула {article!r} (поиск как {lookup!r}) "
            f"на дату {day.isoformat()}"
        )
    if len(matches) > 1:
        raise ValueError(
            f"несколько периодов прайса для {lookup!r} на {day.isoformat()}"
        )
    return float(matches[0]["Минимально допустимая цена, ₽"])


def load_price_tables(catalog_path: Path | str) -> tuple[list[dict], list[dict]]:
    """Прочитать прайс и переименования из одного xlsx."""
    return read_price_history(catalog_path), read_article_renames(catalog_path)
