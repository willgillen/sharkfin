from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
import gzip
from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction, TransactionType
from app.models.import_history import ImportHistory, ImportedTransaction
from app.schemas.imports import (
    CSVPreviewResponse,
    OFXPreviewResponse,
    DuplicatesResponse,
    ImportExecuteResponse,
    ImportHistoryResponse,
    CSVColumnMapping,
    ImportStatus,
    AnalyzeImportForRulesRequest,
    AnalyzeImportForRulesResponse,
    SmartRuleSuggestionResponse,
)
from app.services.import_service import ImportService
from app.services.ofx_service import OFXService
from app.services.duplicate_detection_service import DuplicateDetectionService
from app.services.smart_rule_suggestion_service import SmartRuleSuggestionService
from app.services.payee_service import PayeeService
import json

router = APIRouter()


@router.post("/csv/preview", response_model=CSVPreviewResponse)
async def preview_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload CSV and get preview with suggested column mapping"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format")

    contents = await file.read()

    try:
        service = ImportService(db)
        df = service.parse_csv(contents)

        # Detect format and suggest mapping
        format_type = service.detect_csv_format(df)
        suggested_mapping = service.get_suggested_mapping(df, format_type)

        return CSVPreviewResponse(
            columns=df.columns.tolist(),
            sample_rows=df.head(5).fillna('').to_dict('records'),
            detected_format=format_type,
            suggested_mapping=suggested_mapping,
            row_count=len(df)
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse CSV file: {str(e)}"
        )


