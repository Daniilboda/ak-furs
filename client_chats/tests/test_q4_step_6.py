"""Шаг 6 этапа 4: Q4 на подменённом архиве чатов."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from q4_select import compute_q4, main

DOCS_CHATS = Path(__file__).resolve().parents[2] / "docs" / "04_client_chats.zip"
DOCS_ANNOTATIONS = (
    Path(__file__).resolve().parents[1] / "results" / "chat_annotations.json"
)


def _chat_body(chat_id: str, *lines: str) -> bytes:
    header = f"Чат {chat_id} | клиент CL-1 | заказ A-1 | менеджер Тест"
    text = header + "\n" + "\n".join(lines) + "\n"
    return ("\ufeff" + text).encode("utf-8")


def _write_zip(path: Path, files: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)


def test_q4_on_substituted_zip(tmp_path: Path):
    """Новый zip: список ID считается заново, без зашитых ответов docs/."""
    zip_path = tmp_path / "interview_chats.zip"
    _write_zip(
        zip_path,
        {
            # приглашение раньше цены → Q4
            "chats/C0100.txt": _chat_body(
                "C0100",
                "[01.01.2025 10:00] Менеджер: Лучше приезжайте к нам в ателье на примерку!",
                "[01.01.2025 10:05] Клиент: Сколько стоит?",
                "[01.01.2025 10:10] Менеджер: Стоимость этой модели — 208.000 руб.",
            ),
            # цена раньше приглашения → не Q4
            "chats/C0200.txt": _chat_body(
                "C0200",
                "[01.01.2025 10:00] Менеджер: Цена с учётом всех работ: 53 000 ₽.",
                "[01.01.2025 10:05] Менеджер: Приглашаю на примерку в ателье — когда вам удобно?",
            ),
            # нет цены → не Q4
            "chats/C0300.txt": _chat_body(
                "C0300",
                "[01.01.2025 10:00] Менеджер: Давайте я запишу вас на встречу в шоурум.",
                "[01.01.2025 10:05] Клиент: А цена?",
            ),
            # пропись + приглашение после → не Q4
            "chats/C0400.txt": _chat_body(
                "C0400",
                "[01.01.2025 10:00] Менеджер: Цена с учётом всех работ: сто пятьдесят восемь тысяч рублей.",
                "[01.01.2025 10:05] Менеджер: Когда сможете подъехать на примерку?",
            ),
            # приглашение раньше, цена прописью → Q4
            "chats/C0500.txt": _chat_body(
                "C0500",
                "[01.01.2025 10:00] Менеджер: Когда сможете подъехать на примерку?",
                "[01.01.2025 10:05] Менеджер: Изначальная стоимость двести пятнадцать тысяч рублей.",
            ),
        },
    )
    ids = compute_q4(zip_path=zip_path)
    assert ids == ["C0100", "C0500"]
    assert isinstance(ids, list)
    assert all(isinstance(x, str) and x.startswith("C") for x in ids)


def test_substituted_differs_from_current_docs():
    current = compute_q4(annotations_path=DOCS_ANNOTATIONS)
    assert len(current) == 21
    assert current != ["C0100", "C0500"]
    # пересчёт из текущего zip даёт тот же список, что из разметки
    from_zip = compute_q4(zip_path=DOCS_CHATS)
    assert from_zip == current


def test_cli_on_substituted_zip_writes_list(tmp_path: Path, capsys):
    zip_path = tmp_path / "new_chats.zip"
    out = tmp_path / "q4.json"
    _write_zip(
        zip_path,
        {
            "chats/C0007.txt": _chat_body(
                "C0007",
                "[01.01.2025 10:00] Менеджер: Приглашаю на примерку в ателье — когда вам удобно?",
                "[01.01.2025 10:05] Менеджер: Стоимость этой модели — 100 000 ₽.",
            ),
        },
    )
    assert main(["--zip", str(zip_path), "--out", str(out)]) == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["q4_chats_meeting_before_price"] == ["C0007"]
    assert payload["count"] == 1
    printed = json.loads(capsys.readouterr().out.strip())
    assert printed["q4_chats_meeting_before_price"] == ["C0007"]
