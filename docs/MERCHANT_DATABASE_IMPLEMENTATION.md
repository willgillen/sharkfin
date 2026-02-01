# Known Merchants Database Implementation Strategy

## Overview

This document outlines the implementation strategy for expanding the known merchants database from ~40 merchants to 1,000+ merchants while maintaining full integration with the existing payee system.

## Current System Architecture

### Components Involved

| Component | Location | Purpose |
|-----------|----------|---------|
| **known_merchants.json** | `backend/app/config/known_merchants.json` | Pattern matching for merchant recognition |
| **PayeeExtractionService** | `backend/app/services/payee_extraction_service.py` | Cleans transaction descriptions, uses known_merchants.json |
| **PayeeCategorySuggestionService** | `backend/app/services/payee_category_suggestion_service.py` | 800+ keyword-to-category mappings for fallback |
| **PayeeIconService** | `backend/app/services/payee_icon_service.py` | 500+ brand logos (Simple Icons) + emoji fallbacks |
| **PayeeService** | `backend/app/services/payee_service.py` | Creates/finds payees, auto-assigns icons |
| **find_category_by_name()** | `backend/app/api/v1/imports.py` | Maps category names to user's actual categories |

### Data Flow During Import

```
Transaction Description
    │
    ▼
PayeeExtractionService.extract_payee_name_with_category()
    │
    ├─► Check known_merchants.json patterns (regex)
    │   └─► If MATCH: Return (merchant_name, 0.95 confidence, category)
    │
    └─► If NO MATCH: Apply cleaning pipeline + PayeeCategorySuggestionService
        └─► Return (cleaned_name, confidence, suggested_category)
    │
    ▼
PayeeService.get_or_create()
    │
    ├─► Normalize name
    ├─► Check for existing payee
    └─► If NEW: PayeeIconService.suggest_icon()
        └─► Return Payee with auto-assigned logo_url
    │
    ▼
find_category_by_name()
    │
    └─► Map category name → user's category ID via aliases
    │
    ▼
Create Transaction with payee_id + category_id
```

## Implementation Strategy

### Approach: Split JSON Files by Category

**Why this approach:**
- ✅ Maintains existing JSON-based architecture (no database changes)
- ✅ Easy to maintain and extend (edit individual category files)
- ✅ Version control friendly (smaller diffs when updating)
- ✅ Fast load time (loaded once at startup, cached in memory)
- ✅ No external dependencies
- ✅ Community contribution friendly

### File Structure

```
backend/app/config/
├── known_merchants.json                    # DEPRECATED - kept for backwards compatibility
└── merchants/
    ├── _index.json                         # Master index + metadata
    ├── financial_institutions.json         # 200+ banks, credit unions, investments
    ├── restaurants_fast_food.json          # 150+ fast food chains
    ├── restaurants_casual_dining.json      # 100+ casual dining
    ├── restaurants_coffee_bakery.json      # 75+ coffee shops, bakeries
    ├── grocery_supermarkets.json           # 100+ grocery stores
    ├── retail_department.json              # 75+ department stores
    ├── retail_online.json                  # 50+ e-commerce
    ├── retail_specialty.json               # 75+ specialty retail
    ├── gas_stations.json                   # 50+ gas/fuel stations
    ├── transportation.json                 # 50+ rideshare, rental, transit
    ├── airlines_travel.json                # 75+ airlines, hotels, travel
    ├── utilities.json                      # 50+ electric, gas, water, telecom
    ├── subscriptions_streaming.json        # 50+ streaming services
    ├── subscriptions_software.json         # 50+ software/SaaS
    ├── healthcare_pharmacy.json            # 50+ pharmacies, hospitals
    ├── insurance.json                      # 50+ insurance companies
    ├── fitness_wellness.json               # 50+ gyms, wellness
    └── services.json                       # 50+ professional services
```

**Estimated Total: 1,200+ merchants**

### Enhanced Schema

```json
{
  "category_file": "financial_institutions",
  "version": "1.0",
  "last_updated": "2025-01-26",
  "merchants": [
    {
      "pattern": "\\bCHASE\\b",
      "name": "Chase Bank",
      "category": "bank",
      "simple_icons_slug": "chase",
      "aliases": ["JPMorgan Chase", "JP Morgan", "JPMC"]
    },
    {
      "pattern": "\\bBANK\\s*OF\\s*AMERICA\\b|\\bBOFA\\b",
      "name": "Bank of America",
      "category": "bank",
      "simple_icons_slug": "bankofamerica",
      "aliases": ["BofA", "BOFA", "B of A"]
    }
  ]
}
```

