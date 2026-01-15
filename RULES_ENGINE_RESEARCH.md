# Rules Engine Research for Transaction Categorization

**Date**: 2026-01-14
**Purpose**: Evaluate Python rules engine libraries for automating transaction categorization in Shark Fin

---

## Executive Summary

After researching various Python rules engine options, we have several viable approaches:

1. **Business-Rules (Venmo)** - Mature, JSON-based, non-technical user friendly
2. **python-simple-rules-engine** - Lightweight, code-based, developer friendly
3. **business-rule-engine** - DSL-based, Excel-like functions (inactive maintenance)
4. **durable-rules** - Complex event processing, may be over-engineered
5. **Custom lightweight solution** - Purpose-built for transaction categorization

**Recommendation**: Start with **python-simple-rules-engine** or build a **custom lightweight solution** tailored to our specific transaction categorization needs.

---

## Library Comparison

### 1. Business-Rules (by Venmo)

**Repository**: [github.com/venmo/business-rules](https://github.com/venmo/business-rules)
**PyPI**: [pypi.org/project/business-rules/](https://pypi.org/project/business-rules/)
**Stars**: 972 | **Forks**: 268

#### Pros
- ✅ **JSON-based rules** - Non-developers can modify rules via UI
- ✅ **Type-safe** - Decorators define variables with specific types (`@numeric_rule_variable`, `@string_rule_variable`)
- ✅ **Export function** - `export_rule_data()` generates metadata for frontend integration
- ✅ **Complex conditions** - Supports nested AND/OR logic
- ✅ **Well-documented** - Clear examples and API reference

#### Cons
- ❌ **Overhead** - Requires upfront variable/action design
- ❌ **Limited operators** - Predefined operators only (can't easily extend)
- ❌ **JSON complexity** - Complex rules become verbose
- ❌ **Performance** - JSON parsing/evaluation overhead for high-volume scenarios

#### Use Case Fit
**Good for**: User-facing rule builder UI where non-technical users need to create/modify rules
**Not ideal for**: Simple pattern matching, high-performance batch processing

#### Example
```python
from business_rules.variables import BaseVariables, string_rule_variable, numeric_rule_variable
from business_rules.actions import BaseActions, rule_action
from business_rules import run_all

class TransactionVariables(BaseVariables):
    def __init__(self, transaction):
        self.transaction = transaction

    @string_rule_variable
    def payee(self):
        return self.transaction.payee

    @string_rule_variable
    def description(self):
        return self.transaction.description

    @numeric_rule_variable
    def amount(self):
        return self.transaction.amount

class TransactionActions(BaseActions):
    @rule_action(params={"category_id": FIELD_NUMERIC})
    def set_category(self, category_id):
        self.transaction.category_id = category_id

# JSON rule
rule = {
    "conditions": {
        "all": [
            {"name": "payee", "operator": "contains", "value": "AMAZON"}
        ]
    },
    "actions": [
        {"name": "set_category", "params": {"category_id": 5}}
    ]
}

run_all(rule_list=[rule],
        defined_variables=TransactionVariables(transaction),
        defined_actions=TransactionActions(transaction))
```

---

### 2. python-simple-rules-engine

**Repository**: [github.com/rogervila/python_simple_rules_engine](https://github.com/rogervila/python_simple_rules_engine)
**PyPI**: [pypi.org/project/python-simple-rules-engine/](https://pypi.org/project/python-simple-rules-engine/)

#### Pros
- ✅ **Lightweight** - Minimal dependencies, simple API
- ✅ **Chainable** - Rules execute in sequence with state passing
- ✅ **History tracking** - Optional debugging/logging of rule chain
- ✅ **Flexible** - Easy to extend with custom rule logic
- ✅ **MIT License** - Permissive open source

#### Cons
- ❌ **Code-based** - Rules are Python classes, not configurable without code deploy
- ❌ **Low activity** - Last updated Nov 2023, appears dormant
- ❌ **No UI integration** - Would need custom serialization for database storage
- ❌ **Minimal docs** - Basic examples only

#### Use Case Fit
**Good for**: Developer-defined rules, quick prototyping, simple pattern matching
**Not ideal for**: User-configurable rules, non-technical users

#### Example
```python
from python_simple_rules_engine import AbstractRule, Evaluation, run

class AmazonRule(AbstractRule):
    def evaluate(self, subject):
        if 'AMAZON' in subject.payee.upper():
            return Evaluation(
                result={'category_id': 5},
                stop=False  # Continue to next rule
            )
        return Evaluation(result={}, stop=False)

class StarbuсksRule(AbstractRule):
    def evaluate(self, subject):
        if 'STARBUCKS' in subject.payee.upper():
            return Evaluation(
                result={'category_id': 8},
                stop=True  # Stop processing
            )
        return Evaluation(result={}, stop=False)

rules = [AmazonRule(), StarbucksRule()]
result = run(subject=transaction, rules=rules)
```

---

### 3. business-rule-engine

**PyPI**: [pypi.org/project/business-rule-engine/](https://pypi.org/project/business-rule-engine/)

#### Pros
- ✅ **DSL syntax** - "when/then" conditions and actions
- ✅ **Excel functions** - Supports most Excel formulas
- ✅ **Custom functions** - Register Python functions
- ✅ **Error handling** - Built-in exception handling

#### Cons
- ❌ **Inactive** - Last release Nov 2021 (3+ years ago)
- ❌ **Limited docs** - Sparse documentation
- ❌ **Unknown stability** - No recent updates or maintenance

#### Use Case Fit
**Skip this option** - Lack of maintenance is a red flag for production use

---

### 4. durable-rules

**Repository**: [github.com/jruizgit/rules](https://github.com/jruizgit/rules)
**PyPI**: [pypi.org/project/durable-rules/](https://pypi.org/project/durable-rules/)

#### Pros
- ✅ **Complex Event Processing** - Pattern matching across event streams
- ✅ **Stateful sessions** - Maintains state across rule evaluations
- ✅ **High performance** - Designed for real-time analytics

#### Cons
- ❌ **Over-engineered** - Too complex for simple transaction categorization
- ❌ **Questionable maintenance** - Concerns about ongoing support
- ❌ **Learning curve** - Complex API and concepts
- ❌ **Overkill** - We don't need CEP for transaction categorization

#### Use Case Fit
**Not recommended** - Too complex for our needs; designed for real-time event processing, not batch categorization

---

## Real-World Transaction Categorization Patterns

Based on research from existing financial apps and systems:

### Pattern 1: Payee Matching (Most Common)
```
IF payee CONTAINS "AMAZON" THEN category = "Shopping"
IF payee STARTS_WITH "DOORDASH*" THEN category = "Restaurants"
IF payee MATCHES_REGEX "UBER|LYFT" THEN category = "Transportation"
```

### Pattern 2: Amount-Based Rules
```
IF payee CONTAINS "VENMO" AND amount < 20 THEN category = "Misc"
IF amount > 1000 AND type = "CREDIT" THEN category = "Income"
```

### Pattern 3: Combined Conditions
```
IF (payee CONTAINS "SAFEWAY" OR description CONTAINS "GROCERY")
   AND amount < 200
   THEN category = "Groceries"
```

### Pattern 4: Description Pattern Matching
```
IF description MATCHES "ACH TRANSFER.*PAYROLL" THEN category = "Income"
IF description CONTAINS "ATM WITHDRAWAL" THEN category = "Cash"
```

### Industry Insights

From research sources:
- **35% of transactions** can be categorized using a lookup table of the 100 most common merchants
- **65% remaining** require pattern matching, regex, or ML-based classification
- **Bayesian classifiers** are commonly used (GnuCash) for learning from user behavior
- **Regular expressions** are the most common approach for flexible pattern matching

Sources:
- [Transaction Categorisation using Machine Learning](https://zsviews.wordpress.com/2019/01/30/transaction-categorisation-using-machine-learning/)
- [Python Rule Engines: Top 5 for Your Projects in 2025](https://www.nected.ai/us/blog-us/python-rule-engines-automate-and-enforce-with-python)
- [Python Rule Engine: Logic Automation & Examples](https://djangostars.com/blog/python-rule-engine/)

---

## Recommendation: Custom Lightweight Solution

Given our specific needs, I recommend building a **custom lightweight rules engine** tailored for transaction categorization:

### Why Custom?

1. **Simple requirements** - We need basic pattern matching and conditionals
2. **Database-backed** - Rules should be stored in PostgreSQL, not JSON files
3. **User-configurable** - Users should create/edit rules via UI
4. **Performance** - Batch processing thousands of transactions efficiently
5. **Maintainability** - Full control over features and dependencies

### Proposed Architecture

#### Database Schema

```sql
CREATE TABLE categorization_rules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    priority INTEGER DEFAULT 0,  -- Higher priority = runs first
    enabled BOOLEAN DEFAULT TRUE,

    -- Conditions (all must match)
    payee_pattern VARCHAR(255),          -- NULL = skip this condition
    payee_match_type VARCHAR(20),        -- 'contains', 'starts_with', 'ends_with', 'regex', 'exact'
    description_pattern VARCHAR(255),
    description_match_type VARCHAR(20),
    amount_min NUMERIC(10, 2),
    amount_max NUMERIC(10, 2),
    transaction_type VARCHAR(20),        -- 'DEBIT', 'CREDIT', 'TRANSFER'

    -- Actions (what to apply when conditions match)
    category_id INTEGER REFERENCES categories(id),
    new_payee VARCHAR(200),              -- Optional: rename payee
    notes_append TEXT,                   -- Optional: add to notes

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_matched_at TIMESTAMP,           -- Track when rule last matched
    match_count INTEGER DEFAULT 0,       -- Track rule effectiveness

    INDEX idx_rules_user_enabled (user_id, enabled, priority DESC)
);
```

#### Python Rule Engine Service

```python
class RuleEngine:
    def __init__(self, db: Session):
        self.db = db

    def get_active_rules(self, user_id: int) -> List[Rule]:
        """Get all active rules for user, ordered by priority"""
        return self.db.query(Rule).filter(
            Rule.user_id == user_id,
            Rule.enabled == True
        ).order_by(Rule.priority.desc()).all()

    def evaluate_transaction(self, transaction: Transaction, rules: List[Rule]) -> Optional[Rule]:
        """Find first matching rule for transaction"""
        for rule in rules:
            if self._rule_matches(transaction, rule):
                return rule
        return None

    def _rule_matches(self, transaction: Transaction, rule: Rule) -> bool:
        """Check if all rule conditions match transaction"""
        # Payee matching
        if rule.payee_pattern:
            if not self._text_matches(transaction.payee, rule.payee_pattern, rule.payee_match_type):
                return False

        # Description matching
        if rule.description_pattern:
            if not self._text_matches(transaction.description, rule.description_pattern, rule.description_match_type):
                return False

        # Amount range
        if rule.amount_min and transaction.amount < rule.amount_min:
            return False
        if rule.amount_max and transaction.amount > rule.amount_max:
            return False

        # Transaction type
        if rule.transaction_type and transaction.type != rule.transaction_type:
            return False

        return True

    def _text_matches(self, text: str, pattern: str, match_type: str) -> bool:
        """Match text against pattern using specified match type"""
        if not text:
            return False

        text_lower = text.lower()
        pattern_lower = pattern.lower()

        if match_type == 'contains':
            return pattern_lower in text_lower
        elif match_type == 'starts_with':
            return text_lower.startswith(pattern_lower)
        elif match_type == 'ends_with':
            return text_lower.endswith(pattern_lower)
        elif match_type == 'exact':
            return text_lower == pattern_lower
        elif match_type == 'regex':
            import re
            return bool(re.search(pattern, text, re.IGNORECASE))

        return False

    def apply_rule(self, transaction: Transaction, rule: Rule):
        """Apply rule actions to transaction"""
        if rule.category_id:
            transaction.category_id = rule.category_id

        if rule.new_payee:
            transaction.payee = rule.new_payee

        if rule.notes_append:
            if transaction.notes:
                transaction.notes += f"\n{rule.notes_append}"
            else:
                transaction.notes = rule.notes_append

        # Update rule statistics
        rule.last_matched_at = datetime.utcnow()
        rule.match_count += 1

    def categorize_transactions(self, user_id: int, transactions: List[Transaction]) -> Dict[str, int]:
        """Apply rules to multiple transactions, return stats"""
        rules = self.get_active_rules(user_id)
        stats = {
            'categorized': 0,
            'uncategorized': 0,
            'rules_matched': set()
        }

        for transaction in transactions:
            # Skip if already categorized
            if transaction.category_id:
                continue

            matching_rule = self.evaluate_transaction(transaction, rules)
            if matching_rule:
                self.apply_rule(transaction, matching_rule)
                stats['categorized'] += 1
                stats['rules_matched'].add(matching_rule.id)
            else:
                stats['uncategorized'] += 1

        return {
            'categorized': stats['categorized'],
            'uncategorized': stats['uncategorized'],
            'rules_used': len(stats['rules_matched'])
        }
```

### Advantages of Custom Solution

1. **Tailored to our needs** - No unnecessary features or complexity
2. **Database-native** - Rules stored in PostgreSQL, queryable and reportable
3. **User statistics** - Track which rules are effective (`match_count`, `last_matched_at`)
4. **Performance** - Optimized for batch processing during import
5. **Extensible** - Easy to add new condition types or actions
6. **UI-friendly** - Simple schema maps directly to form fields
7. **No external dependencies** - Just Python + SQLAlchemy + regex
8. **Testable** - Easy to write unit tests for rule matching logic

### Phased Implementation

**Phase 1: Core Engine (MVP)**
- Rule model and database schema
- Basic pattern matching (contains, starts_with, exact)
- Category assignment action
- API endpoints for CRUD operations

**Phase 2: Advanced Matching**
- Regex support
- Amount range conditions
- Transaction type filtering
- Priority/ordering

**Phase 3: UI Integration**
- Rule builder form
- Rule testing/preview
- Rule statistics dashboard
- Bulk apply rules to existing transactions

**Phase 4: Smart Features**
- Rule suggestions based on user patterns
- Duplicate rule detection
- Rule optimization suggestions
- Machine learning categorization fallback

---

## Alternative: Hybrid Approach

If we want the benefits of an existing library + custom features:

Use **python-simple-rules-engine** as the foundation, but:
1. Store rule definitions in database as JSON
2. Dynamically instantiate rule classes from JSON
3. Add our own condition/action types
4. Build UI for rule configuration

This gives us:
- ✅ Battle-tested rule execution logic
- ✅ Chainable rules with history
- ✅ Flexibility to extend
- ✅ Database-backed storage
- ⚠️ Additional complexity of JSON serialization

---

## Conclusion

**Primary Recommendation**: Build a **custom lightweight rules engine** specifically designed for transaction categorization.

**Rationale**:
- Our requirements are simple and well-defined
- Existing libraries are either over-engineered or under-maintained
- Custom solution gives us full control and optimal performance
- Database-backed rules enable powerful user features
- No risk of library abandonment or breaking changes

**Estimated Effort**:
- Phase 1 (MVP): 6-8 hours
- Phase 2 (Advanced): 4-6 hours
- Phase 3 (UI): 8-10 hours
- **Total**: ~20 hours for full-featured rules engine

**Next Steps**:
1. Review and approve this approach
2. Design database schema in detail
3. Implement core RuleEngine service (TDD)
4. Create API endpoints
5. Build frontend rule builder UI

---

## Sources

- [Python Rule Engine: Top 7 for Automation - Nected](https://www.nected.ai/blog/python-rule-engines-automate-and-enforce-with-python)
- [business-rules PyPI](https://pypi.org/project/business-rules/)
- [business-rules GitHub](https://github.com/venmo/business-rules)
- [business-rule-engine PyPI](https://pypi.org/project/business-rule-engine/)
- [durable-rules PyPI](https://pypi.org/project/durable-rules/)
- [durable-rules GitHub](https://github.com/jruizgit/rules)
- [python-simple-rules-engine GitHub](https://github.com/rogervila/python_simple_rules_engine)
- [python-simple-rules-engine PyPI](https://pypi.org/project/python-simple-rules-engine/)
- [Transaction Categorisation using Machine Learning](https://zsviews.wordpress.com/2019/01/30/transaction-categorisation-using-machine-learning/)
- [Python Rule Engines: Top 5 for Your Projects in 2025](https://www.nected.ai/us/blog-us/python-rule-engines-automate-and-enforce-with-python)
- [Django Stars: Python Rule Engine](https://djangostars.com/blog/python-rule-engine/)
- [GoRules: Open-source Business Rules Engine](https://gorules.io/)
