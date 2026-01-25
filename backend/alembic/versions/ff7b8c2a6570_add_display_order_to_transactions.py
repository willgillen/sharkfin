"""add display_order to transactions

Revision ID: ff7b8c2a6570
Revises: 816dd6a7d703
Create Date: 2026-01-25 19:31:18.065424

This migration adds a display_order column to transactions for controlling
the order of transactions within the same date. This is used for accurate
running balance calculations when multiple transactions occur on the same day.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff7b8c2a6570'
down_revision: Union[str, None] = '816dd6a7d703'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add display_order column for intra-day transaction ordering
    op.add_column('transactions', sa.Column('display_order', sa.Integer(), nullable=True))

    # Drop old index and create new one that includes display_order
    # This optimizes running balance queries which order by date, display_order, id
    op.drop_index('idx_transactions_account_date_id', table_name='transactions')
    op.create_index(
        'idx_transactions_account_date_order',
        'transactions',
        ['account_id', 'date', 'display_order', 'id'],
        unique=False
    )


def downgrade() -> None:
    # Restore original index
    op.drop_index('idx_transactions_account_date_order', table_name='transactions')
    op.create_index('idx_transactions_account_date_id', 'transactions', ['account_id', 'date', 'id'], unique=False)
    op.drop_column('transactions', 'display_order')