**Schema Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `pattern` | Yes | Regex pattern for matching transaction descriptions |
| `name` | Yes | Canonical payee name (properly capitalized) |
| `category` | Yes | Category slug for find_category_by_name() lookup |
| `simple_icons_slug` | No | Links to PayeeIconService for brand logo |
| `aliases` | No | Alternative names for fuzzy matching |

### Loading Strategy

Update `PayeeExtractionService._load_known_merchants()`:

```python
def _load_known_merchants(self) -> List[Tuple[str, str, Optional[str]]]:
    """
    Load known merchant patterns from JSON config files.

    Supports both legacy single-file and new multi-file structure.
    """
    config_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'config'
    )

    merchants = []

    # Try new multi-file structure first
    merchants_dir = os.path.join(config_dir, 'merchants')
    if os.path.isdir(merchants_dir):
        for filename in os.listdir(merchants_dir):
            if filename.endswith('.json') and not filename.startswith('_'):
                filepath = os.path.join(merchants_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        for merchant in data.get('merchants', []):
                            pattern = merchant.get('pattern')
                            name = merchant.get('name')
                            category = merchant.get('category')
                            if pattern and name:
                                merchants.append((pattern, name, category))
                except Exception as e:
                    print(f"Error loading {filename}: {e}")

    # Fall back to legacy single file
    if not merchants:
        legacy_path = os.path.join(config_dir, 'known_merchants.json')
        # ... existing loading logic ...

    return merchants
```

## Integration Points

### 1. Category Mapping

The `category` field in merchants JSON must map to entries in `find_category_by_name()` aliases.

**Current supported categories:**
- `transportation`, `auto & transport`, `gas & fuel`
- `restaurants`, `fast_food`, `coffee shops`, `food delivery`, `groceries`
- `shopping`, `retail`
- `entertainment`
- `utilities`, `phone & internet`
- `health & medical`, `gym & fitness`
- `personal care`
- `home services`
- `insurance`
- `travel`
- `education`
- `subscriptions`
- `fees & charges`
- `gifts & donations`
- `pets`
- `childcare`
- `taxes`, `legal`

**New categories to add to find_category_by_name():**
- `bank` → ['Bank', 'Banking', 'Finance', 'Financial']
- `credit_card` → ['Credit Card', 'Credit Cards', 'Finance']
- `investment` → ['Investment', 'Investments', 'Finance', 'Brokerage']
- `pharmacy` → ['Pharmacy', 'Health & Medical', 'Healthcare']
- `airline` → ['Airline', 'Airlines', 'Travel', 'Air Travel']
- `hotel` → ['Hotel', 'Hotels', 'Travel', 'Lodging']
- `streaming` → ['Streaming', 'Entertainment', 'Subscriptions']
- `software` → ['Software', 'Subscriptions', 'Technology']

### 2. Icon Integration

The `simple_icons_slug` field enables automatic brand logo assignment:

```python
# In PayeeService.get_or_create(), icon is auto-assigned via PayeeIconService
# The PayeeIconService.BRAND_MAPPINGS already contains 500+ brands

# Merchants JSON can specify slug to GUARANTEE icon match:
{
  "pattern": "\\bCHASE\\b",
  "name": "Chase Bank",
  "simple_icons_slug": "chase"  # Ensures https://cdn.simpleicons.org/chase/117ACA
}
```

**Implementation in PayeeIconService:**

Add method to check for explicit slug:
```python
def suggest_icon_with_slug(self, payee_name: str, slug_hint: Optional[str] = None) -> dict:
    """Suggest icon with optional explicit slug override."""
    if slug_hint and slug_hint in self._known_slugs:
        # Use explicit slug from merchants config
        color = self._get_slug_color(slug_hint)
        return {
            "icon_type": "brand",
            "icon_value": f"{self.SIMPLE_ICONS_CDN}/{slug_hint}/{color}",
            ...
        }
    # Fall back to normal matching
    return self.suggest_icon(payee_name)
```

### 3. PayeeCategorySuggestionService Integration

The existing service has 800+ keyword mappings. The known_merchants.json takes **priority** over this service:

1. **known_merchants.json** - Exact pattern matches (highest priority)
2. **PayeeCategorySuggestionService** - Keyword-based suggestions (fallback)

No changes needed - the priority is already implemented in `PayeeExtractionService`.

## Implementation Checklist

### Phase 1: Infrastructure Updates

- [ ] Create `backend/app/config/merchants/` directory
- [ ] Update `PayeeExtractionService._load_known_merchants()` for multi-file support
- [ ] Add new category mappings to `find_category_by_name()`
- [ ] Update `PayeeIconService` to accept explicit slug hints
- [ ] Create `_index.json` with metadata and validation schema

### Phase 2: Merchant Data Files

