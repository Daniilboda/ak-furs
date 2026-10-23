"""Разметка чатов (цены и приглашения) — логика согласована агентом Cursor.

Пишет client_chats/results/chat_annotations.json.
Исходный zip не изменяет. Без внешнего API.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from chat_archive import read_chats
from chat_turns import Turn, manager_turns, parse_chat_turns

ROOT = Path(__file__).resolve().parent
DEFAULT_ZIP = ROOT.parent / "docs" / "04_client_chats.zip"
DEFAULT_OUT = ROOT / "results" / "chat_annotations.json"

# --- цена изделия (не платежи / часы) ---
_PRICE_CUE = re.compile(
    r"(?i)(?:"
    r"цен[аыуе]\s+с\s+уч[её]том"
    r"|стоимост"
    r"|итоговая"
    r"|специальн\w*\s+цен"
    r"|цен[аыуе]\s*:"
    r")"
)
_AMOUNT = re.compile(
    r"(?i)(?:\d.*(?:руб|₽|тыс|млн)|(?:руб|₽|тыс|млн).*\d|тысяч|миллион)"
)

# --- приглашение на встречу / примерку ---
_INVITE = re.compile(
    r"(?i)(?:"
    r"приглашаю\s+на\s+примерку"
    r"|на\s+примерку\b"
    r"|примерку\b"
    r"|запишу\s+вас\s+на\s+встречу"
    r"|на\s+встречу\s+в\s+шоурум"
    r"|приезжайте\s+к\s+нам"
    r"|подъехать\s+на\s+примерку"
    r")"
)
# адрес/режим без приглашения
_NOT_INVITE = re.compile(
    r"(?i)(?:"
    r"наш\s+шоурум\s+находится"
    r"|работаем\s+ежедневно"
    r"|шьём\s+в\s+нашем\s+ателье"
    r"|мерки\s+снимаем"
    r")"
)


def is_price_line(text: str) -> bool:
    return _PRICE_CUE.search(text) is not None and _AMOUNT.search(text) is not None


def is_invite_line(text: str) -> bool:
    if _NOT_INVITE.search(text) and _INVITE.search(text) is None:
        return False
    # чистый адрес без «примерк/встреч/приезжа»
    if _NOT_INVITE.search(text) and not re.search(
        r"(?i)(примерк|встреч|приезжа|подъеха|приглаш|запишу)", text
    ):
        return False
    return _INVITE.search(text) is not None


def annotate_turns(turns: list[Turn]) -> dict:
    price_idx = None
    price_text = None
    invite_idx = None
    invite_text = None
    for turn in manager_turns(turns):
        if price_idx is None and is_price_line(turn.text):
            price_idx = turn.index
            price_text = turn.text
        if invite_idx is None and is_invite_line(turn.text):
            invite_idx = turn.index
            invite_text = turn.text
        if price_idx is not None and invite_idx is not None:
            break
    meeting_before_price = (
        invite_idx is not None
        and price_idx is not None
        and invite_idx < price_idx
    )
    return {
        "first_price_index": price_idx,
        "first_price_text": price_text,
        "first_invite_index": invite_idx,
        "first_invite_text": invite_text,
        "meeting_before_price": meeting_before_price,
    }


def build_annotations(zip_path: Path | str) -> dict:
    chats = read_chats(zip_path)
    items = []
    for chat_id in sorted(chats, key=lambda x: int(x[1:])):
        turns = parse_chat_turns(chats[chat_id])
        row = {"chat_id": chat_id, **annotate_turns(turns)}
        items.append(row)
    return {
        "source_zip": str(zip_path),
        "annotator": "cursor_agent",
        "note": (
            "Разметка цен и приглашений выполнена агентом Cursor по репликам менеджера; "
            "результат сохранён для стабильного Q4. Клиентские суммы не учитываются."
        ),
        "chats": items,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Разметка чатов для Q4")
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    payload = build_annotations(args.zip)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    q4 = [c["chat_id"] for c in payload["chats"] if c["meeting_before_price"]]
    no_price = [c["chat_id"] for c in payload["chats"] if c["first_price_index"] is None]
    no_invite = [c["chat_id"] for c in payload["chats"] if c["first_invite_index"] is None]
    print(f"saved={args.out}")
    print(f"chats={len(payload['chats'])}")
    print(f"q4_meeting_before_price={len(q4)}")
    print(f"no_price={no_price}")
    print(f"no_invite_count={len(no_invite)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
