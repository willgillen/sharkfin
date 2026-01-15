from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.categorization_rule import CategorizationRule
from app.models.transaction import Transaction
from app.schemas.rules import (
    CategorizationRuleCreate,
    CategorizationRuleUpdate,
    CategorizationRuleResponse,
    RuleTestRequest,
    RuleTestResponse,
    BulkApplyRulesRequest,
    BulkApplyRulesResponse,
    RuleSuggestion,
    SuggestRulesRequest,
    AcceptSuggestionRequest,
)
from app.services.rule_engine import RuleEngine
from app.services.rule_learning_service import RuleLearningService

router = APIRouter()


@router.post("", response_model=CategorizationRuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(
    rule: CategorizationRuleCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new categorization rule."""
    # Verify category belongs to user if category_id is set
    if rule.category_id:
        from app.models.category import Category
        category = db.query(Category).filter(
            Category.id == rule.category_id,
            Category.user_id == current_user.id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

    db_rule = CategorizationRule(
        user_id=current_user.id,
        **rule.model_dump()
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.get("", response_model=List[CategorizationRuleResponse])
def get_rules(
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all rules for the authenticated user."""
    query = db.query(CategorizationRule).filter(
        CategorizationRule.user_id == current_user.id
    )

    if enabled_only:
        query = query.filter(CategorizationRule.enabled == True)

    rules = query.order_by(
        CategorizationRule.priority.desc(),
        CategorizationRule.created_at.desc()
    ).offset(skip).limit(limit).all()

    return rules


@router.get("/{rule_id}", response_model=CategorizationRuleResponse)
def get_rule(
    rule_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific rule by ID."""
    rule = db.query(CategorizationRule).filter(
        CategorizationRule.id == rule_id,
        CategorizationRule.user_id == current_user.id
    ).first()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )

    return rule


@router.put("/{rule_id}", response_model=CategorizationRuleResponse)
def update_rule(
    rule_id: int,
    rule_update: CategorizationRuleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing rule."""
    db_rule = db.query(CategorizationRule).filter(
        CategorizationRule.id == rule_id,
        CategorizationRule.user_id == current_user.id
    ).first()

    if not db_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )

    # Verify category belongs to user if category_id is being updated
    if rule_update.category_id is not None:
        from app.models.category import Category
        category = db.query(Category).filter(
            Category.id == rule_update.category_id,
            Category.user_id == current_user.id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

    # Update only provided fields
    update_data = rule_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_rule, field, value)

    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(
    rule_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a rule."""
    db_rule = db.query(CategorizationRule).filter(
        CategorizationRule.id == rule_id,
        CategorizationRule.user_id == current_user.id
    ).first()

    if not db_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )

    db.delete(db_rule)
    db.commit()


@router.post("/{rule_id}/test", response_model=RuleTestResponse)
def test_rule(
    rule_id: int,
    test_request: RuleTestRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Test a rule against sample transaction data."""
    db_rule = db.query(CategorizationRule).filter(
        CategorizationRule.id == rule_id,
        CategorizationRule.user_id == current_user.id
    ).first()

    if not db_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )

    rule_engine = RuleEngine(db)
    result = rule_engine.test_rule(
        rule=db_rule,
        payee=test_request.payee,
        description=test_request.description,
        amount=test_request.amount,
        transaction_type=test_request.transaction_type.value
    )

    return RuleTestResponse(
        matches=result['matches'],
        matched_conditions=result['matched_conditions'],
        actions_to_apply=result['actions_to_apply']
    )


@router.post("/apply", response_model=BulkApplyRulesResponse)
def apply_rules(
    request: BulkApplyRulesRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Apply categorization rules to transactions.

    If transaction_ids are specified, apply rules only to those transactions.
    Otherwise, apply to all uncategorized transactions.

    If rule_ids are specified, use only those rules.
    Otherwise, use all enabled rules.
    """
    rule_engine = RuleEngine(db)

    # Get transactions to process
    if request.transaction_ids:
        transactions = db.query(Transaction).filter(
            Transaction.id.in_(request.transaction_ids),
            Transaction.user_id == current_user.id
        ).all()
    else:
        # Get all uncategorized transactions (or all if overwrite_existing)
        query = db.query(Transaction).filter(
            Transaction.user_id == current_user.id
        )
        if not request.overwrite_existing:
            query = query.filter(Transaction.category_id.is_(None))
        transactions = query.all()

    if not transactions:
        return BulkApplyRulesResponse(
            total_processed=0,
            categorized_count=0,
            skipped_count=0,
            rules_used=0,
            transactions_updated=[]
        )

    # Get rules to use
    if request.rule_ids:
        rules = db.query(CategorizationRule).filter(
            CategorizationRule.id.in_(request.rule_ids),
            CategorizationRule.user_id == current_user.id,
            CategorizationRule.enabled == True
        ).order_by(CategorizationRule.priority.desc()).all()
    else:
        rules = rule_engine.get_active_rules(current_user.id)

    # Apply rules
    updated_transaction_ids = []
    categorized = 0
    skipped = 0
    rules_matched = set()

    for transaction in transactions:
        # Skip if already categorized (unless overwrite_existing)
        if transaction.category_id and not request.overwrite_existing:
            skipped += 1
            continue

        matching_rule = rule_engine.evaluate_transaction(transaction, rules)
        if matching_rule:
            rule_engine.apply_rule(transaction, matching_rule)
            categorized += 1
            rules_matched.add(matching_rule.id)
            updated_transaction_ids.append(transaction.id)
        else:
            skipped += 1

    db.commit()

    return BulkApplyRulesResponse(
        total_processed=len(transactions),
        categorized_count=categorized,
        skipped_count=skipped,
        rules_used=len(rules_matched),
        transactions_updated=updated_transaction_ids
    )


@router.post("/suggestions", response_model=List[RuleSuggestion])
def get_rule_suggestions(
    request: SuggestRulesRequest = SuggestRulesRequest(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze user's transaction categorization patterns and suggest automation rules.

    This endpoint examines how the user has manually categorized transactions
    and suggests rules that could automate similar categorizations in the future.
    """
    learning_service = RuleLearningService(db)

    suggestions = learning_service.analyze_user_patterns(
        user_id=current_user.id,
        min_occurrences=request.min_occurrences,
        min_confidence=request.min_confidence
    )

    # Convert to Pydantic models
    return [
        RuleSuggestion(
            suggested_rule_name=s.suggested_rule_name,
            payee_pattern=s.payee_pattern,
            payee_match_type=s.payee_match_type,
            description_pattern=s.description_pattern,
            description_match_type=s.description_match_type,
            amount_min=s.amount_min,
            amount_max=s.amount_max,
            transaction_type=s.transaction_type,
            category_id=s.category_id,
            category_name=s.category_name,
            confidence_score=s.confidence_score,
            match_count=s.match_count,
            sample_transactions=s.sample_transactions
        )
        for s in suggestions
    ]


@router.post("/suggestions/accept", response_model=CategorizationRuleResponse, status_code=status.HTTP_201_CREATED)
def accept_suggestion(
    request: AcceptSuggestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Accept a rule suggestion and create it as an actual rule.

    This endpoint creates a new categorization rule based on a suggestion
    returned from the /suggestions endpoint.
    """
    # Verify category belongs to user
    from app.models.category import Category
    category = db.query(Category).filter(
        Category.id == request.category_id,
        Category.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Create the rule from the suggestion
    db_rule = CategorizationRule(
        user_id=current_user.id,
        name=request.suggested_rule_name,
        priority=request.priority,
        enabled=request.enabled,
        payee_pattern=request.payee_pattern,
        payee_match_type=request.payee_match_type,
        description_pattern=request.description_pattern,
        description_match_type=request.description_match_type,
        amount_min=request.amount_min,
        amount_max=request.amount_max,
        transaction_type=request.transaction_type,
        category_id=request.category_id,
        auto_created=True,  # Mark as auto-created from learning
    )

    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)

    return db_rule
