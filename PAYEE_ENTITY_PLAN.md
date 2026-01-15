# Payee/Source Entity System Implementation Plan

## Overview

Replace the simple string-based `payee` field in transactions with a comprehensive Payee entity system that normalizes payee data, supports metadata (default categories, logos, types), and enables smooth manual entry with autocomplete.

## User Requirements

Based on user input:
1. **NO history tracking** - One-way normalization, canonical names only
2. **NO manual alias system** - Rely on rules engine for normalization
3. **Unified Payee entity** - Single entity handles both payees (expenses) and sources (income)
4. **Metadata support**: Default category, payee type/industry, logo URL
5. **Manual entry**: Typeahead autocomplete with inline payee creation
6. **Import wizard**: Fast payee creation/matching during import
7. **Rules integration**: Smart suggestions create Payee entities

## Architecture Overview

### Current State
- Transaction has simple `payee` string field (nullable, 200 char limit in CSV imports)
- No normalization or deduplication
- Rules match against raw payee strings with 5 match types
- Autocomplete ranks by frequency but returns inconsistent strings

### Target State
- Transaction has `payee_id` foreign key to Payee entity
- Payee table stores canonical names with metadata
- Rules match against Payee.canonical_name
- Autocomplete returns Payee entities with category suggestions
- Import wizard auto-creates/matches Payee entities
- Backward compatible during migration

---

## Phase 1: Database Schema & Models

### 1.1 New Payee Table

```sql
CREATE TABLE payees (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Core identity
    canonical_name VARCHAR(200) NOT NULL,

    -- Metadata
    default_category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    payee_type VARCHAR(50),  -- 'grocery', 'restaurant', 'gas', 'utility', etc.
    logo_url VARCHAR(500),
    notes TEXT,

    -- Statistics
    transaction_count INTEGER DEFAULT 0 NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,

    -- Indexes for performance
    CONSTRAINT idx_payees_unique_user_canonical UNIQUE (user_id, canonical_name)
);

CREATE INDEX idx_payees_user_id ON payees(user_id);
CREATE INDEX idx_payees_user_canonical ON payees(user_id, canonical_name);
CREATE INDEX idx_payees_autocomplete ON payees(user_id, transaction_count DESC, last_used_at DESC);
```

### 1.2 Update Transaction Table

```sql
-- Add new payee_id foreign key (nullable for migration)
ALTER TABLE transactions ADD COLUMN payee_id INTEGER REFERENCES payees(id) ON DELETE SET NULL;
CREATE INDEX idx_transactions_payee_id ON transactions(payee_id);

-- Keep existing payee string field temporarily for backward compatibility
-- Will be deprecated and removed in future version
```

### 1.3 SQLAlchemy Models

**File**: `backend/app/models/payee.py`
```python
class Payee(Base):
    __tablename__ = "payees"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    canonical_name = Column(String(200), nullable=False)
    default_category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    payee_type = Column(String(50), nullable=True)
    logo_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    transaction_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    user = relationship("User", back_populates="payees")
    default_category = relationship("Category")
    transactions = relationship("Transaction", back_populates="payee_entity")

    __table_args__ = (
        Index('idx_payees_user_canonical', 'user_id', 'canonical_name'),
        Index('idx_payees_autocomplete', 'user_id', 'transaction_count', 'last_used_at'),
        Index('idx_payees_unique', 'user_id', 'canonical_name', unique=True),
    )
```

**Update**: `backend/app/models/transaction.py`
```python
class Transaction(Base):
    # ... existing fields ...

    # NEW: Foreign key to Payee
    payee_id = Column(Integer, ForeignKey("payees.id", ondelete="SET NULL"), nullable=True, index=True)

    # LEGACY: Keep for backward compatibility (will deprecate)
    payee = Column(String, nullable=True)

    # NEW: Relationship
    payee_entity = relationship("Payee", back_populates="transactions")
```

**Update**: `backend/app/models/user.py`
```python
class User(Base):
    # ... existing relationships ...

    # NEW: Payees relationship
    payees = relationship("Payee", back_populates="user", cascade="all, delete-orphan")
```

### 1.4 Migration File

**File**: `backend/alembic/versions/XXXXX_add_payee_entity.py`

Creates payees table, adds payee_id to transactions, creates indexes.

---

## Phase 2: Data Migration Service

### 2.1 Payee Migration Service

**File**: `backend/app/services/payee_migration_service.py`

