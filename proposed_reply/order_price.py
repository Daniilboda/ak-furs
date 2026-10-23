"""Цена заказа из cleaned CRM: номер заказа → «Цена за ед.»."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CLEANED_CRM = (
    _ROOT / "crm_cleanup" / "normalized_crm" / "01_crm_orders_export_cleaned.csv"
)


@dataclass(frozen=True)
class OrderPrice:
    order_id: str
    article: str
    unit_price: Decimal
    discount: str
    unit_after_discount: Decimal | None
    status: str
    manager: str


def format_rub(amount: Decimal) -> str:
    """252000 → «252 000 ₽» (как в чатах с цифрами)."""
    quantized = amount.quantize(Decimal("1"))
    as_int = int(quantized)
    grouped = f"{as_int:,}".replace(",", " ")
    return f"{grouped} ₽"


def _to_decimal(value: str) -> Decimal:
    text = str(value).strip().replace(" ", "").replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation as error:
        raise ValueError(f"не удалось разобрать сумму: {value!r}") from error


def read_cleaned_crm(path: Path | str) -> list[dict[str, str]]:
    file_path = Path(path)
    with file_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        if reader.fieldnames is None:
            raise ValueError(f"{file_path} пуст или без заголовка")
        for name in ("Номер заказа", "Артикул", "Цена за ед.", "Скидка", "Статус", "Менеджер"):
            if name not in reader.fieldnames:
                raise ValueError(f"{file_path}: нет колонки {name!r}")
        return [dict(row) for row in reader]


def lines_for_order(crm_rows: list[dict[str, str]], order_id: str) -> list[dict[str, str]]:
    return [row for row in crm_rows if str(row["Номер заказа"]).strip() == str(order_id)]


def price_from_order_lines(order_id: str, lines: list[dict[str, str]]) -> OrderPrice:
    """
    Цена для клиента — «Цена за ед.» без скидки.
    При нескольких строках заказа берём первую по № строки.
    """
    if not lines:
        raise ValueError(f"заказ {order_id} не найден в cleaned CRM")

    def line_no(row: dict[str, str]) -> int:
        raw = str(row.get("№ строки", "1")).strip()
        return int(raw) if raw.isdigit() else 1

    row = sorted(lines, key=line_no)[0]
    unit = _to_decimal(row["Цена за ед."])
    after_raw = row.get("Цена за ед. после скидки", "").strip()
    after = _to_decimal(after_raw) if after_raw else None
    return OrderPrice(
        order_id=str(order_id),
        article=str(row["Артикул"]).strip(),
        unit_price=unit,
        discount=str(row.get("Скидка", "")).strip(),
        unit_after_discount=after,
        status=str(row["Статус"]).strip(),
        manager=str(row["Менеджер"]).strip(),
    )


def order_price_from_crm(
    order_id: str,
    *,
    crm_path: Path | str = DEFAULT_CLEANED_CRM,
    crm_rows: list[dict[str, str]] | None = None,
) -> OrderPrice:
    """Номер заказа → цена из cleaned CRM."""
    rows = crm_rows if crm_rows is not None else read_cleaned_crm(crm_path)
    return price_from_order_lines(order_id, lines_for_order(rows, order_id))
