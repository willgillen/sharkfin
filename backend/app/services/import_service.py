from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import chardet
from io import BytesIO, StringIO
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.import_history import ImportHistory, ImportedTransaction
from app.models.transaction import Transaction
from app.schemas.imports import CSVColumnMapping
from app.services.duplicate_detection_service import DuplicateDetectionService


class ImportService:
    def __init__(self, db: Session):
        self.db = db
        self.duplicate_detector = DuplicateDetectionService(db)

    def detect_csv_encoding(self, file_bytes: bytes) -> str:
        """Detect file encoding using chardet"""
        result = chardet.detect(file_bytes)
        return result['encoding'] or 'utf-8'

    def detect_csv_format(self, df: pd.DataFrame) -> Optional[str]:
        """Auto-detect common CSV formats based on column names"""
        columns_lower = [col.lower().strip() for col in df.columns]

        # Mint format detection
        mint_indicators = {'date', 'amount', 'transaction type', 'category', 'description'}
        if len(mint_indicators & set(columns_lower)) >= 3:
            return "mint"

        # Chase format detection
        chase_indicators = {'posting date', 'amount'}
        if chase_indicators.issubset(set(columns_lower)):
            return "chase"

        # Bank of America format detection
        bofa_indicators = {'date', 'description', 'amount'}
        if bofa_indicators.issubset(set(columns_lower)):
            return "bofa"

        # Wells Fargo format detection
        wells_indicators = {'date', 'amount', 'description'}
        if wells_indicators.issubset(set(columns_lower)):
            return "wellsfargo"

        return "generic"

    def get_suggested_mapping(self, df: pd.DataFrame, format_type: str) -> CSVColumnMapping:
        """Suggest column mapping based on detected format"""
        mappings = {
            "mint": {
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
                "payee": "Description",
                "category": "Category",
                "notes": "Notes",
            },
            "chase": {
                "date": "Posting Date",
                "amount": "Amount",
                "description": "Description",
                "payee": "Description",
            },
            "bofa": {
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
            },
            "wellsfargo": {
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
            },
        }

        if format_type == "generic":
            mapping = self._guess_columns(df)
        else:
            mapping = mappings.get(format_type, self._guess_columns(df))

        # Ensure required fields exist
        if 'date' not in mapping or 'amount' not in mapping:
            mapping = self._guess_columns(df)

        return CSVColumnMapping(**mapping)

    def _guess_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Guess column names for generic CSV by analyzing column names and data"""
        columns = df.columns.tolist()
        mapping = {}

        # Look for date column
        date_keywords = ['date', 'transaction date', 'posting date', 'dt', 'trans date']
        for col in columns:
            if any(kw in col.lower() for kw in date_keywords):
                mapping['date'] = col
                break

        # Look for amount column - check for split debit/credit first
        debit_col = None
        credit_col = None
        for col in columns:
            col_lower = col.lower()
            if ('withdrawal' in col_lower or 'debit' in col_lower) and 'card' not in col_lower:
                debit_col = col
            elif ('deposit' in col_lower or 'credit' in col_lower) and 'card' not in col_lower:
                credit_col = col

        # If we have separate debit/credit columns, combine them with pipe separator
        if debit_col and credit_col:
            mapping['amount'] = f"{debit_col}|{credit_col}"
        else:
            # Look for single amount column
            amount_keywords = ['amount', 'value', 'total', 'sum']
            for col in columns:
                if any(kw in col.lower() for kw in amount_keywords):
                    mapping['amount'] = col
                    break

        # Look for description
        desc_keywords = ['description', 'memo', 'details', 'name', 'transaction']
        for col in columns:
            if any(kw in col.lower() for kw in desc_keywords):
                mapping['description'] = col
                break

        # Look for payee
        payee_keywords = ['payee', 'merchant', 'vendor']
        for col in columns:
            if any(kw in col.lower() for kw in payee_keywords):
                mapping['payee'] = col
                break

        # Look for category
        category_keywords = ['category']
        for col in columns:
            col_lower = col.lower()
            if any(kw in col_lower for kw in category_keywords):
                mapping['category'] = col
                break

        return mapping

    def parse_csv(self, file_bytes: bytes) -> pd.DataFrame:
        """Parse CSV with smart encoding detection"""
        encoding = self.detect_csv_encoding(file_bytes)

        try:
            # Try with detected encoding
            df = pd.read_csv(BytesIO(file_bytes), encoding=encoding)
        except Exception:
            # Fallback to UTF-8 with error handling
            try:
                df = pd.read_csv(BytesIO(file_bytes), encoding='utf-8', encoding_errors='ignore')
            except Exception:
                # Last resort: Latin-1 (accepts all byte sequences)
                df = pd.read_csv(BytesIO(file_bytes), encoding='latin-1')

        # Clean column names
        df.columns = df.columns.str.strip()

        return df

    def map_csv_to_transactions(
        self,
        df: pd.DataFrame,
        column_mapping: CSVColumnMapping,
        skip_rows: List[int] = None
    ) -> List[Dict[str, Any]]:
        """Map CSV rows to transaction dictionaries using column mapping"""
        transactions = []
        skip_rows = skip_rows or []

        for idx, row in df.iterrows():
            if idx in skip_rows:
                continue

            # Extract fields based on mapping
            try:
                date_str = str(row[column_mapping.date]).strip()

                # Handle amount - check if it's split debit/credit columns
                if '|' in column_mapping.amount:
                    # Split column format: "Withdrawal|Deposit"
                    debit_col, credit_col = column_mapping.amount.split('|')
                    debit_val = str(row[debit_col]).strip() if debit_col in row.index else ''
                    credit_val = str(row[credit_col]).strip() if credit_col in row.index else ''

                    # Parse both values
                    debit_amount = self._parse_amount(debit_val) if debit_val and debit_val.lower() not in ['nan', 'none', ''] else 0
                    credit_amount = self._parse_amount(credit_val) if credit_val and credit_val.lower() not in ['nan', 'none', ''] else 0

                    # Determine net amount and type
                    if debit_amount and debit_amount > 0:
                        amount = -abs(debit_amount)  # Withdrawal is negative
                    elif credit_amount and credit_amount > 0:
                        amount = abs(credit_amount)  # Deposit is positive
                    else:
                        continue  # Skip if both are empty/zero
                else:
                    # Single amount column
                    amount_str = str(row[column_mapping.amount]).strip()
                    amount = self._parse_amount(amount_str)
                    if amount is None:
                        continue  # Skip invalid amounts

                # Parse date
                trans_date = self._parse_date(date_str)
                if not trans_date:
                    continue  # Skip invalid dates

                transaction = {
                    'date': trans_date.strftime('%Y-%m-%d'),
                    'amount': abs(amount),  # Store as positive
                    'type': 'DEBIT' if amount < 0 else 'CREDIT',
                    'row': idx,
                }

                # Optional fields
                if column_mapping.description and column_mapping.description in row:
                    transaction['description'] = str(row[column_mapping.description]).strip()[:500]

                if column_mapping.payee and column_mapping.payee in row:
                    transaction['payee'] = str(row[column_mapping.payee]).strip()[:200]

                if column_mapping.notes and column_mapping.notes in row:
                    transaction['notes'] = str(row[column_mapping.notes]).strip()[:1000]

                transactions.append(transaction)

            except Exception as e:
                # Skip rows with errors
                print(f"Error parsing row {idx}: {e}")
                continue

        return transactions

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string with multiple format attempts"""
        # Common date formats
        formats = [
            '%Y-%m-%d',      # 2024-01-15
            '%m/%d/%Y',      # 01/15/2024
            '%m/%d/%y',      # 01/15/24
            '%d/%m/%Y',      # 15/01/2024
            '%Y/%m/%d',      # 2024/01/15
            '%m-%d-%Y',      # 01-15-2024
            '%d-%m-%Y',      # 15-01-2024
            '%b %d, %Y',     # Jan 15, 2024
            '%B %d, %Y',     # January 15, 2024
            '%d %b %Y',      # 15 Jan 2024
            '%Y%m%d',        # 20240115
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string, handling various formats"""
        try:
            # Remove common currency symbols and whitespace
            cleaned = amount_str.replace('$', '').replace(',', '').replace(' ', '').strip()

            # Handle parentheses for negative amounts
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]

            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    def create_import_record(
        self,
        user_id: int,
        account_id: int,
        filename: str,
        import_type: str,
        total_rows: int,
        file_size: int = 0
    ) -> ImportHistory:
        """Create import history record"""
        import_record = ImportHistory(
            user_id=user_id,
            account_id=account_id,
            filename=filename,
            import_type=import_type,
            total_rows=total_rows,
            file_size=file_size
        )
        self.db.add(import_record)
        self.db.commit()
        self.db.refresh(import_record)
        return import_record

    def complete_import_record(
        self,
        import_id: int,
        imported_count: int,
        duplicate_count: int,
        error_count: int,
        status: str = "completed"
    ):
        """Update import record with final counts"""
        import_record = self.db.query(ImportHistory).filter(ImportHistory.id == import_id).first()
        if import_record:
            import_record.imported_count = imported_count
            import_record.duplicate_count = duplicate_count
            import_record.error_count = error_count
            import_record.status = status
            import_record.completed_at = datetime.utcnow()
            self.db.commit()
