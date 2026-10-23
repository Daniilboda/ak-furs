"""Шаг 1 этапа 2: чтение банковской выписки."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bank_statement import BANK_HEADER, REQUIRED_COLUMNS, read_bank_statement

DOCS_BANK = Path(__file__).resolve().parents[2] / "docs" / "02_bank_statement_rub.csv"


def _write_bank(
    path: Path,
    data_rows: list[list[str]],
    *,
    encoding: str = "cp1251",
    account_line: str = "Выписка по счёту 40702810XXXXXXXX1234;;;;;;",
) -> None:
    lines = [account_line, ";".join(BANK_HEADER)]
    lines.extend(";".join(row) for row in data_rows)
    path.write_bytes("\n".join(lines).encode(encoding))


def test_current_statement_opens_as_cp1251_with_required_columns():
    raw = DOCS_BANK.read_bytes()
    with pytest.raises(UnicodeDecodeError):
        raw.decode("utf-8")
    records = read_bank_statement(DOCS_BANK)
    assert records
    assert set(records[0]) == set(BANK_HEADER)
    for name in REQUIRED_COLUMNS:
        assert name in records[0]
    assert all(len(record) == len(BANK_HEADER) for record in records)


def test_read_skips_account_line_and_does_not_depend_on_row_count(tmp_path: Path):
    path = tmp_path / "02_bank_statement_rub.csv"
    _write_bank(
        path,
        [
            [
                "02.01.2025",
                "12:27",
                "445 000,00",
                "RUR",
                "Поступление",
                "Новикова Д.",
                "Предоплата заказ 775",
            ]
        ],
    )
    records = read_bank_statement(path)
    assert len(records) == 1
    assert records[0]["Дата операции"] == "02.01.2025"
    assert records[0]["Сумма"] == "445 000,00"
    assert records[0]["Тип"] == "Поступление"
    assert records[0]["Назначение платежа"] == "Предоплата заказ 775"


def test_read_rejects_non_cp1251(tmp_path: Path):
    path = tmp_path / "02_bank_statement_rub.csv"
    # 0x98 в Windows-1251 не определён — decode должен упасть.
    path.write_bytes(b"\x98\n" + ";".join(BANK_HEADER).encode("cp1251"))
    with pytest.raises(ValueError, match="Windows-1251"):
        read_bank_statement(path)


def test_read_rejects_wrong_header(tmp_path: Path):
    path = tmp_path / "bad.csv"
    path.write_bytes(
        "счёт;;;;;;\nДата;Сумма;Тип;Назначение\n".encode("cp1251")
    )
    with pytest.raises(ValueError, match="колонки"):
        read_bank_statement(path)


def test_read_rejects_wrong_width(tmp_path: Path):
    path = tmp_path / "02_bank_statement_rub.csv"
    _write_bank(path, [["только-одна-колонка"]])
    with pytest.raises(ValueError, match="колонок"):
        read_bank_statement(path)
