#!/bin/bash

# Test script for Import API endpoints
# Run this after starting the backend server

BASE_URL="http://localhost:8001"
API_URL="${BASE_URL}/api/v1"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0

# Function to print test results
print_result() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
    fi
}

echo "======================================="
echo "Shark Fin Import API Tests"
echo "======================================="
echo ""

# Step 1: Login to get access token
echo -e "${YELLOW}Step 1: Authenticating...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo@sharkfin.com&password=demo123")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}Failed to authenticate! Cannot proceed with tests.${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Authentication successful${NC}"
echo ""

# Step 2: Get user's first account ID
echo -e "${YELLOW}Step 2: Getting test account...${NC}"
ACCOUNTS_RESPONSE=$(curl -s -X GET "${API_URL}/accounts" \
  -H "Authorization: Bearer $TOKEN")

ACCOUNT_ID=$(echo $ACCOUNTS_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$ACCOUNT_ID" ]; then
    echo -e "${RED}No accounts found! Please create an account first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Using account ID: $ACCOUNT_ID${NC}"
echo ""

# Step 3: Test CSV Preview - Mint Format
echo -e "${YELLOW}Step 3: Testing CSV Preview (Mint format)...${NC}"
CSV_PREVIEW=$(curl -s -X POST "${API_URL}/imports/csv/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample-mint.csv")

if echo "$CSV_PREVIEW" | grep -q "detected_format"; then
    FORMAT=$(echo $CSV_PREVIEW | grep -o '"detected_format":"[^"]*' | cut -d'"' -f4)
    ROW_COUNT=$(echo $CSV_PREVIEW | grep -o '"row_count":[0-9]*' | cut -d':' -f2)
    print_result 0 "CSV Preview - Format: $FORMAT, Rows: $ROW_COUNT"
else
    print_result 1 "CSV Preview failed"
    echo "Response: $CSV_PREVIEW"
fi
echo ""

# Step 4: Test CSV Preview - Chase Format
echo -e "${YELLOW}Step 4: Testing CSV Preview (Chase format)...${NC}"
CHASE_PREVIEW=$(curl -s -X POST "${API_URL}/imports/csv/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample-chase.csv")

if echo "$CHASE_PREVIEW" | grep -q "detected_format"; then
    FORMAT=$(echo $CHASE_PREVIEW | grep -o '"detected_format":"[^"]*' | cut -d'"' -f4)
    ROW_COUNT=$(echo $CHASE_PREVIEW | grep -o '"row_count":[0-9]*' | cut -d':' -f2)
    print_result 0 "CSV Preview (Chase) - Format: $FORMAT, Rows: $ROW_COUNT"
else
    print_result 1 "CSV Preview (Chase) failed"
fi
echo ""

# Step 5: Test OFX Preview
echo -e "${YELLOW}Step 5: Testing OFX Preview...${NC}"
OFX_PREVIEW=$(curl -s -X POST "${API_URL}/imports/ofx/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample-bank.ofx")

if echo "$OFX_PREVIEW" | grep -q "transaction_count"; then
    TXN_COUNT=$(echo $OFX_PREVIEW | grep -o '"transaction_count":[0-9]*' | cut -d':' -f2)
    ACCOUNT_TYPE=$(echo $OFX_PREVIEW | grep -o '"account_type":"[^"]*' | cut -d'"' -f4)
    print_result 0 "OFX Preview - Type: $ACCOUNT_TYPE, Transactions: $TXN_COUNT"
else
    print_result 1 "OFX Preview failed"
    echo "Response: $OFX_PREVIEW"
fi
echo ""

# Step 6: Test CSV Import Execution (Generic format)
echo -e "${YELLOW}Step 6: Testing CSV Import Execution...${NC}"
COLUMN_MAPPING='{"date":"Date","amount":"Amount","description":"Description","payee":"Payee"}'

IMPORT_RESULT=$(curl -s -X POST "${API_URL}/imports/csv/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample-generic.csv" \
  -F "account_id=$ACCOUNT_ID" \
  -F "column_mapping=$COLUMN_MAPPING" \
  -F "skip_rows=[]")

if echo "$IMPORT_RESULT" | grep -q "import_id"; then
    IMPORT_ID=$(echo $IMPORT_RESULT | grep -o '"import_id":[0-9]*' | cut -d':' -f2)
    IMPORTED=$(echo $IMPORT_RESULT | grep -o '"imported_count":[0-9]*' | cut -d':' -f2)
    print_result 0 "CSV Import - Import ID: $IMPORT_ID, Imported: $IMPORTED transactions"

    # Save import ID for later tests
    CSV_IMPORT_ID=$IMPORT_ID
else
    print_result 1 "CSV Import failed"
    echo "Response: $IMPORT_RESULT"
fi
echo ""

# Step 7: Test OFX Import Execution
echo -e "${YELLOW}Step 7: Testing OFX Import Execution...${NC}"
OFX_IMPORT=$(curl -s -X POST "${API_URL}/imports/ofx/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample-bank.ofx" \
  -F "account_id=$ACCOUNT_ID" \
  -F "skip_rows=[]")

if echo "$OFX_IMPORT" | grep -q "import_id"; then
    IMPORT_ID=$(echo $OFX_IMPORT | grep -o '"import_id":[0-9]*' | cut -d':' -f2)
    IMPORTED=$(echo $OFX_IMPORT | grep -o '"imported_count":[0-9]*' | cut -d':' -f2)
    print_result 0 "OFX Import - Import ID: $IMPORT_ID, Imported: $IMPORTED transactions"

    # Save import ID for later tests
    OFX_IMPORT_ID=$IMPORT_ID
else
    print_result 1 "OFX Import failed"
    echo "Response: $OFX_IMPORT"
fi
echo ""

# Step 8: Test Import History
echo -e "${YELLOW}Step 8: Testing Import History...${NC}"
HISTORY=$(curl -s -X GET "${API_URL}/imports/history" \
  -H "Authorization: Bearer $TOKEN")

if echo "$HISTORY" | grep -q "import_type"; then
    HISTORY_COUNT=$(echo $HISTORY | grep -o '"id":[0-9]*' | wc -l)
    print_result 0 "Import History - Found $HISTORY_COUNT imports"
else
    print_result 1 "Import History failed"
fi
echo ""

# Step 9: Test Duplicate Detection
echo -e "${YELLOW}Step 9: Testing Duplicate Detection...${NC}"
DUPLICATES=$(curl -s -X POST "${API_URL}/imports/csv/detect-duplicates" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample-generic.csv" \
  -F "account_id=$ACCOUNT_ID" \
  -F "column_mapping=$COLUMN_MAPPING")

if echo "$DUPLICATES" | grep -q "total_duplicates"; then
    DUP_COUNT=$(echo $DUPLICATES | grep -o '"total_duplicates":[0-9]*' | cut -d':' -f2)
    print_result 0 "Duplicate Detection - Found $DUP_COUNT potential duplicates"
else
    print_result 1 "Duplicate Detection failed"
    echo "Response: $DUPLICATES"
fi
echo ""

# Step 10: Test Rollback
if [ ! -z "$CSV_IMPORT_ID" ]; then
    echo -e "${YELLOW}Step 10: Testing Import Rollback...${NC}"
    ROLLBACK=$(curl -s -X DELETE "${API_URL}/imports/history/$CSV_IMPORT_ID" \
      -H "Authorization: Bearer $TOKEN")

    if echo "$ROLLBACK" | grep -q "rolled back successfully"; then
        print_result 0 "Import Rollback successful"
    else
        print_result 1 "Import Rollback failed"
        echo "Response: $ROLLBACK"
    fi
    echo ""
fi

# Final Summary
echo "======================================="
echo -e "Test Results: ${GREEN}$PASSED_TESTS${NC}/${TOTAL_TESTS} passed"
echo "======================================="

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi
