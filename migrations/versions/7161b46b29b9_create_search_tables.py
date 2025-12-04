"""create_search_tables

Revision ID: 7161b46b29b9
Revises: 355524647cf5
Create Date: 2025-12-04 15:44:55.385500

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7161b46b29b9'
down_revision: Union[str, None] = '355524647cf5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_recent_searches table
    op.create_table('user_recent_searches',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True, comment='Unique identifier'),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('query', sa.String(length=255), nullable=False),
        sa.Column('searched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'query', name='uq_user_recent_search_user_query')
    )
    op.create_index(op.f('ix_user_recent_searches_id'), 'user_recent_searches', ['id'], unique=False)
    op.create_index('idx_user_recent_searches_user_id', 'user_recent_searches', ['user_id'], unique=False)
    op.create_index('idx_user_recent_searches_searched_at', 'user_recent_searches', ['searched_at'], unique=False)
    
    # Create search_analytics table
    op.create_table('search_analytics',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True, comment='Unique identifier'),
        sa.Column('query', sa.String(length=255), nullable=False),
        sa.Column('searched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('result_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_search_analytics_id'), 'search_analytics', ['id'], unique=False)
    op.create_index('idx_search_analytics_query', 'search_analytics', ['query'], unique=False)
    op.create_index('idx_search_analytics_searched_at', 'search_analytics', ['searched_at'], unique=False)
    op.create_index('idx_search_analytics_user_id', 'search_analytics', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop search_analytics table
    op.drop_index('idx_search_analytics_user_id', table_name='search_analytics')
    op.drop_index('idx_search_analytics_searched_at', table_name='search_analytics')
    op.drop_index('idx_search_analytics_query', table_name='search_analytics')
    op.drop_index(op.f('ix_search_analytics_id'), table_name='search_analytics')
    op.drop_table('search_analytics')
    
    # Drop user_recent_searches table
    op.drop_index('idx_user_recent_searches_searched_at', table_name='user_recent_searches')
    op.drop_index('idx_user_recent_searches_user_id', table_name='user_recent_searches')
    op.drop_index(op.f('ix_user_recent_searches_id'), table_name='user_recent_searches')
    op.drop_table('user_recent_searches')
