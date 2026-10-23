"""Шаг 2 этапа 2: сумма и тип операции."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bank_statement import (
    incoming_payments,
    is_incoming,
    normalize_operation_type,
    parse_amount,
    read_bank_statement,
)

DOCS_BANK = Path(__file__).resolve().parents[2] / "docs" / "02_bank_statement_rub.csv"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1 080 500,00", 1_080_500.0),
        ("445 000,00", 445_000.0),
        ("-445 000,00", -445_000.0),
        ("24 180,00", 24_180.0),
        ("299 750,00", 299_750.0),
    ],
)
def test_parse_amount_examples(raw: str, expected: float):
    assert parse_amount(raw) == expected


def test_parse_amount_rejects_garbage():
    with pytest.raises(ValueError, match="сумм"):
        parse_amount("не сумма")


def test_normalize_operation_type_incoming_and_outgoing():
    assert normalize_operation_type("Поступление") == "Поступление"
    assert normalize_operation_type("Списание") == "Списание"
    assert normalize_operation_type("  Поступление  ") == "Поступление"


def test_unknown_operation_type_raises():
    with pytest.raises(ValueError, match="тип"):
        normalize_operation_type("перевод")


def test_is_incoming_separates_types():
    assert is_incoming("Поступление") is True
    assert is_incoming("Списание") is False


def test_current_statement_amounts_and_types_parse():
    records = read_bank_statement(DOCS_BANK)
    assert records
    for record in records:
        parse_amount(record["Сумма"])
        normalize_operation_type(record["Тип"])
    incoming = incoming_payments(records)
    assert len(incoming) == sum(1 for r in records if r["Тип"].strip() == "Поступление")
    assert all(r["Тип"].strip() == "Поступление" for r in incoming)
    assert len(incoming) < len(records)
