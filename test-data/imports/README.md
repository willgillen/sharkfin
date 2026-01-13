# Transaction Import Test Data

This directory contains sample files for testing the transaction import functionality.

## Test Files

### CSV Files

1. **sample-mint.csv** - Mint format export
   - 10 transactions
   - Includes: Date, Description, Amount, Transaction Type, Category
   - Auto-detected format: `mint`

2. **sample-chase.csv** - Chase bank format
   - 8 transactions
   - Includes: Transaction Date, Post Date, Description, Category, Amount
   - Auto-detected format: `chase`

3. **sample-generic.csv** - Generic CSV format
   - 7 transactions
   - Simple format with: Date, Amount, Description, Payee
   - Auto-detected format: `generic`

### OFX Files

1. **sample-bank.ofx** - Standard OFX/Quicken format
   - 7 transactions
   - Includes full OFX structure with account info and transactions
   - Contains FITID for duplicate detection

## Running Tests

### Automated Test Script

Run the comprehensive test suite:

```bash
cd test-data/imports
./test_import_api.sh
```

This script tests:
- ✅ Authentication
- ✅ CSV Preview (Mint format)
- ✅ CSV Preview (Chase format)
- ✅ OFX Preview
- ✅ CSV Import Execution
- ✅ OFX Import Execution
- ✅ Import History
- ✅ Duplicate Detection
- ✅ Import Rollback

### Manual Testing with curl

#### 1. Authenticate
```bash
curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo@sharkfin.com&password=demo123"
```

#### 2. Preview CSV
```bash
curl -X POST "http://localhost:8001/api/v1/imports/csv/preview" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@sample-mint.csv"
```

#### 3. Preview OFX
```bash
curl -X POST "http://localhost:8001/api/v1/imports/ofx/preview" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@sample-bank.ofx"
```

#### 4. Detect Duplicates
```bash
curl -X POST "http://localhost:8001/api/v1/imports/csv/detect-duplicates" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@sample-generic.csv" \
  -F "account_id=1" \
  -F 'column_mapping={"date":"Date","amount":"Amount","description":"Description","payee":"Payee"}'
```

#### 5. Execute Import
```bash
curl -X POST "http://localhost:8001/api/v1/imports/csv/execute" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@sample-generic.csv" \
  -F "account_id=1" \
  -F 'column_mapping={"date":"Date","amount":"Amount","description":"Description","payee":"Payee"}' \
  -F "skip_rows=[]"
```

#### 6. View Import History
```bash
curl -X GET "http://localhost:8001/api/v1/imports/history" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 7. Rollback Import
```bash
curl -X DELETE "http://localhost:8001/api/v1/imports/history/IMPORT_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Test Results

All tests passed successfully! ✅

- Format detection works for Mint, Chase, and generic CSV files
- OFX parsing correctly extracts transactions and account info
- Duplicate detection identifies all 7 potential duplicates
- Import execution creates transactions successfully
- Rollback functionality removes imported transactions cleanly

## Supported Bank Formats

The import system auto-detects these formats:

- **Mint** - Intuit Mint exports
- **Chase** - Chase bank exports
- **Bank of America** - BofA transaction exports
- **Wells Fargo** - Wells Fargo exports
- **OFX/QFX** - Quicken and most bank OFX downloads
- **Generic** - Any CSV with date, amount, description columns

## Notes

- The demo account (demo@sharkfin.com / demo123) is used for testing
- Import IDs are auto-generated and tracked in the database
- Duplicate detection uses date (±2 days), amount, and fuzzy description matching
- FITID from OFX files helps prevent duplicate imports from the same bank file
