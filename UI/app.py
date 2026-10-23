"""Простой UI загрузки сырых файлов и запуска обработки (AK Furs)."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

from process_pipeline import run_pipeline

PACKAGE = Path(__file__).resolve().parent
WORK = PACKAGE / "work"
WORK.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 80 * 1024 * 1024  # 80 MB


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/process")
def api_process():
    required = ("crm", "bank", "catalog", "chats")
    missing = [name for name in required if name not in request.files or not request.files[name].filename]
    if missing:
        return jsonify({"ok": False, "error": f"не хватает файлов: {', '.join(missing)}"}), 400

    job_id = uuid.uuid4().hex[:12]
    job_dir = WORK / job_id
    data_dir = job_dir / "docs"
    results_dir = job_dir / "results"
    data_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)

    mapping = {
        "crm": "01_crm_orders_export.csv",
        "bank": "02_bank_statement_rub.csv",
        "catalog": "03_catalog_prices_reference.xlsx",
        "chats": "04_client_chats.zip",
    }
    try:
        for key, dest_name in mapping.items():
            upload = request.files[key]
            dest = data_dir / dest_name
            upload.save(dest)

        outputs = run_pipeline(data_dir, results_dir)
    except Exception as exc:  # noqa: BLE001 — показать ошибку в UI
        shutil.rmtree(job_dir, ignore_errors=True)
        return jsonify({"ok": False, "error": str(exc)}), 500

    def rel(path: Path) -> str:
        return path.relative_to(results_dir).as_posix()

    return jsonify(
        {
            "ok": True,
            "job_id": job_id,
            "main": [
                {
                    "title": "Очищенный CRM",
                    "name": outputs["cleaned_crm"].name,
                    "url": f"/download/{job_id}/{rel(outputs['cleaned_crm'])}",
                },
                {
                    "title": "answers.json",
                    "name": "answers.json",
                    "url": f"/download/{job_id}/{rel(outputs['answers'])}",
                },
                {
                    "title": "Сверка с банком (Q2)",
                    "name": "q2_reconciliation.csv",
                    "url": f"/download/{job_id}/{rel(outputs['q2'])}",
                },
            ],
            "additional": [
                {
                    "title": "Разметка чатов",
                    "name": "chat_annotations.json",
                    "url": f"/download/{job_id}/{rel(outputs['annotations'])}",
                },
                {
                    "title": "Чаты Q4",
                    "name": "q4_chats_meeting_before_price.json",
                    "url": f"/download/{job_id}/{rel(outputs['q4'])}",
                },
            ],
        }
    )


@app.get("/download/<job_id>/<path:filename>")
def download(job_id: str, filename: str):
    folder = WORK / job_id / "results"
    return send_from_directory(folder, filename, as_attachment=True)


def main() -> None:
    print("UI: http://127.0.0.1:5050")
    app.run(host="127.0.0.1", port=5050, debug=False)


if __name__ == "__main__":
    main()
