"""add import tables

Revision ID: 879874f4adf2
Revises: 9e366ff8a404
Create Date: 2026-01-13 00:24:47.015370

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '879874f4adf2'
down_revision: Union[str, None] = '9e366ff8a404'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create import_history table
    op.create_table(
        'import_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=True),
        sa.Column('import_type', sa.String(length=20), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('total_rows', sa.Integer(), nullable=False),
        sa.Column('imported_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('duplicate_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('error_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('can_rollback', sa.Boolean(), nullable=True, server_default='true'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_import_history_id'), 'import_history', ['id'], unique=False)
    op.create_index(op.f('ix_import_history_started_at'), 'import_history', ['started_at'], unique=False)
    op.create_index(op.f('ix_import_history_user_id'), 'import_history', ['user_id'], unique=False)

    # Create imported_transactions table
    op.create_table(
        'imported_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('import_id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=True),
        sa.Column('row_number', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['import_id'], ['import_history.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_imported_transactions_id'), 'imported_transactions', ['id'], unique=False)
    op.create_index(op.f('ix_imported_transactions_import_id'), 'imported_transactions', ['import_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_imported_transactions_import_id'), table_name='imported_transactions')
    op.drop_index(op.f('ix_imported_transactions_id'), table_name='imported_transactions')
    op.drop_table('imported_transactions')

    op.drop_index(op.f('ix_import_history_user_id'), table_name='import_history')
    op.drop_index(op.f('ix_import_history_started_at'), table_name='import_history')
    op.drop_index(op.f('ix_import_history_id'), table_name='import_history')
    op.drop_table('import_history')
