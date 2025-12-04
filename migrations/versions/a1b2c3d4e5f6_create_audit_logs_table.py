"""create_audit_logs_table

Revision ID: a1b2c3d4e5f6
Revises: z9a0b1c2d3e4
Create Date: 2025-01-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'z9a0b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True, comment='Unique identifier'),
        sa.Column('performed_by_id', sa.Integer(), nullable=False),
        sa.Column('performed_by_username', sa.String(length=100), nullable=False),
        sa.Column('is_admin', sa.String(length=20), nullable=False, server_default='admin'),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.String(length=100), nullable=False),
        sa.Column('target_identifier', sa.String(length=255), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.ForeignKeyConstraint(['performed_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_performed_by_id'), 'audit_logs', ['performed_by_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_action_type'), 'audit_logs', ['action_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_target_type'), 'audit_logs', ['target_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_target_id'), 'audit_logs', ['target_id'], unique=False)
    op.create_index('idx_audit_log_performed_by', 'audit_logs', ['performed_by_id'], unique=False)
    op.create_index('idx_audit_log_action', 'audit_logs', ['action'], unique=False)
    op.create_index('idx_audit_log_action_type', 'audit_logs', ['action_type'], unique=False)
    op.create_index('idx_audit_log_target', 'audit_logs', ['target_type', 'target_id'], unique=False)
    op.create_index('idx_audit_log_created_at', 'audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop audit_logs table
    op.drop_index('idx_audit_log_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_log_target', table_name='audit_logs')
    op.drop_index('idx_audit_log_action_type', table_name='audit_logs')
    op.drop_index('idx_audit_log_action', table_name='audit_logs')
    op.drop_index('idx_audit_log_performed_by', table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_target_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_target_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_performed_by_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_table('audit_logs')

