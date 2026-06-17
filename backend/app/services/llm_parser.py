from datetime import date
from typing import Any
from pydantic import BaseModel, Field
from app.services.llm_client import get_llm


class ParsedTransaction(BaseModel):
    transaction_date: str = Field(description="Date in YYYY-MM-DD format")
    description: str = Field(description="Transaction description / narration")
    merchant: str = Field(description="Merchant or payee name")
    amount: float = Field(description="Transaction amount (positive number)")
    type: str = Field(description="Either 'debit' or 'credit'")
    balance: float | None = Field(None, description="Running balance after this transaction")


class ParsedStatement(BaseModel):
    opening_balance: float | None = Field(None, description="Opening balance from the statement")
    closing_balance: float | None = Field(None, description="Closing balance from the statement")
    statement_period_start: str | None = Field(None, description="Statement period start date in YYYY-MM-DD")
    statement_period_end: str | None = Field(None, description="Statement period end date in YYYY-MM-DD")
    account_type: str | None = Field(None, description="Account type if detectable (savings, credit_card, etc.)")
    transactions: list[ParsedTransaction] = Field(description="List of parsed transactions")


SYSTEM_PROMPT = """You are a precise bank statement parser. Your job is to extract structured data from raw bank statement text.

Rules:
1. Parse ALL transactions completely — do not skip any.
2. Dates must be output in YYYY-MM-DD format.
3. Amount must be a positive number. Use the `type` field (debit/credit) to indicate direction.
4. If the same text appears as both a description and a merchant, use it for both.
5. For credit card statements: payments/credits reduce the balance (type=credit), purchases increase it (type=debit).
6. If opening/closing balance is embedded in text (e.g. "Opening Balance: ₹10,000"), extract it.
7. If the text contains obvious non-transaction content (advertisements, terms, instructions), skip it.
8. Do NOT fabricate or guess data. If unclear, omit the field (use null).
9. Remove any currency symbols (₹, $, €) and commas from amounts before parsing.
10. Detect the statement period dates if present anywhere in the text."""


async def parse_statement_with_llm(raw_text: str, file_name: str = "") -> dict[str, Any]:
    prompt = f"""Parse the following bank statement text into structured data.
Bank statement filename: {file_name}

Raw text:
---
{raw_text[:15000]}
---
Return the structured statement data including opening balance, closing balance, statement period, and all transactions."""
    llm = get_llm().with_structured_output(schema=ParsedStatement)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    try:
        response: ParsedStatement = await llm.ainvoke(messages)
    except Exception as e:
        return {"error": f"LLM parsing failed: {e}", "transactions": []}

    today = date.today()

    def parse_and_validate_transactions(txns: list[ParsedTransaction]) -> list[dict]:
        results = []
        for tx in txns:
            txn_date = today
            if tx.transaction_date:
                for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%d %b %Y", "%d-%b-%Y"):
                    try:
                        from datetime import datetime
                        txn_date = datetime.strptime(tx.transaction_date, fmt).date()
                        break
                    except (ValueError, TypeError):
                        continue

            results.append({
                "transaction_date": txn_date,
                "description": (tx.description or "")[:500],
                "merchant": (tx.merchant or "")[:255],
                "raw_description": (tx.description or "")[:1000],
                "amount": round(abs(tx.amount), 2),
                "type": tx.type if tx.type in ("debit", "credit") else "unknown",
                "currency": "INR",
                "balance": tx.balance,
            })
        return results

    return {
        "opening_balance": response.opening_balance,
        "closing_balance": response.closing_balance,
        "statement_period_start": response.statement_period_start,
        "statement_period_end": response.statement_period_end,
        "account_type": response.account_type,
        "transactions": parse_and_validate_transactions(response.transactions),
    }
