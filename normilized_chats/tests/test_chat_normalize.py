"""Нормализация шапок чатов (клиент / заказ / менеджер)."""

from __future__ import annotations

import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parent
sys.path.insert(0, str(PACKAGE))
sys.path.insert(0, str(ROOT / "crm_cleanup"))

from chat_normalize import (
    normalize_chat_header_line,
    normalize_chat_text,
    normalize_from_dir,
    normalize_from_zip,
)
from crm_normalize import load_manager_aliases
from run_chat_normalize import main

DOCS_ZIP = ROOT / "docs" / "04_client_chats.zip"
DOCS_CATALOG = ROOT / "docs" / "03_catalog_prices_reference.xlsx"


def test_header_client_order_manager_canonical():
    aliases = load_manager_aliases(DOCS_CATALOG)
    line = "Чат C0010 | клиент cl00608 | заказ A-00702 | менеджер М.Котова"
    assert (
        normalize_chat_header_line(line, aliases)
        == "Чат C0010 | клиент 608 | заказ 702 | менеджер Марина Котова"
    )


def test_body_unchanged():
    aliases = load_manager_aliases(DOCS_CATALOG)
    text = (
        "Чат C0001 | клиент CL 87 | заказ A75 | менеджер Полина\n"
        "[01.01.2025 10:00] Клиент: Сколько стоит?\n"
        "[01.01.2025 10:05] Менеджер: Уточните размер.\n"
    )
    out = normalize_chat_text(text, aliases)
    assert out.startswith("Чат C0001 | клиент 87 | заказ 75 | менеджер Полина Орлова\n")
    assert "[01.01.2025 10:00] Клиент: Сколько стоит?" in out
    assert "Уточните размер." in out


def test_normalize_from_zip_writes_folder(tmp_path: Path):
    out = tmp_path / "normalized"
    result = normalize_from_zip(DOCS_ZIP, DOCS_CATALOG, out)
    assert len(result) == 150
    c0010 = (out / "chats" / "C0010.txt").read_text(encoding="utf-8")
    assert c0010.splitlines()[0] == (
        "Чат C0010 | клиент 608 | заказ 702 | менеджер Марина Котова"
    )


def test_normalize_from_dir_for_several_files(tmp_path: Path):
    src = tmp_path / "incoming"
    src.mkdir()
    (src / "C0007.txt").write_text(
        "Чат C0007 | клиент cl00001 | заказ А-9 | менеджер olga.e\n"
        "[01.01.2025 10:00] Менеджер: Здравствуйте!\n",
        encoding="utf-8",
    )
    (src / "C0008.txt").write_text(
        "Чат C0008 | клиент КЛ-00002 | заказ a10 | менеджер Алина\n"
        "[01.01.2025 11:00] Клиент: Добрый день\n",
        encoding="utf-8",
    )
    out = tmp_path / "out"
    result = normalize_from_dir(src, DOCS_CATALOG, out)
    assert set(result) == {"C0007", "C0008"}
    assert (out / "chats" / "C0007.txt").read_text(encoding="utf-8").splitlines()[
        0
    ] == "Чат C0007 | клиент 1 | заказ 9 | менеджер Ольга Ершова"


def test_cli_default_zip(tmp_path: Path):
    out = tmp_path / "norm"
    assert main(["--zip", str(DOCS_ZIP), "--catalog", str(DOCS_CATALOG), "--out-dir", str(out)]) == 0
    assert (out / "chats" / "C0010.txt").is_file()
