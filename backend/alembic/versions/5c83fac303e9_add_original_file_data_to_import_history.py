"""add_original_file_data_to_import_history

Revision ID: 5c83fac303e9
Revises: ca1d4344fd9d
Create Date: 2026-01-17 20:24:22.315476

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c83fac303e9'
down_revision: Union[str, None] = 'ca1d4344fd9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add original file storage columns to import_history
    op.add_column('import_history', sa.Column('original_file_data', sa.LargeBinary, nullable=True))
    op.add_column('import_history', sa.Column('original_file_name', sa.String(255), nullable=True))
    op.add_column('import_history', sa.Column('original_file_size', sa.Integer, nullable=True))
    op.add_column('import_history', sa.Column('is_compressed', sa.Boolean, default=True, nullable=True))


def downgrade() -> None:
    # Remove original file storage columns
    op.drop_column('import_history', 'is_compressed')
    op.drop_column('import_history', 'original_file_size')
    op.drop_column('import_history', 'original_file_name')
    op.drop_column('import_history', 'original_file_data')
