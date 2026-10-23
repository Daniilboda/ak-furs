"""Прогнать UI/testdata через /api/process и проверить ответы."""

from __future__ import annotations

import json
import shutil
import urllib.request
from pathlib import Path
from urllib.request import Request

BASE = Path(__file__).resolve().parent / "testdata"
API = "http://127.0.0.1:5050"
OUT = BASE / "out_from_api"


def _multipart(files: dict[str, Path]) -> tuple[bytes, str]:
    boundary = "----AkFursBoundary7MA4YWxk"
    chunks: list[bytes] = []
    for field, path in files.items():
        header = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field}"; filename="{path.name}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode()
        chunks.append(header + path.read_bytes() + b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), boundary


def main() -> int:
    mapping = {
        "crm": BASE / "01_crm_orders_export.csv",
        "bank": BASE / "02_bank_statement_rub.csv",
        "catalog": BASE / "03_catalog_prices_reference.xlsx",
        "chats": BASE / "04_client_chats.zip",
    }
    missing = [p.name for p in mapping.values() if not p.is_file()]
    if missing:
        raise SystemExit(f"нет файлов testdata: {missing}; сначала: python UI/build_testdata.py")

    body, boundary = _multipart(mapping)
    req = Request(f"{API}/api/process", data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {err.code}: {detail}") from err

    assert payload.get("ok"), payload
    print("API ok, job:", payload["job_id"])

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    for group in ("main", "additional"):
        for item in payload[group]:
            url = API + item["url"]
            dest = OUT / item["name"]
            dest.write_bytes(urllib.request.urlopen(url).read())
            print(f"  {group}: {dest.name} ({dest.stat().st_size} bytes)")

    answers = json.loads((OUT / "answers.json").read_text(encoding="utf-8"))
    print("Q1", answers["q1_unique_orders"], answers["q1_unique_order_lines"])
    print("Q2a", answers["q2a_paid_orders_without_payment"])
    print(
        "Q2b",
        answers["q2b_unidentified_payments_count"],
        answers["q2b_unidentified_payments_sum_rub"],
    )
    print(
        "Q3",
        answers["q3_price_violation_lines_total"],
        answers["q3_price_violation_lines_by_manager"],
    )
    print("Q4", answers["q4_chats_meeting_before_price"])

    assert answers["q1_unique_orders"] == 5
    assert answers["q1_unique_order_lines"] == 5
    assert 9002 in answers["q2a_paid_orders_without_payment"]
    assert answers["q2b_unidentified_payments_count"] == 2
    assert answers["q2b_unidentified_payments_sum_rub"] == 83000.0
    assert answers["q3_price_violation_lines_total"] == 1
    assert answers["q3_price_violation_lines_by_manager"] == {"Ольга Ершова": 1}
    assert answers["q4_chats_meeting_before_price"] == ["C0100", "C0500"]
    assert isinstance(answers.get("notes"), str) and answers["notes"]
    assert "q2a_paid_orders_without_payment" in (OUT / "q2_reconciliation.csv").read_text(
        encoding="utf-8-sig"
    )
    ann = json.loads((OUT / "chat_annotations.json").read_text(encoding="utf-8"))
    assert "chats" in ann
    q4f = json.loads((OUT / "q4_chats_meeting_before_price.json").read_text(encoding="utf-8"))
    assert q4f["q4_chats_meeting_before_price"] == ["C0100", "C0500"]

    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
