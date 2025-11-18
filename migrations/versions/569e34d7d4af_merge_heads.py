"""merge heads

Revision ID: 569e34d7d4af
Revises: 52fcaa1675df, k0l1m2n3o4p5
Create Date: 2025-11-18 19:32:25.345819

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '569e34d7d4af'
down_revision: Union[str, None] = ('52fcaa1675df', 'k0l1m2n3o4p5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
