"""Этап 06, шаг 1: answers.json строго по ключам шаблона."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data" / "answers_template.json"
ANSWERS = ROOT / "answers.json"

REQUIRED_KEYS = [
    "q1_unique_orders",
    "q1_unique_order_lines",
    "q2a_paid_orders_without_payment",
    "q2b_unidentified_payments_count",
    "q2b_unidentified_payments_sum_rub",
    "q3_price_violation_lines_total",
    "q3_price_violation_lines_by_manager",
    "q4_chats_meeting_before_price",
    "run_command",
    "notes",
]


def test_answers_json_exists_and_is_not_the_template():
    assert ANSWERS.is_file()
    assert ANSWERS.resolve() != TEMPLATE.resolve()


def test_answers_keys_match_template():
    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    answers = json.loads(ANSWERS.read_text(encoding="utf-8"))
    assert list(answers.keys()) == list(template.keys())
    assert set(answers.keys()) == set(REQUIRED_KEYS)


def test_answers_value_types():
    answers = json.loads(ANSWERS.read_text(encoding="utf-8"))
    assert isinstance(answers["q1_unique_orders"], int)
    assert isinstance(answers["q1_unique_order_lines"], int)
    assert isinstance(answers["q2a_paid_orders_without_payment"], list)
    assert all(isinstance(x, int) for x in answers["q2a_paid_orders_without_payment"])
    assert isinstance(answers["q2b_unidentified_payments_count"], int)
    assert isinstance(answers["q2b_unidentified_payments_sum_rub"], (int, float))
    assert isinstance(answers["q3_price_violation_lines_total"], int)
    assert isinstance(answers["q3_price_violation_lines_by_manager"], dict)
    assert all(isinstance(k, str) for k in answers["q3_price_violation_lines_by_manager"])
    assert all(isinstance(v, int) for v in answers["q3_price_violation_lines_by_manager"].values())
    assert isinstance(answers["q4_chats_meeting_before_price"], list)
    assert all(isinstance(x, str) for x in answers["q4_chats_meeting_before_price"])
    assert isinstance(answers["run_command"], str)
    assert isinstance(answers["notes"], str)
