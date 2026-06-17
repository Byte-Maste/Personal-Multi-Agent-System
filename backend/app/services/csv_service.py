import io
import csv
from datetime import datetime
from typing import Any


def parse_csv(file_bytes: bytes, source: str = "") -> list[dict[str, Any]]:
    text = file_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        rows.append({k.strip(): v.strip() for k, v in row.items() if k})
    return rows


def detect_csv_columns(rows: list[dict[str, Any]]) -> dict[str, str]:
    headers = list(rows[0].keys()) if rows else []
    header_lower = {h: h.lower().strip() for h in headers}

    col_map: dict[str, str] = {}

    date_candidates = ["date", "transaction date", "txn_date", "tx date", "posting date", "value date"]
    desc_candidates = ["description", "narration", "particulars", "details", "transaction details", "remarks"]
    debit_candidates = ["debit", "debit amount", "withdrawal", "withdraw", "dr", "expense", "paid", "payment"]
    credit_candidates = ["credit", "credit amount", "deposit", "deposit amount", "cr", "income", "received"]
    balance_candidates = ["balance", "closing balance", "available balance"]
    merchant_candidates = ["merchant", "payee", "vendor", "counterparty", "beneficiary"]

    for h, hl in header_lower.items():
        for cand_list, key in [
            (date_candidates, "date"),
            (desc_candidates, "description"),
            (debit_candidates, "debit"),
            (credit_candidates, "credit"),
            (balance_candidates, "balance"),
            (merchant_candidates, "merchant"),
        ]:
            if any(c in hl for c in cand_list):
                col_map[key] = h
                break
    return col_map


def normalize_csv_row(row: dict[str, str], col_map: dict[str, str]) -> dict:
    raw_date = row.get(col_map.get("date", ""), "")
    raw_desc = row.get(col_map.get("description", ""), "")
    raw_debit = row.get(col_map.get("debit", ""), "0")
    raw_credit = row.get(col_map.get("credit", ""), "0")
    raw_balance = row.get(col_map.get("balance", ""), "")
    raw_merchant = row.get(col_map.get("merchant", ""), raw_desc)

    parsed_date = None
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d %b %Y", "%d-%b-%Y"):
        try:
            parsed_date = datetime.strptime(raw_date, fmt).date()
            break
        except (ValueError, TypeError):
            continue

    def parse_amount(val: str) -> float:
        val = val.replace(",", "").replace(" ", "").replace("₹", "").replace("INR", "").strip()
        try:
            return float(val) if val else 0.0
        except ValueError:
            return 0.0

    debit = parse_amount(raw_debit)
    credit = parse_amount(raw_credit)

    if debit and not credit:
        amount = debit
        txn_type = "debit"
    elif credit and not debit:
        amount = credit
        txn_type = "credit"
    elif debit and credit:
        if debit > credit:
            amount = debit
            txn_type = "debit"
        else:
            amount = credit
            txn_type = "credit"
    else:
        amount = 0.0
        txn_type = "unknown"

    return {
        "transaction_date": parsed_date,
        "description": raw_desc[:500] if raw_desc else "",
        "merchant": raw_merchant[:255] if raw_merchant else "",
        "raw_description": raw_desc[:1000] if raw_desc else "",
        "amount": round(amount, 2),
        "type": txn_type,
        "currency": "INR",
        "balance": parse_amount(raw_balance) if raw_balance else None,
    }
