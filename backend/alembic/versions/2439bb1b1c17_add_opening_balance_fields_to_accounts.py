"""add opening_balance fields to accounts

Revision ID: 2439bb1b1c17
Revises: 3c1957ec05e2
Create Date: 2026-01-25 15:12:10.595004

This migration adds opening_balance and opening_balance_date fields to the accounts table
to support calculated balances from transactions. The current_balance field is kept
temporarily for rollback safety but will be removed in a future migration after verification.

Data Migration Strategy:
1. Add new columns (opening_balance, opening_balance_date)
2. Copy current_balance → opening_balance
3. Set opening_balance_date to earliest transaction date (or created_at if no transactions)
"""
from typing import Sequence, Union
from datetime import date

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column, select, func


# revision identifiers, used by Alembic.
revision: str = '2439bb1b1c17'
down_revision: Union[str, None] = '3c1957ec05e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns
    op.add_column('accounts', sa.Column('opening_balance', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'))
    op.add_column('accounts', sa.Column('opening_balance_date', sa.Date(), nullable=True))

    # Data migration: Copy current_balance to opening_balance
    # and set opening_balance_date to earliest transaction date
    connection = op.get_bind()

    # Define table references for the data migration
    accounts = table('accounts',
        column('id', sa.Integer),
        column('current_balance', sa.Numeric),
        column('opening_balance', sa.Numeric),
        column('opening_balance_date', sa.Date),
        column('created_at', sa.DateTime)
    )

    transactions = table('transactions',
        column('account_id', sa.Integer),
        column('date', sa.Date)
    )

    # Step 1: Copy current_balance to opening_balance for all accounts
    connection.execute(
        accounts.update().values(opening_balance=accounts.c.current_balance)
    )

    # Step 2: Set opening_balance_date to earliest transaction date for each account
    # This is a subquery that finds the MIN(date) for each account
    earliest_tx_subquery = (
        select(
            transactions.c.account_id,
            func.min(transactions.c.date).label('earliest_date')
        )
        .group_by(transactions.c.account_id)
    ).alias('earliest_tx')

    # Update accounts with their earliest transaction date
    # Note: This leaves opening_balance_date as NULL for accounts with no transactions,
    # which is correct (NULL means "from the beginning of time")
    connection.execute(
        accounts.update()
        .values(opening_balance_date=earliest_tx_subquery.c.earliest_date)
        .where(accounts.c.id == earliest_tx_subquery.c.account_id)
    )


def downgrade() -> None:
    # Remove the new columns (current_balance is preserved)
    op.drop_column('accounts', 'opening_balance_date')
    op.drop_column('accounts', 'opening_balance')
