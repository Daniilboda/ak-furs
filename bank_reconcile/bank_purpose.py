"""Номер заказа из назначения и сопоставление с CRM (этап 2, шаги 3–4)."""

from __future__ import annotations

import csv
import re
from pathlib import Path

# A-00243 / A877 / А-54; заказ 775; зак. 528; по счету №828; Счёт № 00991.
# Телефон и прочие цифры без этих маркеров не трогаем.
_PURPOSE_ORDER = re.compile(
    r"(?:"
    r"(?<![A-Za-zА-Яа-я0-9])[AaАа]-?0*(\d+)"
    r"|(?:заказ[ауе]?|зак\.?)\s*№?\s*0*(\d+)"
    r"|(?:по\s+)?сч[её]т[уа]?\s*№\s*0*(\d+)"
    r")",
    re.IGNORECASE,
)


def extract_order_number(purpose: str) -> int | None:
    """Достать номер заказа из назначения или вернуть None.

    Если в тексте несколько разных номеров по маркерам — None (неоднозначно).
    «Счёт № N» / «по счету № N» считаем записью номера заказа (согласовано для этапа 2).
    """
    numbers: list[int] = []
    for match in _PURPOSE_ORDER.finditer(purpose):
        raw = next(group for group in match.groups() if group is not None)
        numbers.append(int(raw))
    if not numbers:
        return None
    unique = set(numbers)
    if len(unique) > 1:
        return None
    return numbers[0]


def payment_order_id(record: dict[str, str]) -> int | None:
    """Номер заказа из поля «Назначение платежа» записи выписки."""
    return extract_order_number(record["Назначение платежа"])


def matched_order_id(
    purpose: str,
    known_order_ids: set[int],
) -> int | None:
    """Номер заказа, если он есть в назначении и среди известных заказов.

    Иначе None — платёж к заказу не относится (шаг 4 / ТЗ).
    """
    order_id = extract_order_number(purpose)
    if order_id is None or order_id not in known_order_ids:
        return None
    return order_id


def is_payment_identified(
    record: dict[str, str],
    known_order_ids: set[int],
) -> bool:
    """True, если поступление опознано: номер из назначения есть в CRM."""
    return matched_order_id(record["Назначение платежа"], known_order_ids) is not None


def unidentified_incoming(
    records: list[dict[str, str]],
    known_order_ids: set[int],
) -> list[dict[str, str]]:
    """Поступления, которые не относятся к существующему заказу.

    По ТЗ: в назначении нет номера существующего заказа
    (номера нет, номер неоднозначен, или такого заказа нет после очистки CRM).
    """
    return [
        record
        for record in records
        if not is_payment_identified(record, known_order_ids)
    ]


UNIDENTIFIED_FIELDNAMES = (
    "Дата операции",
    "Время",
    "Сумма",
    "Валюта",
    "Тип",
    "Контрагент",
    "Назначение платежа",
    "Извлечённый номер",
    "Причина",
)


def enrich_unidentified_row(record: dict[str, str]) -> dict[str, str]:
    """Добавить к операции извлечённый номер и причину неопознанности."""
    order_id = payment_order_id(record)
    if order_id is None:
        reason = "нет номера заказа в назначении"
        extracted = ""
    else:
        reason = "номер есть, но заказа нет в CRM после очистки"
        extracted = str(order_id)
    return {
        **{key: record[key] for key in record},
        "Извлечённый номер": extracted,
        "Причина": reason,
    }


def write_unidentified_incoming_csv(
    path: Path | str,
    records: list[dict[str, str]],
    known_order_ids: set[int],
) -> list[dict[str, str]]:
    """Записать неопознанные поступления в CSV (UTF-8 с BOM, «;»)."""
    rows = unidentified_incoming(records, known_order_ids)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(UNIDENTIFIED_FIELDNAMES), delimiter=";"
        )
        writer.writeheader()
        for record in rows:
            writer.writerow(enrich_unidentified_row(record))
    return rows
