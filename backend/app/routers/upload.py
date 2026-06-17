from datetime import date, datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.models.category import Category
from app.services.auth_service import get_current_user
from app.services.pdf_service import extract_text, decrypt_pdf
from app.services.csv_service import parse_csv, detect_csv_columns, normalize_csv_row
from app.services.normalization_service import detect_source, normalize_batch
from app.services.categorization_service import categorize_batch
from app.services.llm_parser import parse_statement_with_llm
from app.schemas.upload import UploadResponse

router = APIRouter()


@router.post("/statement", response_model=UploadResponse)
async def upload_statement(
    file: UploadFile = File(...),
    source: str = Form("unknown"),
    statement_password: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("pdf", "csv", "xlsx"):
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, CSV, or XLSX.")

    file_bytes = await file.read()
    if len(file_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    raw_text = ""
    raw_transactions: list[dict] = []

    if ext == "pdf":
        try:
            raw_text = extract_text(file_bytes, statement_password)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        detected_source = detect_source(raw_text, file.filename) if source == "unknown" else source

    elif ext == "csv":
        try:
            rows = parse_csv(file_bytes)
            detected_source = detect_source("", file.filename) if source == "unknown" else source
            if rows:
                col_map = detect_csv_columns(rows)
                for row in rows:
                    tx = normalize_csv_row(row, col_map)
                    if tx["transaction_date"] and tx["amount"] > 0:
                        raw_transactions.append(tx)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"CSV parse failed: {e}")
    else:
        detected_source = source

    stmt = Statement(
        user_id=current_user.id,
        file_name=file.filename,
        file_type=ext,
        source=detected_source,
        raw_text=raw_text[:50000] if raw_text else None,
        meta_data={},
        processing_status="processing",
    )
    db.add(stmt)
    await db.commit()
    await db.refresh(stmt)

    if ext == "pdf" and raw_text:
        parsed = await parse_statement_with_llm(raw_text, file.filename)
        if "error" in parsed:
            raise HTTPException(status_code=500, detail=parsed["error"])

        if parsed.get("statement_period_start"):
            try:
                stmt.statement_period_start = datetime.strptime(parsed["statement_period_start"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass
        if parsed.get("statement_period_end"):
            try:
                stmt.statement_period_end = datetime.strptime(parsed["statement_period_end"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

        if parsed.get("opening_balance") is not None:
            stmt.meta_data["opening_balance"] = parsed["opening_balance"]
        if parsed.get("closing_balance") is not None:
            stmt.meta_data["closing_balance"] = parsed["closing_balance"]
        if parsed.get("account_type"):
            stmt.meta_data["account_type"] = parsed["account_type"]

        raw_transactions = parsed.get("transactions", [])

        cat_txns = await categorize_batch(raw_transactions)
        for tx in cat_txns:
            cat = None
            if tx.get("category_name"):
                result = await db.execute(
                    select(Category).where(Category.name == tx["category_name"], Category.is_default == True)
                )
                cat = result.scalar_one_or_none()

            db_tx = Transaction(
                user_id=current_user.id,
                statement_id=stmt.id,
                transaction_date=tx.get("transaction_date"),
                description=tx.get("description", "")[:500],
                merchant=tx.get("merchant", "")[:255],
                raw_description=tx.get("raw_description", "")[:1000],
                amount=tx.get("amount", 0),
                currency=tx.get("currency", "INR"),
                type=tx.get("type", "unknown"),
                category_id=cat.id if cat else None,
            )
            db.add(db_tx)

        stmt.processing_status = "completed"
        await db.commit()

    elif ext == "csv" and raw_transactions:
        cat_txns = await categorize_batch(raw_transactions)
        for tx in cat_txns:
            cat = None
            if tx.get("category_name"):
                result = await db.execute(
                    select(Category).where(Category.name == tx["category_name"], Category.is_default == True)
                )
                cat = result.scalar_one_or_none()

            db_tx = Transaction(
                user_id=current_user.id,
                statement_id=stmt.id,
                transaction_date=tx.get("transaction_date"),
                description=tx.get("description", "")[:500],
                merchant=tx.get("merchant", "")[:255],
                raw_description=tx.get("raw_description", "")[:1000],
                amount=tx.get("amount", 0),
                currency=tx.get("currency", "INR"),
                type=tx.get("type", "unknown"),
                category_id=cat.id if cat else None,
            )
            db.add(db_tx)

        stmt.processing_status = "completed"
        await db.commit()

    await db.refresh(stmt)
    return UploadResponse(
        statement_id=str(stmt.id),
        file_name=file.filename,
        status=stmt.processing_status,
        transactions_count=len(raw_transactions),
        message=f"Processed {len(raw_transactions)} transactions",
    )


@router.get("/status/{statement_id}")
async def upload_status(
    statement_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Statement).where(
            Statement.id == statement_id,
            Statement.user_id == current_user.id,
        )
    )
    stmt = result.scalar_one_or_none()
    if not stmt:
        raise HTTPException(status_code=404, detail="Statement not found")

    result = await db.execute(
        select(Transaction).where(Transaction.statement_id == stmt.id)
    )
    txns = result.scalars().all()

    return {
        "statement_id": str(stmt.id),
        "file_name": stmt.file_name,
        "status": stmt.processing_status,
        "source": stmt.source,
        "transactions_count": len(txns),
        "created_at": stmt.created_at.isoformat() if stmt.created_at else None,
    }
