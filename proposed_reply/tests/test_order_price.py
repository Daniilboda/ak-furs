"""Цена заказа из cleaned CRM."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parent
sys.path.insert(0, str(PACKAGE))

from order_price import format_rub, order_price_from_crm

DOCS_CRM = ROOT / "crm_cleanup" / "normalized_crm" / "01_crm_orders_export_cleaned.csv"


def test_format_rub():
    assert format_rub(Decimal("252000")) == "252 000 ₽"
    assert format_rub(Decimal("63000.00")) == "63 000 ₽"


def test_order_702_unit_price_not_discounted():
    price = order_price_from_crm("702", crm_path=DOCS_CRM)
    assert price.article == "SOB-ZH-01"
    assert price.unit_price == Decimal("252000.00")
    assert price.unit_after_discount == Decimal("226800.00")
