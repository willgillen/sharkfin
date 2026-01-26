"""drop deprecated current_balance column from accounts

Revision ID: 3b523177fdb0
Revises: ff7b8c2a6570
Create Date: 2026-01-25 20:28:46.251277

The current_balance column was deprecated in favor of calculated balances
based on opening_balance + sum(transactions). The balance is now calculated
on-the-fly using Account.calculate_balance() method, ensuring accuracy and
eliminating stale data issues.

Since this product is still in local development with no production instances,
it's safe to drop this column without a deprecation period.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b523177fdb0'
down_revision: Union[str, None] = 'ff7b8c2a6570'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the deprecated current_balance column
    # Balance is now calculated from: opening_balance + sum(transactions)
    op.drop_column('accounts', 'current_balance')


def downgrade() -> None:
    # Re-add the current_balance column for rollback
    # Note: Data will be lost - new balances would need to be calculated
    op.add_column('accounts', sa.Column(
        'current_balance',
        sa.Numeric(precision=15, scale=2),
        nullable=False,
        server_default='0'
    ))
