"""Проверка удаления дублей строк (шаг 4)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crm_dedupe import CRM_HEADER, dedupe_order_lines, exported_at, line_number, order_number, read_crm

DOCS_CRM = Path(__file__).resolve().parents[2] / "docs" / "01_crm_orders_export.csv"


def _record(**overrides: str) -> dict[str, str]:
    record = {column: "" for column in CRM_HEADER}
    record.update(
        {
            "Номер заказа": "A-00372",
            "№ строки": "1",
            "Артикул": "RYS-ZH-01",
            "Цена за ед.": "125000,00",
            "Статус": "отменен",
            "Выгружено": "2026-09-27 23:26",
        }
    )
    record.update(overrides)
    return record


def _write_crm(path: Path, records: list[dict[str, str]]) -> None:
    lines = [";".join(CRM_HEADER)]
    lines.extend(";".join(record[column] for column in CRM_HEADER) for record in records)
    path.write_text("\n".join(lines), encoding="utf-8-sig")


def test_duplicate_pair_keeps_later_export():
    earlier = _record()
    later = _record(**{"Номер заказа": " a-372", "Цена за ед.": "159 000", "Выгружено": "2026-10-01 09:28"})
    kept = dedupe_order_lines([earlier, later])
    assert len(kept) == 1
    assert kept[0]["Цена за ед."] == "159 000"
    assert kept[0]["Выгружено"] == "2026-10-01 09:28"


def test_identical_rows_with_same_time_collapse_to_one():
    row = _record(**{"Номер заказа": " a-889", "Выгружено": "2026-10-01 09:40", "Цена за ед.": "288000"})
    kept = dedupe_order_lines([row, dict(row)])
    assert kept == [row]


def test_same_time_with_different_fields_stops():
    first = _record(**{"Выгружено": "2026-10-01 09:40", "Цена за ед.": "100"})
    second = _record(**{"Выгружено": "2026-10-01 09:40", "Цена за ед.": "200"})
    with pytest.raises(ValueError, match="поля различаются"):
        dedupe_order_lines([first, second])


def test_leading_zero_in_line_number_is_the_same_line():
    earlier = _record(**{"№ строки": "1", "Цена за ед.": "100", "Выгружено": "2026-09-27 23:26"})
    later = _record(**{"№ строки": "01", "Цена за ед.": "159 000", "Выгружено": "2026-10-01 09:28"})
    kept = dedupe_order_lines([earlier, later])
    assert len(kept) == 1
    assert kept[0]["№ строки"] == "01"
    assert kept[0]["Цена за ед."] == "159 000"


def test_different_line_numbers_stay_separate():
    kept = dedupe_order_lines([_record(**{"№ строки": "1"}), _record(**{"№ строки": "2"})])
    assert [record["№ строки"] for record in kept] == ["1", "2"]


def test_dedupe_runs_on_substituted_folder(tmp_path: Path):
    path = tmp_path / "01_crm_orders_export.csv"
    earlier = _record()
    later = _record(**{"Цена за ед.": "159 000", "Выгружено": "2026-10-01 09:28"})
    _write_crm(path, [earlier, later])
    kept = dedupe_order_lines(read_crm(path))
    assert len(kept) == 1
    assert kept[0]["Выгружено"] == "2026-10-01 09:28"


def test_current_export_has_one_row_per_order_line():
    records = read_crm(DOCS_CRM)
    kept = dedupe_order_lines(records)
    keys = [
        (order_number(record["Номер заказа"]), line_number(record["№ строки"]))
        for record in kept
    ]
    assert len(keys) == len(set(keys))
    latest_by_key = {}
    for record in records:
        key = (order_number(record["Номер заказа"]), line_number(record["№ строки"]))
        moment = exported_at(record["Выгружено"])
        if key not in latest_by_key or moment > latest_by_key[key]:
            latest_by_key[key] = moment
    assert len(kept) == len(latest_by_key)
    for record in kept:
        key = (order_number(record["Номер заказа"]), line_number(record["№ строки"]))
        assert exported_at(record["Выгружено"]) == latest_by_key[key]
