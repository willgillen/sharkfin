"""
Tests for amount sign consistency in CSV and OFX imports.

These tests verify that transaction amounts are correctly interpreted
based on account type and transaction type, ensuring consistent behavior
across different import sources.
"""

import pytest
from io import BytesIO
from decimal import Decimal
from app.services.import_service import ImportService
from app.services.ofx_service import OFXService
from app.schemas.imports import CSVColumnMapping


class TestAmountSignConsistency:
    """Test suite for amount sign consistency across import types."""

    def test_csv_checking_account_debit_negative(self, db_session):
        """Checking account: Debit (withdrawal) should have negative amount in CSV, stored as positive with DEBIT type"""
        import_service = ImportService(db_session)

        # Simulate CSV with negative amount (withdrawal from checking)
        csv_data = """Date,Amount,Description
2024-01-15,-50.00,Grocery Store
"""
        df = import_service.parse_csv(csv_data.encode())
        mapping = CSVColumnMapping(
            date="Date",
            amount="Amount",
            description="Description"
        )

        transactions = import_service.map_csv_to_transactions(df, mapping)

        assert len(transactions) == 1
        assert transactions[0]['amount'] == 50.00  # Stored as positive
        assert transactions[0]['type'] == 'DEBIT'  # Type indicates direction

    def test_csv_checking_account_credit_positive(self, db_session):
        """Checking account: Credit (deposit) should have positive amount, stored as positive with CREDIT type"""
        import_service = ImportService(db_session)

        csv_data = """Date,Amount,Description
2024-01-15,1000.00,Paycheck Deposit
"""
        df = import_service.parse_csv(csv_data.encode())
        mapping = CSVColumnMapping(
            date="Date",
            amount="Amount",
            description="Description"
        )

        transactions = import_service.map_csv_to_transactions(df, mapping)

        assert len(transactions) == 1
        assert transactions[0]['amount'] == 1000.00
        assert transactions[0]['type'] == 'CREDIT'

    def test_csv_split_columns_checking_account(self, db_session):
        """Split debit/credit columns: Withdrawals and deposits correctly typed"""
        import_service = ImportService(db_session)

        csv_data = """Date,Withdrawal,Deposit,Description
2024-01-15,50.00,,Grocery Store
2024-01-16,,1000.00,Paycheck
"""
        df = import_service.parse_csv(csv_data.encode())
        mapping = CSVColumnMapping(
            date="Date",
            amount="Withdrawal|Deposit",
            description="Description"
        )

        transactions = import_service.map_csv_to_transactions(df, mapping)

        assert len(transactions) == 2
        # First transaction: withdrawal
        assert transactions[0]['amount'] == 50.00
        assert transactions[0]['type'] == 'DEBIT'
        # Second transaction: deposit
        assert transactions[1]['amount'] == 1000.00
        assert transactions[1]['type'] == 'CREDIT'

    def test_ofx_checking_account_transactions(self):
        """OFX: Negative amounts are debits, positive are credits for checking accounts"""
        # Sample OFX for checking account
        ofx_data = """<?xml version="1.0" encoding="UTF-8"?>
<OFX>
  <SIGNONMSGSRSV1>
    <SONRS>
      <STATUS>
        <CODE>0</CODE>
        <SEVERITY>INFO</SEVERITY>
      </STATUS>
      <DTSERVER>20240115120000</DTSERVER>
      <LANGUAGE>ENG</LANGUAGE>
    </SONRS>
  </SIGNONMSGSRSV1>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <TRNUID>1</TRNUID>
      <STATUS>
        <CODE>0</CODE>
        <SEVERITY>INFO</SEVERITY>
      </STATUS>
      <STMTRS>
        <CURDEF>USD</CURDEF>
        <BANKACCTFROM>
          <BANKID>123456789</BANKID>
          <ACCTID>9876543210</ACCTID>
          <ACCTTYPE>CHECKING</ACCTTYPE>
        </BANKACCTFROM>
        <BANKTRANLIST>
          <DTSTART>20240101</DTSTART>
          <DTEND>20240115</DTEND>
          <STMTTRN>
            <TRNTYPE>DEBIT</TRNTYPE>
            <DTPOSTED>20240115</DTPOSTED>
            <TRNAMT>-50.00</TRNAMT>
            <FITID>TXN001</FITID>
            <NAME>Grocery Store</NAME>
            <MEMO>Purchase</MEMO>
          </STMTTRN>
          <STMTTRN>
            <TRNTYPE>CREDIT</TRNTYPE>
            <DTPOSTED>20240116</DTPOSTED>
            <TRNAMT>1000.00</TRNAMT>
            <FITID>TXN002</FITID>
            <NAME>Paycheck</NAME>
            <MEMO>Salary Deposit</MEMO>
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>"""

        result = OFXService.parse_ofx(ofx_data.encode())
        transactions = result['transactions']

        assert len(transactions) == 2
        # First transaction: debit (withdrawal)
        assert transactions[0]['amount'] == 50.00  # Stored as positive
        assert transactions[0]['type'] == 'DEBIT'
        assert transactions[0]['fitid'] == 'TXN001'
        # Second transaction: credit (deposit)
        assert transactions[1]['amount'] == 1000.00
        assert transactions[1]['type'] == 'CREDIT'
        assert transactions[1]['fitid'] == 'TXN002'

    def test_ofx_credit_card_transactions(self):
        """OFX: Credit card purchases are positive amounts but DEBIT type (money owed)"""
        # Sample OFX for credit card account
        # Note: Credit card transactions work differently
        # - Purchases (debits) increase the balance (positive amounts)
        # - Payments (credits) decrease the balance (negative amounts)
        ofx_data = """<?xml version="1.0" encoding="UTF-8"?>
<OFX>
  <SIGNONMSGSRSV1>
    <SONRS>
      <STATUS>
        <CODE>0</CODE>
        <SEVERITY>INFO</SEVERITY>
      </STATUS>
      <DTSERVER>20240115120000</DTSERVER>
      <LANGUAGE>ENG</LANGUAGE>
    </SONRS>
  </SIGNONMSGSRSV1>
  <CREDITCARDMSGSRSV1>
    <CCSTMTTRNRS>
      <TRNUID>1</TRNUID>
      <STATUS>
        <CODE>0</CODE>
        <SEVERITY>INFO</SEVERITY>
      </STATUS>
      <CCSTMTRS>
        <CURDEF>USD</CURDEF>
        <CCACCTFROM>
          <ACCTID>1234567890123456</ACCTID>
        </CCACCTFROM>
        <BANKTRANLIST>
          <DTSTART>20240101</DTSTART>
          <DTEND>20240115</DTEND>
          <STMTTRN>
            <TRNTYPE>DEBIT</TRNTYPE>
            <DTPOSTED>20240115</DTPOSTED>
            <TRNAMT>50.00</TRNAMT>
            <FITID>TXN003</FITID>
            <NAME>Restaurant</NAME>
            <MEMO>Dinner</MEMO>
          </STMTTRN>
          <STMTTRN>
            <TRNTYPE>CREDIT</TRNTYPE>
            <DTPOSTED>20240116</DTPOSTED>
            <TRNAMT>-100.00</TRNAMT>
            <FITID>TXN004</FITID>
            <NAME>Payment</NAME>
            <MEMO>CC Payment</MEMO>
          </STMTTRN>
        </BANKTRANLIST>
      </CCSTMTRS>
    </CCSTMTTRNRS>
  </CREDITCARDMSGSRSV1>
</OFX>"""

        result = OFXService.parse_ofx(ofx_data.encode())
        transactions = result['transactions']

        assert len(transactions) == 2
        # First transaction: purchase (debit) - positive amount in OFX
        assert transactions[0]['amount'] == 50.00
        assert transactions[0]['type'] == 'DEBIT'  # Still a debit (money owed)
        # Second transaction: payment (credit) - negative amount in OFX
        assert transactions[1]['amount'] == 100.00  # Stored as positive
        assert transactions[1]['type'] == 'CREDIT'  # Payment reduces balance

    def test_csv_parentheses_negative_amounts(self, db_session):
        """CSV: Amounts in parentheses (50.00) should be treated as negative (debits)"""
        import_service = ImportService(db_session)

        csv_data = """Date,Amount,Description
2024-01-15,(50.00),Grocery Store
2024-01-16,1000.00,Paycheck
"""
        df = import_service.parse_csv(csv_data.encode())
        mapping = CSVColumnMapping(
            date="Date",
            amount="Amount",
            description="Description"
        )

        transactions = import_service.map_csv_to_transactions(df, mapping)

        assert len(transactions) == 2
        # First transaction: parentheses mean negative (debit)
        assert transactions[0]['amount'] == 50.00
        assert transactions[0]['type'] == 'DEBIT'
        # Second transaction: positive (credit)
        assert transactions[1]['amount'] == 1000.00
        assert transactions[1]['type'] == 'CREDIT'

    def test_same_file_imported_twice_consistency(self, db_session):
        """Importing the same file twice should produce identical amounts and types"""
        import_service = ImportService(db_session)

        csv_data = """Date,Amount,Description
2024-01-15,-50.00,Grocery Store
2024-01-16,1000.00,Paycheck
2024-01-17,(25.00),Gas Station
"""

        # First import
        df1 = import_service.parse_csv(csv_data.encode())
        mapping = CSVColumnMapping(
            date="Date",
            amount="Amount",
            description="Description"
        )
        transactions1 = import_service.map_csv_to_transactions(df1, mapping)

        # Second import (same data)
        df2 = import_service.parse_csv(csv_data.encode())
        transactions2 = import_service.map_csv_to_transactions(df2, mapping)

        # Should be identical
        assert len(transactions1) == len(transactions2) == 3
        for i in range(3):
            assert transactions1[i]['amount'] == transactions2[i]['amount']
            assert transactions1[i]['type'] == transactions2[i]['type']
            assert transactions1[i]['date'] == transactions2[i]['date']
