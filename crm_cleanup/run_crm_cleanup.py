"""Главный вход очистки CRM: принимает путь к выгрузке и сохраняет результат."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Literal

from crm_dedupe import (
    CRM_HEADER,
    apply_canonical_client_numbers,
    apply_canonical_order_numbers,
    count_q1,
    dedupe_order_lines,
    read_crm,
)
from crm_normalize import (
    apply_canonical_creation_dates,
    apply_canonical_unit_prices,
    apply_currency_normalization,
    apply_discount_fields,
    apply_manager_normalization,
    apply_source_normalization,
    apply_status_normalization,
    load_manager_aliases,
)

Mode = Literal["all", "dedupe", "normalize"]

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_OUT_DIR = PACKAGE_DIR / "normalized_crm"
DEFAULT_CATALOG = PACKAGE_DIR.parent / "docs" / "03_catalog_prices_reference.xlsx"


def cleaned_output_name(crm_path: Path | str) -> str:
    """Имя результата: исходное имя файла + _cleaned, то же расширение."""
    path = Path(crm_path)
    return f"{path.stem}_cleaned{path.suffix}"


def write_crm_csv(path: Path | str, records: list[dict]) -> None:
    """Записать записи в CSV с разделителем «;» и UTF-8 BOM."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    extra_columns: list[str] = []
    for record in records:
        for key in record:
            if key not in CRM_HEADER and key not in extra_columns:
                extra_columns.append(key)
    columns = list(CRM_HEADER) + extra_columns
    with file_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(columns)
        for record in records:
            writer.writerow([_cell(record.get(column, "")) for column in columns])


def _cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def run_cleanup(
    crm_path: Path | str,
    catalog_path: Path | str | None = None,
    *,
    only: Mode = "all",
) -> tuple[list[dict], tuple[int, int]]:
    """Прогнать очистку CRM.

    only:
      - all — дубли, затем нормализация полей;
      - dedupe — только удаление дублей;
      - normalize — только статусы, скидка и менеджеры, без удаления дублей.
    """
    records: list[dict] = list(read_crm(crm_path))
    if only in {"all", "dedupe"}:
        records = list(dedupe_order_lines(records))
    if only in {"all", "normalize"}:
        catalog = Path(catalog_path) if catalog_path is not None else DEFAULT_CATALOG
        records = list(apply_status_normalization(records))
        records = list(apply_discount_fields(records))
        aliases = load_manager_aliases(catalog)
        records = list(apply_manager_normalization(records, aliases))
    records = list(apply_canonical_order_numbers(records))
    records = list(apply_canonical_client_numbers(records))
    records = list(apply_canonical_creation_dates(records))
    records = list(apply_canonical_unit_prices(records))
    records = list(apply_source_normalization(records))
    records = list(apply_currency_normalization(records))
    return records, count_q1(records)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Очистка CRM: дубли, статусы, скидки, менеджеры. Исходный файл не изменяется.",
    )
    parser.add_argument(
        "--crm",
        required=True,
        type=Path,
        help="Путь к выгрузке CRM (CSV)",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG,
        help="Путь к справочнику с листом «Менеджеры» (только чтение, файл не перезаписывается)",
    )
    parser.add_argument(
        "--only",
        choices=("all", "dedupe", "normalize"),
        default="all",
        help="Прогнать весь пайплайн или только dedupe / normalize",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Папка для сохранённого файла",
    )
    args = parser.parse_args(argv)

    records, (unique_orders, unique_lines) = run_cleanup(
        args.crm,
        args.catalog,
        only=args.only,
    )
    out_path = args.out_dir / cleaned_output_name(args.crm)
    write_crm_csv(out_path, records)
    print(f"saved={out_path}")
    print(f"q1_unique_orders={unique_orders}")
    print(f"q1_unique_order_lines={unique_lines}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
