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


def _col_exists(table, column):
    """Return True if the column exists in the table."""
    result = op.get_bind().execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name=:t AND column_name=:c"
        ),
        {"t": table, "c": column},
    ).fetchone()
    return result is not None


def upgrade():
    # --- conversations ---
    if _col_exists('conversations', 'assigned_to_id'):
        op.alter_column('conversations', 'assigned_to_id', new_column_name='assigned_to')

    if _col_exists('conversations', 'sla_breached'):
        op.alter_column('conversations', 'sla_breached', new_column_name='sla_breach')

    if _col_exists('conversations', 'metadata'):
        op.alter_column('conversations', 'metadata', new_column_name='meta')

    for col in ('last_activity_at', 'email_thread_id', 'last_message_id',
                'sla_first_response_due', 'sla_resolution_due'):
        if _col_exists('conversations', col):
            op.drop_column('conversations', col)

    if not _col_exists('conversations', 'summary'):
        op.add_column('conversations', sa.Column('summary', sa.Text(), nullable=True))

    if not _col_exists('conversations', 'summary_cached_at'):
        op.add_column('conversations', sa.Column('summary_cached_at', sa.DateTime(), nullable=True))

    # --- users ---
    if _col_exists('users', 'invited_by_id'):
        op.alter_column('users', 'invited_by_id', new_column_name='invited_by')

    # --- webhook_deliveries ---
    # Add event_type and duration_ms which are in the model but missing from migration
    if not _col_exists('webhook_deliveries', 'event_type'):
        op.add_column('webhook_deliveries', sa.Column('event_type', sa.String(100), nullable=True))
    if not _col_exists('webhook_deliveries', 'duration_ms'):
        op.add_column('webhook_deliveries', sa.Column('duration_ms', sa.Integer(), nullable=True))


def downgrade():
    if _col_exists('conversations', 'assigned_to'):
        op.alter_column('conversations', 'assigned_to', new_column_name='assigned_to_id')
    if _col_exists('conversations', 'sla_breach'):
        op.alter_column('conversations', 'sla_breach', new_column_name='sla_breached')
    if _col_exists('conversations', 'meta'):
        op.alter_column('conversations', 'meta', new_column_name='metadata')
    if _col_exists('users', 'invited_by'):
        op.alter_column('users', 'invited_by', new_column_name='invited_by_id')