```python
class PayeeMigrationService:
    """Migrate existing transaction.payee strings to Payee entities."""

    def migrate_user_payees(self, user_id: int) -> Dict[str, int]:
        """
        1. Get all unique payee strings for user
        2. Normalize each to canonical name
        3. Create Payee entities with metadata:
           - default_category_id from most common category
           - transaction_count from actual usage
           - last_used_at from most recent transaction
        4. Update all transactions to reference Payee entities
        5. Return migration statistics
        """

    def _normalize_payee_name(self, payee: str) -> str:
        """
        Normalize payee string to canonical name:
        - Title case for consistency
        - Remove store numbers (#1234)
        - Remove transaction IDs
        - Strip payment processor prefixes (SQ *, TST *)
        - Truncate to 200 chars
        """

    def _get_most_common_category(self, user_id: int, payee_str: str) -> Optional[int]:
        """Get category used most frequently with this payee."""
```

### 2.2 Migration Script

**File**: `backend/scripts/migrate_payees.py`

Command-line script to run migration for all users or specific user.

---

## Phase 3: Payee Service Layer

### 3.1 PayeeService

**File**: `backend/app/services/payee_service.py`

```python
class PayeeService:
    def get_or_create(self, user_id: int, canonical_name: str,
                     default_category_id: Optional[int] = None) -> Payee:
        """
        Get existing payee or create new one.
        This is the primary method used during transaction creation and import.

        1. Normalize the name
        2. Try to find existing (user_id + canonical_name unique constraint)
        3. If not found, create new Payee
        4. Return Payee entity
        """

    def increment_usage(self, payee_id: int):
        """Update transaction_count and last_used_at statistics."""

    def search_payees(self, user_id: int, query: str, limit: int = 10) -> List[Payee]:
        """
        Search payees for autocomplete.
        Ranks by:
        1. Exact name match first
        2. Starts with query
        3. Contains query
        4. Within each group, by usage frequency and recency
        """

    def update_default_category(self, payee_id: int, category_id: Optional[int]):
        """Learn default category from user behavior."""
```

---

## Phase 4: Update Rules Engine

### 4.1 Rules Model Changes

**File**: `backend/app/models/categorization_rule.py`

```python
class CategorizationRule(Base):
    # ... existing fields ...

    # CHANGE: payee_pattern now matches against Payee.canonical_name
    payee_pattern = Column(String(255), nullable=True)
    payee_match_type = Column(String(20), nullable=True)

    # NEW: Optionally suggest specific Payee entity
    suggested_payee_id = Column(Integer, ForeignKey("payees.id", ondelete="SET NULL"), nullable=True)

    # REMOVE: new_payee field (replaced by suggested_payee_id)

    # NEW: Relationship
    suggested_payee = relationship("Payee")
```

### 4.2 Rules Engine Updates

**File**: `backend/app/services/rule_engine.py`

```python
class RuleEngine:
    def _rule_matches(self, transaction: Transaction, rule: CategorizationRule) -> bool:
        """
        Updated payee matching:
        1. Get payee text from transaction.payee_entity.canonical_name
        2. Fallback to transaction.payee string during migration
        3. Match using existing 5 match types (contains, starts_with, etc.)
        """

    def apply_rule(self, transaction: Transaction, rule: CategorizationRule):
        """
        Updated actions:
        1. Set category_id (unchanged)
        2. Set payee_id from rule.suggested_payee_id (NEW)
        3. Append notes (unchanged)
        4. Update rule statistics (unchanged)
        """
```

### 4.3 Smart Rule Suggestions Update

**File**: `backend/app/services/smart_rule_suggestion_service.py`

```python
class SmartRuleSuggestionService:
    def analyze_import_data(self, transactions: List[Dict], user_id: int) -> List[SmartRuleSuggestion]:
        """
        Updated to work with Payee entities:
        1. Extract merchant names from descriptions
        2. For each detected pattern, create/find Payee entity
        3. Suggest rule with suggested_payee_id instead of new_payee string
        4. Filter out suggestions matching existing rules
        """
```

---

## Phase 5: Pydantic Schemas

### 5.1 Payee Schemas

**File**: `backend/app/schemas/payee.py`

