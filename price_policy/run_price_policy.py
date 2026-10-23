"""CLI этапа 3: нарушения мин. цены (Q3)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from q3_summary import compute_q3_from_cleaned, write_q3_results_csv

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CRM = (
    ROOT / "crm_cleanup" / "normalized_crm" / "01_crm_orders_export_cleaned.csv"
)
DEFAULT_CATALOG = ROOT / "docs" / "03_catalog_prices_reference.xlsx"
DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_OUT = DEFAULT_RESULTS_DIR / "q3_price_violations.csv"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Q3: строки ниже мин. цены (кроме «Отменён»). "
            "Исходные файлы не изменяются."
        ),
    )
    parser.add_argument(
        "--crm",
        type=Path,
        default=DEFAULT_CRM,
        help="Очищенный CRM (*_cleaned.csv)",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG,
        help="Справочник цен (xlsx со скрытым «Прайс_история»)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Куда записать итоги (по умолчанию price_policy/results/q3_price_violations.csv)",
    )
    args = parser.parse_args(argv)

    if not args.crm.is_file():
        raise SystemExit(f"нет файла CRM: {args.crm}")
    if not args.catalog.is_file():
        raise SystemExit(f"нет файла каталога: {args.catalog}")

    result = compute_q3_from_cleaned(args.crm, args.catalog)
    write_q3_results_csv(args.out, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"saved={args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
