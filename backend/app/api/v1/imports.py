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
from app.models.payee import Payee as PayeeModel
from app.models.category import Category
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
    AnalyzePayeesRequest,
    AnalyzePayeesResponse,
    PayeeAnalysisItem,
)
from app.schemas.intelligent_matching import (
    IntelligentPayeeAnalysisResponse,
    IntelligentAnalysisSummarySchema,
    TransactionPayeeAnalysisSchema,
    AlternativeMatchSchema,
    ImportWithPayeeDecisionsRequest,
    PayeeAssignmentDecision,
)
from app.services.import_service import ImportService
from app.services.ofx_service import OFXService
from app.services.duplicate_detection_service import DuplicateDetectionService
from app.services.smart_rule_suggestion_service import SmartRuleSuggestionService
from app.services.payee_service import PayeeService
from app.services.payee_extraction_service import PayeeExtractionService
from app.services.intelligent_payee_matching_service import IntelligentPayeeMatchingService
import json

router = APIRouter()


def find_category_by_name(db: Session, user_id: int, category_name: str) -> Optional[int]:
    """
    Find a user's category by name, with flexible matching.
    Supports: exact match, case-insensitive match, and common aliases.

    Args:
        db: Database session
        user_id: User ID to search within
        category_name: Category name to find (from known_merchants.json or user input)

    Returns:
        Category ID if found, None otherwise
    """
    if not category_name:
        return None

    # Comprehensive category name mappings
    # Maps suggested category names -> possible user category names
    category_aliases = {
        # Transportation & Auto
        'transportation': ['Transportation', 'Transport', 'Auto & Transport', 'Travel'],
        'auto & transport': ['Auto & Transport', 'Transportation', 'Auto', 'Car'],
        'gas & fuel': ['Gas & Fuel', 'Gas', 'Fuel', 'Auto & Transport', 'Transportation'],

        # Food & Dining
        'restaurants': ['Restaurants', 'Restaurant', 'Dining', 'Food & Dining', 'Eating Out'],
        'restaurant': ['Restaurants', 'Restaurant', 'Dining', 'Food & Dining'],
        'fast_food': ['Restaurants', 'Fast Food', 'Food & Dining', 'Dining'],
        'coffee shops': ['Coffee Shops', 'Coffee', 'Restaurants', 'Dining', 'Food & Dining'],
        'food delivery': ['Food Delivery', 'Restaurants', 'Dining', 'Delivery'],
        'groceries': ['Groceries', 'Grocery', 'Food & Dining', 'Food'],

        # Shopping
        'shopping': ['Shopping', 'Retail', 'General Merchandise', 'Stores'],
        'retail': ['Shopping', 'Retail', 'General Merchandise'],

        # Entertainment
        'entertainment': ['Entertainment', 'Fun', 'Recreation', 'Leisure'],

        # Bills & Utilities
        'utilities': ['Utilities', 'Bills & Utilities', 'Bills', 'Home'],
        'phone & internet': ['Phone & Internet', 'Phone', 'Internet', 'Utilities', 'Bills'],

        # Health
        'health & medical': ['Health & Medical', 'Healthcare', 'Medical', 'Health'],
        'gym & fitness': ['Gym & Fitness', 'Fitness', 'Gym', 'Health'],

        # Personal
        'personal care': ['Personal Care', 'Personal', 'Beauty', 'Self Care'],

        # Home
        'home services': ['Home Services', 'Home', 'Home Improvement', 'Services'],

        # Insurance
        'insurance': ['Insurance', 'Bills', 'Auto Insurance', 'Health Insurance'],

        # Travel
        'travel': ['Travel', 'Vacation', 'Transportation', 'Hotels'],

        # Education
        'education': ['Education', 'Learning', 'Books', 'School'],

        # Subscriptions
        'subscriptions': ['Subscriptions', 'Entertainment', 'Software', 'Monthly'],

        # Fees
        'fees & charges': ['Fees & Charges', 'Fees', 'Bank Fees', 'Finance'],

        # Gifts & Donations
        'gifts & donations': ['Gifts & Donations', 'Gifts', 'Donations', 'Charity'],

        # Pets
        'pets': ['Pets', 'Pet Care', 'Pet Supplies'],

        # Childcare
        'childcare': ['Childcare', 'Kids', 'Children', 'Family'],

        # Taxes & Legal
        'taxes': ['Taxes', 'Tax', 'Tax Preparation'],
        'legal': ['Legal', 'Legal Services', 'Attorney'],
    }

    # Get all user categories for matching
    user_categories = db.query(Category).filter(
        Category.user_id == user_id
    ).all()

    # Try exact match first
    for cat in user_categories:
        if cat.name == category_name:
            return cat.id

    # Try case-insensitive match
    category_lower = category_name.lower()
    for cat in user_categories:
        if cat.name.lower() == category_lower:
            return cat.id

    # Try alias mapping
    if category_lower in category_aliases:
        for alias in category_aliases[category_lower]:
            for cat in user_categories:
                if cat.name.lower() == alias.lower():
                    return cat.id

    # Try partial match (category_name is substring of actual name)
    for cat in user_categories:
        if category_lower in cat.name.lower():
            return cat.id

    return None


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


