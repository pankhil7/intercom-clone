"""fix column names to match SQLAlchemy models

Revision ID: 002
Revises: 001
Create Date: 2026-08-09
"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # --- conversations ---
    # assigned_to_id -> assigned_to
    op.alter_column('conversations', 'assigned_to_id', new_column_name='assigned_to')
    # sla_breached -> sla_breach
    op.alter_column('conversations', 'sla_breached', new_column_name='sla_breach')
    # metadata -> meta
    op.alter_column('conversations', 'metadata', new_column_name='meta')
    # Drop columns not in model
    op.drop_column('conversations', 'last_activity_at')
    op.drop_column('conversations', 'email_thread_id')
    op.drop_column('conversations', 'last_message_id')
    op.drop_column('conversations', 'sla_first_response_due')
    op.drop_column('conversations', 'sla_resolution_due')
    # Add columns in model but missing from original migration
    op.add_column('conversations', sa.Column('summary', sa.Text(), nullable=True))
    op.add_column('conversations', sa.Column('summary_cached_at', sa.DateTime(), nullable=True))

    # --- users ---
    # invited_by_id -> invited_by
    op.alter_column('users', 'invited_by_id', new_column_name='invited_by')


def downgrade():
    op.alter_column('conversations', 'assigned_to', new_column_name='assigned_to_id')
    op.alter_column('conversations', 'sla_breach', new_column_name='sla_breached')
    op.alter_column('conversations', 'meta', new_column_name='metadata')
    op.alter_column('users', 'invited_by', new_column_name='invited_by_id')
