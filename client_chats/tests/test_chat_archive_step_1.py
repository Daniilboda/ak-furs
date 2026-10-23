"""Шаг 1 этапа 4: чтение чатов из архива."""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chat_archive import list_chat_ids, read_chat_text, read_chats

DOCS_CHATS = Path(__file__).resolve().parents[2] / "docs" / "04_client_chats.zip"


def test_current_archive_has_c0001_to_c0150_continuous():
    ids = list_chat_ids(DOCS_CHATS)
    assert len(ids) == 150
    assert ids[0] == "C0001"
    assert ids[-1] == "C0150"
    assert ids == [f"C{i:04d}" for i in range(1, 151)]


def test_current_archive_chats_are_utf8_readable():
    chats = read_chats(DOCS_CHATS)
    assert len(chats) == 150
    assert "C0001" in chats
    assert chats["C0001"].startswith("Чат C0001")
    assert "Менеджер:" in chats["C0001"]
    assert "Клиент:" in chats["C0001"]


def test_each_txt_reads_from_substituted_zip(tmp_path: Path):
    path = tmp_path / "chats.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "chats/C0001.txt",
            "\ufeffЧат C0001 | клиент CL-1 | заказ A-1 | менеджер Тест\n"
            "[01.01.2025 10:00] Клиент: привет\n"
            "[01.01.2025 10:01] Менеджер: здравствуйте\n".encode("utf-8"),
        )
        archive.writestr(
            "chats/C0003.txt",
            "Чат C0003\n[01.01.2025 11:00] Менеджер: тест\n".encode("utf-8"),
        )
    ids = list_chat_ids(path)
    assert ids == ["C0001", "C0003"]
    chats = read_chats(path)
    assert chats["C0001"].startswith("Чат C0001")
    assert "привет" in chats["C0001"]
    with zipfile.ZipFile(path) as archive:
        text = read_chat_text(archive, "C0003")
        assert text.startswith("Чат C0003")


def test_non_utf8_chat_raises(tmp_path: Path):
    path = tmp_path / "bad.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("chats/C0001.txt", "Чаты".encode("cp1251"))
    with pytest.raises(ValueError, match="UTF-8"):
        read_chats(path)
