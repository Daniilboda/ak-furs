"""Проверка канонического номера клиента."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crm_dedupe import apply_canonical_client_numbers, client_number, dedupe_order_lines, read_crm
from run_crm_cleanup import run_cleanup

DOCS_CRM = Path(__file__).resolve().parents[2] / "docs" / "01_crm_orders_export.csv"
DOCS_CATALOG = Path(__file__).resolve().parents[2] / "docs" / "03_catalog_prices_reference.xlsx"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("CL-00087", 87),
        ("CL 87", 87),
        ("cl00087", 87),
        ("КЛ-00087", 87),
        ("87", 87),
        ("CL-00777", 777),
        ("CL 536", 536),
        ("cl00544", 544),
    ],
)
def test_client_number_examples(raw: str, expected: int):
    assert client_number(raw) == expected


def test_apply_canonical_client_numbers_writes_digits_only():
    records = [{"Клиент": "CL-00087"}, {"Клиент": "cl00544"}]
    updated = apply_canonical_client_numbers(records)
    assert updated[0]["Клиент"] == "87"
    assert updated[1]["Клиент"] == "544"
    assert records[0]["Клиент"] == "CL-00087"


def test_current_export_clients_parse():
    for record in dedupe_order_lines(read_crm(DOCS_CRM)):
        client_number(record["Клиент"])


def test_cleanup_clients_are_digits_without_leading_zeros():
    records, _ = run_cleanup(DOCS_CRM, DOCS_CATALOG, only="all")
    for record in records:
        assert record["Клиент"].isdigit()
        assert record["Клиент"] == str(int(record["Клиент"]))
