"""Проверка чтения CRM и номера заказа (шаги 1–2)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crm_dedupe import CRM_HEADER, order_number, read_crm

DOCS_CRM = Path(__file__).resolve().parents[2] / "docs" / "01_crm_orders_export.csv"


def _write_crm(path: Path, data_rows: list[list[str]], *, encoding: str = "utf-8-sig", delimiter: str = ";") -> None:
    lines = [delimiter.join(CRM_HEADER)]
    lines.extend(delimiter.join(row) for row in data_rows)
    path.write_bytes("\n".join(lines).encode(encoding))


def test_current_export_opens_as_utf8_with_fourteen_columns():
    raw = DOCS_CRM.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    records = read_crm(DOCS_CRM)
    assert records
    assert set(records[0]) == set(CRM_HEADER)
    assert all(len(record) == 14 for record in records)


def test_read_does_not_depend_on_row_count(tmp_path: Path):
    path = tmp_path / "01_crm_orders_export.csv"
    _write_crm(
        path,
        [["A-00075", "1", "2026-01-01", "CL-1", "Ольга", "Сайт", "SOB-SH-01", "1", "100", "руб", "", "Оплачен", "", "2026-10-01 09:00"]],
    )
    records = read_crm(path)
    assert len(records) == 1
    assert records[0]["Номер заказа"] == "A-00075"


def test_read_rejects_non_utf8(tmp_path: Path):
    path = tmp_path / "01_crm_orders_export.csv"
    path.write_bytes("Номер заказа;№ строки\n".encode("cp1251"))
    with pytest.raises(ValueError, match="UTF-8"):
        read_crm(path)


def test_read_rejects_wrong_width(tmp_path: Path):
    path = tmp_path / "01_crm_orders_export.csv"
    _write_crm(path, [["только-одна-колонка"]])
    with pytest.raises(ValueError, match="колонок"):
        read_crm(path)


@pytest.mark.parametrize(
    "raw",
    ["A-00075", "А-75", "a-75", "A75", "75"],
)
def test_order_number_examples_from_spec(raw: str):
    assert order_number(raw) == 75


def test_order_number_strips_edge_spaces():
    assert order_number(" a-811") == 811


def test_order_number_rejects_text_without_digits():
    with pytest.raises(ValueError):
        order_number("заказ 75")


def test_current_export_order_numbers_parse():
    for record in read_crm(DOCS_CRM):
        order_number(record["Номер заказа"])