- [ ] Create `financial_institutions.json` (200+ banks, credit unions, brokerages)
- [ ] Create `restaurants_fast_food.json` (150+ chains)
- [ ] Create `restaurants_casual_dining.json` (100+ chains)
- [ ] Create `restaurants_coffee_bakery.json` (75+ coffee/bakery)
- [ ] Create `grocery_supermarkets.json` (100+ grocery stores)
- [ ] Create `retail_department.json` (75+ department stores)
- [ ] Create `retail_online.json` (50+ e-commerce)
- [ ] Create `retail_specialty.json` (75+ specialty)
- [ ] Create `gas_stations.json` (50+ gas stations)
- [ ] Create `transportation.json` (50+ rideshare, rental, transit)
- [ ] Create `airlines_travel.json` (75+ airlines, hotels)
- [ ] Create `utilities.json` (50+ utilities, telecom)
- [ ] Create `subscriptions_streaming.json` (50+ streaming)
- [ ] Create `subscriptions_software.json` (50+ software)
- [ ] Create `healthcare_pharmacy.json` (50+ healthcare)
- [ ] Create `insurance.json` (50+ insurance)
- [ ] Create `fitness_wellness.json` (50+ fitness)
- [ ] Create `services.json` (50+ professional services)

### Phase 3: Testing & Validation

- [ ] Add unit tests for multi-file loading
- [ ] Add validation for merchant JSON schema
- [ ] Test category mapping for all new categories
- [ ] Test icon assignment for merchants with `simple_icons_slug`
- [ ] Integration test: import CSV with known merchants
- [ ] Performance test: ensure startup time is acceptable

### Phase 4: Documentation & Cleanup

- [ ] Update CLAUDE.md with merchant contribution guidelines
- [ ] Document JSON schema for community contributions
- [ ] Deprecate legacy `known_merchants.json` (keep for backwards compatibility)
- [ ] Add merchant count to admin dashboard

## Financial Institutions Focus

Since this is a financial app, special attention to financial institutions:

### Banks (Major US)
- Big 4: Chase, Bank of America, Wells Fargo, Citi
- Regional: PNC, US Bank, Truist, Capital One, TD Bank
- Online: Ally, Chime, SoFi, Marcus, Discover

### Credit Unions
- Navy Federal, Pentagon Federal, BECU, Alliant, etc.

### Investment/Brokerage
- Fidelity, Vanguard, Charles Schwab, TD Ameritrade, E*Trade
- Robinhood, Webull, M1 Finance, Acorns, Stash

### Credit Cards
- Amex, Discover, Capital One (specific card patterns)
- Payment patterns: "PAYMENT THANK YOU", "AUTOPAY"

### Payment Processors
- PayPal, Venmo, Zelle, Cash App, Square, Stripe

### Pattern Examples for Financial Institutions

```json
{
  "pattern": "\\bCHASE\\s*(CREDIT|CARD)?\\s*(PAYMENT|AUTOPAY)?\\b",
  "name": "Chase Bank",
  "category": "bank",
  "simple_icons_slug": "chase"
},
{
  "pattern": "\\bFIDELITY\\s*(INVESTMENTS?|BROKERAGE)?\\b",
  "name": "Fidelity Investments",
  "category": "investment",
  "simple_icons_slug": "fidelity"
},
{
  "pattern": "\\bVENMO\\b|\\bPAYPAL\\s*\\*\\s*VENMO\\b",
  "name": "Venmo",
  "category": "transfer",
  "simple_icons_slug": "venmo"
}
```

## Performance Considerations

### Load Time
- 1,200 merchants × ~200 bytes = ~240KB JSON
- Single-threaded load at startup: <100ms expected
- Cached in memory for duration of app lifecycle

### Pattern Matching
- 1,200 regex patterns checked sequentially
- Worst case: 1,200 regex matches per transaction
- Optimization: Pre-compile all patterns at load time
- Further optimization (if needed): Aho-Corasick algorithm for multi-pattern matching

### Memory Usage
- Compiled patterns: ~1-2MB
- Merchant tuples: ~300KB
- Total additional memory: <5MB

## Conclusion

This implementation strategy:

1. **Preserves existing architecture** - No database changes, just JSON files
2. **Integrates with all existing services** - PayeeIconService, PayeeCategorySuggestionService
3. **Scales to 1,000+ merchants** - Split files for maintainability
4. **Prioritizes financial institutions** - Critical for a finance app
5. **Enables community contributions** - Easy to add merchants via JSON
6. **Maintains backwards compatibility** - Legacy file still works

The implementation can be done incrementally:
1. Infrastructure changes first
2. Add merchant files one category at a time
3. Test and validate each category
4. Full deployment when all categories complete
