"""Сравнение цены после скидки с минимумом (этап 3, шаг 5)."""

from __future__ import annotations

from datetime import date

from article_price import min_allowed_price
from unit_after_discount import unit_price_after_discount, unit_price_after_discount_from_row


def is_below_minimum(unit_after_discount: float, minimum: float) -> bool:
    """Нарушение: цена за единицу после скидки строго ниже минимума.

    Равенство минимуму нарушением не считается.
    """
    return unit_after_discount < minimum


def line_is_price_violation(
    record: dict[str, str],
    price_history: list[dict],
    renames: list[dict],
) -> bool:
    """True, если строка заказа нарушает мин. цену на дату создания.

    Статус «Отменён» здесь не фильтруется — это шаг 6.
    """
    unit_after = unit_price_after_discount_from_row(record)
    minimum = min_allowed_price(
        str(record["Артикул"]),
        record["Дата создания"],
        price_history,
        renames,
    )
    return is_below_minimum(unit_after, minimum)


def line_price_check(
    *,
    article: str,
    creation_date: date | str,
    price: str,
    quantity: str,
    discount: str,
    price_history: list[dict],
    renames: list[dict],
) -> tuple[float, float, bool]:
    """Вернуть (цена после скидки, минимум, есть_нарушение)."""
    unit_after = unit_price_after_discount(price, quantity, discount)
    minimum = min_allowed_price(article, creation_date, price_history, renames)
    return unit_after, minimum, is_below_minimum(unit_after, minimum)
