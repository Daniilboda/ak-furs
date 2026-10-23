"""Чтение прайса и переименований артикулов (этап 3, шаг 1)."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook

PRICE_HISTORY_SHEET = "Прайс_история"
RENAMES_SHEET = "Переименования"

PRICE_HISTORY_HEADER = (
    "Артикул",
    "Действует с",
    "Действует по",
    "Рекомендованная цена, ₽",
    "Минимально допустимая цена, ₽",
)

RENAMES_HEADER = (
    "Старый артикул",
    "Новый артикул",
    "Дата перехода",
    "Комментарий",
)


def _as_date(value: object, *, field: str) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise ValueError(f"не удалось разобрать дату в поле {field}: {value!r}")


def _as_number(value: object, *, field: str) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    raise ValueError(f"не удалось разобрать число в поле {field}: {value!r}")


def read_price_history(path: Path | str) -> list[dict]:
    """Прочитать скрытый лист «Прайс_история».

    Возвращает строки с артикулом, периодом действия и минимальной ценой.
    Файл не изменяется.
    """
    file_path = Path(path)
    workbook = load_workbook(file_path, data_only=True, read_only=True)
    if PRICE_HISTORY_SHEET not in workbook.sheetnames:
        raise ValueError(f"{file_path}: нет листа {PRICE_HISTORY_SHEET!r}")
    sheet = workbook[PRICE_HISTORY_SHEET]
    rows = sheet.iter_rows(values_only=True)
    try:
        header = tuple(next(rows))
    except StopIteration as error:
        raise ValueError(f"{file_path}: лист {PRICE_HISTORY_SHEET!r} пуст") from error
    if header != PRICE_HISTORY_HEADER:
        raise ValueError(
            f"{file_path}: ожидались колонки {PRICE_HISTORY_HEADER}, получено {header}"
        )

    records: list[dict] = []
    for line_no, row in enumerate(rows, start=2):
        if row is None or all(cell is None or cell == "" for cell in row):
            continue
        if len(row) < len(PRICE_HISTORY_HEADER):
            raise ValueError(
                f"{file_path}: {PRICE_HISTORY_SHEET} строка {line_no}: мало колонок"
            )
        article, start, end, recommended, minimum = row[:5]
        if article is None or str(article).strip() == "":
            raise ValueError(
                f"{file_path}: {PRICE_HISTORY_SHEET} строка {line_no}: пустой артикул"
            )
        records.append(
            {
                "Артикул": str(article).strip(),
                "Действует с": _as_date(start, field="Действует с"),
                "Действует по": _as_date(end, field="Действует по"),
                "Рекомендованная цена, ₽": _as_number(
                    recommended, field="Рекомендованная цена, ₽"
                ),
                "Минимально допустимая цена, ₽": _as_number(
                    minimum, field="Минимально допустимая цена, ₽"
                ),
            }
        )
    workbook.close()
    return records


def read_article_renames(path: Path | str) -> list[dict]:
    """Прочитать лист «Переименования». Файл не изменяется."""
    file_path = Path(path)
    workbook = load_workbook(file_path, data_only=True, read_only=True)
    if RENAMES_SHEET not in workbook.sheetnames:
        raise ValueError(f"{file_path}: нет листа {RENAMES_SHEET!r}")
    sheet = workbook[RENAMES_SHEET]

    rows = sheet.iter_rows(values_only=True)
    try:
        header = tuple(next(rows))
    except StopIteration as error:
        raise ValueError(f"{file_path}: лист {RENAMES_SHEET!r} пуст") from error
    if header != RENAMES_HEADER:
        raise ValueError(
            f"{file_path}: ожидались колонки {RENAMES_HEADER}, получено {header}"
        )

    records: list[dict] = []
    for line_no, row in enumerate(rows, start=2):
        if row is None or all(cell is None or cell == "" for cell in row):
            continue
        if len(row) < len(RENAMES_HEADER):
            raise ValueError(
                f"{file_path}: {RENAMES_SHEET} строка {line_no}: мало колонок"
            )
        old, new, switched, comment = row[:4]
        records.append(
            {
                "Старый артикул": str(old).strip(),
                "Новый артикул": str(new).strip(),
                "Дата перехода": _as_date(switched, field="Дата перехода"),
                "Комментарий": "" if comment is None else str(comment).strip(),
            }
        )
    workbook.close()
    return records


def price_history_sheet_is_hidden(path: Path | str) -> bool:
    """True, если лист «Прайс_история» скрыт (как в учебном файле)."""
    workbook = load_workbook(Path(path), read_only=True)
    try:
        if PRICE_HISTORY_SHEET not in workbook.sheetnames:
            raise ValueError(f"{path}: нет листа {PRICE_HISTORY_SHEET!r}")
        return workbook[PRICE_HISTORY_SHEET].sheet_state == "hidden"
    finally:
        workbook.close()
