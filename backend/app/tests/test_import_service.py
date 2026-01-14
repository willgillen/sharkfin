import pytest
from io import BytesIO
import pandas as pd
from app.services.import_service import ImportService
from app.schemas.imports import CSVColumnMapping


class TestImportService:
    """Test suite for CSV import functionality"""

    @pytest.fixture
    def import_service(self, db_session):
        """Create an ImportService instance with test database session"""
        return ImportService(db_session)

    def test_parse_csv_with_split_withdrawal_deposit_columns(self, import_service):
        """Test parsing CSV with separate Withdrawal and Deposit columns"""
        csv_data = b"""Date,Status,Type,CheckNumber,Description,Withdrawal,Deposit,RunningBalance
2024-01-15,Posted,Debit,,GROCERY STORE,45.67,,1500.00
2024-01-16,Posted,Credit,,PAYCHECK,,2000.00,3500.00
2024-01-17,Posted,Debit,,ATM WITHDRAWAL,100.00,,3400.00"""

        df = import_service.parse_csv(csv_data)

        assert len(df) == 3
        assert 'Withdrawal' in df.columns
        assert 'Deposit' in df.columns
        assert df.iloc[0]['Description'] == 'GROCERY STORE'

    def test_detect_csv_format_generic(self, import_service):
        """Test format detection for generic CSV with split columns"""
        csv_data = b"""Date,Description,Withdrawal,Deposit
2024-01-15,TEST,100.00,"""

        df = import_service.parse_csv(csv_data)
        format_type = import_service.detect_csv_format(df)

        assert format_type == "generic"

    def test_suggest_mapping_for_split_columns(self, import_service):
        """Test column mapping suggestion for split Withdrawal/Deposit columns"""
        csv_data = b"""Date,Description,Withdrawal,Deposit
2024-01-15,TEST,100.00,"""

        df = import_service.parse_csv(csv_data)
        format_type = import_service.detect_csv_format(df)
        mapping = import_service.get_suggested_mapping(df, format_type)

        assert mapping.date == "Date"
        assert mapping.amount == "Withdrawal|Deposit"  # Combined with pipe
        assert mapping.description == "Description"

    def test_map_transactions_with_split_columns(self, import_service):
        """Test mapping CSV rows to transactions with split amount columns"""
        csv_data = b"""Date,Description,Withdrawal,Deposit
2024-01-15,GROCERY STORE,45.67,
2024-01-16,PAYCHECK,,2000.00
2024-01-17,ATM WITHDRAWAL,100.00,"""

        df = import_service.parse_csv(csv_data)
        format_type = import_service.detect_csv_format(df)
        mapping = import_service.get_suggested_mapping(df, format_type)
        transactions = import_service.map_csv_to_transactions(df, mapping)

        assert len(transactions) == 3

        # First transaction: withdrawal (debit)
        assert transactions[0]['type'] == 'DEBIT'
        assert transactions[0]['amount'] == 45.67
        assert transactions[0]['description'] == 'GROCERY STORE'

        # Second transaction: deposit (credit)
        assert transactions[1]['type'] == 'CREDIT'
        assert transactions[1]['amount'] == 2000.00
        assert transactions[1]['description'] == 'PAYCHECK'

        # Third transaction: withdrawal (debit)
        assert transactions[2]['type'] == 'DEBIT'
        assert transactions[2]['amount'] == 100.00

    def test_skip_rows_with_empty_amounts_both_columns(self, import_service):
        """Test that rows with empty values in both amount columns are skipped"""
        csv_data = b"""Date,Description,Withdrawal,Deposit
2024-01-15,VALID TRANSACTION,45.67,
2024-01-16,INVALID ROW,,
2024-01-17,ANOTHER VALID,100.00,"""

        df = import_service.parse_csv(csv_data)
        mapping = CSVColumnMapping(
            date="Date",
            amount="Withdrawal|Deposit",
            description="Description"
        )
        transactions = import_service.map_csv_to_transactions(df, mapping)

        # Should only have 2 transactions (row with empty amounts skipped)
        assert len(transactions) == 2
        assert transactions[0]['description'] == 'VALID TRANSACTION'
        assert transactions[1]['description'] == 'ANOTHER VALID'

    def test_skip_rows_with_zero_in_both_columns(self, import_service):
        """Test that rows with 0.00 in both amount columns are skipped"""
        csv_data = b"""Date,Description,Withdrawal,Deposit
2024-01-15,VALID TRANSACTION,45.67,
2024-01-16,ZERO ROW,0.00,0.00
2024-01-17,ANOTHER VALID,,100.00"""

        df = import_service.parse_csv(csv_data)
        mapping = CSVColumnMapping(
            date="Date",
            amount="Withdrawal|Deposit",
            description="Description"
        )
        transactions = import_service.map_csv_to_transactions(df, mapping)

        # Should only have 2 transactions (row with zeros skipped)
        assert len(transactions) == 2
        assert transactions[0]['amount'] == 45.67
        assert transactions[1]['amount'] == 100.00

    def test_no_nan_values_in_transaction_amounts(self, import_service):
        """Test that NaN values are never present in transaction amounts"""
        import math

        csv_data = b"""Date,Description,Withdrawal,Deposit
2024-01-15,VALID,45.67,
2024-01-16,EMPTY,,
2024-01-17,SPACES,  ,
2024-01-18,ZEROS,0.00,0.00
2024-01-19,VALID CREDIT,,100.00"""

        df = import_service.parse_csv(csv_data)
        mapping = CSVColumnMapping(
            date="Date",
            amount="Withdrawal|Deposit",
            description="Description"
        )
        transactions = import_service.map_csv_to_transactions(df, mapping)

        # Verify no NaN or infinite values in amounts
        for txn in transactions:
            amount = txn['amount']
            assert isinstance(amount, (int, float))
            assert not math.isnan(amount), f"Transaction has NaN amount: {txn}"
            assert not math.isinf(amount), f"Transaction has infinite amount: {txn}"
            assert amount > 0, f"Transaction has non-positive amount: {txn}"

    def test_parse_amount_returns_none_for_invalid_values(self, import_service):
        """Test _parse_amount method with various invalid inputs"""
        test_cases = [
            ('', None),           # Empty string
            ('nan', None),        # Literal 'nan'
            ('NaN', None),        # Uppercase 'NaN'
            ('none', None),       # 'none'
            ('null', None),       # 'null'
            ('   ', None),        # Whitespace
            ('100.50', 100.50),   # Valid positive
            ('-50.25', -50.25),   # Valid negative
            ('(75.00)', -75.00),  # Parentheses notation
            ('$1,234.56', 1234.56),  # Currency formatting
            ('0', 0.0),           # Zero
            ('0.00', 0.0),        # Zero with decimals
        ]

        for input_val, expected in test_cases:
            result = import_service._parse_amount(input_val)
            assert result == expected, f"Failed for input '{input_val}': expected {expected}, got {result}"

    def test_parse_amount_rejects_nan_and_infinity(self, import_service):
        """Test that _parse_amount explicitly rejects NaN and infinity"""
        import math

        # These should all return None
        invalid_values = [
            'nan',
            'NaN',
            'inf',
            '-inf',
            'infinity',
        ]

        for val in invalid_values:
            result = import_service._parse_amount(val)
            assert result is None, f"_parse_amount should return None for '{val}', got {result}"

    def test_real_bank_csv_format(self, import_service):
        """Test with realistic bank CSV export format"""
        csv_data = b"""Date,Status,Type,CheckNumber,Description,Withdrawal,Deposit,RunningBalance
2024-01-15,Posted,Debit,,GROCERY STORE,45.67,,1500.00
2024-01-16,Posted,Credit,,PAYCHECK,,2000.00,3500.00
2024-01-17,Posted,Debit,,ATM WITHDRAWAL,100.00,,3400.00
2024-01-18,Posted,Debit,,GAS STATION,35.50,,3364.50
2024-01-19,Posted,Debit,,RESTAURANT,25.00,,3339.50
2024-01-20,Posted,Credit,,REFUND,,10.00,3349.50"""

        df = import_service.parse_csv(csv_data)
        format_type = import_service.detect_csv_format(df)
        mapping = import_service.get_suggested_mapping(df, format_type)
        transactions = import_service.map_csv_to_transactions(df, mapping)

        # All 6 transactions should be parsed
        assert len(transactions) == 6

        # Verify transaction types
        debits = [t for t in transactions if t['type'] == 'DEBIT']
        credits = [t for t in transactions if t['type'] == 'CREDIT']
        assert len(debits) == 4  # 4 debit transactions
        assert len(credits) == 2  # 2 credit transactions

        # Verify amounts are positive
        for txn in transactions:
            assert txn['amount'] > 0

        # Verify descriptions are captured
        descriptions = [t['description'] for t in transactions]
        assert 'GROCERY STORE' in descriptions
        assert 'PAYCHECK' in descriptions

    def test_csv_with_various_date_formats(self, import_service):
        """Test parsing CSV with different date formats"""
        csv_data = b"""Date,Description,Amount
2024-01-15,Transaction 1,100.00
01/16/2024,Transaction 2,200.00
01-17-2024,Transaction 3,300.00"""

        df = import_service.parse_csv(csv_data)
        mapping = CSVColumnMapping(
            date="Date",
            amount="Amount",
            description="Description"
        )
        transactions = import_service.map_csv_to_transactions(df, mapping)

        # All 3 should parse successfully
        assert len(transactions) == 3
        assert transactions[0]['date'] == '2024-01-15'
        assert transactions[1]['date'] == '2024-01-16'
        assert transactions[2]['date'] == '2024-01-17'

    def test_csv_encoding_detection(self, import_service):
        """Test CSV encoding detection"""
        # UTF-8 CSV
        csv_data_utf8 = "Date,Description,Amount\n2024-01-15,Café,100.00\n".encode('utf-8')
        encoding = import_service.detect_csv_encoding(csv_data_utf8)
        # chardet might return various encodings that are compatible with UTF-8
        assert encoding is not None
        assert isinstance(encoding, str)
        # Verify the detected encoding can parse the data
        df = import_service.parse_csv(csv_data_utf8)
        assert len(df) == 1

    def test_handle_currency_symbols_and_commas(self, import_service):
        """Test parsing amounts with currency symbols and thousands separators"""
        csv_data = b"""Date,Description,Amount
2024-01-15,Transaction 1,"$1,234.56"
2024-01-16,Transaction 2,"$2,000.00"
2024-01-17,Transaction 3,500"""

        df = import_service.parse_csv(csv_data)
        mapping = CSVColumnMapping(
            date="Date",
            amount="Amount",
            description="Description"
        )
        transactions = import_service.map_csv_to_transactions(df, mapping)

        assert len(transactions) == 3
        assert transactions[0]['amount'] == 1234.56
        assert transactions[1]['amount'] == 2000.00
        assert transactions[2]['amount'] == 500.00

    def test_single_amount_column_format(self, import_service):
        """Test CSV with a single amount column (non-split format)"""
        csv_data = b"""Date,Description,Amount
2024-01-15,EXPENSE,-45.67
2024-01-16,INCOME,2000.00
2024-01-17,EXPENSE,-100.00"""

        df = import_service.parse_csv(csv_data)
        mapping = CSVColumnMapping(
            date="Date",
            amount="Amount",
            description="Description"
        )
        transactions = import_service.map_csv_to_transactions(df, mapping)

        assert len(transactions) == 3
        assert transactions[0]['type'] == 'DEBIT'
        assert transactions[0]['amount'] == 45.67  # Stored as positive
        assert transactions[1]['type'] == 'CREDIT'
        assert transactions[1]['amount'] == 2000.00
        assert transactions[2]['type'] == 'DEBIT'
        assert transactions[2]['amount'] == 100.00

    def test_skip_rows_with_invalid_dates(self, import_service):
        """Test that rows with invalid dates are skipped"""
        csv_data = b"""Date,Description,Amount
2024-01-15,VALID,100.00
INVALID_DATE,SHOULD SKIP,200.00
2024-01-17,VALID,300.00"""

        df = import_service.parse_csv(csv_data)
        mapping = CSVColumnMapping(
            date="Date",
            amount="Amount",
            description="Description"
        )
        transactions = import_service.map_csv_to_transactions(df, mapping)

        # Should only have 2 transactions (row with invalid date skipped)
        assert len(transactions) == 2
        assert transactions[0]['amount'] == 100.00
        assert transactions[1]['amount'] == 300.00
