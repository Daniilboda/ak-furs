"""CLI: предполагаемый ответ клиентке по нормализованному чату и cleaned CRM (Q5b)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from order_price import DEFAULT_CLEANED_CRM, format_rub
from proposed_reply import (
    DEFAULT_NORMALIZED_CHATS,
    DEFAULT_OUT_DIR,
    write_proposed_reply,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Собрать предполагаемый ответ клиентке: заказ из шапки нормализованного чата → "
            "цена за ед. из cleaned CRM → текст в стиле переписок ателье."
        )
    )
    parser.add_argument("--chat-id", default="C0010", help="ID чата, например C0010")
    parser.add_argument(
        "--chats-dir",
        type=Path,
        default=DEFAULT_NORMALIZED_CHATS,
        help="Папка с нормализованными Cxxxx.txt",
    )
    parser.add_argument("--crm", type=Path, default=DEFAULT_CLEANED_CRM)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)

    path, price = write_proposed_reply(
        args.chat_id,
        chats_dir=args.chats_dir,
        crm_path=args.crm,
        out_dir=args.out_dir,
    )
    print(
        json.dumps(
            {
                "chat_id": args.chat_id,
                "order_id": price.order_id,
                "article": price.article,
                "unit_price": str(price.unit_price),
                "unit_price_display": format_rub(price.unit_price),
                "out": str(path),
            },
            ensure_ascii=False,
        )
    )
    print(path.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
