import re
from datetime import datetime
from typing import Any

PATTERNS: list[dict] = [
    {"regex": r"(?:ICICI|HDFC|SBI|AXIS)\s*Bank.*Statement", "source": "bank_statement"},
    {"regex": r"Credit\s*Card.*Statement", "source": "credit_card"},
    {"regex": r"UPI.*Statement|PhonePe|Google\s*Pay|Paytm", "source": "upi"},
]


def detect_source(text: str, file_name: str = "") -> str:
    text_lower = text.lower() + " " + file_name.lower()
    for pattern in PATTERNS:
        if re.search(pattern["regex"], text_lower, re.IGNORECASE):
            return pattern["source"]
    if ".csv" in file_name.lower():
        return "csv_upload"
    return "unknown"


def parse_amount(raw: str) -> float:
    raw = raw.replace(",", "").replace(" ", "").replace("₹", "").replace("INR", "").strip()
    try:
        return float(raw) if raw else 0.0
    except ValueError:
        return 0.0


def normalize_transaction(raw: dict[str, Any]) -> dict[str, Any]:
    transaction_date = raw.get("transaction_date")
    if isinstance(transaction_date, str):
        for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d %b %Y", "%d-%b-%Y"):
            try:
                transaction_date = datetime.strptime(transaction_date, fmt).date()
                break
            except (ValueError, TypeError):
                continue

    amount = raw.get("amount", 0)
    if isinstance(amount, str):
        amount = parse_amount(amount)

    txn_type = raw.get("type", "")
    if not txn_type:
        txn_type = "debit" if amount > 0 else "credit"
        amount = abs(amount)

    return {
        "transaction_date": transaction_date,
        "description": str(raw.get("description", "") or "")[:500],
        "merchant": str(raw.get("merchant", "") or "")[:255],
        "raw_description": str(raw.get("raw_description", "") or "")[:1000],
        "amount": round(abs(amount), 2),
        "currency": str(raw.get("currency", "INR")),
        "type": txn_type,
        "balance": raw.get("balance"),
    }


def normalize_batch(raw_transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [normalize_transaction(tx) for tx in raw_transactions]
