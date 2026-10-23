"""Чтение выгрузки CRM, удаление дублей, канонические номера заказов и клиентов, подсчёт Q1."""

from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path

CRM_HEADER = (
    "Номер заказа",
    "№ строки",
    "Дата создания",
    "Клиент",
    "Менеджер",
    "Источник",
    "Артикул",
    "Кол-во",
    "Цена за ед.",
    "Валюта",
    "Скидка",
    "Статус",
    "Комментарий",
    "Выгружено",
)

# С префиксом A/А или уже просто число (как в cleaned-файле).
_ORDER_NUMBER = re.compile(r"^\s*(?:[AaАа]-?)?0*(\d+)\s*$")
# CL-00087, CL 87, cl00087, КЛ-00087 или уже просто число.
_CLIENT_NUMBER = re.compile(r"^\s*(?:[CcКк][LlЛл][\s-]*)?0*(\d+)\s*$")


def read_crm(path: Path | str) -> list[dict[str, str]]:
    """Прочитать CRM-выгрузку: UTF-8, разделитель «;», 14 колонок.

    Метка BOM допускается. Файл по этому пути не изменяется.
    """
    file_path = Path(path)
    raw = file_path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError(f"{file_path} не в кодировке UTF-8") from error

    rows = list(csv.reader(text.splitlines(), delimiter=";"))
    if not rows:
        raise ValueError(f"{file_path} пуст")
    header = tuple(rows[0])
    if header != CRM_HEADER:
        raise ValueError(
            f"{file_path}: ожидались колонки {CRM_HEADER}, получено {header}"
        )
    records: list[dict[str, str]] = []
    for line_no, row in enumerate(rows[1:], start=2):
        if len(row) != len(CRM_HEADER):
            raise ValueError(
                f"{file_path}: строка {line_no} содержит {len(row)} колонок, нужно {len(CRM_HEADER)}"
            )
        records.append(dict(zip(CRM_HEADER, row, strict=True)))
    return records


def order_number(value: str) -> int:
    """Свести номер заказа к числу.

    A-00075, А-75, a-75, A75 и 75 означают 75. Буква A может быть латинской
    или кириллической. Пробелы по краям не учитываются.
    """
    match = _ORDER_NUMBER.match(value)
    if match is None:
        raise ValueError(f"не удалось разобрать номер заказа: {value!r}")
    return int(match.group(1))


def apply_canonical_order_numbers(records: list[dict]) -> list[dict]:
    """Записать номер заказа каноническим числом: A-00075 → «75»."""
    result: list[dict] = []
    for record in records:
        updated = dict(record)
        updated["Номер заказа"] = str(order_number(str(record["Номер заказа"])))
        result.append(updated)
    return result


def client_number(value: str) -> int:
    """Свести код клиента к числу.

    CL-00087, CL 87, cl00087, КЛ-00087 и 87 означают 87.
    Ведущие нули убираются. Пробелы по краям не учитываются.
    """
    match = _CLIENT_NUMBER.match(value)
    if match is None:
        raise ValueError(f"не удалось разобрать код клиента: {value!r}")
    return int(match.group(1))


def apply_canonical_client_numbers(records: list[dict]) -> list[dict]:
    """Записать код клиента каноническим числом: CL-00087 → «87»."""
    result: list[dict] = []
    for record in records:
        updated = dict(record)
        updated["Клиент"] = str(client_number(str(record["Клиент"])))
        result.append(updated)
    return result


def exported_at(value: str) -> datetime:
    """Разобрать «Выгружено» в дату и время.

    В выгрузке время записано как «2026-10-01 09:28».
    """
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d %H:%M")
    except (AttributeError, ValueError) as error:
        raise ValueError(f"не удалось разобрать «Выгружено»: {value!r}") from error


def later_row(left: dict[str, str], right: dict[str, str]) -> dict[str, str]:
    """Оставить запись с более поздним «Выгружено».

    Если время совпало, шаг не выбирает строку: для такого дубля правило ещё не задано.
    """
    left_at = exported_at(left["Выгружено"])
    right_at = exported_at(right["Выгружено"])
    if left_at == right_at:
        raise ValueError("одинаковое «Выгружено»: какая строка остаётся, шаг 3 не решает")
    return left if left_at > right_at else right


def line_number(value: str) -> int:
    """Свести № строки к числу. «01» и «1» означают строку 1."""
    text = value.strip()
    if not text.isdigit():
        raise ValueError(f"не удалось разобрать № строки: {value!r}")
    return int(text)


def _line_key(record: dict[str, str]) -> tuple[int, int]:
    return order_number(record["Номер заказа"]), line_number(record["№ строки"])


def _same_payload(left: dict[str, str], right: dict[str, str]) -> bool:
    return all(
        left[column].strip() == right[column].strip()
        for column in CRM_HEADER
        if column not in {"Номер заказа", "№ строки"}
    )


def dedupe_order_lines(records: list[dict[str, str]]) -> list[dict[str, str]]:
    """Оставить одну запись на пару «номер заказа + № строки».

    № строки сводится к числу: «01» и «1» — одна позиция. Берётся запись
    с самым поздним «Выгружено». Если у нескольких записей это время совпало
    и остальные поля одинаковы, остаётся первая из них. Если время совпало,
    а поля различаются, расчёт останавливается.
    """
    grouped: dict[tuple[int, int], list[dict[str, str]]] = {}
    key_order: list[tuple[int, int]] = []
    for record in records:
        key = _line_key(record)
        if key not in grouped:
            grouped[key] = []
            key_order.append(key)
        grouped[key].append(record)

    kept: list[dict[str, str]] = []
    for key in key_order:
        items = grouped[key]
        latest = max(exported_at(item["Выгружено"]) for item in items)
        candidates = [item for item in items if exported_at(item["Выгружено"]) == latest]
        for other in candidates[1:]:
            if not _same_payload(candidates[0], other):
                order_id, line = key
                raise ValueError(
                    f"заказ {order_id}, строка {line}: несколько записей с «Выгружено» "
                    f"{candidates[0]['Выгружено']}, поля различаются"
                )
        kept.append(candidates[0])
    return kept


def count_q1(records: list[dict[str, str]]) -> tuple[int, int]:
    """Посчитать уникальные заказы и уникальные строки заказов.

    Номер заказа сводится к числу. Строка заказа — пара «номер заказа + № строки».
    Ожидаются записи после удаления дублей; повтор пары не увеличивает счётчик строк.
    """
    orders: set[int] = set()
    lines: set[tuple[int, int]] = set()
    for record in records:
        order_id = order_number(record["Номер заказа"])
        line_id = line_number(record["№ строки"])
        orders.add(order_id)
        lines.add((order_id, line_id))
    return len(orders), len(lines)
