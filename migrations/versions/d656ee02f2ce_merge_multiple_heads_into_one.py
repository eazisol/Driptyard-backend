"""Merge multiple heads into one

Revision ID: d656ee02f2ce
Revises: 660ff205b055, ab12cd34ef56
Create Date: 2025-11-10 18:38:20.839346

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd656ee02f2ce'
down_revision: Union[str, None] = ('660ff205b055', 'ab12cd34ef56')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
