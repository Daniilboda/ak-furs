"""Дата создания заказа для выбора периода прайса (этап 3, шаг 2)."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

_CRM_CLEANUP = Path(__file__).resolve().parent.parent / "crm_cleanup"
if str(_CRM_CLEANUP) not in sys.path:
    sys.path.insert(0, str(_CRM_CLEANUP))

from crm_normalize import parse_creation_date as _parse_creation_date  # noqa: E402


def order_creation_date(value: str | date) -> date:
    """Свести «Дата создания» к календарной дате.

    Принимает сырые форматы выгрузки и уже канонический вид ДД.ММ.ГГГГ
    из cleaned CRM. Тот же разбор, что в этапе 1.
    """
    if isinstance(value, date):
        return value
    return _parse_creation_date(str(value))
