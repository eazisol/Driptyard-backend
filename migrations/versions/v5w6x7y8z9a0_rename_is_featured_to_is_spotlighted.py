"""rename is_featured to is_spotlighted

Revision ID: v5w6x7y8z9a0
Revises: u9v0w1x2y3z4
Create Date: 2025-11-24 12:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'v5w6x7y8z9a0'
down_revision: Union[str, None] = 'u9v0w1x2y3z4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename column from is_featured to is_spotlighted
    op.alter_column('products', 'is_featured', new_column_name='is_spotlighted')


def downgrade() -> None:
    # Rename column back from is_spotlighted to is_featured
    op.alter_column('products', 'is_spotlighted', new_column_name='is_featured')