```python
class PayeeBase(BaseModel):
    canonical_name: str
    default_category_id: Optional[int] = None
    payee_type: Optional[str] = None
    logo_url: Optional[str] = None
    notes: Optional[str] = None

class PayeeCreate(PayeeBase):
    pass

class PayeeUpdate(BaseModel):
    canonical_name: Optional[str] = None
    default_category_id: Optional[int] = None
    payee_type: Optional[str] = None
    logo_url: Optional[str] = None
    notes: Optional[str] = None

class Payee(PayeeBase):
    id: int
    user_id: int
    transaction_count: int
    last_used_at: Optional[datetime] = None
    created_at: datetime

class PayeeWithCategory(Payee):
    """Payee with default category details for autocomplete."""
    default_category_name: Optional[str] = None
```

### 5.2 Update Transaction Schemas

**File**: `backend/app/schemas/transaction.py`

```python
class TransactionBase(BaseModel):
    # ... existing fields ...

    # NEW: Support both payee_id (preferred) and payee string (legacy)
    payee_id: Optional[int] = None
    payee: Optional[str] = None  # Deprecated but kept for compatibility

class TransactionWithPayee(TransactionInDB):
    """Transaction enriched with payee entity details."""
    payee_canonical_name: Optional[str] = None
    payee_default_category_id: Optional[int] = None
```

---

## Phase 6: API Endpoints

### 6.1 Payee CRUD Endpoints

**File**: `backend/app/api/v1/payees.py`

```python
router = APIRouter()

@router.post("", response_model=Payee)
def create_payee(payee_data: PayeeCreate, ...):
    """Create new payee (uses get_or_create to avoid duplicates)."""

@router.get("", response_model=List[Payee])
def get_payees(q: Optional[str] = None, limit: int = 50, ...):
    """Get payees with optional search."""

@router.get("/autocomplete", response_model=List[PayeeWithCategory])
def autocomplete_payees(q: str, limit: int = 10, ...):
    """
    Autocomplete for transaction entry.
    Returns payees with category suggestions ranked by usage.
    """

@router.get("/{payee_id}", response_model=Payee)
def get_payee(payee_id: int, ...):
    """Get specific payee."""

@router.put("/{payee_id}", response_model=Payee)
def update_payee(payee_id: int, payee_data: PayeeUpdate, ...):
    """Update payee metadata."""

@router.delete("/{payee_id}")
def delete_payee(payee_id: int, ...):
    """Delete payee (sets transactions.payee_id to NULL)."""
```

### 6.2 Update Transaction Endpoints

**File**: `backend/app/api/v1/transactions.py`

```python
@router.post("", response_model=Transaction)
def create_transaction(transaction_data: TransactionCreate, ...):
    """
    Updated to handle payee entities:
    1. If payee_id provided, use it directly
    2. If payee string provided, call PayeeService.get_or_create()
    3. Increment payee usage statistics
    4. Create transaction with payee_id
    """

@router.get("/suggestions/payees", response_model=List[PayeeWithCategory])
def get_payee_suggestions(q: Optional[str] = None, limit: int = 10, ...):
    """
    Updated autocomplete using Payee entities.
    Returns most frequently used payees with category info.
    """
```

### 6.3 Update Import Endpoints

**File**: `backend/app/api/v1/imports.py`

No changes needed - ImportService will handle payee creation internally.

---

## Phase 7: Update Import Service

### 7.1 Import Service Changes

**File**: `backend/app/services/import_service.py`

```python
class ImportService:
    def map_csv_to_transactions(self, df: pd.DataFrame, column_mapping: CSVColumnMapping,
                               user_id: int, skip_rows: List[int] = None) -> List[Dict]:
        """
        Updated to create Payee entities during CSV parsing:
        1. Extract payee string from CSV column
        2. Call PayeeService.get_or_create() to get/create Payee entity
        3. Include payee_id in transaction dict
        4. Return transactions with payee_id ready for import
        """
```

**File**: `backend/app/services/ofx_service.py`

Similar updates for OFX/QFX parsing.

---

## Phase 8: Frontend Integration

### 8.1 TypeScript Types

**File**: `frontend/types/payee.ts`

```typescript
export interface Payee {
  id: number;
  user_id: number;
  canonical_name: string;
  default_category_id?: number;
  payee_type?: string;
  logo_url?: string;
  notes?: string;
  transaction_count: number;
  last_used_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface PayeeWithCategory extends Payee {
  default_category_name?: string;
}

export interface PayeeCreate {
  canonical_name: string;
  default_category_id?: number;
  payee_type?: string;
  logo_url?: string;
  notes?: string;
}
```

