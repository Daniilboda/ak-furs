"""CLI этапа 2: сверка cleaned CRM с выпиской, расчёт Q2."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from bank_q2 import compute_q2_from_cleaned, public_q2_result, write_q2_outputs

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CRM = (
    ROOT / "crm_cleanup" / "normalized_crm" / "01_crm_orders_export_cleaned.csv"
)
DEFAULT_BANK = ROOT / "docs" / "02_bank_statement_rub.csv"
DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_OUT = DEFAULT_RESULTS_DIR / "q2_reconciliation.csv"
DEFAULT_UNIDENTIFIED = DEFAULT_RESULTS_DIR / "unidentified_incoming.csv"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Q2: сверка очищенного CRM (*_cleaned.csv) с банковской выпиской. "
            "Исходные файлы не изменяются."
        ),
    )
    parser.add_argument(
        "--crm",
        type=Path,
        default=DEFAULT_CRM,
        help="Путь к очищенному CRM (имя может быть любым, обычно *_cleaned.csv)",
    )
    parser.add_argument(
        "--bank",
        type=Path,
        default=DEFAULT_BANK,
        help="Путь к рублёвой выписке (имя файла может быть любым)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Куда записать итоги сверки (по умолчанию bank_reconcile/results/q2_reconciliation.csv)",
    )
    parser.add_argument(
        "--unidentified-out",
        type=Path,
        default=DEFAULT_UNIDENTIFIED,
        help="Куда записать список неопознанных (по умолчанию bank_reconcile/results/unidentified_incoming.csv)",
    )
    args = parser.parse_args(argv)

    if not args.crm.is_file():
        raise SystemExit(f"нет файла CRM: {args.crm}")
    if not args.bank.is_file():
        raise SystemExit(f"нет файла выписки: {args.bank}")

    result = compute_q2_from_cleaned(args.crm, args.bank)
    write_q2_outputs(result, args.out, args.unidentified_out)
    print(json.dumps(public_q2_result(result), ensure_ascii=False, indent=2))
    print(f"saved={args.out}")
    print(f"unidentified_saved={args.unidentified_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
