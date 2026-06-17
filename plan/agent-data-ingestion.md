# Agent 1: Data Ingestion Agent

## Purpose
The Data Ingestion Agent is the entry point of the entire system. It receives raw files (PDF bank statements, CSV exports, UPI transaction history, credit card statements) and converts them into structured, normalized transaction records.

## Domain: FinTech
In the FinTech domain, data comes in many shapes: HDFC PDFs, SBI CSV exports, ICICI password-protected PDFs, PhonePe UPI history, Amazon Pay wallet statements. Each format has unique structure, layout, and quirks. The ingestion agent must handle them all.

## LangGraph ReAct Pattern
**Reasoning step:** The agent analyzes the uploaded file, determines its source, file type, and whether it is password-protected. It then selects the appropriate parsing strategy.

**Action step:** The agent uses tools to extract text/rows, decrypt (if needed), parse, validate, normalize, and insert clean transactions into the database.

## Input
- File bytes (PDF / CSV / XLSX)
- File type (statement / credit card / UPI / wallet)
- Source bank/issuer name
- Optional PDF password (from frontend)

## Output (writes to SharedState)
- `statement_ids`: list of created statement record IDs
- `raw_text_preview`: first 2000 chars of extracted text (for LLM context)
- `extracted_transactions`: up to 50 parsed transaction dicts (preview batch)

## Internal Tools Used
| Tool | Description |
|---|---|
| `decrypt_pdf(file_bytes, password)` | Attempts PDF decryption using pypdf; returns error if password is wrong without storing it |
| `extract_text_pypdf(file_bytes)` | Fast text extraction via pypdf |
| `extract_text_pdfplumber(file_bytes)` | Table-aware extraction for tabular bank statements |
| `extract_text_ocr(file_bytes)` | OCR fallback (tesseract/easyocr) for scanned/image-based PDFs |
| `sort_text_blocks_spatially(text_blocks)` | Sorts OCR output blocks by (y0, x0) to preserve column alignment (Debit/Credit/Balance) before LLM |
| `parse_transactions_llm(text, source)` | Sends raw text to Groq LLM to extract structured transactions when regex fails |
| `parse_transactions_regex(text, source)` | Pattern-matching parser for known bank formats |
| `normalize_transaction(raw_tx)` | Standardizes amounts, dates, currency, description |
| `write_transactions_to_db(user_id, transactions)` | Batch inserts into Postgres |

## Agent Logic Flow

```
1. Receive upload → file_bytes, source, password (optional)
2. If file_type is PDF:
   a. If password provided → call decrypt_pdf()
      - If decryption fails → return error "Invalid password", STOP
   b. Call extract_text_pypdf()
   c. If result is empty or low-confidence → call extract_text_pdfplumber()
    d. If still empty → call extract_text_ocr()
    e. Apply sort_text_blocks_spatially() on OCR output to preserve Debit/Credit/Balance column ordering before forwarding to LLM
3. Store raw_text as CLOB in statements table
4. Call parse_transactions_*() depending on source format
5. Normalize each transaction
6. Write to DB via write_transactions_to_db()
7. Update SharedState with statement_ids and preview batch
8. Return control to Orchestrator
```

## Edge Cases Handled

| Edge Case | Response |
|---|---|
| Corrupted PDF | Return error, log corruption detail |
| Wrong password | "Invalid password, please re-upload" — password never saved |
| Mixed-language statements (Hindi + English) | OCR + LLM handles both |
| Merged cells / multi-line entries | pdfplumber table extraction + LLM fallback |
| Empty file | Rejected at upload |
| Very large file (>50MB) | Chunked processing; limit to first 20 pages |
| Unknown bank format | Flag as "unrecognized"; route to LLM parsing |

## Error States
- `NO_TEXT_EXTRACTED`: file could not be parsed
- `INVALID_PASSWORD`: PDF encryption password was incorrect
- `PARSE_FAILED`: text was extracted but no transactions could be identified
- `DB_WRITE_FAILED`: database connection / transaction error
- `SOURCE_NOT_RECOGNIZED`: the source field doesn't match any known parser

## State Impact
```
Before ingestion:
  statement_ids = []
  extracted_transactions = []
  raw_text_preview = ""

After ingestion:
  statement_ids = ["uuid-1", "uuid-2"]
  extracted_transactions = [{date, amount, merchant, ...}, ...]
  raw_text_preview = "TRANSACTION HISTORY HDFC BANK ..."
```

## ReAct Example Interaction

**User Input (from Orchestrator):**
```
Process file: HDFC_Statement_Mar2025.pdf
Source: HDFC Bank
Password: null
User ID: u_123
```

**Agent Reasoning:**
```
This is a PDF from HDFC Bank without a password.
HDFC statements typically have a tabular layout with columns:
Date, Narration, Chq/Ref No, Debit, Credit, Balance.
I should try pdfplumber first (table-aware), then fall back to pypdf.
```

**Action Taken:**
```
extract_text_pdfplumber(file_bytes)
→ returns 400 rows of structured table data
parse_transactions_regex(text, "HDFC")
→ 85 transactions parsed
normalize each → write to DB
→ statement_id: "abc-123"
→ preview: 50 transactions in state
```

## Verification
- All transactions have: `date`, `description`, `amount`, `type` (debit/credit)
- No PII leaked into SharedState (only merchant/amount/date)
- DB `statements.processing_status` = `completed`
- Count of extracted transactions matches manual review for test files