### 8.2 Payee API Client

**File**: `frontend/lib/api/payees.ts`

```typescript
export const payeesAPI = {
  getAll: async (): Promise<Payee[]> => { ... },
  autocomplete: async (query: string, limit: number = 10): Promise<PayeeWithCategory[]> => { ... },
  create: async (data: PayeeCreate): Promise<Payee> => { ... },
  update: async (id: number, data: Partial<PayeeCreate>): Promise<Payee> => { ... },
  delete: async (id: number): Promise<void> => { ... },
  get: async (id: number): Promise<Payee> => { ... }
};
```

### 8.3 Update QuickAddBar Component

**File**: `frontend/components/transactions/QuickAddBar.tsx`

```typescript
// Add state for payee entity
const [payeeId, setPayeeId] = useState<number | null>(null);
const [payee, setPayee] = useState(""); // Display value
const [payeeSuggestions, setPayeeSuggestions] = useState<PayeeWithCategory[]>([]);

// Fetch suggestions with debounce
useEffect(() => {
  if (payee.length >= 2) {
    const debounce = setTimeout(async () => {
      const suggestions = await payeesAPI.autocomplete(payee);
      setPayeeSuggestions(suggestions);
    }, 300);
    return () => clearTimeout(debounce);
  }
}, [payee]);

// Handle selection
const handlePayeeSelect = (selectedPayee: PayeeWithCategory) => {
  setPayee(selectedPayee.canonical_name);
  setPayeeId(selectedPayee.id);

  // Auto-fill category if payee has default
  if (selectedPayee.default_category_id) {
    setCategoryId(selectedPayee.default_category_id);
  }
};

// Submit with payee_id or payee string
await transactionsAPI.create({
  payee_id: payeeId,
  payee: !payeeId ? payee : undefined, // Fallback for new payees
  // ... other fields
});
```

### 8.4 Import Wizard Updates

**File**: `frontend/components/import/SmartRuleSuggestionsStep.tsx`

No major changes needed - backend handles Payee entity creation during import.

Optional: Add UI to show which payees were created during import.

---

## Phase 9: Implementation Sequence

### Week 1: Foundation
1. ✅ Create Payee model and migration
2. ✅ Add payee_id to Transaction model
3. ✅ Create PayeeService with get_or_create()
4. ✅ Create Pydantic schemas
5. ✅ Run migration on dev database
6. ✅ Create PayeeMigrationService
7. ✅ Test migration on dev data

### Week 2: Backend Integration
1. ✅ Update RuleEngine to work with Payee entities
2. ✅ Update SmartRuleSuggestionService
3. ✅ Update ImportService to create Payees
4. ✅ Create Payee API endpoints
5. ✅ Update Transaction API endpoints
6. ✅ Write unit tests for PayeeService
7. ✅ Write integration tests

### Week 3: Data Migration & Frontend
1. ✅ Run data migration for all users
2. ✅ Verify data integrity
3. ✅ Create frontend TypeScript types
4. ✅ Create payees API client
5. ✅ Update QuickAddBar with autocomplete
6. ✅ Test manual transaction entry
7. ✅ Test import wizard

### Week 4: Testing & Polish
1. ✅ Comprehensive testing (unit + integration)
2. ✅ Performance testing with large datasets
3. ✅ UI/UX refinement
4. ✅ Documentation updates
5. ✅ Backward compatibility verification

---

## Phase 10: Testing Strategy

### Unit Tests

```python
# backend/app/tests/test_payee_service.py

def test_get_or_create_new_payee():
    """Test creating a new payee."""

def test_get_or_create_existing_payee():
    """Test retrieving existing payee."""

def test_normalize_payee_name():
    """Test normalization removes store numbers, etc."""

def test_autocomplete_ranking():
    """Test autocomplete ranks by usage frequency."""
```

### Integration Tests

```python
# backend/app/tests/test_payee_integration.py

def test_transaction_create_with_payee_string():
    """Test legacy payee string creates entity."""

def test_transaction_create_with_payee_id():
    """Test using payee_id directly."""

def test_import_creates_payee_entities():
    """Test CSV import auto-creates payees."""

def test_rule_matching_with_payee_entities():
    """Test rules match against canonical names."""
```

---

## Phase 11: Backward Compatibility

