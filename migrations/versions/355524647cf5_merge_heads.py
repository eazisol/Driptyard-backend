"""merge heads

Revision ID: 355524647cf5
Revises: 0c66d313034d, a1b2c3d4e5f6
Create Date: 2025-12-04 12:59:35.837030

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '355524647cf5'
down_revision: Union[str, None] = ('0c66d313034d', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