@router.post("/ofx/analyze-all-payees", response_model=AnalyzePayeesResponse)
async def analyze_all_ofx_payees(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Parse OFX/QFX file and analyze ALL transactions for payee extraction.

    This returns payee analysis for the FULL file, not just a sample.
    Used by the PayeeReviewStep in the import wizard.
    """
    if not (file.filename.endswith('.ofx') or file.filename.endswith('.qfx')):
        raise HTTPException(status_code=400, detail="File must be OFX or QFX format")

    contents = await file.read()

    try:
        result = OFXService.parse_ofx(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse OFX file: {str(e)}")

    # Extract payees from ALL transactions
    extraction_service = PayeeExtractionService(db)
    payee_items = []

    for txn in result['transactions']:
        description = txn.get('description', '')
        payee = txn.get('payee', '')

        text_to_extract = description or payee

        if not text_to_extract or text_to_extract.strip() == '':
            continue

        extracted_name, confidence = extraction_service.extract_payee_name(text_to_extract)

        if extracted_name:
            payee_items.append(
                PayeeAnalysisItem(
                    original=text_to_extract,
                    suggested=extracted_name,
                    confidence=confidence
                )
            )

    return AnalyzePayeesResponse(
        payees=payee_items,
        total_transactions_analyzed=len(result['transactions'])
    )


@router.post("/csv/analyze-all-payees", response_model=AnalyzePayeesResponse)
async def analyze_all_csv_payees(
    file: UploadFile = File(...),
    column_mapping: str = Form(...),  # JSON string
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Parse CSV file and analyze ALL transactions for payee extraction.

    This returns payee analysis for the FULL file, not just a sample.
    Used by the PayeeReviewStep in the import wizard.
    """
    contents = await file.read()

    try:
        # Parse column mapping from JSON string
        mapping_dict = json.loads(column_mapping)
        column_map = CSVColumnMapping(**mapping_dict)

        service = ImportService(db)
        df = service.parse_csv(contents)

        # Map CSV to transactions (gets ALL rows)
        mapped_transactions = service.map_csv_to_transactions(df, column_map)

        # Extract payees from ALL transactions
        extraction_service = PayeeExtractionService(db)
        payee_items = []

        for txn_data in mapped_transactions:
            description = txn_data.get('description', '')
            payee = txn_data.get('payee', '')

            text_to_extract = description or payee

            if not text_to_extract or text_to_extract.strip() == '':
                continue

            extracted_name, confidence = extraction_service.extract_payee_name(text_to_extract)

            if extracted_name:
                payee_items.append(
                    PayeeAnalysisItem(
                        original=text_to_extract,
                        suggested=extracted_name,
                        confidence=confidence
                    )
                )

        return AnalyzePayeesResponse(
            payees=payee_items,
            total_transactions_analyzed=len(mapped_transactions)
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to analyze payees: {str(e)}"
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
    payee_name_overrides: str = Form(default="{}"),  # JSON object of suggested_name -> final_name
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
        payee_overrides = json.loads(payee_name_overrides)

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
        extraction_service = PayeeExtractionService(db)

        for trans_data in mapped_transactions:
            try:
                # Handle payee entity creation with overrides
                payee_id = None
                payee_entity = None
                description = trans_data.get('description', '')
                payee = trans_data.get('payee', '')
                text_to_extract = description or payee

                if text_to_extract and text_to_extract.strip():
                    # Extract canonical name using SAME logic as analyze-all-payees
                    extracted_name, _ = extraction_service.extract_payee_name(text_to_extract)

                    # Apply user override if exists
                    final_payee_name = payee_overrides.get(extracted_name, extracted_name)

                    # Create or get payee with final name
                    payee_entity = payee_service.get_or_create(
                        user_id=current_user.id,
                        canonical_name=final_payee_name
                    )
                    payee_id = payee_entity.id

                # Get category from payee's default_category if available
                category_id = None
                if payee_entity and payee_entity.default_category_id:
                    category_id = payee_entity.default_category_id

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
                    category_id=category_id,
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
    payee_name_overrides: str = Form(default="{}"),  # JSON object of suggested_name -> final_name
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
        payee_overrides = json.loads(payee_name_overrides)

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
        extraction_service = PayeeExtractionService(db)

        for idx, trans_data in enumerate(transactions):
            if idx in skip_row_list:
                continue

            try:
                # Handle payee entity creation with overrides
                payee_id = None
                payee_entity = None
                description = trans_data.get('description', '')
                payee = trans_data.get('payee', '')
                text_to_extract = description or payee

                if text_to_extract and text_to_extract.strip():
                    # Extract canonical name using SAME logic as analyze-all-payees
                    extracted_name, _ = extraction_service.extract_payee_name(text_to_extract)

                    # Apply user override if exists
                    final_payee_name = payee_overrides.get(extracted_name, extracted_name)

                    # Create or get payee with final name
                    payee_entity = payee_service.get_or_create(
                        user_id=current_user.id,
                        canonical_name=final_payee_name
                    )
                    payee_id = payee_entity.id

                # Get category from payee's default_category if available
                category_id = None
                if payee_entity and payee_entity.default_category_id:
                    category_id = payee_entity.default_category_id

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
                    category_id=category_id,
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
            file_size=imp.file_size,
            account_id=imp.account_id,
            account_name=account_name,
            total_rows=imp.total_rows,
            imported_count=imp.imported_count,
            duplicate_count=imp.duplicate_count,
            error_count=imp.error_count,
            status=imp.status,
            started_at=imp.started_at,
            completed_at=imp.completed_at,
            can_rollback=imp.can_rollback,
            original_file_name=imp.original_file_name,
            original_file_size=imp.original_file_size,
            has_file_data=imp.original_file_data is not None
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

    smart_suggestion_service = SmartRuleSuggestionService(db=db)

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
            detected_merchant=s.detected_merchant,
            extracted_payee_name=s.extracted_payee_name,
            extraction_confidence=s.extraction_confidence
        )
        for s in filtered_suggestions
    ]

    return AnalyzeImportForRulesResponse(
        suggestions=suggestion_responses,
        total_transactions_analyzed=len(request.transactions),
        total_suggestions=len(suggestion_responses)
    )


