"""Итог Q3: число нарушений и разбивка по менеджерам (этап 3, шаг 7)."""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from article_price import load_price_tables
from q3_filter import line_is_q3_violation

_CRM_CLEANUP = Path(__file__).resolve().parent.parent / "crm_cleanup"
if str(_CRM_CLEANUP) not in sys.path:
    sys.path.insert(0, str(_CRM_CLEANUP))

from run_crm_cleanup import run_cleanup  # noqa: E402

REQUIRED_COLUMNS = (
    "Артикул",
    "Дата создания",
    "Цена за ед.",
    "Кол-во",
    "Скидка",
    "Статус",
    "Менеджер",
)


def read_cleaned_crm(path: Path | str) -> list[dict[str, str]]:
    """Прочитать cleaned CRM (допускаются доп. колонки)."""
    file_path = Path(path)
    with file_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        if reader.fieldnames is None:
            raise ValueError(f"{file_path} пуст или без заголовка")
        for name in REQUIRED_COLUMNS:
            if name not in reader.fieldnames:
                raise ValueError(f"{file_path}: нет колонки {name!r}")
        return [dict(row) for row in reader]


def q3_violations_by_manager(
    crm_records: list[dict[str, str]],
    price_history: list[dict],
    renames: list[dict],
) -> dict[str, int]:
    """Счётчик нарушений по каноническому имени менеджера."""
    counts: Counter[str] = Counter()
    for record in crm_records:
        if line_is_q3_violation(record, price_history, renames):
            manager = str(record["Менеджер"]).strip()
            counts[manager] += 1
    return dict(sorted(counts.items(), key=lambda item: item[0]))


def compute_q3(
    crm_records: list[dict[str, str]],
    price_history: list[dict],
    renames: list[dict],
) -> dict[str, Any]:
    """Q3: total и разбивка; сумма по менеджерам равна total."""
    by_manager = q3_violations_by_manager(crm_records, price_history, renames)
    total = sum(by_manager.values())
    return {
        "q3_price_violation_lines_total": total,
        "q3_price_violation_lines_by_manager": by_manager,
    }


def compute_q3_from_cleaned(
    cleaned_crm_path: Path | str,
    catalog_path: Path | str,
) -> dict[str, Any]:
    """Посчитать Q3 по cleaned CRM и каталогу цен."""
    records = read_cleaned_crm(cleaned_crm_path)
    history, renames = load_price_tables(catalog_path)
    return compute_q3(records, history, renames)


def compute_q3_from_raw(
    crm_path: Path | str,
    catalog_path: Path | str,
) -> dict[str, Any]:
    """Посчитать Q3 из сырой CRM (сначала cleanup этапа 1)."""
    records, _ = run_cleanup(crm_path, catalog_path, only="all")
    history, renames = load_price_tables(catalog_path)
    return compute_q3(records, history, renames)


def write_q3_results_csv(path: Path | str, result: dict[str, Any]) -> None:
    """Записать итоги Q3 в CSV (UTF-8 с BOM, «;»)."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    by_manager = result["q3_price_violation_lines_by_manager"]
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["показатель", "значение"])
        writer.writerow(
            ["q3_price_violation_lines_total", result["q3_price_violation_lines_total"]]
        )
        writer.writerow([])
        writer.writerow(["менеджер", "нарушений"])
        for name, count in by_manager.items():
            writer.writerow([name, count])

