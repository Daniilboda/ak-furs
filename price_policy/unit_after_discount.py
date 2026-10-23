"""Цена за единицу после скидки (этап 3, шаг 4)."""

from __future__ import annotations

import sys
from pathlib import Path

_CRM_CLEANUP = Path(__file__).resolve().parent.parent / "crm_cleanup"
if str(_CRM_CLEANUP) not in sys.path:
    sys.path.insert(0, str(_CRM_CLEANUP))

from crm_normalize import unit_price_after_discount as _unit_price_after_discount  # noqa: E402


def unit_price_after_discount(price: str, quantity: str, discount: str) -> float:
    """Цена за единицу после скидки.

    «N%» — от суммы строки (цена × кол-во).
    Число без % — рубли на всю строку.
    Тот же расчёт, что в этапе 1.
    """
    return _unit_price_after_discount(price, quantity, discount)


def unit_price_after_discount_from_row(record: dict[str, str]) -> float:
    """То же по полям строки CRM / cleaned (всегда пересчёт из цены, кол-ва, скидки)."""
    return unit_price_after_discount(
        str(record["Цена за ед."]),
        str(record["Кол-во"]),
        str(record.get("Скидка", "")),
    )
