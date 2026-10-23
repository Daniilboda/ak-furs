"""Шаг 7 этапа 2: Q2 на подменённых заказах и выписке."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "crm_cleanup"))

from bank_q2 import compute_q2, compute_q2_from_cleaned
from bank_statement import BANK_HEADER
from crm_dedupe import CRM_HEADER
from run_bank_reconcile import main
from run_crm_cleanup import cleaned_output_name, run_cleanup, write_crm_csv

DOCS_CATALOG = Path(__file__).resolve().parents[2] / "docs" / "03_catalog_prices_reference.xlsx"
DOCS_CRM = Path(__file__).resolve().parents[2] / "docs" / "01_crm_orders_export.csv"
DOCS_BANK = Path(__file__).resolve().parents[2] / "docs" / "02_bank_statement_rub.csv"


def _write_crm(path: Path, rows: list[list[str]]) -> None:
    lines = [";".join(CRM_HEADER)]
    lines.extend(";".join(row) for row in rows)
    path.write_text("\n".join(lines), encoding="utf-8-sig")


def _crm_row(order: str, *, status: str = "Оплачен") -> list[str]:
    values = {column: "" for column in CRM_HEADER}
    values.update(
        {
            "Номер заказа": order,
            "№ строки": "1",
            "Дата создания": "01.01.2025",
            "Клиент": "CL-1",
            "Менеджер": "olga.e",
            "Источник": "Сайт",
            "Артикул": "SOB-SH-01",
            "Кол-во": "1",
            "Цена за ед.": "10000",
            "Валюта": "руб",
            "Скидка": "",
            "Статус": status,
            "Выгружено": "2026-10-01 09:00",
        }
    )
    return [values[column] for column in CRM_HEADER]


def _write_bank(path: Path, data_rows: list[list[str]]) -> None:
    lines = [
        "Выписка по счёту TEST;;;;;;",
        ";".join(BANK_HEADER),
    ]
    lines.extend(";".join(row) for row in data_rows)
    path.write_bytes("\n".join(lines).encode("cp1251"))


def _bank_row(amount: str, purpose: str, *, op_type: str = "Поступление") -> list[str]:
    return [
        "01.01.2025",
        "12:00",
        amount,
        "RUR",
        op_type,
        "Тест",
        purpose,
    ]


def test_compute_q2_on_substituted_files(tmp_path: Path):
    crm_path = tmp_path / "interview_crm.csv"
    bank_path = tmp_path / "interview_bank.csv"
    _write_crm(
        crm_path,
        [
            _crm_row("A-00010", status="PAID"),
            _crm_row("A-00020", status="оплачено"),
            _crm_row("A-00030", status="NEW"),
        ],
    )
    _write_bank(
        bank_path,
        [
            _bank_row("1 000,00", "A20 доплата"),
            _bank_row("500,00", "Перевод"),
            _bank_row("250,00", "заказ 999"),
            _bank_row("100,00", "A10", op_type="Списание"),
        ],
    )
    result = compute_q2(crm_path, bank_path, DOCS_CATALOG)
    assert result["q2a_paid_orders_without_payment"] == [10]
    assert result["q2b_unidentified_payments_count"] == 2
    assert result["q2b_unidentified_payments_sum_rub"] == 750.0
    assert isinstance(result["q2a_paid_orders_without_payment"], list)
    assert all(isinstance(x, int) for x in result["q2a_paid_orders_without_payment"])


def test_substituted_result_differs_from_current_docs():
    current = compute_q2(DOCS_CRM, DOCS_BANK, DOCS_CATALOG)
    assert current["q2b_unidentified_payments_count"] == 16
    assert current["q2a_paid_orders_without_payment"] != [10]


def test_cli_on_temp_folder_prints_json(tmp_path: Path, capsys):
    raw_crm = tmp_path / "interview_crm.csv"
    bank_path = tmp_path / "interview_bank.csv"
    out_csv = tmp_path / "q2_reconciliation.csv"
    unidentified_csv = tmp_path / "unidentified_incoming.csv"
    _write_crm(raw_crm, [_crm_row("A-5", status="Оплачен")])
    cleaned_records, _ = run_cleanup(raw_crm, DOCS_CATALOG)
    cleaned_path = tmp_path / cleaned_output_name(raw_crm)
    write_crm_csv(cleaned_path, cleaned_records)
    _write_bank(bank_path, [_bank_row("10,00", "без заказа")])
    code = main(
        [
            "--crm",
            str(cleaned_path),
            "--bank",
            str(bank_path),
            "--out",
            str(out_csv),
            "--unidentified-out",
            str(unidentified_csv),
        ]
    )
    assert code == 0
    stdout = capsys.readouterr().out
    payload = json.loads(stdout.split("saved=")[0])
    assert payload["q2a_paid_orders_without_payment"] == [5]
    assert payload["q2b_unidentified_payments_count"] == 1
    assert payload["q2b_unidentified_payments_sum_rub"] == 10.0
    assert out_csv.is_file()
    text = out_csv.read_text(encoding="utf-8-sig")
    assert "q2b_unidentified_payments_count" in text
    assert "unidentified_incoming" in text
    assert "без заказа" in text
    assert "Причина" in text
    assert unidentified_csv.is_file()
    assert "без заказа" in unidentified_csv.read_text(encoding="utf-8-sig")


def test_compute_q2_from_cleaned_matches_raw_pipeline(tmp_path: Path):
    raw_crm = tmp_path / "crm.csv"
    bank_path = tmp_path / "bank.csv"
    _write_crm(
        raw_crm,
        [
            _crm_row("A-00010", status="PAID"),
            _crm_row("A-00020", status="оплачено"),
        ],
    )
    _write_bank(
        bank_path,
        [
            _bank_row("1 000,00", "A20 доплата"),
            _bank_row("500,00", "Перевод"),
        ],
    )
    cleaned, _ = run_cleanup(raw_crm, DOCS_CATALOG)
    cleaned_path = tmp_path / "crm_cleaned.csv"
    write_crm_csv(cleaned_path, cleaned)
    from_raw = compute_q2(raw_crm, bank_path, DOCS_CATALOG)
    from_cleaned = compute_q2_from_cleaned(cleaned_path, bank_path)
    assert from_cleaned["q2a_paid_orders_without_payment"] == from_raw["q2a_paid_orders_without_payment"]
    assert from_cleaned["q2b_unidentified_payments_count"] == from_raw["q2b_unidentified_payments_count"]
    assert from_cleaned["q2b_unidentified_payments_sum_rub"] == from_raw["q2b_unidentified_payments_sum_rub"]


def test_cleanup_still_runs_inside_compute_q2(tmp_path: Path):
    crm_path = tmp_path / "crm.csv"
    bank_path = tmp_path / "bank.csv"
    _write_crm(crm_path, [_crm_row("A-00007", status="PAID")])
    _write_bank(bank_path, [_bank_row("1,00", "A7 доплата")])
    cleaned, _ = run_cleanup(crm_path, DOCS_CATALOG)
    assert cleaned[0]["Номер заказа"] == "7"
    assert cleaned[0]["Статус"] == "Оплачен"
    result = compute_q2(crm_path, bank_path, DOCS_CATALOG)
    assert result["q2a_paid_orders_without_payment"] == []
    assert result["q2b_unidentified_payments_count"] == 0
