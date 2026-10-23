"""Чтение рублёвой банковской выписки и разбор суммы/типа (этап 2)."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Literal

OperationType = Literal["Поступление", "Списание"]

BANK_HEADER = (
    "Дата операции",
    "Время",
    "Сумма",
    "Валюта",
    "Тип",
    "Контрагент",
    "Назначение платежа",
)

# Колонки, которые нужны для Q2 по stages.xlsx / ТЗ.
REQUIRED_COLUMNS = (
    "Дата операции",
    "Сумма",
    "Тип",
    "Назначение платежа",
)


def read_bank_statement(path: Path | str) -> list[dict[str, str]]:
    """Прочитать выписку: Windows-1251, разделитель «;».

    Первая строка — сведения о счёте (пропускается).
    Вторая — заголовки колонок. Дальше — операции.
    Файл по этому пути не изменяется.
    """
    file_path = Path(path)
    raw = file_path.read_bytes()
    try:
        text = raw.decode("cp1251")
    except UnicodeDecodeError as error:
        raise ValueError(f"{file_path} не в кодировке Windows-1251") from error

    rows = list(csv.reader(text.splitlines(), delimiter=";"))
    if len(rows) < 2:
        raise ValueError(f"{file_path}: нужны строка счёта и строка заголовков")

    header = tuple(cell.strip() for cell in rows[1])
    if header != BANK_HEADER:
        raise ValueError(
            f"{file_path}: ожидались колонки {BANK_HEADER}, получено {header}"
        )
    for name in REQUIRED_COLUMNS:
        if name not in header:
            raise ValueError(f"{file_path}: нет колонки {name!r}")

    records: list[dict[str, str]] = []
    for line_no, row in enumerate(rows[2:], start=3):
        if len(row) == 1 and row[0].strip() == "":
            continue
        if len(row) != len(BANK_HEADER):
            raise ValueError(
                f"{file_path}: строка {line_no} содержит {len(row)} колонок, "
                f"нужно {len(BANK_HEADER)}"
            )
        records.append(dict(zip(BANK_HEADER, (cell.strip() for cell in row), strict=True)))
    return records


def parse_amount(value: str) -> float:
    """Разобрать сумму выписки: «1 080 500,00» → 1080500.0, «-445 000,00» → -445000.0."""
    text = value.strip().replace("\xa0", " ").replace(" ", "")
    if text == "":
        raise ValueError(f"пустая сумма: {value!r}")
    text = text.replace(",", ".")
    if not re.fullmatch(r"-?\d+(\.\d+)?", text):
        raise ValueError(f"не удалось разобрать сумму: {value!r}")
    return float(text)


def normalize_operation_type(value: str) -> OperationType:
    """Свести тип операции к «Поступление» или «Списание»."""
    text = value.strip()
    if text == "Поступление":
        return "Поступление"
    if text == "Списание":
        return "Списание"
    raise ValueError(f"неизвестный тип операции: {value!r}")


def is_incoming(value: str) -> bool:
    """True, если операция — поступление (нужна для Q2)."""
    return normalize_operation_type(value) == "Поступление"


def incoming_payments(records: list[dict[str, str]]) -> list[dict[str, str]]:
    """Оставить только поступления."""
    return [record for record in records if is_incoming(record["Тип"])]
