"""create_report_tables

Revision ID: r7s8t9u0v1w2
Revises: q6r7s8t9u0v1
Create Date: 2025-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'r7s8t9u0v1w2'
down_revision: Union[str, None] = 'q6r7s8t9u0v1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create report_statuses table
    op.create_table('report_statuses',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True, comment='Unique identifier'),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_statuses_id'), 'report_statuses', ['id'], unique=False)
    op.create_index(op.f('ix_report_statuses_status'), 'report_statuses', ['status'], unique=True)
    
    # Create product_reports table
    op.create_table('product_reports',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True, comment='Unique identifier'),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['status_id'], ['report_statuses.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'product_id', name='uq_user_product_report')
    )
    op.create_index(op.f('ix_product_reports_id'), 'product_reports', ['id'], unique=False)
    op.create_index(op.f('ix_product_reports_product_id'), 'product_reports', ['product_id'], unique=False)
    op.create_index(op.f('ix_product_reports_status_id'), 'product_reports', ['status_id'], unique=False)
    op.create_index(op.f('ix_product_reports_user_email'), 'product_reports', ['user_email'], unique=False)
    op.create_index(op.f('ix_product_reports_user_id'), 'product_reports', ['user_id'], unique=False)
    
    # Insert initial statuses
    op.execute("""
        INSERT INTO report_statuses (status, created_at, updated_at) VALUES
        ('pending', now(), now()),
        ('active', now(), now()),
        ('approved', now(), now()),
        ('rejected', now(), now()),
        ('processing', now(), now()),
        ('inactive', now(), now())
    """)


def downgrade() -> None:
    op.drop_index(op.f('ix_product_reports_user_id'), table_name='product_reports')
    op.drop_index(op.f('ix_product_reports_user_email'), table_name='product_reports')
    op.drop_index(op.f('ix_product_reports_status_id'), table_name='product_reports')
    op.drop_index(op.f('ix_product_reports_product_id'), table_name='product_reports')
    op.drop_index(op.f('ix_product_reports_id'), table_name='product_reports')
    op.drop_table('product_reports')
    op.drop_index(op.f('ix_report_statuses_status'), table_name='report_statuses')
    op.drop_index(op.f('ix_report_statuses_id'), table_name='report_statuses')
    op.drop_table('report_statuses')