@router.post("/ofx/preview", response_model=OFXPreviewResponse)
async def preview_ofx(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload OFX/QFX and get preview"""
    if not (file.filename.endswith('.ofx') or file.filename.endswith('.qfx')):
        raise HTTPException(status_code=400, detail="File must be OFX or QFX format")

    contents = await file.read()

    try:
        result = OFXService.parse_ofx(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse OFX file: {str(e)}")

    return OFXPreviewResponse(
        account_name=result['account_name'],
        account_type=result['account_type'],
        account_number=result.get('account_number'),
        bank_name=result.get('bank_name'),
        start_date=result.get('start_date'),
        end_date=result.get('end_date'),
        transaction_count=len(result['transactions']),
        sample_transactions=result['transactions'][:5]
    )


@router.post("/csv/detect-duplicates", response_model=DuplicatesResponse)
async def detect_csv_duplicates(
    file: UploadFile = File(...),
    account_id: int = Form(...),
    column_mapping: str = Form(...),  # JSON string
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Check for duplicate transactions before importing CSV"""
    # Verify account ownership
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    contents = await file.read()

    try:
        # Parse column mapping from JSON string
        mapping_dict = json.loads(column_mapping)
        column_map = CSVColumnMapping(**mapping_dict)

        service = ImportService(db)
        df = service.parse_csv(contents)

        # Map CSV to transactions
        mapped_transactions = service.map_csv_to_transactions(df, column_map)

        # Find duplicates
        duplicates = service.duplicate_detector.find_duplicates(
            current_user.id,
            account_id,
            mapped_transactions
        )

        return DuplicatesResponse(
            duplicates=duplicates,
            total_new_transactions=len(mapped_transactions),
            total_duplicates=len(duplicates)
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to detect duplicates: {str(e)}"
        )


@router.post("/ofx/detect-duplicates", response_model=DuplicatesResponse)
async def detect_ofx_duplicates(
    file: UploadFile = File(...),
    account_id: int = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Check for duplicate transactions before importing OFX"""
    # Verify account ownership
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    contents = await file.read()

    try:
        ofx_service = OFXService()
        parsed = ofx_service.parse_ofx(contents)
        transactions = parsed['transactions']

        # Find duplicates
        service = ImportService(db)
        duplicates = service.duplicate_detector.find_duplicates(
            current_user.id,
            account_id,
            transactions
        )

        return DuplicatesResponse(
            duplicates=duplicates,
            total_new_transactions=len(transactions),
            total_duplicates=len(duplicates)
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to detect duplicates: {str(e)}"
        )


@router.post("/csv/execute", response_model=ImportExecuteResponse)
async def execute_csv_import(
    file: UploadFile = File(...),
    account_id: int = Form(...),
    column_mapping: str = Form(...),  # JSON string
    skip_rows: str = Form(default="[]"),  # JSON array of row numbers to skip
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Execute CSV import after user confirmation"""
    # Verify account ownership
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    contents = await file.read()

    try:
        # Parse parameters
        mapping_dict = json.loads(column_mapping)
        column_map = CSVColumnMapping(**mapping_dict)
        skip_row_list = json.loads(skip_rows)

        service = ImportService(db)
        df = service.parse_csv(contents)

        # Create import record with original file data
        import_record = service.create_import_record(
            user_id=current_user.id,
            account_id=account_id,
            filename=file.filename,
            import_type="csv",
            total_rows=len(df),
            file_size=len(contents),
            file_data=contents  # Store compressed original file
        )

        # Map and import transactions
        mapped_transactions = service.map_csv_to_transactions(df, column_map, skip_row_list)

        imported_count = 0
        error_count = 0
        payee_service = PayeeService(db)

        for trans_data in mapped_transactions:
            try:
                # Handle payee entity creation
                payee_id = None
                if trans_data.get('payee'):
                    payee = payee_service.get_or_create(
                        user_id=current_user.id,
                        canonical_name=trans_data['payee']
                    )
                    payee_id = payee.id

                # Create transaction
                transaction = Transaction(
                    user_id=current_user.id,
                    account_id=account_id,
                    amount=trans_data['amount'],
                    type=TransactionType[trans_data['type']],
                    date=trans_data['date'],
                    description=trans_data.get('description'),
                    payee=trans_data.get('payee'),
                    payee_id=payee_id,
                    notes=trans_data.get('notes'),
                )
                db.add(transaction)
                db.flush()  # Get transaction ID

                # Increment payee usage
                if payee_id:
                    payee_service.increment_usage(payee_id)

                # Link to import
                imported_txn = ImportedTransaction(
                    import_id=import_record.id,
                    transaction_id=transaction.id,
                    row_number=trans_data.get('row')
                )
                db.add(imported_txn)
                imported_count += 1

            except Exception as e:
                error_count += 1
                print(f"Error importing transaction: {e}")

        # Commit all transactions
        db.commit()

        # Update import record
        service.complete_import_record(
            import_id=import_record.id,
            imported_count=imported_count,
            duplicate_count=len(skip_row_list),
            error_count=error_count
        )

        return ImportExecuteResponse(
            import_id=import_record.id,
            status=ImportStatus.COMPLETED,
            total_rows=len(df),
            imported_count=imported_count,
            duplicate_count=len(skip_row_list),
            error_count=error_count,
            message=f"Successfully imported {imported_count} transactions"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to import transactions: {str(e)}"
        )


@router.post("/ofx/execute", response_model=ImportExecuteResponse)
async def execute_ofx_import(
    file: UploadFile = File(...),
    account_id: int = Form(...),
    skip_rows: str = Form(default="[]"),  # JSON array of row numbers to skip
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Execute OFX/QFX import after user confirmation"""
    # Verify account ownership
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    contents = await file.read()

    try:
        skip_row_list = json.loads(skip_rows)

        ofx_service = OFXService()
        parsed = ofx_service.parse_ofx(contents)
        transactions = parsed['transactions']

        service = ImportService(db)

        # Create import record with original file data
        import_type = "qfx" if file.filename.endswith('.qfx') else "ofx"
        import_record = service.create_import_record(
            user_id=current_user.id,
            account_id=account_id,
            filename=file.filename,
            import_type=import_type,
            total_rows=len(transactions),
            file_size=len(contents),
            file_data=contents  # Store compressed original file
        )

        imported_count = 0
        error_count = 0
        payee_service = PayeeService(db)

        for idx, trans_data in enumerate(transactions):
            if idx in skip_row_list:
                continue

            try:
                # Handle payee entity creation
                payee_id = None
                if trans_data.get('payee'):
                    payee = payee_service.get_or_create(
                        user_id=current_user.id,
                        canonical_name=trans_data['payee']
                    )
                    payee_id = payee.id

                # Create transaction
                transaction = Transaction(
                    user_id=current_user.id,
                    account_id=account_id,
                    amount=trans_data['amount'],
                    type=TransactionType[trans_data['type']],
                    date=trans_data['date'],
                    description=trans_data.get('description'),
                    payee=trans_data.get('payee'),
                    payee_id=payee_id,
                    fitid=trans_data.get('fitid'),  # Store FITID in dedicated column
                    notes=trans_data.get('notes'),
                )
                db.add(transaction)
                db.flush()

                # Increment payee usage
                if payee_id:
                    payee_service.increment_usage(payee_id)

                # Link to import
                imported_txn = ImportedTransaction(
                    import_id=import_record.id,
                    transaction_id=transaction.id,
                    row_number=idx
                )
                db.add(imported_txn)
                imported_count += 1

            except Exception as e:
                error_count += 1
                print(f"Error importing transaction: {e}")

        db.commit()

        # Update import record
        service.complete_import_record(
            import_id=import_record.id,
            imported_count=imported_count,
            duplicate_count=len(skip_row_list),
            error_count=error_count
        )

        return ImportExecuteResponse(
            import_id=import_record.id,
            status=ImportStatus.COMPLETED,
            total_rows=len(transactions),
            imported_count=imported_count,
            duplicate_count=len(skip_row_list),
            error_count=error_count,
            message=f"Successfully imported {imported_count} transactions"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to import transactions: {str(e)}"
        )


@router.get("/history", response_model=List[ImportHistoryResponse])
async def get_import_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """Get user's import history"""
    imports = db.query(ImportHistory).filter(
        ImportHistory.user_id == current_user.id
    ).order_by(ImportHistory.started_at.desc()).offset(skip).limit(limit).all()

    # Enrich with account names
    result = []
    for imp in imports:
        account_name = None
        if imp.account_id:
            account = db.query(Account).filter(Account.id == imp.account_id).first()
            if account:
                account_name = account.name

        result.append(ImportHistoryResponse(
            id=imp.id,
            import_type=imp.import_type,
            filename=imp.filename,
            account_id=imp.account_id,
            account_name=account_name,
            total_rows=imp.total_rows,
            imported_count=imp.imported_count,
            duplicate_count=imp.duplicate_count,
            error_count=imp.error_count,
            status=imp.status,
            started_at=imp.started_at,
            completed_at=imp.completed_at,
            can_rollback=imp.can_rollback
        ))

    return result


@router.delete("/history/{import_id}")
async def rollback_import(
    import_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Rollback an import (delete all imported transactions)"""
    import_record = db.query(ImportHistory).filter(
        ImportHistory.id == import_id,
        ImportHistory.user_id == current_user.id,
        ImportHistory.can_rollback == True
    ).first()

    if not import_record:
        raise HTTPException(status_code=404, detail="Import not found or cannot be rolled back")

    try:
        # Delete all transactions from this import
        deleted_count = 0
        for imported_txn in import_record.imported_transactions:
            if imported_txn.transaction:
                db.delete(imported_txn.transaction)
                deleted_count += 1

        import_record.status = "cancelled"
        import_record.can_rollback = False
        import_record.completed_at = import_record.completed_at or db.func.now()
        db.commit()

        return {
            "message": f"Import rolled back successfully. Deleted {deleted_count} transactions.",
            "deleted_count": deleted_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rollback import: {str(e)}"
        )


@router.post("/analyze-for-rules", response_model=AnalyzeImportForRulesResponse)
async def analyze_import_for_rules(
    request: AnalyzeImportForRulesRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze import transaction data and suggest smart categorization rules.

    This endpoint examines the transactions being imported and uses pattern
    recognition and merchant detection to suggest useful rules that can be
    created before completing the import.

    IMPORTANT: Filters out suggestions that match existing user rules to avoid
    suggesting duplicate rules.
    """
    from app.models.categorization_rule import CategorizationRule

    smart_suggestion_service = SmartRuleSuggestionService()

    suggestions = smart_suggestion_service.analyze_import_data(
        transactions=request.transactions,
        min_occurrences=request.min_occurrences,
        min_confidence=request.min_confidence
    )

    # Get existing user rules to filter out duplicates
    existing_rules = db.query(CategorizationRule).filter(
        CategorizationRule.user_id == current_user.id,
        CategorizationRule.enabled == True
    ).all()

    # Create a set of existing patterns (case-insensitive)
    existing_patterns = set()
    for rule in existing_rules:
        if rule.payee_pattern:
            existing_patterns.add(rule.payee_pattern.upper())

    # Filter out suggestions that match existing rules
    filtered_suggestions = []
    for s in suggestions:
        pattern_upper = s.payee_pattern.upper()

        # Check if this pattern is already covered by an existing rule
        pattern_exists = False
        for existing_pattern in existing_patterns:
            # Check if patterns overlap significantly
            if (pattern_upper in existing_pattern or
                existing_pattern in pattern_upper or
                pattern_upper == existing_pattern):
                pattern_exists = True
                break

        if not pattern_exists:
            filtered_suggestions.append(s)

    # Convert to response format
    suggestion_responses = [
        SmartRuleSuggestionResponse(
            suggested_name=s.suggested_name,
            payee_pattern=s.payee_pattern,
            payee_match_type=s.payee_match_type,
            matching_row_indices=s.matching_rows,
            sample_descriptions=s.sample_descriptions,
            confidence=s.confidence,
            detected_merchant=s.detected_merchant
        )
        for s in filtered_suggestions
    ]

    return AnalyzeImportForRulesResponse(
        suggestions=suggestion_responses,
        total_transactions_analyzed=len(request.transactions),
        total_suggestions=len(suggestion_responses)
    )


@router.get("/{import_id}/download")
async def download_import_file(
    import_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Download the original import file.

    Returns the original file that was imported, decompressed if it was stored compressed.
    """
    # Get import record and verify ownership
    import_record = db.query(ImportHistory).filter(
        ImportHistory.id == import_id,
        ImportHistory.user_id == current_user.id
    ).first()

    if not import_record:
        raise HTTPException(status_code=404, detail="Import not found")

    if not import_record.original_file_data:
        raise HTTPException(
            status_code=404,
            detail="Original file not available for this import"
        )

    # Decompress the file data
    file_data = import_record.original_file_data
    if import_record.is_compressed:
        try:
            file_data = gzip.decompress(file_data)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to decompress file: {str(e)}"
            )

    # Determine media type based on file type
    media_type_map = {
        'csv': 'text/csv',
        'ofx': 'application/x-ofx',
        'qfx': 'application/x-ofx'
    }
    media_type = media_type_map.get(import_record.import_type, 'application/octet-stream')

    # Return file with appropriate headers
    filename = import_record.original_file_name or import_record.filename
    return Response(
        content=file_data,
        media_type=media_type,
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )
