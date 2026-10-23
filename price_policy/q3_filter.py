"""Фильтр статуса для Q3 (этап 3, шаг 6)."""

from __future__ import annotations

from price_violation import line_is_price_violation

CANCELLED_STATUS = "Отменён"


def is_cancelled(record: dict[str, str]) -> bool:
    """True, если строка со статусом «Отменён»."""
    return str(record.get("Статус", "")).strip() == CANCELLED_STATUS


def counts_for_q3(record: dict[str, str]) -> bool:
    """Строка участвует в Q3: любой статус, кроме «Отменён»."""
    return not is_cancelled(record)


def line_is_q3_violation(
    record: dict[str, str],
    price_history: list[dict],
    renames: list[dict],
) -> bool:
    """Нарушение мин. цены для Q3: не «Отменён» и цена после скидки ниже минимума."""
    if is_cancelled(record):
        return False
    return line_is_price_violation(record, price_history, renames)
