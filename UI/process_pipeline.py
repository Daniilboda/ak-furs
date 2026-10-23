"""Пайплайн для UI: сырые файлы → cleaned CRM, Q2 CSV, annotations, Q4, answers.json."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _add_packages() -> None:
    for name in ("crm_cleanup", "bank_reconcile", "price_policy", "client_chats"):
        path = ROOT / name
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


def run_pipeline(data_dir: Path, results_dir: Path) -> dict[str, Path]:
    """
    data_dir: папка с 01_crm…, 02_bank…, 03_catalog…, 04_client_chats.zip
    results_dir: куда положить артефакты для скачивания
    """
    _add_packages()
    from annotate_chats import build_annotations
    from bank_q2 import compute_q2_from_cleaned, write_q2_outputs
    from q4_select import compute_q4, write_q4_result
    from run_crm_cleanup import cleaned_output_name, run_cleanup, write_crm_csv

    data_dir = Path(data_dir)
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    extra_dir = results_dir / "additional"
    extra_dir.mkdir(parents=True, exist_ok=True)

    crm = data_dir / "01_crm_orders_export.csv"
    bank = data_dir / "02_bank_statement_rub.csv"
    catalog = data_dir / "03_catalog_prices_reference.xlsx"
    chats = data_dir / "04_client_chats.zip"
    for path in (crm, bank, catalog, chats):
        if not path.is_file():
            raise FileNotFoundError(f"нет входного файла: {path.name}")

    records, _ = run_cleanup(crm, catalog, only="all")
    cleaned_name = cleaned_output_name(crm)
    cleaned_path = results_dir / cleaned_name
    write_crm_csv(cleaned_path, records)

    q2 = compute_q2_from_cleaned(cleaned_path, bank)
    q2_path = results_dir / "q2_reconciliation.csv"
    unidentified_path = results_dir / "unidentified_incoming.csv"
    write_q2_outputs(q2, q2_path, unidentified_path)

    annotations = build_annotations(chats)
    annotations_path = extra_dir / "chat_annotations.json"
    annotations_path.write_text(
        json.dumps(annotations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    q4_ids = compute_q4(zip_path=chats)
    q4_path = extra_dir / "q4_chats_meeting_before_price.json"
    write_q4_result(q4_ids, q4_path)

    # notes — только ваши, из корневого answers.json; solve их сохранит
    answers_out = results_dir / "answers.json"
    root_answers = ROOT / "answers.json"
    if root_answers.is_file():
        shutil.copy2(root_answers, answers_out)
    else:
        answers_out.write_text(
            json.dumps({"notes": "", "run_command": "python solve.py"}, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )

    solve_py = ROOT / "solve.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(solve_py),
            str(data_dir),
            "--out",
            str(answers_out),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "solve.py завершился с ошибкой:\n"
            f"{completed.stderr or completed.stdout}"
        )

    return {
        "cleaned_crm": cleaned_path,
        "answers": answers_out,
        "q2": q2_path,
        "unidentified": unidentified_path,
        "annotations": annotations_path,
        "q4": q4_path,
    }
