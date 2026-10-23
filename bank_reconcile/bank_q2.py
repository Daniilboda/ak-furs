"""Ответы Q2: оплаченные без поступлений и неопознанные поступления."""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

from bank_purpose import (
    UNIDENTIFIED_FIELDNAMES,
    enrich_unidentified_row,
    matched_order_id,
    unidentified_incoming,
    write_unidentified_incoming_csv,
)
from bank_statement import incoming_payments, parse_amount, read_bank_statement

_CRM_CLEANUP = Path(__file__).resolve().parent.parent / "crm_cleanup"
if str(_CRM_CLEANUP) not in sys.path:
    sys.path.insert(0, str(_CRM_CLEANUP))

from run_crm_cleanup import run_cleanup  # noqa: E402

REQUIRED_CLEANED_COLUMNS = ("Номер заказа", "Статус")


def paid_order_ids(crm_records: list[dict[str, str]]) -> set[int]:
    """Номера заказов со статусом «Оплачен» (после очистки CRM)."""
    result: set[int] = set()
    for record in crm_records:
        if record["Статус"] == "Оплачен":
            result.add(int(record["Номер заказа"]))
    return result


def order_ids_with_incoming(
    bank_records: list[dict[str, str]],
    known_order_ids: set[int],
) -> set[int]:
    """Заказы, по которым в выписке есть хотя бы одно поступление."""
    result: set[int] = set()
    for record in incoming_payments(bank_records):
        order_id = matched_order_id(record["Назначение платежа"], known_order_ids)
        if order_id is not None:
            result.add(order_id)
    return result


def q2a_paid_orders_without_payment(
    crm_records: list[dict[str, str]],
    bank_records: list[dict[str, str]],
) -> list[int]:
    """Q2a: оплаченные заказы без ни одного поступления в выписке.

    Номера — числа, по возрастанию.
    """
    known = {int(record["Номер заказа"]) for record in crm_records}
    paid = paid_order_ids(crm_records)
    with_payment = order_ids_with_incoming(bank_records, known)
    return sorted(paid - with_payment)


def q2b_unidentified_payments(
    crm_records: list[dict[str, str]],
    bank_records: list[dict[str, str]],
) -> tuple[int, float]:
    """Q2b: число и сумма (руб.) неопознанных поступлений."""
    known = {int(record["Номер заказа"]) for record in crm_records}
    rows = unidentified_incoming(incoming_payments(bank_records), known)
    total = sum(parse_amount(record["Сумма"]) for record in rows)
    return len(rows), total


def read_cleaned_crm(path: Path | str) -> list[dict[str, str]]:
    """Прочитать уже очищенный CRM (*_cleaned.csv): UTF-8, «;».

    Допускаются дополнительные колонки (например «Цена за ед. после скидки»).
    """
    file_path = Path(path)
    with file_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        if reader.fieldnames is None:
            raise ValueError(f"{file_path} пуст или без заголовка")
        for name in REQUIRED_CLEANED_COLUMNS:
            if name not in reader.fieldnames:
                raise ValueError(f"{file_path}: нет колонки {name!r}")
        return [dict(row) for row in reader]


def _q2_payload(
    crm_records: list[dict[str, str]],
    bank_records: list[dict[str, str]],
) -> dict[str, Any]:
    known = {int(record["Номер заказа"]) for record in crm_records}
    incoming = incoming_payments(bank_records)
    identified = [
        record
        for record in incoming
        if matched_order_id(record["Назначение платежа"], known) is not None
    ]
    unidentified = unidentified_incoming(incoming, known)
    count, total = q2b_unidentified_payments(crm_records, bank_records)
    return {
        "q2a_paid_orders_without_payment": q2a_paid_orders_without_payment(
            crm_records, bank_records
        ),
        "q2b_unidentified_payments_count": count,
        "q2b_unidentified_payments_sum_rub": total,
        "incoming_total": len(incoming),
        "incoming_identified": len(identified),
        "incoming_unidentified": count,
        "unidentified_payments": [
            enrich_unidentified_row(record) for record in unidentified
        ],
        "_bank_records": bank_records,
        "_known_order_ids": known,
    }


def compute_q2(
    crm_path: Path | str,
    bank_path: Path | str,
    catalog_path: Path | str | None = None,
) -> dict[str, Any]:
    """Посчитать Q2a/Q2b из сырых файлов (CRM очищается тем же пайплайном этапа 1)."""
    crm_records, _ = run_cleanup(crm_path, catalog_path, only="all")
    bank_records = read_bank_statement(bank_path)
    return _q2_payload(crm_records, bank_records)


def compute_q2_from_cleaned(
    cleaned_crm_path: Path | str,
    bank_path: Path | str,
) -> dict[str, Any]:
    """Посчитать Q2 по уже очищенному CRM (*_cleaned.csv) и выписке."""
    crm_records = read_cleaned_crm(cleaned_crm_path)
    bank_records = read_bank_statement(bank_path)
    return _q2_payload(crm_records, bank_records)


def public_q2_result(result: dict[str, Any]) -> dict[str, Any]:
    """Итоги без служебных полей — для печати в JSON."""
    skip = {"unidentified_payments", "_bank_records", "_known_order_ids"}
    return {key: value for key, value in result.items() if key not in skip}


def write_q2_reconciliation_csv(path: Path | str, result: dict[str, Any]) -> None:
    """Записать итоги сверки и список неопознанных поступлений в один CSV."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    q2a = result["q2a_paid_orders_without_payment"]
    summary = [
        ("q2a_paid_orders_without_payment", "|".join(str(n) for n in q2a)),
        ("q2a_count", str(len(q2a))),
        ("q2b_unidentified_payments_count", str(result["q2b_unidentified_payments_count"])),
        (
            "q2b_unidentified_payments_sum_rub",
            f"{float(result['q2b_unidentified_payments_sum_rub']):.2f}",
        ),
        ("incoming_total", str(result["incoming_total"])),
        ("incoming_identified", str(result["incoming_identified"])),
        ("incoming_unidentified", str(result["incoming_unidentified"])),
    ]
    unidentified = result.get("unidentified_payments", [])
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["показатель", "значение"])
        writer.writerows(summary)
        writer.writerow([])
        writer.writerow(["unidentified_incoming"])
        writer.writerow(list(UNIDENTIFIED_FIELDNAMES))
        for record in unidentified:
            writer.writerow([record.get(name, "") for name in UNIDENTIFIED_FIELDNAMES])


def write_q2_outputs(
    result: dict[str, Any],
    reconciliation_path: Path | str,
    unidentified_path: Path | str,
) -> None:
    """Записать q2_reconciliation.csv (с неопознанными) и отдельный unidentified_incoming.csv."""
    write_q2_reconciliation_csv(reconciliation_path, result)
    bank_records = result["_bank_records"]
    known = result["_known_order_ids"]
    write_unidentified_incoming_csv(
        unidentified_path,
        incoming_payments(bank_records),
        known,
    )
