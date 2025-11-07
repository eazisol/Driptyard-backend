"""merge migration heads

Revision ID: 660ff205b055
Revises: c7d8e9f0a1b2, e5f6a7b8c9d0
Create Date: 2025-11-07 18:37:57.111112

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '660ff205b055'
down_revision: Union[str, None] = ('c7d8e9f0a1b2', 'e5f6a7b8c9d0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