@router.post("/analyze-payees", response_model=AnalyzePayeesResponse)
async def analyze_payees(
    request: AnalyzePayeesRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze transactions and extract payee information.

    This endpoint uses the PayeeExtractionService to extract clean payee names
    from transaction descriptions. It returns the original description, suggested
    payee name, and confidence score for each transaction.

    This is used in the import wizard to show users what payees will be created
    and allow them to edit the names before import.
    """
    extraction_service = PayeeExtractionService(db)

    payee_items = []

    for txn in request.transactions:
        # Get description or payee field
        description = txn.get('description', '')
        payee = txn.get('payee', '')

        # Use description as primary source (that's where payee info is in CSV)
        text_to_extract = description or payee

        if not text_to_extract or text_to_extract.strip() == '':
            continue

        # Extract payee name with confidence
        extracted_name, confidence = extraction_service.extract_payee_name(text_to_extract)

        if extracted_name and len(extracted_name) >= 2:
            payee_items.append(
                PayeeAnalysisItem(
                    original=text_to_extract,
                    suggested=extracted_name,
                    confidence=confidence
                )
            )

    return AnalyzePayeesResponse(
        payees=payee_items,
        total_transactions_analyzed=len(request.transactions)
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


# ============================================================================
# INTELLIGENT PAYEE MATCHING ENDPOINTS
# ============================================================================

@router.post("/csv/analyze-payees-intelligent", response_model=IntelligentPayeeAnalysisResponse)
async def analyze_csv_payees_intelligent(
    file: UploadFile = File(...),
    column_mapping: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze CSV transactions using intelligent payee matching.

    Uses three-tier matching strategy:
    1. Known merchants (high confidence)
    2. Learned patterns (variable confidence)
    3. Fuzzy matching to existing payees (0.70+ threshold)

    Returns analysis with HIGH/LOW/NO_MATCH classifications for UI display.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format")

    contents = await file.read()

    try:
        # Parse column mapping
        mapping_dict = json.loads(column_mapping)
        mapping = CSVColumnMapping(**mapping_dict)

        # Parse CSV and map to transactions
        service = ImportService(db)
        df = service.parse_csv(contents)
        parsed_transactions = service.map_csv_to_transactions(df, mapping, [])

        # Run intelligent analysis
        matching_service = IntelligentPayeeMatchingService(db)
        analyses = matching_service.analyze_transactions_for_import(
            user_id=current_user.id,
            transactions=parsed_transactions
        )

        # Convert to Pydantic schemas
        analysis_schemas = [
            TransactionPayeeAnalysisSchema(
                transaction_index=a.transaction_index,
                original_description=a.original_description,
                extracted_payee_name=a.extracted_payee_name,
                extraction_confidence=a.extraction_confidence,
                match_type=a.match_type,
                matched_payee_id=a.matched_payee_id,
                matched_payee_name=a.matched_payee_name,
                match_confidence=a.match_confidence,
                match_reason=a.match_reason,
                suggested_category=a.suggested_category,
                alternative_matches=[
                    AlternativeMatchSchema(
                        payee_id=alt.payee_id,
                        payee_name=alt.payee_name,
                        confidence=alt.confidence
                    )
                    for alt in a.alternative_matches
                ]
            )
            for a in analyses
        ]

        # Generate summary
        high_confidence_count = len([a for a in analyses if a.match_type == 'HIGH_CONFIDENCE'])
        low_confidence_count = len([a for a in analyses if a.match_type == 'LOW_CONFIDENCE'])
        no_match_count = len([a for a in analyses if a.match_type == 'NO_MATCH'])

        # Count which existing payees were matched
        payee_match_counts = {}
        for a in analyses:
            if a.matched_payee_id:
                if a.matched_payee_id not in payee_match_counts:
                    payee_match_counts[a.matched_payee_id] = {
                        'payee_id': a.matched_payee_id,
                        'name': a.matched_payee_name,
                        'count': 0
                    }
                payee_match_counts[a.matched_payee_id]['count'] += 1

        summary = IntelligentAnalysisSummarySchema(
            high_confidence_matches=high_confidence_count,
            low_confidence_matches=low_confidence_count,
            new_payees_needed=no_match_count,
            total_transactions=len(analyses),
            existing_payees_matched=list(payee_match_counts.values())
        )

        return IntelligentPayeeAnalysisResponse(
            analyses=analysis_schemas,
            summary=summary
        )

    except Exception as e:
        import traceback
        traceback.print_exc()  # Log full traceback
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze CSV payees: {str(e)}"
        )


@router.post("/ofx/analyze-payees-intelligent", response_model=IntelligentPayeeAnalysisResponse)
async def analyze_ofx_payees_intelligent(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze OFX/QFX transactions using intelligent payee matching.

    Uses three-tier matching strategy:
    1. Known merchants (high confidence)
    2. Learned patterns (variable confidence)
    3. Fuzzy matching to existing payees (0.70+ threshold)

    Returns analysis with HIGH/LOW/NO_MATCH classifications for UI display.
    """
    if not (file.filename.endswith('.ofx') or file.filename.endswith('.qfx')):
        raise HTTPException(status_code=400, detail="File must be OFX or QFX format")

    contents = await file.read()

    try:
        # Parse OFX transactions
        parsed_ofx = OFXService.parse_ofx(contents)
        parsed_transactions = OFXService.map_ofx_to_transactions(parsed_ofx)

        # Run intelligent analysis
        matching_service = IntelligentPayeeMatchingService(db)
        analyses = matching_service.analyze_transactions_for_import(
            user_id=current_user.id,
            transactions=parsed_transactions
        )

        # Convert to Pydantic schemas
        analysis_schemas = [
            TransactionPayeeAnalysisSchema(
                transaction_index=a.transaction_index,
                original_description=a.original_description,
                extracted_payee_name=a.extracted_payee_name,
                extraction_confidence=a.extraction_confidence,
                match_type=a.match_type,
                matched_payee_id=a.matched_payee_id,
                matched_payee_name=a.matched_payee_name,
                match_confidence=a.match_confidence,
                match_reason=a.match_reason,
                suggested_category=a.suggested_category,
                alternative_matches=[
                    AlternativeMatchSchema(
                        payee_id=alt.payee_id,
                        payee_name=alt.payee_name,
                        confidence=alt.confidence
                    )
                    for alt in a.alternative_matches
                ]
            )
            for a in analyses
        ]

        # Generate summary
        high_confidence_count = len([a for a in analyses if a.match_type == 'HIGH_CONFIDENCE'])
        low_confidence_count = len([a for a in analyses if a.match_type == 'LOW_CONFIDENCE'])
        no_match_count = len([a for a in analyses if a.match_type == 'NO_MATCH'])

        # Count which existing payees were matched
        payee_match_counts = {}
        for a in analyses:
            if a.matched_payee_id:
                if a.matched_payee_id not in payee_match_counts:
                    payee_match_counts[a.matched_payee_id] = {
                        'payee_id': a.matched_payee_id,
                        'name': a.matched_payee_name,
                        'count': 0
                    }
                payee_match_counts[a.matched_payee_id]['count'] += 1

        summary = IntelligentAnalysisSummarySchema(
            high_confidence_matches=high_confidence_count,
            low_confidence_matches=low_confidence_count,
            new_payees_needed=no_match_count,
            total_transactions=len(analyses),
            existing_payees_matched=list(payee_match_counts.values())
        )

        return IntelligentPayeeAnalysisResponse(
            analyses=analysis_schemas,
            summary=summary
        )

    except Exception as e:
        import traceback
        traceback.print_exc()  # Log full traceback
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze OFX payees: {str(e)}"
        )


