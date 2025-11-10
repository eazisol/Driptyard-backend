"""add_extended_product_fields

Revision ID: ab12cd34ef56
Revises: e5f6a7b8c9d0
Create Date: 2025-11-10 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab12cd34ef56'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extended product metadata
    op.add_column('products', sa.Column('gender', sa.String(length=20), nullable=True))
    op.add_column('products', sa.Column('product_type', sa.String(length=100), nullable=True))
    op.add_column('products', sa.Column('sub_category', sa.String(length=100), nullable=True))
    op.add_column('products', sa.Column('designer', sa.String(length=100), nullable=True))
    op.add_column('products', sa.Column('size', sa.String(length=50), nullable=True))
    op.add_column('products', sa.Column('colors', sa.JSON(), nullable=True))
    op.add_column('products', sa.Column('product_style', sa.String(length=50), nullable=True))
    op.add_column('products', sa.Column('measurement_chest', sa.String(length=50), nullable=True))
    op.add_column('products', sa.Column('measurement_sleeve_length', sa.String(length=50), nullable=True))
    op.add_column('products', sa.Column('measurement_length', sa.String(length=50), nullable=True))
    op.add_column('products', sa.Column('measurement_hem', sa.String(length=50), nullable=True))
    op.add_column('products', sa.Column('measurement_shoulders', sa.String(length=50), nullable=True))

    # Purchase and fulfilment configuration
    op.add_column('products', sa.Column('purchase_button_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    op.add_column('products', sa.Column('delivery_method', sa.String(length=20), nullable=True))
    op.add_column('products', sa.Column('delivery_time', sa.String(length=20), nullable=True))
    op.add_column('products', sa.Column('delivery_fee', sa.Numeric(10, 2), nullable=True))
    op.add_column('products', sa.Column('delivery_fee_type', sa.String(length=20), nullable=True))
    op.add_column('products', sa.Column('tracking_provided', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('products', sa.Column('shipping_address', sa.String(length=255), nullable=True))
    op.add_column('products', sa.Column('meetup_locations', sa.JSON(), nullable=True))

    # Drop server defaults once existing records are populated
    op.alter_column('products', 'purchase_button_enabled', server_default=None)
    op.alter_column('products', 'tracking_provided', server_default=None)


def downgrade() -> None:
    op.drop_column('products', 'meetup_locations')
    op.drop_column('products', 'shipping_address')
    op.drop_column('products', 'tracking_provided')
    op.drop_column('products', 'delivery_fee_type')
    op.drop_column('products', 'delivery_fee')
    op.drop_column('products', 'delivery_time')
    op.drop_column('products', 'delivery_method')
    op.drop_column('products', 'purchase_button_enabled')
    op.drop_column('products', 'measurement_shoulders')
    op.drop_column('products', 'measurement_hem')
    op.drop_column('products', 'measurement_length')
    op.drop_column('products', 'measurement_sleeve_length')
    op.drop_column('products', 'measurement_chest')
    op.drop_column('products', 'product_style')
    op.drop_column('products', 'colors')
    op.drop_column('products', 'size')
    op.drop_column('products', 'designer')
    op.drop_column('products', 'sub_category')
    op.drop_column('products', 'product_type')
    op.drop_column('products', 'gender')