During transition:
1. Both `payee` (string) and `payee_id` (FK) exist on Transaction
2. API accepts either payee string or payee_id
3. When string provided, auto-create/find Payee entity
4. Rules engine checks payee_entity first, falls back to payee string
5. Frontend can gradually migrate to entity-based approach

Future deprecation (v2.0):
1. Remove Transaction.payee string field
2. Require payee_id in API
3. Update all clients to use Payee entities

---

## Phase 12: Performance Considerations

### Indexes
- `idx_payees_user_canonical`: Fast get_or_create lookups (unique constraint)
- `idx_payees_autocomplete`: Optimizes autocomplete queries (user_id, count, last_used)
- `idx_transactions_payee_id`: Fast transaction-to-payee joins

### Caching (Optional)
```python
# Redis cache for frequent queries
"user:{user_id}:payees:autocomplete:{query}"  # Cache autocomplete results
"user:{user_id}:payees:frequent"              # Cache top 20 payees
```

### Query Optimization
- Eager load category relationship in autocomplete
- Batch update statistics (don't increment on every transaction create)
- Consider database trigger for transaction_count updates

---

## Phase 13: Critical Files

### Backend Files to Create
1. `backend/app/models/payee.py` - Payee model with relationships
2. `backend/app/services/payee_service.py` - Core business logic
3. `backend/app/services/payee_migration_service.py` - Data migration
4. `backend/app/schemas/payee.py` - Pydantic schemas
5. `backend/app/api/v1/payees.py` - CRUD endpoints
6. `backend/alembic/versions/XXXXX_add_payee_entity.py` - Database migration
7. `backend/scripts/migrate_payees.py` - Migration script

### Backend Files to Modify
1. `backend/app/models/transaction.py` - Add payee_id and relationship
2. `backend/app/models/user.py` - Add payees relationship
3. `backend/app/models/categorization_rule.py` - Add suggested_payee_id
4. `backend/app/services/rule_engine.py` - Update matching logic
5. `backend/app/services/smart_rule_suggestion_service.py` - Create Payee entities
6. `backend/app/services/import_service.py` - Auto-create payees during import
7. `backend/app/api/v1/transactions.py` - Support payee_id in create/update
8. `backend/app/schemas/transaction.py` - Add payee_id field

### Frontend Files to Create
1. `frontend/types/payee.ts` - TypeScript types
2. `frontend/lib/api/payees.ts` - API client

### Frontend Files to Modify
1. `frontend/components/transactions/QuickAddBar.tsx` - Add autocomplete
2. `frontend/types/index.ts` - Export payee types

---

## Phase 14: Verification Plan

### Manual Testing
1. ✅ Create new transaction with payee autocomplete
2. ✅ Select existing payee from dropdown
3. ✅ Type new payee name and submit (auto-creates entity)
4. ✅ Verify category auto-filled from payee default
5. ✅ Import CSV file with payees
6. ✅ Verify payee entities created during import
7. ✅ Create rule with payee pattern
8. ✅ Apply rule and verify payee entity linked
9. ✅ Test smart rule suggestions create Payee entities
10. ✅ Run data migration script
11. ✅ Verify all existing transactions have payee_id

### Automated Testing
```bash
# Backend tests
docker-compose exec backend pytest app/tests/test_payee_service.py
docker-compose exec backend pytest app/tests/test_payee_integration.py
docker-compose exec backend pytest app/tests/test_payee_migration.py

# Check test coverage
docker-compose exec backend pytest --cov=app.services.payee_service --cov-report=html
```

---

## Phase 15: Migration Rollback Plan

If migration fails:
1. Restore database backup taken before migration
2. Remove payee_id column from transactions
3. Drop payees table
4. Keep transaction.payee string field
5. Revert code changes

Safety measures:
- Take database backup before migration
- Run migration on staging/copy first
- Monitor migration progress with logging
- Test rollback procedure before production migration

---

## Summary

This plan creates a robust Payee entity system that:
- ✅ Normalizes payee data with canonical names
- ✅ Supports metadata (categories, types, logos)
- ✅ Enables smooth manual entry with autocomplete
- ✅ Auto-creates payees during import
- ✅ Integrates with rules engine for smart suggestions
- ✅ Maintains backward compatibility during migration
- ✅ Provides clear migration path from strings to entities
- ✅ Optimizes performance with proper indexing
- ✅ Supports user-provided CSV sample for testing

The system is designed to be implemented incrementally with minimal disruption to existing functionality.
