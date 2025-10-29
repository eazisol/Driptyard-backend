"""add company_name and sin_number to users

Revision ID: c7d8e9f0a1b2
Revises: 409a5a6473f9
Create Date: 2025-10-29 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, None] = '409a5a6473f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add company_name and sin_number to users table
    op.add_column('users', sa.Column('company_name', sa.String(length=200), nullable=True))
    op.add_column('users', sa.Column('sin_number', sa.String(length=20), nullable=True))
    
    # Add company_name and sin_number to registration_data table
    op.add_column('registration_data', sa.Column('company_name', sa.String(length=200), nullable=True))
    op.add_column('registration_data', sa.Column('sin_number', sa.String(length=20), nullable=True))


def downgrade() -> None:
    # Remove company_name and sin_number from registration_data table
    op.drop_column('registration_data', 'sin_number')
    op.drop_column('registration_data', 'company_name')
    
    # Remove company_name and sin_number from users table
    op.drop_column('users', 'sin_number')
    op.drop_column('users', 'company_name')

