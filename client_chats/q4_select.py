"""Отбор чатов Q4: приглашение менеджера раньше цены (этап 4, шаг 5)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from annotate_chats import annotate_turns, build_annotations
from chat_turns import Turn, parse_chat_turns

ROOT = Path(__file__).resolve().parent
DEFAULT_ANNOTATIONS = ROOT / "results" / "chat_annotations.json"
DEFAULT_ZIP = ROOT.parent / "docs" / "04_client_chats.zip"
DEFAULT_OUT = ROOT / "results" / "q4_chats_meeting_before_price.json"


def chat_is_q4(annotation: dict) -> bool:
    """Чат в Q4, если у менеджера есть и приглашение, и цена, и приглашение раньше."""
    return bool(annotation.get("meeting_before_price"))


def q4_ids_from_annotations(payload: dict) -> list[str]:
    """Список ID из готовой разметки, по возрастанию номера."""
    chats = payload.get("chats") or []
    ids = [row["chat_id"] for row in chats if chat_is_q4(row)]
    return sorted(ids, key=lambda chat_id: int(str(chat_id)[1:]))


def q4_from_turns(turns: list[Turn]) -> bool:
    """Q4 по разобранным репликам одного чата (та же логика, что в разметке)."""
    return chat_is_q4(annotate_turns(turns))


def q4_from_chat_text(chat_text: str) -> bool:
    return q4_from_turns(parse_chat_turns(chat_text))


def load_annotations(path: Path | str) -> dict:
    file_path = Path(path)
    return json.loads(file_path.read_text(encoding="utf-8"))


def compute_q4(
    *,
    annotations_path: Path | str | None = None,
    zip_path: Path | str | None = None,
) -> list[str]:
    """
    Список ID для answers.json.
    Если есть файл разметки — читаем его; иначе строим разметку из zip.
    """
    if annotations_path is not None:
        return q4_ids_from_annotations(load_annotations(annotations_path))
    if zip_path is not None:
        return q4_ids_from_annotations(build_annotations(zip_path))
    raise ValueError("нужен annotations_path или zip_path")


def write_q4_result(ids: list[str], out_path: Path | str) -> Path:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"q4_chats_meeting_before_price": ids, "count": len(ids)}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Q4: чаты, где приглашение раньше цены")
    parser.add_argument(
        "--annotations",
        type=Path,
        default=DEFAULT_ANNOTATIONS,
        help="Готовая разметка chat_annotations.json",
    )
    parser.add_argument(
        "--zip",
        type=Path,
        default=None,
        help="Если указан — пересчитать разметку из zip и взять Q4 из неё (annotations игнор.)",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    if args.zip is not None:
        ids = compute_q4(zip_path=args.zip)
    else:
        ids = compute_q4(annotations_path=args.annotations)

    out = write_q4_result(ids, args.out)
    print(json.dumps({"count": len(ids), "q4_chats_meeting_before_price": ids}, ensure_ascii=False))
    print(f"saved={out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
