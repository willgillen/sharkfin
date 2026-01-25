"""add index for transaction running balance performance

Revision ID: 816dd6a7d703
Revises: 2439bb1b1c17
Create Date: 2026-01-25 15:39:02.535284

This migration adds a composite index on (account_id, date, id) to optimize
the running balance calculation query using window functions.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '816dd6a7d703'
down_revision: Union[str, None] = '2439bb1b1c17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create composite index for running balance queries
    # This index optimizes:
    # 1. Filtering transactions by account_id
    # 2. Ordering by date for window function
    # 3. Using id as tiebreaker for consistent ordering
    op.create_index(
        'idx_transactions_account_date_id',
        'transactions',
        ['account_id', 'date', 'id'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_transactions_account_date_id', table_name='transactions')
