from typing import List, Dict, Any
from ofxparse import OfxParser
from io import BytesIO
from datetime import datetime


class OFXService:
    @staticmethod
    def parse_ofx(file_bytes: bytes) -> Dict[str, Any]:
        """Parse OFX/QFX file and extract account and transaction information"""
        try:
            ofx = OfxParser.parse(BytesIO(file_bytes))
        except Exception as e:
            raise ValueError(f"Failed to parse OFX file: {str(e)}")

        account = ofx.account
        transactions = []

        # Extract transactions
        if hasattr(account, 'statement') and account.statement:
            for txn in account.statement.transactions:
                try:
                    # Determine transaction type based on amount sign
                    amount = float(txn.amount)
                    trans_type = 'DEBIT' if amount < 0 else 'CREDIT'

                    transaction = {
                        'date': txn.date.strftime('%Y-%m-%d') if txn.date else None,
                        'amount': abs(amount),
                        'payee': txn.payee[:200] if txn.payee else None,
                        'description': txn.memo[:500] if txn.memo else None,
                        'type': trans_type,
                        'fitid': txn.id if hasattr(txn, 'id') else None,  # Financial Institution Transaction ID
                    }

                    # Only add if we have essential fields
                    if transaction['date'] and transaction['amount'] is not None:
                        transactions.append(transaction)

                except Exception as e:
                    # Skip transactions that fail to parse
                    print(f"Skipping transaction due to error: {e}")
                    continue

        # Extract account information
        account_info = {
            'account_name': account.routing_number or 'Unknown Account',
            'account_number': account.account_id if hasattr(account, 'account_id') else None,
            'account_type': account.account_type if hasattr(account, 'account_type') else 'UNKNOWN',
            'bank_name': None,
            'start_date': None,
            'end_date': None,
            'transactions': transactions
        }

        # Extract bank information if available
        if hasattr(ofx.account, 'institution') and ofx.account.institution:
            if hasattr(ofx.account.institution, 'organization'):
                account_info['bank_name'] = ofx.account.institution.organization

        # Extract statement date range if available
        if hasattr(account, 'statement') and account.statement:
            if hasattr(account.statement, 'start_date') and account.statement.start_date:
                account_info['start_date'] = account.statement.start_date.strftime('%Y-%m-%d')
            if hasattr(account.statement, 'end_date') and account.statement.end_date:
                account_info['end_date'] = account.statement.end_date.strftime('%Y-%m-%d')

        return account_info

    @staticmethod
    def map_ofx_to_transactions(parsed_ofx: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert parsed OFX transactions to standard transaction format"""
        return parsed_ofx['transactions']
