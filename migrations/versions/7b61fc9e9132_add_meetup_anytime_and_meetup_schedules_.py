"""add meetup_anytime and meetup_schedules to products

Revision ID: 7b61fc9e9132
Revises: 7161b46b29b9
Create Date: 2026-01-07 20:11:02.157659

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b61fc9e9132'
down_revision: Union[str, None] = '7161b46b29b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('products', sa.Column('meetup_anytime', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('products', sa.Column('meetup_schedules', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('products', 'meetup_schedules')
    op.drop_column('products', 'meetup_anytime')