@router.post("/csv/execute-with-payee-decisions", response_model=ImportExecuteResponse)
async def execute_csv_import_with_decisions(
    file: UploadFile = File(...),
    column_mapping: str = Form(...),
    request_data: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Execute CSV import using user's payee decisions from intelligent analysis.

    Flow:
    1. Create any new payees based on user's decisions
    2. Create initial patterns for new payees (learning)
    3. Import transactions with assigned payee_ids
    4. Strengthen patterns for accepted matches
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format")

    contents = await file.read()

    try:
        # Parse inputs
        mapping_dict = json.loads(column_mapping)
        mapping = CSVColumnMapping(**mapping_dict)
        request_dict = json.loads(request_data)
        request = ImportWithPayeeDecisionsRequest(**request_dict)

        # Verify account belongs to user
        account = db.query(Account).filter(
            Account.id == request.account_id,
            Account.user_id == current_user.id
        ).first()

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        # Parse CSV and map to transactions
        import_service = ImportService(db)
        df = import_service.parse_csv(contents)
        parsed_transactions = import_service.map_csv_to_transactions(df, mapping, [])

        # Debug logging
        print(f"[CSV Execute] Total payee_assignments: {len(request.payee_assignments)}")
        print(f"[CSV Execute] Total parsed_transactions: {len(parsed_transactions)}")
        for i, d in enumerate(request.payee_assignments[:5]):  # First 5
            print(f"[CSV Execute] Assignment {i}: idx={d.transaction_index}, payee_id={d.payee_id}, new_name={d.new_payee_name}, category={d.new_payee_category}")

        # Services
        payee_service = PayeeService(db)
        matching_service = IntelligentPayeeMatchingService(db)

        # Step 1: Create new payees and patterns
        new_payees = {}  # Map transaction_index -> payee_id
        new_payee_categories = {}  # Map transaction_index -> category_id
        for decision in request.payee_assignments:
            if decision.new_payee_name:
                # Look up category ID by name with flexible matching
                default_category_id = find_category_by_name(
                    db, current_user.id, decision.new_payee_category
                )

                # User wants to create new payee
                payee = payee_service.get_or_create(
                    user_id=current_user.id,
                    canonical_name=decision.new_payee_name,
                    default_category_id=default_category_id
                )
                new_payees[decision.transaction_index] = payee.id
                if default_category_id:
                    new_payee_categories[decision.transaction_index] = default_category_id

                # Create initial pattern if requested
                if decision.create_pattern:
                    matching_service.create_pattern_from_match(
                        user_id=current_user.id,
                        payee_id=payee.id,
                        description=decision.original_description,
                        pattern_type='description_contains',
                        source='import_learning'
                    )

        # Step 2: Build payee override map for import
        payee_overrides = {}  # Map transaction_index -> final_payee_id
        print(f"[CSV Execute] Step 2 - new_payees keys: {list(new_payees.keys())}")
        for idx, txn in enumerate(parsed_transactions):
            if idx in request.skip_rows:
                continue

            # Find decision for this transaction
            decision = next(
                (d for d in request.payee_assignments if d.transaction_index == idx),
                None
            )

            if decision:
                # Use user's decision
                if decision.payee_id:
                    # User selected existing payee
                    payee_overrides[str(idx)] = decision.payee_id
                    print(f"[CSV Execute] Override idx={idx}: existing payee_id={decision.payee_id}")

                    # Strengthen pattern if requested
                    if decision.create_pattern:
                        matching_service.create_pattern_from_match(
                            user_id=current_user.id,
                            payee_id=decision.payee_id,
                            description=decision.original_description,
                            pattern_type='description_contains',
                            source='import_learning'
                        )
                elif idx in new_payees:
                    # New payee was created
                    payee_overrides[str(idx)] = new_payees[idx]
                    print(f"[CSV Execute] Override idx={idx}: new payee_id={new_payees[idx]}")
            else:
                print(f"[CSV Execute] No decision found for idx={idx}")

        print(f"[CSV Execute] Final payee_overrides: {payee_overrides}")

        # Step 3: Execute import - create transactions directly
        # Create import record
        import_record = import_service.create_import_record(
            user_id=current_user.id,
            account_id=request.account_id,
            filename=file.filename,
            import_type="csv",
            total_rows=len(parsed_transactions),
            file_size=len(contents),
            file_data=contents
        )

        imported_count = 0
        error_count = 0
        skip_row_list = request.skip_rows or []

        for idx, trans_data in enumerate(parsed_transactions):
            if idx in skip_row_list:
                continue

            try:
                # Skip transactions with invalid amounts (NaN, None, etc.)
                import math
                amount = trans_data.get('amount')
                if amount is None or (isinstance(amount, float) and (math.isnan(amount) or math.isinf(amount))):
                    error_count += 1
                    continue

                # Determine payee_id from user decisions
                payee_id = payee_overrides.get(str(idx))
                payee_entity = None

                # If no decision was made, fall back to extraction
                if payee_id is None:
                    description = trans_data.get('description', '')
                    payee = trans_data.get('payee', '')
                    text_to_extract = description or payee

                    if text_to_extract and text_to_extract.strip():
                        extraction_service = PayeeExtractionService(db)
                        extracted_name, _ = extraction_service.extract_payee_name(text_to_extract)
                        if extracted_name:
                            payee_entity = payee_service.get_or_create(
                                user_id=current_user.id,
                                canonical_name=extracted_name
                            )
                            payee_id = payee_entity.id
                else:
                    # Look up the payee entity to get its default category
                    payee_entity = db.query(PayeeModel).filter(
                        PayeeModel.id == payee_id,
                        PayeeModel.user_id == current_user.id
                    ).first()

                # Get category from payee's default_category if available
                category_id = None
                if payee_entity and payee_entity.default_category_id:
                    category_id = payee_entity.default_category_id

                # Create transaction - payee name comes from linked Payee entity via API
                transaction = Transaction(
                    user_id=current_user.id,
                    account_id=request.account_id,
                    amount=amount,
                    type=TransactionType[trans_data['type']],
                    date=trans_data['date'],
                    description=trans_data.get('description'),
                    payee_id=payee_id,
                    category_id=category_id,
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
                print(f"Error importing CSV transaction {idx}: {e}")

        db.commit()

        # Update import record
        import_service.complete_import_record(
            import_id=import_record.id,
            imported_count=imported_count,
            duplicate_count=len(skip_row_list),
            error_count=error_count
        )

        return ImportExecuteResponse(
            import_id=import_record.id,
            status=ImportStatus.COMPLETED,
            total_rows=len(parsed_transactions),
            imported_count=imported_count,
            duplicate_count=len(skip_row_list),
            error_count=error_count,
            message=f"Successfully imported {imported_count} transactions"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute CSV import: {str(e)}"
        )


@router.post("/ofx/execute-with-payee-decisions", response_model=ImportExecuteResponse)
async def execute_ofx_import_with_decisions(
    file: UploadFile = File(...),
    request_data: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Execute OFX/QFX import using user's payee decisions from intelligent analysis.

    Flow:
    1. Create any new payees based on user's decisions
    2. Create initial patterns for new payees (learning)
    3. Import transactions with assigned payee_ids
    4. Strengthen patterns for accepted matches
    """
    if not (file.filename.endswith('.ofx') or file.filename.endswith('.qfx')):
        raise HTTPException(status_code=400, detail="File must be OFX or QFX format")

    contents = await file.read()

    try:
        # Parse request
        request_dict = json.loads(request_data)
        request = ImportWithPayeeDecisionsRequest(**request_dict)

        # Verify account belongs to user
        account = db.query(Account).filter(
            Account.id == request.account_id,
            Account.user_id == current_user.id
        ).first()

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        # Parse OFX transactions
        parsed_ofx = OFXService.parse_ofx(contents)
        parsed_transactions = OFXService.map_ofx_to_transactions(parsed_ofx)

        # Services
        payee_service = PayeeService(db)
        matching_service = IntelligentPayeeMatchingService(db)

        # Step 1: Create new payees and patterns
        new_payees = {}  # Map transaction_index -> payee_id
        new_payee_categories = {}  # Map transaction_index -> category_id
        for decision in request.payee_assignments:
            if decision.new_payee_name:
                # Look up category ID by name with flexible matching
                default_category_id = find_category_by_name(
                    db, current_user.id, decision.new_payee_category
                )

                # User wants to create new payee
                payee = payee_service.get_or_create(
                    user_id=current_user.id,
                    canonical_name=decision.new_payee_name,
                    default_category_id=default_category_id
                )
                new_payees[decision.transaction_index] = payee.id
                if default_category_id:
                    new_payee_categories[decision.transaction_index] = default_category_id

                # Create initial pattern if requested
                if decision.create_pattern:
                    matching_service.create_pattern_from_match(
                        user_id=current_user.id,
                        payee_id=payee.id,
                        description=decision.original_description,
                        pattern_type='description_contains',
                        source='import_learning'
                    )

        # Step 2: Build payee override map for import
        payee_overrides = {}  # Map extracted_name -> final_payee_id
        for idx, txn in enumerate(parsed_transactions):
            if idx in request.skip_rows:
                continue

            # Find decision for this transaction
            decision = next(
                (d for d in request.payee_assignments if d.transaction_index == idx),
                None
            )

            if decision:
                # Use user's decision
                if decision.payee_id:
                    # User selected existing payee
                    payee_overrides[str(idx)] = decision.payee_id

                    # Strengthen pattern if requested
                    if decision.create_pattern:
                        matching_service.create_pattern_from_match(
                            user_id=current_user.id,
                            payee_id=decision.payee_id,
                            description=decision.original_description,
                            pattern_type='description_contains',
                            source='import_learning'
                        )
                elif idx in new_payees:
                    # New payee was created
                    payee_overrides[str(idx)] = new_payees[idx]

        # Step 3: Execute import - create transactions directly
        import_service = ImportService(db)

        # Create import record
        import_type = "qfx" if file.filename.endswith('.qfx') else "ofx"
        import_record = import_service.create_import_record(
            user_id=current_user.id,
            account_id=request.account_id,
            filename=file.filename,
            import_type=import_type,
            total_rows=len(parsed_transactions),
            file_size=len(contents),
            file_data=contents
        )

        imported_count = 0
        error_count = 0
        skip_row_list = request.skip_rows or []

        for idx, trans_data in enumerate(parsed_transactions):
            if idx in skip_row_list:
                continue

            try:
                # Determine payee_id from user decisions
                payee_id = payee_overrides.get(str(idx))
                payee_entity = None

                # If no decision was made, fall back to extraction
                if payee_id is None:
                    description = trans_data.get('description', '')
                    payee = trans_data.get('payee', '')
                    text_to_extract = description or payee

                    if text_to_extract and text_to_extract.strip():
                        extraction_service = PayeeExtractionService(db)
                        extracted_name, _ = extraction_service.extract_payee_name(text_to_extract)
                        if extracted_name:
                            payee_entity = payee_service.get_or_create(
                                user_id=current_user.id,
                                canonical_name=extracted_name
                            )
                            payee_id = payee_entity.id
                else:
                    # Look up the payee entity to get its default category
                    payee_entity = db.query(PayeeModel).filter(
                        PayeeModel.id == payee_id,
                        PayeeModel.user_id == current_user.id
                    ).first()

                # Get category from payee's default_category if available
                category_id = None
                if payee_entity and payee_entity.default_category_id:
                    category_id = payee_entity.default_category_id

                # Create transaction
                transaction = Transaction(
                    user_id=current_user.id,
                    account_id=request.account_id,
                    amount=trans_data['amount'],
                    type=TransactionType[trans_data['type']],
                    date=trans_data['date'],
                    description=trans_data.get('description'),
                    payee=trans_data.get('payee'),
                    payee_id=payee_id,
                    category_id=category_id,
                    fitid=trans_data.get('fitid'),
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
        import_service.complete_import_record(
            import_id=import_record.id,
            imported_count=imported_count,
            duplicate_count=len(skip_row_list),
            error_count=error_count
        )

        return ImportExecuteResponse(
            import_id=import_record.id,
            status=ImportStatus.COMPLETED,
            total_rows=len(parsed_transactions),
            imported_count=imported_count,
            duplicate_count=len(skip_row_list),
            error_count=error_count,
            message=f"Successfully imported {imported_count} transactions"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute OFX import: {str(e)}"
        )
