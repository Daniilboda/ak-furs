"""
Одна команда пересчёта answers.json из сырых файлов (этап 06).

Поле notes не генерируется скриптом: при пересчёте сохраняется ваш текст
из уже существующего answers.json (если файл есть).

Пример (из корня проекта):
  python solve.py
  python solve.py docs/
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RUN_COMMAND = "python solve.py"


def _add_packages() -> None:
    for name in ("crm_cleanup", "bank_reconcile", "price_policy", "client_chats"):
        path = ROOT / name
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


def load_existing_notes(answers_path: Path | str) -> str:
    """Прочитать notes, которые вы написали вручную в answers.json."""
    path = Path(answers_path)
    if not path.is_file():
        return ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    notes = payload.get("notes", "")
    return notes if isinstance(notes, str) else ""


def resolve_inputs(data_dir: Path) -> dict[str, Path]:
    """Найти CRM, выписку, каталог и zip чатов в папке данных."""
    data_dir = data_dir.resolve()
    if not data_dir.is_dir():
        raise FileNotFoundError(f"нет папки данных: {data_dir}")

    preferred = {
        "crm": data_dir / "01_crm_orders_export.csv",
        "bank": data_dir / "02_bank_statement_rub.csv",
        "catalog": data_dir / "03_catalog_prices_reference.xlsx",
        "chats": data_dir / "04_client_chats.zip",
    }
    if all(path.is_file() for path in preferred.values()):
        return preferred

    csvs = sorted(data_dir.glob("*.csv"))
    xlsx = sorted(data_dir.glob("*.xlsx"))
    zips = sorted(data_dir.glob("*.zip"))
    if len(xlsx) != 1:
        raise FileNotFoundError(f"{data_dir}: нужен ровно один .xlsx (каталог), найдено {len(xlsx)}")
    if len(zips) != 1:
        raise FileNotFoundError(f"{data_dir}: нужен ровно один .zip (чаты), найдено {len(zips)}")
    if len(csvs) < 2:
        raise FileNotFoundError(f"{data_dir}: нужны CRM и выписка (.csv), найдено {len(csvs)}")

    def pick_csv(tokens: list[str], label: str) -> Path:
        for path in csvs:
            name = path.name.casefold()
            if any(token in name for token in tokens):
                return path
        raise FileNotFoundError(f"{data_dir}: не найден файл {label} среди {[p.name for p in csvs]}")

    crm = pick_csv(["crm", "order"], "CRM")
    bank = pick_csv(["bank", "statement", "выпис"], "выписки")
    if crm == bank:
        # два csv без явных имён — лексикографически: первый CRM, второй банк
        crm, bank = csvs[0], csvs[1]
    return {"crm": crm, "bank": bank, "catalog": xlsx[0], "chats": zips[0]}


def build_answers(
    data_dir: Path | str,
    *,
    notes: str = "",
    run_command: str = RUN_COMMAND,
) -> dict[str, Any]:
    """Посчитать Q1–Q4 из сырых файлов. notes передаётся снаружи (ваши толкования)."""
    _add_packages()
    from bank_q2 import compute_q2_from_cleaned
    from q3_summary import compute_q3_from_cleaned
    from q4_select import compute_q4
    from run_crm_cleanup import run_cleanup, write_crm_csv

    paths = resolve_inputs(Path(data_dir))
    records, (q1_orders, q1_lines) = run_cleanup(paths["crm"], paths["catalog"], only="all")

    with tempfile.TemporaryDirectory(prefix="akfurs_solve_") as tmp:
        cleaned = Path(tmp) / "crm_cleaned.csv"
        write_crm_csv(cleaned, records)
        q2 = compute_q2_from_cleaned(cleaned, paths["bank"])
        q3 = compute_q3_from_cleaned(cleaned, paths["catalog"])

    q4_ids = compute_q4(zip_path=paths["chats"])

    return {
        "q1_unique_orders": int(q1_orders),
        "q1_unique_order_lines": int(q1_lines),
        "q2a_paid_orders_without_payment": list(q2["q2a_paid_orders_without_payment"]),
        "q2b_unidentified_payments_count": int(q2["q2b_unidentified_payments_count"]),
        "q2b_unidentified_payments_sum_rub": float(q2["q2b_unidentified_payments_sum_rub"]),
        "q3_price_violation_lines_total": int(q3["q3_price_violation_lines_total"]),
        "q3_price_violation_lines_by_manager": dict(q3["q3_price_violation_lines_by_manager"]),
        "q4_chats_meeting_before_price": list(q4_ids),
        "run_command": run_command,
        "notes": notes,
    }


def write_answers(payload: dict[str, Any], out_path: Path | str) -> Path:
    path = Path(out_path)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Пересчитать answers.json из сырых выгрузок (CRM, банк, каталог, чаты)."
    )
    parser.add_argument(
        "data_dir",
        nargs="?",
        default=str(ROOT / "docs"),
        help="Папка с сырыми файлами (по умолчанию docs/)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "answers.json",
        help="Куда записать answers.json (по умолчанию ./answers.json)",
    )
    args = parser.parse_args(argv)

    notes = load_existing_notes(args.out)
    payload = build_answers(args.data_dir, notes=notes)
    write_answers(payload, args.out)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
