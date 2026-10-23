"""Предполагаемый ответ клиентке (Q5b): заказ из нормализованного чата + цена из order_price."""

from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_NORM = _ROOT / "normilized_chats"
if str(_NORM) not in sys.path:
    sys.path.insert(0, str(_NORM))

from chat_normalize import parse_chat_header  # noqa: E402

from order_price import (  # noqa: E402
    DEFAULT_CLEANED_CRM,
    OrderPrice,
    format_rub,
    order_price_from_crm,
)

DEFAULT_NORMALIZED_CHATS = _ROOT / "normilized_chats" / "chats"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent

# Как в живых ответах на «А цену можно сначала?» (C0033, C0042, C0092)
PAYMENT_LINE = "Возможна предоплата 30%, остальное при получении."


def load_normalized_chat(chat_id: str, chats_dir: Path | str) -> str:
    path = Path(chats_dir) / f"{chat_id}.txt"
    if not path.is_file():
        raise FileNotFoundError(f"нет нормализованного чата: {path}")
    return path.read_text(encoding="utf-8-sig")


def order_id_from_chat(chat_text: str) -> str:
    """Номер заказа из шапки нормализованного чата (уже числом)."""
    header = chat_text.splitlines()[0]
    parts = parse_chat_header(header)
    order = parts["order"].strip()
    if not re.fullmatch(r"\d+", order):
        raise ValueError(f"в нормализованной шапке заказ должен быть числом: {order!r}")
    return order


def lookup_order_price(
    chat_id: str,
    *,
    chats_dir: Path | str = DEFAULT_NORMALIZED_CHATS,
    crm_path: Path | str = DEFAULT_CLEANED_CRM,
) -> OrderPrice:
    """Чат → номер заказа → цена из cleaned CRM."""
    chat_text = load_normalized_chat(chat_id, chats_dir)
    order_id = order_id_from_chat(chat_text)
    return order_price_from_crm(order_id, crm_path=crm_path)


def build_price_first_reply(price: OrderPrice) -> str:
    """Короткий предполагаемый ответ в стиле менеджеров на «А цену можно сначала?»."""
    line = f"Цена с учётом всех работ: {format_rub(price.unit_price)}."
    return f"{line}\n{PAYMENT_LINE}\n"


def build_proposed_reply(
    chat_id: str,
    *,
    chats_dir: Path | str = DEFAULT_NORMALIZED_CHATS,
    crm_path: Path | str = DEFAULT_CLEANED_CRM,
) -> tuple[str, OrderPrice]:
    price = lookup_order_price(chat_id, chats_dir=chats_dir, crm_path=crm_path)
    return build_price_first_reply(price), price


def reply_output_path(chat_id: str, out_dir: Path | str = DEFAULT_OUT_DIR) -> Path:
    return Path(out_dir) / f"proposed_reply_{chat_id}.txt"


def write_proposed_reply(
    chat_id: str,
    *,
    chats_dir: Path | str = DEFAULT_NORMALIZED_CHATS,
    crm_path: Path | str = DEFAULT_CLEANED_CRM,
    out_dir: Path | str = DEFAULT_OUT_DIR,
) -> tuple[Path, OrderPrice]:
    text, price = build_proposed_reply(chat_id, chats_dir=chats_dir, crm_path=crm_path)
    path = reply_output_path(chat_id, out_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path, price
