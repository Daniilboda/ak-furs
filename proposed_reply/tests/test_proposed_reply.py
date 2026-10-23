"""Предполагаемый ответ клиентке: чат → заказ → order_price → текст."""

from __future__ import annotations

import csv
import sys
from decimal import Decimal
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parent
sys.path.insert(0, str(PACKAGE))
sys.path.insert(0, str(ROOT / "normilized_chats"))

from order_price import format_rub
from proposed_reply import (
    build_price_first_reply,
    lookup_order_price,
    order_id_from_chat,
    write_proposed_reply,
)
from run_proposed_reply import main

DOCS_NORM = ROOT / "normilized_chats" / "chats"
DOCS_CRM = ROOT / "crm_cleanup" / "normalized_crm" / "01_crm_orders_export_cleaned.csv"


def test_order_from_normalized_c0010():
    text = (DOCS_NORM / "C0010.txt").read_text(encoding="utf-8")
    assert order_id_from_chat(text) == "702"


def test_lookup_c0010_via_chat():
    price = lookup_order_price("C0010", chats_dir=DOCS_NORM, crm_path=DOCS_CRM)
    assert price.order_id == "702"
    assert price.unit_price == Decimal("252000.00")


def test_reply_style_matches_atelier_chats():
    price = lookup_order_price("C0010", chats_dir=DOCS_NORM, crm_path=DOCS_CRM)
    text = build_price_first_reply(price)
    assert text == (
        "Цена с учётом всех работ: 252 000 ₽.\n"
        "Возможна предоплата 30%, остальное при получении.\n"
    )
    assert format_rub(price.unit_price) in text


def test_write_and_cli(tmp_path: Path):
    out_dir = tmp_path / "out"
    path, price = write_proposed_reply(
        "C0010", chats_dir=DOCS_NORM, crm_path=DOCS_CRM, out_dir=out_dir
    )
    assert path.name == "proposed_reply_C0010.txt"
    assert "252 000" in path.read_text(encoding="utf-8")
    assert price.unit_price == Decimal("252000.00")

    other_crm = tmp_path / "crm.csv"
    with DOCS_CRM.open(encoding="utf-8-sig", newline="") as src:
        rows = list(csv.DictReader(src, delimiter=";"))
    fieldnames = list(rows[0].keys())
    for row in rows:
        if row["Номер заказа"] == "702":
            row["Цена за ед."] = "199000.00"
            row["Цена за ед. после скидки"] = "199000.00"
    with other_crm.open("w", encoding="utf-8-sig", newline="") as dst:
        writer = csv.DictWriter(dst, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    assert (
        main(
            [
                "--chat-id",
                "C0010",
                "--chats-dir",
                str(DOCS_NORM),
                "--crm",
                str(other_crm),
                "--out-dir",
                str(out_dir),
            ]
        )
        == 0
    )
    assert "199 000" in (out_dir / "proposed_reply_C0010.txt").read_text(encoding="utf-8")
