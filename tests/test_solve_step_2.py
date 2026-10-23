"""Этап 06, шаг 2: одна команда пересчитывает answers.json из сырых файлов."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOLVE = ROOT / "solve.py"
DATA = ROOT / "data"
ANSWERS = ROOT / "answers.json"
TEMPLATE = ROOT / "data" / "answers_template.json"


def test_build_answers_matches_current_data():
    sys.path.insert(0, str(ROOT))
    from solve import RUN_COMMAND, build_answers

    payload = build_answers(DATA)
    assert list(payload.keys()) == list(json.loads(TEMPLATE.read_text(encoding="utf-8")).keys())
    assert payload["q1_unique_orders"] == 1000
    assert payload["q1_unique_order_lines"] == 1368
    assert payload["q2a_paid_orders_without_payment"] == [12, 59, 84, 221, 600, 805, 827, 857, 993]
    assert payload["q2b_unidentified_payments_count"] == 16
    assert payload["q2b_unidentified_payments_sum_rub"] == 3437100.0
    assert payload["q3_price_violation_lines_total"] == 68
    assert payload["q3_price_violation_lines_by_manager"]["Полина Орлова"] == 42
    assert len(payload["q4_chats_meeting_before_price"]) == 21
    assert payload["run_command"] == RUN_COMMAND
    assert payload["notes"] == ""


def test_cli_preserves_manual_notes(tmp_path: Path):
    out = tmp_path / "answers.json"
    out.write_text(
        json.dumps({"notes": "мои толкования вручную"}, ensure_ascii=False),
        encoding="utf-8",
    )
    cmd = [sys.executable, str(SOLVE), str(DATA), "--out", str(out)]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=str(ROOT), env=env)
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["notes"] == "мои толкования вручную"
    assert payload["q1_unique_orders"] == 1000


def test_cli_writes_answers_and_is_idempotent(tmp_path: Path):
    out = tmp_path / "answers.json"
    cmd = [sys.executable, str(SOLVE), str(DATA), "--out", str(out)]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=str(ROOT), env=env)
    first = out.read_text(encoding="utf-8")
    subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=str(ROOT), env=env)
    second = out.read_text(encoding="utf-8")
    assert first == second
    payload = json.loads(first)
    assert payload["q1_unique_orders"] == 1000
    assert "q4_chats_meeting_before_price" in payload
