"""merge heads

Revision ID: 52fcaa1675df
Revises: h1i2j3k4l5m6, i7j8k9l0m1n2
Create Date: 2025-11-18 17:13:11.939440

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52fcaa1675df'
down_revision: Union[str, None] = ('h1i2j3k4l5m6', 'i7j8k9l0m1n2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
