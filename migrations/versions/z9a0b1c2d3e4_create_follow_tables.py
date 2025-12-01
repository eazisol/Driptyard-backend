"""create_follow_tables

Revision ID: z9a0b1c2d3e4
Revises: y8z9a0b1c2d3
Create Date: 2025-01-28 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'z9a0b1c2d3e4'
down_revision: Union[str, None] = 'y8z9a0b1c2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create seller_follows table
    op.create_table('seller_follows',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True, comment='Unique identifier'),
        sa.Column('follower_id', sa.Integer(), nullable=False),
        sa.Column('followed_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.ForeignKeyConstraint(['follower_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['followed_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('follower_id', 'followed_user_id', name='uq_follower_followed_user'),
        sa.CheckConstraint('follower_id != followed_user_id', name='ck_no_self_follow')
    )
    op.create_index(op.f('ix_seller_follows_id'), 'seller_follows', ['id'], unique=False)
    op.create_index(op.f('ix_seller_follows_follower_id'), 'seller_follows', ['follower_id'], unique=False)
    op.create_index(op.f('ix_seller_follows_followed_user_id'), 'seller_follows', ['followed_user_id'], unique=False)
    op.create_index('idx_follower_id', 'seller_follows', ['follower_id'], unique=False)
    op.create_index('idx_followed_user_id', 'seller_follows', ['followed_user_id'], unique=False)
    
    # Create product_follows table
    op.create_table('product_follows',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True, comment='Unique identifier'),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'product_id', name='uq_user_product_follow')
    )
    op.create_index(op.f('ix_product_follows_id'), 'product_follows', ['id'], unique=False)
    op.create_index(op.f('ix_product_follows_user_id'), 'product_follows', ['user_id'], unique=False)
    op.create_index(op.f('ix_product_follows_product_id'), 'product_follows', ['product_id'], unique=False)
    op.create_index('idx_user_id', 'product_follows', ['user_id'], unique=False)
    op.create_index('idx_product_id', 'product_follows', ['product_id'], unique=False)


def downgrade() -> None:
    # Drop product_follows table
    op.drop_index('idx_product_id', table_name='product_follows')
    op.drop_index('idx_user_id', table_name='product_follows')
    op.drop_index(op.f('ix_product_follows_product_id'), table_name='product_follows')
    op.drop_index(op.f('ix_product_follows_user_id'), table_name='product_follows')
    op.drop_index(op.f('ix_product_follows_id'), table_name='product_follows')
    op.drop_table('product_follows')
    
    # Drop seller_follows table
    op.drop_index('idx_followed_user_id', table_name='seller_follows')
    op.drop_index('idx_follower_id', table_name='seller_follows')
    op.drop_index(op.f('ix_seller_follows_followed_user_id'), table_name='seller_follows')
    op.drop_index(op.f('ix_seller_follows_follower_id'), table_name='seller_follows')
    op.drop_index(op.f('ix_seller_follows_id'), table_name='seller_follows')
    op.drop_table('seller_follows')

