"""add_product_verification_fields

Revision ID: e5f6a7b8c9d0
Revises: 409a5a6473f9
Create Date: 2025-11-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = '409a5a6473f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add verification related columns
    op.add_column('products', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('products', sa.Column('verification_code', sa.String(length=6), nullable=True))
    op.add_column('products', sa.Column('verification_expires_at', sa.DateTime(), nullable=True))
    op.add_column('products', sa.Column('verification_attempts', sa.Integer(), nullable=False, server_default=sa.text('0')))

    # Populate existing rows as verified to preserve current behaviour
    op.execute('UPDATE products SET is_verified = is_active')

    # Create index for quick lookups
    op.create_index(op.f('ix_products_is_verified'), 'products', ['is_verified'], unique=False)

    # Drop server defaults to allow SQLAlchemy to manage defaults
    op.alter_column('products', 'is_verified', server_default=None)
    op.alter_column('products', 'verification_attempts', server_default=None)


def downgrade() -> None:
    # Drop index and newly added columns
    op.drop_index(op.f('ix_products_is_verified'), table_name='products')
    op.drop_column('products', 'verification_attempts')
    op.drop_column('products', 'verification_expires_at')
    op.drop_column('products', 'verification_code')
    op.drop_column('products', 'is_verified')

